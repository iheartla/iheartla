//! Eigen (C++) backend.
//!
//! Generates a header with a struct `heartlib` (or the given name) whose
//! constructor takes the parameters in declaration order and computes every
//! defined symbol as a member; local functions become member functions.
//! Vectors and matrices with numeric sizes are fixed-size Eigen types, others
//! are dynamic (`Eigen::MatrixXd`); integer-valued ones store `int`, and
//! `conv` casts them where they meet real values. Sequences and sets are
//! `std::vector`s, functions `std::function`s.

use super::names::{convert_unicode, has_special_symbol, Kind};
use crate::ast::*;
use crate::dims::Dim;
use crate::ty::*;
use std::collections::HashSet;

const HEADER: &str = "#include <Eigen/Core>\n#include <Eigen/QR>\n#include <Eigen/Dense>\n#include <Eigen/Sparse>\n\
#include <Eigen/SVD>\n#include <iostream>\n#include <set>\n#include <vector>\n#include <tuple>\n#include <functional>\n\
#include <algorithm>\n#include <cmath>\n#include <stdexcept>\n\
#ifndef IHEARTLA_SORTED_SET\n#define IHEARTLA_SORTED_SET\n\
// sets are sorted vectors without duplicates (defined before the last #include:\n\
// code that wraps the generated code in a namespace starts it after that)\n\
template<typename T> std::vector<T> sorted_set(std::vector<T> v) { std::sort(v.begin(), v.end()); v.erase(std::unique(v.begin(), v.end()), v.end()); return v; }\n\
#endif\n\
#include <unsupported/Eigen/MatrixFunctions>\n";

pub fn generate(prog: &Program, struct_name: &str) -> String {
    let mut out = String::new();
    out.push_str(&format!("/*\n{}\n*/\n", prog.source.replace("*/", "* /")));
    out.push_str(HEADER);
    let mut kinds = Vec::new();
    mesh_kinds(prog, &mut kinds);
    if !kinds.is_empty() {
        for k in &kinds {
            out.push_str(&format!("#include \"{}.h\"\n", mesh_class(*k)));
        }
        out.push_str("#include \"MeshHelper.h\"\nusing namespace iheartmesh;\n");
    }
    out.push('\n');
    let body = structure(prog, struct_name);
    if body.contains("LBFGSpp::") {
        // (header-only: https://github.com/yixuan/LBFGSpp)
        out.push_str("#include <LBFGS.h>\n#include <LBFGSB.h>\n\n");
    }
    out.push_str(&body);
    out
}

/// The mesh kinds a program and the modules it imports use.
fn mesh_kinds(prog: &Program, out: &mut Vec<MeshKind>) {
    for (_, k) in &prog.meshes {
        if !out.contains(k) {
            out.push(*k);
        }
    }
    for m in &prog.modules {
        mesh_kinds(&m.prog, out);
    }
}

/// The runtime's C++ class for a mesh kind.
fn mesh_class(k: MeshKind) -> &'static str {
    match k {
        MeshKind::Edge => "EdgeMesh",
        MeshKind::Face => "FaceMesh",
        MeshKind::Cell => "CellMesh",
    }
}

/// A program as a struct; imported modules are nested structs, held as
/// members and constructed with the importer's arguments.
fn structure(prog: &Program, struct_name: &str) -> String {
    let mut g = Gen { prog, lines: Vec::new(), indent: 2, tmp: 0, locals: Vec::new() };
    let mut out = String::new();
    out.push_str(&format!("struct {struct_name} {{\n    using DT = double;\n"));
    let mut done = HashSet::new();
    for m in &prog.modules {
        if done.insert(m.name.clone()) {
            for l in structure(&m.prog, &m.name).lines() {
                out.push_str(&format!("    {l}\n"));
            }
        }
    }
    for m in &prog.modules {
        out.push_str(&format!("    {} _{};\n", m.name, m.name));
        // imported values are members; imported functions forward to the module
        let funcs: Vec<&String> = m.prog.funcs.iter().flat_map(|(_, l)| l.iter().map(|(_, n)| n)).collect();
        for (inner, here) in &m.syms {
            if funcs.contains(&inner) {
                out.push_str(&format!(
                    "    template<typename... Args> auto {}(Args&&... args) {{ return _{}.{}(std::forward<Args>(args)...); }}\n",
                    cpp_ident(here),
                    m.name,
                    cpp_ident(inner)
                ));
            } else if let Some((_, t)) = m.prog.defs.iter().find(|(n, _)| n == inner) {
                out.push_str(&format!("    {} {};\n", cpp_type(t), cpp_ident(here)));
            }
        }
    }
    // members: parameters and dimensions (used by member functions), definitions
    for p in &prog.params {
        out.push_str(&format!("    {} {};\n", cpp_type(&p.ty), cpp_ident(&p.name)));
    }
    for d in &prog.dims {
        out.push_str(&format!("    long {};\n", cpp_ident(&d.name)));
    }
    for (n, t) in &prog.defs {
        out.push_str(&format!("    {} {};\n", cpp_type(t), cpp_ident(n)));
    }
    let params: Vec<String> = prog
        .params
        .iter()
        .map(|p| format!("const {} & {}", cpp_type(&p.ty), cpp_ident(&p.name)))
        .collect();
    if !params.is_empty() {
        out.push_str(&format!("\n    {struct_name}() {{}}"));
    }
    out.push_str(&format!("\n    {struct_name}({})\n    {{\n", params.join(", ")));
    g.init_params();
    for m in &prog.modules {
        let args: Vec<String> = m.args.iter().map(|a| g.name(a)).collect();
        g.line(format!("this->_{} = {}({});", m.name, m.name, args.join(", ")));
        let funcs: Vec<&String> = m.prog.funcs.iter().flat_map(|(_, l)| l.iter().map(|(_, n)| n)).collect();
        for (inner, here) in &m.syms {
            if !funcs.contains(&inner) {
                g.line(format!("this->{} = this->_{}.{};", cpp_ident(here), m.name, cpp_ident(inner)));
            }
        }
    }
    let mut funcs = Vec::new();
    for s in &prog.stmts {
        match s {
            Stmt::Func(f) => funcs.push(f),
            s => g.stmt(s),
        }
    }
    out.push_str(&g.lines.join("\n"));
    out.push_str("\n    }\n");
    for f in funcs {
        out.push('\n');
        out.push_str(&g.local_func(f));
    }
    out.push_str("};\n");
    out
}

/// A C++ identifier for an I❤LA name.
pub fn cpp_ident(name: &str) -> String {
    let n = if name.contains('`') || has_special_symbol(name) {
        convert_unicode(Kind::Eigen, name).replace('-', "_")
    } else {
        name.to_string()
    };
    if crate::helper::is_keyword(&n, crate::helper::KeywordSet::Eigen) {
        return format!("{n}_");
    }
    n
}

