//! Data structures of the type walker (la_parser/la_data.py and the helper
//! classes at the top of la_parser/type_walker.py).

use crate::dims::Dim;
use crate::ir::N;
use crate::pnode::Val;
use crate::types::T;
use indexmap::{IndexMap, IndexSet};
use std::cell::RefCell;
use std::rc::Rc;

/// A symbol table: name -> type. Shared, because the Python compiler aliases
/// symbol-table dicts (e.g. `main_param.symtable is walker.symtable`) and
/// rebinds them (restoring a deep copy after a failed statement).
pub type Symtab = Rc<RefCell<IndexMap<String, T>>>;

pub fn new_symtab() -> Symtab {
    Rc::new(RefCell::new(IndexMap::new()))
}

/// `copy.deepcopy(symtable)` (one memo for the whole table).
pub fn deep_copy_symtab(s: &Symtab) -> Symtab {
    let mut memo = crate::types::DeepCopyMemo::default();
    let copied = s.borrow().iter().map(|(k, v)| (k.clone(), v.deep_copy_memo(&mut memo))).collect();
    Rc::new(RefCell::new(copied))
}

/// Subscripts of an identifier: Python stores either a str (iterated by
/// character) or a list of str.
#[derive(Clone, Debug, PartialEq)]
pub enum Subs {
    Str(String),
    List(Vec<String>),
}

impl Subs {
    /// Iterate as Python would (characters of a str).
    pub fn items(&self) -> Vec<String> {
        match self {
            Subs::Str(s) => s.chars().map(|c| c.to_string()).collect(),
            Subs::List(v) => v.clone(),
        }
    }
    pub fn len(&self) -> usize {
        match self {
            Subs::Str(s) => s.chars().count(),
            Subs::List(v) => v.len(),
        }
    }
    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }
}

/// `Identifier(main_id, subs)` (la_types.py)
#[derive(Clone, Debug, PartialEq)]
pub struct Identifier {
    pub main_id: String,
    pub subs: Subs,
}

impl Identifier {
    pub fn contain_subscript(&self) -> bool {
        !self.subs.is_empty()
    }
}

/// `ParamsData` (la_data.py)
#[derive(Clone, Debug, Default)]
pub struct ParamsData {
    pub arith_dim_list: Vec<Dim>,
    /// sets of dimensions known to be equal (Python sets; kept in insertion order)
    pub same_dim_list: Vec<Vec<Dim>>,
    pub subscripts: IndexMap<String, Vec<String>>,
    pub sub_name_dict: IndexMap<String, String>,
    /// dimension symbol -> {parameter: position}
    pub dim_dict: IndexMap<String, IndexMap<String, usize>>,
    pub seq_dim_dict: IndexMap<String, IndexMap<String, Vec<usize>>>,
    pub dim_seq_set: IndexSet<String>,
    pub ids_dict: IndexMap<String, Identifier>,
    /// parameter names; `None` while the where block is being walked
    pub parameters: Vec<Option<String>>,
    pub symtable: Option<Symtab>,
    pub set_checking: IndexMap<String, String>,
}

/// Shared `ParamsData` (the walker and code generators share these objects).
pub type PD = Rc<RefCell<ParamsData>>;

impl ParamsData {
    pub fn new_shared() -> PD {
        Rc::new(RefCell::new(ParamsData { symtable: Some(new_symtab()), ..Default::default() }))
    }

    pub fn symtable(&self) -> Symtab {
        self.symtable.clone().expect("ParamsData without symtable")
    }

    pub fn update_dim_dict(&mut self, dim: &str, target: &str, pos: usize) {
        if self.dim_seq_set.contains(dim) {
            self.seq_dim_dict
                .entry(dim.to_string())
                .or_default()
                .entry(target.to_string())
                .or_default()
                .push(pos);
        }
        self.dim_dict.entry(dim.to_string()).or_default().insert(target.to_string(), pos);
    }

    pub fn remove_dim(&mut self, dim: &str, target: &str) {
        if let Some(d) = self.dim_dict.get_mut(dim) {
            d.shift_remove(target);
            if d.is_empty() {
                self.dim_dict.shift_remove(dim);
            }
        }
    }

    pub fn remove_target_from_dim_dict(&mut self, target: &str) {
        let keys: Vec<String> = self.dim_dict.keys().cloned().collect();
        for key in keys {
            let d = self.dim_dict.get_mut(&key).unwrap();
            if d.contains_key(target) {
                d.shift_remove(target);
                if d.is_empty() {
                    self.dim_dict.shift_remove(&key);
                }
                break;
            }
        }
    }

    /// Parameter names without placeholders.
    pub fn param_names(&self) -> Vec<String> {
        self.parameters.iter().flatten().cloned().collect()
    }

    pub fn reset(&mut self) {
        let st = self.symtable.clone();
        *self = ParamsData::default();
        if let Some(s) = st {
            s.borrow_mut().clear();
            self.symtable = Some(s);
        }
    }

