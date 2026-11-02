//! `generateRandomData()` and `main()` for the code backends (the Python
//! compiler's output with `class_only=False`): random arguments of the
//! parameters' types, and a main that calls `heartlib` with them and prints
//! the result.
//!
//! Dimensions are random in 1..=9; all sequences get the same length, in
//! 4..=9 (the typed program doesn't record which sequences share a
//! subscript; programs use items 1, 2, 3 by number), or a mesh's vertex
//! count; integer
//! values are in 0..=9, and `index` set values are below the smallest
//! dimension (0-based, 1-based in MATLAB). A mesh parameter is an octahedron
//! (NumPy and Eigen; it needs the I❤️MESH runtime).

use super::eigen::{cpp_ident, cpp_type};
use super::matlab::m_ident;
use super::numpy::py_ident;
use crate::ast::Program;
use crate::dims::Dim;
use crate::ty::*;

/// An octahedron's faces (vertex indices).
const OCTAHEDRON: &str = "[[0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1], [5, 2, 1], [5, 3, 2], [5, 4, 3], [5, 1, 4]]";

/// How a dimension symbol gets its value.
enum DimVal {
    /// random, at least the given size
    Draw(i64),
    /// the length shared by sequences
    Seq,
    /// fixed by an equality with a number
    Int(i64),
    /// the same as an earlier dimension
    Alias(String),
}

/// The dimension symbols to set, in order. Integer parameters that size
/// other parameters come first (they are dimensions); equalities between
/// dimensions (`Program::dim_checks`) fix or alias values.
fn dims(prog: &Program) -> Vec<(String, DimVal)> {
    let mut names: Vec<(String, bool)> = Vec::new();
    for p in prog.params.iter().filter(|p| int_dim_param(prog, &p.name)) {
        names.push((p.name.clone(), false));
    }
    for d in &prog.dims {
        let seq = matches!(prog.params.iter().find(|p| p.name == d.param).map(|p| &p.ty), Some(Seq { .. })) && d.axis == 0;
        names.push((d.name.clone(), seq));
    }
    let mut out: Vec<(String, DimVal)> = Vec::new();
    for (name, seq) in names {
        let partners: Vec<&Dim> = prog
            .dim_checks
            .iter()
            .filter_map(|(a, b)| match (a, b) {
                (Dim::Str(x), o) if *x == name => Some(o),
                (o, Dim::Str(x)) if *x == name => Some(o),
                _ => None,
            })
            .collect();
        let v = if let Some(i) = partners.iter().find_map(|d| d.as_int()) {
            DimVal::Int(i)
        } else if let Some(o) = partners.iter().find_map(|d| match d {
            Dim::Str(o) if out.iter().any(|(n, _)| n == o) => Some(o.clone()),
            _ => None,
        }) {
            DimVal::Alias(o)
        } else if seq {
            DimVal::Seq
        } else {
            DimVal::Draw(prog.min_dims.iter().find(|(n, _)| *n == name).map_or(1, |(_, k)| (*k).max(1)))
        };
        out.push((name, v));
    }
    out
}

/// An integer parameter used as a dimension of another parameter (`n` in
/// `A ∈ ℝ^(n×n)`, `n ∈ ℤ`).
fn int_dim_param(prog: &Program, name: &str) -> bool {
    let is_int = prog.params.iter().any(|p| p.name == name && matches!(p.ty, Scalar(e) if e.is_int()));
    is_int && prog.params.iter().any(|p| uses_dim(&p.ty, name))
}

fn uses_dim(t: &Ty, name: &str) -> bool {
    let dim = |d: &Dim| match d {
        Dim::Str(s) => s == name,
        Dim::Sym(_) => sym_names(&d.to_string()).iter().any(|n| n == name),
        _ => false,
    };
    match t {
        Vector { rows, .. } => dim(rows),
        Matrix { rows, cols, .. } => dim(rows) || dim(cols),
        Seq { size, elem } => dim(size) || uses_dim(elem, name),
        _ => false,
    }
}

/// The dimensions of a function's parameters, as expressions of its
/// arguments (`arg(i, axis)`): a random function's result has the sizes its
/// arguments imply.
fn arg_dims(params: &[Ty], arg: &dyn Fn(usize, usize) -> String) -> Vec<(String, String)> {
    let mut out = Vec::new();
    for (i, p) in params.iter().enumerate() {
        let axes: Vec<&Dim> = match p {
            Vector { rows, .. } => vec![rows],
            Matrix { rows, cols, .. } => vec![rows, cols],
            _ => vec![],
        };
        for (a, d) in axes.into_iter().enumerate() {
            if let Dim::Str(n) = d {
                if !out.iter().any(|(m, _)| m == n) {
                    out.push((n.clone(), arg(i, a)));
                }
            }
        }
    }
    out
}

