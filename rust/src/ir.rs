//! The intermediate representation (la_parser/ir.py).
//!
//! The Python IR is a tree of objects of ~100 classes whose attributes are
//! read and written by name throughout the type walker and code generators.
//! Here every node is one `IrNode` struct holding the union of all
//! attributes; `node_type` says which class it is. Nodes are shared and
//! mutable (`N` is a reference, as in Python), and `parent` is a weak link.
//!
//! Attribute names follow Python, except where one name had different types
//! in different classes:
//!
//! | Python                                        | here          |
//! |-----------------------------------------------|---------------|
//! | `left`/`right` lists (Assign, Destructuring, Equation) | `lefts`/`rights` |
//! | `NumMatrixNode.left` (str '0'/'1'/'𝟙')        | `left_str`    |
//! | `WhereConditionsNode.value` (list)            | `values`      |
//! | `IntegerNode.value` (int)                     | `int_value`   |
//! | `DoubleNode.value` (str)                      | `str_value`   |
//! | `WhereConditionNode.id` (list)                | `ids`         |
//! | `WhereConditionNode.type` (node)              | `type_node`   |
//! | `MatrixTypeNode/VectorTypeNode.type` (str)    | `type_str`    |
//! | `SetTypeNode.type` (list of str)              | `type_strs`   |
//! | `name` as str (NamedType, ElementConvert)     | `name_str`    |
//! | `op` as str (Assign, AddSub, BinComp, Destructuring) | `op_str` |
//! | `MulNode.op` / `DivNode.op` (enums)           | `mul_op` / `div_op` |
//! | `FactorNode.op` (node)                        | `op`          |
//! | `NormNode.sub` as int / 'F'                   | `sub_int` / `sub_str` |
//! | `MathFuncNode.sub` (str '_')                  | `sub_str`     |
//! | `SetNode.f`, `SetNode.o` (str)                | `f_str`, `o_str` |
//! | `MatrixRowsNode.r` (node)                     | `r_node`      |
//! | `cur_type` (Assign / Destructuring)           | `assign_type` / `destruct_type` |
//! | `func_type` (MathFunc / GPFunc)               | `math_func_type` / `gp_type` |
//! | `FunctionNode.order` (int)                    | `order_int`   |
//! | `loop`                                        | `loop_`       |
//! | `MatrixIndexNode.subs` (list of str/int)      | `subs` (ints as strings) |
//! | `InNode.set` / `NotInNode.set`                | `set_node`    |

use crate::helper::ParseInfo;
use crate::types::{T, VarType};
use indexmap::{IndexMap, IndexSet};
use std::cell::RefCell;
use std::collections::HashMap;
use std::rc::{Rc, Weak};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, PartialOrd, Ord, Default)]
pub enum IRNodeType {
    #[default]
    Invalid = -1,
    Id = 0,
    Double = 1,
    Integer = 2,
    Factor = 3,
    Expression = 4,
    Subexpression = 5,
    Constant = 6,
    Cast = 7,
    Fraction = 8,
    Start = 50,
    Block = 51,
    Assignment = 52,
    If = 53,
    Function = 54,
    LocalFunc = 55,
    Equation = 56,
    Destructuring = 57,
    Condition = 99,
    In = 100,
    NotIn = 101,
    BinComp = 102,
    Eq = 103,
    Ne = 104,
    Lt = 105,
    Le = 106,
    Gt = 107,
    Ge = 108,
    Add = 200,
    Sub = 201,
    Mul = 202,
    Div = 203,
    AddSub = 204,
    Summation = 205,
    Norm = 206,
    Transpose = 207,
    Power = 208,
    Solver = 209,
    Derivative = 210,
    MathFunc = 211,
    Optimize = 212,
    Domain = 213,
    Integral = 214,
    InnerProduct = 215,
    FroProduct = 216,
    HadamardProduct = 217,
    CrossProduct = 218,
    KroneckerProduct = 219,
    DotProduct = 220,
    Squareroot = 221,
    PseudoInverse = 222,
    Divergence = 223,
    Gradient = 224,
    Laplace = 225,
    Partial = 226,
    Size = 227,
    Module = 228,
    Geometry = 229,
    GPFunction = 230,
    Union = 231,
    Intersection = 232,
    Difference = 233,
    UnionSequence = 234,
    Matrix = 300,
    MatrixRows = 301,
    MatrixRow = 302,
    MatrixRowCommas = 303,
    ExpInMatrix = 304,
    SparseMatrix = 305,
    SparseIfs = 306,
    SparseIf = 307,
    SparseOther = 308,
    NumMatrix = 309,
    Vector = 310,
    ToMatrix = 311,
    MultiConds = 312,
    Set = 313,
    ElementConvert = 314,
    ToDouble = 315,
    MatrixIndex = 320,
    VectorIndex = 321,
    SequenceIndex = 322,
    SeqDimIndex = 323,
    TupleIndex = 324,
    SetIndex = 325,
    ParamsBlock = 399,
    WhereConditions = 400,
    WhereCondition = 401,
    MatrixType = 402,
    VectorType = 403,
    SetType = 404,
    ScalarType = 405,
    FunctionType = 406,
    MappingType = 407,
    TupleType = 408,
    NamedType = 409,
    Import = 500,
    ImportVar = 501,
    OdeFirstOrder = 600,
}

