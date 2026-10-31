//! Code generation base (la_parser/ir_visitor.py `IRVisitor` and
//! la_parser/codegen.py `CodeGen`, `CodeFrame`, `CodeModule`).
//!
//! Each backend is a struct holding a `VisitorBase` (the Python IRVisitor
//! attributes) and implementing `Backend`, whose `visit` dispatches on the IR
//! node type to `visit_xxx` methods. The default methods are those of
//! `IRBaseVisitor`/`CodeGen`; a backend overrides what its Python class
//! overrides. All visits return `CodeNodeInfo`; the LaTeX family, which
//! returns strings in Python, uses `CodeNodeInfo::s(...)` and `.content.s()`.

#![allow(non_snake_case)]

use crate::helper::{is_keyword, KeywordSet};
use crate::ir::{GPType, IRNodeType, N};
use crate::packages::{self, Backend as Kind};
use crate::types::T;
use crate::walker::{BuiltinModuleData, FuncDataDict, MeshData, ParamsData, Symtab, TypeWalker, PD, GLOBAL};
use indexmap::{IndexMap, IndexSet};
use std::cell::RefCell;
use std::rc::Rc;

pub const CLASS_NAME: &str = "heartlib";

/// `CodeNodeInfo.content`: a string, or matrix rows (lists of strings).
#[derive(Clone, Debug)]
pub enum Content {
    Str(String),
    List(Vec<Content>),
}

impl Default for Content {
    fn default() -> Self {
        Content::Str(String::new())
    }
}

impl Content {
    pub fn s(&self) -> String {
        match self {
            Content::Str(s) => s.clone(),
            Content::List(_) => panic!("content is a list"),
        }
    }
    pub fn list(&self) -> Vec<Content> {
        match self {
            Content::List(v) => v.clone(),
            Content::Str(_) => panic!("content is a string"),
        }
    }
    pub fn strs(&self) -> Vec<String> {
        self.list().iter().map(|c| c.s()).collect()
    }
}

/// `CodeNodeInfo(content, pre_list)`
#[derive(Clone, Debug, Default)]
pub struct CodeNodeInfo {
    pub content: Content,
    pub pre_list: Vec<String>,
}

impl CodeNodeInfo {
    pub fn new(content: impl Into<String>) -> Self {
        CodeNodeInfo { content: Content::Str(content.into()), pre_list: Vec::new() }
    }
    pub fn with(content: impl Into<String>, pre_list: Vec<String>) -> Self {
        CodeNodeInfo { content: Content::Str(content.into()), pre_list }
    }
    pub fn list(items: Vec<Content>, pre_list: Vec<String>) -> Self {
        CodeNodeInfo { content: Content::List(items), pre_list }
    }
    /// The content string.
    pub fn s(&self) -> String {
        self.content.s()
    }
}

/// `CodeFrame`
#[derive(Clone, Debug, Default)]
pub struct CodeFrame {
    pub parse_type: Option<Kind>,
    pub desc: String,
    pub include: String,
    pub namespace: String,
    pub struct_: String,
    pub rand_data: String,
    pub main: String,
    pub expr: String,
    pub expr_dict: IndexMap<String, String>,
    pub pre_str: String,
    pub post_str: String,
    pub pre_block: String,
    pub extra_include: String,
    pub extra_funcs: Vec<String>,
}

impl CodeFrame {
    pub fn new(kind: Kind) -> Self {
        CodeFrame { parse_type: Some(kind), ..Default::default() }
    }

    pub fn get_code(&self) -> String {
        match self.parse_type {
            Some(Kind::Eigen) | Some(Kind::Numpy) => format!(
                "{}{}{}{}{}{}\n\n{}\n\n\n{}",
                self.desc,
                self.include,
                self.extra_include,
                self.namespace,
                self.get_extra_func_impl(),
                self.struct_,
                self.rand_data,
                self.main
            ),
            Some(Kind::Matlab) => {
                format!("{}{}{}{}", self.extra_include, self.namespace, self.get_extra_func_impl(), self.struct_)
            }
            _ => self.main.clone(),
        }
    }

    pub fn get_extra_func_impl(&self) -> String {
        let kind = self.parse_type.unwrap_or(Kind::Eigen);
        self.extra_funcs.iter().map(|f| packages::get_gp_func_impl(f, kind)).collect()
    }

    pub fn get_mathjax_content(&self) -> String {
        format!("{}{}{}", self.pre_str, self.expr, self.post_str)
    }

    pub fn reset(&mut self) {
        let pt = self.parse_type;
        *self = CodeFrame { parse_type: pt, namespace: std::mem::take(&mut self.namespace), ..Default::default() };
    }
}

/// `CodeModule`: a compiled imported module.
#[derive(Clone, Debug, Default)]
pub struct CodeModule {
    pub frame: CodeFrame,
    pub name: String,
    pub syms: Vec<String>,
    pub r_syms: Vec<String>,
    pub params: Vec<String>,
    pub func_sig_dict: IndexMap<String, String>,
}

