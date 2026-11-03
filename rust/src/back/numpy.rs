//! NumPy backend.
//!
//! Generates a class `heartlib` (or the given name) whose constructor takes
//! the parameters in declaration order, checks their shapes, and computes
//! every defined symbol as an attribute; local functions become methods.
//! This is the interface of the Python compiler's NumPy output.

use super::names::{convert_unicode, has_special_symbol, Kind};
use crate::ast::*;
use crate::dims::Dim;
use crate::ty::*;
use std::collections::{HashMap, HashSet};

pub fn generate(prog: &Program, class_name: &str) -> String {
    let (include, class) = generate_parts(prog, class_name);
    format!("\"\"\"\n{}\n\"\"\"\n{include}{class}", prog.source)
}

/// The imports and the class (H❤️rtDown puts several programs' classes in one
/// file).
pub fn generate_parts(prog: &Program, class_name: &str) -> (String, String) {
    let mut out = String::new();
    // (derivatives with autograd, which differentiates through Python control flow)
    let np = if prog.derivatives { "import autograd.numpy as np\nimport autograd\n" } else { "import numpy as np\n" };
    out.push_str(np);
    out.push_str("import scipy\nimport scipy.linalg\nfrom scipy import sparse\n");
    out.push_str("from scipy.integrate import quad, solve_ivp\nfrom scipy.optimize import minimize\n");
    if uses_mesh(prog) {
        out.push_str("from triangle_mesh import *\n");
        if prog.derivatives {
            // (again: the star import brings NumPy's np)
            out.push_str("import autograd.numpy as np\n");
        }
    }
    out.push_str("\n\n");
    let mut code = class(prog, class_name);
    if prog.derivatives {
        // autograd differentiates np.array, not np.asarray
        code = code.replace("np.asarray(", "np.array(");
    }
    (out, code)
}

/// Whether a program or a module it imports uses meshes.
fn uses_mesh(prog: &Program) -> bool {
    !prog.meshes.is_empty() || prog.modules.iter().any(|m| uses_mesh(&m.prog))
}

/// A program as a class; imported modules are nested classes.
fn class(prog: &Program, class_name: &str) -> String {
    let mut g = Gen { prog, lines: Vec::new(), indent: 2, tmp: 0, method: false, locals: Vec::new(), subst: HashMap::new(), saw_partial: false };
    let mut out = String::new();
    out.push_str(&format!("class {class_name}:\n"));
    if prog.derivatives {
        out.push_str("    _differentiating = 0  # (> 0 while the program is recomputed for a derivative)\n\n");
    }
    let params: Vec<String> = prog.params.iter().map(|p| py_ident(&p.name)).collect();
    out.push_str(&format!("    def __init__(self{}):\n", params.iter().map(|p| format!(", {p}")).collect::<String>()));
    g.init_params();
    let mut funcs = Vec::new();
    for s in &prog.stmts {
        match s {
            Stmt::Func(f) => funcs.push(f),
            s => {
                let start = g.lines.len();
                g.saw_partial = false;
                g.stmt(s);
                if g.saw_partial {
                    // (not when the program is recomputed to differentiate it)
                    for l in &mut g.lines[start..] {
                        l.insert_str(0, "    ");
                    }
                    g.lines.insert(start, "        if not type(self)._differentiating:".into());
                }
            }
        }
    }
    if g.lines.is_empty() {
        g.line("pass");
    }
    out.push_str(&g.lines.join("\n"));
    out.push('\n');
    for f in funcs {
        out.push('\n');
        out.push_str(&g.local_func(f));
    }
    if prog.derivatives {
        for l in [
            "",
            "    def _without_derivatives(self, make):",
            "        \"\"\"make(), skipping the derivatives of every instance it constructs\"\"\"",
            "        type(self)._differentiating += 1",
            "        try:",
            "            return make()",
            "        finally:",
            "            type(self)._differentiating -= 1",
        ] {
            out.push_str(l);
            out.push('\n');
        }
    }
    // each imported module once (a module imported twice is instantiated twice)
    let mut done = HashSet::new();
    for m in &prog.modules {
        if done.insert(m.name.clone()) {
            out.push('\n');
            for l in class(&m.prog, &m.name).lines() {
                if l.is_empty() {
                    out.push('\n');
                } else {
                    out.push_str(&format!("    {l}\n"));
                }
            }
        }
    }
    out
}

/// A valid Python identifier for an I❤LA name.
pub fn py_ident(name: &str) -> String {
    let n = if name.contains('`') || has_special_symbol(name) { convert_unicode(Kind::Numpy, name).replace('-', "_") } else { name.to_string() };
    if crate::helper::is_keyword(&n, crate::helper::KeywordSet::Numpy) {
        return format!("{n}_");
    }
    n
}

struct Gen<'p> {
    prog: &'p Program,
    lines: Vec<String>,
    indent: usize,
    tmp: usize,
    /// inside a method (a local function): globals are attributes
    method: bool,
    /// local names (function parameters, loop variables, temporaries)
    locals: Vec<HashSet<String>>,
    /// names printed as other code (the variable a derivative is taken with respect to)
    subst: HashMap<String, String>,
    /// whether the statement being generated has a derivative
    saw_partial: bool,
}

impl<'p> Gen<'p> {
    fn line(&mut self, s: impl AsRef<str>) {
        self.lines.push(format!("{}{}", "    ".repeat(self.indent), s.as_ref()));
    }

    fn fresh(&mut self, base: &str) -> String {
        self.tmp += 1;
        format!("{base}_{}", self.tmp)
    }

    fn is_local(&self, n: &str) -> bool {
        self.locals.iter().any(|s| s.contains(n))
    }

