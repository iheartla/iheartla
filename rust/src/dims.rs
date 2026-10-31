//! Dimensions of matrices, vectors, sequences and sets.
//!
//! The Python compiler stores a dimension as an `int`, a `str` (a symbol such
//! as `n`, or text such as `n+1` from a type annotation), a SymPy expression
//! (results of `mul_dims`, `add_syms`, `get_sum_value`), or `None`, and its
//! behavior depends on which: `isinstance(d, int)` checks, `str(d)` when
//! printing, SymPy equality in `is_same_expr`. `Dim` keeps that distinction.
//! `Sym` is a small computer-algebra system that evaluates and prints sums and
//! products of symbols the way SymPy does (`sympify("n*2+1")` prints as
//! `2*n + 1`), which is all that dimensions need.

use std::cmp::Ordering;
use std::fmt;

#[derive(Clone, Debug, Default, PartialEq)]
pub enum Dim {
    #[default]
    None,
    Int(i64),
    Str(String),
    Sym(Sym),
}

impl Dim {
    pub fn is_none(&self) -> bool {
        matches!(self, Dim::None)
    }
    /// `isinstance(d, int)`
    pub fn is_int(&self) -> bool {
        matches!(self, Dim::Int(_))
    }
    /// `isinstance(d, str)`
    pub fn is_str(&self) -> bool {
        matches!(self, Dim::Str(_))
    }
    pub fn as_int(&self) -> Option<i64> {
        match self {
            Dim::Int(i) => Some(*i),
            _ => None,
        }
    }
    pub fn as_str(&self) -> Option<&str> {
        match self {
            Dim::Str(s) => Some(s),
            _ => None,
        }
    }
    /// Python truthiness (`if d:`): 0, '' and None are false. SymPy
    /// expressions other than numbers raise in Python; they count as true.
    pub fn truthy(&self) -> bool {
        match self {
            Dim::None => false,
            Dim::Int(i) => *i != 0,
            Dim::Str(s) => !s.is_empty(),
            Dim::Sym(s) => s.as_integer() != Some(0),
        }
    }
    /// `str(d)` (`format`); None prints as "None".
    pub fn to_py_string(&self) -> String {
        self.to_string()
    }
    /// Python `==`. A SymPy expression equals an int if it is that integer,
    /// and never equals a str.
    pub fn py_eq(&self, other: &Dim) -> bool {
        match (self, other) {
            (Dim::None, Dim::None) => true,
            (Dim::Int(a), Dim::Int(b)) => a == b,
            (Dim::Str(a), Dim::Str(b)) => a == b,
            (Dim::Sym(a), Dim::Sym(b)) => a == b,
            (Dim::Sym(a), Dim::Int(b)) | (Dim::Int(b), Dim::Sym(a)) => a.as_integer() == Some(*b),
            _ => false,
        }
    }
    /// `str.isnumeric()` for string dims; false otherwise.
    pub fn is_numeric_str(&self) -> bool {
        match self {
            Dim::Str(s) => !s.is_empty() && s.chars().all(crate::helper::py_isnumeric),
            _ => false,
        }
    }
    /// Convert to a SymPy expression as `sympify(str(d))` would.
    pub fn to_sym(&self) -> Result<Sym, String> {
        match self {
            Dim::Int(i) => Ok(Sym::int(*i)),
            Dim::Sym(s) => Ok(s.clone()),
            Dim::Str(s) => Sym::parse(s),
            Dim::None => Err("None".into()),
        }
    }
}

impl fmt::Display for Dim {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Dim::None => write!(f, "None"),
            Dim::Int(i) => write!(f, "{i}"),
            Dim::Str(s) => write!(f, "{s}"),
            Dim::Sym(s) => write!(f, "{s}"),
        }
    }
}

