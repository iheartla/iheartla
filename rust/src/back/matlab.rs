//! MATLAB backend (also runs in GNU Octave).
//!
//! Generates a function `output = NAME(params...)` whose struct `output`
//! holds every defined symbol, as the Python compiler's MATLAB output does.
//! Vectors are columns (vector arguments are reshaped); a sequence of
//! scalars is a column, of vectors an n×k array (item i is row i), of
//! matrices an n×r×c array; other sequences, ragged ones and sequences of
//! functions are cell arrays. Sets are matrices with one row per element.
//! Local functions are nested functions (they see the parameters and
//! definitions). Subscripts are 1-based as in I❤LA, and so are `index`
//! values in MATLAB (the Python compiler's MATLAB convention and its tests).

use super::names::{convert_unicode, Kind};
use crate::ast::*;
use crate::dims::Dim;
use crate::ty::*;

pub fn generate(prog: &Program, func_name: &str) -> String {
    let mut g = Gen { prog, lines: Vec::new(), indent: 1, tmp: 0 };
    let params: Vec<String> = prog.params.iter().map(|p| m_ident(&p.name)).collect();
    let mut out = format!("function output = {func_name}({})\n", params.join(", "));
    out.push_str(&format!("% output = {func_name}({})\n%\n", params.join(", ")));
    for l in prog.source.trim_end().lines() {
        out.push_str(&format!("%    {l}\n"));
    }
    if !prog.meshes.is_empty() || !prog.modules.is_empty() {
        out.push_str("    error('I❤MESH meshes and modules are not supported by the MATLAB backend');\nend\n");
        return out;
    }
    g.init_params();
    let mut funcs = Vec::new();
    for s in &prog.stmts {
        match s {
            Stmt::Func(f) => funcs.push(f),
            s => g.stmt(s),
        }
    }
    for f in funcs {
        g.local_func(f);
    }
    for (n, _) in &prog.defs {
        // (the field keeps the name even where the variable avoids a reserved word)
        g.line(format!("output.{} = {};", m_field(n), m_ident(n)));
    }
    out.push_str(&g.lines.join("\n"));
    out.push_str("\nend\n");
    out
}

/// A valid MATLAB identifier for an I❤LA name.
pub fn m_ident(name: &str) -> String {
    let n = m_field(name);
    if crate::helper::is_keyword(&n, crate::helper::KeywordSet::Numpy) || MATLAB_RESERVED.contains(&n.as_str()) {
        return format!("{n}_");
    }
    n
}

/// A valid MATLAB name (a struct field) for an I❤LA name: ASCII letters,
/// digits and `_`, starting with a letter, at most 63 characters.
pub fn m_field(name: &str) -> String {
    // (as in the Python compiler, every name: μ becomes mu)
    let n = convert_unicode(Kind::Matlab, name).replace('-', "_");
    let mut out = String::new();
    for c in n.chars() {
        if c.is_ascii_alphanumeric() || c == '_' {
            out.push(c);
        } else {
            out += &format!("u{:x}", c as u32);
        }
    }
    if !out.starts_with(|c: char| c.is_ascii_alphabetic()) {
        out = format!("v{out}");
    }
    if out.len() > 63 {
        // a prefix and a hash of the whole name (FNV-1a) keep long names distinct
        let h = name.bytes().fold(0xcbf29ce484222325u64, |h, b| (h ^ b as u64).wrapping_mul(0x100000001b3));
        out = format!("{}_{:08x}", &out[..50], h as u32);
    }
    out
}

const MATLAB_RESERVED: &[&str] = &[
    "end", "function", "if", "else", "elseif", "while", "for", "switch", "case", "otherwise", "break", "continue", "return",
    "global", "persistent", "try", "catch", "output", "i", "j", "pi", "eps", "inf", "nan", "sum", "size", "zeros", "ones", "eye",
];

/// How a sequence is stored.
#[derive(PartialEq)]
enum SeqStore {
    /// a column (scalars)
    Column,
    /// an n×k array (vectors)
    Rows,
    /// an n×r×c array (matrices)
    Slices,
    /// a cell array
    Cells,
}

fn seq_store(elem: &Ty) -> SeqStore {
    let ragged = |d: &Dim| matches!(d, Dim::Str(s) if s.ends_with("[i]"));
    match elem {
        Scalar(_) => SeqStore::Column,
        Vector { rows, .. } if !ragged(rows) => SeqStore::Rows,
        Matrix { rows, cols, sparse: false, .. } if !ragged(rows) && !ragged(cols) => SeqStore::Slices,
        _ => SeqStore::Cells,
    }
}