/// A dimension as an expression of the drawn dimension names (`ident` makes
/// a name valid in the target language).
fn dim_expr(d: &Dim, ident: &dyn Fn(&str) -> String, mesh: &dyn Fn(&str, &str) -> String) -> String {
    match d {
        Dim::Int(i) => i.to_string(),
        Dim::Str(s) if s.starts_with("@mesh:") => {
            let parts: Vec<&str> = s.splitn(3, ':').collect();
            mesh(parts[1], parts[2])
        }
        // a ragged sequence's item size: drawn like any dimension
        Dim::Str(s) if s.ends_with("[i]") => "3".into(),
        Dim::Str(s) => ident(s),
        Dim::None => "1".into(),
        d => {
            let mut t = d.to_string();
            for name in sym_names(&t) {
                t = regex::Regex::new(&format!(r"\b{}\b", regex::escape(&name))).unwrap().replace_all(&t, ident(&name).as_str()).into_owned();
            }
            t
        }
    }
}

fn sym_names(t: &str) -> Vec<String> {
    let re = regex::Regex::new(r"[A-Za-z_\p{L}][A-Za-z0-9_\p{L}]*").unwrap();
    re.find_iter(t).map(|m| m.as_str().to_string()).collect()
}

/// The sizes in the parameters' types that are numbers (indices into them
/// must stay below the smallest).
fn fixed_sizes(prog: &Program) -> Vec<i64> {
    fn walk(t: &Ty, out: &mut Vec<i64>) {
        match t {
            Vector { rows, .. } => out.extend(rows.as_int()),
            Matrix { rows, cols, .. } => out.extend(rows.as_int().into_iter().chain(cols.as_int())),
            Seq { size, elem } => {
                out.extend(size.as_int());
                walk(elem, out);
            }
            _ => {}
        }
    }
    let mut out = Vec::new();
    for p in &prog.params {
        walk(&p.ty, &mut out);
    }
    out
}

/// The smallest size, as an expression of the dimension names (`ident`) or
/// a number, written by `min` (e.g. `|xs| format!("min([{xs}])")`).
fn smallest(prog: &Program, ident: &dyn Fn(&str) -> String, min: &dyn Fn(&str) -> String) -> String {
    let mut parts: Vec<String> = prog.dims.iter().map(|x| ident(&x.name)).collect();
    if let Some(m) = fixed_sizes(prog).into_iter().min() {
        parts.push(m.to_string());
    }
    match parts.len() {
        0 => "5".into(),
        1 => parts.remove(0),
        _ => min(&parts.join(", ")),
    }
}

fn mesh_size(k: &str) -> &'static str {
    match k {
        "v" => "n_vertices",
        "e" => "n_edges",
        "f" => "n_faces",
        _ => "n_tets",
    }
}

fn ret_name(prog: &Program) -> Option<&str> {
    prog.ret.as_deref()
}

// -- NumPy --------------------------------------------------------------------