impl From<i64> for Dim {
    fn from(i: i64) -> Self {
        Dim::Int(i)
    }
}
impl From<i32> for Dim {
    fn from(i: i32) -> Self {
        Dim::Int(i as i64)
    }
}
impl From<usize> for Dim {
    fn from(i: usize) -> Self {
        Dim::Int(i as i64)
    }
}
impl From<&str> for Dim {
    fn from(s: &str) -> Self {
        Dim::Str(s.to_string())
    }
}
impl From<String> for Dim {
    fn from(s: String) -> Self {
        Dim::Str(s)
    }
}

/// `is_same_expr(lhs, rhs)`: `sympify('{} == {}'.format(lhs, rhs))`.
pub fn is_same_expr(a: &Dim, b: &Dim) -> bool {
    match (a, b) {
        (Dim::None, Dim::None) => true,
        (Dim::None, _) | (_, Dim::None) => false,
        _ => match (a.to_sym(), b.to_sym()) {
            (Ok(x), Ok(y)) => x == y,
            _ => a.to_string() == b.to_string(),
        },
    }
}

/// `is_same_expr` on strings (used with orders such as "1+1" and "2").
pub fn is_same_expr_str(a: &str, b: &str) -> bool {
    match (Sym::parse(a), Sym::parse(b)) {
        (Ok(x), Ok(y)) => x == y,
        _ => a == b,
    }
}

fn combine(lhs: &Dim, rhs: &Dim, op: char) -> Dim {
    if let (Dim::Int(a), Dim::Int(b)) = (lhs, rhs) {
        let v = match op {
            '*' => a * b,
            _ => a + b,
        };
        return Dim::Sym(Sym::int(v));
    }
    // Python formats both sides into a string and sympifies it (so "n+1" * m
    // becomes "n+1*m"); non-str, non-int values go through str() as well.
    let text = format!("{lhs}{op}{rhs}");
    match Sym::parse(&text) {
        Ok(s) => Dim::Sym(s),
        Err(_) => Dim::Str(text),
    }
}

/// `mul_dims(lhs, rhs)`
pub fn mul_dims(lhs: &Dim, rhs: &Dim) -> Dim {
    combine(lhs, rhs, '*')
}

/// `add_syms(lhs, rhs)`
pub fn add_syms(lhs: &Dim, rhs: &Dim) -> Dim {
    combine(lhs, rhs, '+')
}

/// `simpify_dims(text)`
pub fn simpify(text: &str) -> Dim {
    match Sym::parse(text) {
        Ok(s) => Dim::Sym(s),
        Err(_) => Dim::Str(text.to_string()),
    }
}

// ---------------------------------------------------------------------------
// A small SymPy subset: rational numbers, symbols, sums, products, integer powers.

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Sym {
    /// A rational number p/q with q > 0, in lowest terms.
    Num(i64, i64),
    Symbol(String),
    /// A sum, flattened, like terms combined, at most one number (last when
    /// sorted), at least two terms.
    Add(Vec<Sym>),
    /// A product: a coefficient and non-numeric factors (bases with integer
    /// exponents), at least one factor; coefficient 1 with one factor of
    /// exponent 1 collapses to the factor.
    Mul(i64, i64, Vec<(Sym, i64)>),
}

fn gcd(a: i64, b: i64) -> i64 {
    if b == 0 {
        a.abs()
    } else {
        gcd(b, a % b)
    }
}

fn rat(p: i64, q: i64) -> Sym {
    let g = gcd(p, q).max(1);
    let (mut p, mut q) = (p / g, q / g);
    if q < 0 {
        p = -p;
        q = -q;
    }
    Sym::Num(p, q)
}

impl Sym {
    pub fn int(i: i64) -> Sym {
        Sym::Num(i, 1)
    }

    pub fn as_integer(&self) -> Option<i64> {
        match self {
            Sym::Num(p, 1) => Some(*p),
            _ => None,
        }
    }

    pub fn parse(text: &str) -> Result<Sym, String> {
        let mut p = SymParser { chars: text.chars().collect(), pos: 0 };
        let e = p.expr()?;
        p.skip_ws();
        if p.pos != p.chars.len() {
            return Err(format!("cannot sympify {text:?}"));
        }
        Ok(e)
    }