    /// `copy.deepcopy(params_data)`
    pub fn deep_copy(&self) -> ParamsData {
        let mut c = self.clone();
        c.symtable = self.symtable.as_ref().map(deep_copy_symtab);
        c
    }
}

/// `LocalFuncData` (la_data.py)
#[derive(Clone, Debug)]
pub struct LocalFuncData {
    pub name: String,
    pub params_data: PD,
}

impl LocalFuncData {
    pub fn new(name: &str) -> LocalFuncData {
        LocalFuncData { name: name.to_string(), params_data: ParamsData::new_shared() }
    }
}

/// The walker's `func_data_dict`: shared, deep-copied and restored as a whole.
pub type FuncDataDict = Rc<RefCell<IndexMap<String, LocalFuncData>>>;

/// `copy.deepcopy(func_data_dict)`
pub fn deep_copy_func_data(d: &FuncDataDict) -> FuncDataDict {
    let copied = d
        .borrow()
        .iter()
        .map(|(k, v)| {
            (k.clone(), LocalFuncData { name: v.name.clone(), params_data: Rc::new(RefCell::new(v.params_data.borrow().deep_copy())) })
        })
        .collect();
    Rc::new(RefCell::new(copied))
}

/// `DependenceData` (type_walker.py)
#[derive(Clone, Debug, Default)]
pub struct DependenceData {
    pub module: String,
    pub initialized_list: Vec<String>,
    pub name_list: Vec<String>,
}

/// `BuiltinModuleData` (type_walker.py)
#[derive(Clone, Debug, Default)]
pub struct BuiltinModuleData {
    pub module: String,
    pub instance_name: String,
    pub name_list: Vec<String>,
    pub params_list: Vec<String>,
    pub r_dict: IndexMap<String, String>,
    pub inverse_dict: IndexMap<String, String>,
}

impl BuiltinModuleData {
    pub fn new(
        module: &str,
        instance_name: String,
        params_list: Vec<String>,
        name_list: Vec<String>,
        r_dict: IndexMap<String, String>,
    ) -> Self {
        let inverse_dict = r_dict.iter().map(|(k, v)| (v.clone(), k.clone())).collect();
        BuiltinModuleData { module: module.to_string(), instance_name, name_list, params_list, r_dict, inverse_dict }
    }
}

/// `MeshData` (la_package.py): the symbols of `v, e, f = ElementSets(M)`.
#[derive(Clone, Debug, Default)]
pub struct MeshData {
    pub v: Option<String>,
    pub e: Option<String>,
    pub f: Option<String>,
    pub t: Option<String>,
    pub la_type: Option<T>,
}

impl MeshData {
    pub fn init_dims(&mut self, dims: &[String]) {
        if dims.len() >= 3 {
            self.v = Some(dims[0].clone());
            self.e = Some(dims[1].clone());
            self.f = Some(dims[2].clone());
        }
        if dims.len() > 3 {
            self.t = Some(dims[3].clone());
        }
    }
}

/// `HessianInfo` (ir.py)
#[derive(Clone, Debug)]
pub struct HessianInfo {
    pub upper: String,
    pub lower: String,
    pub ir_node: N,
}

/// `NodeInfo.content`: whatever a walk method computed as the textual or
/// structural content of a node.
#[derive(Clone, Debug, Default)]
pub enum Content {
    #[default]
    None,
    Str(String),
    Int(i64),
    /// a matrix row (IR nodes)
    Nodes(Vec<N>),
    /// matrix rows
    Rows(Vec<Vec<N>>),
}

impl Content {
    /// The content as a symbol name (str), as most callers use it.
    pub fn str(&self) -> String {
        match self {
            Content::Str(s) => s.clone(),
            Content::Int(i) => i.to_string(),
            Content::None => "None".into(),
            _ => panic!("content is not a string"),
        }
    }
    pub fn is_int(&self) -> bool {
        matches!(self, Content::Int(_))
    }
    pub fn as_int(&self) -> Option<i64> {
        match self {
            Content::Int(i) => Some(*i),
            _ => None,
        }
    }
    pub fn is_str(&self) -> bool {
        matches!(self, Content::Str(_))
    }
    /// `str(content)` in Python
    pub fn py_str(&self) -> String {
        self.str()
    }
}

/// A node type, or a list of types (functions with several return values,
/// argmin over several variables, some builtin functions).
#[derive(Clone, Debug)]
pub enum LaTy {
    One(T),
    List(Vec<T>),
}

impl LaTy {
    /// The single type (panics on a list, like calling a method on a list).
    pub fn t(&self) -> T {
        match self {
            LaTy::One(t) => t.clone(),
            LaTy::List(_) => panic!("type is a list"),
        }
    }
    pub fn is_list(&self) -> bool {
        matches!(self, LaTy::List(_))
    }
    pub fn list(&self) -> Vec<T> {
        match self {
            LaTy::One(t) => vec![t.clone()],
            LaTy::List(v) => v.clone(),
        }
    }
}