fn fixed(d: &Dim) -> Option<i64> {
    d.as_int()
}

fn scalar(int: bool) -> &'static str {
    if int {
        "int"
    } else {
        "double"
    }
}

/// A dynamic-size matrix type.
fn dyn_matrix(int: bool) -> String {
    if int {
        "Eigen::Matrix<int, Eigen::Dynamic, Eigen::Dynamic>".into()
    } else {
        "Eigen::MatrixXd".into()
    }
}

/// The C++ type of a value of an I❤LA type.
pub fn cpp_type(t: &Ty) -> String {
    match t {
        Scalar(e) => (if e.is_int() { "int" } else { "double" }).into(),
        Vector { rows, elem } => match (fixed(rows), elem.is_int()) {
            (Some(r), int) => format!("Eigen::Matrix<{}, {r}, 1>", scalar(int)),
            (None, false) => "Eigen::VectorXd".into(),
            (None, true) => "Eigen::Matrix<int, Eigen::Dynamic, 1>".into(),
        },
        Matrix { sparse: true, elem, .. } => format!("Eigen::SparseMatrix<{}>", scalar(elem.is_int())),
        Matrix { rows, cols, elem, .. } => match (fixed(rows), fixed(cols)) {
            (Some(r), Some(c)) => format!("Eigen::Matrix<{}, {r}, {c}>", scalar(elem.is_int())),
            _ => dyn_matrix(elem.is_int()),
        },
        Seq { elem, .. } => format!("std::vector<{}>", cpp_type(elem)),
        Set { elems, .. } => {
            let el: Vec<&str> = elems.iter().map(|e| if e.is_int() { "int" } else { "double" }).collect();
            if el.len() == 1 {
                format!("std::vector<{}>", el[0])
            } else {
                format!("std::vector<std::tuple<{}>>", el.join(", "))
            }
        }
        Tuple(v) => format!("std::tuple<{}>", v.iter().map(cpp_type).collect::<Vec<_>>().join(", ")),
        Func { params, rets } => {
            let ret = if rets.len() == 1 { cpp_type(&rets[0]) } else { cpp_type(&Tuple(rets.clone())) };
            format!("std::function<{ret}({})>", params.iter().map(cpp_type).collect::<Vec<_>>().join(", "))
        }
        Mesh(k) => mesh_class(*k).into(),
    }
}

struct Gen<'p> {
    prog: &'p Program,
    lines: Vec<String>,
    indent: usize,
    tmp: usize,
    locals: Vec<HashSet<String>>,
}

impl<'p> Gen<'p> {
    fn line(&mut self, s: impl AsRef<str>) {
        self.lines.push(format!("{}{}", "    ".repeat(self.indent), s.as_ref()));
    }

    fn fresh(&mut self, base: &str) -> String {
        self.tmp += 1;
        format!("{base}_{}", self.tmp)
    }

    fn name(&self, n: &str) -> String {
        let id = cpp_ident(n);
        if self.locals.iter().any(|s| s.contains(n)) {
            return id;
        }
        format!("this->{id}")
    }

    fn dim(&self, d: &Dim) -> String {
        match d {
            Dim::Str(s) if s.starts_with("@mesh:") => {
                let parts: Vec<&str> = s.splitn(3, ':').collect();
                let f = match parts[2] {
                    "v" => "n_vertices",
                    "e" => "n_edges",
                    "f" => "n_faces",
                    _ => "n_tets",
                };
                format!("{}.{f}()", self.name(parts[1]))
            }
            Dim::Str(s) if s.starts_with("@len:") => {
                let parts: Vec<&str> = s.splitn(4, ':').collect();
                let item = match parts[2].parse::<i64>() {
                    Ok(i) => (i - 1).to_string(),
                    Err(_) => format!("{}-1", self.name(parts[2])),
                };
                let axis = if parts[3] == "0" { "rows" } else { "cols" };
                format!("{}.at({item}).{axis}()", self.name(parts[1]))
            }
            Dim::Str(s) if self.prog.dims.iter().any(|x| &x.name == s) || self.prog.params.iter().any(|p| &p.name == s) => {
                self.name(s)
            }
            Dim::Str(_) | Dim::Sym(_) => {
                let mut t = d.to_string();
                for dim in &self.prog.dims {
                    t = replace_word(&t, &dim.name, &format!("this->{}", cpp_ident(&dim.name)));
                }
                t
            }
            d => d.to_string(),
        }
    }

    fn init_params(&mut self) {
        let prog = self.prog;
        for p in &prog.params {
            let n = cpp_ident(&p.name);
            self.line(format!("this->{n} = {n};"));
        }
        for d in &prog.dims {
            let p = cpp_ident(&d.param);
            let ty = &prog.params.iter().find(|x| x.name == d.param).unwrap().ty;
            let src = match (ty, d.axis) {
                (Seq { .. }, 0) => format!("{p}.size()"),
                (Seq { .. }, 1) => format!("{p}[0].rows()"),
                (Seq { .. }, _) => format!("{p}[0].cols()"),
                (_, 0) => format!("{p}.rows()"),
                _ => format!("{p}.cols()"),
            };
            self.line(format!("this->{} = {src};", cpp_ident(&d.name)));
        }
        for p in &prog.params {
            let n = cpp_ident(&p.name);
            match &p.ty {
                Matrix { rows, cols, sparse: false, .. } if fixed(rows).is_none() || fixed(cols).is_none() => {
                    self.line(format!("assert( {n}.rows() == {} && {n}.cols() == {} );", self.dim(rows), self.dim(cols)));
                }
                Vector { rows, .. } if fixed(rows).is_none() => {
                    self.line(format!("assert( {n}.rows() == {} );", self.dim(rows)));
                }
                _ => {}
            }
        }
    }

    fn comment(&mut self, text: &str) {
        for l in text.lines() {
            self.line(format!("// {l}"));
        }
    }

    fn stmt(&mut self, s: &Stmt) {
        match s {
            Stmt::Assign(a) => {
                self.comment(&a.text);
                let target = self.name(&a.lhs);
                if self.locals.last().is_some_and(|l| l.contains(&a.lhs)) && a.subs.is_empty() && !a.accumulate {
                    let v = self.conv(&a.rhs, &a.ty);
                    self.line(format!("{} {} = {v};", cpp_type(&a.ty), cpp_ident(&a.lhs)));
                } else if a.subs.is_empty() {
                    let v = self.conv(&a.rhs, &a.ty);
                    let op = if a.accumulate { "+=" } else { "=" };
                    self.line(format!("{target} {op} {v};"));
                } else {
                    self.elementwise(a, &target);
                }
            }
            Stmt::Multi { lhs, rhs, text } => {
                self.comment(text);
                let v = self.expr(rhs);
                let tmp = self.fresh("tuple");
                self.line(format!("auto {tmp} = {v};"));
                for (k, (n, _)) in lhs.iter().enumerate() {
                    let target = self.name(n);
                    let item = match &rhs.ty {
                        Tuple(_) => format!("std::get<{k}>({tmp})"),
                        Vector { .. } => format!("{tmp}({k})"),
                        _ => format!("{tmp}.at({k})"),
                    };
                    // a local of a function body is declared here
                    if self.locals.last().is_some_and(|l| l.contains(n)) {
                        self.line(format!("{} {} = {item};", cpp_type(&lhs[k].1), cpp_ident(n)));
                    } else {
                        self.line(format!("{target} = {item};"));
                    }
                }
            }
            Stmt::Func(_) => {}
        }
    }

