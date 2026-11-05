//! Code generators.

pub mod names;
pub mod eigen;
pub mod latex;
pub mod matlab;
pub mod random;
pub mod numpy;

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
}
