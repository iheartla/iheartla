//! The type walker (la_parser/type_walker.py): walks the parse tree, checks
//! types and builds the IR.
//!
//! This is a line-by-line port. Methods keep their Python names
//! (`walk_Assignment`, `get_sym_type`, ...) so the two can be read side by
//! side. Python exceptions become `WalkError`s; a failed `assert_expr` is
//! `WalkError::Assert` with the user-facing message. The walker also catches
//! *any* exception while trying statements in def-use order, so Rust panics
//! (index errors and the like, where Python would raise) are caught there too.

#![allow(non_snake_case, clippy::too_many_arguments)]

pub mod data;
mod exprs;
mod funcs;
mod ids;
mod matrices;
mod params;
mod statements;

pub use data::*;

use crate::helper::{get_err_msg_info, ParseInfo, Source};
use crate::ir::{IRNodeType, N, VBlock};
use crate::pnode::{PNode, Val};
use crate::types::{get_func_signature, T};
use indexmap::{IndexMap, IndexSet};
use std::cell::RefCell;
use std::panic::{catch_unwind, AssertUnwindSafe};
use std::rc::Rc;

pub const GLOBAL: &str = "global";

/// `self.pattern` in the walker
fn ident_pattern() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r"^[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*$").unwrap()
    })
}

/// The type walker's state (fields of `TypeWalker.__init__`).
pub struct TypeWalker {
    pub src: Rc<Source>,
    pub symtable: Symtab,
    pub parameters: Vec<Option<String>>,
    pub name_cnt_dict: Rc<RefCell<IndexMap<String, i64>>>,
    pub def_use_mode: bool,
    pub unofficial_method: bool,
    pub has_opt: bool,
    pub has_derivative: bool,
    pub is_param_block: bool,
    pub ret_symbol: Option<String>,
    pub is_generate_ret: bool,
    pub constants: Vec<String>,
    pub multi_lhs_list: Vec<String>,
    pub multi_dim_list: Vec<String>,
    pub lhs_list: Vec<String>,
    pub sum_subs: Vec<String>,
    pub sum_sym_list: Vec<IndexMap<String, Vec<String>>>,
    pub lhs_subs: Vec<String>,
    pub lhs_sym_list: Vec<IndexMap<String, Vec<String>>>,
    pub scope_list: Vec<String>,
    pub sum_conds: Vec<bool>,
    pub la_content: String,
    pub lhs_sub_dict: IndexMap<String, Vec<N>>,
    pub hessian_list: Vec<HessianInfo>,
    pub hessian_sum_list: Vec<N>,
    pub visiting_lhs: bool,
    pub visiting_solver_eq: bool,
    pub cur_eq_type: u8,
    pub solved_func: Vec<String>,
    pub need_mutator: bool,
    pub unknown_sym: Vec<String>,
    pub mesh_type_list: Vec<crate::types::MeshKind>,
    pub dyn_dim: bool,
    pub pre_walk: bool,
    pub rhs_raw_str_list: Vec<String>,
    pub dependency_set: IndexSet<String>,
    pub dependency_dim_dict: IndexMap<String, Option<ParseInfo>>,
    pub local_func_syms: Vec<String>,
    pub local_func_pars: Vec<String>,
    pub local_func_parsing: bool,
    pub local_func_error: bool,
    pub local_func_name: String,
    /// local function name -> parameter symbol table
    pub local_func_dict: IndexMap<String, Symtab>,
    pub visiting_opt: bool,
    pub opt_cur_init_list: Vec<String>,
    pub opt_key: String,
    pub opt_dict: IndexMap<String, PD>,
    pub func_data_dict: FuncDataDict,
    pub func_mapping_dict: IndexMap<String, String>,
    /// local function definition text -> local function name
    pub func_name_dict: IndexMap<String, String>,
    pub func_sig_dict: IndexMap<String, String>,
    pub func_imported_renaming: IndexMap<String, String>,
    pub extra_symtable: Symtab,
    pub desc_dict: IndexMap<String, String>,
    pub import_module_list: Vec<DependenceData>,
    pub builtin_module_dict: IndexMap<String, BuiltinModuleData>,
    pub mesh_dict: IndexMap<String, MeshData>,
    pub main_param: PD,
    pub used_params: Vec<String>,
    pub der_vars: Vec<String>,
    pub der_defined_lhs_list: Vec<String>,
    pub lhs_on_der: Vec<String>,
    pub visiting_der: bool,
    pub opt_syms: Vec<String>,
    pub expr_dict: IndexMap<String, Vec<String>>,
    pub mapping_dict: IndexMap<String, N>,
    pub omit_assert: bool,
    pub class_only: bool,
    /// `self.saved_*` of push_environment / push_scope_environment
    saved: Option<SavedEnv>,
    saved_scope_func_data_dict: Option<FuncDataDict>,
}

struct SavedEnv {
    symtable: Symtab,
    sum_subs: Vec<String>,
    sum_sym_list: Vec<IndexMap<String, Vec<String>>>,
    lhs_subs: Vec<String>,
    sum_conds: Vec<bool>,
    lhs_sub_dict: IndexMap<String, Vec<N>>,
    func_data_dict: FuncDataDict,
    local_func_dict: IndexMap<String, Symtab>,
    extra_symtable: Symtab,
    used_params: Vec<String>,
    der_vars: Vec<String>,
    der_defined_lhs_list: Vec<String>,
    opt_syms: Vec<String>,
    opt_dict: IndexMap<String, PD>,
    scope_list: Vec<String>,
}

