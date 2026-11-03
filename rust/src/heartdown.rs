//! What H❤️rtDown needs from a compile: each backend's output in the parts it
//! assembles a paper's code and equations from, and the paper's equation data
//! (the symbols a context defines and uses, their types and descriptions,
//! and which symbols each equation relates), which its glossary, symbol
//! colors and click handlers are built from.
//!
//! It is the Rust counterpart of the Python compiler's
//! `compile_la_content(..., get_json=True)`: `iheartla/rust_heartdown.py`
//! turns this JSON into the objects that function returns. Names are as the
//! Python compiler's symbol table has them (a backticked name that isn't a
//! plain word keeps its backticks, `` `E_\text{data}` ``).

use crate::ast::{Program, Stmt};
use crate::back::latex::{self, Flavor};
use crate::decls::main_name;
use crate::dims::Dim;
use crate::pnode::Val;
use crate::ty::Ty;
use serde_json::{json, Map, Value};

/// Compile `src` (the context `name`) for H❤️rtDown, with modules found by
/// `loader`, to the backends listed (numpy, eigen, matlab, mathjax,
/// macromathjax):
///
/// ```text
/// {"frames": {backend: {"include": str, "struct": str}          (numpy, eigen, matlab)
///                    | {"pre": str, "post": str, "exprs": [[source text, output]]}},
///  "equation": {"parameters": [name], "definition": [name], "opt_syms": [name],
///               "types": {name: type}, "desc": {name: str},
///               "local_funcs": [{"name", "parameters": [name], "types": {name: type}, "symbols": [name]}],
///               "dependence": [{"module", "names": [name], "args": [name]}],
///               "expr_symbols": [[name, [name]]]}}
/// ```
///
/// A type is `{"type": "scalar" | "vector" | "matrix" | "sequence" | "set" |
/// "function" | …, "is_int": bool, …}` with dimensions as strings, as the
/// Python compiler's `get_json_content()` has them.
///
/// On an error: `{"error": message, "msg": str, "code": str}`, with the
/// error alone and the line of code it's on (the Python compiler's
/// `LaMsg.cur_msg` and `cur_code`, which the editor highlights).
pub fn compile(src: &str, name: &str, backends: &[&str], loader: &std::rc::Rc<crate::modules::Loader>) -> Value {
    crate::helper::LA_MSG.with(|m| *m.borrow_mut() = (String::new(), String::new()));
    match compile_inner(src, name, backends, loader) {
        Ok(v) => v,
        Err(e) => {
            let (msg, code) = crate::helper::LA_MSG.with(|m| m.borrow().clone());
            json!({ "error": e, "msg": msg, "code": code })
        }
    }
}

fn compile_inner(src: &str, name: &str, backends: &[&str], loader: &std::rc::Rc<crate::modules::Loader>) -> Result<Value, String> {
    let (tree, prog) = crate::front_end_with(src, loader)?;
    let mut frames = Map::new();
    for b in backends {
        let frame = match *b {
            "numpy" => {
                let (include, class) = crate::back::numpy::generate_parts(&prog, name);
                json!({ "include": include, "struct": class })
            }
            "eigen" => {
                let (include, body) = crate::back::eigen::generate_parts(&prog, name);
                json!({ "include": include, "struct": body })
            }
            "matlab" => json!({ "include": "", "struct": crate::back::matlab::generate(&prog, name) }),
            "mathjax" | "macromathjax" => {
                let flavor = if *b == "mathjax" { Flavor::Mathjax } else { Flavor::MacroMathjax };
                let (_, exprs) = latex::generate_named(&prog, &tree, flavor, name);
                let (pre, post) = latex::MATHJAX_PRE_POST;
                json!({ "pre": pre, "post": post, "exprs": exprs })
            }
            other => return Err(format!("unknown backend {other}")),
        };
        frames.insert(b.to_string(), frame);
    }
    Ok(json!({ "frames": frames, "equation": equation(&prog, &tree) }))
}