    fn elementwise(&mut self, a: &Assign, target: &str) {
        let subs: Vec<String> = a.subs.iter().map(|s| cpp_ident(s)).collect();
        let ext: Vec<String> = a.extents.iter().map(|d| self.dim(d)).collect();
        let fresh = !a.accumulate && !a.update;
        let mut write_to = target.to_string();
        match &a.ty {
            Vector { .. } => {
                if fresh {
                    self.line(format!("{target} = {}::Zero({});", cpp_type(&a.ty), ext[0]));
                }
            }
            Matrix { sparse, rows, cols, .. } => {
                if *sparse {
                    write_to = self.fresh("dense");
                    if fresh {
                        self.line(format!("Eigen::MatrixXd {write_to} = Eigen::MatrixXd::Zero({}, {});", self.dim(rows), self.dim(cols)));
                    } else {
                        self.line(format!("Eigen::MatrixXd {write_to} = Eigen::MatrixXd({target});"));
                    }
                } else if fresh {
                    self.line(format!("{target} = {}::Zero({}, {});", cpp_type(&a.ty), ext[0], ext[1]));
                }
            }
            Seq { .. } if !a.update => {
                self.line(format!("{target}.clear();"));
                self.line(format!("for(int {} = 1; {} <= {}; {}++){{", subs[0], subs[0], ext[0], subs[0]));
                self.indent += 1;
                self.locals.push(HashSet::from([a.subs[0].clone()]));
                let v = self.expr(&a.rhs);
                self.locals.pop();
                self.line(format!("{target}.push_back({v});"));
                self.indent -= 1;
                self.line("}");
                return;
            }
            _ => {}
        }
        self.locals.push(a.subs.iter().cloned().collect());
        let diag = a.subs.len() == 2 && a.subs[0] == a.subs[1];
        let loops = if diag { 1 } else { a.subs.len() };
        for k in 0..loops {
            self.line(format!("for(int {} = 1; {} <= {}; {}++){{", subs[k], subs[k], ext[k], subs[k]));
            self.indent += 1;
        }
        let v = self.expr(&a.rhs);
        let op = if a.accumulate { "+=" } else { "=" };
        let index: Vec<String> = subs.iter().map(|s| format!("{s}-1")).collect();
        let lhs = match &a.ty {
            Seq { .. } => format!("{write_to}.at({})", index[0]),
            _ => format!("{write_to}({})", index.join(", ")),
        };
        self.line(format!("{lhs} {op} {v};"));
        for _ in 0..loops {
            self.indent -= 1;
            self.line("}");
        }
        self.locals.pop();
        if write_to != target {
            self.line(format!("{target} = {write_to}.sparseView();"));
        }
    }

    fn local_func(&mut self, f: &LocalFunc) -> String {
        let saved = (std::mem::take(&mut self.lines), self.indent);
        self.indent = 2;
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
        self.locals.push(scope);
        for (p, set) in &f.checks {
            let set = self.name(set);
            self.line(format!("assert( std::binary_search({set}.begin(), {set}.end(), {}) );", cpp_ident(p)));
        }
        for s in &f.body {
            self.stmt(s);
        }
        let Func { rets, .. } = &f.ty else { unreachable!() };
        let v = if rets.len() == 1 { self.conv(&f.expr, &rets[0].clone()) } else { self.expr(&f.expr) };
        self.line(format!("return {v};"));
        self.locals.pop();
        let body = std::mem::replace(&mut self.lines, saved.0);
        self.indent = saved.1;
        let ret = if rets.len() == 1 { cpp_type(&rets[0]) } else { cpp_type(&Tuple(rets.clone())) };
        let params: Vec<String> = f.params.iter().map(|(n, t)| format!("const {} & {}", cpp_type(t), cpp_ident(n))).collect();
        format!("    {ret} {}({})\n    {{\n{}\n    }}\n", cpp_ident(&f.name), params.join(", "), body.join("\n"))
    }

    // -- expressions ---------------------------------------------------------

    fn index(&mut self, i: &Idx) -> String {
        match i {
            Idx::All => String::new(),
            Idx::At(e) if e.ty.elem().is_zero_based() => self.expr(e),
            Idx::At(e) => match &*e.kind {
                ExprKind::Int(v) => (v - 1).to_string(),
                _ => format!("{}-1", self.paren(e)),
            },
        }
    }

    /// An operand that needs parentheses.
    fn paren(&mut self, e: &Expr) -> String {
        let s = self.expr(e);
        match &*e.kind {
            ExprKind::Add(..) | ExprKind::Sub(..) | ExprKind::Neg(..) | ExprKind::Mul(..) | ExprKind::Div(..) => format!("({s})"),
            ExprKind::Int(v) if *v < 0 => format!("({s})"),
            _ => s,
        }
    }

    /// A dense (evaluated) value, for operations that need one.
    fn dense(&mut self, e: &Expr) -> String {
        let s = self.expr(e);
        match &e.ty {
            Matrix { sparse: true, .. } => format!("Eigen::MatrixXd({s})"),
            Matrix { .. } | Vector { .. } => format!("({s}).eval()"),
            _ => s,
        }
    }