macro_rules! py_enum {
    ($name:ident { $($variant:ident = $val:expr),* $(,)? } default $def:ident) => {
        #[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
        pub enum $name { $($variant = $val),* }
        impl Default for $name { fn default() -> Self { $name::$def } }
    };
}

py_enum!(LocalFuncDefType { Invalid = -1, Parenthesis = 0, Bracket = 1 } default Invalid);
py_enum!(DestructuringType { Invalid = -1, Set = 0, Sequence = 1, Vector = 2, Tuple = 3, List = 4 } default Set);
py_enum!(AssignType { Invalid = -1, Normal = 0, Solver = 1 } default Normal);
py_enum!(ConditionType { Invalid = -1, And = 0, Or = 1 } default And);
py_enum!(UnionFormat { Invalid = -1, Normal = 0, Add = 1 } default Normal);
py_enum!(DiffFormat { Invalid = -1, Normal = 0, Split = 1 } default Normal);
py_enum!(MulOpType { Invalid = -1, Dot = 0 } default Invalid);
py_enum!(DivOpType { Invalid = -1, Slash = 0, Unicode = 1 } default Slash);
py_enum!(EleConvertType {
    Invalid = -1, ToVertexSet = 0, ToEdgeSet = 1, ToFaceSet = 2, ToTetSet = 3, ToSimplicialSet = 4, ToTuple = 5,
    ToVertex = 6, ToEdge = 7, ToFace = 8, ToTet = 9, ToSequence = 10
} default Invalid);
py_enum!(OptimizeType { Invalid = -1, Min = 0, Max = 1, Argmin = 2, Argmax = 3 } default Invalid);
py_enum!(NormType {
    Invalid = -1, Frobenius = 0, Nuclear = 1, Integer = 2, Identifier = 3, Max = 4, Det = 5, Size = 6
} default Invalid);
py_enum!(ConstantType { Invalid = -1, Pi = 0, E = 1, Inf = 2 } default Invalid);
py_enum!(DerivativeType { Invalid = -1, Fraction = 0, SFraction = 1, Prime = 2, Dot = 3 } default Fraction);
py_enum!(PartialOrderType { Invalid = -1, Normal = 0, Hessian = 1 } default Normal);
py_enum!(FuncFormat { Invalid = -1, Normal = 0, Short = 1 } default Normal);
py_enum!(OrderFormat { Invalid = -1, Prime = 0, Dot = 1 } default Prime);
py_enum!(MathFuncType {
    Invalid = -1, Sin = 0, Asin = 1, Cos = 2, Acos = 3, Tan = 4, Atan = 5, Sinh = 6, Asinh = 7, Cosh = 8,
    Acosh = 9, Tanh = 10, Atanh = 11, Cot = 12, Sec = 13, Csc = 14, Atan2 = 15, Exp = 16, Log = 17, Log2 = 18,
    Log10 = 19, Ln = 20, Sqrt = 21, Trace = 22, Diag = 23, Vec = 24, Det = 25, Rank = 26, Null = 27, Orth = 28,
    Inv = 29, Min = 30, Max = 31, InverseVec = 32, SVD = 33
} default Invalid);
py_enum!(GPType {
    Invalid = -1, FacesOfEdge = 0, Dihedral = 1, FaceNormal = 2, AdjacentVerticesV = 3, IncidentEdgesV = 4,
    IncidentFacesV = 5, IncidentVerticesE = 6, IncidentFacesE = 7, DiamondVerticesE = 8, IncidentVerticesF = 9,
    IncidentEdgesF = 10, AdjacentFacesF = 11, BuildVertexVector = 12, BuildEdgeVector = 13, BuildFaceVector = 14,
    GetVerticesE = 15, GetVerticesF = 16, GetEdgesF = 17, Vertices = 18, Edges = 19, Faces = 20, Tets = 21,
    Diamond = 22, DiamondFacesE = 23, VectorToVertex = 24, VectorToEdge = 25, VectorToFace = 26,
    VertexPositions = 27, FaceMatrix = 28, Star = 100, Closure = 101, Link = 102, Boundary = 103, IsComplex = 104,
    IsPureComplex = 105, MeshSets = 200, BoundaryMatrices = 201, UnsignedBoundaryMatrices = 202,
    CanonicalVertexOrderings = 203, NonZeros = 204, IndicatorVector = 205, ValueSet = 206
} default Invalid);