    fn is_param(&self, n: &str) -> bool {
        self.prog.params.iter().any(|p| p.name == n)
    }

    fn is_dim(&self, n: &str) -> bool {
        self.prog.dims.iter().any(|d| d.name == n)
    }

    /// How to refer to a name here.
    fn name(&self, n: &str) -> String {
        if let Some(s) = self.subst.get(n) {
            return s.clone();
        }
        let id = py_ident(n);
        if self.is_local(n) {
            return id;
        }
        if (self.is_param(n) || self.is_dim(n)) && !self.method {
            return id;
        }
        format!("self.{id}")
    }

    fn dim(&self, d: &Dim) -> String {
        match d {
            Dim::Str(s) if s.starts_with("@size:") => format!("len({})", self.name(&s["@size:".len()..])),
            Dim::Str(s) if s.starts_with("@len:") => {
                // the extent of axis `a` of item `i` of a ragged sequence
                let parts: Vec<&str> = s.splitn(4, ':').collect();
                let item = match parts[2].parse::<i64>() {
                    Ok(i) => (i - 1).to_string(),
                    Err(_) => format!("{}-1", self.name(parts[2])),
                };
                format!("np.shape({}[{item}])[{}]", self.name(parts[1]), parts[3])
            }
            Dim::Str(s) if s.ends_with("[i]") => s.clone(),
            Dim::Str(s) if s.starts_with("@mesh:") => {
                // the number of elements of a kind in a mesh
                let parts: Vec<&str> = s.splitn(3, ':').collect();
                let f = match parts[2] {
                    "v" => "n_vertices",
                    "e" => "n_edges",
                    "f" => "n_faces",
                    _ => "n_tets",
                };
                format!("{}.{f}()", self.name(parts[1]))
            }
            Dim::Str(s) if self.is_dim(s) || self.is_param(s) || self.is_local(s) => self.name(s),
            Dim::Sym(_) | Dim::Str(_) => {
                // an expression of dimension symbols
                let mut t = d.to_string();
                if self.method {
                    for dim in &self.prog.dims {
                        t = replace_word(&t, &dim.name, &format!("self.{}", py_ident(&dim.name)));
                    }
                }
                t
            }
            d => d.to_string(),
        }
    }

    fn init_params(&mut self) {
        let prog = self.prog;
        let mut decls = Vec::new();
        let mut checks = Vec::new();
        for p in &prog.params {
            let n = py_ident(&p.name);
            let dtype = |t: &Ty| if t.is_int() { "np.int64" } else { "np.float64" };
            match &p.ty {
                Matrix { sparse: true, .. } => {}
                Matrix { rows, cols, .. } => {
                    decls.push(format!("{n} = np.asarray({n}, dtype={})", dtype(&p.ty)));
                    checks.push(format!("assert {n}.shape == ({}, {})", self.dim(rows), self.dim(cols)));
                }
                Vector { rows, .. } => {
                    decls.push(format!("{n} = np.asarray({n}, dtype={})", dtype(&p.ty)));
                    checks.push(format!("assert {n}.shape == ({},)", self.dim(rows)));
                }
                Seq { elem, .. } => {
                    let dynamic = matches!(elem.rows(), Dim::Str(ref s) if s.ends_with("[i]"))
                        || matches!(elem.cols(), Dim::Str(ref s) if s.ends_with("[i]"));
                    if elem.is_func() || elem.is_set() || elem.is_sparse() || dynamic {
                        decls.push(format!("{n} = list({n})"));
                    } else {
                        decls.push(format!("{n} = np.asarray({n}, dtype={})", dtype(elem)));
                    }
                }
                Scalar(_) => checks.push(format!("assert np.ndim({n}) == 0")),
                Set { .. } => decls.push(format!("{n} = frozenset({n})")),
                _ => {}
            }
        }
        for d in decls {
            self.line(d);
        }
        for d in &prog.dims {
            let p = py_ident(&d.param);
            let ty = &prog.params.iter().find(|x| x.name == d.param).unwrap().ty;
            let src = if ty.is_seq() && d.axis == 0 {
                format!("len({p})")
            } else if ty.is_seq() {
                format!("np.asarray({p}[0]).shape[{}]", d.axis - 1)
            } else {
                format!("{p}.shape[{}]", d.axis)
            };
            self.line(format!("{} = {src}", py_ident(&d.name)));
        }
        for c in checks {
            self.line(c);
        }
        // parameters and dimensions are also attributes (methods use them)
        for p in &prog.params {
            let n = py_ident(&p.name);
            self.line(format!("self.{n} = {n}"));
        }
        for d in &prog.dims {
            let n = py_ident(&d.name);
            self.line(format!("self.{n} = {n}"));
        }
        // imported modules: an instance each, with the imported symbols copied
        for m in &prog.modules {
            let inst = format!("_{}", m.name);
            let args: Vec<String> = m.args.iter().map(|a| self.name(a)).collect();
            self.line(format!("{inst} = self.{}({})", m.name, args.join(", ")));
            for (inner, here) in &m.syms {
                self.line(format!("self.{} = {inst}.{}", py_ident(here), py_ident(inner)));
            }
        }
    }

    fn comment(&mut self, text: &str) {
        let t: Vec<&str> = text.lines().collect();
        for l in t {
            self.line(format!("# {l}"));
        }
    }