struct Gen<'p> {
    prog: &'p Program,
    lines: Vec<String>,
    indent: usize,
    tmp: usize,
}

impl<'p> Gen<'p> {
    fn line(&mut self, s: impl AsRef<str>) {
        self.lines.push(format!("{}{}", "    ".repeat(self.indent), s.as_ref()));
    }

    fn fresh(&mut self, base: &str) -> String {
        self.tmp += 1;
        format!("{base}_{}", self.tmp)
    }

    fn dim(&self, d: &Dim) -> String {
        match d {
            Dim::Str(s) if s.starts_with("@len:") => {
                let parts: Vec<&str> = s.splitn(4, ':').collect();
                let axis: usize = parts[3].parse().unwrap_or(0);
                format!("size({}{{{}}}, {})", m_ident(parts[1]), m_ident(parts[2]), axis + 1)
            }
            Dim::Str(s) if s.ends_with("[i]") => s.clone(),
            Dim::Str(s) => m_ident(s),
            d => d.to_string(),
        }
    }

    fn init_params(&mut self) {
        let prog = self.prog;
        for p in &prog.params {
            let n = m_ident(&p.name);
            match &p.ty {
                Vector { .. } => self.line(format!("{n} = reshape({n}, [], 1);")),
                Seq { elem, .. } if seq_store(elem) == SeqStore::Column => self.line(format!("{n} = reshape({n}, [], 1);")),
                Set { elems, .. } if elems.len() == 1 => self.line(format!("{n} = reshape({n}, [], 1);")),
                _ => {}
            }
        }
        for d in &prog.dims {
            let p = m_ident(&d.param);
            let ty = &prog.params.iter().find(|x| x.name == d.param).unwrap().ty;
            let src = match ty {
                Seq { elem, .. } if d.axis > 0 && seq_store(elem) == SeqStore::Cells => format!("size({p}{{1}}, {})", d.axis),
                _ => format!("size({p}, {})", d.axis + 1),
            };
            self.line(format!("{} = {src};", m_ident(&d.name)));
        }
        for p in &prog.params {
            let n = m_ident(&p.name);
            match &p.ty {
                Matrix { rows, cols, sparse: false, .. } => {
                    let (r, c) = (self.dim(rows), self.dim(cols));
                    self.line(format!("assert( isequal(size({n}), [{r}, {c}]) );"));
                }
                Vector { rows, .. } => {
                    let r = self.dim(rows);
                    self.line(format!("assert( numel({n}) == {r} );"));
                }
                Scalar(_) => self.line(format!("assert( numel({n}) == 1 );")),
                _ => {}
            }
        }
        if !prog.params.is_empty() {
            self.line("");
        }
    }

    fn comment(&mut self, text: &str) {
        for l in text.lines() {
            self.line(format!("% {l}"));
        }
    }

    fn stmt(&mut self, s: &Stmt) {
        match s {
            Stmt::Assign(a) => {
                self.comment(&a.text);
                let target = m_ident(&a.lhs);
                if a.subs.is_empty() {
                    let v = self.expr(&a.rhs);
                    if a.accumulate {
                        self.line(format!("{target} = {target} + {v};"));
                    } else {
                        self.line(format!("{target} = {v};"));
                    }
                } else {
                    self.elementwise(a, &target);
                }
            }
            Stmt::Multi { lhs, rhs, text } => {
                self.comment(text);
                let v = self.expr(rhs);
                let tmp = self.fresh("tuple");
                self.line(format!("{tmp} = {v};"));
                for (k, (n, _)) in lhs.iter().enumerate() {
                    let item = match &rhs.ty {
                        Tuple(_) | Seq { .. } => format!("{tmp}{{{}}}", k + 1),
                        _ => format!("{tmp}({})", k + 1),
                    };
                    let item = if matches!(&rhs.ty, Seq { elem, .. } if seq_store(elem) != SeqStore::Cells) { format!("{tmp}({})", k + 1) } else { item };
                    self.line(format!("{} = {item};", m_ident(n)));
                }
            }
            Stmt::Func(_) => {}
        }
    }