/// The attributes of `IRVisitor` (shared by all backends).
#[derive(Clone)]
pub struct VisitorBase {
    pub parse_type: Kind,
    pub pre_str: String,
    pub post_str: String,
    pub def_dict: IndexMap<String, bool>,
    pub local_func_parsing: bool,
    pub local_func_name: String,
    pub name_cnt_dict: Rc<RefCell<IndexMap<String, i64>>>,
    pub ret_symbol: Option<String>,
    pub unofficial_method: bool,
    pub has_opt: bool,
    pub need_mutator: bool,
    pub has_derivative: bool,
    pub content: String,
    pub local_func_def: String,
    pub local_func_syms: Vec<String>,
    pub local_func_dict: IndexMap<String, Symtab>,
    pub extra_symtable: Symtab,
    pub scope_list: Vec<String>,
    pub visiting_opt: bool,
    pub opt_key: String,
    pub opt_dict: IndexMap<String, PD>,
    pub name_convention_dict: IndexMap<String, String>,
    pub func_name: String,
    pub param_name_test: String,
    pub convert_matrix: bool,
    pub visiting_lhs: bool,
    pub visiting_func_name: bool,
    pub visiting_diff_eq: bool,
    pub visiting_diff_init: bool,
    pub visiting_sum: bool,
    pub class_only: bool,
    pub lhs_list: Vec<String>,
    pub lhs_on_der: Vec<String>,
    pub module_list: Vec<CodeModule>,
    pub module_syms: IndexMap<String, T>,
    pub builtin_module_dict: IndexMap<String, BuiltinModuleData>,
    pub la_content: String,
    pub new_id_prefix: String,
    pub comment_placeholder: String,
    pub comment_dict: IndexMap<String, String>,
    pub declared_symbols: IndexSet<String>,
    pub used_params: Vec<String>,
    pub der_vars: Vec<String>,
    pub der_vars_mapping: IndexMap<String, String>,
    pub der_defined_lhs_list: Vec<String>,
    pub opt_syms: Vec<String>,
    pub mesh_dict: IndexMap<String, MeshData>,
    pub duplicate_func_list: Vec<String>,
    pub mesh_type_list: Vec<crate::types::MeshKind>,
    pub main_param: PD,
    pub func_data_dict: FuncDataDict,
    pub code_frame: CodeFrame,
}

impl VisitorBase {
    pub fn new(kind: Kind) -> Self {
        VisitorBase {
            parse_type: kind,
            pre_str: String::new(),
            post_str: String::new(),
            def_dict: IndexMap::new(),
            local_func_parsing: false,
            local_func_name: String::new(),
            name_cnt_dict: Rc::new(RefCell::new(IndexMap::new())),
            ret_symbol: None,
            unofficial_method: false,
            has_opt: false,
            need_mutator: false,
            has_derivative: false,
            content: String::new(),
            local_func_def: String::new(),
            local_func_syms: Vec::new(),
            local_func_dict: IndexMap::new(),
            extra_symtable: crate::walker::new_symtab(),
            scope_list: vec![GLOBAL.into()],
            visiting_opt: false,
            opt_key: String::new(),
            opt_dict: IndexMap::new(),
            name_convention_dict: IndexMap::new(),
            func_name: "myExpression".into(),
            param_name_test: "p".into(),
            convert_matrix: false,
            visiting_lhs: false,
            visiting_func_name: false,
            visiting_diff_eq: false,
            visiting_diff_init: false,
            visiting_sum: false,
            class_only: false,
            lhs_list: Vec::new(),
            lhs_on_der: Vec::new(),
            module_list: Vec::new(),
            module_syms: IndexMap::new(),
            builtin_module_dict: IndexMap::new(),
            la_content: String::new(),
            new_id_prefix: String::new(),
            comment_placeholder: "iheartlacomment".into(),
            comment_dict: IndexMap::new(),
            declared_symbols: IndexSet::new(),
            used_params: Vec::new(),
            der_vars: Vec::new(),
            der_vars_mapping: IndexMap::new(),
            der_defined_lhs_list: Vec::new(),
            opt_syms: Vec::new(),
            mesh_dict: IndexMap::new(),
            duplicate_func_list: Vec::new(),
            mesh_type_list: Vec::new(),
            main_param: ParamsData::new_shared(),
            func_data_dict: Rc::new(RefCell::new(IndexMap::new())),
            code_frame: CodeFrame::new(kind),
        }
    }

    /// `IRVisitor.init_type(type_walker, func_name)` (and `CodeGen.init_type`,
    /// which first resets the code frame).
    pub fn init_type(&mut self, w: &TypeWalker, func_name: Option<&str>) {
        self.code_frame.reset();
        // ir_visitor.py: a backend that raised mid-visit leaves scopes pushed
        self.scope_list = vec![GLOBAL.into()];
        self.main_param = w.main_param.clone();
        for key in self.symtable().borrow().keys() {
            self.def_dict.insert(key.clone(), false);
        }
        self.func_data_dict = w.func_data_dict.clone();
        self.name_cnt_dict = w.name_cnt_dict.clone();
        self.ret_symbol = w.ret_symbol.clone();
        self.unofficial_method = w.unofficial_method;
        self.has_opt = w.has_opt;
        self.has_derivative = w.has_derivative;
        self.need_mutator = w.need_mutator;
        self.lhs_list = w.lhs_list.clone();
        self.la_content = w.la_content.clone();
        self.local_func_syms = w.local_func_syms.clone();
        self.local_func_dict = w.local_func_dict.clone();
        self.extra_symtable = w.extra_symtable.clone();
        self.opt_dict = w.opt_dict.clone();
        self.used_params = w.used_params.clone();
        self.der_vars = w.der_vars.clone();
        self.der_defined_lhs_list = w.der_defined_lhs_list.clone();
        self.lhs_on_der = w.lhs_on_der.clone();
        self.der_vars_mapping.clear();
        for param in self.der_vars.clone() {
            if self.get_sym_type(&param).is_scalar() {
                self.der_vars_mapping.insert(param.clone(), param);
            } else {
                let n = self.generate_var_name(&format!("new_{param}"));
                self.der_vars_mapping.insert(param, n);
            }
        }
        self.builtin_module_dict = w.builtin_module_dict.clone();
        self.opt_syms = w.opt_syms.clone();
        self.mesh_dict = w.mesh_dict.clone();
        self.class_only = w.class_only;
        self.mesh_type_list = w.mesh_type_list.clone();
        self.func_name = match func_name {
            Some(f) => f.replace(' ', ""),
            None => CLASS_NAME.into(),
        };
        self.declared_symbols.clear();
        self.local_func_def.clear();
        self.comment_dict.clear();
        self.duplicate_func_list.clear();
    }