    fn stmt(&mut self, s: &Stmt) {
        match s {
            Stmt::Assign(a) => {
                self.comment(&a.text);
                let target = self.name(&a.lhs);
                if a.subs.is_empty() {
                    let v = self.expr(&a.rhs);
                    let op = if a.accumulate { "+=" } else { "=" };
                    self.line(format!("{target} {op} {v}"));
                } else {
                    self.elementwise(a, &target);
                }
                if !self.method && self.is_local(&a.lhs) {
                    // a definition local to a function body
                }
            }
            Stmt::Multi { lhs, rhs, text } => {
                self.comment(text);
                let v = self.expr(rhs);
                let targets: Vec<String> = lhs.iter().map(|(n, _)| self.name(n)).collect();
                self.line(format!("{} = {v}", targets.join(", ")));
            }
            Stmt::Func(_) => {}
        }
    }

    fn elementwise(&mut self, a: &Assign, target: &str) {
        let subs: Vec<String> = a.subs.iter().map(|s| py_ident(s)).collect();
        let ext: Vec<String> = a.extents.iter().map(|d| self.dim(d)).collect();
        let fresh = !a.accumulate && !a.update;
        // sparse matrices are built densely and converted at the end
        let mut write_to = target.to_string();
        match &a.ty {
            Vector { .. } => {
                if fresh {
                    self.line(format!("{target} = np.zeros({})", ext[0]));
                }
            }
            Matrix { sparse, rows, cols, .. } => {
                if *sparse {
                    write_to = self.fresh("dense");
                    if fresh {
                        self.line(format!("{write_to} = np.zeros(({}, {}))", self.dim(rows), self.dim(cols)));
                    } else {
                        self.line(format!("{write_to} = np.asarray(sparse.csr_matrix({target}).toarray(), dtype=np.float64)"));
                    }
                } else if fresh {
                    self.line(format!("{target} = np.zeros(({}, {}))", ext[0], ext[1]));
                } else if a.update {
                    self.line(format!("{target} = np.array({target}, dtype=np.float64)"));
                }
            }
            Seq { .. } if a.update => {}
            _ => {
                let tmp = self.fresh("seq");
                self.locals.push(HashSet::from([a.subs[0].clone()]));
                self.line(format!("{tmp} = []"));
                self.line(format!("for {} in range(1, {}+1):", subs[0], ext[0]));
                self.indent += 1;
                let v = self.expr(&a.rhs);
                self.line(format!("{tmp}.append({v})"));
                self.indent -= 1;
                self.locals.pop();
                self.line(format!("{target} = np.asarray({tmp})"));
                return;
            }
        }
        let mut scope = HashSet::new();
        for s in &a.subs {
            scope.insert(s.clone());
        }
        self.locals.push(scope);
        let diag = a.subs.len() == 2 && a.subs[0] == a.subs[1];
        let loops = if diag { 1 } else { a.subs.len() };
        // (a row or column at a time: m_i,* = v_i)
        let mut opened = 0;
        for k in 0..loops {
            if a.subs[k] == "*" {
                continue;
            }
            self.line(format!("for {} in range(1, {}+1):", subs[k], ext[k]));
            self.indent += 1;
            opened += 1;
        }
        let loops = opened;
        let v = self.expr(&a.rhs);
        let v = if a.subs.iter().any(|s| s == "*") { format!("np.ravel({v})") } else { v };
        let index: Vec<String> = a.subs.iter().zip(&subs).map(|(raw, s)| if raw == "*" { ":".to_string() } else { format!("{s}-1") }).collect();
        let op = if a.accumulate { "+=" } else { "=" };
        self.line(format!("{write_to}[{}] {op} {v}", index.join(", ")));
        self.indent -= loops;
        self.locals.pop();
        if write_to != target {
            self.line(format!("{target} = sparse.csr_matrix({write_to})"));
        }
    }

    fn local_func(&mut self, f: &LocalFunc) -> String {
        let saved = (std::mem::take(&mut self.lines), self.indent, self.method);
        self.indent = 2;
        self.method = true;
        let mut scope: HashSet<String> = f.params.iter().map(|(n, _)| n.clone()).collect();
        for s in &f.body {
            match s {
                Stmt::Assign(a) => {
                    scope.insert(a.lhs.clone());
                }
                Stmt::Multi { lhs, .. } => {
                    for (n, _) in lhs {
                        scope.insert(n.clone());
                    }
                }
                _ => {}
            }
        }
        // (a sequence parameter's length, `U_n` for U_i ∈ ...)
        let lens: Vec<String> = f.params.iter().filter_map(|(_, t)| match t {
            Seq { size: Dim::Str(s), .. } => Some(s.clone()),
            _ => None,
        }).collect();
        scope.extend(lens.iter().cloned());
        self.locals.push(scope);
        for (n, t) in &f.params {
            if let Seq { size: Dim::Str(s), .. } = t {
                self.line(format!("{} = len({})", py_ident(s), py_ident(n)));
            }
        }
        for (n, t) in &f.params {
            let n = py_ident(n);
            if t.is_vector() || t.is_matrix() && !t.is_sparse() {
                let dtype = if t.is_int() { "np.int64" } else { "np.float64" };
                self.line(format!("{n} = np.asarray({n}, dtype={dtype})"));
            } else if t.is_scalar() && f.checks.iter().any(|(p, _)| py_ident(p) == n) {
                self.line(format!("assert np.ndim({n}) == 0"));
            } else if t.is_set() {
                self.line(format!("{n} = frozenset({n})"));
            }
        }
        for (p, set) in &f.checks {
            let set = self.name(set);
            self.line(format!("assert {} in {set}", py_ident(p)));
        }
        for s in &f.body {
            self.stmt(s);
        }
        let v = self.expr(&f.expr);
        self.line(format!("return {v}"));
        self.locals.pop();
        let body = std::mem::replace(&mut self.lines, saved.0);
        self.indent = saved.1;
        self.method = saved.2;
        let params: String = f.params.iter().map(|(n, _)| format!(", {}", py_ident(n))).collect();
        format!("    def {}(self{params}):\n{}\n", py_ident(&f.name), body.join("\n"))
    }