    fn elementwise(&mut self, a: &Assign, target: &str) {
        let subs: Vec<String> = a.subs.iter().map(|s| m_ident(s)).collect();
        let ext: Vec<String> = a.extents.iter().map(|d| self.dim(d)).collect();
        let fresh = !a.accumulate && !a.update;
        let mut write = target.to_string();
        match &a.ty {
            Vector { .. } if fresh => self.line(format!("{target} = zeros({}, 1);", ext[0])),
            Matrix { sparse, rows, cols, .. } => {
                if *sparse {
                    write = self.fresh("dense");
                    if fresh {
                        let (r, c) = (self.dim(rows), self.dim(cols));
                        self.line(format!("{write} = zeros({r}, {c});"));
                    } else {
                        self.line(format!("{write} = full({target});"));
                    }
                } else if fresh {
                    self.line(format!("{target} = zeros({}, {});", ext[0], ext[1]));
                }
            }
            Seq { elem, .. } if fresh => match seq_store(elem) {
                SeqStore::Column => self.line(format!("{target} = zeros({}, 1);", ext[0])),
                SeqStore::Rows => self.line(format!("{target} = zeros({}, {});", ext[0], self.dim(&elem.rows()))),
                SeqStore::Slices => self.line(format!("{target} = zeros({}, {}, {});", ext[0], self.dim(&elem.rows()), self.dim(&elem.cols()))),
                SeqStore::Cells => self.line(format!("{target} = cell({}, 1);", ext[0])),
            },
            _ => {}
        }
        let diag = a.subs.len() == 2 && a.subs[0] == a.subs[1];
        let loops = if diag { 1 } else { a.subs.len() };
        for k in 0..loops {
            self.line(format!("for {} = 1:{}", subs[k], ext[k]));
            self.indent += 1;
        }
        let v = self.expr(&a.rhs);
        let lhs = match &a.ty {
            Seq { elem, .. } => match seq_store(elem) {
                SeqStore::Column => format!("{write}({})", subs[0]),
                SeqStore::Rows => format!("{write}({}, :)", subs[0]),
                SeqStore::Slices => format!("{write}({}, :, :)", subs[0]),
                SeqStore::Cells => format!("{write}{{{}}}", subs[0]),
            },
            _ => format!("{write}({})", subs.join(", ")),
        };
        let v = match &a.ty {
            Seq { elem, .. } if seq_store(elem) == SeqStore::Rows => format!("({v}).'"),
            Seq { elem, .. } if seq_store(elem) == SeqStore::Slices => format!("reshape({v}, [1, size({v})])"),
            _ => v,
        };
        if a.accumulate {
            self.line(format!("{lhs} = {lhs} + {v};"));
        } else {
            self.line(format!("{lhs} = {v};"));
        }
        for _ in 0..loops {
            self.indent -= 1;
            self.line("end");
        }
        if write != target {
            self.line(format!("{target} = sparse({write});"));
        }
    }

    fn local_func(&mut self, f: &LocalFunc) {
        let params: Vec<String> = f.params.iter().map(|(n, _)| m_ident(n)).collect();
        self.line(format!("function ret = {}({})", m_ident(&f.name), params.join(", ")));
        self.indent += 1;
        for (n, t) in &f.params {
            if t.is_vector() {
                let n = m_ident(n);
                self.line(format!("{n} = reshape({n}, [], 1);"));
            }
            // (a sequence parameter's length, `U_n` for U_i ∈ ...)
            if let Seq { size: Dim::Str(s), .. } = t {
                self.line(format!("{} = size({}, 1);", m_ident(s), m_ident(n)));
            }
        }
        for s in &f.body {
            self.stmt(s);
        }
        let Func { rets, .. } = &f.ty else { unreachable!() };
        let v = self.expr(&f.expr);
        if rets.len() > 1 {
            self.line(format!("ret = {{{v}}};"));
        } else {
            self.line(format!("ret = {v};"));
        }
        self.indent -= 1;
        self.line("end");
    }

    // -- expressions ---------------------------------------------------------

    fn index(&mut self, i: &Idx) -> String {
        match i {
            Idx::All => ":".into(),
            Idx::At(e) => self.expr(e),
        }
    }

    fn paren(&mut self, e: &Expr) -> String {
        let s = self.expr(e);
        match &*e.kind {
            ExprKind::Add(..) | ExprKind::Sub(..) | ExprKind::Neg(..) | ExprKind::Mul(..) | ExprKind::Div(..) | ExprKind::Pow(..) => format!("({s})"),
            ExprKind::Int(v) if *v < 0 => format!("({s})"),
            _ => s,
        }
    }

