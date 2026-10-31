//! I❤LA types (la_parser/la_types.py).
//!
//! The Python compiler's types are mutable objects that are shared: the type
//! walker stores the same object in symbol tables and IR nodes and mutates it
//! (e.g. `node_type.symbol = value`), and deep-copies where it wants
//! independence. `T` is a shared, mutable handle with the same semantics:
//! cloning a `T` shares the type, `T::deep_copy` copies it (preserving
//! sharing inside the copied structure, as `copy.deepcopy` does).
//!
//! One Python quirk is reproduced on purpose because outputs depend on it:
//! `MatrixType` and `VectorType` have a mutable default argument
//! `element_type=ScalarType()`, so every matrix (vector) created without an
//! element type shares one scalar type object per process, and setting its
//! `is_int` or `owner` affects all of them. See `default_matrix_element`.

use crate::dims::{mul_dims, Dim};
use crate::ir::N;
use indexmap::IndexMap;
use std::cell::RefCell;
use std::collections::HashMap;
use std::rc::Rc;

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Default)]
pub enum VarType {
    #[default]
    Invalid = 0,
    Sequence = 1,
    Matrix = 2,
    Vector = 3,
    Set = 4,
    Scalar = 5,
    Function = 6,
    Index = 7,
    Mapping = 8,
    Tuple = 9,
    OverloadingFunction = 10,
    VertexType = 11,
    EdgeType = 12,
    FaceType = 13,
    TetType = 14,
    Mesh = 15,
}

impl VarType {
    /// `str(VarTypeEnum.X)`
    pub fn py_str(&self) -> String {
        let name = match self {
            VarType::Invalid => "INVALID",
            VarType::Sequence => "SEQUENCE",
            VarType::Matrix => "MATRIX",
            VarType::Vector => "VECTOR",
            VarType::Set => "SET",
            VarType::Scalar => "SCALAR",
            VarType::Function => "FUNCTION",
            VarType::Index => "INDEX",
            VarType::Mapping => "MAPPING",
            VarType::Tuple => "TUPLE",
            VarType::OverloadingFunction => "OVERLOADINGFUNCTION",
            VarType::VertexType => "VERTEXTYPE",
            VarType::EdgeType => "EDGETYPE",
            VarType::FaceType => "FACETYPE",
            VarType::TetType => "TETTYPE",
            VarType::Mesh => "MESH",
        };
        format!("VarTypeEnum.{name}")
    }
}

/// `DynamicTypeEnum` flags
pub const DYN_INVALID: u8 = 0;
pub const DYN_ROW: u8 = 1;
pub const DYN_COL: u8 = 2;
pub const DYN_DIM: u8 = 4;

/// `SetTypeEnum` (also used as the element kind of index scalars)
#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub enum SetKind {
    #[default]
    Default,
    Vertex,
    Edge,
    Face,
    Tet,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub enum MeshKind {
    Default = 0,
    #[default]
    Triangle = 1,
    PointCloud = 2,
    Polygon = 3,
    Tetrahedron = 4,
    Polyhedron = 5,
    EdgeMesh = 6,
    FaceMesh = 7,
    CellMesh = 8,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub enum FuncKind {
    Invalid = -1,
    #[default]
    Determined = 0,
    Dynamic = 1,
}

/// The Python class of a type (behavior differs between subclasses that share
/// a `VarType`, e.g. `VertexType` vs `ScalarType`).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub enum Class {
    #[default]
    Base,
    Scalar,
    Int,
    Vertex,
    Edge,
    Face,
    Tet,
    Mesh,
    Sequence,
    Matrix,
    Vector,
    Set,
    VertexSet,
    EdgeSet,
    FaceSet,
    TetSet,
    Tuple,
    SimplicialSet,
    Index,
    Function,
    Overloading,
    Mapping,
}

/// All attributes of all type classes (unused ones keep their defaults).
#[derive(Clone, Debug, Default)]
pub struct LaType {
    pub class: Class,
    pub var_type: VarType,
    pub desc: Option<String>,
    pub element_type: Option<T>,
    pub symbol: Option<String>,
    pub index_type: bool,
    pub dynamic: u8,
    pub owner: Option<String>,
    // ScalarType
    pub is_int: bool,
    pub is_constant: bool,
    pub cur_type: SetKind,
    // SequenceType, SetType, TupleType
    pub size: Dim,
    pub check_dim: bool,
    pub length: Dim,
    // MatrixType, VectorType
    pub rows: Dim,
    pub cols: Dim,
    pub rows_ir: Option<N>,
    pub cols_ir: Option<N>,
    pub need_exp: bool,
    pub diagonal: bool,
    pub sparse: bool,
    pub block: bool,
    pub subs: Vec<String>,
    /// block matrix: (row, col) -> [rows, cols] of lifted items
    pub list_dim: Option<IndexMap<(usize, usize), [Dim; 2]>>,
    pub index_var: Option<String>,
    pub value_var: Option<String>,
    /// block matrix items, as IR nodes per row
    pub item_types: Option<Vec<Vec<N>>>,
    // SetType, TupleType
    pub int_list: Vec<bool>,
    pub type_list: Vec<T>,
    // FunctionType
    pub params: Vec<T>,
    pub ret: Vec<T>,
    pub template_symbols: IndexMap<String, usize>,
    pub ret_symbols: Vec<String>,
    pub func_kind: FuncKind,
    // OverloadingFunctionType
    pub func_list: Vec<T>,
    pub fname_list: Option<Vec<String>>,
    pub pre_fname_list: Option<Vec<String>>,
    // MappingType
    pub src: Option<String>,
    pub dst: Option<T>,
    pub ele_set: Option<String>,
    pub subset: bool,
    // MeshType
    pub vi_size: Dim,
    pub ei_size: Dim,
    pub fi_size: Dim,
    pub ti_size: Dim,
    pub cur_mesh: MeshKind,
}