pub fn numpy(prog: &Program, class_name: &str) -> String {
    let ident = |s: &str| py_ident(s);
    let mesh = |m: &str, k: &str| format!("{}.{}()", py_ident(m), mesh_size(k));
    let d = |x: &Dim| dim_expr(x, &ident, &mesh);
    let mut body = Vec::new();
    // meshes first: sizes may depend on them
    for p in prog.params.iter().filter(|p| matches!(p.ty, Mesh(_))) {
        body.push(format!("{} = np.random.MESH", py_ident(&p.name)));
    }
    let mut have_seq = false;
    for (name, v) in dims(prog) {
        let value = match v {
            DimVal::Draw(k) => format!("np.random.randint({k}, {})", k + 9),
            DimVal::Int(i) => i.to_string(),
            DimVal::Alias(o) => py_ident(&o),
            DimVal::Seq => {
                if !have_seq {
                    body.push(format!("seq_n = {}", match prog.meshes.first() {
                    // (sequences over a mesh are usually per vertex)
                    Some((m, _)) => format!("{}.n_vertices()", py_ident(m)),
                    None => "np.random.randint(4, 10)".to_string(),
                }));
                    have_seq = true;
                }
                "seq_n".to_string()
            }
        };
        body.push(format!("{} = {value}", py_ident(&name)));
    }
    // index values stay below every dimension
    let smallest = smallest(prog, &|x| py_ident(x), &|xs| format!("min({xs})"));
    for p in prog.params.iter().filter(|p| !int_dim_param(prog, &p.name) && !matches!(p.ty, Mesh(_))) {
        let n = py_ident(&p.name);
        body.push(format!("{n} = {}", np_value(&p.ty, &d, &smallest, &mut Vec::new(), &n)));
    }
    let names: Vec<String> = prog.params.iter().map(|p| py_ident(&p.name)).collect();
    let mut out = String::from("\n\ndef generateRandomData():\n");
    for l in &body {
        // a function value is a definition
        out += &format!("    {l}\n");
    }
    out += &format!("    return {}\n", if names.is_empty() { "None".to_string() } else { names.join(", ") });
    out += "\n\nif __name__ == '__main__':\n";
    if names.is_empty() {
        out += "    generateRandomData()\n";
    } else {
        out += &format!("    {} = generateRandomData()\n", names.join(", "));
        for n in &names {
            out += &format!("    print(\"{n}:\", {n})\n");
        }
    }
    out += &format!("    func_value = {class_name}({})\n", names.join(", "));
    if let Some(r) = ret_name(prog) {
        out += &format!("    print(\"return value: \", func_value.{})\n", py_ident(r));
    }
    // functions are defined inline as lambdas; meshes need the runtime
    out.replace("np.random.MESH", &format!("TriangleMesh(np.array({OCTAHEDRON}))"))
}

fn np_value(t: &Ty, d: &dyn Fn(&Dim) -> String, smallest: &str, _defs: &mut Vec<String>, _name: &str) -> String {
    match t {
        // (integers may subscript: within the smallest dimension)
        Scalar(e) if e.is_zero_based() => format!("np.random.randint({smallest})"),
        Scalar(e) if e.is_int() => format!("np.random.randint(1, {smallest} + 1)"),
        Scalar(_) => "np.random.randn()".into(),
        Vector { rows, elem } if elem.is_int() => format!("np.random.randint(10, size={})", d(rows)),
        Vector { rows, .. } => format!("np.random.randn({})", d(rows)),
        Matrix { rows, cols, sparse: true, .. } => format!("sparse.random({}, {}, density=0.25, format='csr')", d(rows), d(cols)),
        Matrix { rows, cols, elem, .. } if elem.is_int() => format!("np.random.randint(10, size=({}, {}))", d(rows), d(cols)),
        Matrix { rows, cols, .. } => format!("np.random.randn({}, {})", d(rows), d(cols)),
        Seq { size, elem } => {
            let n = d(size);
            match &**elem {
                Scalar(e) if e.is_int() => format!("np.random.randint(10, size={n})"),
                Scalar(_) => format!("np.random.randn({n})"),
                Vector { rows, elem } if !elem.is_int() => format!("np.random.randn({n}, {})", d(rows)),
                Matrix { rows, cols, elem, sparse: false } if !elem.is_int() => format!("np.random.randn({n}, {}, {})", d(rows), d(cols)),
                e => format!("[{} for _ in range({n})]", np_value(e, d, smallest, _defs, _name)),
            }
        }
        Set { elems, .. } => {
            let item = |e: &Elem| if e.is_zero_based() { format!("np.random.randint({smallest})") } else if e.is_int() { "np.random.randint(10)".into() } else { "np.random.randn()".into() };
            if elems.len() == 1 {
                if elems[0].is_int() {
                    format!("frozenset(int({}) for _ in range(5))", item(&elems[0]))
                } else {
                    format!("frozenset({} for _ in range(5))", item(&elems[0]))
                }
            } else {
                let parts: Vec<String> = elems.iter().map(|e| format!("int({})", item(e))).collect();
                format!("frozenset(({},) for _ in range(5))", parts.join(", "))
            }
        }
        Func { params, rets } => {
            let map = arg_dims(params, &|i, a| format!("np.shape(args[{i}])[{a}]"));
            let fd = |x: &Dim| match x {
                Dim::Str(n) => map.iter().find(|(m, _)| m == n).map(|(_, e)| e.clone()).unwrap_or_else(|| d(x)),
                _ => d(x),
            };
            let r: Vec<String> = rets.iter().map(|x| np_value(x, &fd, smallest, _defs, _name)).collect();
            let v = if r.len() == 1 { r[0].clone() } else { format!("({})", r.join(", ")) };
            format!("lambda *args: {v}")
        }
        Tuple(v) => format!("({},)", v.iter().map(|x| np_value(x, d, smallest, _defs, _name)).collect::<Vec<_>>().join(", ")),
        Mesh(_) => "np.random.MESH".into(),
    }
}