    // -- expressions ---------------------------------------------------------

    fn index(&mut self, i: &Idx) -> String {
        match i {
            Idx::All => ":".into(),
            // index-typed values are already 0-based
            Idx::At(e) if e.ty.elem().is_zero_based() => self.expr(e),
            Idx::At(e) => match &*e.kind {
                ExprKind::Int(v) => (v - 1).to_string(),
                _ => format!("{}-1", self.paren(e)),
            },
        }
    }

    fn expr(&mut self, e: &Expr) -> String {
        use ExprKind::*;
        match &*e.kind {
            Int(v) => v.to_string(),
            Real(s) => s.clone(),
            Fraction(a, b) => format!("({a}/{b})"),
            Const(Constant::Pi) => "np.pi".into(),
            Const(Constant::E) => "np.e".into(),
            Const(Constant::Inf) => "np.inf".into(),
            Var(n) => self.name(n),
            Index { base, base_ty, idx } => {
                let b = self.name(base);
                let parts: Vec<String> = idx.iter().map(|i| self.index(i)).collect();
                match base_ty {
                    Matrix { sparse: true, .. } => format!("{b}.tocsr()[{}]", parts.join(", ")),
                    Matrix { .. } => format!("{b}[{}]", parts.join(", ")),
                    Seq { elem, .. } if elem.is_matrix() && parts.len() == 3 => {
                        format!("{b}[{}][{}, {}]", parts[0], parts[1], parts[2])
                    }
                    Tuple(_) => format!("{b}[{}]", parts[0]),
                    // the i-th element of a set, in increasing order
                    Set { .. } => format!("sorted({b})[{}]", parts[0]),
                    VecSet { .. } => format!("np.asarray(sorted({b})[{}])", parts[0]),
                    _ => parts.iter().fold(b, |acc, p| format!("{acc}[{p}]")),
                }
            }
            MeshCall { func, mesh, args } => {
                let a: Vec<String> = args.iter().map(|x| self.expr(x)).collect();
                match func {
                    MeshFunc::ElementSets => format!("{}.ElementSets()", self.name(mesh)),
                    MeshFunc::BoundaryMatrices => format!("{}.BoundaryMatrices()", self.name(mesh)),
                    MeshFunc::UnsignedBoundaryMatrices => format!("{}.UnsignedBoundaryMatrices()", self.name(mesh)),
                    MeshFunc::NonZeros => format!("nonzeros({})", a[0]),
                    MeshFunc::ValueSet => format!("ValueSet({})", a.join(", ")),
                    MeshFunc::IndicatorVector(k) => {
                        let n = self.dim(&Dim::Str(format!("@mesh:{mesh}:{}", crate::check::elem_letter(*k))));
                        format!("indicator({}, {n})", a[0])
                    }
                }
            }
            SetOp(k, a, b) => {
                let (l, r) = (self.expr(a), self.expr(b));
                match k {
                    SetOpKind::Union => format!("frozenset.union({l}, {r})"),
                    SetOpKind::Intersection => format!("frozenset.intersection({l}, {r})"),
                    SetOpKind::Difference => format!("({l}) - ({r})"),
                }
            }
            Partial { upper, var, hessian, def } => {
                self.saw_partial = true;
                let x = self.name(var);
                let flat = !matches!(self.prog.params.iter().find(|p| p.name == *var).map(|p| &p.ty), Some(Scalar(_)));
                // the function of the (flattened) variable, as a nested def: its body may need statements
                let f = self.fresh("f");
                let dx = self.fresh("dx");
                let value = if flat { format!("np.reshape({dx}, np.shape({x}))") } else { dx.clone() };
                self.line(format!("def {f}({dx}):"));
                self.indent += 1;
                self.locals.push(HashSet::from([dx.clone()]));
                let body = match def {
                    // a definition of the program: the program recomputed with the variable replaced
                    Some(d) => {
                        let args: Vec<String> = self.prog.params.iter().map(|p| if p.name == *var { value.clone() } else { self.name(&p.name) }).collect();
                        format!("self._without_derivatives(lambda: type(self)({})).{}", args.join(", "), py_ident(d))
                    }
                    None => {
                        let saved = self.subst.insert(var.clone(), value.clone());
                        let b = self.expr(upper);
                        match saved {
                            Some(s) => self.subst.insert(var.clone(), s),
                            None => self.subst.remove(var),
                        };
                        b
                    }
                };
                self.line(format!("return {body}"));
                self.locals.pop();
                self.indent -= 1;
                let at = if flat { format!("np.ravel({x})") } else { x };
                let d = if *hessian {
                    "autograd.hessian"
                } else if upper.ty.is_vector() {
                    "autograd.jacobian"
                } else {
                    "autograd.grad"
                };
                // (the Hessian with respect to a scalar is a 0-d array)
                if *hessian && !flat { format!("float({d}({f})({at}))") } else { format!("{d}({f})({at})") }
            }
            Sequence { base, items } => {
                let a: Vec<String> = items.iter().map(|x| self.expr(x)).collect();
                match base {
                    // (a copy: the sequence itself is unchanged)
                    Some(b) => format!("list({}) + [{}]", self.expr(b), a.join(", ")),
                    None => format!("[{}]", a.join(", ")),
                }
            }
            Convert(args) => {
                let a: Vec<String> = args.iter().map(|x| self.expr(x)).collect();
                if a.len() == 1 && !e.ty.is_tuple() {
                    a[0].clone()
                } else {
                    // a CellularSet's missing sets are empty
                    let mut a = a;
                    if let Tuple(ts) = &e.ty {
                        while a.len() < ts.len() {
                            a.push("frozenset()".into());
                        }
                    }
                    format!("[{}]", a.join(", "))
                }
            }
            Union { vars, range, body, one_based } => {
                let acc = self.fresh("union");
                let items: Vec<String> = vars.iter().map(|v| py_ident(v)).collect();
                let target = if items.len() == 1 { items[0].clone() } else { format!("({})", items.join(", ")) };
                let r = match range {
                    SumRange::Set(r) => self.expr(r),
                    SumRange::Implicit(d) => format!("range(1, {}+1)", self.dim(d)),
                    SumRange::Explicit(lo, hi) => format!("range({}, {}+1)", self.expr(lo), self.expr(hi)),
                    SumRange::Cond(..) => unreachable!("the checker rejects conditional unions"),
                };
                self.line(format!("{acc} = frozenset()"));
                self.line(format!("for {target} in {r}:"));
                self.indent += 1;
                for (v, plus1) in items.iter().zip(one_based) {
                    if *plus1 {
                        self.line(format!("{v} = {v} + 1"));
                    }
                }
                self.locals.push(vars.iter().cloned().collect());
                let b = self.expr(body);
                self.locals.pop();
                self.line(format!("{acc} = {acc} | frozenset({b})"));
                self.indent -= 1;
                if let Some(s) = self.locals.last_mut() {
                    s.insert(acc.clone());
                } else {
                    self.locals.push(std::collections::HashSet::from([acc.clone()]));
                }
                acc
            }
            SetComp { vars, range, cond, item } => {
                let r = self.expr(range);
                self.locals.push(vars.iter().cloned().collect());
                let v: Vec<String> = vars.iter().map(|x| py_ident(x)).collect();
                let it = self.expr(item);
                let c = cond.as_ref().map(|c| format!(" if {}", self.cond(c))).unwrap_or_default();
                self.locals.pop();
                let target = if v.len() == 1 { v[0].clone() } else { format!("({})", v.join(", ")) };
                // (a vector is stored as a tuple: arrays aren't hashable)
                let it = if item.ty.is_vector() { format!("tuple(np.ravel({it}))") } else { it };
                format!("frozenset({{{it} for {target} in {r}{c}}})")
            }
            Neg(x) => format!("-{}", self.expr(x)),
            Add(a, b) => format!("{} + {}", self.expr(a), self.expr(b)),
            Sub(a, b) => {
                if a.ty.is_set() {
                    format!("{} - {}", self.expr(a), self.expr(b))
                } else {
                    format!("{} - {}", self.expr(a), self.paren(b))
                }
            }
            Mul(a, b) => self.mul(a, b, &e.ty),
            Div(a, b) => format!("{} / {}", self.paren(a), self.paren(b)),
            Hadamard(a, b) => format!("np.multiply({}, {})", self.expr(a), self.expr(b)),
            Kronecker(a, b) if e.ty.is_sparse() => format!("sparse.kron({}, {})", self.expr(a), self.expr(b)),
            Kronecker(a, b) => format!("np.kron({}, {})", self.expr(a), self.expr(b)),
            Cross(a, b) => format!("np.cross({}, {})", self.expr(a), self.expr(b)),
            Dot(a, b) => format!("np.dot(({}).ravel(), ({}).ravel())", self.expr(a), self.expr(b)),
            Inner(a, b, None) => format!("np.dot(({}).ravel(), ({}).ravel())", self.expr(a), self.expr(b)),
            Inner(a, b, Some(m)) => format!("({}).T @ ({}) @ ({})", self.expr(b), self.expr(m), self.expr(a)),
            Frobenius(a, b) => format!("np.sum(np.multiply({}, {}))", self.expr(a), self.expr(b)),
            Pow(a, b) => {
                // not **, which is elementwise for SciPy's sparse arrays (such as spsolve returns)
                if a.ty.is_matrix() && a.ty.is_sparse() {
                    format!("sparse.linalg.matrix_power({}, {})", self.expr(a), self.expr(b))
                } else if a.ty.is_matrix() {
                    format!("np.linalg.matrix_power({}, {})", self.expr(a), self.expr(b))
                } else {
                    format!("{}**{}", self.paren(a), self.paren(b))
                }
            }
            Transpose(a) => {
                if a.ty.is_vector() {
                    format!("({}).reshape(1, -1)", self.expr(a))
                } else {
                    format!("{}.T", self.paren(a))
                }
            }
            Inverse(a) => {
                if a.ty.is_matrix() {
                    if a.ty.is_sparse() {
                        format!("sparse.linalg.inv({})", self.expr(a))
                    } else {
                        format!("np.linalg.inv({})", self.expr(a))
                    }
                } else {
                    format!("1 / {}", self.paren(a))
                }
            }
            PseudoInverse(a) => format!("np.linalg.pinv({})", self.expr(a)),
            Solve(a, b) => {
                if a.ty.is_sparse() {
                    format!("sparse.linalg.spsolve({}, {})", self.expr(a), self.expr(b))
                } else {
                    format!("np.linalg.solve({}, {})", self.expr(a), self.expr(b))
                }
            }
            Sqrt(a) => format!("np.sqrt({})", self.expr(a)),
            Norm { arg, kind, p } => {
                let x = self.expr(arg);
                match kind {
                    NormKind::P => match p {
                        None => format!("np.linalg.norm({x}, 2)"),
                        Some(p) if p.ty.is_matrix() => format!("np.sqrt(({x}).T @ {} @ ({x}))", self.expr(p)),
                        Some(p) => format!("np.linalg.norm({x}, {})", self.expr(p)),
                    },
                    NormKind::Max => format!("np.linalg.norm({x}, np.inf)"),
                    NormKind::Frobenius => {
                        if arg.ty.is_sparse() {
                            format!("sparse.linalg.norm({x}, 'fro')")
                        } else {
                            format!("np.linalg.norm({x}, 'fro')")
                        }
                    }
                    NormKind::Nuclear => format!("np.linalg.norm({x}, 'nuc')"),
                    NormKind::Abs => format!("np.absolute({x})"),
                    NormKind::Det => format!("np.linalg.det({x})"),
                    NormKind::Size => format!("len({x})"),
                }
            }
            Call { callee, args } => self.call(callee, args),
            Block(rows) => self.block(rows, &e.ty),
            Stack(items) => {
                let parts: Vec<String> = items.iter().map(|x| self.expr(x)).collect();
                format!("np.hstack(({},))", parts.join(", "))
            }
            Filled { value, rows, cols } => {
                let f = if *value == 0 { "np.zeros" } else { "np.ones" };
                match cols {
                    Some(c) => format!("{f}(({}, {}))", self.dim(rows), self.dim(c)),
                    None => format!("{f}({})", self.dim(rows)),
                }
            }
            Identity(d) => format!("np.identity({})", self.dim(d)),
            Sum { var, range, body, extras } => self.sum(var, range, body, extras, &e.ty),
            Piecewise { cases, otherwise } => self.piecewise(cases, otherwise.as_ref(), &e.ty),
            Integral { var, lo, hi, body } => {
                self.locals.push(HashSet::from([var.clone()]));
                let b = self.expr(body);
                self.locals.pop();
                format!("quad(lambda {}: {b}, {}, {})[0]", py_ident(var), self.expr(lo), self.expr(hi))
            }
            Optimize { kind, vars, objective, constraints, .. } => self.optimize(*kind, vars, objective, constraints),
            SetLit(items) => {
                let parts: Vec<String> = items.iter().map(|x| self.expr(x)).collect();
                format!("frozenset({{{}}})", parts.join(", "))
            }
            Size(x) => {
                if x.ty.is_matrix() {
                    format!("{}.shape", self.expr(x))
                } else {
                    format!("len({})", self.expr(x))
                }
            }
        }
    }