/// A shared, mutable type (a Python type object reference).
#[derive(Clone, Debug)]
pub struct T(pub Rc<RefCell<LaType>>);

impl PartialEq for T {
    /// identity (Python `is`)
    fn eq(&self, other: &Self) -> bool {
        Rc::ptr_eq(&self.0, &other.0)
    }
}

thread_local! {
    static DEFAULT_MATRIX_ELEMENT: T = T::new(LaType { class: Class::Scalar, var_type: VarType::Scalar, ..Default::default() });
    static DEFAULT_VECTOR_ELEMENT: T = T::new(LaType { class: Class::Scalar, var_type: VarType::Scalar, ..Default::default() });
}

/// The `ScalarType()` default argument of `MatrixType.__init__`, shared by
/// all matrices created without an element type (see the module docs).
pub fn default_matrix_element() -> T {
    DEFAULT_MATRIX_ELEMENT.with(|t| t.clone())
}

/// The `ScalarType()` default argument of `VectorType.__init__`.
pub fn default_vector_element() -> T {
    DEFAULT_VECTOR_ELEMENT.with(|t| t.clone())
}

/// Reset the shared default element types (a new process in Python).
pub fn reset_default_elements() {
    for t in [default_matrix_element(), default_vector_element()] {
        let mut b = t.0.borrow_mut();
        *b = LaType { class: Class::Scalar, var_type: VarType::Scalar, ..Default::default() };
    }
}

macro_rules! getters {
    ($($name:ident : $ty:ty),* $(,)?) => {
        impl T {
            $(pub fn $name(&self) -> $ty { self.0.borrow().$name.clone() })*
        }
    };
}

getters! {
    class: Class, var_type: VarType, desc: Option<String>, element_type: Option<T>, symbol: Option<String>,
    index_type: bool, dynamic: u8, owner: Option<String>, is_int: bool, is_constant: bool, cur_type: SetKind,
    size: Dim, check_dim: bool, length: Dim, rows: Dim, cols: Dim, rows_ir: Option<N>, cols_ir: Option<N>,
    need_exp: bool, diagonal: bool, sparse: bool, block: bool, subs: Vec<String>,
    list_dim: Option<IndexMap<(usize, usize), [Dim; 2]>>, index_var: Option<String>, value_var: Option<String>,
    item_types: Option<Vec<Vec<N>>>, int_list: Vec<bool>, type_list: Vec<T>, params: Vec<T>, ret: Vec<T>,
    template_symbols: IndexMap<String, usize>, ret_symbols: Vec<String>, func_kind: FuncKind, func_list: Vec<T>,
    fname_list: Option<Vec<String>>, pre_fname_list: Option<Vec<String>>, src: Option<String>, dst: Option<T>,
    ele_set: Option<String>, subset: bool, vi_size: Dim, ei_size: Dim, fi_size: Dim, ti_size: Dim, cur_mesh: MeshKind,
}

impl T {
    pub fn new(t: LaType) -> T {
        T(Rc::new(RefCell::new(t)))
    }

    /// Mutable access: `t.set(|t| t.rows = 3.into())`.
    pub fn set(&self, f: impl FnOnce(&mut LaType)) {
        f(&mut self.0.borrow_mut())
    }