    pub fn add_name_conventions(&mut self, d: &IndexMap<String, String>) {
        for (k, v) in d {
            self.name_convention_dict.insert(k.clone(), v.clone());
        }
    }

    pub fn del_name_conventions(&mut self, d: &IndexMap<String, String>) {
        for k in d.keys() {
            self.name_convention_dict.shift_remove(k);
        }
    }

    pub fn is_local_param(&self, sym: &str) -> bool {
        self.local_func_dict.values().any(|v| !v.borrow().is_empty() && v.borrow().contains_key(sym))
    }

    /// `get_cur_param_data()`
    pub fn get_cur_param_data(&self) -> PD {
        let cur = self.scope_list.last().map(String::as_str).unwrap_or(GLOBAL);
        if cur != GLOBAL {
            return self.func_data_dict.borrow()[cur].params_data.clone();
        }
        self.main_param.clone()
    }

    /// `self.symtable` (the current scope's)
    pub fn symtable(&self) -> Symtab {
        self.get_cur_param_data().borrow().symtable()
    }

    /// `self.parameters` (the current scope's)
    pub fn parameters(&self) -> Vec<String> {
        self.get_cur_param_data().borrow().param_names()
    }

    pub fn convert_seq_dim_dict(&self) -> IndexMap<String, IndexMap<usize, String>> {
        let mut seq: IndexMap<String, IndexMap<usize, String>> = IndexMap::new();
        for (key, vd) in self.get_cur_param_data().borrow().seq_dim_dict.iter() {
            for (sym, idx) in vd {
                let e = seq.entry(sym.clone()).or_default();
                for i in idx {
                    e.insert(*i, key.clone());
                }
            }
        }
        seq
    }

    pub fn get_dynamic_seq_set(&self) -> IndexSet<String> {
        let mut s = IndexSet::new();
        for v in self.get_cur_param_data().borrow().seq_dim_dict.values() {
            s.extend(v.keys().cloned());
        }
        s
    }

    pub fn get_intersect_list(&self) -> Vec<IndexSet<String>> {
        let seq_set = self.get_dynamic_seq_set();
        let mut out = Vec::new();
        for subs in self.get_cur_param_data().borrow().subscripts.values() {
            let inter: IndexSet<String> = subs.iter().filter(|s| seq_set.contains(*s)).cloned().collect();
            if inter.len() > 1 {
                out.push(inter);
            }
        }
        out
    }

    pub fn get_same_seq_list(&self, name: &str) -> Vec<IndexMap<String, Vec<usize>>> {
        self.get_cur_param_data().borrow().seq_dim_dict.values().filter(|v| v.contains_key(name)).cloned().collect()
    }

    pub fn get_same_seq_symbols(&self, name: &str) -> IndexSet<String> {
        let mut s = IndexSet::new();
        for v in self.get_cur_param_data().borrow().seq_dim_dict.values() {
            if v.contains_key(name) {
                s.extend(v.keys().cloned());
            }
        }
        s.shift_remove(name);
        s
    }

    /// `get_sym_type(sym)`
    pub fn get_sym_type(&self, sym: &str) -> T {
        for scope in self.scope_list.iter().rev() {
            let st = if scope == GLOBAL {
                self.main_param.borrow().symtable()
            } else {
                self.func_data_dict.borrow()[scope.as_str()].params_data.borrow().symtable()
            };
            let found = st.borrow().get(sym).cloned();
            if let Some(t) = found {
                return t;
            }
        }
        if let Some(t) = self.extra_symtable.borrow().get(sym) {
            return t.clone();
        }
        T::invalid()
    }

    /// `generate_var_name(base)`: `base`, `base_1`, `base_2`, ...
    pub fn generate_var_name(&self, base: &str) -> String {
        let mut index = self.name_cnt_dict.borrow().get(base).copied().unwrap_or(-1);
        index += 1;
        let st = self.symtable();
        let ret = loop {
            let r = if index == 0 {
                format!("{}{}", self.new_id_prefix, base)
            } else {
                format!("{}{}_{}", self.new_id_prefix, base, index)
            };
            index += 1;
            if !st.borrow().contains_key(&r) {
                break r;
            }
        };
        self.name_cnt_dict.borrow_mut().insert(base.to_string(), index - 1);
        ret
    }

    pub fn push_scope(&mut self, scope: &str) {
        self.scope_list.push(scope.to_string());
    }

    pub fn pop_scope(&mut self) {
        self.scope_list.pop();
    }

    pub fn is_main_scope(&self) -> bool {
        self.scope_list.last().map(String::as_str) == Some(GLOBAL)
    }

    pub fn keyword_set(&self) -> KeywordSet {
        match self.parse_type {
            Kind::Numpy => KeywordSet::Numpy,
            Kind::Eigen => KeywordSet::Eigen,
            _ => KeywordSet::Both,
        }
    }

    pub fn is_keyword(&self, name: &str) -> bool {
        is_keyword(name, self.keyword_set())
    }