    fn expr(&mut self, e: &Expr) -> String {
        use ExprKind::*;
        match &*e.kind {
            Int(v) => v.to_string(),
            Real(s) => s.clone(),
            Fraction(a, b) => format!("({a}/{b})"),
            Const(Constant::Pi) => "pi".into(),
            Const(Constant::E) => "exp(1)".into(),
            Const(Constant::Inf) => "Inf".into(),
            Var(n) => m_ident(n),
            Index { base, base_ty, idx } => {
                let b = m_ident(base);
                let p: Vec<String> = idx.iter().map(|i| self.index(i)).collect();
                match base_ty {
                    Vector { .. } => format!("{b}({})", p[0]),
                    Matrix { .. } => match (&idx[0], &idx[1]) {
                        (_, Idx::All) => format!("{b}({}, :).'", p[0]),
                        _ => format!("{b}({}, {})", p[0], p[1]),
                    },
                    Seq { elem, .. } => match (seq_store(elem), p.len()) {
                        (SeqStore::Column, _) => format!("{b}({})", p[0]),
                        (SeqStore::Rows, 1) => format!("{b}({}, :).'", p[0]),
                        (SeqStore::Rows, _) => format!("{b}({}, {})", p[0], p[1]),
                        (SeqStore::Slices, 1) => format!("reshape({b}({}, :, :), {}, {})", p[0], self.dim(&elem.rows()), self.dim(&elem.cols())),
                        (SeqStore::Slices, _) => match (&idx[1], &idx[2]) {
                            (Idx::All, _) => format!("reshape({b}({}, :, {}), [], 1)", p[0], p[2]),
                            (_, Idx::All) => format!("reshape({b}({}, {}, :), 1, [])", p[0], p[1]),
                            _ => format!("{b}({}, {}, {})", p[0], p[1], p[2]),
                        },
                        (SeqStore::Cells, 1) => format!("{b}{{{}}}", p[0]),
                        (SeqStore::Cells, _) => format!("{b}{{{}}}({})", p[0], p[1..].join(", ")),
                    },
                    Tuple(_) => format!("{b}{{{}}}", p[0]),
                    Set { .. } => format!("{b}({}, :)", p[0]),
                    _ => format!("{b}({})", p.join(", ")),
                }
            }
            Neg(x) => format!("-{}", self.paren(x)),
            Add(a, b) => format!("{} + {}", self.expr(a), self.expr(b)),
            Sub(a, b) => format!("{} - {}", self.expr(a), self.paren(b)),
            Mul(a, b) => format!("{} * {}", self.paren(a), self.paren(b)),
            Div(a, b) => format!("{} / {}", self.paren(a), self.paren(b)),
            Hadamard(a, b) => format!("{} .* {}", self.paren(a), self.paren(b)),
            Kronecker(a, b) => format!("kron({}, {})", self.expr(a), self.expr(b)),
            Cross(a, b) => format!("cross({}, {})", self.expr(a), self.expr(b)),
            Dot(a, b) | Inner(a, b, None) => format!("dot({}, {})", self.expr(a), self.expr(b)),
            Inner(a, b, Some(m)) => format!("({}).' * {} * {}", self.expr(b), self.paren(m), self.paren(a)),
            Frobenius(a, b) => format!("sum(sum({} .* {}))", self.paren(a), self.paren(b)),
            Pow(a, b) => {
                if a.ty.is_matrix() {
                    format!("{}^{}", self.paren(a), self.paren(b))
                } else {
                    format!("{}.^{}", self.paren(a), self.paren(b))
                }
            }
            Transpose(a) => format!("{}.'", self.paren(a)),
            Inverse(a) => {
                if a.ty.is_matrix() {
                    format!("inv({})", self.expr(a))
                } else {
                    format!("1 / {}", self.paren(a))
                }
            }
            PseudoInverse(a) => format!("pinv(full({}))", self.expr(a)),
            Solve(a, b) => format!("{} \\ {}", self.paren(a), self.paren(b)),
            Sqrt(a) => format!("sqrt({})", self.expr(a)),
            Norm { arg, kind, p } => {
                let x = self.expr(arg);
                match kind {
                    NormKind::P => match p {
                        None => format!("norm({x})"),
                        Some(p) if p.ty.is_matrix() => format!("sqrt(({x}).' * {} * ({x}))", self.expr(p)),
                        Some(p) => match &*p.kind {
                            ExprKind::Int(0) => format!("nnz({x})"),
                            _ => format!("norm({x}, {})", self.expr(p)),
                        },
                    },
                    NormKind::Max => format!("norm({x}, Inf)"),
                    NormKind::Frobenius => format!("norm(full({x}), 'fro')"),
                    NormKind::Nuclear => format!("sum(svd(full({x})))"),
                    NormKind::Abs => format!("abs({x})"),
                    NormKind::Det => format!("det({x})"),
                    NormKind::Size => format!("size({x}, 1)"),
                }
            }
            Call { callee, args } => self.call(callee, args),
            Block(rows) => {
                let r: Vec<String> = rows.iter().map(|row| format!("[{}]", row.iter().map(|x| self.expr(x)).collect::<Vec<_>>().join(", "))).collect();
                format!("[{}]", r.join("; "))
            }
            Stack(items) => format!("[{}]", items.iter().map(|x| self.expr(x)).collect::<Vec<_>>().join("; ")),
            Filled { value, rows, cols } => {
                let f = if *value == 0 { "zeros" } else { "ones" };
                match cols {
                    Some(c) => format!("{f}({}, {})", self.dim(rows), self.dim(c)),
                    None => format!("{f}({}, 1)", self.dim(rows)),
                }
            }
            Identity(d) => format!("eye({})", self.dim(d)),
            Sum { var, range, body, extras } => self.sum(var, range, body, extras, &e.ty),
            Piecewise { cases, otherwise } => self.piecewise(cases, otherwise.as_ref(), &e.ty),
            Integral { var, lo, hi, body } => {
                let b = self.expr(body);
                let v = m_ident(var);
                format!("integral(@(t) arrayfun(@({v}) {b}, t), {}, {}, 'AbsTol', 1e-14, 'RelTol', 1e-14)", self.expr(lo), self.expr(hi))
            }
            Optimize { kind, vars, objective, constraints, .. } => self.optimize(*kind, vars, objective, constraints, &e.ty),
            SetLit(items) => {
                let rows: Vec<String> = items
                    .iter()
                    .map(|x| match &*x.kind {
                        // a tuple literal is one row
                        ExprKind::Stack(parts) => parts.iter().map(|p| self.expr(p)).collect::<Vec<_>>().join(", "),
                        _ => self.expr(x),
                    })
                    .collect();
                format!("unique([{}], 'rows')", rows.join("; "))
            }
            Size(x) => format!("numel({})", self.expr(x)),
            Union { vars, range: SumRange::Set(range), body, .. } => {
                // (index values are 1-based in MATLAB: no offset)
                let acc = self.fresh("union");
                let set = self.expr(range);
                let k = self.fresh("row");
                self.line(format!("{acc} = zeros(0, 1);"));
                self.line(format!("for {k} = 1:size({set}, 1)"));
                self.indent += 1;
                for (c, v) in vars.iter().enumerate() {
                    self.line(format!("{} = {set}({k}, {});", m_ident(v), c + 1));
                }
                let b = self.expr(body);
                self.line(format!("{acc} = union({acc}, reshape({b}, [], 1));"));
                self.indent -= 1;
                self.line("end");
                acc
            }
            Union { vars, range, body, .. } => {
                let acc = self.fresh("union");
                let r = match range {
                    SumRange::Implicit(d) => format!("1:{}", self.dim(d)),
                    SumRange::Explicit(lo, hi) => format!("{}:{}", self.expr(lo), self.expr(hi)),
                    _ => unreachable!("the checker rejects conditional unions"),
                };
                self.line(format!("{acc} = zeros(0, 1);"));
                self.line(format!("for {} = {r}", m_ident(&vars[0])));
                self.indent += 1;
                let b = self.expr(body);
                self.line(format!("{acc} = union({acc}, reshape({b}, [], 1));"));
                self.indent -= 1;
                self.line("end");
                acc
            }
            MeshCall { .. } | SetOp(..) | Convert(_) | SetComp { .. } => "error('not supported by the MATLAB backend')".into(),
        }
    }

