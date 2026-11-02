//! Declarations pass: from the first (simplified-grammar) parse tree, find
//! the names the full grammar must know about, i.e. the configuration of the
//! second parse.
//!
//! I❤LA juxtaposition means `ab` is `a·b` unless `ab` was declared, and
//! `f(x)` is a call only if `f` is a function. The first parse reads every
//! word as one identifier; this pass collects declared multi-letter names
//! (parameters, assigned symbols, local functions and their parameters,
//! dimension symbols, imported names) and function names, which the second
//! parse then recognizes as single tokens.
//!
//! The rules follow the Python compiler's `get_new_parser` and the first
//! "pre-walk" of its type walker, so that both parse programs the same way.

use crate::helper::{get_unicode_subscript, get_unicode_superscript, is_keyword, py_re_escape, KeywordSet};
use crate::peg::ParserConfig;
use crate::pnode::Val;
use indexmap::{IndexMap, IndexSet};
use regex::Regex;
use std::sync::OnceLock;

pub const MESH_HELPER: &str = "MeshConnectivity";

/// Functions and symbols of the builtin packages.
pub fn package_names(pkg: &str) -> Option<&'static [&'static str]> {
    match pkg {
        "trigonometry" => Some(&[
            "sin", "asin", "arcsin", "cos", "acos", "arccos", "tan", "atan", "arctan", "atan2", "sinh", "asinh",
            "arsinh", "cosh", "acosh", "arcosh", "tanh", "atanh", "artanh", "cot", "sec", "csc", "e",
        ]),
        "linearalgebra" => {
            Some(&["trace", "tr", "diag", "inversevec", "vec⁻¹", "vec", "det", "rank", "null", "orth", "inv", "svd"])
        }
        MESH_HELPER => Some(&[
            "ElementSets", "BoundaryMatrices", "UnsignedBoundaryMatrices", "NonZeros", "IndicatorVector", "ValueSet",
        ]),
        _ => None,
    }
}

/// A single letter (with combining marks): needs no declaration.
pub fn is_single_letter(s: &str) -> bool {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"^[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*$").unwrap()).is_match(s)
}

fn ident_word(s: &str) -> bool {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"^[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*$").unwrap())
        .is_match(s)
}

/// The name of an `IdentifierAlone` parse node: its letters, or `` `text` ``
/// for a backticked name. Backticks are dropped from names that are plain
/// words (and not keywords).
pub fn ident_name(node: &Val) -> String {
    let value = node.get("value");
    let raw = if value.truthy() {
        let v = value.flat_text();
        get_unicode_superscript(&get_unicode_subscript(&v))
    } else if let Some(id) = node.get("id").as_str() {
        format!("`{id}`")
    } else {
        node.get("const").flat_text()
    };
    strip_backticks(&raw)
}

/// Drop the backticks of a backticked name that is a plain word (and not a keyword).
pub fn strip_backticks(raw: &str) -> String {
    if raw.contains('`') {
        let inner = raw.replace('`', "");
        if ident_word(&inner) && !is_keyword(&inner, KeywordSet::Both) {
            return inner;
        }
    }
    raw.to_string()
}

/// The main name of an identifier node (without subscripts).
pub fn main_name(node: &Val) -> String {
    match node.class() {
        "IdentifierSubscript" => main_name(node.get("left")),
        _ => ident_name(node),
    }
}

fn len(s: &str) -> usize {
    s.chars().count()
}

#[derive(Default)]
struct Collector {
    /// multi-letter names to declare (before dedup)
    multi: Vec<String>,
    /// function names in the order the Python symbol table would list them
    funcs: IndexMap<String, ()>,
    /// function-typed parameters of local functions
    local_func_params: Vec<String>,
    local_funcs: Vec<String>,
    rhs_texts: Vec<String>,
}

impl Collector {
    fn add_multi(&mut self, name: &str) {
        if !is_single_letter(name) {
            self.multi.push(name.to_string());
        }
    }

    /// Multi-letter dimension symbols in a type annotation.
    fn type_dims(&mut self, t: &Val) {
        match t {
            Val::Node(n) => {
                if n.class == Some("ArithFactor") {
                    let id0 = t.get("id0");
                    if id0.class() == "IdentifierAlone" {
                        let name = ident_name(id0);
                        if len(&name) > 1 {
                            self.multi.push(name);
                        }
                    }
                }
                for (_, v) in &n.fields {
                    self.type_dims(v);
                }
            }
            Val::List(v) | Val::Closure(v) | Val::Tuple(v) => v.iter().for_each(|x| self.type_dims(x)),
            _ => {}
        }
    }

    /// The left-hand sides of an assignment (and its rhs texts).
    fn assignment(&mut self, text: &dyn Fn(&Val) -> String, assign: &Val) {
        for left in assign.get("left").items() {
            let name = main_name(left);
            if len(&name) > 1 {
                self.add_multi(&name);
            }
            for e in assign.get("right").items() {
                self.rhs_texts.push(text(e));
            }
        }
    }
}

