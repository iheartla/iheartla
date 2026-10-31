//! A PEG engine with TatSu's semantics.
//!
//! The grammar rules in `grammar/` are translated from TatSu-generated Python
//! and call the methods below, which reproduce what TatSu's `ParseContext`
//! does: ordered choice, the CST/AST construction rules (including how
//! sequences, groups and closures nest), memoization, and TatSu's algorithm
//! for left recursion (growing a seed result per position until it stops
//! getting longer). Reproducing these exactly is what makes the parse trees
//! identical to the Python compiler's.
//!
//! Differences that do not change results: positions are byte offsets
//! (converted to characters for output), the memo table is unbounded (TatSu
//! evicts after 1024 entries, which only costs time), and a failure's rule
//! stack is recorded only when it could become the reported error.

use crate::pnode::{PNode, Val};
use regex::Regex;
use std::collections::HashMap;
use std::rc::Rc;
use std::sync::OnceLock;

pub type RuleId = usize;
pub type PResult = Result<(), Fail>;

pub struct RuleInfo {
    pub name: &'static str,
    pub class: Option<&'static str>,
    pub leftrec: bool,
    pub memo: bool,
    pub body: fn(&mut Parser) -> PResult,
}

pub struct Grammar {
    pub rules: &'static [RuleInfo],
    pub patterns: &'static [&'static str],
    pub compiled: &'static OnceLock<Vec<Regex>>,
    pub start: RuleId,
}

impl Grammar {
    fn regexes(&self) -> &'static [Regex] {
        self.compiled.get_or_init(|| self.patterns.iter().map(|p| compile_pattern(p)).collect())
    }

    pub fn rule_id(&self, name: &str) -> Option<RuleId> {
        self.rules.iter().position(|r| r.name == name)
    }
}

/// Compile a Python `regex`-module pattern for matching at the current position.
pub fn compile_pattern(pat: &str) -> Regex {
    Regex::new(&format!("^(?:{})", py_regex_to_rust(pat)))
        .unwrap_or_else(|e| panic!("bad pattern {pat:?}: {e}"))
}

/// Python treats `[`, `&` and `~` inside a character class literally; Rust's
/// regex crate gives them meaning (nested classes, set operations).
fn py_regex_to_rust(pat: &str) -> String {
    let mut out = String::with_capacity(pat.len());
    let mut in_class = false;
    let mut class_start = false;
    let mut chars = pat.chars().peekable();
    while let Some(c) = chars.next() {
        if c == '\\' {
            out.push(c);
            if let Some(n) = chars.next() {
                out.push(n);
            }
            class_start = false;
            continue;
        }
        if in_class {
            match c {
                ']' if !class_start => in_class = false,
                '[' | '&' | '~' => {
                    out.push('\\');
                }
                _ => {}
            }
            class_start = class_start && c == '^';
        } else if c == '[' {
            in_class = true;
            class_start = true;
            out.push(c);
            continue;
        }
        out.push(c);
    }
    out
}