    fn call(&mut self, callee: &Callee, args: &[Expr]) -> String {
        let a: Vec<String> = args.iter().map(|x| self.expr(x)).collect();
        let a0 = a.first().cloned().unwrap_or_default();
        match callee {
            Callee::Builtin(f) => match f.as_str() {
                "sin" | "cos" | "tan" | "sinh" | "cosh" | "tanh" | "exp" | "sqrt" | "log2" | "log10" | "asin" | "acos" | "atan" | "asinh"
                | "acosh" | "atanh" | "cot" | "sec" | "csc" => format!("{f}({a0})"),
                "log" | "ln" => format!("log({a0})"),
                "atan2" => format!("atan2({a0}, {})", a[1]),
                "trace" => format!("trace({a0})"),
                "diag" => format!("diag({a0})"),
                "vec" => format!("reshape({a0}, [], 1)"),
                "det" => format!("det({a0})"),
                "rank" => format!("rank(full({a0}))"),
                "inv" => format!("inv({a0})"),
                "min" | "max" => {
                    if a.len() > 1 {
                        format!("{f}([{}])", a.join(", "))
                    } else {
                        format!("{f}({a0}(:))")
                    }
                }
                other => format!("{other}({})", a.join(", ")),
            },
            Callee::Named(n) => format!("{}({})", m_ident(n), a.join(", ")),
        }
    }