impl TypeWalker {
    pub fn new(src: Rc<Source>) -> TypeWalker {
        let symtable = new_symtab();
        let main_param = ParamsData::new_shared();
        TypeWalker {
            src,
            symtable,
            parameters: Vec::new(),
            name_cnt_dict: Rc::new(RefCell::new(IndexMap::new())),
            def_use_mode: true,
            unofficial_method: false,
            has_opt: false,
            has_derivative: false,
            is_param_block: false,
            ret_symbol: None,
            is_generate_ret: false,
            constants: vec!["π".into()],
            multi_lhs_list: Vec::new(),
            multi_dim_list: Vec::new(),
            lhs_list: Vec::new(),
            sum_subs: Vec::new(),
            sum_sym_list: Vec::new(),
            lhs_subs: Vec::new(),
            lhs_sym_list: Vec::new(),
            scope_list: Vec::new(),
            sum_conds: Vec::new(),
            la_content: String::new(),
            lhs_sub_dict: IndexMap::new(),
            hessian_list: Vec::new(),
            hessian_sum_list: Vec::new(),
            visiting_lhs: false,
            visiting_solver_eq: false,
            cur_eq_type: crate::ir::EQ_DEFAULT,
            solved_func: Vec::new(),
            need_mutator: false,
            unknown_sym: Vec::new(),
            mesh_type_list: Vec::new(),
            dyn_dim: false,
            pre_walk: false,
            rhs_raw_str_list: Vec::new(),
            dependency_set: IndexSet::new(),
            dependency_dim_dict: IndexMap::new(),
            local_func_syms: Vec::new(),
            local_func_pars: Vec::new(),
            local_func_parsing: false,
            local_func_error: false,
            local_func_name: String::new(),
            local_func_dict: IndexMap::new(),
            visiting_opt: false,
            opt_cur_init_list: Vec::new(),
            opt_key: String::new(),
            opt_dict: IndexMap::new(),
            func_data_dict: Rc::new(RefCell::new(IndexMap::new())),
            func_mapping_dict: IndexMap::new(),
            func_name_dict: IndexMap::new(),
            func_sig_dict: IndexMap::new(),
            func_imported_renaming: IndexMap::new(),
            extra_symtable: new_symtab(),
            desc_dict: IndexMap::new(),
            import_module_list: Vec::new(),
            builtin_module_dict: IndexMap::new(),
            mesh_dict: IndexMap::new(),
            main_param,
            used_params: Vec::new(),
            der_vars: Vec::new(),
            der_defined_lhs_list: Vec::new(),
            lhs_on_der: Vec::new(),
            visiting_der: false,
            opt_syms: Vec::new(),
            expr_dict: IndexMap::new(),
            mapping_dict: IndexMap::new(),
            omit_assert: false,
            class_only: true,
            saved: None,
            saved_scope_func_data_dict: None,
        }
    }

    // -- parse tree access -------------------------------------------------

    /// `node.parseinfo` as character offsets in the current source.
    pub fn pinfo(&self, node: &Val) -> Option<ParseInfo> {
        let n = node.node()?;
        let (a, b) = n.span?;
        Some(ParseInfo { src: self.src.clone(), pos: self.src.char_of_byte(a), endpos: self.src.char_of_byte(b) })
    }

    /// `node.text` (None without parse info).
    pub fn text(&self, node: &Val) -> Option<String> {
        let n = node.node()?;
        let (a, b) = n.span?;
        Some(self.src.text[a..b].to_string())
    }

    /// `node.text` where Python would use the string (panics on None).
    pub fn text_s(&self, node: &Val) -> String {
        self.text(node).unwrap_or_else(|| "None".into())
    }