    fn expr(&mut self, e: &Expr) -> String {
        use ExprKind::*;
        match &*e.kind {
            Int(v) => v.to_string(),
            Real(s) => s.clone(),
            Fraction(a, b) => format!("({a}/double({b}))"),
            Const(Constant::Pi) => "M_PI".into(),
            Const(Constant::E) => "M_E".into(),
            Const(Constant::Inf) => "std::numeric_limits<double>::infinity()".into(),
            Var(n) => self.name(n),
            Index { base, base_ty, idx } => {
                let b = self.name(base);
                let p: Vec<String> = idx.iter().map(|i| self.index(i)).collect();
                match base_ty {
                    Vector { .. } => format!("{b}({})", p[0]),
                    Matrix { sparse: true, .. } => format!("{b}.coeff({}, {})", p[0], p[1]),
                    Matrix { .. } => match (&idx[0], &idx[1]) {
                        (Idx::All, _) => format!("{b}.col({})", p[1]),
                        (_, Idx::All) => format!("{b}.row({}).transpose()", p[0]),
                        _ => format!("{b}({}, {})", p[0], p[1]),
                    },
                    Seq { elem, .. } => {
                        let item = format!("{b}.at({})", p[0]);
                        match (&**elem, p.len()) {
                            (_, 1) => item,
                            (Vector { .. }, 2) => format!("{item}({})", p[1]),
                            (Matrix { .. }, 3) => match (&idx[1], &idx[2]) {
                                (Idx::All, _) => format!("{item}.col({})", p[2]),
                                (_, Idx::All) => format!("{item}.row({})", p[1]),
                                _ => format!("{item}({}, {})", p[1], p[2]),
                            },
                            _ => item,
                        }
                    }
                    Tuple(_) => match &*match &idx[0] {
                        Idx::At(x) => x.kind.clone(),
                        Idx::All => Box::new(ExprKind::Int(1)),
                    } {
                        ExprKind::Int(k) => format!("std::get<{}>({b})", k - 1),
                        _ => b,
                    },
                    _ => format!("{b}.at({})", p[0]),
                }
            }
            Neg(x) => format!("-{}", self.paren(x)),
            Add(a, b) => {
                if a.ty.is_set() {
                    format!("set_union({}, {})", self.expr(a), self.expr(b))
                } else {
                    format!("{} + {}", self.conv(a, &e.ty), self.conv(b, &e.ty))
                }
            }
            Sub(a, b) => {
                let r = self.conv(b, &e.ty);
                let r = if matches!(&*b.kind, Add(..) | Sub(..) | Neg(..)) && !r.ends_with(".cast<double>()") { format!("({r})") } else { r };
                format!("{} - {r}", self.conv(a, &e.ty))
            }
            Mul(a, b) => {
                let (l, r) = (self.conv_paren(a, &e.ty), self.conv_paren(b, &e.ty));
                if e.ty.is_scalar() && !(a.ty.is_scalar() && b.ty.is_scalar()) {
                    format!("({l} * {r}).value()")
                } else {
                    format!("{l} * {r}")
                }
            }
            Div(a, b) => {
                if a.ty.is_int() && b.ty.is_int() && a.ty.is_scalar() && !e.ty.is_int() {
                    format!("double({}) / {}", self.expr(a), self.paren(b))
                } else {
                    format!("{} / {}", self.conv_paren(a, &e.ty), self.paren(b))
                }
            }
            Hadamard(a, b) => format!("({}).cwiseProduct({})", self.conv(a, &e.ty), self.conv(b, &e.ty)),
            Kronecker(a, b) => {
                let (l, r) = (self.dense(a), self.dense(b));
                let k = format!(
                    "[&](){{ Eigen::MatrixXd A = {l}; Eigen::MatrixXd B = {r}; Eigen::MatrixXd K(A.rows()*B.rows(), A.cols()*B.cols()); \
for(int i = 0; i < A.rows(); i++) for(int j = 0; j < A.cols(); j++) K.block(i*B.rows(), j*B.cols(), B.rows(), B.cols()) = A(i, j) * B; return K; }}()"
                );
                if e.ty.is_sparse() {
                    format!("Eigen::SparseMatrix<double>(({k}).sparseView())")
                } else {
                    k
                }
            }
            Cross(a, b) => {
                if a.ty.is_int() != b.ty.is_int() {
                    format!("({}).cross({})", self.conv(a, &e.ty), self.conv(b, &e.ty))
                } else {
                    format!("({}).cross({})", self.dense(a), self.dense(b))
                }
            }
            Dot(a, b) | Inner(a, b, None) => {
                if a.ty.is_int() != b.ty.is_int() {
                    format!("({}).dot({})", self.conv(a, &Ty::real()), self.conv(b, &Ty::real()))
                } else {
                    format!("({}).dot({})", self.dense(a), self.dense(b))
                }
            }
            Inner(a, b, Some(m)) => format!("(({}).transpose() * {} * {}).value()", self.dense(b), self.paren(m), self.paren(a)),
            Frobenius(a, b) => format!("({}).cwiseProduct({}).sum()", self.dense(a), self.dense(b)),
            Pow(a, b) => {
                if a.ty.is_matrix() {
                    format!("{}({}).pow({}).eval()", cpp_type(&a.ty), self.expr(a), self.expr(b))
                } else {
                    format!("pow({}, {})", self.expr(a), self.expr(b))
                }
            }
            Transpose(a) => format!("{}.transpose()", self.paren(a)),
            Inverse(a) => {
                if a.ty.is_matrix() {
                    format!("{}.inverse()", self.dense_paren(a))
                } else {
                    format!("1.0 / {}", self.paren(a))
                }
            }
            PseudoInverse(a) => format!("({}).completeOrthogonalDecomposition().pseudoInverse()", self.dense(a)),
            Solve(a, b) => format!("({}).colPivHouseholderQr().solve({})", self.dense(a), self.dense(b)),
            Sqrt(a) => format!("sqrt({})", self.expr(a)),
            Norm { arg, kind, p } => {
                let x = self.expr(arg);
                match kind {
                    NormKind::P => match p {
                        None => format!("({x}).norm()"),
                        Some(p) if p.ty.is_matrix() => {
                            let m = self.expr(p);
                            format!("sqrt((({x}).transpose() * {m} * ({x})).value())")
                        }
                        Some(p) => match &*p.kind {
                            ExprKind::Int(2) => format!("({x}).norm()"),
                            ExprKind::Int(0) => format!("double((({x}).array() != 0).count())"),
                            ExprKind::Int(k) => format!("({x}).lpNorm<{k}>()"),
                            _ => {
                                let pv = self.expr(p);
                                format!("pow(({x}).array().abs().pow({pv}).sum(), 1.0/{pv})")
                            }
                        },
                    },
                    NormKind::Max => format!("({x}).lpNorm<Eigen::Infinity>()"),
                    NormKind::Frobenius => format!("({x}).norm()"),
                    NormKind::Nuclear => format!("Eigen::JacobiSVD<Eigen::MatrixXd>({}).singularValues().sum()", self.dense(arg)),
                    NormKind::Abs => format!("fabs({x})"),
                    NormKind::Det => format!("({}).determinant()", self.dense(arg)),
                    NormKind::Size => format!("int(({x}).size())"),
                }
            }
            Call { callee, args } => self.call(callee, args, &e.ty),
            Block(rows) => self.block(rows, &e.ty),
            Stack(items) => {
                let parts: Vec<String> = items.iter().map(|x| self.conv(x, &e.ty)).collect();
                let t = cpp_type(&e.ty);
                format!("[&](){{ {t} v({}); v << {}; return v; }}()", self.dim(&e.ty.rows()), parts.join(", "))
            }
            Filled { value, rows, cols } => {
                let f = if *value == 0 { "Zero" } else { "Ones" };
                let t = cpp_type(&e.ty);
                match cols {
                    Some(c) => format!("{t}::{f}({}, {})", self.dim(rows), self.dim(c)),
                    None => format!("{t}::{f}({})", self.dim(rows)),
                }
            }
            Identity(d) => {
                let d = self.dim(d);
                format!("{}::Identity({d}, {d})", cpp_type(&e.ty))
            }
            Sum { var, range, body, extras } => self.sum(var, range, body, extras, &e.ty),
            Piecewise { cases, otherwise } => self.piecewise(cases, otherwise.as_ref(), &e.ty),
            Integral { var, lo, hi, body } => {
                // Gauss–Legendre quadrature (20 points on 20 subintervals)
                let (l, h) = (self.expr(lo), self.expr(hi));
                self.locals.push(HashSet::from([var.clone()]));
                let b = self.expr(body);
                self.locals.pop();
                let v = cpp_ident(var);
                format!(
                    "[&](){{ const double a = {l}, b = {h}; const double x5[5] = {{0.0, 0.5384693101056831, -0.5384693101056831, 0.9061798459386640, -0.9061798459386640}}; \
const double w5[5] = {{0.5688888888888889, 0.4786286704993665, 0.4786286704993665, 0.2369268850561891, 0.2369268850561891}}; \
double s = 0; const int n = 64; const double hh = (b - a) / n; for(int k = 0; k < n; k++){{ const double c = a + (k + 0.5) * hh; \
for(int q = 0; q < 5; q++){{ const double {v} = c + 0.5 * hh * x5[q]; s += 0.5 * hh * w5[q] * ({b}); }} }} return s; }}()"
                )
            }
            Optimize { kind, vars, objective, constraints, texts } => self.optimize(*kind, vars, objective, constraints, texts, &e.ty),
            SetLit(items) => {
                let parts: Vec<String> = items.iter().map(|x| self.expr(x)).collect();
                format!("sorted_set({}{{{}}})", cpp_type(&e.ty), parts.join(", "))
            }
            Size(x) => format!("int(({}).size())", self.expr(x)),
            MeshCall { func, mesh, args } => {
                let a: Vec<String> = args.iter().map(|x| self.expr(x)).collect();
                match func {
                    MeshFunc::ElementSets => format!("{}.ElementSets()", self.name(mesh)),
                    MeshFunc::BoundaryMatrices => format!("{}.BoundaryMatrices()", self.name(mesh)),
                    MeshFunc::UnsignedBoundaryMatrices => format!("{}.UnsignedBoundaryMatrices()", self.name(mesh)),
                    MeshFunc::NonZeros => format!("nonzeros(Eigen::SparseMatrix<int>({}))", a[0]),
                    MeshFunc::ValueSet => format!("[&](){{ auto s = ValueSet(Eigen::SparseMatrix<int>({}), {}); return std::vector<int>(s.begin(), s.end()); }}()", a[0], a[1]),
                    MeshFunc::IndicatorVector(k) => {
                        let n = self.dim(&Dim::Str(format!("@mesh:{mesh}:{}", crate::check::elem_letter(*k))));
                        format!("indicator({}, {n})", a[0])
                    }
                }
            }
            SetOp(k, a, b) => {
                let (l, r) = (self.expr(a), self.expr(b));
                let f = match k {
                    SetOpKind::Union => "std::set_union",
                    SetOpKind::Intersection => "std::set_intersection",
                    SetOpKind::Difference => "std::set_difference",
                };
                // (the operands are bound once: calls return new temporaries)
                format!(
                    "[&](){{ const auto l = {l}; const auto r = {r}; {} out; {f}(l.begin(), l.end(), r.begin(), r.end(), std::back_inserter(out)); return out; }}()",
                    cpp_type(&e.ty)
                )
            }
            Convert(args) => {
                let mut a: Vec<String> = args.iter().map(|x| self.expr(x)).collect();
                match &e.ty {
                    Tuple(ts) => {
                        // a CellularSet's missing sets are empty
                        while a.len() < ts.len() {
                            a.push(format!("{}()", cpp_type(&ts[a.len()])));
                        }
                        format!("{}({})", cpp_type(&e.ty), a.join(", "))
                    }
                    _ => a.remove(0),
                }
            }
            Union { vars, range, body, one_based } => {
                let r = self.expr(range);
                self.locals.push(vars.iter().cloned().collect());
                let b = self.expr(body);
                self.locals.pop();
                let bind = if vars.len() == 1 {
                    format!("const int {} = x{};", cpp_ident(&vars[0]), if one_based[0] { " + 1" } else { "" })
                } else {
                    vars.iter()
                        .enumerate()
                        .map(|(k, v)| format!("const int {} = std::get<{k}>(x){};", cpp_ident(v), if one_based[k] { " + 1" } else { "" }))
                        .collect::<Vec<_>>()
                        .join(" ")
                };
                let t = cpp_type(&e.ty);
                // (each term is bound once and sorted: it may be a call's new temporary)
                format!(
                    "[&](){{ const auto range = {r}; {t} acc; for(const auto & x : range){{ {bind} const {t} s = sorted_set({t}({b})); {t} u; \
std::set_union(acc.begin(), acc.end(), s.begin(), s.end(), std::back_inserter(u)); acc = u; }} return acc; }}()"
                )
            }
            SetComp { vars, range, cond, item } => {
                let r = self.expr(range);
                self.locals.push(vars.iter().cloned().collect());
                let it = self.expr(item);
                let c = cond.as_ref().map(|c| self.cond(c));
                self.locals.pop();
                let bind = if vars.len() == 1 {
                    format!("const auto & {} = x;", cpp_ident(&vars[0]))
                } else {
                    vars.iter().enumerate().map(|(k, v)| format!("const auto & {} = std::get<{k}>(x);", cpp_ident(v))).collect::<Vec<_>>().join(" ")
                };
                let push = match c {
                    Some(c) => format!("if({c}){{ out.push_back({it}); }}"),
                    None => format!("out.push_back({it});"),
                };
                format!(
                    "[&](){{ const auto range = {r}; {} out; for(const auto & x : range){{ {bind} {push} }} return sorted_set(out); }}()",
                    cpp_type(&e.ty)
                )
            }
        }
    }