fn equation(prog: &Program, tree: &Val) -> Value {
    let vblocks: Vec<Val> = tree.get("vblock").items().to_vec();
    let stats: Vec<Val> = vblocks.iter().filter(|b| b.class() == "Statements").map(|b| b.get("stat").clone()).collect();
    let mut types = Map::new();
    let mut set_type = |types: &mut Map<String, Value>, n: &str, t: Option<&Ty>| {
        if let Some(t) = t {
            types.entry(n.to_string()).or_insert_with(|| ty_json(t));
        }
    };
    // parameters, in declaration order
    let parameters: Vec<String> = prog.params.iter().map(|p| p.name.clone()).collect();
    for p in &prog.params {
        set_type(&mut types, &p.name, Some(&p.ty));
    }
    // definitions, in source order
    let mut definition = Vec::new();
    for s in &stats {
        if matches!(s.class(), "Assignment" | "GeneralAssignment" | "Destructure") {
            for l in sides(s.get("left")) {
                let n = main_name(&l);
                if !definition.contains(&n) {
                    definition.push(n);
                }
            }
        }
    }
    for d in &definition {
        set_type(&mut types, d, prog.defs.iter().find(|(n, _)| n == d).map(|(_, t)| t));
    }
    // optimization variables, in source order
    let mut opt_syms = Vec::new();
    for o in find_all(tree, "Optimize") {
        for d in o.get("defs").items() {
            for id in d.get("id").items() {
                let n = main_name(id);
                if !opt_syms.contains(&n) {
                    opt_syms.push(n);
                }
            }
        }
    }
    for v in &opt_syms {
        set_type(&mut types, v, prog.opt_vars.iter().find(|(n, _)| n == v).map(|(_, t)| t));
    }
    // descriptions, from where blocks
    let mut desc = Map::new();
    for c in find_all(tree, "WhereCondition") {
        // (as written, after the colon and spaces)
        if let Some(d) = c.get("desc").as_str() {
            for id in c.get("id").items() {
                desc.insert(main_name(id), Value::String(d.to_string()));
            }
        }
    }
    // local functions
    let mut local_funcs = Vec::new();
    for f in prog.stmts.iter().filter_map(|s| if let Stmt::Func(f) = s { Some(f) } else { None }) {
        if local_funcs.iter().any(|x: &Value| x["name"] == f.base.as_str()) {
            continue; // (an overload: the glossary lists the name once)
        }
        set_type(&mut types, &f.base, Some(&f.ty));
        let mut ftypes = Map::new();
        let mut symbols = Vec::new();
        for (p, t) in &f.params {
            ftypes.insert(p.clone(), ty_json(t));
            dim_names(t, &mut symbols);
        }
        for st in &f.body {
            if let Stmt::Assign(a) = st {
                symbols.push(a.lhs.clone());
            }
        }
        symbols.retain(|s| !ftypes.contains_key(s));
        symbols.dedup();
        local_funcs.push(json!({
            "name": f.base,
            "parameters": f.params.iter().map(|(p, _)| p.clone()).collect::<Vec<_>>(),
            "types": ftypes,
            "symbols": symbols,
        }));
    }
    // imported modules
    let mut dependence = Vec::new();
    for m in &prog.modules {
        let mut names: Vec<String> = Vec::new();
        for (in_module, here) in &m.syms {
            if !names.contains(here) {
                names.push(here.clone());
                set_type(&mut types, here, module_symbol_type(&m.prog, in_module).as_ref());
            }
        }
        dependence.push(json!({ "module": m.name, "names": names, "args": m.args }));
    }
    // the symbols each definition relates (the Python compiler's
    // `expr_dict`): an optimization's variables, what its objective uses; an
    // assignment's (first) symbol, what its right side uses and itself; a
    // local function, what it uses, its parameters and itself
    struct Entry {
        key: String,
        node: Val,
        in_func: bool,
        params: Vec<String>,
        own: bool,
    }
    let mut entries = Vec::new();
    for s in &stats {
        let in_func = s.class() == "LocalFunc";
        for o in find_all(s, "Optimize") {
            for d in o.get("defs").items() {
                for id in d.get("id").items() {
                    entries.push(Entry { key: main_name(id), node: o.clone(), in_func, params: vec![], own: false });
                }
            }
        }
        match s.class() {
            // (each symbol an assignment defines; a piecewise right side relates none)
            "Assignment" => {
                let right = sides(s.get("right"));
                let piecewise = right.first().is_some_and(|r| r.class() == "MultiCondExpr" || r.get("value").class() == "MultiCondExpr");
                let node = if piecewise { Val::default() } else { s.get("right").clone() };
                for l in sides(s.get("left")) {
                    entries.push(Entry { key: main_name(&l), node: node.clone(), in_func, params: vec![], own: true });
                }
            }
            "LocalFunc" => {
                let params = latex::local_func_params(s);
                entries.push(Entry { key: main_name(s.get("name")), node: s.get("expr").clone(), in_func, params, own: true });
            }
            _ => {}
        }
    }
    let nodes: Vec<(&Val, bool)> = entries.iter().map(|e| (&e.node, e.in_func)).collect();
    let syms = latex::node_symbols(prog, tree, &nodes);
    let mut expr_symbols = Vec::new();
    for (e, mut list) in entries.iter().zip(syms) {
        for p in &e.params {
            if !list.contains(p) {
                list.push(p.clone());
            }
        }
        if e.own {
            list.push(e.key.clone());
        }
        expr_symbols.push(json!([e.key, list]));
    }
    json!({
        "parameters": parameters,
        "definition": definition,
        "opt_syms": opt_syms,
        "types": types,
        "desc": desc,
        "local_funcs": local_funcs,
        "dependence": dependence,
        "expr_symbols": expr_symbols,
    })
}