// -- Eigen --------------------------------------------------------------------

pub fn eigen(prog: &Program, struct_name: &str) -> String {
    let ident = |s: &str| cpp_ident(s);
    let mesh = |m: &str, k: &str| format!("{}.{}()", cpp_ident(m), mesh_size(k));
    let d = |x: &Dim| dim_expr(x, &ident, &mesh);
    let params: Vec<String> = prog.params.iter().map(|p| format!("{} & {}", cpp_type(&p.ty), cpp_ident(&p.name))).collect();
    let mut out = String::from("\n#include <cstdlib>\n#include <ctime>\n\n");
    out += &format!("void generateRandomData({})\n{{\n", params.join(", "));
    let mut have_seq = false;
    for (name, v) in dims(prog) {
        let value = match v {
            DimVal::Draw(k) => format!("{k} + rand() % 9"),
            DimVal::Int(i) => i.to_string(),
            DimVal::Alias(o) => cpp_ident(&o),
            DimVal::Seq => {
                if !have_seq {
                    out += &format!("    const int seq_n = {};\n", match prog.meshes.first() {
                        Some((m, _)) => format!("{}.n_vertices()", cpp_ident(m)),
                        None => "4 + rand() % 6".to_string(),
                    });
                    have_seq = true;
                }
                "seq_n".to_string()
            }
        };
        if int_dim_param(prog, &name) {
            out += &format!("    {} = {value};\n", cpp_ident(&name));
        } else {
            out += &format!("    const int {} = {value};\n", cpp_ident(&name));
        }
    }
    let smallest = smallest(prog, &|x| cpp_ident(x), &|xs| format!("std::min({{{xs}}})"));
    for p in prog.params.iter().filter(|p| !int_dim_param(prog, &p.name)) {
        let n = cpp_ident(&p.name);
        out += &cpp_fill(&n, &p.ty, &d, &smallest, 1);
    }
    out += "}\n\n";
    out += "int main(int argc, char *argv[])\n{\n    srand((int)time(NULL));\n";
    for p in &prog.params {
        if let Mesh(_) = p.ty {
            continue;
        }
        out += &format!("    {} {};\n", cpp_type(&p.ty), cpp_ident(&p.name));
    }
    // a mesh is built from an octahedron (the mesh runtime's TriangleMesh)
    for p in &prog.params {
        if let Mesh(_) = p.ty {
            let n = cpp_ident(&p.name);
            out += &format!(
                "    Eigen::MatrixXi {n}_T(8, 3);\n    {n}_T << {};\n    iheartmesh::TriangleMesh {n}_tri({n}_T);\n    {} {n}({n}_tri.bm1, {n}_tri.bm2);\n",
                OCTAHEDRON.replace(['[', ']'], ""),
                cpp_type(&p.ty)
            );
        }
    }
    let names: Vec<String> = prog.params.iter().map(|p| cpp_ident(&p.name)).collect();
    out += &format!("    generateRandomData({});\n", names.join(", "));
    if names.is_empty() {
        out += &format!("    {struct_name} func_value;\n");
    } else {
        out += &format!("    {struct_name} func_value({});\n", names.join(", "));
    }
    if let Some(r) = ret_name(prog) {
        let t = prog.defs.iter().find(|(n, _)| n == r).map(|(_, t)| t.clone());
        let printable = matches!(t, Some(Scalar(_) | Vector { .. } | Matrix { .. }));
        if printable {
            out += &format!("    std::cout << \"return value:\\n\" << func_value.{} << std::endl;\n", cpp_ident(r));
        }
    }
    out += "    return 0;\n}\n";
    out
}

