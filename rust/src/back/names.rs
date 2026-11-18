//! `IRVisitor.convert_unicode`: turn an I❤LA identifier into one that is
//! valid in the target language (e.g. `θ` -> `θ` in Python but `theta` in
//! MATLAB, `x²` -> `x2`).

use crate::ast::{Program, Stmt};
use crate::helper::{py_isalnum, py_isnumeric, py_isspace, str_isnumeric};
use std::cell::RefCell;
use std::collections::{HashMap, HashSet};

/// Target languages (their identifier rules differ).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    Numpy,
    Eigen,
    Matlab,
    Latex,
}

#[path = "common_symbols.rs"]
mod common_symbols;

const SPECIAL: &[(char, &str)] = &[('∂', "dee"), ('⁰', "0"), ('¹', "1"), ('²', "2"), ('ᵀ', "T")];

fn uni_num(c: char) -> Option<char> {
    let subs = "₀₁₂₃₄₅₆₇₈₉";
    let sups = "⁰¹²³⁴⁵⁶⁷⁸⁹";
    subs.chars()
        .position(|x| x == c)
        .or_else(|| sups.chars().position(|x| x == c))
        .map(|i| char::from_digit(i as u32, 10).unwrap())
}

pub fn has_special_symbol(target: &str) -> bool {
    SPECIAL.iter().any(|(k, _)| target.contains(*k))
}

/// Python's `unicodedata.name(c).lower().replace(' ', '_')`.
fn unicode_name(c: char) -> Option<String> {
    unicode_names2::name(c).map(|n| n.to_string().to_lowercase().replace(' ', "_"))
}

pub fn convert_unicode(kind: Kind, name: &str) -> String {
    if !has_special_symbol(name) && !name.contains('`') && kind != Kind::Matlab {
        return name.to_string();
    }
    let mut name = name.to_string();
    // a minus in a subscript is m, so `b_{-1}` (b_m1) and `b_1` (b_1) stay distinct
    if let Some(sub_start) = name.find('_') {
        name = format!("{}{}", &name[..sub_start], name[sub_start..].replace('-', "m"));
    }
    for rm in ["`$", "$`", "`", "(", ")", "{", "}", "\\", "-"] {
        name = name.replace(rm, "");
    }
    let first = name.chars().next().expect("string index out of range");
    if str_isnumeric(&name) || py_isnumeric(first) {
        name = format!("num{name}");
    }
    let mut new_list: Vec<String> = Vec::new();
    let mut pre_unicode = false;
    for mut e in name.chars() {
        if let Some((_, v)) = SPECIAL.iter().find(|(k, _)| *k == e) {
            new_list.push(v.to_string());
            continue;
        }
        if matches!(kind, Kind::Numpy | Kind::Matlab | Kind::Eigen) && py_isnumeric(e) {
            if let Some(d) = uni_num(e) {
                e = d;
            }
        }
        if ((kind != Kind::Matlab || e.is_ascii()) && py_isalnum(e)) || e == '_' {
            if pre_unicode {
                new_list.push("_".into());
                pre_unicode = false;
            }
            new_list.push(e.to_string());
        } else if py_isspace(e) {
            new_list.push(String::new());
        } else {
            let common = if kind == Kind::Matlab {
                common_symbols::COMMON_SYMBOLS.iter().find(|(k, _)| *k == e).map(|(_, v)| *v)
            } else {
                None
            };
            match common {
                Some(v) => new_list.push(v.to_string()),
                None => {
                    if !pre_unicode {
                        new_list.push("_".into());
                    }
                    match unicode_name(e) {
                        Some(n) => new_list.push(n),
                        None => continue,
                    }
                }
            }
            new_list.push("_".into());
            pre_unicode = true;
        }
    }
    if new_list.first().is_some_and(|s| str_isnumeric(s)) {
        new_list.insert(0, "_".into());
    }
    let joined = new_list.concat();
    let mut collapsed = String::with_capacity(joined.len());
    for c in joined.chars() {
        if c == '_' && collapsed.ends_with('_') {
            continue;
        }
        collapsed.push(c);
    }
    collapsed.trim_matches('_').to_string()
}

thread_local! {
    /// The names given a different identifier because their usual one is taken, for each
    /// program being generated (an imported module's innermost).
    static RENAMES: RefCell<Vec<HashMap<String, String>>> = const { RefCell::new(Vec::new()) };
}

/// The identifier `name` was given in the program being generated, if it isn't its usual one.
pub fn renamed(name: &str) -> Option<String> {
    RENAMES.with(|r| r.borrow().last().and_then(|m| m.get(name).cloned()))
}

/// Run `f` with the identifiers of `prog`'s names: `ident` gives a name's usual identifier.
/// When two names have the same one, as `` `a_{(1)}` `` and `` `a_1` `` (both a_1), all but the
/// first, longest first, get a `_` in front (`suffix`: behind) until it is free, as the Python
/// compiler's `IRVisitor.trim_content` does. A name whose identifier is itself keeps it.
pub fn with_names<T>(prog: &Program, ident: fn(&str) -> String, suffix: bool, f: impl FnOnce() -> T) -> T {
    let mut names = program_names(prog);
    names.sort_by(|a, b| b.chars().count().cmp(&a.chars().count()).then_with(|| a.cmp(b)));
    let mut taken: HashSet<String> = names.iter().filter(|n| ident(n) == **n).cloned().collect();
    let mut map = HashMap::new();
    for n in names.iter().filter(|n| ident(n) != **n) {
        let mut id = ident(n);
        if taken.contains(&id) {
            while taken.contains(&id) {
                id = if suffix { format!("{id}_") } else { format!("_{id}") };
            }
            map.insert(n.clone(), id.clone());
        }
        taken.insert(id);
    }
    RENAMES.with(|r| r.borrow_mut().push(map));
    let out = f();
    RENAMES.with(|r| r.borrow_mut().pop());
    out
}

/// Every name a program declares or defines, once.
fn program_names(prog: &Program) -> Vec<String> {
    fn stmts(ss: &[Stmt], out: &mut Vec<String>) {
        for s in ss {
            match s {
                Stmt::Assign(a) => {
                    out.push(a.lhs.clone());
                    out.extend(a.subs.iter().cloned());
                }
                Stmt::Multi { lhs, .. } => out.extend(lhs.iter().map(|(n, _)| n.clone())),
                Stmt::Func(f) => {
                    out.push(f.name.clone());
                    out.push(f.base.clone());
                    out.extend(f.params.iter().map(|(n, _)| n.clone()));
                    stmts(&f.body, out);
                }
            }
        }
    }
    let mut out: Vec<String> = Vec::new();
    out.extend(prog.params.iter().map(|p| p.name.clone()));
    out.extend(prog.dims.iter().map(|d| d.name.clone()));
    out.extend(prog.defs.iter().map(|(n, _)| n.clone()));
    out.extend(prog.opt_vars.iter().map(|(n, _)| n.clone()));
    out.extend(prog.meshes.iter().map(|(n, _)| n.clone()));
    for (n, overloads) in &prog.funcs {
        out.push(n.clone());
        out.extend(overloads.iter().map(|(_, i)| i.clone()));
    }
    for m in &prog.modules {
        out.extend(m.syms.iter().map(|(_, here)| here.clone()));
    }
    stmts(&prog.stmts, &mut out);
    let mut seen = HashSet::new();
    out.retain(|n| seen.insert(n.clone()));
    out
}