    pub fn get_bin_comp_str(&self, comp_type: IRNodeType) -> &'static str {
        match comp_type {
            IRNodeType::Eq => "==",
            IRNodeType::Ne => "!=",
            IRNodeType::Lt => "<",
            IRNodeType::Le => "<=",
            IRNodeType::Gt => ">",
            IRNodeType::Ge => ">=",
            _ => "",
        }
    }

    pub fn get_int_dim(&self, dims: &[crate::dims::Dim]) -> i64 {
        dims.iter().find_map(|d| d.as_int()).unwrap_or(-1)
    }

    pub fn get_dim_check_str(&self) -> Vec<String> {
        let mut out = Vec::new();
        for set in self.get_cur_param_data().borrow().same_dim_list.iter() {
            for d in set.iter().skip(1) {
                out.push(format!("{} == {}", set[0], d));
            }
        }
        out
    }

    pub fn update_prelist_str(&self, pre_list: &[String], prefix: &str) -> String {
        let mut lines = Vec::new();
        for line in pre_list {
            for s in line.split('\n') {
                if !s.is_empty() {
                    lines.push(s.to_string());
                }
            }
        }
        format!("{}{}\n", prefix, lines.join(&format!("\n{prefix}")))
    }

    pub fn convert_bound_symbol(&self, name: &str) -> String {
        let pd = self.get_cur_param_data();
        let pd = pd.borrow();
        if pd.dim_seq_set.contains(name) {
            if let Some((k, _)) = pd.dim_dict.get(name).and_then(|d| d.first()) {
                return k.clone();
            }
        }
        name.to_string()
    }

    pub fn has_special_symbol(&self, target: &str) -> bool {
        ["∂", "⁰", "¹", "²", "ᵀ"].iter().any(|k| target.contains(k))
    }

    /// `convert_unicode(name)`: make a name valid in the target language.
    pub fn convert_unicode(&self, name: &str) -> String {
        crate::codegen::names::convert_unicode(self.parse_type, name)
    }

    /// `fill_comment(content)`
    pub fn fill_comment(&self, content: &str) -> String {
        let mut content = content.to_string();
        for (k, v) in &self.comment_dict {
            let re = regex::Regex::new(&format!(r"(?s)(?P<prefix>[ \t]*){}", regex::escape(k))).unwrap();
            let matches: Vec<(String, String)> = re
                .captures_iter(&content.clone())
                .map(|m| (m.get(0).unwrap().as_str().to_string(), m.name("prefix").unwrap().as_str().to_string()))
                .collect();
            for (whole, prefix) in matches {
                if !prefix.is_empty() {
                    let rep = self.update_prelist_str(&[v.clone()], &prefix);
                    content = content.replace(&whole, &rep[..rep.len() - 1]);
                } else {
                    content = content.replace(&whole, v);
                }
            }
        }
        content
    }

    /// `trim_content(content)`: rename identifiers containing special characters.
    pub fn trim_content(&self, content: &str) -> String {
        let mut res = content.to_string();
        let mut ids: Vec<String> = self.symtable().borrow().keys().cloned().collect();
        let pd = self.get_cur_param_data();
        let id_keys: Vec<String> = pd.borrow().ids_dict.keys().cloned().collect();
        for id in id_keys {
            ids.extend(self.get_all_ids(&id).1);
        }
        for fd in self.func_data_dict.borrow().values() {
            ids.extend(fd.params_data.borrow().symtable().borrow().keys().cloned());
        }
        let mut uniq: Vec<String> = ids.into_iter().collect::<IndexSet<_>>().into_iter().filter(|x| x != "*").collect();
        // Python sorts a set by length (stable); ties keep set order, which
        // differs between runs in Python, so break ties deterministically
        uniq.sort_by(|a, b| b.chars().count().cmp(&a.chars().count()));
        let mut names: Vec<String> = Vec::new();
        let st = self.symtable();
        for special in uniq {
            let convert = self.has_special_symbol(&special)
                || ((special.contains('`') || self.parse_type == Kind::Matlab) && !crate::helper::str_isnumeric(&special));
            if !convert {
                continue;
            }
            let mut new_str = self.convert_unicode(&special).replace('-', "_");
            if new_str != special {
                while names.contains(&new_str) || st.borrow().contains_key(&new_str) || self.is_keyword(&new_str) {
                    if self.parse_type == Kind::Matlab {
                        new_str.push('_');
                    } else {
                        new_str = format!("_{new_str}");
                    }
                }
                names.push(new_str.clone());
                res = res.replace(&special, &new_str);
            }
        }
        self.fill_comment(&res)
    }

    /// `filter_symbol(symbol)` (the visitor's version)
    pub fn filter_symbol(&self, symbol: &str) -> String {
        if symbol.contains('`') {
            let new_symbol = symbol.replace('`', "");
            if crate::helper::str_isnumeric(&new_symbol) {
                return format!("num{new_symbol}");
            }
            let ascii_word = !new_symbol.is_empty() && new_symbol.chars().all(|c| c.is_ascii_alphabetic());
            if !ascii_word || is_keyword(&new_symbol, KeywordSet::Both) {
                return symbol.to_string();
            }
            return new_symbol;
        }
        symbol.to_string()
    }

    pub fn contain_subscript(&self, identifier: &str) -> bool {
        self.get_cur_param_data().borrow().ids_dict.get(identifier).is_some_and(|i| i.contain_subscript())
    }

    /// `get_all_ids(identifier)`
    pub fn get_all_ids(&self, identifier: &str) -> (String, Vec<String>) {
        if let Some(i) = self.get_cur_param_data().borrow().ids_dict.get(identifier) {
            return (i.main_id.clone(), i.subs.items());
        }
        let res: Vec<&str> = identifier.split('_').collect();
        assert!(res.len() > 1, "list index out of range");
        (res[0].to_string(), res[1].chars().map(|c| c.to_string()).collect())
    }

    pub fn get_result_type(&self) -> String {
        self.func_name.clone()
    }

    pub fn get_main_id(&self, identifier: &str) -> String {
        if let Some(i) = self.get_cur_param_data().borrow().ids_dict.get(identifier) {
            return i.main_id.clone();
        }
        if self.contain_subscript(identifier) {
            return self.get_all_ids(identifier).0;
        }
        identifier.to_string()
    }

    /// `CodeGen.get_builtin_func_name(name)`
    pub fn get_builtin_func_name(&self, name: &str) -> String {
        let mut res = name.to_string();
        for (key, data) in &self.builtin_module_dict {
            if packages::CLASS_PACKAGES.contains(&key.as_str()) && key == packages::MESH_HELPER {
                if let Some(v) = data.inverse_dict.get(name) {
                    res = v.clone();
                }
            }
        }
        res
    }

    /// `CodeGen.convert_overloaded_name(name)`
    pub fn convert_overloaded_name(&self, name: &str) -> String {
        packages::backend_overloading_name(self.parse_type, name)
    }
}