fn cpp_fill(n: &str, t: &Ty, d: &dyn Fn(&Dim) -> String, smallest: &str, depth: usize) -> String {
    let pad = "    ".repeat(depth);
    let rnd_int = "rand() % 10";
    let rnd_real = "(2.0 * rand() / RAND_MAX - 1.0)";
    match t {
        // (integers may subscript: within the smallest dimension)
        Scalar(e) if e.is_zero_based() => format!("{pad}{n} = rand() % {smallest};\n"),
        Scalar(e) if e.is_int() => format!("{pad}{n} = 1 + rand() % {smallest};\n"),
        Scalar(_) => format!("{pad}{n} = {rnd_real};\n"),
        Vector { rows, elem } => format!(
            "{pad}{n} = {}::NullaryExpr({}, [](){{ return {}; }});\n",
            cpp_type(t),
            d(rows),
            if elem.is_int() { rnd_int } else { rnd_real }
        ),
        Matrix { rows, cols, sparse: true, elem } => format!(
            "{pad}{{ std::vector<Eigen::Triplet<{s}>> t; for(int r = 0; r < {rr}; r++) for(int c = 0; c < {cc}; c++) if(rand() % 4 == 0) t.emplace_back(r, c, {v}); \
{n}.resize({rr}, {cc}); {n}.setFromTriplets(t.begin(), t.end()); }}\n",
            s = if elem.is_int() { "int" } else { "double" },
            rr = d(rows),
            cc = d(cols),
            v = if elem.is_int() { rnd_int } else { rnd_real }
        ),
        Matrix { rows, cols, elem, .. } => format!(
            "{pad}{n} = {}::NullaryExpr({}, {}, [](){{ return {}; }});\n",
            cpp_type(t),
            d(rows),
            d(cols),
            if elem.is_int() { rnd_int } else { rnd_real }
        ),
        Seq { size, elem } => {
            let item = format!("{n}_item");
            format!(
                "{pad}{n}.resize({});\n{pad}for(auto & {item} : {n}){{\n{}{pad}}}\n",
                d(size),
                cpp_fill(&item, elem, d, smallest, depth + 1)
            )
        }
        Set { elems, .. } => {
            let item = |e: &Elem| if e.is_zero_based() { format!("rand() % {smallest}") } else if e.is_int() { rnd_int.to_string() } else { rnd_real.to_string() };
            let v = if elems.len() == 1 { item(&elems[0]) } else { format!("std::make_tuple({})", elems.iter().map(item).collect::<Vec<_>>().join(", ")) };
            format!("{pad}{n}.clear();\n{pad}for(int k = 0; k < 5; k++){{ {n}.push_back({v}); }}\n{pad}{n} = sorted_set({n});\n")
        }
        Func { params, rets } => {
            let ps: Vec<String> = params.iter().enumerate().map(|(i, p)| format!("{} a{i}", cpp_type(p))).collect();
            let r = if rets.len() == 1 { rets[0].clone() } else { Tuple(rets.clone()) };
            // a random result, sized as the arguments imply
            let map = arg_dims(params, &|i, a| format!("a{i}.{}()", if a == 0 { "rows" } else { "cols" }));
            let fd = |x: &Dim| match x {
                Dim::Str(nm) => map.iter().find(|(m, _)| m == nm).map(|(_, e)| e.clone()).unwrap_or_else(|| d(x)),
                _ => d(x),
            };
            // (values the function's body can't see are fixed when it is made)
            let caps = "=";
            format!(
                "{pad}{n} = [{caps}]({ps}) -> {rt} {{ {rt} value; {fill} return value; }};\n",
                rt = cpp_type(&r),
                fill = cpp_fill("value", &r, &fd, smallest, 0).trim(),
                ps = ps.join(", ")
            )
        }
        Tuple(v) => {
            let mut s = String::new();
            for (k, x) in v.iter().enumerate() {
                s += &cpp_fill(&format!("std::get<{k}>({n})"), x, d, smallest, depth);
            }
            s
        }
        Mesh(_) => String::new(),
    }
}

// -- MATLAB -------------------------------------------------------------------