    pub fn borrow(&self) -> std::cell::Ref<'_, LaType> {
        self.0.borrow()
    }

    /// Element type (panics when absent, like an AttributeError on None).
    pub fn elem(&self) -> T {
        self.element_type().expect("type has no element_type")
    }

    // -- constructors ------------------------------------------------------

    /// `LaVarType(VarTypeEnum.INVALID)`
    pub fn invalid() -> T {
        T::new(LaType::default())
    }

    /// `LaVarType(var_type)`
    pub fn base(var_type: VarType) -> T {
        T::new(LaType { var_type, ..Default::default() })
    }

    /// `ScalarType()`
    pub fn scalar() -> T {
        T::new(LaType { class: Class::Scalar, var_type: VarType::Scalar, ..Default::default() })
    }

    /// `ScalarType(is_int=...)`
    pub fn scalar_int(is_int: bool) -> T {
        let t = T::scalar();
        t.set(|t| t.is_int = is_int);
        t
    }

    /// `IntType()`
    pub fn int_type() -> T {
        T::new(LaType { class: Class::Int, var_type: VarType::Scalar, is_int: true, ..Default::default() })
    }

    fn index_scalar(class: Class, kind: SetKind, owner: Option<String>) -> T {
        T::new(LaType {
            class,
            var_type: VarType::Scalar,
            is_int: true,
            index_type: true,
            cur_type: kind,
            owner,
            ..Default::default()
        })
    }
    /// `VertexType(owner)`
    pub fn vertex(owner: Option<String>) -> T {
        T::index_scalar(Class::Vertex, SetKind::Vertex, owner)
    }
    pub fn edge(owner: Option<String>) -> T {
        T::index_scalar(Class::Edge, SetKind::Edge, owner)
    }
    pub fn face(owner: Option<String>) -> T {
        T::index_scalar(Class::Face, SetKind::Face, owner)
    }
    pub fn tet(owner: Option<String>) -> T {
        T::index_scalar(Class::Tet, SetKind::Tet, owner)
    }

    /// `MeshType(cur_mesh=...)`, dims initialized to 0
    pub fn mesh(cur_mesh: MeshKind) -> T {
        T::new(LaType {
            class: Class::Mesh,
            var_type: VarType::Mesh,
            cur_mesh,
            vi_size: Dim::Int(0),
            ei_size: Dim::Int(0),
            fi_size: Dim::Int(0),
            ti_size: Dim::Int(0),
            ..Default::default()
        })
    }

    /// `SequenceType(size, element_type)`
    pub fn sequence(size: Dim, element_type: T) -> T {
        let t = T::new(LaType {
            class: Class::Sequence,
            var_type: VarType::Sequence,
            size,
            check_dim: true,
            element_type: Some(element_type),
            ..Default::default()
        });
        t
    }

    /// `MatrixType(rows, cols)` with the shared default element type.
    pub fn matrix(rows: impl Into<Dim>, cols: impl Into<Dim>) -> T {
        T::matrix_with(rows.into(), cols.into(), None)
    }

    /// `MatrixType(rows, cols, element_type)`; `None` uses the shared default.
    pub fn matrix_with(rows: Dim, cols: Dim, element_type: Option<T>) -> T {
        let element = element_type.unwrap_or_else(default_matrix_element);
        T::new(LaType {
            class: Class::Matrix,
            var_type: VarType::Matrix,
            rows,
            cols,
            element_type: Some(element),
            ..Default::default()
        })
    }

    /// `VectorType(rows)` with the shared default element type.
    pub fn vector(rows: impl Into<Dim>) -> T {
        T::vector_with(rows.into(), None)
    }

    pub fn vector_with(rows: Dim, element_type: Option<T>) -> T {
        let element = element_type.unwrap_or_else(default_vector_element);
        T::new(LaType {
            class: Class::Vector,
            var_type: VarType::Vector,
            rows,
            cols: Dim::Int(1),
            element_type: Some(element),
            ..Default::default()
        })
    }

    /// `SetType(size, int_list, type_list, element_type=None)`
    pub fn set_type(size: impl Into<Dim>, int_list: Vec<bool>, type_list: Vec<T>, element_type: Option<T>) -> T {
        let t = T::new(LaType {
            class: Class::Set,
            var_type: VarType::Set,
            size: size.into(),
            int_list,
            type_list: type_list.clone(),
            element_type,
            ..Default::default()
        });
        t.init_set_element();
        t
    }

    /// The tail of `SetType.__init__`: derive the element type from the type list.
    fn init_set_element(&self) {
        let (has_elem, tl, owner) = {
            let b = self.0.borrow();
            (b.element_type.is_some(), b.type_list.clone(), b.owner.clone())
        };
        if !has_elem && !tl.is_empty() {
            let elem = if tl.len() > 1 { T::tuple(tl.clone()) } else { tl[0].clone() };
            elem.set(|e| e.owner = owner);
            self.set(|t| t.element_type = Some(elem));
        }
    }

    fn mesh_set(class: Class, kind: SetKind, elem: T, length: Dim, owner: Option<String>) -> T {
        let t = T::new(LaType {
            class,
            var_type: VarType::Set,
            size: Dim::Int(1),
            length,
            int_list: vec![true],
            type_list: vec![elem],
            cur_type: kind,
            owner,
            ..Default::default()
        });
        t.apply_owner_to_element();
        t.init_set_element();
        t
    }
    /// `VertexSetType(length, owner)`
    pub fn vertex_set(length: Dim, owner: Option<String>) -> T {
        T::mesh_set(Class::VertexSet, SetKind::Vertex, T::vertex(None), length, owner)
    }
    pub fn edge_set(length: Dim, owner: Option<String>) -> T {
        T::mesh_set(Class::EdgeSet, SetKind::Edge, T::edge(None), length, owner)
    }
    pub fn face_set(length: Dim, owner: Option<String>) -> T {
        T::mesh_set(Class::FaceSet, SetKind::Face, T::face(None), length, owner)
    }
    pub fn tet_set(length: Dim, owner: Option<String>) -> T {
        T::mesh_set(Class::TetSet, SetKind::Tet, T::tet(None), length, owner)
    }

    /// `TupleType(type_list)`
    pub fn tuple(type_list: Vec<T>) -> T {
        let size = Dim::Int(type_list.len() as i64);
        T::new(LaType { class: Class::Tuple, var_type: VarType::Tuple, type_list, size, ..Default::default() })
    }

    /// `SimplicialSetType()`
    pub fn simplicial_set() -> T {
        let t = T::tuple(vec![
            T::vertex_set(Dim::None, None),
            T::edge_set(Dim::None, None),
            T::face_set(Dim::None, None),
            T::tet_set(Dim::None, None),
        ]);
        t.set(|t| t.class = Class::SimplicialSet);
        t
    }

    /// `FunctionType(params, ret)`
    pub fn function(params: Vec<T>, ret: Vec<T>) -> T {
        T::new(LaType { class: Class::Function, var_type: VarType::Function, params, ret, ..Default::default() })
    }

    /// `OverloadingFunctionType(func_list, fname_list)`
    pub fn overloading(func_list: Vec<T>, fname_list: Option<Vec<String>>) -> T {
        T::new(LaType {
            class: Class::Overloading,
            var_type: VarType::OverloadingFunction,
            func_list,
            fname_list,
            ..Default::default()
        })
    }

    /// `MappingType(...)`
    pub fn mapping(src: Option<String>, dst: Option<T>, ele_set: Option<String>) -> T {
        T::new(LaType { class: Class::Mapping, var_type: VarType::Mapping, src, dst, ele_set, ..Default::default() })
    }

    /// `LaVarType.__init__`: an owner given to the constructor is also given to
    /// an element type that has none (this can modify a shared default).
    pub fn apply_owner_to_element(&self) {
        let (elem, owner) = {
            let b = self.0.borrow();
            (b.element_type.clone(), b.owner.clone())
        };
        if let (Some(e), Some(o)) = (elem, owner) {
            if e.owner().is_none() {
                e.set(|e| e.owner = Some(o));
            }
        }
    }

    /// Set the owner and apply it to the element type, as passing `owner=` to
    /// a constructor does.
    pub fn with_owner(self, owner: Option<String>) -> T {
        self.set(|t| t.owner = owner);
        self.apply_owner_to_element();
        self
    }

    // -- predicates ----------------------------------------------------------

    pub fn is_valid(&self) -> bool {
        self.var_type() != VarType::Invalid
    }
    pub fn is_matrix(&self) -> bool {
        self.var_type() == VarType::Matrix
    }
    pub fn is_sparse_matrix(&self) -> bool {
        let b = self.0.borrow();
        b.var_type == VarType::Matrix && b.sparse
    }
    pub fn is_sequence(&self) -> bool {
        self.var_type() == VarType::Sequence
    }
    pub fn is_matrix_seq(&self) -> bool {
        self.is_sequence() && self.elem().is_matrix()
    }
    pub fn is_vector_seq(&self) -> bool {
        self.is_sequence() && self.elem().is_vector()
    }
    pub fn is_scalar_seq(&self) -> bool {
        self.is_sequence() && self.elem().is_scalar()
    }
    pub fn is_vector(&self) -> bool {
        self.var_type() == VarType::Vector
    }
    pub fn is_scalar(&self) -> bool {
        matches!(
            self.var_type(),
            VarType::Scalar | VarType::VertexType | VarType::EdgeType | VarType::FaceType | VarType::TetType
        )
    }
    pub fn is_mapping(&self) -> bool {
        self.var_type() == VarType::Mapping
    }
    pub fn is_int_scalar(&self) -> bool {
        self.var_type() == VarType::Scalar && self.is_integer_element()
    }
    pub fn is_set(&self) -> bool {
        self.var_type() == VarType::Set
    }
    pub fn is_mesh_element_set(&self) -> bool {
        self.is_vertex_set() || self.is_edge_set() || self.is_face_set() || self.is_tet_set()
    }
    pub fn is_vertex_type(&self) -> bool {
        self.is_scalar() && self.cur_type() == SetKind::Vertex
    }
    pub fn is_edge_type(&self) -> bool {
        self.is_scalar() && self.cur_type() == SetKind::Edge
    }
    pub fn is_face_type(&self) -> bool {
        self.is_scalar() && self.cur_type() == SetKind::Face
    }
    pub fn is_tet_type(&self) -> bool {
        self.is_scalar() && self.cur_type() == SetKind::Tet
    }
    pub fn is_vertex_set(&self) -> bool {
        self.is_set() && self.cur_type() == SetKind::Vertex
    }
    pub fn is_edge_set(&self) -> bool {
        self.is_set() && self.cur_type() == SetKind::Edge
    }
    pub fn is_face_set(&self) -> bool {
        self.is_set() && self.cur_type() == SetKind::Face
    }
    pub fn is_tet_set(&self) -> bool {
        self.is_set() && self.cur_type() == SetKind::Tet
    }
    pub fn is_mesh_ele_set(&self) -> bool {
        self.is_set() && self.cur_type() != SetKind::Default
    }
    pub fn is_tuple(&self) -> bool {
        self.var_type() == VarType::Tuple
    }
    pub fn is_function(&self) -> bool {
        matches!(self.var_type(), VarType::Function | VarType::OverloadingFunction)
    }
    pub fn is_overloaded(&self) -> bool {
        self.var_type() == VarType::OverloadingFunction
    }
    pub fn is_mesh(&self) -> bool {
        self.var_type() == VarType::Mesh
    }
    pub fn is_dynamic(&self) -> bool {
        if self.class() == Class::Sequence {
            return self.elem().is_dynamic();
        }
        self.dynamic() != DYN_INVALID
    }
    pub fn is_dynamic_row(&self) -> bool {
        self.dynamic() & DYN_ROW != 0
    }
    pub fn is_dynamic_col(&self) -> bool {
        self.dynamic() & DYN_COL != 0
    }
    pub fn is_dynamic_dim(&self) -> bool {
        self.dynamic() & DYN_DIM != 0
    }
    pub fn set_dynamic_type(&self, d: u8) {
        self.set(|t| t.dynamic = d);
    }
    pub fn add_dynamic_type(&self, d: u8) {
        self.set(|t| if d == DYN_INVALID { t.dynamic = d } else { t.dynamic |= d });
    }

    /// `is_integer_element()`
    pub fn is_integer_element(&self) -> bool {
        match self.class() {
            Class::Scalar | Class::Int | Class::Vertex | Class::Edge | Class::Face | Class::Tet => self.is_int(),
            Class::Sequence | Class::Matrix | Class::Vector => self.elem().is_integer_element(),
            Class::Set | Class::VertexSet | Class::EdgeSet | Class::FaceSet | Class::TetSet => {
                let tl = self.type_list();
                if !tl.is_empty() {
                    return tl.iter().all(|t| t.is_integer_element());
                }
                self.int_list().iter().all(|b| *b)
            }
            Class::Tuple | Class::SimplicialSet => self.type_list().iter().all(|t| t.is_integer_element()),
            _ => false,
        }
    }

    /// `set_int(value)`
    pub fn set_int(&self, value: bool) {
        match self.element_type() {
            Some(e) => e.set_int(value),
            None => self.set(|t| t.is_int = value),
        }
    }

    pub fn contains_single_int(&self) -> bool {
        let tl = self.type_list();
        tl.len() == 1 && tl[0].is_int_scalar()
    }

    /// `ret_template()`
    pub fn ret_template(&self) -> bool {
        !self.ret_symbols().is_empty()
    }

    /// `get_dim_size(dim_index)`
    pub fn get_dim_size(&self, dim_index: usize) -> Dim {
        match self.var_type() {
            VarType::Sequence => {
                if dim_index == 0 {
                    self.size()
                } else {
                    self.elem().get_dim_size(dim_index - 1)
                }
            }
            VarType::Matrix => {
                if dim_index == 0 {
                    self.rows()
                } else {
                    self.cols()
                }
            }
            VarType::Vector => {
                if dim_index == 0 {
                    self.rows()
                } else {
                    Dim::Int(0)
                }
            }
            _ => Dim::Int(0),
        }
    }

    /// `is_dim_constant()`
    pub fn is_dim_constant(&self) -> bool {
        match self.var_type() {
            VarType::Sequence => self.size().is_int(),
            VarType::Matrix => self.rows().is_int() && self.cols().is_int(),
            VarType::Vector => self.rows().is_int(),
            _ => true,
        }
    }

    /// `is_same_type(other, omit_size)`
    pub fn is_same_type(&self, other: &T, omit_size: bool) -> bool {
        if self.var_type() != other.var_type() {
            return false;
        }
        match self.var_type() {
            VarType::Sequence => {
                if omit_size {
                    self.elem().is_same_type(&other.elem(), false)
                } else {
                    self.size().py_eq(&other.size()) && self.elem().is_same_type(&other.elem(), false)
                }
            }
            VarType::Matrix => {
                if omit_size {
                    self.elem().is_same_type(&other.elem(), false)
                } else {
                    self.rows().py_eq(&other.rows())
                        && self.cols().py_eq(&other.cols())
                        && self.elem().is_same_type(&other.elem(), false)
                }
            }
            VarType::Vector => {
                if omit_size {
                    self.rows().py_eq(&other.rows()) && self.elem().is_same_type(&other.elem(), false)
                } else {
                    self.rows().py_eq(&other.rows())
                }
            }
            VarType::Set | VarType::Scalar => self.cur_type() == other.cur_type(),
            _ => true,
        }
    }

    // -- text ----------------------------------------------------------------

    fn elem_int_char(&self) -> &'static str {
        if self.elem().is_int() {
            "ℤ"
        } else {
            "ℝ"
        }
    }

    /// `get_raw_text()`
    pub fn get_raw_text(&self) -> String {
        match self.class() {
            Class::Scalar => (if self.is_int() { "ℤ" } else { "ℝ" }).into(),
            Class::Int => "ℤ".into(),
            Class::Vertex => "v:ℤ".into(),
            Class::Edge => "e:ℤ".into(),
            Class::Face => "f:ℤ".into(),
            Class::Tet => "t:ℤ".into(),
            Class::Mesh => format!("mesh({},{},{},{})", self.vi_size(), self.ei_size(), self.fi_size(), self.ti_size()),
            Class::Matrix => format!("{}^({}×{})", self.elem_int_char(), self.rows(), self.cols()),
            Class::Vector => format!("{}^{}", self.elem_int_char(), self.rows()),
            Class::Set | Class::VertexSet | Class::EdgeSet | Class::FaceSet | Class::TetSet => {
                let il = self.int_list();
                let all_true = il.iter().all(|b| *b);
                let all_false = il.iter().all(|b| !*b);
                if all_true || all_false {
                    format!("{{ ℤ^{} }}", self.size())
                } else {
                    let parts: Vec<&str> = il.iter().map(|b| if *b { "ℤ" } else { "ℝ" }).collect();
                    format!("{{ {} }}", parts.join("×"))
                }
            }
            _ => String::new(),
        }
    }

    /// `get_signature()`
    pub fn get_signature(&self) -> String {
        match self.class() {
            Class::Scalar | Class::Int | Class::Vertex | Class::Edge | Class::Face | Class::Tet => self.get_raw_text(),
            Class::Mesh => self.get_raw_text(),
            Class::Sequence => format!("sequence of {}", self.elem().get_signature()),
            Class::Matrix => format!("{}^({}×{})", self.elem().get_signature(), self.rows(), self.cols()),
            Class::Vector => format!("{}^{}", self.elem().get_signature(), self.rows()),
            Class::Set => self.get_raw_text(),
            Class::VertexSet => format!("vertexset:{}", list_sig(&self.type_list())),
            Class::EdgeSet => format!("edgeset:{}", list_sig(&self.type_list())),
            Class::FaceSet => format!("faceset:{}", list_sig(&self.type_list())),
            Class::TetSet => format!("tetset:{}", list_sig(&self.type_list())),
            Class::Tuple | Class::SimplicialSet => format!("tuple:{}", list_sig(&self.type_list())),
            Class::Function => {
                let rets: Vec<String> = self.ret().iter().map(|r| r.get_signature()).collect();
                format!("{} → {}", get_list_signature(&self.params(), false), rets.join(","))
            }
            Class::Overloading => {
                let fl = self.func_list();
                let sigs: Vec<String> = fl.iter().map(|f| f.get_signature()).collect();
                format!("overloadingfunc,size:{},\n{}", fl.len(), sigs.join("\n"))
            }
            _ => String::new(),
        }
    }

    /// `get_relaxed_signature()`
    pub fn get_relaxed_signature(&self) -> String {
        match self.class() {
            Class::Mesh => "mesh()".into(),
            Class::Matrix => format!("{}^(×)", self.elem().get_signature()),
            Class::Vector => format!("{}^", self.elem().get_signature()),
            _ => self.get_signature(),
        }
    }

    /// `get_cpp_signature()`
    pub fn get_cpp_signature(&self) -> String {
        match self.class() {
            Class::Vertex | Class::Edge | Class::Face | Class::Tet => "ℤ".into(),
            Class::VertexSet | Class::EdgeSet | Class::FaceSet | Class::TetSet => self.get_raw_text(),
            Class::Matrix => {
                let e = self.elem_int_char();
                if self.cols().py_eq(&Dim::Int(1)) {
                    format!("{}^{}", e, self.rows())
                } else {
                    format!("{}^({}×{})", e, self.rows(), self.cols())
                }
            }
            Class::Vector => format!("{}^{}", self.elem_int_char(), self.rows()),
            _ => self.get_signature(),
        }
    }

    /// `FunctionType.get_overloading_signature()` (= parameter signature)
    pub fn get_overloading_signature(&self) -> String {
        self.get_param_signature(false)
    }

    pub fn get_param_signature(&self, cpp: bool) -> String {
        get_list_signature(&self.params(), cpp)
    }

    pub fn get_param_relaxed_signature(&self, cpp: bool) -> String {
        get_list_relaxed_signature(&self.params(), cpp)
    }

    /// `FunctionType.same_as(target)`
    pub fn same_as(&self, target: &T) -> bool {
        target.is_function() && self.get_signature() == target.get_signature()
    }

    /// `get_json_content()`
    pub fn get_json_content(&self) -> String {
        let py_bool = crate::helper::py_bool;
        match self.class() {
            Class::Scalar | Class::Int | Class::Vertex | Class::Edge | Class::Face | Class::Tet => {
                format!("{{\"type\": \"scalar\", \"is_int\":\"{}\"}}", py_bool(self.is_integer_element()))
            }
            Class::Sequence => format!(
                "{{\"type\": \"sequence\", \"is_int\":\"{}\", \"element\":{}, \"size\":\"{}\"}}",
                py_bool(self.is_integer_element()),
                self.elem().get_json_content(),
                self.size()
            ),
            Class::Matrix => format!(
                "{{\"type\": \"matrix\", \"is_int\":\"{}\", \"element\":{}, \"rows\":\"{}\", \"cols\":\"{}\"}}",
                py_bool(self.is_integer_element()),
                self.elem().get_json_content(),
                self.rows(),
                self.cols()
            ),
            Class::Vector => format!(
                "{{\"type\": \"vector\", \"is_int\":\"{}\", \"element\":{}, \"rows\":\"{}\"}}",
                py_bool(self.is_integer_element()),
                self.elem().get_json_content(),
                self.rows()
            ),
            Class::Set | Class::VertexSet | Class::EdgeSet | Class::FaceSet | Class::TetSet => {
                let els: Vec<String> =
                    self.int_list().iter().map(|b| format!("\"{}\"", if *b { 1 } else { 0 })).collect();
                format!(
                    "{{\"type\": \"set\", \"is_int\":\"{}\", \"element\":[{}], \"size\":\"{}\"}}",
                    py_bool(self.is_integer_element()),
                    els.join(","),
                    self.size()
                )
            }
            Class::Function => {
                let p: Vec<String> = self.params().iter().map(|t| t.get_json_content()).collect();
                let r: Vec<String> = self.ret().iter().map(|t| t.get_json_content()).collect();
                format!("{{\"type\": \"function\", \"params\":[{}], \"ret\":[{}]}}", p.join(","), r.join(","))
            }
            _ => String::new(),
        }
    }

    // -- mutation helpers ----------------------------------------------------

    /// `replace_sym_dims(mapping_dict)`
    pub fn replace_sym_dims(&self, mapping: &HashMap<String, String>) {
        let class = self.class();
        if let Some(o) = self.owner() {
            if let Some(n) = mapping.get(&o) {
                self.set(|t| t.owner = Some(n.clone()));
            }
        }
        if let Some(e) = self.element_type() {
            e.replace_sym_dims(mapping);
        }
        match class {
            Class::Sequence => {
                // SequenceType replaces the element's dims a second time
                if let Some(e) = self.element_type() {
                    e.replace_sym_dims(mapping);
                }
            }
            Class::Matrix => {
                let map_dim = |d: &mut Dim| {
                    if let Dim::Str(s) = d {
                        if let Some(n) = mapping.get(s) {
                            *d = Dim::Str(n.clone());
                        }
                    }
                };
                self.set(|t| {
                    map_dim(&mut t.rows);
                    map_dim(&mut t.cols);
                });
            }
            Class::Vector => {
                self.set(|t| {
                    if let Dim::Str(s) = &t.rows {
                        if let Some(n) = mapping.get(s) {
                            t.rows = Dim::Str(n.clone());
                        }
                    }
                });
            }
            Class::Function => {
                for p in self.params() {
                    p.replace_sym_dims(mapping);
                }
                for r in self.ret() {
                    r.replace_sym_dims(mapping);
                }
            }
            Class::Overloading => {
                for f in self.func_list() {
                    f.replace_sym_dims(mapping);
                }
            }
            _ => {}
        }
    }

    /// `OverloadingFunctionType.get_correct_ftype(param_list, allow_omit)`
    pub fn get_correct_ftype(&self, param_list: &[T], allow_omit: bool) -> (Option<T>, bool) {
        let param_sig = get_list_signature(param_list, false);
        for f in self.func_list() {
            if param_sig == f.get_param_signature(false) {
                return (Some(f), false);
            }
        }
        if allow_omit {
            let param_sig = get_list_relaxed_signature(param_list, false);
            for f in self.func_list() {
                if param_sig == f.get_param_relaxed_signature(false) {
                    return (Some(f), true);
                }
            }
            return (None, true);
        }
        (None, false)
    }

    /// `OverloadingFunctionType.add_new_type(f_type)`
    pub fn add_new_type(&self, f_type: T) -> bool {
        let (found, _) = self.get_correct_ftype(&f_type.params(), false);
        if found.is_none() {
            self.set(|t| t.func_list.push(f_type));
            true
        } else {
            false
        }
    }

    /// `has_duplicate_cpp_types()`
    pub fn has_duplicate_cpp_types(&self) -> bool {
        let mut seen: Vec<String> = Vec::new();
        for f in self.func_list() {
            let s = f.get_param_signature(true);
            if seen.contains(&s) {
                return true;
            }
            seen.push(s);
        }
        false
    }

    /// `MeshType.init_dims(dim_dict)`
    pub fn init_mesh_dims(&self, vi: Dim, ei: Dim, fi: Dim, ti: Dim) {
        self.set(|t| {
            t.vi_size = vi;
            t.ei_size = ei;
            t.fi_size = fi;
            t.ti_size = ti;
        });
    }

    // -- copying -------------------------------------------------------------

    /// `copy.deepcopy(t)`
    pub fn deep_copy(&self) -> T {
        let mut memo = DeepCopyMemo::default();
        self.deep_copy_memo(&mut memo)
    }

    /// `copy.deepcopy` with a shared memo (one Python `deepcopy` call).
    pub fn deep_copy_memo(&self, memo: &mut DeepCopyMemo) -> T {
        let key = Rc::as_ptr(&self.0) as usize;
        if let Some(t) = memo.types.get(&key) {
            return t.clone();
        }
        let copy = T::new(LaType::default());
        memo.types.insert(key, copy.clone());
        let src = self.0.borrow().clone();
        let c = |t: &Option<T>, memo: &mut DeepCopyMemo| t.as_ref().map(|t| t.deep_copy_memo(memo));
        let cl = |v: &Vec<T>, memo: &mut DeepCopyMemo| v.iter().map(|t| t.deep_copy_memo(memo)).collect::<Vec<_>>();
        let mut new = src.clone();
        new.element_type = c(&src.element_type, memo);
        new.type_list = cl(&src.type_list, memo);
        new.params = cl(&src.params, memo);
        new.ret = cl(&src.ret, memo);
        new.func_list = cl(&src.func_list, memo);
        new.dst = c(&src.dst, memo);
        // MatrixType/VectorType.__deepcopy__ keep item_types, rows_ir, cols_ir
        // shared; other classes would deep-copy them, but they are only set on
        // matrices and vectors.
        *copy.0.borrow_mut() = new;
        copy
    }
}