    pub fn pnode<'a>(&self, node: &'a Val) -> &'a PNode {
        node.node().expect("not a parse node")
    }

    // -- assertions ----------------------------------------------------------

    /// `assert_expr(cond, msg)`: only checked in the second walk.
    pub fn assert_expr(&self, cond: bool, msg: impl FnOnce() -> String) -> WResult<()> {
        if !self.pre_walk && !self.omit_assert && !cond {
            return Err(WalkError::Assert(msg()));
        }
        Ok(())
    }

    /// A plain Python `assert` (also checked in the first walk).
    pub fn py_assert(&self, cond: bool, msg: impl FnOnce() -> String) -> WResult<()> {
        if !cond {
            return Err(WalkError::Assert(msg()));
        }
        Ok(())
    }

    /// `get_err_msg_info(parse_info, msg)`
    pub fn err_info(pi: &Option<ParseInfo>, msg: &str) -> String {
        get_err_msg_info(pi.as_ref(), msg)
    }

    // -- scopes and symbol tables ------------------------------------------

    pub fn get_sym_sig_dict(&self, names: &[String]) -> IndexMap<String, String> {
        let mut sig = IndexMap::new();
        for name in names {
            let t = self.symtable.borrow()[name].clone();
            if t.is_overloaded() {
                for f in t.func_list() {
                    let s = get_func_signature(name, &f);
                    sig.insert(s.clone(), self.func_sig_dict[&s].clone());
                }
            }
        }
        sig
    }

    /// `get_cur_param_data()`: the local function's parameter data, or the
    /// main parameter data (whose symtable is rebound to the walker's).
    pub fn get_cur_param_data(&self) -> PD {
        let cur = self.scope_list.last().map(String::as_str).unwrap_or(GLOBAL);
        if cur != GLOBAL {
            return self.func_data_dict.borrow()[cur].params_data.clone();
        }
        self.main_param.borrow_mut().symtable = Some(self.symtable.clone());
        self.main_param.clone()
    }

    /// The current scope's symbol table.
    pub fn cur_symtable(&self) -> Symtab {
        self.get_cur_param_data().borrow().symtable()
    }

    pub fn get_param_data(&self, scope: &str) -> PD {
        if scope == GLOBAL {
            self.main_param.clone()
        } else {
            self.func_data_dict.borrow()[scope].params_data.clone()
        }
    }

    pub fn get_upper_param_data(&self) -> PD {
        if self.scope_list.len() > 1 {
            self.get_param_data(&self.get_upper_scope())
        } else {
            self.main_param.clone()
        }
    }

    pub fn filter_symbol(&self, symbol: &str) -> String {
        if symbol.contains('`') {
            let new_symbol = symbol.replace('`', "");
            if !ident_pattern().is_match(&new_symbol)
                || crate::helper::is_keyword(&new_symbol, crate::helper::KeywordSet::Both)
            {
                return symbol.to_string();
            }
            return new_symbol;
        }
        symbol.to_string()
    }

    pub fn is_inside_sum(&self) -> bool {
        !self.sum_subs.is_empty()
    }

    /// `reset_state(la_content)`
    pub fn reset_state(&mut self, la_content: &str) {
        self.symtable.borrow_mut().clear();
        self.parameters.clear();
        self.name_cnt_dict.borrow_mut().clear();
        self.hessian_list.clear();
        self.ret_symbol = None;
        self.is_generate_ret = false;
        self.unofficial_method = false;
        self.has_opt = false;
        self.has_derivative = false;
        self.sum_subs.clear();
        self.sum_sym_list.clear();
        self.multi_lhs_list.clear();
        self.multi_dim_list.clear();
        self.lhs_subs.clear();
        self.lhs_sym_list.clear();
        self.scope_list.clear();
        self.sum_conds.clear();
        self.lhs_list.clear();
        self.la_content = la_content.to_string();
        self.rhs_raw_str_list.clear();
        self.dependency_set.clear();
        self.dependency_dim_dict.clear();
        self.local_func_syms.clear();
        self.local_func_pars.clear();
        self.local_func_parsing = false;
        self.local_func_error = false;
        self.local_func_name.clear();
        self.local_func_dict.clear();
        self.extra_symtable.borrow_mut().clear();
        self.func_sig_dict.clear();
        self.func_imported_renaming.clear();
        self.opt_dict.clear();
        self.func_data_dict.borrow_mut().clear();
        self.func_mapping_dict.clear();
        self.desc_dict.clear();
        self.import_module_list.clear();
        self.builtin_module_dict.clear();
        self.mesh_dict.clear();
        self.main_param.borrow_mut().reset();
        self.used_params.clear();
        self.der_vars.clear();
        self.der_defined_lhs_list.clear();
        self.opt_syms.clear();
        self.expr_dict.clear();
        self.visiting_opt = false;
        self.visiting_lhs = false;
        self.visiting_solver_eq = false;
        self.solved_func.clear();
        self.mesh_type_list.clear();
        self.need_mutator = false;
        self.opt_key.clear();
        self.omit_assert = false;
    }

    /// `get_func_symbols()`: function names (and their signatures) that the
    /// second parse must recognize.
    pub fn get_func_symbols(&self) -> IndexMap<String, String> {
        let mut ret = IndexMap::new();
        let mut seq_func_list: Vec<String> = Vec::new();
        for (k, t) in self.symtable.borrow().iter() {
            if t.is_function() {
                ret.insert(k.clone(), t.get_signature());
            } else if t.is_sequence() && t.elem().is_function() {
                seq_func_list.push(k.clone());
            }
        }
        let mut tmp_sym_dict: IndexMap<String, T> = IndexMap::new();
        for (_, v) in self.local_func_dict.iter() {
            for (sym, ty) in v.borrow().iter() {
                if ty.is_function() {
                    seq_func_list.push(sym.clone());
                    tmp_sym_dict.insert(sym.clone(), ty.clone());
                }
            }
        }
        let rhs_str = self.rhs_raw_str_list.join("\n");
        for seq in &seq_func_list {
            let sig = match self.symtable.borrow().get(seq) {
                Some(t) => t.get_signature(),
                None => tmp_sym_dict[seq].get_signature(),
            };
            for m in find_seq_func_calls(seq, &rhs_str) {
                ret.insert(m.clone(), format!("{sig}{m}"));
            }
        }
        for sym in &self.local_func_syms {
            let c_sym = self.func_mapping_dict.get(sym).cloned().unwrap_or_else(|| sym.clone());
            ret.insert(c_sym.clone(), format!("localF;{c_sym}"));
        }
        for sym in tmp_sym_dict.keys() {
            ret.insert(sym.clone(), format!("localFP;{sym}"));
        }
        for sym in &self.solved_func {
            ret.insert(sym.clone(), format!("solved;{sym}"));
        }
        ret
    }

    /// `generate_var_name(base)`: `base_0`, `base_1`, ... not in the main symtable.
    pub fn generate_var_name(&self, base: &str) -> String {
        let mut index = self.name_cnt_dict.borrow().get(base).copied().unwrap_or(-1);
        index += 1;
        let ret = loop {
            let r = format!("{base}_{index}");
            index += 1;
            if !self.symtable.borrow().contains_key(&r) {
                break r;
            }
        };
        self.name_cnt_dict.borrow_mut().insert(base.to_string(), index - 1);
        ret
    }

    /// `add_sym_type(sym, c_type, error_msg, is_main, need_check, to_upper)`
    pub fn add_sym_type(
        &mut self,
        sym: &str,
        c_type: T,
        error_msg: &str,
        is_main: bool,
        need_check: bool,
        to_upper: bool,
    ) -> WResult<Option<String>> {
        let mut new_sym_name = None;
        let target = if is_main {
            self.symtable.clone()
        } else if to_upper {
            let upper = &self.scope_list[self.scope_list.len() - 2];
            if upper != GLOBAL {
                self.func_data_dict.borrow()[upper.as_str()].params_data.borrow().symtable()
            } else {
                self.symtable.clone()
            }
        } else {
            self.cur_symtable()
        };
        let check = self.scope_list.last().map(String::as_str) == Some(GLOBAL);
        let existing = target.borrow().get(sym).cloned();
        match existing {
            None => {
                target.borrow_mut().insert(sym.to_string(), c_type.clone());
            }
            Some(e) if e.is_function() => {
                if e.is_overloaded() {
                    let ok = e.add_new_type(c_type.clone());
                    if !ok {
                        self.assert_expr(false, || "Multiple functions with same signature".into())?;
                    }
                } else if e.get_overloading_signature() != c_type.get_overloading_signature() {
                    target.borrow_mut().insert(sym.to_string(), T::overloading(vec![e, c_type.clone()], None));
                } else {
                    self.assert_expr(false, || "Multiple functions with same signature".into())?;
                }
            }
            Some(_) => {
                self.assert_expr(false, || error_msg.to_string())?;
            }
        }
        if need_check && check && c_type.is_function() && !c_type.is_overloaded() {
            let sig = get_func_signature(sym, &c_type);
            if !self.func_sig_dict.contains_key(&sig) {
                let n_name = self.generate_var_name(sym);
                self.func_sig_dict.insert(sig, n_name.clone());
                self.extra_symtable.borrow_mut().insert(n_name.clone(), c_type.clone());
                self.func_mapping_dict.insert(n_name.clone(), sym.to_string());
                new_sym_name = Some(n_name);
            }
        }
        Ok(new_sym_name)
    }

    /// `add_sym_type` with Python's default arguments.
    pub fn add_sym(&mut self, sym: &str, c_type: T, error_msg: &str) -> WResult<Option<String>> {
        self.add_sym_type(sym, c_type, error_msg, false, true, false)
    }

    /// `get_sym_type(sym)`: innermost scope first, then the extra symtable;
    /// a fresh invalid type if unknown.
    pub fn get_sym_type(&self, sym: &str) -> T {
        for scope in self.scope_list.iter().rev() {
            let st = if scope == GLOBAL {
                self.symtable.clone()
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

    pub fn is_sym_existed(&self, sym: &str) -> bool {
        for scope in self.scope_list.iter().rev() {
            let st = if scope == GLOBAL {
                self.symtable.clone()
            } else {
                self.func_data_dict.borrow()[scope.as_str()].params_data.borrow().symtable()
            };
            if st.borrow().contains_key(sym) {
                return true;
            }
        }
        self.extra_symtable.borrow().contains_key(sym)
    }

    pub fn param_names(&self) -> Vec<String> {
        self.parameters.iter().flatten().cloned().collect()
    }

    pub fn in_parameters(&self, sym: &str) -> bool {
        self.parameters.iter().any(|p| p.as_deref() == Some(sym))
    }

    pub fn is_sym_parameter(&self, sym: &str) -> bool {
        let cur = self.get_cur_scope();
        if cur == GLOBAL {
            return self.in_parameters(sym);
        }
        let in_local =
            self.func_data_dict.borrow()[cur.as_str()].params_data.borrow().parameters.iter().any(|p| p.as_deref() == Some(sym));
        in_local || self.in_parameters(sym)
    }

    /// `check_sym_existence(sym, msg, existed)`
    pub fn check_sym_existence(&self, sym: &str, msg: &str, existed: bool) -> WResult<()> {
        if existed {
            let mut resolved = false;
            for scope in self.scope_list.iter().rev() {
                let st = if scope == GLOBAL {
                    self.symtable.clone()
                } else {
                    self.func_data_dict.borrow()[scope.as_str()].params_data.borrow().symtable()
                };
                if st.borrow().contains_key(sym) {
                    resolved = true;
                    break;
                }
            }
            self.assert_expr(resolved, || msg.to_string())
        } else {
            let st = self.cur_symtable();
            let has = st.borrow().contains_key(sym);
            self.assert_expr(!has, || msg.to_string())
        }
    }

    pub fn push_scope(&mut self, scope: &str) {
        self.scope_list.push(scope.to_string());
        if !self.func_data_dict.borrow().contains_key(scope) {
            self.func_data_dict.borrow_mut().insert(scope.to_string(), LocalFuncData::new(scope));
        }
    }

    pub fn pop_scope(&mut self) {
        self.scope_list.pop();
    }

    pub fn is_main_scope(&self) -> bool {
        self.scope_list.last().map(String::as_str) == Some(GLOBAL)
    }

    pub fn get_cur_scope(&self) -> String {
        self.scope_list.last().cloned().unwrap_or_default()
    }

    pub fn get_upper_scope(&self) -> String {
        self.scope_list[self.scope_list.len() - 2].clone()
    }

    // -- identifiers with subscripts ----------------------------------------

    pub fn contain_subscript(&self, identifier: &str) -> bool {
        let pd = self.get_cur_param_data();
        let pd = pd.borrow();
        pd.ids_dict.get(identifier).is_some_and(|i| i.contain_subscript())
    }

    /// `get_all_ids(identifier)`: (main id, subscripts)
    pub fn get_all_ids(&self, identifier: &str) -> (String, Vec<String>) {
        let pd = self.get_cur_param_data();
        if let Some(i) = pd.borrow().ids_dict.get(identifier) {
            return (i.main_id.clone(), i.subs.items());
        }
        let res: Vec<&str> = identifier.split('_').collect();
        if res.len() == 1 {
            return (res[0].to_string(), Vec::new());
        }
        (res[0].to_string(), res[1].chars().map(|c| c.to_string()).collect())
    }

    /// `get_all_ids` when Python would index `[1]` of a one-element list
    /// (an identifier without `_`): the IndexError becomes a panic.
    pub fn get_all_ids_subs(&self, identifier: &str) -> Vec<String> {
        let pd = self.get_cur_param_data();
        if let Some(i) = pd.borrow().ids_dict.get(identifier) {
            return i.subs.items();
        }
        let res: Vec<&str> = identifier.split('_').collect();
        assert!(res.len() > 1, "list index out of range");
        res[1].chars().map(|c| c.to_string()).collect()
    }

    pub fn get_main_id(&self, identifier: &str) -> String {
        let pd = self.get_cur_param_data();
        let pd = pd.borrow();
        match pd.ids_dict.get(identifier) {
            Some(i) => i.main_id.clone(),
            None => identifier.to_string(),
        }
    }

    // -- environments for def-use ordering ---------------------------------

    fn push_environment(&mut self) {
        self.saved = Some(SavedEnv {
            symtable: deep_copy_symtab(&self.symtable),
            sum_subs: self.sum_subs.clone(),
            sum_sym_list: self.sum_sym_list.clone(),
            lhs_subs: self.lhs_subs.clone(),
            sum_conds: self.sum_conds.clone(),
            lhs_sub_dict: self.lhs_sub_dict.clone(),
            func_data_dict: deep_copy_func_data(&self.func_data_dict),
            local_func_dict: self.local_func_dict.iter().map(|(k, v)| (k.clone(), deep_copy_symtab(v))).collect(),
            extra_symtable: deep_copy_symtab(&self.extra_symtable),
            used_params: self.used_params.clone(),
            der_vars: self.der_vars.clone(),
            der_defined_lhs_list: self.der_defined_lhs_list.clone(),
            opt_syms: self.opt_syms.clone(),
            opt_dict: self
                .opt_dict
                .iter()
                .map(|(k, v)| (k.clone(), Rc::new(RefCell::new(v.borrow().deep_copy()))))
                .collect(),
            scope_list: self.scope_list.clone(),
        });
    }

    fn push_scope_environment(&mut self) {
        self.saved_scope_func_data_dict = Some(deep_copy_func_data(&self.func_data_dict));
    }

    fn pop_environment(&mut self) {
        let s = self.saved.take().expect("pop_environment without push");
        self.symtable = s.symtable;
        self.sum_subs = s.sum_subs;
        self.sum_sym_list = s.sum_sym_list;
        self.lhs_subs = s.lhs_subs;
        self.sum_conds = s.sum_conds;
        self.lhs_sub_dict = s.lhs_sub_dict;
        self.local_func_dict = s.local_func_dict;
        self.func_data_dict = s.func_data_dict;
        self.extra_symtable = s.extra_symtable;
        self.opt_dict = s.opt_dict;
        self.used_params = s.used_params;
        self.der_vars = s.der_vars;
        self.der_defined_lhs_list = s.der_defined_lhs_list;
        self.opt_syms = s.opt_syms;
        self.local_func_parsing = false;
        self.is_param_block = false;
        self.visiting_solver_eq = false;
        self.local_func_error = false;
        self.scope_list = s.scope_list;
    }

    fn pop_scope_environment(&mut self) {
        if let Some(d) = self.saved_scope_func_data_dict.take() {
            self.func_data_dict = d;
        }
    }

    /// Walk, catching panics as Python's `except Exception` would.
    pub fn try_walk(&mut self, node: &Val, kw: &Kwargs) -> WResult<Walked> {
        match catch_unwind(AssertUnwindSafe(|| self.walk(node, kw))) {
            Ok(r) => r,
            Err(p) => {
                let msg = p
                    .downcast_ref::<String>()
                    .cloned()
                    .or_else(|| p.downcast_ref::<&str>().map(|s| s.to_string()))
                    .unwrap_or_else(|| "internal error".into());
                Err(WalkError::Other(msg))
            }
        }
    }

    /// `get_ordered_stat(stat_list)`: walk statements in def-use order.
    pub fn get_ordered_stat(&mut self, stat_list: &[Val]) -> WResult<(Vec<N>, Vec<Option<N>>)> {
        let mut new_list = Vec::new();
        let mut tex_list: Vec<Option<N>> = vec![None; stat_list.len()];
        let mut order_list: Vec<i64> = vec![-1; stat_list.len()];
        let mut cnt = 0;
        let mut retries = 0;
        while cnt < stat_list.len() {
            let mut visited = vec![false; stat_list.len()];
            for cur_index in 0..stat_list.len() {
                if order_list[cur_index] == -1 && !visited[cur_index] {
                    self.push_scope_environment();
                    match self.try_walk(&stat_list[cur_index], &Kwargs::default()) {
                        Ok(w) => {
                            let ir = w.node();
                            new_list.push(ir.clone());
                            order_list[cur_index] = cnt as i64;
                            tex_list[cur_index] = Some(ir);
                            cnt += 1;
                            retries = 0;
                            break;
                        }
                        Err(e) => {
                            retries += 1;
                            visited[cur_index] = true;
                            if retries > stat_list.len() {
                                return Err(e);
                            }
                            self.pop_scope_environment();
                            continue;
                        }
                    }
                }
            }
        }
        Ok((new_list, tex_list))
    }

    /// `get_meshset_assign(stat_list)`: assignments `V, E, F = ElementSets(M)`.
    fn get_meshset_assign(&self, stat_list: &[Val]) -> (Vec<usize>, Vec<String>) {
        let mut ret = Vec::new();
        let mut names = Vec::new();
        for (index, stat) in stat_list.iter().enumerate() {
            if !is_ast_assignment(stat) {
                continue;
            }
            let right = stat.get("right");
            let Some(rhs) = right.items().first() else { continue };
            if rhs.class() == "Expression" && rhs.get("value").class() == "Factor" && rhs.get("value").get("op").class() == "Function"
            {
                if let Some(m) = self.builtin_module_dict.get(crate::packages::MESH_HELPER) {
                    if let Some(r) = m.r_dict.get(crate::packages::MESH_SETS) {
                        let op = rhs.get("value").get("op");
                        if op.get("name").as_str() == Some(r.as_str()) {
                            ret.push(index);
                            names.push(self.text_s(&op.get("params").items()[0]));
                        }
                    }
                }
            }
        }
        (ret, names)
    }

    /// `convert_mapping_type()`: mapping types in the current scope become
    /// sequences (V → ℝ³) or element types (f ∈ F).
    pub fn convert_mapping_type(&mut self) -> WResult<()> {
        let pd = self.get_cur_param_data();
        let st = pd.borrow().symtable();
        let entries: Vec<(String, T)> = st.borrow().iter().map(|(k, v)| (k.clone(), v.clone())).collect();
        for (k, c_type) in entries {
            let v = if c_type.is_sequence() { c_type.elem() } else { c_type.clone() };
            if !v.is_mapping() {
                continue;
            }
            if let Some(src) = v.src() {
                let src_type = self.get_sym_type(&src);
                self.assert_expr(src_type.is_mesh_element_set(), || format!("Symbol {src} should be vertices/edges/faces"))?;
                let seq = T::sequence(src_type.length(), v.dst().unwrap());
                st.borrow_mut().insert(k.clone(), seq);
            } else {
                let ele_set = v.ele_set().unwrap();
                self.check_sym_existence(&ele_set, &format!("Symbol {ele_set} is not defined"), true)?;
                let set_type = self.get_sym_type(&ele_set);
                let mut la_type = set_type.elem();
                la_type.set(|t| t.owner = set_type.owner());
                if v.subset() {
                    la_type = set_type.clone();
                } else {
                    pd.borrow_mut().set_checking.insert(k.clone(), ele_set.clone());
                }
                self.assert_expr(set_type.is_set(), || format!("Symbol {ele_set} should be a set"))?;
                if c_type.is_sequence() {
                    c_type.set(|t| t.element_type = Some(la_type));
                } else {
                    st.borrow_mut().insert(k.clone(), la_type);
                }
            }
        }
        Ok(())
    }

    /// `gen_block_node(stat_list, index_list, ir_node)`: walk statements in
    /// def-use order and collect them into the block.
    fn gen_block_node(&mut self, stat_list: &[Val], index_list: &[usize], ir_node: &N, kw: &Kwargs) -> WResult<()> {
        let (meshset_list, name_list) = self.get_meshset_assign(stat_list);
        let block = N::new(IRNodeType::Block);
        block.set(|b| b.meshset_list = meshset_list.clone());
        let mut kwargs = kw.clone();
        let mut new_list = Vec::new();
        let mut order_list: Vec<i64> = vec![-1; stat_list.len()];
        let mut cnt = 0;
        let mut retries = 0;
        for (c_index, &cur_index) in meshset_list.iter().enumerate() {
            let ir = self.walk(&stat_list[cur_index], &kwargs)?.node();
            set_vblock(ir_node, index_list[cur_index], ir.clone());
            let lhs_list: Vec<String> = ir.lefts().iter().map(|l| l.get_main_id()).collect();
            if let Some(md) = self.mesh_dict.get_mut(&name_list[c_index]) {
                md.init_dims(&lhs_list);
            } else {
                panic!("KeyError: {}", name_list[c_index]);
            }
            new_list.push(ir);
            order_list[cur_index] = cnt as i64;
            cnt += 1;
        }
        self.convert_mapping_type()?;
        while cnt < stat_list.len() {
            let mut visited = vec![false; stat_list.len()];
            for cur_index in 0..stat_list.len() {
                if order_list[cur_index] != -1 || visited[cur_index] {
                    continue;
                }
                let cur_stat = &stat_list[cur_index];
                self.push_environment();
                let mut update_ret_type = false;
                if cur_index == stat_list.len() - 1 {
                    if is_ast_assignment(cur_stat) {
                        kwargs.set_ret_symbol = true;
                    } else if cur_stat.class() != "LocalFunc" && cur_stat.class() != "MultiCondExpr" {
                        self.ret_symbol = Some("ret".into());
                        update_ret_type = true;
                        self.is_generate_ret = true;
                        kwargs.lhs = Some("ret".into());
                        self.lhs_list.push("ret".into());
                    }
                }
                match self.try_walk(cur_stat, &kwargs) {
                    Ok(w) => {
                        let info_type = match &w {
                            Walked::Info(i) => i.la_type.clone(),
                            _ => None,
                        };
                        let ir = w.node();
                        set_vblock(ir_node, index_list[cur_index], ir.clone());
                        new_list.push(ir);
                        if update_ret_type {
                            let t = match info_type {
                                Some(LaTy::One(t)) => t,
                                Some(LaTy::List(v)) => v[0].clone(),
                                None => T::invalid(),
                            };
                            let ret = self.ret_symbol.clone().unwrap();
                            self.symtable.borrow_mut().insert(ret, t);
                        }
                        order_list[cur_index] = cnt as i64;
                        cnt += 1;
                        retries = 0;
                        break;
                    }
                    Err(e) => {
                        retries += 1;
                        visited[cur_index] = true;
                        if retries > stat_list.len() {
                            return Err(e);
                        }
                        self.pop_environment();
                        continue;
                    }
                }
            }
        }
        block.set(|b| b.stmts = new_list);
        ir_node.set(|n| n.stat = Some(block));
        Ok(())
    }

    fn convert_parameters(&mut self) {
        for i in 0..self.parameters.len() {
            let Some(p) = self.parameters[i].clone() else { continue };
            if self.get_sym_type(&p).is_function() {
                let mapped = self.func_mapping_dict[&p].clone();
                if !self.get_sym_type(&mapped).is_overloaded() {
                    self.parameters[i] = Some(mapped);
                }
            }
        }
    }

    fn fill_func_names(&mut self) {
        let entries: Vec<(String, T)> = self.symtable.borrow().iter().map(|(k, v)| (k.clone(), v.clone())).collect();
        for (k, v) in entries {
            if v.is_overloaded() {
                let fl = v.func_list();
                if v.fname_list().map_or(true, |n| n.len() != fl.len()) {
                    let names = fl.iter().map(|c| self.func_sig_dict[&get_func_signature(&k, c)].clone()).collect();
                    v.set(|t| t.fname_list = Some(names));
                }
            }
        }
    }

    fn check_sparse_hessian(&mut self, vblock: &[VBlock]) {
        let stat_list: Vec<N> = vblock
            .iter()
            .filter_map(|v| match v {
                VBlock::Ir(n) => Some(n.clone()),
                _ => None,
            })
            .collect();
        let hessians = self.hessian_list.clone();
        for hess in hessians {
            let node = get_assign_node(&hess.upper, &stat_list);
            self.hessian_sum_list.clear();
            let need_sparse = match &node {
                Some(n) => self.check_expr_node(&n.rights()[0]),
                None => false,
            };
            if need_sparse {
                let n = node.unwrap();
                let new_name = self.generate_var_name("hess");
                n.set(|x| {
                    x.need_sparse_hessian = true;
                    x.hessian_var = hess.lower.clone();
                    x.new_hessian_name = new_name.clone();
                    x.need_sparse = true;
                });
                hess.ir_node.set(|x| x.new_hessian_name = new_name.clone());
                for sum in self.hessian_sum_list.clone() {
                    let list = crate::ir_iterator::sum_index_list(&hess.lower, &self.get_sym_type(&hess.lower), &sum);
                    sum.set(|s| s.sum_index_list = list);
                }
            }
        }
    }

    fn check_expr_node(&mut self, node: &N) -> bool {
        let mut f = node.clone();
        if f.is_node(IRNodeType::Subexpression) {
            f = f.value().unwrap();
        }
        if f.is_node(IRNodeType::Expression) {
            f = f.value().unwrap();
        }
        if f.is_node(IRNodeType::Factor) {
            if let Some(op) = f.op() {
                if op.is_node(IRNodeType::Summation) {
                    self.hessian_sum_list.push(op);
                    return true;
                }
            } else if let Some(sub) = f.sub() {
                return self.check_expr_node(&sub);
            }
        } else if f.is_node(IRNodeType::Add) {
            return self.check_expr_node(&f.left().unwrap()) && self.check_expr_node(&f.right().unwrap());
        }
        false
    }

    /// `update_parameters(identifier, index)`
    pub fn update_parameters(&mut self, identifier: &str, index: usize) {
        let name = if self.contain_subscript(identifier) { self.get_all_ids(identifier).0 } else { identifier.to_string() };
        if index >= self.parameters.len() {
            self.parameters.resize(index + 1, None);
        }
        self.parameters[index] = Some(name);
    }

    /// `gen_json_content()` is used by the GUI only and is not ported.

    // -- dispatch ------------------------------------------------------------

    /// `self.walk(node, **kwargs)`: dispatch on the parse node's class.
    pub fn walk(&mut self, node: &Val, kw: &Kwargs) -> WResult<Walked> {
        let class = node.class().to_string();
        match class.as_str() {
            "Start" => self.walk_Start(node, kw).map(Walked::Node),
            "ParamsBlock" => self.walk_ParamsBlock(node, kw).map(Walked::Node),
            "WhereConditions" => self.walk_WhereConditions(node, kw).map(Walked::Node),
            "WhereCondition" => self.walk_WhereCondition(node, kw).map(Walked::Node),
            "DeWhereCondition" => Ok(Walked::None),
            "MatrixType" => self.walk_MatrixType(node, kw).map(Walked::Node),
            "VectorType" => self.walk_VectorType(node, kw).map(Walked::Node),
            "ScalarType" => self.walk_ScalarType(node, kw).map(Walked::Node),
            "NamedType" => self.walk_NamedType(node, kw).map(Walked::Node),
            "SetType" => self.walk_SetType(node, kw).map(Walked::Node),
            "TupleType" => self.walk_TupleType(node, kw).map(Walked::Node),
            "FunctionType" => self.walk_FunctionType(node, kw).map(Walked::Node),
            "MappingType" => self.walk_MappingType(node, kw).map(Walked::Node),
            "ImportVar" => self.walk_ImportVar(node, kw),
            "Import" => self.walk_Import(node, kw).map(Walked::Node),
            "Statements" => Ok(Walked::Stmts(vec![node.get("stat").clone()])),
            "Expression" => self.walk_Expression(node, kw).map(Walked::Info),
            "Add" => self.walk_Add(node, kw).map(Walked::Info),
            "Subtract" => self.walk_Subtract(node, kw).map(Walked::Info),
            "AddSub" => self.walk_AddSub(node, kw).map(Walked::Info),
            "Union" => self.walk_Union(node, kw).map(Walked::Info),
            "Intersection" => self.walk_Intersection(node, kw).map(Walked::Info),
            "Multiply" => self.walk_Multiply(node, kw).map(Walked::Info),
            "Divide" => self.walk_Divide(node, kw).map(Walked::Info),
            "Subexpression" => self.walk_Subexpression(node, kw).map(Walked::Info),
            "LocalFunc" => self.walk_LocalFunc(node, kw).map(Walked::Info),
            "Destructure" => self.walk_Destructure(node, kw).map(Walked::Info),
            "Assignment" => self.walk_Assignment(node, kw).map(Walked::Info),
            "GeneralAssignment" => self.walk_GeneralAssignment(node, kw).map(Walked::Info),
            "DeSolver" => Ok(Walked::None),
            "Summation" => self.walk_Summation(node, kw).map(Walked::Info),
            "Optimize" => self.walk_Optimize(node, kw).map(Walked::Info),
            "MultiCond" => self.walk_MultiCond(node, kw).map(Walked::Nodes),
            "Domain" => self.walk_Domain(node, kw).map(Walked::Node),
            "Integral" => self.walk_Integral(node, kw).map(Walked::Info),
            "Norm" => self.walk_Norm(node, kw).map(Walked::Info),
            "InnerProduct" => self.walk_InnerProduct(node, kw).map(Walked::Info),
            "FroProduct" => self.walk_FroProduct(node, kw).map(Walked::Info),
            "HadamardProduct" => self.walk_HadamardProduct(node, kw).map(Walked::Info),
            "CrossProduct" => self.walk_CrossProduct(node, kw).map(Walked::Info),
            "KroneckerProduct" => self.walk_KroneckerProduct(node, kw).map(Walked::Info),
            "DotProduct" => self.walk_DotProduct(node, kw).map(Walked::Info),
            "SizeOp" => self.walk_SizeOp(node, kw).map(Walked::Info),
            "Derivative" => self.walk_Derivative(node, kw).map(Walked::Info),
            "Partial" => self.walk_Partial(node, kw).map(Walked::Info),
            "Divergence" => self.walk_Divergence(node, kw).map(Walked::Info),
            "Gradient" => self.walk_Gradient(node, kw).map(Walked::Info),
            "Laplace" => self.walk_Laplace(node, kw).map(Walked::Info),
            "Power" => self.walk_Power(node, kw).map(Walked::Info),
            "Solver" => self.walk_Solver(node, kw).map(Walked::Info),
            "Transpose" => self.walk_Transpose(node, kw).map(Walked::Info),
            "PseudoInverse" => self.walk_PseudoInverse(node, kw).map(Walked::Info),
            "Squareroot" => self.walk_Squareroot(node, kw).map(Walked::Info),
            "Function" => self.walk_Function(node, kw).map(Walked::Info),
            "IfCondition" => self.walk_IfCondition(node, kw).map(Walked::Info),
            "AndCondition" => self.walk_AndCondition(node, kw).map(Walked::Info),
            "AtomCondition" => self.walk_AtomCondition(node, kw).map(Walked::Info),
            "InCondition" => self.walk_InCondition(node, kw).map(Walked::Info),
            "NotInCondition" => self.walk_NotInCondition(node, kw).map(Walked::Info),
            "NeCondition" | "EqCondition" | "GreaterCondition" | "GreaterEqualCondition" | "LessCondition"
            | "LessEqualCondition" => self.walk_BinComp(node, kw, &class).map(Walked::Info),
            "IdentifierSubscript" => self.walk_IdentifierSubscript(node, kw).map(Walked::Info),
            "IdentifierAlone" => self.walk_IdentifierAlone(node, kw).map(Walked::Info),
            "Factor" => self.walk_Factor(node, kw).map(Walked::Info),
            "Pi" | "Infinity" | "E" => self.walk_Constant(node, kw, &class).map(Walked::Info),
            "Integer" => self.walk_Integer(node, kw).map(Walked::Info),
            "SubInteger" => self.walk_SubInteger(node, kw).map(Walked::Info),
            "SupInteger" => self.walk_SupInteger(node, kw).map(Walked::Info),
            "Double" => self.walk_Double(node, kw).map(Walked::Info),
            "Fraction" => self.walk_Fraction(node, kw).map(Walked::Info),
            "Mantissa" => self.walk_Mantissa(node, kw).map(Walked::Str),
            "Exponent" => self.walk_Exponent(node, kw).map(Walked::Str),
            "Float" => self.walk_Float(node, kw).map(Walked::Str),
            "MultiCondExpr" => self.walk_MultiCondExpr(node, kw).map(Walked::Info),
            "MultiIfs" => self.walk_MultiIfs(node, kw).map(Walked::Info),
            "SingleIf" => self.walk_SingleIf(node, kw).map(Walked::Info),
            "Vector" => self.walk_Vector(node, kw).map(Walked::Info),
            "Set" => self.walk_Set(node, kw).map(Walked::Info),
            "Matrix" => self.walk_Matrix(node, kw).map(Walked::Info),
            "MatrixRows" => self.walk_MatrixRows(node, kw).map(Walked::Info),
            "MatrixRow" => self.walk_MatrixRow(node, kw).map(Walked::Info),
            "MatrixRowCommas" => self.walk_MatrixRowCommas(node, kw).map(Walked::Info),
            "ExpInMatrix" => self.walk_ExpInMatrix(node, kw).map(Walked::Info),
            "NumMatrix" => self.walk_NumMatrix(node, kw).map(Walked::Info),
            "ElementConvertFunc" => self.walk_ElementConvertFunc(node, kw).map(Walked::Info),
            "ArithExpression" => self.walk_ArithExpression(node, kw).map(Walked::Info),
            "ArithSubexpression" => self.walk_ArithSubexpression(node, kw).map(Walked::Info),
            "ArithAdd" | "ArithSubtract" | "ArithMultiply" | "ArithDivide" => {
                self.walk_ArithBinary(node, kw, &class).map(Walked::Info)
            }
            "ArithFactor" => self.walk_ArithFactor(node, kw).map(Walked::Info),
            c => {
                if let Some(r) = self.walk_builtin_func(node, kw, c)? {
                    return Ok(Walked::Info(r));
                }
                panic!("Unexpected type {c} walked")
            }
        }
    }

    /// Walk and return the NodeInfo.
    pub fn wi(&mut self, node: &Val, kw: &Kwargs) -> WResult<NodeInfo> {
        Ok(self.walk(node, kw)?.info())
    }

    /// Walk without kwargs (`self.walk(node)` in Python).
    pub fn wi0(&mut self, node: &Val) -> WResult<NodeInfo> {
        Ok(self.walk(node, &Kwargs::default())?.info())
    }
}

/// Replace a statement block in `StartNode.vblock` by its IR.
fn set_vblock(start: &N, index: usize, ir: N) {
    start.set(|s| s.vblock[index] = VBlock::Ir(ir));
}

fn get_assign_node(lhs: &str, stat_list: &[N]) -> Option<N> {
    let mut res = None;
    for node in stat_list {
        if node.is_node(IRNodeType::Assignment) && node.lefts()[0].raw_text().as_deref() == Some(lhs) {
            res = Some(node.clone());
        }
    }
    res
}

/// `is_ast_assignment(node)`
pub fn is_ast_assignment(node: &Val) -> bool {
    matches!(node.class(), "Assignment" | "Destructure")
}

/// The calls `seq_i(` in the source that `get_func_symbols` finds with
/// `seq_`…`|seq_<id>|seq_\d*` followed by `(` (the symbol is used as a regex
/// fragment, unescaped, as in Python).
fn find_seq_func_calls(seq: &str, text: &str) -> Vec<String> {
    let pat = format!(
        r"(?:{seq}_`[^`]*`|{seq}_[A-Za-z\p{{Ll}}\p{{Lu}}\p{{Lo}}]\p{{M}}*(?:[A-Z0-9a-z\p{{Ll}}\p{{Lu}}\p{{Lo}}]\p{{M}}*)*|{seq}_\d*)"
    );
    let Ok(re) = regex::Regex::new(&pat) else { return Vec::new() };
    let mut out = Vec::new();
    let mut start = 0;
    while start <= text.len() {
        let Some(m) = re.find_at(text, start) else { break };
        if text[m.end()..].starts_with('(') {
            out.push(m.as_str().to_string());
            start = if m.end() > m.start() { m.end() } else { m.end() + 1 };
        } else {
            // the lookahead failed; Python retries from the next position
            start = m.start() + text[m.start()..].chars().next().map_or(1, |c| c.len_utf8());
        }
    }
    out
}
