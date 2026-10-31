//! `IRVisitor.convert_unicode`: turn an I❤LA identifier into one that is
//! valid in the target language (e.g. `θ` -> `θ` in Python but `theta` in
//! MATLAB, `x²` -> `x2`).

use crate::helper::{py_isalnum, py_isnumeric, py_isspace, str_isnumeric};
use crate::packages::Backend as Kind;

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