/// The statements to put at the top of the MATLAB function: random input
/// data when it is called without arguments.
pub fn matlab(prog: &Program) -> String {
    if prog.params.is_empty() || !prog.meshes.is_empty() {
        return String::new();
    }
    let ident = |s: &str| m_ident(s);
    let mesh = |_: &str, _: &str| "1".to_string();
    let d = |x: &Dim| dim_expr(x, &ident, &mesh);
    let names: Vec<String> = prog.params.iter().map(|p| m_ident(&p.name)).collect();
    let mut out = String::new();
    out += "    if nargin == 0\n        warning('generating random input data');\n";
    out += &format!("        [{}] = generateRandomData();\n    end\n", names.join(", "));
    out += &format!("    function [{}] = generateRandomData()\n", names.join(", "));
    let mut have_seq = false;
    for (name, v) in dims(prog) {
        let value = match v {
            DimVal::Draw(k) => if k == 1 { "randi(9)".to_string() } else { format!("{} + randi(9)", k - 1) },
            DimVal::Int(i) => i.to_string(),
            DimVal::Alias(o) => m_ident(&o),
            DimVal::Seq => {
                if !have_seq {
                    out += "        seq_n = randi([4, 9]);\n";
                    have_seq = true;
                }
                "seq_n".to_string()
            }
        };
        out += &format!("        {} = {value};\n", m_ident(&name));
    }
    let smallest = smallest(prog, &|x| m_ident(x), &|xs| format!("min([{xs}])"));
    for p in prog.params.iter().filter(|p| !int_dim_param(prog, &p.name)) {
        let n = m_ident(&p.name);
        match &p.ty {
            // a function returning a value drawn once
            // a function returning a random value sized as its arguments imply
            Func { params, rets } => {
                let map = arg_dims(params, &|i, a| format!("size(varargin{{{}}}, {})", i + 1, a + 1));
                let fd = |x: &Dim| match x {
                    Dim::Str(nm) => map.iter().find(|(m, _)| m == nm).map(|(_, e)| e.clone()).unwrap_or_else(|| d(x)),
                    _ => d(x),
                };
                let v: Vec<String> = rets.iter().map(|r| m_value(r, &fd, &smallest)).collect();
                let v = if v.len() == 1 { v[0].clone() } else { format!("{{{}}}", v.join(", ")) };
                out += &format!("        {n} = @(varargin) {v};\n");
            }
            t => out += &format!("        {n} = {};\n", m_value(t, &d, &smallest)),
        }
    }
    out += "    end\n";
    out
}

fn m_value(t: &Ty, d: &dyn Fn(&Dim) -> String, smallest: &str) -> String {
    match t {
        // (integers may subscript: within the smallest dimension, 1-based)
        Scalar(e) if e.is_int() => format!("randi({smallest})"),
        Scalar(_) => "randn()".into(),
        Vector { rows, elem } if elem.is_int() => format!("randi(10, {}, 1) - 1", d(rows)),
        Vector { rows, .. } => format!("randn({}, 1)", d(rows)),
        Matrix { rows, cols, sparse: true, .. } => format!("sprandn({}, {}, 0.25)", d(rows), d(cols)),
        Matrix { rows, cols, elem, .. } if elem.is_int() => format!("randi(10, {}, {}) - 1", d(rows), d(cols)),
        Matrix { rows, cols, .. } => format!("randn({}, {})", d(rows), d(cols)),
        Seq { size, elem } => {
            let n = d(size);
            let ragged = |x: &Dim| matches!(x, Dim::Str(s) if s.ends_with("[i]"));
            if ragged(&elem.rows()) || (elem.is_matrix() && ragged(&elem.cols())) {
                // a cell array (items of one size: sequences sharing a ragged size agree)
                let r = d(&elem.rows());
                let c = if elem.is_matrix() { d(&elem.cols()) } else { "1".to_string() };
                return format!("arrayfun(@(k) randn({r}, {c}), (1:{n})', 'UniformOutput', false)");
            }
            match &**elem {
                Scalar(e) if e.is_int() => format!("randi(10, {n}, 1) - 1"),
                Scalar(_) => format!("randn({n}, 1)"),
                Vector { rows, elem } if !elem.is_int() => format!("randn({n}, {})", d(rows)),
                Matrix { rows, cols, elem, sparse: false } if !elem.is_int() => format!("randn({n}, {}, {})", d(rows), d(cols)),
                e => format!("arrayfun(@(k) {}, (1:{n})', 'UniformOutput', false)", m_value(e, d, smallest)),
            }
        }
        Set { elems, .. } => {
            // (index values are 1-based in MATLAB)
            let cols: Vec<String> = elems
                .iter()
                .map(|e| if e.is_zero_based() { format!("randi({smallest}, 5, 1)") } else if e.is_int() { "randi(10, 5, 1) - 1".into() } else { "randn(5, 1)".into() })
                .collect();
            format!("unique([{}], 'rows')", cols.join(", "))
        }
        // (a function parameter is drawn by `matlab`; inside other values, a constant function)
        Func { .. } => "@(varargin) 0".into(),
        Tuple(v) => format!("{{{}}}", v.iter().map(|x| m_value(x, d, smallest)).collect::<Vec<_>>().join(", ")),
        Mesh(_) => "[]".into(),
    }
}