/// `EqTypeEnum` flags
pub const EQ_INVALID: u8 = 0;
pub const EQ_DEFAULT: u8 = 1;
pub const EQ_NORMAL: u8 = 1;
pub const EQ_ODE: u8 = 2;
pub const EQ_PDE: u8 = 4;

/// An item of `StartNode.vblock`: an IR node, or (before the second walk
/// replaces it) the list of parse-tree statements of a `Statements` block.
#[derive(Clone, Debug)]
pub enum VBlock {
    Ir(N),
    Stmts(Vec<crate::pnode::Val>),
}

/// A shared, mutable IR node (a Python IR object reference).
#[derive(Clone, Debug)]
pub struct N(pub Rc<RefCell<IrNode>>);

impl PartialEq for N {
    /// identity (Python `is`)
    fn eq(&self, other: &Self) -> bool {
        Rc::ptr_eq(&self.0, &other.0)
    }
}

macro_rules! ir_node {
    ($($field:ident : $ty:ty),* $(,)?) => {
        /// Union of the attributes of all IR node classes.
        #[derive(Clone, Debug, Default)]
        pub struct IrNode {
            pub node_type: IRNodeType,
            pub la_type: Option<T>,
            pub la_types: Option<Vec<T>>,
            pub parent: Option<Weak<RefCell<IrNode>>>,
            pub parse_info: Option<ParseInfo>,
            pub raw_text: Option<String>,
            $(pub $field: $ty,)*
        }
        impl N {
            $(pub fn $field(&self) -> $ty { self.0.borrow().$field.clone() })*
        }
    };
}

ir_node! {
    // StartNode
    cond: Option<N>, given_cond: Option<N>, stat: Option<N>, directives: Vec<N>, vblock: Vec<VBlock>,
    module_list: Vec<crate::codegen::CodeModule>, module_syms: IndexMap<String, T>,
    // ParamsBlock, WhereConditions, WhereCondition
    annotation: Option<String>, conds: Option<N>, values: Vec<Option<N>>, ids: Vec<N>, type_node: Option<N>,
    attrib: Option<String>, desc: Option<String>, belong: Option<String>,
    // type nodes
    type_str: Option<String>, type_strs: Vec<String>, type1: Option<String>, type2: Option<String>, cnt: Option<i64>,
    sub_types: Vec<N>, homogeneous_types: Vec<N>, id1: Option<N>, id2: Option<N>, is_int: bool,
    name_str: Option<String>, empty: Option<String>, separators: Vec<String>, params: Vec<N>, ret: Option<N>,
    src: Option<N>, dst: Option<N>, ele_set: Option<N>, subset: bool,
    // Import
    package: Option<N>, module: Option<N>, names: Vec<N>, r_dict: IndexMap<String, String>, import_all: bool,
    rname: Option<N>,
    // Block
    stmts: Vec<N>, meshset_list: Vec<usize>,
    // LocalFunc, Function
    name: Option<N>, identity_name: Option<String>, expr: Vec<N>, symbols: IndexSet<String>,
    def_type: LocalFuncDefType, defs: Vec<N>, n_subs: usize, extra_list: Vec<N>, tex_list: Vec<Option<N>>,
    scope_name: Option<String>, mode: FuncFormat, order_int: Option<i64>, order_mode: OrderFormat,
    // Assignment, Destructuring, Equation
    lefts: Vec<N>, rights: Vec<N>, op_str: Option<String>, lhs_sub_dict: IndexMap<String, Vec<N>>,
    optimize_param: bool, assign_type: AssignType, destruct_type: DestructuringType, la_list: Vec<T>,
    unknown_id: Option<N>, change_ele_only: bool, need_sparse_hessian: bool, new_hessian_name: String,
    hessian_var: String, eq_type: u8, init_list: Vec<N>, param_dict: IndexMap<usize, Vec<String>>,
    // conditions
    loop_: bool, cond_list: Vec<N>, cond_type: ConditionType, tex_node: Option<N>, items: Vec<N>, set_node: Option<N>,
    comp_type: IRNodeType,
    // binary operators
    left: Option<N>, right: Option<N>, left_str: Option<String>, union_format: UnionFormat,
    diff_format: DiffFormat, mul_op: MulOpType, div_op: DivOpType,
    // Expression, Factor, Cast, Subexpression
    value: Option<N>, sign: Option<String>, op: Option<N>, sub: Option<N>, nm: Option<N>, id: Option<N>,
    num: Option<N>, m: Option<N>, v: Option<N>, s: Option<N>, c: Option<N>, size: Option<N>,
    // Id
    main_id: String, subs: Vec<String>,
    // Matrix, Vector, Set, ElementConvert
    symbol: Option<String>, enum_list: Vec<String>, range: Option<N>, f_str: Option<String>, o_str: Option<String>,
    to_type: EleConvertType, item: Option<N>, rs: Option<N>, r_node: Option<N>, rc: Option<N>, exp: Option<N>,
    // Summation, UnionSequence
    content: Option<String>, sym_dict: IndexMap<String, Vec<String>>, use_tuple: bool, lower: Option<N>,
    upper: Option<N>, sum_index_list: Vec<String>,
    // Optimize, Integral, Domain
    opt_type: OptimizeType, base_list: Vec<N>, base_type_list: Vec<N>, def_list: Vec<N>, key: String,
    init_syms: Vec<String>, domain: Option<N>, base: Option<N>,
    // Norm, products, power, solver
    sub_int: Option<i64>, sub_str: Option<String>, norm_type: NormType, f: Option<N>, t: Option<String>,
    r: Option<String>, power: Option<N>, pow: Option<String>,
    // derivatives
    d_type: DerivativeType, order: Option<N>, lower_list: Vec<N>, lorder_list: Vec<N>,
    order_type: PartialOrderType, need_sparse: bool,
    // Size, MathFunc, GPFunc
    param: Option<N>, remain_params: Vec<N>, math_func_type: MathFuncType, gp_type: GPType,
    func_name: Option<String>, separator: Option<String>,
    // MultiConds, SparseMatrix, SparseIf(s)
    ifs: Option<N>, other: Option<N>, lhs: Option<String>, id0: Option<N>, first_in_list: bool,
    in_cond_only: bool,
    // index nodes
    main: Option<N>, row_index: Option<N>, col_index: Option<N>, main_index: Option<N>,
    dependence: Option<String>, slice_matrix: bool, real_symbol: Option<String>, dim_index: usize,
    // numbers, constants
    int_value: i64, str_value: String, c_type: ConstantType, numerator: i64, denominator: i64, unicode: String,
}