    /// (coefficient, non-numeric part) of a term.
    fn split_coeff(&self) -> ((i64, i64), Option<Sym>) {
        match self {
            Sym::Num(p, q) => ((*p, *q), None),
            Sym::Mul(p, q, f) => {
                let rest = if f.len() == 1 && f[0].1 == 1 { f[0].0.clone() } else { Sym::Mul(1, 1, f.clone()) };
                ((*p, *q), Some(rest))
            }
            other => ((1, 1), Some(other.clone())),
        }
    }

    fn factors(&self) -> Vec<(Sym, i64)> {
        match self {
            Sym::Mul(1, 1, f) => f.clone(),
            other => vec![(other.clone(), 1)],
        }
    }

    pub fn add(terms: Vec<Sym>) -> Sym {
        let mut flat = Vec::new();
        for t in terms {
            match t {
                Sym::Add(v) => flat.extend(v),
                t => flat.push(t),
            }
        }
        let (mut np, mut nq) = (0i64, 1i64);
        let mut parts: Vec<((i64, i64), Sym)> = Vec::new();
        for t in flat {
            let ((p, q), rest) = t.split_coeff();
            match rest {
                None => {
                    let r = rat(np * q + p * nq, nq * q);
                    if let Sym::Num(a, b) = r {
                        np = a;
                        nq = b;
                    }
                }
                Some(r) => match parts.iter_mut().find(|(_, x)| *x == r) {
                    Some(((cp, cq), _)) => {
                        if let Sym::Num(a, b) = rat(*cp * q + p * *cq, *cq * q) {
                            *cp = a;
                            *cq = b;
                        }
                    }
                    None => parts.push(((p, q), r)),
                },
            }
        }
        let mut out: Vec<Sym> = parts
            .into_iter()
            .filter(|((p, _), _)| *p != 0)
            .map(|((p, q), r)| Sym::mul_coeff(p, q, r))
            .collect();
        if np != 0 {
            out.push(Sym::Num(np, nq));
        }
        out.sort_by(canonical_cmp);
        match out.len() {
            0 => Sym::int(0),
            1 => out.pop().unwrap(),
            _ => Sym::Add(out),
        }
    }

    fn mul_coeff(p: i64, q: i64, r: Sym) -> Sym {
        if p == 1 && q == 1 {
            return r;
        }
        match r {
            Sym::Mul(_, _, f) => Sym::Mul(p, q, f),
            other => Sym::Mul(p, q, vec![(other, 1)]),
        }
    }

    pub fn mul(factors: Vec<Sym>) -> Sym {
        let (mut cp, mut cq) = (1i64, 1i64);
        let mut bases: Vec<(Sym, i64)> = Vec::new();
        let mut adds: Vec<Sym> = Vec::new();
        for f in factors {
            match f {
                Sym::Num(p, q) => {
                    if let Sym::Num(a, b) = rat(cp * p, cq * q) {
                        cp = a;
                        cq = b;
                    }
                }
                Sym::Mul(p, q, fs) => {
                    if let Sym::Num(a, b) = rat(cp * p, cq * q) {
                        cp = a;
                        cq = b;
                    }
                    for (b, e) in fs {
                        push_base(&mut bases, b, e);
                    }
                }
                Sym::Add(v) => adds.push(Sym::Add(v)),
                s => push_base(&mut bases, s, 1),
            }
        }
        if cp == 0 {
            return Sym::int(0);
        }
        // SymPy distributes a number over a single sum: 2*(n + 1) -> 2*n + 2
        if bases.is_empty() && adds.len() == 1 && !(cp == 1 && cq == 1) {
            if let Sym::Add(v) = adds.pop().unwrap() {
                return Sym::add(v.into_iter().map(|t| Sym::mul(vec![Sym::Num(cp, cq), t])).collect());
            }
        }
        for a in adds {
            push_base(&mut bases, a, 1);
        }
        bases.retain(|(_, e)| *e != 0);
        bases.sort_by(|a, b| canonical_cmp(&a.0, &b.0));
        if bases.is_empty() {
            return Sym::Num(cp, cq);
        }
        if cp == 1 && cq == 1 && bases.len() == 1 && bases[0].1 == 1 {
            return bases.pop().unwrap().0;
        }
        Sym::Mul(cp, cq, bases)
    }