/// The type of a module's symbol (a definition, parameter or function).
fn module_symbol_type(prog: &Program, name: &str) -> Option<Ty> {
    prog.defs
        .iter()
        .find(|(n, _)| n == name)
        .map(|(_, t)| t.clone())
        .or_else(|| prog.params.iter().find(|p| p.name == name).map(|p| p.ty.clone()))
        .or_else(|| prog.funcs.iter().find(|(n, _)| n == name).and_then(|(_, o)| o.first()).map(|(t, _)| t.clone()))
}

fn sides(v: &Val) -> Vec<Val> {
    if v.is_seq() {
        v.items().to_vec()
    } else if v.truthy() {
        vec![v.clone()]
    } else {
        vec![]
    }
}

/// The nodes of class `class` in a parse tree, in source order.
fn find_all(n: &Val, class: &str) -> Vec<Val> {
    let mut out = Vec::new();
    fn go(n: &Val, class: &str, out: &mut Vec<Val>) {
        if n.is_seq() {
            for x in n.items() {
                go(x, class, out);
            }
            return;
        }
        let Some(node) = n.node() else { return };
        if n.class() == class {
            out.push(n.clone());
        }
        for (_, v) in &node.fields {
            go(v, class, out);
        }
    }
    go(n, class, &mut out);
    out.sort_by_key(|x| x.node().and_then(|n| n.span).map(|s| s.0).unwrap_or(0));
    out
}

/// The dimension names in a type (`n` of `ℝ^(n×3)`).
fn dim_names(t: &Ty, out: &mut Vec<String>) {
    let mut dim = |d: &Dim| {
        if let Dim::Str(s) | Dim::Sym(crate::dims::Sym::Symbol(s)) = d {
            if !s.chars().all(|c| c.is_ascii_digit()) && !out.contains(s) {
                out.push(s.clone());
            }
        }
    };
    match t {
        Ty::Vector { rows, .. } => dim(rows),
        Ty::Matrix { rows, cols, .. } => {
            dim(rows);
            dim(cols);
        }
        Ty::Seq { size, elem } => {
            dim(size);
            dim_names(elem, out);
        }
        _ => {}
    }
}

/// A dimension as text for H❤️rtDown's pages, which embed it in JSON
/// without escaping it: without backslashes, quotes and backticks (a
/// dimension the program doesn't name, such as a sequence's length, has the
/// compiler's name, which may be made from a backticked name: `` `$\boldsymbol{u}$`_n ``).
fn dim_text(d: &Dim) -> String {
    d.to_string().chars().filter(|c| !matches!(c, '\\' | '"' | '\'' | '`' | '$')).collect()
}

/// A type as JSON, as the Python compiler's `get_json_content()` describes it.
pub fn ty_json(t: &Ty) -> Value {
    match t {
        Ty::Scalar(e) => json!({ "type": "scalar", "is_int": e.is_int() }),
        Ty::Vector { rows, elem } => {
            json!({ "type": "vector", "is_int": elem.is_int(), "element": ty_json(&Ty::Scalar(*elem)), "rows": dim_text(rows) })
        }
        Ty::Matrix { rows, cols, elem, .. } => json!({
            "type": "matrix", "is_int": elem.is_int(), "element": ty_json(&Ty::Scalar(*elem)),
            "rows": dim_text(rows), "cols": dim_text(cols),
        }),
        Ty::Seq { size, elem } => json!({ "type": "sequence", "is_int": elem.is_int(), "element": ty_json(elem), "size": dim_text(size) }),
        Ty::Set { elems, .. } => json!({
            "type": "set", "is_int": elems.iter().all(|e| e.is_int()),
            "element": elems.iter().map(|e| if e.is_int() { "1" } else { "0" }).collect::<Vec<_>>(),
            "size": elems.len().to_string(),
        }),
        Ty::Func { params, rets } => json!({
            "type": "function",
            "params": params.iter().map(ty_json).collect::<Vec<_>>(),
            "ret": rets.iter().map(ty_json).collect::<Vec<_>>(),
        }),
        other => json!({ "type": other.to_string(), "is_int": other.is_int() }),
    }
}