    fn zero_of(&self, ty: &Ty) -> String {
        match ty {
            Vector { rows, .. } => format!("zeros({}, 1)", self.dim(rows)),
            Matrix { rows, cols, .. } => format!("zeros({}, {})", self.dim(rows), self.dim(cols)),
            _ => "0".into(),
        }
    }

    fn sum(&mut self, var: &[String], range: &SumRange, body: &Expr, extras: &[Stmt], ty: &Ty) -> String {
        let acc = self.fresh("sum");
        let zero = self.zero_of(ty);
        self.line(format!("{acc} = {zero};"));
        let vars: Vec<String> = var.iter().map(|v| m_ident(v)).collect();
        let mut cond = None;
        match range {
            SumRange::Implicit(d) => {
                let d = self.dim(d);
                self.line(format!("for {} = 1:{d}", vars[0]));
            }
            SumRange::Cond(d, c) => {
                let d = self.dim(d);
                self.line(format!("for {} = 1:{d}", vars[0]));
                cond = Some(c);
            }
            SumRange::Explicit(lo, hi) => {
                let (l, h) = (self.expr(lo), self.expr(hi));
                self.line(format!("for {} = {l}:{h}", vars[0]));
            }
            SumRange::Set(s) => {
                let set = self.expr(s);
                let k = self.fresh("row");
                self.line(format!("for {k} = 1:size({set}, 1)"));
                self.indent += 1;
                if vars.len() == 1 {
                    self.line(format!("{} = {set}({k}, :);", vars[0]));
                } else {
                    for (c, v) in vars.iter().enumerate() {
                        self.line(format!("{v} = {set}({k}, {});", c + 1));
                    }
                }
                self.indent -= 1;
            }
        }
        self.indent += 1;
        if let Some(c) = cond {
            let c = self.cond(c);
            self.line(format!("if {c}"));
            self.indent += 1;
        }
        for s in extras {
            self.stmt(s);
        }
        let b = self.expr(body);
        self.line(format!("{acc} = {acc} + {b};"));
        if cond.is_some() {
            self.indent -= 1;
            self.line("end");
        }
        self.indent -= 1;
        self.line("end");
        acc
    }

    fn piecewise(&mut self, cases: &[(Cond, Expr)], otherwise: Option<&Expr>, ty: &Ty) -> String {
        let v = self.fresh("ret");
        self.line(format!("{v} = {};", self.zero_of(ty)));
        for (i, (c, e)) in cases.iter().enumerate() {
            let c = self.cond(c);
            self.line(format!("{} {c}", if i == 0 { "if" } else { "elseif" }));
            self.indent += 1;
            let x = self.expr(e);
            self.line(format!("{v} = {x};"));
            self.indent -= 1;
        }
        if let Some(o) = otherwise {
            self.line("else");
            self.indent += 1;
            let x = self.expr(o);
            self.line(format!("{v} = {x};"));
            self.indent -= 1;
        }
        self.line("end");
        v
    }