    fn neg(self) -> Sym {
        Sym::mul(vec![Sym::int(-1), self])
    }

    fn pow(self, e: i64) -> Result<Sym, String> {
        match self {
            Sym::Num(p, q) if e >= 0 => Ok(rat(p.pow(e as u32), q.pow(e as u32))),
            s => Ok(Sym::mul(vec![Sym::Mul(1, 1, vec![(s, e)])])),
        }
    }

    fn is_negative_term(&self) -> bool {
        match self {
            Sym::Num(p, _) => *p < 0,
            Sym::Mul(p, _, _) => *p < 0,
            _ => false,
        }
    }

    /// Lexicographic monomial over generators, for SymPy's `as_ordered_terms`.
    fn monomial(&self, gens: &[Sym]) -> Vec<i64> {
        let mut m = vec![0; gens.len()];
        for (b, e) in self.split_coeff().1.map(|r| r.factors()).unwrap_or_default() {
            if let Some(i) = gens.iter().position(|g| *g == b) {
                m[i] = e;
            }
        }
        m
    }
}

fn push_base(bases: &mut Vec<(Sym, i64)>, b: Sym, e: i64) {
    match bases.iter_mut().find(|(x, _)| *x == b) {
        Some((_, ee)) => *ee += e,
        None => bases.push((b, e)),
    }
}

/// An approximation of SymPy's canonical argument order (`default_sort_key`):
/// numbers first, then symbols by name, then compound expressions.
fn canonical_cmp(a: &Sym, b: &Sym) -> Ordering {
    fn rank(s: &Sym) -> u8 {
        match s {
            Sym::Num(..) => 0,
            Sym::Symbol(_) => 1,
            Sym::Mul(..) => 2,
            Sym::Add(_) => 3,
        }
    }
    match (a, b) {
        (Sym::Symbol(x), Sym::Symbol(y)) => x.cmp(y),
        (Sym::Num(p1, q1), Sym::Num(p2, q2)) => (p1 * q2).cmp(&(p2 * q1)),
        _ => rank(a).cmp(&rank(b)).then_with(|| a.to_string().cmp(&b.to_string())),
    }
}

impl fmt::Display for Sym {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Sym::Num(p, 1) => write!(f, "{p}"),
            Sym::Num(p, q) => write!(f, "{p}/{q}"),
            Sym::Symbol(s) => write!(f, "{s}"),
            Sym::Mul(p, q, fs) => {
                let mut num = Vec::new();
                let mut den = Vec::new();
                for (b, e) in fs {
                    let base = match b {
                        Sym::Add(_) => format!("({b})"),
                        _ => b.to_string(),
                    };
                    if *e > 0 {
                        num.push(if *e == 1 { base } else { format!("{base}**{e}") });
                    } else {
                        den.push(if *e == -1 { base } else { format!("{base}**{}", -e) });
                    }
                }
                let mut s = String::new();
                if *p == -1 && !num.is_empty() {
                    s.push('-');
                } else if *p != 1 || num.is_empty() {
                    s.push_str(&format!("{p}"));
                    if !num.is_empty() {
                        s.push('*');
                    }
                }
                s.push_str(&num.join("*"));
                if *q != 1 {
                    den.insert(0, q.to_string());
                }
                if !den.is_empty() {
                    s.push('/');
                    if den.len() > 1 {
                        s.push_str(&format!("({})", den.join("*")));
                    } else {
                        s.push_str(&den[0]);
                    }
                }
                write!(f, "{s}")
            }
            Sym::Add(terms) => {
                let ordered = ordered_terms(terms);
                let mut out = String::new();
                for (i, t) in ordered.iter().enumerate() {
                    let text = match t {
                        Sym::Add(_) => format!("({t})"),
                        _ => t.to_string(),
                    };
                    let (neg, body) = match text.strip_prefix('-') {
                        Some(b) if !matches!(t, Sym::Add(_)) => (true, b.to_string()),
                        _ => (false, text),
                    };
                    if i == 0 {
                        if neg {
                            out.push('-');
                        }
                    } else {
                        out.push_str(if neg { " - " } else { " + " });
                    }
                    out.push_str(&body);
                }
                write!(f, "{out}")
            }
        }
    }
}