fn summation_extras(rhs: &Val) -> Vec<Val> {
    if rhs.class() == "Expression" && rhs.get("value").class() == "Factor" {
        let op = rhs.get("value").get("op");
        if op.class() == "Summation" {
            return op.get("extra").items().to_vec();
        }
    }
    Vec::new()
}

/// Compute the configuration of the second parse from the first parse tree.
/// `text(node)` returns a node's source text.
pub fn second_parse_config(start: &Val, text: &dyn Fn(&Val) -> String) -> ParserConfig {
    second_parse_config_with(start, text, &|_| None)
}

/// The second parse's configuration, with `module_funcs` giving the names of
/// the functions an imported module defines (None: no such module).
pub fn second_parse_config_with(
    start: &Val,
    text: &dyn Fn(&Val) -> String,
    module_funcs: &dyn Fn(&str) -> Option<Vec<String>>,
) -> ParserConfig {
    let mut c = Collector::default();
    let vblocks = start.get("vblock").items();
    // parameters: where/given blocks, functions last (as the walker orders them)
    let mut func_params: Vec<String> = Vec::new();
    for block in vblocks.iter().filter(|b| b.class() == "ParamsBlock") {
        for cond in block.get("conds").get("value").items() {
            let ty = cond.get("type");
            c.type_dims(ty);
            for id in cond.get("id").items() {
                let name = main_name(id);
                let is_func = ty.class() == "FunctionType";
                if is_func {
                    func_params.push(name);
                } else if !is_single_letter(&name) && len(&name) > 1 && !name.contains('_') && !name.contains('`') {
                    c.multi.push(name);
                }
            }
        }
    }
    // (a subscripted one, D_i, is the function D of its subscripts too)
    for name in &func_params {
        c.funcs.insert(name.clone(), ());
    }
    // imports
    let mut package_names_dict: IndexMap<String, Vec<String>> = IndexMap::new();
    let mut package_rdict: IndexMap<String, IndexMap<String, String>> = IndexMap::new();
    let mut module_pars: Vec<String> = Vec::new();
    let mut imported_funcs: Vec<String> = Vec::new();
    for block in vblocks.iter().filter(|b| b.class() == "Import") {
        let pkg = ident_name(block.get("package"));
        let mut names = Vec::new();
        let mut r_dict = IndexMap::new();
        for v in block.get("names").items() {
            let name = ident_name(v.get("name"));
            let r = if v.get("r").truthy() { ident_name(v.get("r")) } else { name.clone() };
            r_dict.insert(name.clone(), r);
            names.push(name);
        }
        match package_names(&pkg) {
            Some(all) => {
                if block.get("star").truthy() {
                    names = all.iter().map(|s| s.to_string()).collect();
                    r_dict = names.iter().map(|n| (n.clone(), n.clone())).collect();
                }
                if pkg == MESH_HELPER {
                    // imported mesh functions are symbols of function type
                    for n in &names {
                        c.funcs.insert(r_dict[n].clone(), ());
                    }
                }
                let e = package_names_dict.entry(pkg.clone()).or_default();
                e.extend(names);
                e.sort();
                e.dedup();
                // (every import from the package adds its renamings)
                package_rdict.entry(pkg).or_default().extend(r_dict);
            }
            None => {
                // functions imported from a module are called like local functions
                if let Some(funcs) = module_funcs(&pkg) {
                    if block.get("star").truthy() {
                        imported_funcs.extend(funcs.iter().cloned());
                    } else {
                        for n in &names {
                            if funcs.contains(n) {
                                imported_funcs.push(r_dict[n].clone());
                            }
                        }
                    }
                }
                for p in block.get("params").items() {
                    let n = ident_name(p);
                    if !module_pars.contains(&n) {
                        module_pars.push(n);
                    }
                }
                for n in names {
                    if !module_pars.contains(&n) {
                        module_pars.push(n);
                    }
                }
            }
        }
    }
    // statements
    let mut local_func_names: IndexSet<String> = IndexSet::new();
    for block in vblocks.iter().filter(|b| b.class() == "Statements") {
        let stat = block.get("stat");
        match stat.class() {
            "Assignment" | "Destructure" => {
                c.assignment(text, stat);
                for rhs in stat.get("right").items() {
                    for extra in summation_extras(rhs) {
                        c.assignment(text, &extra);
                    }
                }
            }
            "LocalFunc" => {
                let mut name = match stat.get("name").as_str() {
                    Some(s) => s.to_string(),
                    None => main_name(stat.get("name")),
                };
                let original = name.clone();
                if local_func_names.contains(&name) {
                    // an overloaded definition gets a generated name mapped back to the original
                    name = format!("{name}_0");
                }
                local_func_names.insert(name);
                if len(&original) > 1 {
                    c.add_multi(&original);
                }
                c.local_funcs.push(original);
                for def in stat.get("defs").items() {
                    let ty = def.get("type");
                    c.type_dims(ty);
                    for id in def.get("id").items() {
                        let par = main_name(id);
                        if ty.class() == "FunctionType" {
                            c.local_func_params.push(par.clone());
                        }
                        if len(&par) > 1 {
                            c.add_multi(&par);
                        }
                    }
                }
                for extra in stat.get("extra").items() {
                    c.assignment(text, extra);
                    for rhs in extra.get("right").items() {
                        let mut r = rhs.clone();
                        if r.class() == "Expression" && r.get("value").class() == "Factor" && r.get("value").get("sub").truthy() {
                            r = r.get("value").get("sub").get("value").clone();
                        }
                        for e in summation_extras(&r) {
                            c.assignment(text, &e);
                        }
                    }
                }
                for e in stat.get("expr").items() {
                    c.rhs_texts.push(text(e));
                }
            }
            _ => c.rhs_texts.push(text(stat)),
        }
    }

    // `g = f` with f a function makes g a function
    for block in vblocks.iter().filter(|b| b.class() == "Statements") {
        let stat = block.get("stat");
        if stat.class() != "Assignment" {
            continue;
        }
        let Some(rhs) = stat.get("right").items().first() else { continue };
        let id0 = rhs.get("value").get("id0");
        if rhs.class() == "Expression" && rhs.get("value").class() == "Factor" && id0.class() == "IdentifierAlone" {
            if c.funcs.contains_key(&ident_name(id0)) {
                for left in stat.get("left").items() {
                    if left.class() == "IdentifierAlone" {
                        c.funcs.insert(ident_name(left), ());
                    }
                }
            }
        }
    }

    // function names: symbol-table functions, calls f_i(…) of local functions'
    // function parameters, local functions, function parameters of local functions
    let mut func_dict: IndexMap<String, ()> = c.funcs.clone();
    let rhs = c.rhs_texts.join("\n");
    for seq in &c.local_func_params {
        for m in find_seq_calls(seq, &rhs) {
            func_dict.insert(m, ());
        }
    }
    for f in &c.local_funcs {
        func_dict.insert(f.clone(), ());
    }
    for p in &c.local_func_params {
        func_dict.insert(p.clone(), ());
    }
    for f in &imported_funcs {
        func_dict.insert(f.clone(), ());
    }

    // builtin functions imported from packages
    let mut builtins: Vec<String> = Vec::new();
    let mut key_names: Vec<String> = Vec::new();
    let mut rename = std::collections::HashMap::new();
    let mut const_e = false;
    for (pkg, names) in &package_names_dict {
        let r = &package_rdict[pkg];
        let mut names = names.clone();
        if let Some(i) = names.iter().position(|n| n == "e") {
            names.remove(i);
            const_e = true;
        }
        for name in &names {
            if !is_single_letter(&r[name]) {
                c.multi.insert(0, r[name].clone());
            }
            if pkg == MESH_HELPER {
                continue;
            }
            key_names.push(if name == "vec⁻¹" { "inversevec_func".into() } else { format!("{name}_func") });
        }
        for (k, v) in r {
            if k != v {
                rename.insert(k.clone(), v.clone());
            }
        }
    }
    builtins.extend(key_names);

    for p in &module_pars {
        c.add_multi(p);
    }
    let mut funcs: Vec<String> = Vec::new();
    if !func_dict.is_empty() {
        let mut keys: Vec<String> = func_dict.keys().cloned().collect();
        let extra: Vec<String> = keys.iter().filter(|k| !k.contains('`')).map(|k| format!("`{k}`")).collect();
        keys.extend(extra);
        funcs = keys.iter().map(|k| py_re_escape(k)).collect();
        funcs.sort_by_key(|k| std::cmp::Reverse(len(k)));
        for f in funcs.clone() {
            if !is_single_letter(&f) {
                c.multi.push(f);
            }
        }
    }
    let mut ids: Vec<String> = c.multi.iter().filter(|k| !k.contains('`')).cloned().collect::<IndexSet<_>>().into_iter().collect();
    ids = ids.iter().map(|k| py_re_escape(k)).collect();
    ids.sort_by_key(|k| std::cmp::Reverse(len(k)));
    ParserConfig { ids, funcs, builtins, rename, const_e }
}

/// Calls `seq_i(` of a function sequence in the right-hand sides.
fn find_seq_calls(seq: &str, text: &str) -> Vec<String> {
    let pat = format!(
        r"(?:{seq}_`[^`]*`|{seq}_[A-Za-z\p{{Ll}}\p{{Lu}}\p{{Lo}}]\p{{M}}*(?:[A-Z0-9a-z\p{{Ll}}\p{{Lu}}\p{{Lo}}]\p{{M}}*)*|{seq}_\d*)"
    );
    let Ok(re) = Regex::new(&pat) else { return Vec::new() };
    let mut out = Vec::new();
    let mut start = 0;
    while start <= text.len() {
        let Some(m) = re.find_at(text, start) else { break };
        if text[m.end()..].starts_with('(') {
            out.push(m.as_str().to_string());
            start = m.end().max(m.start() + 1);
        } else {
            start = m.start() + text[m.start()..].chars().next().map_or(1, |c| c.len_utf8());
        }
    }
    out
}