    fn cond(&mut self, c: &Cond) -> String {
        match c {
            Cond::Cmp(op, a, b) => {
                let o = match op {
                    CmpOp::Eq => "==",
                    CmpOp::Ne => "~=",
                    CmpOp::Lt => "<",
                    CmpOp::Le => "<=",
                    CmpOp::Gt => ">",
                    CmpOp::Ge => ">=",
                };
                format!("{} {o} {}", self.expr(a), self.expr(b))
            }
            Cond::In(items, s) | Cond::NotIn(items, s) => {
                let it: Vec<String> = items.iter().map(|x| self.expr(x)).collect();
                let set = self.expr(s);
                let test = format!("ismember([{}], {set}, 'rows')", it.join(", "));
                if matches!(c, Cond::NotIn(..)) {
                    format!("~{test}")
                } else {
                    test
                }
            }
            Cond::And(a, b) => format!("({}) && ({})", self.cond(a), self.cond(b)),
            Cond::Or(a, b) => format!("({}) || ({})", self.cond(a), self.cond(b)),
        }
    }

    /// Optimization: over a finite set, a search; over real values, `fminsearch`
    /// on the packed variables, with box bounds (constraints bounding a
    /// variable or an entry of one by a constant) by a change of variables.
    fn optimize(&mut self, kind: OptKind, vars: &[(String, Ty)], objective: &Expr, constraints: &[Cond], ty: &Ty) -> String {
        let res = self.fresh("opt");
        let maximize = matches!(kind, OptKind::Max | OptKind::Argmax);
        if let ([(v, Scalar(_))], [Cond::In(items, set)]) = (vars, constraints) {
            if items.len() == 1 && matches!(&*items[0].kind, ExprKind::Var(n) if n == v) {
                let s = self.expr(set);
                let var = m_ident(v);
                let obj = self.expr(objective);
                let (best, arg, k) = (self.fresh("best"), self.fresh("arg"), self.fresh("k"));
                let better = if maximize { ">" } else { "<" };
                self.line(format!("{best} = NaN; {arg} = NaN;"));
                self.line(format!("for {k} = 1:numel({s})"));
                self.line(format!("    {var} = {s}({k});"));
                let val = self.fresh("value");
                self.line(format!("    {val} = {obj};"));
                self.line(format!("    if isnan({best}) || {val} {better} {best}"));
                self.line(format!("        {best} = {val}; {arg} = {var};"));
                self.line("    end");
                self.line("end");
                let r = if matches!(kind, OptKind::Min | OptKind::Max) { best } else { arg };
                self.line(format!("{res} = {r};"));
                return res;
            }
        }
        // packed layout
        let mut layout = Vec::new();
        let mut offset = "0".to_string();
        for (v, t) in vars {
            let (r, c) = match t {
                Scalar(_) => ("1".to_string(), "1".to_string()),
                Vector { rows, .. } => (self.dim(rows), "1".to_string()),
                Matrix { rows, cols, .. } => (self.dim(rows), self.dim(cols)),
                _ => {
                    self.line(format!("error('optimization over this type is not supported'); {res} = 0;"));
                    return res;
                }
            };
            layout.push((v.clone(), offset.clone(), r.clone(), c.clone()));
            offset = format!("{offset} + ({r})*({c})");
        }
        let n = self.fresh("n");
        self.line(format!("{n} = {offset};"));
        let (lb, ub) = (self.fresh("lb"), self.fresh("ub"));
        self.line(format!("{lb} = -Inf({n}, 1); {ub} = Inf({n}, 1);"));
        for c in constraints {
            match self.bound(c, &layout) {
                Some((k, lower, value)) => {
                    if lower {
                        self.line(format!("{lb}({k}) = max({lb}({k}), {value});"));
                    } else {
                        self.line(format!("{ub}({k}) = min({ub}({k}), {value});"));
                    }
                }
                None => {
                    self.line("error('only constraints that bound a variable by a constant are supported by the MATLAB backend');");
                }
            }
        }
        // x(z): bounded components through a sine (both bounds) or a square (one bound)
        let map = self.fresh("tobox");
        let (zz, xx, mm) = (self.fresh("z"), self.fresh("x"), self.fresh("m"));
        self.line(format!("function {xx} = {map}({zz})"));
        self.line(format!("    {xx} = {zz};"));
        self.line(format!("    {mm} = isfinite({lb}) & isfinite({ub}); {xx}({mm}) = {lb}({mm}) + ({ub}({mm}) - {lb}({mm})) .* (sin({zz}({mm})) + 1) / 2;"));
        self.line(format!("    {mm} = isfinite({lb}) & ~isfinite({ub}); {xx}({mm}) = {lb}({mm}) + {zz}({mm}).^2;"));
        self.line(format!("    {mm} = ~isfinite({lb}) & isfinite({ub}); {xx}({mm}) = {ub}({mm}) - {zz}({mm}).^2;"));
        self.line("end");
        let obj_fn = self.fresh("objective");
        let xv = self.fresh("X");
        let val = self.fresh("value");
        let saved = std::mem::take(&mut self.lines);
        let unpack: Vec<String> = vars
            .iter()
            .zip(&layout)
            .map(|((v, t), (_, off, r, c))| match t {
                Scalar(_) => format!("{} = {xv}({off} + 1);", m_ident(v)),
                _ => format!("{} = reshape({xv}({off} + 1:{off} + ({r})*({c})), {r}, {c});", m_ident(v)),
            })
            .collect();
        let obj = self.expr(objective);
        let hoisted = std::mem::replace(&mut self.lines, saved);
        // the objective as a nested function (statements an expression needs go in it)
        let zp = self.fresh("z");
        self.line(format!("function {val} = {obj_fn}({zp})"));
        self.indent += 1;
        self.line(format!("{xv} = {map}({zp});"));
        for u in &unpack {
            self.line(u);
        }
        for h in hoisted {
            self.lines.push(format!("    {h}"));
        }
        let sign = if maximize { "-" } else { "" };
        self.line(format!("{val} = {sign}({obj});"));
        self.indent -= 1;
        self.line("end");
        let z = self.fresh("z");
        self.line(format!(
            "{z} = fminsearch(@{obj_fn}, zeros({n}, 1), optimset('TolX', 1e-12, 'TolFun', 1e-12, 'MaxFunEvals', 1e5, 'MaxIter', 1e5));"
        ));
        match kind {
            OptKind::Min | OptKind::Max => self.line(format!("{res} = {sign}{obj_fn}({z});")),
            _ => {
                let (_, off, r, c) = &layout[0];
                match &vars[0].1 {
                    Scalar(_) => self.line(format!("{res} = {map}({z}); {res} = {res}({off} + 1);")),
                    _ => self.line(format!("{res} = {map}({z}); {res} = reshape({res}({off} + 1:{off} + ({r})*({c})), {r}, {c});")),
                }
            }
        }
        let _ = ty;
        res
    }