pub mod names;
pub mod numpy;
pub mod eigen;
pub mod matlab;
pub mod latex;
pub mod mathjax;
pub mod macromathjax;

/// A code generator for a backend.
pub fn new_backend(kind: Kind) -> Box<dyn Backend> {
    match kind {
        Kind::Numpy => Box::new(numpy::CodeGenNumpy::new()),
        Kind::Eigen => Box::new(eigen::CodeGenEigen::new()),
        Kind::Matlab => Box::new(matlab::CodeGenMatlab::new()),
        Kind::Latex => Box::new(latex::CodeGenLatex::new()),
        Kind::Mathjax => Box::new(mathjax::CodeGenMathjax::new()),
        Kind::MacroMathjax => Box::new(macromathjax::CodeGenMacroMathjax::new()),
    }
}

/// A code generator. `visit` dispatches on the node type; the default
/// methods are those of the Python base classes.
pub trait Backend {
    fn base(&self) -> &VisitorBase;
    fn base_mut(&mut self) -> &mut VisitorBase;

    /// `init_type(type_walker, func_name)`
    fn init_type(&mut self, w: &TypeWalker, func_name: Option<&str>) {
        self.base_mut().init_type(w, func_name);
    }

    /// `visit_code(node)`: generate code for the start node.
    fn visit_code(&mut self, node: &N) -> CodeFrame {
        self.base_mut().module_list = node.module_list();
        self.base_mut().module_syms = node.module_syms();
        let body = self.visit(node, &Kw::default());
        let b = self.base_mut();
        b.content = format!("{}{}{}", b.pre_str, body.s(), b.post_str);
        b.code_frame.clone()
    }