    /// `e` as a value of a context of type `target`: integer vectors and
    /// matrices are cast where the context is real.
    fn conv(&mut self, e: &Expr, target: &Ty) -> String {
        let s = self.expr(e);
        if e.ty.is_int() && !target.is_int() && (e.ty.is_vector() || e.ty.is_matrix()) && !e.ty.is_sparse() {
            return format!("({s}).cast<double>()");
        }
        s
    }

    fn conv_paren(&mut self, e: &Expr, target: &Ty) -> String {
        if e.ty.is_int() && !target.is_int() && (e.ty.is_vector() || e.ty.is_matrix()) && !e.ty.is_sparse() {
            return self.conv(e, target);
        }
        self.paren(e)
    }

    fn dense_paren(&mut self, e: &Expr) -> String {
        match &e.ty {
            Matrix { sparse: true, .. } => format!("Eigen::MatrixXd({})", self.expr(e)),
            _ => format!("({})", self.expr(e)),
        }
    }

    fn call(&mut self, callee: &Callee, args: &[Expr], ty: &Ty) -> String {
        let a: Vec<String> = args.iter().map(|x| self.expr(x)).collect();
        let a0 = a.first().cloned().unwrap_or_default();
        let elementwise = |f: &str, x: &str, t: &Ty| -> String {
            if t.is_scalar() {
                format!("{f}({x})")
            } else {
                format!("({x}).array().{f}().matrix()")
            }
        };
        match callee {
            Callee::Builtin(f) => {
                let t0 = args.first().map(|x| x.ty.clone()).unwrap_or(Ty::real());
                match f.as_str() {
                    "sin" | "cos" | "tan" | "sinh" | "cosh" | "tanh" | "exp" | "sqrt" | "log" | "asin" | "acos" | "atan" | "log10" => {
                        elementwise(f, &a0, &t0)
                    }
                    "asinh" | "acosh" | "atanh" | "log2" => {
                        if t0.is_scalar() {
                            format!("{f}({a0})")
                        } else {
                            format!("({a0}).unaryExpr([](double v){{ return {f}(v); }}).eval()")
                        }
                    }
                    "ln" => elementwise("log", &a0, &t0),
                    "cot" | "sec" | "csc" => {
                        let base = match f.as_str() {
                            "cot" => "tan",
                            "sec" => "cos",
                            _ => "sin",
                        };
                        if t0.is_scalar() {
                            format!("1.0/{base}({a0})")
                        } else {
                            format!("({a0}).array().{base}().inverse().matrix()")
                        }
                    }
                    "atan2" => format!("atan2({a0}, {})", a[1]),
                    "trace" => format!("({a0}).trace()"),
                    "diag" => {
                        if t0.is_matrix() {
                            format!("Eigen::VectorXd(({a0}).diagonal())")
                        } else {
                            format!("Eigen::MatrixXd(({a0}).asDiagonal())")
                        }
                    }
                    "vec" => format!("[&](){{ Eigen::MatrixXd t = {a0}; return Eigen::VectorXd(Eigen::Map<Eigen::VectorXd>(t.data(), t.size())); }}()"),
                    "det" => format!("({}).determinant()", self.dense(&args[0])),
                    "rank" => format!("double(Eigen::FullPivLU<Eigen::MatrixXd>({}).rank())", self.dense(&args[0])),
                    "inv" => format!("({}).inverse()", self.dense(&args[0])),
                    "min" | "max" => {
                        if a.len() > 1 {
                            format!("std::{f}({{{}}})", a.iter().map(|x| format!("double({x})")).collect::<Vec<_>>().join(", "))
                        } else if t0.is_set() || t0.is_seq() {
                            format!("*std::{f}_element(({a0}).begin(), ({a0}).end())")
                        } else {
                            format!("({a0}).{f}Coeff()")
                        }
                    }
                    other => format!("{other}({})", a.join(", ")),
                }
            }
            Callee::Named(n) => {
                let _ = ty;
                // cast integer arguments to real parameters
                let a: Vec<String> = match self.func_params(n) {
                    Some(ps) if ps.len() == args.len() => args.iter().zip(&ps).map(|(x, t)| self.conv(x, t)).collect(),
                    _ => a,
                };
                format!("{}({})", self.name(n), a.join(", "))
            }
            Callee::SeqItem(n, i) => {
                let idx = self.index(&Idx::At(i.clone()));
                format!("{}.at({idx})({})", self.name(n), a.join(", "))
            }
        }
    }