/// SymPy's `Expr.as_ordered_terms()` for an Add.
fn ordered_terms(terms: &[Sym]) -> Vec<Sym> {
    // special case: a positive number and a negated product (1 - n)
    if terms.len() == 2 {
        let num = terms.iter().find(|t| matches!(t, Sym::Num(..)));
        let other = terms.iter().find(|t| !matches!(t, Sym::Num(..)));
        if let (Some(Sym::Num(p, _)), Some(o @ Sym::Mul(c, _, _))) = (num, other) {
            if *p > 0 && *c < 0 {
                return vec![num.unwrap().clone(), o.clone()];
            }
        }
    }
    let mut gens: Vec<Sym> = Vec::new();
    for t in terms {
        if let Some(r) = t.split_coeff().1 {
            for (b, _) in r.factors() {
                if !gens.contains(&b) {
                    gens.push(b);
                }
            }
        }
    }
    gens.sort_by(canonical_cmp);
    let mut v: Vec<Sym> = terms.to_vec();
    v.sort_by(|a, b| {
        let (ma, mb) = (a.monomial(&gens), b.monomial(&gens));
        // larger monomials first (lex), then by coefficient
        mb.cmp(&ma).then_with(|| {
            let ((p1, q1), _) = a.split_coeff();
            let ((p2, q2), _) = b.split_coeff();
            (p1 * q2).cmp(&(p2 * q1))
        })
    });
    let _ = Sym::is_negative_term;
    v
}

struct SymParser {
    chars: Vec<char>,
    pos: usize,
}

