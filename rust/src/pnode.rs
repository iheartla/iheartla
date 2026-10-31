//! Parse-tree values, with the same shapes as TatSu's: rule nodes with named
//! fields, strings, and three kinds of lists.

use std::fmt::Write;
use std::rc::Rc;

/// A value in the parse tree.
#[derive(Clone, Debug, Default)]
pub enum Val {
    #[default]
    None,
    Str(Rc<str>),
    /// A rule result with a class name (`rule::Class`), or a rule without a
    /// class that named some of its elements (an AST dict, `class: None`).
    Node(Rc<PNode>),
    /// A Python `list`: an unnamed sequence, or values accumulated under one name.
    List(Rc<Vec<Val>>),
    /// The result of `{…}` or `{…}+` (TatSu's `closure`, a list subclass).
    Closure(Rc<Vec<Val>>),
    /// The result of a rule without names whose elements formed a sequence.
    Tuple(Rc<Vec<Val>>),
}

#[derive(Debug)]
pub struct PNode {
    pub class: Option<&'static str>,
    /// Byte span in the source; `None` when the rule had no named elements.
    pub span: Option<(usize, usize)>,
    pub fields: Vec<(&'static str, Val)>,
    /// For a class rule without named elements: the rule's unnamed result.
    pub raw: Val,
}

impl Val {
    pub fn is_none(&self) -> bool {
        matches!(self, Val::None)
    }

    pub fn node(&self) -> Option<&Rc<PNode>> {
        match self {
            Val::Node(n) => Some(n),
            _ => None,
        }
    }

    pub fn as_str(&self) -> Option<&str> {
        match self {
            Val::Str(s) => Some(s),
            _ => None,
        }
    }

    /// Elements of any list kind (`None` gives an empty slice).
    pub fn items(&self) -> &[Val] {
        match self {
            Val::List(v) | Val::Closure(v) | Val::Tuple(v) => v,
            _ => &[],
        }
    }

    pub fn is_seq(&self) -> bool {
        matches!(self, Val::List(_) | Val::Closure(_) | Val::Tuple(_))
    }

    /// Python truthiness.
    pub fn truthy(&self) -> bool {
        match self {
            Val::None => false,
            Val::Str(s) => !s.is_empty(),
            Val::Node(_) => true,
            Val::List(v) | Val::Closure(v) | Val::Tuple(v) => !v.is_empty(),
        }
    }

    /// Class name of a rule node (`type(node).__name__` in the Python walker).
    pub fn class(&self) -> &str {
        match self {
            Val::Node(n) => n.class.unwrap_or("AST"),
            Val::Str(_) => "str",
            Val::List(_) | Val::Closure(_) => "list",
            Val::Tuple(_) => "tuple",
            Val::None => "NoneType",
        }
    }

    /// Field of a rule node; `None` when absent (TatSu nodes return None too).
    pub fn get(&self, name: &str) -> &Val {
        match self {
            Val::Node(n) => n.get(name),
            _ => &NONE.0,
        }
    }

    /// Python `str()` of a parse value, as used by the walker (`''.join` of
    /// string lists etc.).
    pub fn flat_text(&self) -> String {
        let mut s = String::new();
        self.flat_into(&mut s);
        s
    }

    fn flat_into(&self, out: &mut String) {
        match self {
            Val::Str(s) => out.push_str(s),
            Val::List(v) | Val::Closure(v) | Val::Tuple(v) => v.iter().for_each(|x| x.flat_into(out)),
            _ => {}
        }
    }
}

impl PNode {
    pub fn get(&self, name: &str) -> &Val {
        self.fields.iter().find(|(k, _)| *k == name).map(|(_, v)| v).unwrap_or(&NONE.0)
    }

    pub fn has(&self, name: &str) -> bool {
        self.fields.iter().any(|(k, _)| *k == name)
    }
}

/// A shared `None` for field lookups that miss.
struct NoneVal(Val);
// SAFETY: `Val::None` holds no `Rc`, so sharing it between threads is sound.
unsafe impl Sync for NoneVal {}
static NONE: NoneVal = NoneVal(Val::None);

/// Serialize as JSON in the format of rust/tools/golden.py (`ast_json`), with
/// character offsets. `char_of` maps byte offsets to character offsets.
pub fn to_json(v: &Val, char_of: &dyn Fn(usize) -> usize) -> String {
    let mut s = String::new();
    write_json(v, char_of, &mut s);
    s
}

fn write_json(v: &Val, char_of: &dyn Fn(usize) -> usize, out: &mut String) {
    match v {
        Val::None => out.push_str("null"),
        Val::Str(s) => write_json_str(s, out),
        Val::List(items) | Val::Closure(items) | Val::Tuple(items) => {
            out.push('[');
            for (i, x) in items.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                write_json(x, char_of, out);
            }
            out.push(']');
        }
        Val::Node(n) => {
            if n.class.is_none() {
                out.push_str("{\"{}\":");
            }
            out.push('{');
            let mut first = true;
            if let Some(c) = n.class {
                out.push_str("\"_\":");
                write_json_str(c, out);
                first = false;
                if let Some((a, b)) = n.span {
                    let _ = write!(out, ",\"@\":[{},{}]", char_of(a), char_of(b));
                }
            }
            for (k, x) in &n.fields {
                if !first {
                    out.push(',');
                }
                first = false;
                write_json_str(k, out);
                out.push(':');
                write_json(x, char_of, out);
            }
            out.push('}');
            if n.class.is_none() {
                out.push('}');
            }
        }
    }
}

fn write_json_str(s: &str, out: &mut String) {
    out.push('"');
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => {
                let _ = write!(out, "\\u{:04x}", c as u32);
            }
            c => out.push(c),
        }
    }
    out.push('"');
}