    /// Parameter types of a local function or function-typed parameter.
    fn func_params(&self, n: &str) -> Option<Vec<Ty>> {
        let ty = self.prog.params.iter().find(|p| p.name == n).map(|p| &p.ty).or_else(|| {
            self.prog.stmts.iter().find_map(|s| match s {
                Stmt::Func(f) if f.name == n => Some(&f.ty),
                _ => None,
            })
        })?;
        match ty {
            Func { params, .. } => Some(params.clone()),
            _ => None,
        }
    }

    fn block(&mut self, rows: &[Vec<Expr>], ty: &Ty) -> String {
        let mut items = Vec::new();
        for row in rows {
            for e in row {
                items.push(if e.ty.is_sparse() { format!("Eigen::MatrixXd({})", self.expr(e)) } else { self.conv(e, ty) });
            }
        }
        let (r, c) = (self.dim(&ty.rows()), self.dim(&ty.cols()));
        let m = if ty.is_sparse() { "Eigen::MatrixXd".to_string() } else { dyn_matrix(ty.is_int()) };
        let body = format!("[&](){{ {m} m({r}, {c}); m << {}; return m; }}()", items.join(", "));
        if ty.is_sparse() {
            format!("Eigen::SparseMatrix<double>(({body}).sparseView())")
        } else {
            body
        }
    }

    fn zero_of(&self, ty: &Ty) -> String {
        match ty {
            Vector { rows, .. } => format!("{}::Zero({})", cpp_type(ty), self.dim(rows)),
            Matrix { rows, cols, sparse: false, .. } => format!("{}::Zero({}, {})", cpp_type(ty), self.dim(rows), self.dim(cols)),
            Matrix { rows, cols, .. } => format!("Eigen::SparseMatrix<double>({}, {})", self.dim(rows), self.dim(cols)),
            Scalar(e) if e.is_int() => "0".into(),
            _ => "0.0".into(),
        }
    }

    /// Emit a statement block as an immediately invoked lambda.
    fn lambda(&mut self, f: impl FnOnce(&mut Self)) -> String {
        let saved = (std::mem::take(&mut self.lines), self.indent);
        self.indent = 0;
        f(self);
        let body = std::mem::replace(&mut self.lines, saved.0);
        self.indent = saved.1;
        format!("[&](){{ {} }}()", body.join(" "))
    }