    /// An operand that needs parentheses inside `*`, `/`, `**`, `-`.
    fn paren(&mut self, e: &Expr) -> String {
        let s = self.expr(e);
        match &*e.kind {
            ExprKind::Add(..) | ExprKind::Sub(..) | ExprKind::Neg(..) | ExprKind::Mul(..) | ExprKind::Div(..)
            | ExprKind::Pow(..) | ExprKind::Real(_) | ExprKind::Inverse(_) => format!("({s})"),
            ExprKind::Int(v) if *v < 0 => format!("({s})"),
            _ => s,
        }
    }

    fn mul(&mut self, a: &Expr, b: &Expr, ty: &Ty) -> String {
        if a.ty.is_scalar() || b.ty.is_scalar() {
            return format!("{} * {}", self.paren(a), self.paren(b));
        }
        let mut l = self.paren(a);
        let r = self.paren(b);
        if a.ty.is_vector() {
            // a column vector times a row
            l = format!("({l}).reshape(-1, 1)");
        }
        if ty.is_scalar() {
            return format!("np.asarray({l} @ {r}).item()");
        }
        format!("{l} @ {r}")
    }

    fn call(&mut self, callee: &Callee, args: &[Expr]) -> String {
        let a: Vec<String> = args.iter().map(|x| self.expr(x)).collect();
        let a0 = a.first().cloned().unwrap_or_default();
        match callee {
            Callee::Builtin(f) => match f.as_str() {
                "sin" | "cos" | "tan" | "sinh" | "cosh" | "tanh" | "exp" | "sqrt" | "log2" | "log10" => format!("np.{f}({a0})"),
                "asin" | "acos" | "atan" | "asinh" | "acosh" | "atanh" => format!("np.arc{}({a0})", &f[1..]),
                "log" | "ln" => format!("np.log({a0})"),
                "cot" => format!("1/np.tan({a0})"),
                "sec" => format!("1/np.cos({a0})"),
                "csc" => format!("1/np.sin({a0})"),
                "atan2" => format!("np.arctan2({a0}, {})", a[1]),
                "trace" => format!("np.trace({a0})"),
                "diag" => format!("np.diag({a0})"),
                "vec" => format!("np.asarray({a0}).ravel(order='F')"),
                "det" => format!("np.linalg.det({a0})"),
                "rank" => format!("np.linalg.matrix_rank({a0})"),
                "inv" => format!("np.linalg.inv({a0})"),
                // (U, the singular values, V: NumPy gives Vᵀ)
                "svd" => format!("(lambda s: (s[0], s[1], s[2].T))(np.linalg.svd({a0}))"),
                "min" | "max" => {
                    if a.len() > 1 {
                        format!("{f}({})", a.join(", "))
                    } else if args[0].ty.is_set() {
                        format!("{f}({a0})")
                    } else {
                        format!("np.{f}({a0})")
                    }
                }
                other => format!("{other}({})", a.join(", ")),
            },
            Callee::Named(n) => format!("{}({})", self.name(n), a.join(", ")),
        }
    }