    /// A constraint `v op c` (or `v_k op c`, `c op v`) as a box bound:
    /// (1-based index in the packed vector, lower?, value).
    fn bound(&mut self, c: &Cond, layout: &[(String, String, String, String)]) -> Option<(String, bool, String)> {
        let Cond::Cmp(op, a, b) = c else { return None };
        let constant = |e: &Expr| {
            matches!(&*e.kind, ExprKind::Int(_) | ExprKind::Real(_) | ExprKind::Fraction(..))
                || matches!(&*e.kind, ExprKind::Neg(x) if matches!(&*x.kind, ExprKind::Int(_) | ExprKind::Real(_)))
        };
        let slot = |e: &Expr| -> Option<String> {
            let k = |i: &Idx| match i {
                Idx::At(x) => match &*x.kind {
                    ExprKind::Int(v) => Some(*v),
                    _ => None,
                },
                Idx::All => None,
            };
            match &*e.kind {
                ExprKind::Var(n) => layout.iter().find(|l| &l.0 == n).filter(|l| l.2 == "1" && l.3 == "1").map(|l| format!("{} + 1", l.1)),
                ExprKind::Index { base, idx, .. } => {
                    let l = layout.iter().find(|l| &l.0 == base)?;
                    match idx.len() {
                        1 => Some(format!("{} + {}", l.1, k(&idx[0])?)),
                        // column-major, as reshape packs a matrix
                        2 => Some(format!("{} + {} + ({})*({})", l.1, k(&idx[0])?, k(&idx[1])? - 1, l.2)),
                        _ => None,
                    }
                }
                _ => None,
            }
        };
        let (k, gt_is_lower, value) = if let (Some(k), true) = (slot(a), constant(b)) {
            (k, true, self.expr(b))
        } else if let (Some(k), true) = (slot(b), constant(a)) {
            (k, false, self.expr(a))
        } else {
            return None;
        };
        let lower = match op {
            CmpOp::Gt | CmpOp::Ge => gt_is_lower,
            CmpOp::Lt | CmpOp::Le => !gt_is_lower,
            _ => return None,
        };
        Some((k, lower, value))
    }
}