/// Memo for `deep_copy_memo` (Python's deepcopy memo dict).
#[derive(Default)]
pub struct DeepCopyMemo {
    types: HashMap<usize, T>,
}

fn list_sig(v: &[T]) -> String {
    v.iter().map(|t| t.get_signature()).collect::<Vec<_>>().join(",")
}

/// `get_list_signature(param_list, cpp)`
pub fn get_list_signature(param_list: &[T], cpp: bool) -> String {
    param_list
        .iter()
        .map(|p| if cpp { p.get_cpp_signature() } else { p.get_signature() })
        .collect::<Vec<_>>()
        .join(",")
}

/// `get_list_relatex_signature(param_list, cpp)`
pub fn get_list_relaxed_signature(param_list: &[T], cpp: bool) -> String {
    param_list
        .iter()
        .map(|p| if cpp { p.get_cpp_signature() } else { p.get_relaxed_signature() })
        .collect::<Vec<_>>()
        .join(",")
}

/// `get_func_signature(name, la_type)`
pub fn get_func_signature(name: &str, la_type: &T) -> String {
    format!("{} = {}", name, la_type.get_overloading_signature())
}

/// `TypeInferenceEnum`
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum TypeInference {
    Add,
    Sub,
    Mul,
    Div,
    MatrixRow,
}