    fn block(&mut self, rows: &[Vec<Expr>], ty: &Ty) -> String {
        let all_scalar = rows.iter().flatten().all(|e| e.ty.is_scalar());
        if self.prog.derivatives && !all_scalar && !ty.is_sparse() && !ty.is_int() {
            // autograd differentiates np.concatenate, not np.block (each item 2-D)
            let mut parts = Vec::new();
            for row in rows {
                let items: Vec<String> = row
                    .iter()
                    .map(|e| {
                        let s = self.expr(e);
                        match &e.ty {
                            Scalar(_) => format!("np.reshape({s}, (1, 1))"),
                            Vector { .. } => format!("np.reshape({s}, (-1, 1))"),
                            Matrix { sparse: true, .. } => format!("({s}).toarray()"),
                            _ => s,
                        }
                    })
                    .collect();
                parts.push(format!("np.concatenate([{}], axis=1)", items.join(", ")));
            }
            return format!("np.concatenate([{}], axis=0)", parts.join(", "));
        }
        let mut parts = Vec::new();
        for row in rows {
            let items: Vec<String> = row
                .iter()
                .map(|e| {
                    let s = self.expr(e);
                    if e.ty.is_scalar() && ty.is_sparse() {
                        format!("np.array([[{s}]])")
                    } else if e.ty.is_vector() {
                        format!("({s}).reshape(-1, 1)")
                    } else if e.ty.is_sparse() {
                        format!("({s}).toarray()")
                    } else {
                        s
                    }
                })
                .collect();
            parts.push(format!("[{}]", items.join(", ")));
        }
        let elem = if ty.is_int() { "np.int64" } else { "np.float64" };
        if ty.is_sparse() {
            return format!("sparse.bmat([{}])", parts.join(", ").replace(".toarray()", ""));
        }
        if all_scalar {
            format!("np.array([{}], dtype={elem})", parts.join(", "))
        } else {
            format!("np.block([{}]).astype({elem})", parts.join(", "))
        }
    }