impl From<T> for LaTy {
    fn from(t: T) -> Self {
        LaTy::One(t)
    }
}

/// IR of a NodeInfo: a node, or a list of nodes (`walk_MultiIfs`).
#[derive(Clone, Debug, Default)]
pub enum IrRef {
    #[default]
    None,
    One(N),
    List(Vec<N>),
}

/// `NodeInfo` (la_types.py)
#[derive(Clone, Debug, Default)]
pub struct NodeInfo {
    pub la_type: Option<LaTy>,
    pub content: Content,
    pub symbols: IndexSet<String>,
    pub ir: IrRef,
    /// set dynamically by some walk methods (`node_info.symbol = ...`)
    pub symbol: Option<String>,
}

impl NodeInfo {
    pub fn new(la_type: Option<LaTy>) -> NodeInfo {
        NodeInfo { la_type, ..Default::default() }
    }
    pub fn with(la_type: impl Into<LaTy>, content: Content, symbols: IndexSet<String>, ir: N) -> NodeInfo {
        NodeInfo { la_type: Some(la_type.into()), content, symbols, ir: IrRef::One(ir), symbol: None }
    }
    /// The IR node (panics if it is a list or unset).
    pub fn ir(&self) -> N {
        match &self.ir {
            IrRef::One(n) => n.clone(),
            _ => panic!("NodeInfo.ir is not a node"),
        }
    }
    pub fn ir_list(&self) -> Vec<N> {
        match &self.ir {
            IrRef::List(v) => v.clone(),
            IrRef::One(n) => vec![n.clone()],
            IrRef::None => vec![],
        }
    }
    pub fn set_ir(&mut self, n: N) {
        self.ir = IrRef::One(n);
    }
    /// `node_info.la_type` as a single type.
    pub fn t(&self) -> T {
        self.la_type.as_ref().expect("NodeInfo without la_type").t()
    }
    pub fn la_ty(&self) -> LaTy {
        self.la_type.clone().expect("NodeInfo without la_type")
    }
    pub fn la_type_is_list(&self) -> bool {
        self.la_type.as_ref().is_some_and(|t| t.is_list())
    }
}

/// What a walk method returns (the Python methods return different things).
#[derive(Clone, Debug, Default)]
pub enum Walked {
    #[default]
    None,
    Info(NodeInfo),
    Node(N),
    Nodes(Vec<N>),
    Str(String),
    /// `walk_Statements`: the parse-tree statements
    Stmts(Vec<Val>),
}

impl Walked {
    pub fn info(self) -> NodeInfo {
        match self {
            Walked::Info(i) => i,
            other => panic!("expected NodeInfo, got {other:?}"),
        }
    }
    pub fn node(self) -> N {
        match self {
            Walked::Node(n) => n,
            Walked::Info(i) => i.ir(),
            other => panic!("expected IR node, got {other:?}"),
        }
    }
    pub fn nodes(self) -> Vec<N> {
        match self {
            Walked::Nodes(n) => n,
            other => panic!("expected IR node list, got {other:?}"),
        }
    }
    pub fn str(self) -> String {
        match self {
            Walked::Str(s) => s,
            other => panic!("expected str, got {other:?}"),
        }
    }
}

/// The `**kwargs` passed between walk methods. Python passes a copy to each
/// call (`self.walk(node, **kwargs)`), so callers keep their own.
#[derive(Clone, Debug, Default)]
pub struct Kwargs {
    pub lhs: Option<String>,
    pub assign_op: Option<String>,
    pub inside_matrix: bool,
    pub inside_summation: bool,
    pub if_cond: bool,
    pub set_ret_symbol: bool,
    pub param_index: Option<usize>,
    pub pre_walk: bool,
}

/// Why a walk failed (Python exceptions).
#[derive(Clone, Debug)]
pub enum WalkError {
    /// a failed `assert_expr` / `assert` with its message
    Assert(String),
    /// `RecursiveException`: a function used before its definition
    Recursive,
    /// any other exception (a Rust panic in the port)
    Other(String),
}

impl WalkError {
    pub fn message(&self) -> String {
        match self {
            WalkError::Assert(m) => m.clone(),
            WalkError::Recursive => "RecursiveException".into(),
            WalkError::Other(m) => m.clone(),
        }
    }
}

pub type WResult<X> = Result<X, WalkError>;

/// `IndexSet` of one string (Python `{x}`).
pub fn set1(s: impl Into<String>) -> IndexSet<String> {
    let mut v = IndexSet::new();
    v.insert(s.into());
    v
}

/// Python `a.union(b)`.
pub fn union(a: &IndexSet<String>, b: &IndexSet<String>) -> IndexSet<String> {
    let mut r = a.clone();
    r.extend(b.iter().cloned());
    r
}