/// `get_op_desc(op)`
pub fn get_op_desc(op: TypeInference) -> &'static str {
    match op {
        TypeInference::Add => "add",
        TypeInference::Sub => "subtract",
        TypeInference::Mul => "multiply",
        TypeInference::Div => "divide",
        TypeInference::MatrixRow => "place",
    }
}

/// `get_type_desc(la_type)`
pub fn get_type_desc(t: &T) -> String {
    if t.is_sequence() {
        "sequence".into()
    } else if t.is_matrix() {
        let mut dim = format!("{}, {}", t.rows(), t.cols());
        if t.is_dynamic() {
            if t.is_dynamic_row() && t.is_dynamic_col() {
                dim = "*,*".into();
            } else if t.is_dynamic_row() {
                dim = format!("*,{}", t.cols());
            } else if t.is_dynamic_col() {
                dim = format!("{},*", t.rows());
            }
        }
        format!("matrix({dim})")
    } else if t.is_vector() {
        let dim = if t.is_dynamic_row() { "*".to_string() } else { t.rows().to_string() };
        format!("vector({dim})")
    } else if t.is_scalar() {
        "scalar".into()
    } else if t.is_set() {
        "set".into()
    } else if t.is_function() {
        "function".into()
    } else {
        "NoneType".into()
    }
}