    fn zero_of(&self, ty: &Ty) -> String {
        match ty {
            Vector { rows, .. } => format!("np.zeros({})", self.dim(rows)),
            Matrix { rows, cols, .. } => format!("np.zeros(({}, {}))", self.dim(rows), self.dim(cols)),
            _ => "0".into(),
        }
    }

    fn sum(&mut self, var: &[String], range: &SumRange, body: &Expr, extras: &[Stmt], ty: &Ty) -> String {
        let acc = self.fresh("sum");
        let zero = self.zero_of(ty);
        self.line(format!("{acc} = {zero}"));
        let vars: Vec<String> = var.iter().map(|v| py_ident(v)).collect();
        let mut scope: HashSet<String> = var.iter().cloned().collect();
        for s in extras {
            match s {
                Stmt::Assign(a) => {
                    scope.insert(a.lhs.clone());
                }
                // (j, k = ...: a destructuring in the sum)
                Stmt::Multi { lhs, .. } => scope.extend(lhs.iter().map(|(n, _)| n.clone())),
                _ => {}
            }
        }
        self.locals.push(scope);
        let mut cond = None;
        match range {
            SumRange::Implicit(d) => {
                let d = self.dim(d);
                self.line(format!("for {} in range(1, {d}+1):", vars[0]));
            }
            SumRange::Cond(d, c) => {
                let d = self.dim(d);
                self.line(format!("for {} in range(1, {d}+1):", vars[0]));
                cond = Some(c);
            }
            SumRange::Explicit(lo, hi) => {
                let (l, h) = (self.expr(lo), self.expr(hi));
                self.line(format!("for {} in range({l}, {h}+1):", vars[0]));
            }
            SumRange::Set(s) => {
                let s = self.expr(s);
                let target = if vars.len() == 1 { vars[0].clone() } else { format!("({})", vars.join(", ")) };
                self.line(format!("for {target} in {s}:"));
            }
        }
        self.indent += 1;
        if let Some(c) = cond {
            let c = self.cond(c);
            self.line(format!("if {c}:"));
            self.indent += 1;
        }
        for s in extras {
            self.stmt(s);
        }
        let b = self.expr(body);
        self.line(format!("{acc} += {b}"));
        if cond.is_some() {
            self.indent -= 1;
        }
        self.indent -= 1;
        self.locals.pop();
        self.locals.push(HashSet::from([acc.clone()]));
        // keep the temporary local for the rest of this statement
        let _ = self.locals.pop();
        self.locals.last_mut().map(|s| s.insert(acc.clone()));
        if self.locals.is_empty() {
            self.locals.push(HashSet::from([acc.clone()]));
        }
        acc
    }

    fn piecewise(&mut self, cases: &[(Cond, Expr)], otherwise: Option<&Expr>, ty: &Ty) -> String {
        let v = self.fresh("ret");
        self.line(format!("{v} = {}", self.zero_of(ty)));
        for (i, (c, e)) in cases.iter().enumerate() {
            let c = self.cond(c);
            self.line(format!("{} {c}:", if i == 0 { "if" } else { "elif" }));
            self.indent += 1;
            let x = self.expr(e);
            self.line(format!("{v} = {x}"));
            self.indent -= 1;
        }
        if let Some(o) = otherwise {
            self.line("else:");
            self.indent += 1;
            let x = self.expr(o);
            self.line(format!("{v} = {x}"));
            self.indent -= 1;
        }
        match self.locals.last_mut() {
            Some(s) => {
                s.insert(v.clone());
            }
            None => self.locals.push(HashSet::from([v.clone()])),
        }
        v
    }