impl N {
    /// A node of the given class with default attributes (an invalid type).
    pub fn new(node_type: IRNodeType) -> N {
        N(Rc::new(RefCell::new(IrNode { node_type, la_type: Some(T::invalid()), ..Default::default() })))
    }

    /// A node with parse info and raw text, as `XxxNode(parse_info=..., raw_text=...)`.
    pub fn with(node_type: IRNodeType, parse_info: Option<ParseInfo>, raw_text: Option<String>) -> N {
        let n = N::new(node_type);
        n.set(|x| {
            x.parse_info = parse_info;
            x.raw_text = raw_text;
        });
        n
    }

    pub fn set(&self, f: impl FnOnce(&mut IrNode)) {
        f(&mut self.0.borrow_mut())
    }

    pub fn borrow(&self) -> std::cell::Ref<'_, IrNode> {
        self.0.borrow()
    }

    pub fn node_type(&self) -> IRNodeType {
        self.0.borrow().node_type
    }

    pub fn is_node(&self, t: IRNodeType) -> bool {
        self.node_type() == t
    }

    /// `node.la_type` (a fresh invalid type if unset, like the Python property).
    pub fn la_type(&self) -> T {
        if let Some(t) = &self.0.borrow().la_type {
            return t.clone();
        }
        T::invalid()
    }

    /// `node.la_type = t` (None becomes an invalid type).
    pub fn set_la_type(&self, t: Option<T>) {
        self.set(|n| {
            n.la_type = Some(t.unwrap_or_else(T::invalid));
            n.la_types = None;
        });
    }

    /// Some nodes have a list of types as `la_type` (multiple return values,
    /// argmin over several variables).
    pub fn la_types(&self) -> Option<Vec<T>> {
        self.0.borrow().la_types.clone()
    }

    pub fn set_la_types(&self, ts: Vec<T>) {
        self.set(|n| n.la_types = Some(ts));
    }

    pub fn parse_info(&self) -> Option<ParseInfo> {
        self.0.borrow().parse_info.clone()
    }

    pub fn raw_text(&self) -> Option<String> {
        self.0.borrow().raw_text.clone()
    }

    /// `node.raw_text` where Python would format None as "None".
    pub fn raw_text_or_none(&self) -> String {
        self.raw_text().unwrap_or_else(|| "None".into())
    }

    pub fn set_parent(&self, parent: &N) {
        let w = Rc::downgrade(&parent.0);
        self.set(|n| n.parent = Some(w));
    }

    pub fn parent(&self) -> Option<N> {
        self.0.borrow().parent.as_ref().and_then(|w| w.upgrade()).map(N)
    }

    /// `get_ancestor(node_type)`
    pub fn get_ancestor(&self, t: IRNodeType) -> Option<N> {
        let mut cur = self.parent();
        while let Some(p) = cur {
            if p.is_node(t) {
                return Some(p);
            }
            cur = p.parent();
        }
        None
    }

    /// `get_child(node_type)` (defined for If, BinComp, Expression, Add, Sub, AddSub)
    pub fn get_child(&self, t: IRNodeType) -> Option<N> {
        match self.node_type() {
            IRNodeType::If => {
                let cond = self.cond()?;
                if cond.is_node(t) {
                    Some(cond)
                } else {
                    cond.get_child(t)
                }
            }
            IRNodeType::Expression => {
                let v = self.value()?;
                if v.is_node(t) {
                    Some(v)
                } else {
                    v.get_child(t)
                }
            }
            IRNodeType::BinComp | IRNodeType::Add | IRNodeType::Sub | IRNodeType::AddSub => {
                let (l, r) = (self.left()?, self.right()?);
                if l.is_node(t) {
                    Some(l)
                } else if r.is_node(t) {
                    Some(r)
                } else {
                    l.get_child(t).or_else(|| r.get_child(t))
                }
            }
            _ => None,
        }
    }

    /// `contain_sym(sym)`: substring test on raw text.
    pub fn contain_sym(&self, sym: &str) -> bool {
        self.raw_text().is_some_and(|r| r.contains(sym))
    }

    /// `get_signature(extra)` (FunctionNode and DerivativeNode override it)
    pub fn get_signature(&self, extra_param: Option<&str>) -> Option<String> {
        match self.node_type() {
            IRNodeType::Function => {
                if let Some(order) = self.order_int() {
                    let name = self.name().unwrap().get_main_id();
                    if order == 1 {
                        let params = self.params();
                        if params.len() == 1 {
                            return Some(format!("{}&{}", name, params[0].raw_text_or_none()));
                        } else if let Some(p) = extra_param {
                            return Some(format!("{name}&{p}"));
                        }
                    }
                    return Some(name);
                }
                self.name().unwrap().raw_text()
            }
            IRNodeType::Derivative => {
                if self.is_first_order() {
                    return Some(format!(
                        "{}&{}",
                        self.upper().unwrap().raw_text_or_none(),
                        self.lower().unwrap().raw_text_or_none()
                    ));
                }
                self.raw_text()
            }
            _ => self.raw_text(),
        }
    }

    /// `DerivativeNode.is_first_order()`
    pub fn is_first_order(&self) -> bool {
        match self.order() {
            None => true,
            Some(o) => {
                if o.is_node(IRNodeType::Integer) {
                    o.int_value() == 1
                } else {
                    o.raw_text().as_deref() == Some("1")
                }
            }
        }
    }

    // -- identifiers -------------------------------------------------------

    /// `contain_subscript()`
    pub fn contain_subscript(&self) -> bool {
        match self.node_type() {
            IRNodeType::Id => !self.subs().is_empty(),
            IRNodeType::MatrixIndex
            | IRNodeType::VectorIndex
            | IRNodeType::SetIndex
            | IRNodeType::TupleIndex
            | IRNodeType::SequenceIndex => true,
            _ => false,
        }
    }

    /// `get_main_id()`
    pub fn get_main_id(&self) -> String {
        match self.node_type() {
            IRNodeType::Id => self.main_id(),
            IRNodeType::MatrixIndex
            | IRNodeType::VectorIndex
            | IRNodeType::SetIndex
            | IRNodeType::TupleIndex
            | IRNodeType::SequenceIndex
            | IRNodeType::SeqDimIndex => self.main().expect("index node without main").get_main_id(),
            other => panic!("get_main_id on {other:?}"),
        }
    }

    /// `get_name()`
    pub fn get_name(&self) -> String {
        match self.node_type() {
            IRNodeType::Id => {
                let subs = self.subs();
                if subs.is_empty() {
                    self.main_id()
                } else {
                    format!("{}_{}", self.main_id(), subs.concat())
                }
            }
            IRNodeType::MatrixIndex
            | IRNodeType::VectorIndex
            | IRNodeType::SetIndex
            | IRNodeType::TupleIndex
            | IRNodeType::SequenceIndex
            | IRNodeType::SeqDimIndex => self.raw_text().unwrap_or_default(),
            other => panic!("get_name on {other:?}"),
        }
    }

    fn node_content(n: &Option<N>) -> String {
        match n {
            None => "*".into(),
            Some(n) if n.is_node(IRNodeType::Id) => n.get_main_id(),
            Some(n) if n.is_node(IRNodeType::Integer) => n.int_value().to_string(),
            Some(_) => panic!("get_node_content: unsupported index"),
        }
    }

    /// `get_all_ids()`: (main id, subscripts)
    pub fn get_all_ids(&self) -> (String, Vec<String>) {
        match self.node_type() {
            IRNodeType::Id => (self.main_id(), self.subs()),
            IRNodeType::MatrixIndex => (
                self.get_main_id(),
                vec![N::node_content(&self.row_index()), N::node_content(&self.col_index())],
            ),
            IRNodeType::VectorIndex | IRNodeType::SetIndex => {
                (self.get_main_id(), vec![N::node_content(&self.row_index())])
            }
            IRNodeType::TupleIndex => (self.get_main_id(), vec![self.row_index().unwrap().get_main_id()]),
            IRNodeType::SequenceIndex => {
                if self.row_index().is_some() {
                    (
                        self.get_main_id(),
                        vec![
                            N::node_content(&self.main_index()),
                            N::node_content(&self.row_index()),
                            N::node_content(&self.col_index()),
                        ],
                    )
                } else {
                    (self.get_main_id(), vec![N::node_content(&self.main_index())])
                }
            }
            other => panic!("get_all_ids on {other:?}"),
        }
    }

    fn is_id_named(n: &Option<N>, sym: &str) -> bool {
        n.as_ref().is_some_and(|n| n.is_node(IRNodeType::Id) && n.get_main_id() == sym)
    }

    /// `contain_sub_sym(sym)`
    pub fn contain_sub_sym(&self, sym: &str) -> bool {
        match self.node_type() {
            IRNodeType::MatrixIndex => {
                N::is_id_named(&self.row_index(), sym) || N::is_id_named(&self.col_index(), sym)
            }
            IRNodeType::VectorIndex | IRNodeType::SetIndex | IRNodeType::TupleIndex => {
                N::is_id_named(&self.row_index(), sym)
            }
            IRNodeType::SequenceIndex => {
                N::is_id_named(&self.main_index(), sym)
                    || N::is_id_named(&self.row_index(), sym)
                    || N::is_id_named(&self.col_index(), sym)
            }
            IRNodeType::SeqDimIndex => N::is_id_named(&self.main_index(), sym),
            _ => false,
        }
    }

    pub fn same_as_size_sym(&self, sym: &str) -> bool {
        N::is_id_named(&self.main_index(), sym)
    }
    pub fn same_as_row_sym(&self, sym: &str) -> bool {
        N::is_id_named(&self.row_index(), sym)
    }
    pub fn same_as_col_sym(&self, sym: &str) -> bool {
        N::is_id_named(&self.col_index(), sym)
    }

    /// `process_subs_dict(subs_dict)`: register this index node under every
    /// subscript symbol it uses.
    pub fn process_subs_dict(&self, subs_dict: &mut IndexMap<String, Vec<N>>) {
        let keys: Vec<String> = subs_dict.keys().cloned().collect();
        for key in keys {
            if self.contain_sub_sym(&key) {
                subs_dict.get_mut(&key).unwrap().push(self.clone());
            }
        }
    }

    /// `IdNode.convert_to_vector_index()` / `convert_to_sequence_index()` are
    /// unused by the compiler; omitted.

    /// `ExpressionNode.is_id_node()`
    pub fn is_id_node(&self) -> bool {
        self.value().is_some_and(|v| v.is_node(IRNodeType::Factor) && v.id().is_some())
    }

    // -- conditions ----------------------------------------------------------

    /// `ConditionNode.get_single_in_node()`
    pub fn get_single_in_node(&self) -> Option<N> {
        let cl = self.cond_list();
        if cl.len() == 1 {
            if cl[0].is_node(IRNodeType::Condition) {
                return cl[0].get_single_in_node();
            }
            let c = cl[0].cond()?;
            if c.is_node(IRNodeType::In) {
                return Some(c);
            }
        }
        None
    }

    /// `same_subs(subs)` for ConditionNode and InNode
    pub fn same_subs(&self, subs: &[String]) -> bool {
        match self.node_type() {
            IRNodeType::Condition => self.get_single_in_node().is_some_and(|n| n.same_subs(subs)),
            IRNodeType::In => {
                let items = self.items();
                if subs.len() == items.len() {
                    let raw: std::collections::HashSet<String> =
                        items.iter().map(|i| i.raw_text_or_none()).collect();
                    let s: std::collections::HashSet<String> = subs.iter().cloned().collect();
                    return raw == s;
                }
                false
            }
            _ => false,
        }
    }

    /// `set_loop(loop)` for If, Condition, SparseIf
    pub fn set_loop(&self, value: bool) {
        match self.node_type() {
            IRNodeType::If => {
                if let Some(c) = self.cond() {
                    c.set(|n| n.loop_ = value);
                }
            }
            IRNodeType::Condition => {
                self.set(|n| n.loop_ = value);
                for c in self.cond_list() {
                    c.set_loop(value);
                }
            }
            IRNodeType::SparseIf => {
                self.set(|n| n.loop_ = value);
                if let Some(c) = self.cond() {
                    c.set_loop(value);
                }
            }
            _ => {}
        }
    }

    /// `SparseIfsNode.set_in_cond_only(value)`
    pub fn set_in_cond_only(&self, value: bool) {
        self.set(|n| n.in_cond_only = value);
        if value {
            for c in self.cond_list() {
                c.set_loop(true);
            }
        }
    }

    /// `AddSubNode.split_node()`: an Add and a Sub with the same operands.
    pub fn split_node(&self) -> (N, N) {
        let add = N::new(IRNodeType::Add);
        let sub = N::new(IRNodeType::Sub);
        for n in [&add, &sub] {
            n.set(|x| {
                x.left = self.left();
                x.right = self.right();
            });
            if let Some(p) = self.parent() {
                n.set_parent(&p);
            }
        }
        (add, sub)
    }

    /// `StartNode.get_block_list()`: (params blocks, statements, indices of statement blocks)
    pub fn get_block_list(&self) -> (Vec<N>, Vec<crate::pnode::Val>, Vec<usize>) {
        let mut params = Vec::new();
        let mut stats = Vec::new();
        let mut index = Vec::new();
        for (i, vb) in self.vblock().into_iter().enumerate() {
            match vb {
                VBlock::Stmts(s) => {
                    stats.extend(s);
                    index.push(i);
                }
                VBlock::Ir(n) => params.push(n),
            }
        }
        (params, stats, index)
    }

    /// `StartNode.get_package_dict()`: package -> sorted unique imported names
    pub fn get_package_dict(&self) -> IndexMap<String, Vec<String>> {
        let mut d: IndexMap<String, Vec<String>> = IndexMap::new();
        for dir in self.directives() {
            if let Some(pkg) = dir.package() {
                let name = pkg.get_name();
                let mut v = d.get(&name).cloned().unwrap_or_default();
                v.extend(dir.get_name_list());
                v.sort();
                v.dedup();
                d.insert(name, v);
            }
        }
        d
    }

    /// `StartNode.get_package_rdict()`
    pub fn get_package_rdict(&self) -> IndexMap<String, IndexMap<String, String>> {
        let mut d = IndexMap::new();
        for dir in self.directives() {
            if let Some(pkg) = dir.package() {
                d.entry(pkg.get_name()).or_insert_with(|| dir.r_dict());
            }
        }
        d
    }

    /// `StartNode.get_module_pars_list()`
    pub fn get_module_pars_list(&self) -> Vec<String> {
        let mut out: Vec<String> = Vec::new();
        for dir in self.directives() {
            if dir.module().is_some() {
                for p in dir.params().iter().chain(dir.names().iter()) {
                    let n = p.get_name();
                    if !out.contains(&n) {
                        out.push(n);
                    }
                }
            }
        }
        out
    }

    /// `StartNode.get_module_directives()`
    pub fn get_module_directives(&self) -> Vec<N> {
        self.directives().into_iter().filter(|d| d.module().is_some()).collect()
    }

    /// `ImportNode.get_name_list()`
    pub fn get_name_list(&self) -> Vec<String> {
        self.names().iter().map(|n| n.get_name()).collect()
    }

    /// `ImportNode.get_rname_list()`
    pub fn get_rname_list(&self) -> Vec<String> {
        let r = self.r_dict();
        self.names().iter().map(|n| r[&n.get_name()].clone()).collect()
    }

    /// `ImportNode.get_name_raw_list()`
    pub fn get_name_raw_list(&self) -> Vec<String> {
        let r = self.r_dict();
        self.names()
            .iter()
            .map(|n| {
                let raw = n.get_name();
                match r.get(&raw) {
                    Some(v) if *v != raw => format!("{raw} as {v}"),
                    _ => raw,
                }
            })
            .collect()
    }

    /// `ImportNode.get_param_list()`
    pub fn get_param_list(&self) -> Vec<String> {
        self.params().iter().map(|p| p.get_name()).collect()
    }

    /// `ImportNode.get_imported_sym()`
    pub fn get_imported_sym(&self) -> Vec<String> {
        let r = self.r_dict();
        self.names()
            .iter()
            .map(|n| {
                let m = n.get_main_id();
                r.get(&m).cloned().unwrap_or(m)
            })
            .collect()
    }

    /// `WhereConditionNode.get_type_dict()`
    pub fn get_type_dict(&self) -> IndexMap<String, T> {
        let t = self.type_node().unwrap().la_type();
        self.ids().iter().map(|id| (id.get_main_id(), t.clone())).collect()
    }

    /// `SummationNode.iter_mesh_ele()`
    pub fn iter_mesh_ele(&self) -> bool {
        self.la_type().is_mesh_ele_set()
    }

    // -- construction helpers -------------------------------------------------

    /// `IdNode(main_id, subs, parse_info, raw_text)`
    pub fn id_node(main_id: &str, subs: Vec<String>, parse_info: Option<ParseInfo>, raw_text: Option<String>) -> N {
        let n = N::with(IRNodeType::Id, parse_info, raw_text);
        n.set(|x| {
            x.main_id = main_id.to_string();
            x.subs = subs;
        });
        n
    }

    /// `IntegerNode(value=v)`
    pub fn integer(value: i64, parse_info: Option<ParseInfo>, raw_text: Option<String>) -> N {
        let n = N::with(IRNodeType::Integer, parse_info, raw_text);
        n.set(|x| x.int_value = value);
        n.set_la_type(Some(T::scalar_int(true)));
        n
    }

    /// `CastNode(value=v, raw_text=...)`: takes parse info, text and type from `v`.
    pub fn cast(value: &N, raw_text: Option<String>) -> N {
        let n = N::with(IRNodeType::Cast, None, raw_text);
        n.set(|x| {
            x.value = Some(value.clone());
            x.parse_info = value.parse_info();
            x.raw_text = value.raw_text();
        });
        n.set_la_type(Some(value.la_type()));
        n
    }

    // -- deep copy -----------------------------------------------------------

    /// `copy.deepcopy(node)`: copies the subtree, its types (preserving
    /// sharing within the copy); parent links still point at the originals.
    pub fn deep_copy(&self) -> N {
        let mut memo = IrCopyMemo::default();
        self.deep_copy_memo(&mut memo)
    }

    fn deep_copy_memo(&self, memo: &mut IrCopyMemo) -> N {
        let key = Rc::as_ptr(&self.0) as usize;
        if let Some(n) = memo.nodes.get(&key) {
            return n.clone();
        }
        let copy = N(Rc::new(RefCell::new(IrNode::default())));
        memo.nodes.insert(key, copy.clone());
        let src = self.0.borrow().clone();
        let mut new = src.clone();
        let cn = |o: &Option<N>, memo: &mut IrCopyMemo| o.as_ref().map(|n| n.deep_copy_memo(memo));
        let cv = |v: &Vec<N>, memo: &mut IrCopyMemo| v.iter().map(|n| n.deep_copy_memo(memo)).collect::<Vec<_>>();
        let ct = |o: &Option<T>, memo: &mut IrCopyMemo| o.as_ref().map(|t| t.deep_copy_memo(&mut memo.types));
        new.la_type = ct(&src.la_type, memo);
        new.la_types = src.la_types.as_ref().map(|v| v.iter().map(|t| t.deep_copy_memo(&mut memo.types)).collect());
        // deepcopy treats weak references as atomic: copies keep the original parent
        new.parent = src.parent.clone();
        macro_rules! copy_nodes {
            ($($f:ident),*) => { $(new.$f = cn(&src.$f, memo);)* };
        }
        macro_rules! copy_vecs {
            ($($f:ident),*) => { $(new.$f = cv(&src.$f, memo);)* };
        }
        copy_nodes!(
            cond, stat, conds, type_node, id1, id2, ret, src, dst, ele_set, package, module, rname, name, unknown_id,
            tex_node, set_node, left, right, value, op, sub, nm, id, num, m, v, s, c, size, range, item, rs, r_node, rc,
            exp, lower, upper, domain, base, f, power, order, param, ifs, other, id0, main, row_index, col_index,
            main_index
        );
        copy_vecs!(
            directives, sub_types, homogeneous_types, params, ids, names, stmts, expr, defs, extra_list, lefts, rights,
            init_list, cond_list, items, base_list, base_type_list, def_list, lower_list, lorder_list, remain_params
        );
        new.values = src.values.iter().map(|o| cn(o, memo)).collect();
        new.tex_list = src.tex_list.iter().map(|o| cn(o, memo)).collect();
        *copy.0.borrow_mut() = new;
        copy
    }
}

#[derive(Default)]
struct IrCopyMemo {
    nodes: HashMap<usize, N>,
    types: crate::types::DeepCopyMemo,
}

/// `is_derivative_node(node)`: a gradient, derivative or partial derivative.
pub fn is_derivative_node(node: &N) -> bool {
    let mut f = node.clone();
    if f.is_node(IRNodeType::Subexpression) {
        f = f.value().unwrap();
    }
    if f.is_node(IRNodeType::Expression) {
        f = f.value().unwrap();
    }
    if f.is_node(IRNodeType::Factor) {
        if let Some(op) = f.op() {
            return op.is_node(IRNodeType::Gradient)
                || op.is_node(IRNodeType::Derivative)
                || op.is_node(IRNodeType::Partial);
        }
    }
    false
}

/// Whether a type is the base `LaVarType` with `VarTypeEnum.SCALAR` (used
/// for `NodeInfo(VarTypeEnum.SCALAR)`).
pub fn var_type_marker(vt: VarType) -> T {
    T::base(vt)
}