/// Settings of the full ("default") grammar that depend on the program:
/// the Python compiler patched these into its generated parser.
#[derive(Clone, Debug, Default)]
pub struct ParserConfig {
    /// Declared multi-letter identifiers, as regex patterns (already escaped),
    /// longest first.
    pub ids: Vec<String>,
    /// Function names, as regex patterns.
    pub funcs: Vec<String>,
    /// Imported builtin function rules (e.g. `sin_func`).
    pub builtins: Vec<String>,
    /// Imported builtin functions renamed with `as`: original -> new name.
    pub rename: HashMap<String, String>,
    /// Whether `e` was imported as a constant.
    pub const_e: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FailKind {
    Token,
    Pattern,
    LeftRecursion,
    Other,
}

#[derive(Clone, Debug)]
pub enum Msg {
    Static(&'static str),
    Token(&'static str),
    Pattern(usize),
    Dynamic(Rc<str>),
    ExpectingRule(RuleId),
    LeftRecursion(RuleId),
}

#[derive(Clone, Debug)]
pub struct Fail {
    pub pos: usize,
    pub kind: FailKind,
    pub msg: Msg,
    /// Rule stack, innermost first; only kept when this failure was the
    /// furthest so far when it was made.
    pub stack: Option<Rc<[RuleId]>>,
}

/// The furthest parse failure, as reported to users.
#[derive(Clone, Debug)]
pub struct ParseError {
    pub pos: usize,
    pub message: String,
    pub stack: Vec<&'static str>,
}

#[derive(Clone, Debug, Default)]
enum Cst {
    #[default]
    Empty,
    One(Val),
    Many(Vec<Val>),
}

#[derive(Clone, Default)]
struct State {
    ast: Vec<(&'static str, Val)>,
    cst: Cst,
    pos: usize,
}

type MemoKey = (usize, RuleId);

#[derive(Clone)]
struct RuleResult {
    node: Val,
    newpos: usize,
}

pub struct Parser<'a> {
    pub text: &'a str,
    pub pos: usize,
    pub config: &'a ParserConfig,
    grammar: &'a Grammar,
    regexes: &'static [Regex],
    dyn_regexes: HashMap<String, Regex>,
    states: Vec<State>,
    last_node: Val,
    rule_stack: Vec<RuleId>,
    memos: HashMap<MemoKey, Result<RuleResult, Fail>>,
    lr_memo_keys: Vec<MemoKey>,
    results: HashMap<MemoKey, Result<RuleResult, Fail>>,
    furthest: Option<Fail>,
    pub calls: usize,
}

impl<'a> Parser<'a> {
    pub fn new(text: &'a str, grammar: &'a Grammar, config: &'a ParserConfig) -> Self {
        Parser {
            text,
            pos: 0,
            config,
            grammar,
            regexes: grammar.regexes(),
            dyn_regexes: HashMap::new(),
            states: vec![State::default()],
            last_node: Val::None,
            rule_stack: Vec::new(),
            memos: HashMap::new(),
            lr_memo_keys: Vec::new(),
            results: HashMap::new(),
            furthest: None,
            calls: 0,
        }
    }

    pub fn parse(mut self) -> Result<Val, ParseError> {
        let start = self.grammar.start;
        match self.call(start) {
            Ok(()) => Ok(self.last_node.clone()),
            Err(e) => {
                self.set_furthest(&e);
                let f = self.furthest.clone().unwrap();
                Err(self.report(&f))
            }
        }
    }

    fn report(&self, f: &Fail) -> ParseError {
        let message = match &f.msg {
            Msg::Static(s) | Msg::Token(s) => s.to_string(),
            Msg::Pattern(i) => self.grammar.patterns[*i].to_string(),
            Msg::Dynamic(s) => s.to_string(),
            Msg::ExpectingRule(r) => format!("Expecting <{}>", self.grammar.rules[*r].name),
            Msg::LeftRecursion(r) => self.grammar.rules[*r].name.to_string(),
        };
        let stack = f
            .stack
            .as_ref()
            .map(|s| s.iter().map(|r| self.grammar.rules[*r].name).collect())
            .unwrap_or_default();
        ParseError { pos: f.pos, message, stack }
    }

    // -- state ----------------------------------------------------------------

    fn top(&mut self) -> &mut State {
        self.states.last_mut().unwrap()
    }

    fn make_fail(&self, kind: FailKind, msg: Msg) -> Fail {
        let stack = match &self.furthest {
            Some(f) if f.pos >= self.pos => None,
            _ => Some(self.rule_stack.iter().rev().copied().collect::<Vec<_>>().into()),
        };
        Fail { pos: self.pos, kind, msg, stack }
    }

    fn set_furthest(&mut self, e: &Fail) {
        if self.furthest.as_ref().map_or(true, |f| e.pos > f.pos) {
            self.furthest = Some(e.clone());
        }
    }

    pub fn error(&self, msg: &'static str) -> Fail {
        self.make_fail(FailKind::Other, Msg::Static(msg))
    }

    fn push_ast(&mut self, copy: bool) {
        let pos = self.pos;
        let ast = if copy { self.top().ast.clone() } else { Vec::new() };
        self.top().pos = pos;
        self.states.push(State { ast, cst: Cst::Empty, pos });
    }

    fn pop_ast(&mut self) {
        self.states.pop();
        self.pos = self.top().pos;
    }

    fn merge_ast(&mut self) {
        let pos = self.pos;
        let child = self.states.pop().unwrap();
        self.top().ast = child.ast;
        self.extend_cst(cst_to_val(child.cst));
        self.pos = pos;
    }

    fn push_cst(&mut self) {
        let ast = self.top().ast.clone();
        self.states.push(State { ast, cst: Cst::Empty, pos: 0 });
    }

    /// Pop a CST state; its AST (names set inside) carries over to the parent.
    fn pop_cst(&mut self) -> Cst {
        let child = self.states.pop().unwrap();
        self.top().ast = child.ast;
        child.cst
    }

    fn append_cst(&mut self, node: Val) {
        self.last_node = node.clone();
        let top = self.top();
        top.cst = match std::mem::take(&mut top.cst) {
            Cst::Empty => match node {
                Val::None => Cst::Empty,
                Val::List(v) => Cst::Many((*v).clone()),
                n => Cst::One(n),
            },
            Cst::Many(mut v) => {
                v.push(node);
                Cst::Many(v)
            }
            Cst::One(prev) => Cst::Many(vec![prev, node]),
        };
    }

    fn extend_cst(&mut self, node: Val) {
        self.last_node = node.clone();
        if node.is_none() {
            return;
        }
        let top = self.top();
        top.cst = match (std::mem::take(&mut top.cst), node) {
            (Cst::Empty, Val::List(v)) => Cst::Many((*v).clone()),
            (Cst::Empty, n) => Cst::One(n),
            (Cst::Many(mut prev), Val::List(v)) => {
                prev.extend(v.iter().cloned());
                Cst::Many(prev)
            }
            (Cst::One(prev), Val::List(v)) => {
                let mut all = vec![prev];
                all.extend(v.iter().cloned());
                Cst::Many(all)
            }
            (Cst::Many(mut prev), n) => {
                prev.push(n);
                Cst::Many(prev)
            }
            (Cst::One(prev), n) => Cst::Many(vec![prev, n]),
        };
    }

    fn ast_set(&mut self, name: &'static str, value: Val, force_list: bool) {
        let ast = &mut self.top().ast;
        match ast.iter_mut().find(|(k, _)| *k == name) {
            Some((_, prev)) => {
                *prev = match std::mem::take(prev) {
                    Val::None if force_list => Val::List(Rc::new(vec![value])),
                    Val::None => value,
                    Val::List(v) => {
                        let mut v = (*v).clone();
                        v.push(value);
                        Val::List(Rc::new(v))
                    }
                    p => Val::List(Rc::new(vec![p, value])),
                }
            }
            None => {
                let v = if force_list { Val::List(Rc::new(vec![value])) } else { value };
                ast.push((name, v));
            }
        }
    }

    // -- operations used by the grammar --------------------------------------

    pub fn name_last_node(&mut self, name: &'static str) {
        let v = self.last_node.clone();
        self.ast_set(name, v, false);
    }

    pub fn add_last_node_to_name(&mut self, name: &'static str) {
        let v = self.last_node.clone();
        self.ast_set(name, v, true);
    }

    pub fn define(&mut self, keys: &[&'static str], list_keys: &[&'static str]) {
        let old = std::mem::take(&mut self.top().ast);
        let mut ast: Vec<(&'static str, Val)> = Vec::with_capacity(keys.len() + list_keys.len() + old.len());
        for k in keys {
            if !ast.iter().any(|(n, _)| n == k) {
                ast.push((k, Val::None));
            }
        }
        for k in list_keys {
            if !ast.iter().any(|(n, _)| n == k) {
                ast.push((k, Val::List(Rc::new(Vec::new()))));
            }
        }
        for (k, v) in old {
            match ast.iter_mut().find(|(n, _)| *n == k) {
                Some((_, slot)) => *slot = v,
                None => ast.push((k, v)),
            }
        }
        self.top().ast = ast;
    }

    pub fn token(&mut self, token: &'static str) -> PResult {
        let rest = &self.text[self.pos..];
        if rest.starts_with(token) {
            let after = rest[token.len()..].chars().next();
            let guarded = token.chars().next().is_some_and(py_isalpha)
                && after.is_some_and(py_isalnum)
                && token.chars().all(py_isalnum);
            if !guarded {
                self.pos += token.len();
                self.append_cst(Val::Str(token.into()));
                return Ok(());
            }
        }
        Err(self.make_fail(FailKind::Token, Msg::Token(token)))
    }

    pub fn pattern(&mut self, id: usize) -> PResult {
        let re = &self.regexes[id];
        match re.find(&self.text[self.pos..]) {
            Some(m) => {
                let s = &self.text[self.pos..self.pos + m.end()];
                self.pos += m.end();
                self.append_cst(Val::Str(s.into()));
                Ok(())
            }
            None => Err(self.make_fail(FailKind::Pattern, Msg::Pattern(id))),
        }
    }

    /// Match a pattern given at run time (e.g. a declared identifier).
    pub fn dyn_pattern(&mut self, pat: &str) -> PResult {
        if !self.dyn_regexes.contains_key(pat) {
            self.dyn_regexes.insert(pat.to_string(), compile_pattern(pat));
        }
        let re = &self.dyn_regexes[pat];
        match re.find(&self.text[self.pos..]) {
            Some(m) => {
                let s = &self.text[self.pos..self.pos + m.end()];
                self.pos += m.end();
                self.append_cst(Val::Str(s.into()));
                Ok(())
            }
            None => Err(self.make_fail(FailKind::Pattern, Msg::Dynamic(pat.into()))),
        }
    }

    /// A builtin function keyword, unless it was imported under another name.
    pub fn renamed_pattern(&mut self, key: &str, default: usize) -> PResult {
        match self.config.rename.get(key) {
            Some(new) => {
                let new = new.clone();
                self.dyn_pattern(&new)
            }
            None => self.pattern(default),
        }
    }

    pub fn check_eof(&mut self) -> PResult {
        if self.pos < self.text.len() {
            return Err(self.make_fail(FailKind::Other, Msg::Static("Expecting end of text")));
        }
        Ok(())
    }

    /// `with self._choice():` — the body returns early when an option succeeds.
    pub fn choice(&mut self, body: impl FnOnce(&mut Self) -> PResult) -> PResult {
        self.last_node = Val::None;
        body(self)
    }

    /// `with self._option():` — returns whether the option matched; a failed
    /// option leaves no trace.
    pub fn option(&mut self, body: impl FnOnce(&mut Self) -> PResult) -> bool {
        self.last_node = Val::None;
        self.push_ast(true);
        self.last_node = Val::None;
        match body(self) {
            Ok(()) => {
                self.merge_ast();
                true
            }
            Err(_) => {
                self.pop_ast();
                false
            }
        }
    }

    pub fn optional(&mut self, body: impl FnOnce(&mut Self) -> PResult) {
        self.last_node = Val::None;
        self.choice(|p| {
            p.option(body);
            Ok(())
        })
        .ok();
    }

    pub fn group(&mut self, body: impl FnOnce(&mut Self) -> PResult) -> PResult {
        self.push_cst();
        match body(self) {
            Ok(()) => {
                let cst = self.pop_cst();
                self.extend_cst(cst_to_val(cst));
                Ok(())
            }
            Err(e) => {
                self.pop_cst();
                Err(e)
            }
        }
    }

    /// `&e`: succeed without consuming input or building anything.
    pub fn lookahead(&mut self, body: impl FnOnce(&mut Self) -> PResult) -> PResult {
        self.push_ast(false);
        let r = body(self);
        self.pop_ast();
        r
    }

    /// `!e`
    pub fn ifnot(&mut self, body: impl FnOnce(&mut Self) -> PResult) -> PResult {
        match self.lookahead(body) {
            Ok(()) => Err(self.make_fail(FailKind::Other, Msg::Static(""))),
            Err(_) => Ok(()),
        }
    }

    pub fn closure(&mut self, body: impl Fn(&mut Self) -> PResult) -> PResult {
        self.push_cst();
        let mut items = Vec::new();
        // first iteration, as an option
        let start = self.pos;
        let first = {
            self.push_ast(true);
            self.last_node = Val::None;
            match body(self) {
                Ok(()) => {
                    let pos = self.pos;
                    let child = self.states.pop().unwrap();
                    self.top().ast = child.ast;
                    self.pos = pos;
                    items.push(cst_to_val(child.cst));
                    true
                }
                Err(_) => {
                    self.pop_ast();
                    false
                }
            }
        };
        let _ = start;
        if first {
            self.repeat(&body, &mut items);
        }
        self.finish_closure(items);
        Ok(())
    }

    pub fn positive_closure(&mut self, body: impl Fn(&mut Self) -> PResult) -> PResult {
        self.push_cst();
        match body(self) {
            Ok(()) => {
                let first = std::mem::take(&mut self.top().cst);
                let mut items = vec![cst_to_val(first)];
                self.repeat(&body, &mut items);
                self.finish_closure(items);
                Ok(())
            }
            Err(e) => {
                self.pop_cst();
                Err(e)
            }
        }
    }

    fn repeat(&mut self, body: &impl Fn(&mut Self) -> PResult, items: &mut Vec<Val>) {
        loop {
            let p = self.pos;
            self.last_node = Val::None;
            self.push_ast(true);
            self.last_node = Val::None;
            // _isolate(block)
            self.push_cst();
            let r = body(self);
            let cst = self.pop_cst();
            let ok = r.is_ok() && self.pos != p;
            if ok {
                let pos = self.pos;
                let child = self.states.pop().unwrap();
                self.top().ast = child.ast;
                self.pos = pos;
                // unlike the first iteration, a later one that built nothing adds nothing
                match cst {
                    Cst::Many(v) => items.push(Val::Closure(Rc::new(v))),
                    Cst::One(v) => items.push(v),
                    Cst::Empty => {}
                }
            } else {
                self.pop_ast();
                break;
            }
        }
    }

    fn finish_closure(&mut self, items: Vec<Val>) {
        self.pop_cst();
        self.extend_cst(Val::Closure(Rc::new(items)));
    }

    // -- rules -----------------------------------------------------------------

    pub fn call(&mut self, rule: RuleId) -> PResult {
        self.calls += 1;
        self.rule_stack.push(rule);
        let pos = self.pos;
        self.last_node = Val::None;
        let r = self.recursive_call(rule);
        let out = match r {
            Ok(res) => {
                self.pos = res.newpos;
                self.append_cst(res.node);
                Ok(())
            }
            Err(e) if e.kind == FailKind::Pattern => {
                Err(self.make_fail(FailKind::Other, Msg::ExpectingRule(rule)))
            }
            Err(e) => {
                self.pos = pos;
                self.set_furthest(&e);
                Err(e)
            }
        };
        self.rule_stack.pop();
        out
    }

    fn recursive_call(&mut self, rule: RuleId) -> Result<RuleResult, Fail> {
        let key = (self.pos, rule);
        let info = &self.grammar.rules[rule];
        if !info.leftrec {
            return self.invoke_rule(rule, key);
        }
        if let Some(r) = self.results.get(&key) {
            return r.clone();
        }
        let mut result: Result<RuleResult, Fail> =
            Err(self.make_fail(FailKind::LeftRecursion, Msg::LeftRecursion(rule)));
        self.results.insert(key, result.clone());
        let initial = self.pos;
        let mut lastpos: isize = initial as isize - 1;
        loop {
            self.clear_recursion_errors();
            let new_result = match self.invoke_rule(rule, key) {
                Ok(r) => {
                    self.pos = initial;
                    r
                }
                Err(_) => break,
            };
            if new_result.newpos as isize > lastpos {
                lastpos = new_result.newpos as isize;
                self.results.insert(key, Ok(new_result.clone()));
                result = Ok(new_result);
            } else {
                break;
            }
        }
        result
    }

    fn clear_recursion_errors(&mut self) {
        for key in std::mem::take(&mut self.lr_memo_keys) {
            if let Some(Err(f)) = self.memos.get(&key) {
                if f.kind == FailKind::LeftRecursion {
                    self.memos.remove(&key);
                }
            }
        }
    }

    fn memoize(&mut self, key: MemoKey, value: Result<RuleResult, Fail>) {
        if let Err(f) = &value {
            if f.kind == FailKind::LeftRecursion {
                self.lr_memo_keys.push(key);
            }
        }
        self.memos.insert(key, value);
    }

    fn invoke_rule(&mut self, rule: RuleId, key: MemoKey) -> Result<RuleResult, Fail> {
        if let Some(m) = self.memos.get(&key) {
            return m.clone();
        }
        let info = &self.grammar.rules[rule];
        let memo = info.memo;
        if memo {
            let guard = self.make_fail(FailKind::LeftRecursion, Msg::LeftRecursion(rule));
            self.memoize(key, Err(guard));
        }
        self.push_ast(false);
        let r = (info.body)(self);
        let out = match r {
            Ok(()) => {
                let node = self.get_node(key.0, info);
                let res = RuleResult { node, newpos: self.pos };
                if memo {
                    self.memoize(key, Ok(res.clone()));
                }
                Ok(res)
            }
            Err(e) => {
                if memo {
                    self.memoize(key, Err(e.clone()));
                }
                Err(e)
            }
        };
        self.pop_ast();
        out
    }

    fn get_node(&mut self, pos: usize, info: &RuleInfo) -> Val {
        let endpos = self.pos;
        let top = self.top();
        if !top.ast.is_empty() {
            let fields = std::mem::take(&mut top.ast);
            Val::Node(Rc::new(PNode { class: info.class, span: Some((pos, endpos)), fields, raw: Val::None }))
        } else {
            let raw = match std::mem::take(&mut top.cst) {
                Cst::Empty => Val::None,
                Cst::One(v) => v,
                Cst::Many(v) => Val::Tuple(Rc::new(v)),
            };
            match info.class {
                Some(c) => Val::Node(Rc::new(PNode { class: Some(c), span: None, fields: Vec::new(), raw })),
                None => raw,
            }
        }
    }

    /// Call a rule by name (for imported builtin functions).
    pub fn call_named(&mut self, name: &str) -> PResult {
        match self.grammar.rule_id(name) {
            Some(r) => self.call(r),
            None => Err(self.error("unknown rule")),
        }
    }
}

fn cst_to_val(c: Cst) -> Val {
    match c {
        Cst::Empty => Val::None,
        Cst::One(v) => v,
        Cst::Many(v) => Val::List(Rc::new(v)),
    }
}

/// Python's `str.isalpha` (letters).
pub fn py_isalpha(c: char) -> bool {
    static RE: OnceLock<Regex> = OnceLock::new();
    if c.is_ascii() {
        return c.is_ascii_alphabetic();
    }
    let re = RE.get_or_init(|| Regex::new(r"^\p{L}$").unwrap());
    let mut buf = [0u8; 4];
    re.is_match(c.encode_utf8(&mut buf))
}

/// Python's `str.isalnum` (letters and numbers).
pub fn py_isalnum(c: char) -> bool {
    static RE: OnceLock<Regex> = OnceLock::new();
    if c.is_ascii() {
        return c.is_ascii_alphanumeric();
    }
    let re = RE.get_or_init(|| Regex::new(r"^[\p{L}\p{N}]$").unwrap());
    let mut buf = [0u8; 4];
    re.is_match(c.encode_utf8(&mut buf))
}