    fn cond(&mut self, c: &Cond) -> String {
        match c {
            Cond::Cmp(op, a, b) => {
                let o = match op {
                    CmpOp::Eq => "==",
                    CmpOp::Ne => "!=",
                    CmpOp::Lt => "<",
                    CmpOp::Le => "<=",
                    CmpOp::Gt => ">",
                    CmpOp::Ge => ">=",
                };
                format!("{} {o} {}", self.expr(a), self.expr(b))
            }
            Cond::In(items, s) | Cond::NotIn(items, s) => {
                // an index set stores 0-based indices
                let index_set = matches!(&s.ty, Set { elems, .. } if elems.iter().any(|e| e.is_zero_based()));
                let it: Vec<String> = items
                    .iter()
                    .map(|x| {
                        if index_set && !x.ty.elem().is_zero_based() {
                            format!("{}-1", self.paren(x))
                        } else {
                            self.expr(x)
                        }
                    })
                    .collect();
                let lhs = if it.len() == 1 { it[0].clone() } else { format!("({})", it.join(", ")) };
                let neg = if matches!(c, Cond::NotIn(..)) { "not in" } else { "in" };
                format!("{lhs} {neg} {}", self.expr(s))
            }
            Cond::And(a, b) => format!("({}) and ({})", self.cond(a), self.cond(b)),
            Cond::Or(a, b) => format!("({}) or ({})", self.cond(a), self.cond(b)),
        }
    }

    fn optimize(&mut self, kind: OptKind, vars: &[(String, Ty)], objective: &Expr, constraints: &[Cond]) -> String {
        // one scalar variable restricted to a finite set: search the set
        if let ([(v, Scalar(_))], [Cond::In(items, set)]) = (vars, constraints) {
            if items.len() == 1 && matches!(&*items[0].kind, ExprKind::Var(n) if n == v) {
                let s = self.expr(set);
                self.locals.push(HashSet::from([v.clone()]));
                let obj = self.expr(objective);
                self.locals.pop();
                let var = py_ident(v);
                return match kind {
                    OptKind::Min => format!("min({obj} for {var} in {s})"),
                    OptKind::Max => format!("max({obj} for {var} in {s})"),
                    OptKind::Argmin => format!("min({s}, key=lambda {var}: {obj})"),
                    OptKind::Argmax => format!("max({s}, key=lambda {var}: {obj})"),
                };
            }
        }
        // pack all variables into one vector for scipy.optimize.minimize
        let x = self.fresh("x");
        let mut sizes = Vec::new();
        let mut unpack = Vec::new();
        let mut offset = String::from("0");
        for (n, t) in vars {
            let size = match t {
                Vector { rows, .. } => self.dim(rows),
                Matrix { rows, cols, .. } => format!("({})*({})", self.dim(rows), self.dim(cols)),
                _ => "1".into(),
            };
            let slice = format!("{x}[{offset}:{offset}+{size}]");
            let val = match t {
                Vector { .. } => slice,
                Matrix { rows, cols, .. } => format!("{slice}.reshape(({}, {}))", self.dim(rows), self.dim(cols)),
                _ => format!("{x}[{offset}]"),
            };
            unpack.push((py_ident(n), val));
            offset = format!("{offset}+{size}");
            sizes.push(size);
        }
        let f = self.fresh("objective");
        self.line(format!("def {f}({x}):"));
        self.indent += 1;
        self.locals.push(vars.iter().map(|(n, _)| n.clone()).collect());
        for (n, v) in &unpack {
            self.line(format!("{n} = {v}"));
        }
        let obj = self.expr(objective);
        let sign = if matches!(kind, OptKind::Max | OptKind::Argmax) { "-" } else { "" };
        self.line(format!("return {sign}({obj})"));
        self.indent -= 1;
        let mut cons = Vec::new();
        for (k, c) in constraints.iter().enumerate() {
            let cf = format!("{f}_c{k}");
            self.line(format!("def {cf}({x}):"));
            self.indent += 1;
            for (n, v) in &unpack {
                self.line(format!("{n} = {v}"));
            }
            let (kind, body) = match c {
                Cond::Cmp(op, a, b) => {
                    let (a, b) = (self.expr(a), self.expr(b));
                    match op {
                        CmpOp::Eq => ("eq", format!("{a} - ({b})")),
                        CmpOp::Ge | CmpOp::Gt => ("ineq", format!("{a} - ({b})")),
                        _ => ("ineq", format!("{b} - ({a})")),
                    }
                }
                _ => ("ineq", "0".into()),
            };
            self.line(format!("return {body}"));
            self.indent -= 1;
            cons.push(format!("{{'type': '{kind}', 'fun': {cf}}}"));
        }
        self.locals.pop();
        let total = sizes.join("+");
        let res = self.fresh("res");
        let cons_arg = if cons.is_empty() { String::new() } else { format!(", constraints=[{}]", cons.join(", ")) };
        self.line(format!("{res} = minimize({f}, np.zeros({total}){cons_arg})"));
        // the minimizer is an attribute too (`min_(c ∈ ℝ^m) …`: .c), as in the Python compiler's output
        if !self.method {
            for ((n, _), (name, v)) in vars.iter().zip(&unpack) {
                if !self.is_param(n) && !self.prog.defs.iter().any(|(d, _)| d == n) {
                    self.line(format!("self.{name} = {}", v.replace(&x, &format!("{res}.x"))));
                }
            }
        }
        let ret = match kind {
            OptKind::Min => format!("{res}.fun"),
            OptKind::Max => format!("-{res}.fun"),
            _ => {
                if unpack.len() == 1 {
                    unpack[0].1.replace(&x, &format!("{res}.x"))
                } else {
                    let parts: Vec<String> = unpack.iter().map(|(_, v)| v.replace(&x, &format!("{res}.x"))).collect();
                    format!("({})", parts.join(", "))
                }
            }
        };
        if let Some(s) = self.locals.last_mut() {
            s.insert(res.clone());
        } else {
            self.locals.push(HashSet::from([res.clone(), f.clone()]));
        }
        ret
    }
}

fn replace_word(text: &str, word: &str, with: &str) -> String {
    let re = regex::Regex::new(&format!(r"\b{}\b", regex::escape(word))).unwrap();
    re.replace_all(text, with).into_owned()
}