/// `get_derivative_type(upper_type, lower_type)`
pub fn get_derivative_type(upper: &T, lower: &T) -> T {
    let mut ret = T::scalar();
    if upper.is_scalar() {
        if lower.is_scalar() {
            ret = T::scalar();
        } else if lower.is_vector() {
            ret = T::vector(lower.rows());
        } else if lower.is_matrix() {
            ret = T::vector(mul_dims(&lower.rows(), &lower.cols()));
        } else if lower.is_sequence() {
            if lower.elem().is_scalar() {
                ret = T::vector(lower.size());
            } else if lower.elem().is_vector() {
                ret = T::vector(mul_dims(&lower.size(), &lower.elem().rows()));
            }
        }
    } else if upper.is_vector() {
        if lower.is_scalar() {
            ret = T::vector(lower.rows());
        } else if lower.is_vector() {
            ret = T::matrix(upper.rows(), lower.rows());
        } else if lower.is_sequence() && lower.elem().is_scalar() {
            ret = T::matrix(upper.rows(), lower.size());
        }
    } else if upper.is_matrix() {
        if lower.is_scalar() {
            ret = T::matrix(upper.rows(), upper.cols());
        }
    } else if upper.is_sequence() {
        if upper.elem().is_scalar() {
            if lower.is_scalar() {
                ret = T::vector(upper.size());
            } else if lower.is_vector() {
                ret = T::matrix(upper.size(), lower.rows());
            } else if lower.is_sequence() && lower.elem().is_scalar() {
                ret = T::matrix(upper.size(), lower.size());
            }
        } else if upper.elem().is_vector() {
            ret = T::matrix(upper.size(), upper.elem().rows());
        }
    }
    ret
}

/// `get_hessian_type(upper_type, lower_type)`
pub fn get_hessian_type(upper: &T, lower: &T) -> T {
    let mut ret = T::scalar();
    if upper.is_scalar() {
        if lower.is_vector() {
            ret = T::matrix_with(lower.rows(), lower.rows(), Some(T::scalar()));
        } else if lower.is_sequence() {
            ret = T::matrix(lower.size(), lower.size());
            if lower.elem().is_scalar() {
                ret = T::matrix(lower.size(), lower.size());
            } else if lower.elem().is_vector() {
                let size = mul_dims(&lower.size(), &lower.elem().rows());
                ret = T::matrix(size.clone(), size);
            }
        }
    }
    ret
}