    fn sum(&mut self, var: &[String], range: &SumRange, body: &Expr, extras: &[Stmt], ty: &Ty) -> String {
        let ty = ty.clone();
        let zero = self.zero_of(&ty);
        let t = if ty.is_sparse() { "Eigen::SparseMatrix<double>".to_string() } else { cpp_type(&ty) };
        let vars: Vec<String> = var.iter().map(|v| cpp_ident(v)).collect();
        self.lambda(|g| {
            g.line(format!("{t} sum = {zero};"));
            let mut scope: HashSet<String> = var.iter().cloned().collect();
            for s in extras {
                if let Stmt::Assign(a) = s {
                    scope.insert(a.lhs.clone());
                }
            }
            g.locals.push(scope);
            let mut cond = None;
            match range {
                SumRange::Implicit(d) | SumRange::Cond(d, _) => {
                    let d = g.dim(d);
                    g.line(format!("for(int {v} = 1; {v} <= {d}; {v}++){{", v = vars[0]));
                    if let SumRange::Cond(_, c) = range {
                        cond = Some(c);
                    }
                }
                SumRange::Explicit(lo, hi) => {
                    let (l, h) = (g.expr(lo), g.expr(hi));
                    g.line(format!("for(int {v} = {l}; {v} <= {h}; {v}++){{", v = vars[0]));
                }
                SumRange::Set(s) => {
                    let s = g.expr(s);
                    g.line(format!("for(const auto & item : {s}){{"));
                    if vars.len() == 1 {
                        g.line(format!("auto {} = item;", vars[0]));
                    } else {
                        for (k, v) in vars.iter().enumerate() {
                            g.line(format!("auto {v} = std::get<{k}>(item);"));
                        }
                    }
                }
            }
            if let Some(c) = cond {
                let c = g.cond(c);
                g.line(format!("if({c}){{"));
            }
            for s in extras {
                g.stmt(s);
            }
            let b = g.conv(body, &ty);
            g.line(format!("sum += {b};"));
            if cond.is_some() {
                g.line("}");
            }
            g.line("}");
            g.line("return sum;");
            g.locals.pop();
        })
    }