impl SymParser {
    fn skip_ws(&mut self) {
        while self.pos < self.chars.len() && self.chars[self.pos].is_whitespace() {
            self.pos += 1;
        }
    }
    fn peek(&mut self) -> Option<char> {
        self.skip_ws();
        self.chars.get(self.pos).copied()
    }
    fn expr(&mut self) -> Result<Sym, String> {
        let mut terms = vec![self.term()?];
        while let Some(c) = self.peek() {
            match c {
                '+' => {
                    self.pos += 1;
                    terms.push(self.term()?);
                }
                '-' => {
                    self.pos += 1;
                    terms.push(self.term()?.neg());
                }
                _ => break,
            }
        }
        Ok(if terms.len() == 1 { terms.pop().unwrap() } else { Sym::add(terms) })
    }
    fn term(&mut self) -> Result<Sym, String> {
        let mut f = self.unary()?;
        loop {
            match self.peek() {
                Some('*') if self.chars.get(self.pos + 1) != Some(&'*') => {
                    self.pos += 1;
                    let r = self.unary()?;
                    f = Sym::mul(vec![f, r]);
                }
                Some('/') => {
                    self.pos += 1;
                    let r = self.unary()?;
                    f = Sym::mul(vec![f, r.pow(-1)?]);
                }
                _ => break,
            }
        }
        Ok(f)
    }
    fn unary(&mut self) -> Result<Sym, String> {
        match self.peek() {
            Some('-') => {
                self.pos += 1;
                Ok(self.unary()?.neg())
            }
            Some('+') => {
                self.pos += 1;
                self.unary()
            }
            _ => self.power(),
        }
    }
    fn power(&mut self) -> Result<Sym, String> {
        let base = self.atom()?;
        if self.peek() == Some('*') && self.chars.get(self.pos + 1) == Some(&'*') {
            self.pos += 2;
            let e = self.unary()?;
            return match e.as_integer() {
                Some(i) => base.pow(i),
                None => Err("non-integer power".into()),
            };
        }
        Ok(base)
    }
    fn atom(&mut self) -> Result<Sym, String> {
        match self.peek() {
            Some('(') => {
                self.pos += 1;
                let e = self.expr()?;
                if self.peek() != Some(')') {
                    return Err("expected )".into());
                }
                self.pos += 1;
                Ok(e)
            }
            Some(c) if c.is_ascii_digit() => {
                let start = self.pos;
                while self.pos < self.chars.len() && self.chars[self.pos].is_ascii_digit() {
                    self.pos += 1;
                }
                let s: String = self.chars[start..self.pos].iter().collect();
                s.parse::<i64>().map(Sym::int).map_err(|e| e.to_string())
            }
            Some(c) if c.is_alphabetic() || c == '_' => {
                let start = self.pos;
                while self.pos < self.chars.len()
                    && (self.chars[self.pos].is_alphanumeric() || self.chars[self.pos] == '_')
                {
                    self.pos += 1;
                }
                let s: String = self.chars[start..self.pos].iter().collect();
                // names SymPy predefines as functions or constants behave differently
                if matches!(s.as_str(), "N" | "S" | "Q" | "O" | "E" | "I" | "pi" | "oo" | "zoo" | "nan" | "None") {
                    return Err(format!("sympy special name {s}"));
                }
                Ok(Sym::Symbol(s))
            }
            _ => Err("unexpected character".into()),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn s(t: &str) -> String {
        Sym::parse(t).unwrap().to_string()
    }

    #[test]
    fn prints_like_sympy() {
        let cases = [
            ("n+1", "n + 1"),
            ("1+n", "n + 1"),
            ("n-1", "n - 1"),
            ("1-n", "1 - n"),
            ("-n-1", "-n - 1"),
            ("2*n", "2*n"),
            ("n*2", "2*n"),
            ("n*m", "m*n"),
            ("n*n", "n**2"),
            ("n+m", "m + n"),
            ("m+n+1", "m + n + 1"),
            ("3*n+2*m+1", "2*m + 3*n + 1"),
            ("n*m+n", "m*n + n"),
            ("2*3", "6"),
            ("n+n", "2*n"),
            ("n+1*m", "m + n"),
            ("(n+1)*m", "m*(n + 1)"),
            ("a*b*c", "a*b*c"),
            ("dimv*3", "3*dimv"),
            ("x_1+1", "x_1 + 1"),
            ("n**2+n", "n**2 + n"),
            ("n/2", "n/2"),
            ("2*n+n*m", "m*n + 2*n"),
            ("b*a+c", "a*b + c"),
            ("n-m", "-m + n"),
            ("m-n", "m - n"),
            ("-n", "-n"),
            ("n+1+1", "n + 2"),
            ("n*(m+1)", "n*(m + 1)"),
            ("2*(n+1)", "2*n + 2"),
        ];
        for (input, expected) in cases {
            assert_eq!(s(input), expected, "sympify({input:?})");
        }
    }

    #[test]
    fn equality() {
        assert!(is_same_expr(&Dim::from("n+1"), &Dim::from("1+n")));
        assert!(is_same_expr(&Dim::Int(6), &mul_dims(&Dim::Int(2), &Dim::Int(3))));
        assert!(!is_same_expr(&Dim::from("n"), &Dim::from("m")));
        assert!(Dim::Sym(Sym::int(6)).py_eq(&Dim::Int(6)));
        assert!(!Dim::Sym(Sym::Symbol("n".into())).py_eq(&Dim::from("n")));
    }
}