    fn visit(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        use IRNodeType::*;
        match node.node_type() {
            Id => self.visit_id(node, kw),
            Double => self.visit_double(node, kw),
            Fraction => self.visit_fraction(node, kw),
            Integer => self.visit_integer(node, kw),
            Factor => self.visit_factor(node, kw),
            Expression => self.visit_expression(node, kw),
            Subexpression => self.visit_sub_expr(node, kw),
            Constant => self.visit_constant(node, kw),
            Cast => self.visit_cast(node, kw),
            Start => self.visit_start(node, kw),
            Block => self.visit_block(node, kw),
            Assignment => self.visit_assignment(node, kw),
            If => self.visit_if(node, kw),
            Function => self.visit_function(node, kw),
            LocalFunc => self.visit_local_func(node, kw),
            Equation => self.visit_equation(node, kw),
            Destructuring => self.visit_destructuring(node, kw),
            Condition => self.visit_condition(node, kw),
            In => self.visit_in(node, kw),
            NotIn => self.visit_not_in(node, kw),
            BinComp => self.visit_bin_comp(node, kw),
            Add => self.visit_add(node, kw),
            Sub => self.visit_sub(node, kw),
            Mul => self.visit_mul(node, kw),
            Div => self.visit_div(node, kw),
            Union => self.visit_union(node, kw),
            Intersection => self.visit_intersection(node, kw),
            Difference => self.visit_difference(node, kw),
            AddSub => self.visit_add_sub(node, kw),
            Summation => self.visit_summation(node, kw),
            UnionSequence => self.visit_union_sequence(node, kw),
            Norm => self.visit_norm(node, kw),
            Transpose => self.visit_transpose(node, kw),
            PseudoInverse => self.visit_pseudoinverse(node, kw),
            Squareroot => self.visit_squareroot(node, kw),
            Power => self.visit_power(node, kw),
            Solver => self.visit_solver(node, kw),
            Derivative => self.visit_derivative(node, kw),
            MathFunc => self.visit_math_func(node, kw),
            GPFunction => self.visit_gp_func(node, kw),
            Optimize => self.visit_optimize(node, kw),
            Domain => self.visit_domain(node, kw),
            Integral => self.visit_integral(node, kw),
            InnerProduct => self.visit_inner_product(node, kw),
            FroProduct => self.visit_fro_product(node, kw),
            HadamardProduct => self.visit_hadamard_product(node, kw),
            CrossProduct => self.visit_cross_product(node, kw),
            KroneckerProduct => self.visit_kronecker_product(node, kw),
            DotProduct => self.visit_dot_product(node, kw),
            Divergence => self.visit_divergence(node, kw),
            Gradient => self.visit_gradient(node, kw),
            Laplace => self.visit_laplace(node, kw),
            Partial => self.visit_partial(node, kw),
            Size => self.visit_size(node, kw),
            Matrix => self.visit_matrix(node, kw),
            MatrixRows => self.visit_matrix_rows(node, kw),
            MatrixRow => self.visit_matrix_row(node, kw),
            MatrixRowCommas => self.visit_matrix_row_commas(node, kw),
            ExpInMatrix => self.visit_exp_in_matrix(node, kw),
            MultiConds => self.visit_multi_conditionals(node, kw),
            SparseMatrix => self.visit_sparse_matrix(node, kw),
            SparseIfs => self.visit_sparse_ifs(node, kw),
            SparseIf => self.visit_sparse_if(node, kw),
            SparseOther => self.visit_sparse_other(node, kw),
            NumMatrix => self.visit_num_matrix(node, kw),
            Vector => self.visit_vector(node, kw),
            Set => self.visit_set(node, kw),
            ToMatrix => self.visit_to_matrix(node, kw),
            ToDouble => self.visit_to_double(node, kw),
            ElementConvert => self.visit_element_convert(node, kw),
            MatrixIndex => self.visit_matrix_index(node, kw),
            VectorIndex => self.visit_vector_index(node, kw),
            SequenceIndex => self.visit_sequence_index(node, kw),
            SeqDimIndex => self.visit_seq_dim_index(node, kw),
            TupleIndex => self.visit_tuple_index(node, kw),
            SetIndex => self.visit_set_index(node, kw),
            ParamsBlock => self.visit_params_block(node, kw),
            WhereConditions => self.visit_where_conditions(node, kw),
            WhereCondition => self.visit_where_condition(node, kw),
            MatrixType => self.visit_matrix_type(node, kw),
            VectorType => self.visit_vector_type(node, kw),
            SetType => self.visit_set_type(node, kw),
            ScalarType => self.visit_scalar_type(node, kw),
            FunctionType => self.visit_function_type(node, kw),
            MappingType => self.visit_mapping_type(node, kw),
            TupleType => self.visit_tuple_type(node, kw),
            NamedType => self.visit_named_type(node, kw),
            Import => self.visit_import(node, kw),
            OdeFirstOrder => self.visit_first_order_ode(node, kw),
            other => panic!("invalid node type {other:?}"),
        }
    }

    // -- IRBaseVisitor / IRVisitor / CodeGen defaults ------------------------

    fn visit_id(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_id(self, node, kw)
    }
    fn visit_double(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_double(self, node, kw)
    }
    fn visit_fraction(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_fraction(self, node, kw)
    }
    fn visit_integer(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_integer(self, node, kw)
    }
    fn visit_factor(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_factor(self, node, kw)
    }
    fn visit_expression(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_expression(self, node, kw)
    }
    fn visit_sub_expr(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_sub_expr(self, node, kw)
    }
    fn visit_start(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_start(self, node, kw)
    }
    fn visit_add(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_add(self, node, kw)
    }
    fn visit_sub(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_sub(self, node, kw)
    }
    fn visit_function(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_function(self, node, kw)
    }
    fn visit_matrix_rows(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_matrix_rows(self, node, kw)
    }
    fn visit_matrix_row(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_matrix_row(self, node, kw)
    }
    fn visit_matrix_row_commas(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_matrix_row_commas(self, node, kw)
    }
    fn visit_exp_in_matrix(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_exp_in_matrix(self, node, kw)
    }
    fn visit_to_matrix(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_to_matrix(self, node, kw)
    }
    fn visit_to_double(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_to_double(self, node, kw)
    }
    fn get_mesh_str(&self, mesh: &str) -> String {
        mesh.to_string()
    }
    fn visit_gp_func(&mut self, node: &N, kw: &Kw) -> CodeNodeInfo {
        super_visit_gp_func(self, node, kw)
    }