    fn piecewise(&mut self, cases: &[(Cond, Expr)], otherwise: Option<&Expr>, ty: &Ty) -> String {
        let t = cpp_type(ty);
        let zero = self.zero_of(ty);
        self.lambda(|g| {
            for (i, (c, e)) in cases.iter().enumerate() {
                let c = g.cond(c);
                let x = g.conv(e, ty);
                g.line(format!("{}if({c}){{ return {t}({x}); }}", if i == 0 { "" } else { "else " }));
            }
            match otherwise {
                Some(o) => {
                    let x = g.conv(o, ty);
                    g.line(format!("return {t}({x});"));
                }
                None => g.line(format!("return {t}({zero});")),
            }
        })
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
                let index_set = matches!(&s.ty, Set { elems, .. } if elems.iter().any(|e| e.is_zero_based()));
                let it: Vec<String> = items
                    .iter()
                    .map(|x| if index_set && !x.ty.elem().is_zero_based() { format!("{}-1", self.paren(x)) } else { self.expr(x) })
                    .collect();
                let key = if it.len() == 1 { it[0].clone() } else { format!("std::make_tuple({})", it.join(", ")) };
                let set = self.expr(s);
                // bind the set once: a call returns a new temporary each time
                let found = format!("[&](){{ const auto & s = {set}; return std::find(s.begin(), s.end(), {key}) != s.end(); }}()");
                if matches!(c, Cond::NotIn(..)) {
                    format!("!{found}")
                } else {
                    found
                }
            }
            Cond::And(a, b) => format!("({}) && ({})", self.cond(a), self.cond(b)),
            Cond::Or(a, b) => format!("({}) || ({})", self.cond(a), self.cond(b)),
        }
    }

    fn optimize(&mut self, kind: OptKind, vars: &[(String, Ty)], objective: &Expr, constraints: &[Cond], texts: &[String], ty: &Ty) -> String {
        if let ([(v, Scalar(_))], [Cond::In(items, set)]) = (vars, constraints) {
            if items.len() == 1 && matches!(&*items[0].kind, ExprKind::Var(n) if n == v) {
                let s = self.expr(set);
                self.locals.push(HashSet::from([v.clone()]));
                let obj = self.expr(objective);
                self.locals.pop();
                let var = cpp_ident(v);
                let better = if matches!(kind, OptKind::Min | OptKind::Argmin) { "<" } else { ">" };
                let ret = if matches!(kind, OptKind::Min | OptKind::Max) { "best" } else { "arg" };
                return format!(
                    "[&](){{ bool first = true; double best = 0; double arg = 0; for(const auto & {var} : {s}){{ double f = {obj}; \
if(first || f {better} best){{ best = f; arg = {var}; first = false; }} }} return {}({ret}); }}()",
                    cpp_type(ty)
                );
            }
        }
        self.continuous_optimize(kind, vars, objective, constraints, texts, ty)
    }

    /// Minimization over real scalars, vectors and matrices with LBFGSpp:
    /// the variables are packed into one vector; gradients are central
    /// differences; constraints that bound a variable (or an entry of one) by
    /// a constant become box bounds (LBFGS-B). Other constraints are not
    /// supported (an exception at run time).
    fn continuous_optimize(&mut self, kind: OptKind, vars: &[(String, Ty)], objective: &Expr, constraints: &[Cond], texts: &[String], ty: &Ty) -> String {
        let rt = cpp_type(ty);
        // each variable's offset and size (as C++ expressions) in the packed vector
        let mut layout: Vec<(String, String, String, String)> = Vec::new(); // (name, offset, rows, cols)
        let mut offset = "0".to_string();
        for (v, t) in vars {
            let (r, c) = match t {
                Scalar(_) => ("1".to_string(), "1".to_string()),
                Vector { rows, .. } => (self.dim(rows), "1".to_string()),
                Matrix { rows, cols, .. } => (self.dim(rows), self.dim(cols)),
                _ => return format!("[&]() -> {rt} {{ throw std::runtime_error(\"optimization over this type is not supported\"); }}()"),
            };
            layout.push((v.clone(), offset.clone(), r.clone(), c.clone()));
            offset = format!("{offset} + ({r})*({c})");
        }
        let n = offset;
        // box bounds
        let mut bounds = Vec::new();
        for (k, c) in constraints.iter().enumerate() {
            match self.bound(c, &layout) {
                Some(b) => bounds.extend(b),
                None => {
                    let text = texts.get(k).map(|t| t.replace('\\', "\\\\").replace('"', "\\\"")).unwrap_or_default();
                    return format!(
                        "[&]() -> {rt} {{ throw std::runtime_error(\"I\\u2764\\ufe0fLA: in C++ output, optimization constraints must bound a variable \
(or an entry of one) by an expression without the variables; unsupported: {text}\"); }}()"
                    );
                }
            }
        }
        let sign = if matches!(kind, OptKind::Max | OptKind::Argmax) { "-" } else { "" };
        self.locals.push(vars.iter().map(|(v, _)| v.clone()).collect());
        let obj = self.conv(objective, &Ty::real());
        self.locals.pop();
        let unpack: Vec<String> = vars
            .iter()
            .zip(&layout)
            .map(|((v, t), (_, off, r, c))| match t {
                Scalar(_) => format!("const double {} = X({off});", cpp_ident(v)),
                _ => format!("const {} {} = Eigen::Map<const Eigen::MatrixXd>(X.data() + ({off}), {r}, {c});", cpp_type(&t.with_elem(Elem::Real)), cpp_ident(v)),
            })
            .collect();
        let objective_fn = format!("auto objective = [&](const Eigen::VectorXd & X) -> double {{ {} return {sign}(double({obj})); }};", unpack.join(" "));
        // (the best point evaluated is kept: the line search can fail near a
        // nonsmooth or exactly-zero minimum, and then that point is used)
        let grad_fn = "double best_f = std::numeric_limits<double>::infinity(); Eigen::VectorXd best_x; \
auto f = [&](const Eigen::VectorXd & X, Eigen::VectorXd & grad) -> double { Eigen::VectorXd Y = X; \
for(int k = 0; k < X.size(); k++){ const double h = 1e-6 * std::max(1.0, std::abs(X(k))); Y(k) = X(k) + h; const double fp = objective(Y); \
Y(k) = X(k) - h; const double fm = objective(Y); Y(k) = X(k); grad(k) = (fp - fm) / (2 * h); } \
const double value = objective(X); if(value < best_f){ best_f = value; best_x = X; } return value; };";
        let solve = if bounds.is_empty() {
            "LBFGSpp::LBFGSParam<double> param; param.epsilon = 1e-10; param.max_iterations = 1000; \
LBFGSpp::LBFGSSolver<double> solver(param); double fx; \
try { solver.minimize(f, x, fx); } catch(const std::runtime_error &) { if(best_x.size() == 0) throw; x = best_x; fx = best_f; }"
                .to_string()
        } else {
            let mut b = String::from("Eigen::VectorXd lb = Eigen::VectorXd::Constant(N, -std::numeric_limits<double>::infinity()); \
Eigen::VectorXd ub = Eigen::VectorXd::Constant(N, std::numeric_limits<double>::infinity()); ");
            for (k, lower, value) in &bounds {
                let (vec, f) = if *lower { ("lb", "max") } else { ("ub", "min") };
                b += &format!("{vec}({k}) = std::{f}({vec}({k}), double({value})); ");
            }
            b + "x = x.cwiseMax(lb).cwiseMin(ub); LBFGSpp::LBFGSBParam<double> param; param.epsilon = 1e-10; param.max_iterations = 1000; \
LBFGSpp::LBFGSBSolver<double> solver(param); double fx; \
try { solver.minimize(f, x, fx, lb, ub); } catch(const std::runtime_error &) { if(best_x.size() == 0) throw; x = best_x; fx = best_f; }"
        };
        let result = match kind {
            OptKind::Min | OptKind::Max => format!("return {sign}fx;"),
            _ => {
                let (v, t) = &vars[0];
                let (_, off, r, c) = &layout[0];
                let _ = v;
                match t {
                    Scalar(_) => format!("return x({off});"),
                    _ => format!("return {rt}(Eigen::Map<const Eigen::MatrixXd>(x.data() + ({off}), {r}, {c}));"),
                }
            }
        };
        format!("[&]() -> {rt} {{ const int N = {n}; {objective_fn} {grad_fn} Eigen::VectorXd x = Eigen::VectorXd::Zero(N); {solve} {result} }}()")
    }

    /// A constraint `v op c` (or `v_k op c`, `c op v`, `v = c`), where `c`
    /// doesn't involve the variables, as box bounds: (index in the packed
    /// vector, lower?, value) for each bound.
    fn bound(&mut self, c: &Cond, layout: &[(String, String, String, String)]) -> Option<Vec<(String, bool, String)>> {
        let Cond::Cmp(op, a, b) = c else { return None };
        let names: Vec<&String> = layout.iter().map(|l| &l.0).collect();
        let constant = |e: &Expr| e.ty.is_scalar() && !mentions(e, &names);
        let slot = |e: &Expr| -> Option<String> {
            match &*e.kind {
                ExprKind::Var(n) => layout.iter().find(|l| &l.0 == n).filter(|l| l.2 == "1" && l.3 == "1").map(|l| l.1.clone()),
                ExprKind::Index { base, idx, .. } => {
                    let l = layout.iter().find(|l| &l.0 == base)?;
                    let k = |i: &Idx| match i {
                        Idx::At(x) => match &*x.kind {
                            ExprKind::Int(v) => Some(v - 1),
                            _ => None,
                        },
                        Idx::All => None,
                    };
                    match idx.len() {
                        1 => Some(format!("({}) + {}", l.1, k(&idx[0])?)),
                        // column-major, as Eigen::Map packs a matrix
                        2 => Some(format!("({}) + {} + {}*({})", l.1, k(&idx[0])?, k(&idx[1])?, l.2)),
                        _ => None,
                    }
                }
                _ => None,
            }
        };
        let (k, lower_if_gt, value) = if let (Some(k), true) = (slot(a), constant(b)) {
            (k, true, self.expr(b))
        } else if let (Some(k), true) = (slot(b), constant(a)) {
            (k, false, self.expr(a))
        } else {
            return None;
        };
        // v > c, v >= c: a lower bound (strict bounds are closed); v = c: both
        Some(match op {
            CmpOp::Gt | CmpOp::Ge => vec![(k, lower_if_gt, value)],
            CmpOp::Lt | CmpOp::Le => vec![(k, !lower_if_gt, value)],
            CmpOp::Eq => vec![(k.clone(), true, value.clone()), (k, false, value)],
            CmpOp::Ne => return None,
        })
    }
}

/// Whether an expression uses any of the names (as variables or indexed).
fn mentions(e: &Expr, names: &[&String]) -> bool {
    use ExprKind::*;
    let any = |xs: &[&Expr]| xs.iter().any(|x| mentions(x, names));
    match &*e.kind {
        Var(n) => names.contains(&n),
        Index { base, idx, .. } => names.contains(&base) || idx.iter().any(|i| matches!(i, Idx::At(x) if mentions(x, names))),
        Int(_) | Real(_) | Fraction(..) | Const(_) | Filled { .. } | Identity(_) => false,
        Neg(a) | Transpose(a) | Inverse(a) | PseudoInverse(a) | Sqrt(a) | Size(a) => mentions(a, names),
        Add(a, b) | Sub(a, b) | Mul(a, b) | Div(a, b) | Hadamard(a, b) | Kronecker(a, b) | Cross(a, b) | Dot(a, b) | Frobenius(a, b)
        | Pow(a, b) | Solve(a, b) => any(&[a, b]),
        Norm { arg, .. } => mentions(arg, names),
        Call { args, .. } => args.iter().any(|x| mentions(x, names)),
        // (anything else: assume it may)
        _ => true,
    }
}

fn replace_word(text: &str, word: &str, with: &str) -> String {
    let re = regex::Regex::new(&format!(r"\b{}\b", regex::escape(word))).unwrap();
    re.replace_all(text, with).into_owned()
}
