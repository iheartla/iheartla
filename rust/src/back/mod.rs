//! Code generators.

pub mod names;
pub mod eigen;
pub mod latex;
pub mod matlab;
pub mod random;
pub mod numpy;

use crate::ast::Program;
use crate::dims::Dim;
use crate::ty::Ty;

/// The dimensions of parameters that divide (x ∈ ℝ^(n/2)), rendered by `render`, in order and
/// without repeats. Division is real division, so a backend asserts that each is an integer
/// (as the Python compiler does).
pub(crate) fn arith_dims(prog: &Program, render: impl Fn(&Dim) -> String) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    for p in &prog.params {
        let dims: Vec<&Dim> = match &p.ty {
            Ty::Vector { rows, .. } => vec![rows],
            Ty::Matrix { rows, cols, .. } => vec![rows, cols],
            _ => vec![],
        };
        for d in dims {
            if matches!(d, Dim::Sym(_) | Dim::Str(_)) {
                let t = render(d);
                if t.contains('/') && !out.contains(&t) {
                    out.push(t);
                }
            }
        }
    }
    out
}

#[cfg(test)]
mod tests {
    /// The generated statement for `y`, without spaces or `this->`.
    fn line(src: &str, backend: &str) -> String {
        let out = crate::compile(src, backend, "heartlib", false).unwrap();
        let prefix = match backend {
            "numpy" => "self.y = ",
            "eigen" => "this->y = ",
            _ => "y = ",
        };
        // (the last one: MATLAB's header comment repeats the source)
        let l = out
            .lines()
            .map(|l| l.trim())
            .filter(|l| l.starts_with(prefix))
            .last()
            .unwrap_or_else(|| panic!("no y in {out}"))
            .to_string();
        l.split_once(" = ").unwrap().1.trim_end_matches(';').replace("this->", "").replace(' ', "")
    }

    fn scalars(e: &str) -> String {
        format!("y = {e}\nwhere\na,b,c,d ∈ ℝ\n")
    }

    /// Parentheses in the source stay in every code backend: floating-point `+` and
    /// `*` aren't associative (issue: `a + (b - c)` became `a + b - c`).
    #[test]
    fn keeps_source_grouping() {
        let cases = [
            ("a + (b - c)", "a+(b-c)"),
            ("a + (b + c)", "a+(b+c)"),
            ("a - (b - c)", "a-(b-c)"),
            ("a b + (a c)", "a*b+(a*c)"),
            ("(a - b) + (c - d)", "(a-b)+(c-d)"),
            ("a + (b + (c + d))", "a+(b+(c+d))"),
            ("-(a - b)", "-(a-b)"),
            ("-(a + b) + c", "-(a+b)+c"),
            ("a (b c)", "a*(b*c)"),
            ("(a+(b+c))(c-(a-b))(c+(a-b))(a+(b-c))", "(((a+(b+c))*(c-(a-b)))*(c+(a-b)))*(a+(b-c))"),
        ];
        for (src, want) in cases {
            for backend in ["numpy", "eigen", "matlab"] {
                assert_eq!(line(&scalars(src), backend), want, "{src} in {backend}");
            }
        }
        // (no extra parentheses where the source had none)
        assert_eq!(line(&scalars("a + b - c"), "numpy"), "a+b-c");
        // vectors, and the Hadamard product (a function call in NumPy and C++)
        let v = "y = u + (v + w)\nwhere\nu,v,w ∈ ℝ^3\n";
        for backend in ["numpy", "eigen", "matlab"] {
            assert_eq!(line(v, backend), "u+(v+w)", "{backend}");
        }
        let h = "y = A ∘ (B ∘ C)\nwhere\nA,B,C ∈ ℝ^(2×2)\n";
        assert_eq!(line(h, "matlab"), "A.*(B.*C)");
    }

    /// NumPy scalar powers use np.power (nan, not a complex number, for a negative
    /// base and a fractional exponent; inf, not OverflowError, on overflow), as the
    /// Python compiler does; integer powers keep `**`.
    #[test]
    fn numpy_scalar_power() {
        assert_eq!(line(&scalars("a^b"), "numpy"), "np.power(a,b)");
        assert_eq!(line(&scalars("(a + b)^(c - d)"), "numpy"), "np.power((a+b),(c-d))");
        assert_eq!(line("y = i^2\nwhere\ni ∈ ℤ\n", "numpy"), "i**2");
    }

    /// Division is real division with a real type, also of integers (7/2 is 3.5), and so
    /// is a negative power of an integer: C++ declares `double y` and divides as doubles.
    #[test]
    fn integer_division_is_real() {
        let ints = |e: &str| format!("y = {e}\nwhere\ni,j,k ∈ ℤ\n");
        for (src, want) in [
            ("i/j", "double(i)/j"),
            ("(i + j)/k", "double((i+j))/k"),
            ("i/j/k", "(double(i)/j)/k"),
            ("i/(j/k)", "i/(double(j)/k)"),
            ("i^(-1)", "1.0/i"),
            ("1/2", "double(1)/2"),
            ("2^(-1)", "1.0/2"),
        ] {
            assert_eq!(line(&ints(src), "eigen"), want, "{src}");
            let out = crate::compile(&ints(src), "eigen", "heartlib", false).unwrap();
            assert!(out.contains("    double y;"), "{src}: {out}");
        }
        let v = "y = v/2\nwhere\nv ∈ ℤ^3\n";
        assert_eq!(line(v, "eigen"), "(v).cast<double>()/2");
        assert!(crate::compile(v, "eigen", "heartlib", false).unwrap().contains("Eigen::Matrix<double, 3, 1> y;"));
    }

    /// A subscript expression must be an integer, so v_(i/2) is an error; a division in a
    /// dimension must be exact, and every backend checks that it is.
    #[test]
    fn division_in_subscript_and_dimension() {
        let e = crate::compile("y = v_(i/2)\nwhere\nv ∈ ℝ^3\ni ∈ ℤ\n", "numpy", "heartlib", false).unwrap_err();
        assert!(e.contains("Subscript i/2 must be an integer"), "{e}");
        let d = "y_i = x_i + 1\nwhere\nx ∈ ℝ^(n/2)\nn ∈ ℤ\n";
        let np = crate::compile(d, "numpy", "heartlib", false).unwrap();
        assert!(np.contains("assert n/2 == int(n/2)") && np.contains("np.zeros(int(n/2))"), "{np}");
        let cpp = crate::compile(d, "eigen", "heartlib", false).unwrap();
        assert!(cpp.contains("assert( fmod(n/(double)2, 1) == 0.0 );"), "{cpp}");
        let m = crate::compile(d, "matlab", "heartlib", false).unwrap();
        assert!(m.contains("assert( mod(n/2, 1) == 0.0 );"), "{m}");
    }
}