    // methods that IRBaseVisitor defines as `pass` (returning None)
    fn visit_constant(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_cast(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_block(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_assignment(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_if(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_local_func(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_equation(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_destructuring(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_condition(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_in(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_not_in(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_bin_comp(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_mul(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_div(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_union(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_intersection(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_difference(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_add_sub(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_summation(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_union_sequence(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_norm(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_transpose(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_pseudoinverse(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_squareroot(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_power(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_solver(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_derivative(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_math_func(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_optimize(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_domain(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_integral(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_inner_product(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_fro_product(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_hadamard_product(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_cross_product(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_kronecker_product(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_dot_product(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_divergence(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_gradient(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_laplace(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_partial(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_size(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_matrix(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_multi_conditionals(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_sparse_matrix(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_sparse_ifs(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_sparse_if(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_sparse_other(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_num_matrix(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_vector(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_set(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_element_convert(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_matrix_index(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_vector_index(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_sequence_index(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_seq_dim_index(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_tuple_index(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_set_index(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_params_block(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_where_conditions(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_where_condition(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_matrix_type(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_vector_type(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_set_type(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_scalar_type(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_function_type(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_mapping_type(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_tuple_type(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_named_type(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_import(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
    fn visit_first_order_ode(&mut self, _n: &N, _kw: &Kw) -> CodeNodeInfo { CodeNodeInfo::default() }
}

/// The `**kwargs` of visit methods (keyword arguments the backends pass).
#[derive(Clone, Debug, Default)]
pub struct Kw {
    pub map: IndexMap<String, KwVal>,
}

#[derive(Clone, Debug)]
pub enum KwVal {
    Bool(bool),
    Str(String),
    Node(N),
    Strs(Vec<String>),
}

impl Kw {
    pub fn has(&self, k: &str) -> bool {
        self.map.contains_key(k)
    }
    pub fn get(&self, k: &str) -> Option<&KwVal> {
        self.map.get(k)
    }
    pub fn str(&self, k: &str) -> Option<String> {
        match self.map.get(k) {
            Some(KwVal::Str(s)) => Some(s.clone()),
            _ => None,
        }
    }
    pub fn bool(&self, k: &str) -> bool {
        matches!(self.map.get(k), Some(KwVal::Bool(true)))
    }
    pub fn node(&self, k: &str) -> Option<N> {
        match self.map.get(k) {
            Some(KwVal::Node(n)) => Some(n.clone()),
            _ => None,
        }
    }
    pub fn with(&self, k: &str, v: KwVal) -> Kw {
        let mut c = self.clone();
        c.map.insert(k.to_string(), v);
        c
    }
    pub fn set(&mut self, k: &str, v: KwVal) {
        self.map.insert(k.to_string(), v);
    }
    pub fn remove(&mut self, k: &str) {
        self.map.shift_remove(k);
    }
}

/// The base-class `visit_id` (call from an override for `super().visit_id(...)`).
pub fn super_visit_id<B: Backend + ?Sized>(b: &mut B, node: &N, _kw: &Kw) -> CodeNodeInfo {
    CodeNodeInfo::new(node.get_name())
}

/// The base-class `visit_double` (call from an override for `super().visit_double(...)`).
pub fn super_visit_double<B: Backend + ?Sized>(b: &mut B, node: &N, _kw: &Kw) -> CodeNodeInfo {
    CodeNodeInfo::new(node.str_value())
}

/// The base-class `visit_fraction` (call from an override for `super().visit_fraction(...)`).
pub fn super_visit_fraction<B: Backend + ?Sized>(b: &mut B, node: &N, _kw: &Kw) -> CodeNodeInfo {
    CodeNodeInfo::new(format!("({}/{})", node.numerator(), node.denominator()))
}

/// The base-class `visit_integer` (call from an override for `super().visit_integer(...)`).
pub fn super_visit_integer<B: Backend + ?Sized>(b: &mut B, node: &N, _kw: &Kw) -> CodeNodeInfo {
    let v = node.int_value();
    CodeNodeInfo::new(if v < 0 { format!("({v})") } else { v.to_string() })
}

/// The base-class `visit_factor` (call from an override for `super().visit_factor(...)`).
pub fn super_visit_factor<B: Backend + ?Sized>(b: &mut B, node: &N, kw: &Kw) -> CodeNodeInfo {
    let n = node.borrow();
    let child = n
        .id
        .clone()
        .or(n.num.clone())
        .or(n.sub.clone())
        .or(n.m.clone())
        .or(n.v.clone())
        .or(n.s.clone())
        .or(n.nm.clone())
        .or(n.op.clone())
        .or(n.c.clone());
    drop(n);
    match child {
        Some(c) => b.visit(&c, kw),
        None => CodeNodeInfo::default(),
    }
}

/// The base-class `visit_expression` (call from an override for `super().visit_expression(...)`).
pub fn super_visit_expression<B: Backend + ?Sized>(b: &mut B, node: &N, kw: &Kw) -> CodeNodeInfo {
    let mut info = b.visit(&node.value().unwrap(), kw);
    if node.sign().is_some() {
        info.content = Content::Str(format!("-{}", info.s()));
    }
    info
}

/// The base-class `visit_sub_expr` (call from an override for `super().visit_sub_expr(...)`).
pub fn super_visit_sub_expr<B: Backend + ?Sized>(b: &mut B, node: &N, kw: &Kw) -> CodeNodeInfo {
    let mut info = b.visit(&node.value().unwrap(), kw);
    info.content = Content::Str(format!("({})", info.s()));
    info
}

/// The base-class `visit_start` (call from an override for `super().visit_start(...)`).
pub fn super_visit_start<B: Backend + ?Sized>(b: &mut B, node: &N, kw: &Kw) -> CodeNodeInfo {
    b.visit(&node.stat().unwrap(), kw)
}

/// The base-class `visit_add` (call from an override for `super().visit_add(...)`).
pub fn super_visit_add<B: Backend + ?Sized>(b: &mut B, node: &N, kw: &Kw) -> CodeNodeInfo {
    let mut l = b.visit(&node.left().unwrap(), kw);
    let r = b.visit(&node.right().unwrap(), kw);
    l.content = Content::Str(format!("{} + {}", l.s(), r.s()));
    l.pre_list.extend(r.pre_list);
    l
}

/// The base-class `visit_sub` (call from an override for `super().visit_sub(...)`).
pub fn super_visit_sub<B: Backend + ?Sized>(b: &mut B, node: &N, kw: &Kw) -> CodeNodeInfo {
    let mut l = b.visit(&node.left().unwrap(), kw);
    let r = b.visit(&node.right().unwrap(), kw);
    l.content = Content::Str(format!("{} - {}", l.s(), r.s()));
    l.pre_list.extend(r.pre_list);
    l
}

/// The base-class `visit_function` (call from an override for `super().visit_function(...)`).
pub fn super_visit_function<B: Backend + ?Sized>(b: &mut B, node: &N, kw: &Kw) -> CodeNodeInfo {
    let name = b.visit(&node.name().unwrap(), kw);
    let mut pre = Vec::new();
    let mut params = Vec::new();
    for p in node.params() {
        let i = b.visit(&p, kw);
        params.push(i.s());
        pre.extend(i.pre_list);
    }
    CodeNodeInfo::with(format!("{}({})", name.s(), params.join(", ")), pre)
}

/// The base-class `visit_matrix_rows` (call from an override for `super().visit_matrix_rows(...)`).
pub fn super_visit_matrix_rows<B: Backend + ?Sized>(b: &mut B, node: &N, kw: &Kw) -> CodeNodeInfo {
    let mut ret = Vec::new();
    let mut pre = Vec::new();
    if let Some(rs) = node.rs() {
        let i = b.visit(&rs, kw);
        ret.extend(i.content.list());
        pre.extend(i.pre_list);
    }
    if let Some(r) = node.r_node() {
        let i = b.visit(&r, kw);
        ret.push(i.content);
        pre.extend(i.pre_list);
    }
    CodeNodeInfo::list(ret, pre)
}

/// The base-class `visit_matrix_row` (call from an override for `super().visit_matrix_row(...)`).
pub fn super_visit_matrix_row<B: Backend + ?Sized>(b: &mut B, node: &N, kw: &Kw) -> CodeNodeInfo {
    let mut ret = Vec::new();
    let mut pre = Vec::new();
    if let Some(rc) = node.rc() {
        let i = b.visit(&rc, kw);
        ret.extend(i.content.list());
        pre.extend(i.pre_list);
    }
    if let Some(e) = node.exp() {
        let i = b.visit(&e, kw);
        ret.push(i.content);
        pre.extend(i.pre_list);
    }
    CodeNodeInfo::list(ret, pre)
}

/// The base-class `visit_matrix_row_commas` (call from an override for `super().visit_matrix_row_commas(...)`).
pub fn super_visit_matrix_row_commas<B: Backend + ?Sized>(b: &mut B, node: &N, kw: &Kw) -> CodeNodeInfo {
    let mut ret = Vec::new();
    let mut pre = Vec::new();
    if let Some(v) = node.value() {
        let i = b.visit(&v, kw);
        ret.extend(i.content.list());
        pre.extend(i.pre_list);
    }
    if let Some(e) = node.exp() {
        let i = b.visit(&e, kw);
        ret.push(i.content);
        pre.extend(i.pre_list);
    }
    CodeNodeInfo::list(ret, pre)
}

/// The base-class `visit_exp_in_matrix` (call from an override for `super().visit_exp_in_matrix(...)`).
pub fn super_visit_exp_in_matrix<B: Backend + ?Sized>(b: &mut B, node: &N, kw: &Kw) -> CodeNodeInfo {
    let mut info = b.visit(&node.value().unwrap(), kw);
    if node.sign().is_some() {
        info.content = Content::Str(format!("-{}", info.s()));
    }
    info
}

/// The base-class `visit_to_matrix` (call from an override for `super().visit_to_matrix(...)`).
pub fn super_visit_to_matrix<B: Backend + ?Sized>(b: &mut B, node: &N, kw: &Kw) -> CodeNodeInfo {
    b.visit(&node.item().unwrap(), kw)
}

/// The base-class `visit_to_double` (call from an override for `super().visit_to_double(...)`).
pub fn super_visit_to_double<B: Backend + ?Sized>(b: &mut B, node: &N, kw: &Kw) -> CodeNodeInfo {
    b.visit(&node.item().unwrap(), kw)
}

/// The base-class `visit_gp_func` (call from an override for `super().visit_gp_func(...)`).
pub fn super_visit_gp_func<B: Backend + ?Sized>(b: &mut B, node: &N, kw: &Kw) -> CodeNodeInfo {
    let fname = node.func_name().unwrap_or_default();
    if !b.base().code_frame.extra_funcs.contains(&fname) {
        b.base_mut().code_frame.extra_funcs.push(fname);
    }
    let mut contents = Vec::new();
    let mut pre = Vec::new();
    let params = node.params();
    for p in &params {
        let i = b.visit(p, kw);
        contents.push(i.s());
        pre.extend(i.pre_list);
    }
    let vb = b.base();
    let name = vb.convert_overloaded_name(&node.identity_name().unwrap_or_default());
    let content = if params[0].la_type().is_mesh() {
        format!("{}.{}({})", b.get_mesh_str(&contents[0]), vb.get_builtin_func_name(&name), contents[1..].join(", "))
    } else if node.gp_type() == GPType::NonZeros {
        format!("{}({})", vb.get_builtin_func_name(&name), contents.join(", "))
    } else if node.gp_type() == GPType::IndicatorVector {
        let dim = match vb.get_builtin_func_name(&name).as_str() {
            packages::VERTICES_TO_VECTOR => "n_vertices()",
            packages::EDGES_TO_VECTOR => "n_edges()",
            packages::FACES_TO_VECTOR => "n_faces()",
            packages::TETS_TO_VECTOR => "n_tets()",
            other => panic!("KeyError: {other}"),
        };
        let owner = params[0].la_type().owner().unwrap_or_else(|| "None".into());
        format!("indicator({}, {}.{})", contents.join(", "), b.get_mesh_str(&owner), dim)
    } else {
        let owner = params[0].la_type().owner().unwrap_or_else(|| "None".into());
        format!("{}.{}({})", b.get_mesh_str(&owner), vb.get_builtin_func_name(&name), contents.join(", "))
    };
    CodeNodeInfo::with(content, pre)
}
