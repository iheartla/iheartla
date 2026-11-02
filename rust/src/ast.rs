//! The typed program that the checker produces and the backends consume.
//!
//! Every expression carries its type. Names are I❤LA names (backends make
//! them valid in their language). Subscripts are 1-based as in I❤LA.

use crate::dims::Dim;
use crate::ty::{Elem, MeshKind, Ty};

#[derive(Clone, Debug)]
pub struct Program {
    pub source: String,
    /// parameters, in declaration order (the generated constructor's order)
    pub params: Vec<Param>,
    /// dimension symbols and where to read them
    pub dims: Vec<DimSym>,
    /// equalities between dimensions (e.g. the extents a subscript ranges over)
    pub dim_checks: Vec<(Dim, Dim)>,
    /// the largest constant subscript into each dimension (`x₁₀` of `x ∈ ℝ^n`:
    /// n ≥ 10), for drawing random data that fits
    pub min_dims: Vec<(String, i64)>,
    /// statements in evaluation (def-use) order
    pub stmts: Vec<Stmt>,
    /// the symbol holding the result: the last statement's symbol
    pub ret: Option<String>,
    /// all symbols the program defines (outputs), with types
    pub defs: Vec<(String, Ty)>,
    /// the type of every checked expression, by byte span in `source`
    pub expr_types: std::collections::HashMap<(usize, usize), Ty>,
    /// the type of the indexed symbol of every indexing expression (`A_ij`), by span
    pub base_types: std::collections::HashMap<(usize, usize), Ty>,
    /// mesh parameters (`M ∈ FaceMesh`), in declaration order
    pub meshes: Vec<(String, MeshKind)>,
    /// imported modules (`VertexOneRing from Neighborhoods(M)`)
    pub modules: Vec<ModuleUse>,
    /// every function (local, parameter or imported) by name: the type and
    /// implementation name of each overload
    pub funcs: Vec<(String, Vec<(Ty, String)>)>,
}

/// A module imported by a program: compiled separately, instantiated with
/// the importer's arguments, its symbols copied into the importer.
#[derive(Clone, Debug)]
pub struct ModuleUse {
    pub name: String,
    pub prog: std::rc::Rc<Program>,
    /// the importer's arguments, one per module parameter
    pub args: Vec<String>,
    /// imported symbols: (name in the module, name in the importer), with one
    /// entry per overload for functions
    pub syms: Vec<(String, String)>,
}

#[derive(Clone, Debug)]
pub struct Param {
    pub name: String,
    pub ty: Ty,
    pub desc: Option<String>,
}

/// A dimension symbol read from the shape of a parameter: `name =
/// param.shape[axis]` (`axis` counts the sequence index first for sequences).
#[derive(Clone, Debug)]
pub struct DimSym {
    pub name: String,
    pub param: String,
    pub axis: usize,
}

#[derive(Clone, Debug)]
pub enum Stmt {
    /// `lhs = rhs`, `lhs_i = rhs` (a sequence/vector defined elementwise),
    /// `lhs_ij = rhs` (a matrix defined elementwise)
    Assign(Assign),
    /// `a, b = f(...)`: several results of one expression
    Multi { lhs: Vec<(String, Ty)>, rhs: Expr, text: String },
    /// a local function definition
    Func(LocalFunc),
}

#[derive(Clone, Debug)]
pub struct Assign {
    pub lhs: String,
    /// subscript variables of an elementwise definition
    pub subs: Vec<String>,
    /// the type of `lhs` (the whole sequence/vector/matrix when elementwise)
    pub ty: Ty,
    pub rhs: Expr,
    /// `+=`
    pub accumulate: bool,
    /// elementwise assignment into an existing matrix/vector
    pub update: bool,
    /// source text, for comments
    pub text: String,
    /// for elementwise definitions: the extent of each subscript
    pub extents: Vec<Dim>,
}

#[derive(Clone, Debug)]
pub struct LocalFunc {
    /// the implementation name (`f`, or `f_0`, `f_1`, ... for later overloads)
    pub name: String,
    /// the name as written
    pub base: String,
    /// parameters that must be elements of a set (`v ∈ V`): (parameter, set)
    pub checks: Vec<(String, String)>,
    pub params: Vec<(String, Ty)>,
    /// `where` assignments inside the function, in order
    pub body: Vec<Stmt>,
    pub expr: Expr,
    pub ty: Ty,
    pub text: String,
}

#[derive(Clone, Debug)]
pub struct Expr {
    pub kind: Box<ExprKind>,
    pub ty: Ty,
}

impl Expr {
    pub fn new(kind: ExprKind, ty: Ty) -> Expr {
        Expr { kind: Box::new(kind), ty }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Constant {
    Pi,
    E,
    Inf,
}

/// A subscript in an index expression.
#[derive(Clone, Debug)]
pub enum Idx {
    /// 1-based index
    At(Expr),
    /// `*`: a whole row or column
    All,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum NormKind {
    /// p-norm (2 by default) of a vector
    P,
    Frobenius,
    Nuclear,
    Max,
    /// |x| of a scalar
    Abs,
    /// |A| of a matrix
    Det,
    /// |S| of a set
    Size,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum CmpOp {
    Eq,
    Ne,
    Lt,
    Le,
    Gt,
    Ge,
}

#[derive(Clone, Debug)]
pub enum Cond {
    Cmp(CmpOp, Expr, Expr),
    In(Vec<Expr>, Expr),
    NotIn(Vec<Expr>, Expr),
    And(Box<Cond>, Box<Cond>),
    Or(Box<Cond>, Box<Cond>),
}

/// How a summation's index ranges.
#[derive(Clone, Debug)]
pub enum SumRange {
    /// over the extent of what the index subscripts (`∑_i x_i`)
    Implicit(Dim),
    /// `∑_(i=lo)^hi`
    Explicit(Expr, Expr),
    /// `∑_(i for cond)`: indices satisfying a condition, over the implicit extent
    Cond(Dim, Cond),
    /// `∑_(e ∈ S)` (`vars` has one variable per tuple component)
    Set(Expr),
}

#[derive(Clone, Debug)]
pub enum Callee {
    /// a builtin function (`sin`, `trace`, ...)
    Builtin(String),
    /// a local function, or a function-typed parameter
    Named(String),
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum OptKind {
    Min,
    Max,
    Argmin,
    Argmax,
}

#[derive(Clone, Debug)]
pub enum ExprKind {
    Int(i64),
    /// a real literal, as written
    Real(String),
    /// a fraction literal like ½
    Fraction(i64, i64),
    Const(Constant),
    Var(String),
    Index { base: String, base_ty: Ty, idx: Vec<Idx> },
    Neg(Expr),
    Add(Expr, Expr),
    Sub(Expr, Expr),
    /// scalar, matrix or matrix-vector product
    Mul(Expr, Expr),
    Div(Expr, Expr),
    Hadamard(Expr, Expr),
    Kronecker(Expr, Expr),
    Cross(Expr, Expr),
    /// `u ⋅ v` for vectors
    Dot(Expr, Expr),
    /// `⟨u, v⟩`, optionally with a metric matrix
    Inner(Expr, Expr, Option<Expr>),
    /// `A : B`
    Frobenius(Expr, Expr),
    /// scalar power, or matrix power (square matrix, scalar exponent)
    Pow(Expr, Expr),
    Transpose(Expr),
    Inverse(Expr),
    PseudoInverse(Expr),
    /// `A \ b`
    Solve(Expr, Expr),
    Sqrt(Expr),
    Norm { arg: Expr, kind: NormKind, p: Option<Expr> },
    Call { callee: Callee, args: Vec<Expr> },
    /// a (block) matrix: rows of items (scalars, vectors, matrices)
    Block(Vec<Vec<Expr>>),
    /// `(a, b, c)`: a column vector stacked from scalars and vectors
    Stack(Vec<Expr>),
    /// `0_m,n`, `1_n`, `I_n`
    Filled { value: i64, rows: Dim, cols: Option<Dim> },
    Identity(Dim),
    Sum { var: Vec<String>, range: SumRange, body: Expr, extras: Vec<Stmt> },
    /// `{ e1 if c1, ..., e otherwise }`
    Piecewise { cases: Vec<(Cond, Expr)>, otherwise: Option<Expr> },
    Integral { var: String, lo: Expr, hi: Expr, body: Expr },
    /// (`texts`: each constraint as written, for error messages)
    Optimize { kind: OptKind, vars: Vec<(String, Ty)>, objective: Expr, constraints: Vec<Cond>, texts: Vec<String> },
    /// `{a, b}` or `{e for i ∈ S if c}`
    SetLit(Vec<Expr>),
    /// `#x`: size
    Size(Expr),
    /// a MeshConnectivity function
    MeshCall { func: MeshFunc, mesh: String, args: Vec<Expr> },
    /// `A ∪ B`, `A ∩ B`, `A - B` on sets
    SetOp(SetOpKind, Expr, Expr),
    /// `vertexset(S)`, `tuple(a, b)`, `CellularSet(V, E, F)`: a conversion
    /// that changes only the type
    Convert(Vec<Expr>),
    /// `∪_(i ∈ S) e`: the union of the sets `e` over the elements of `S`
    /// (each variable is the element's value, plus 1 for `index` values in
    /// 0-based backends: `one_based`)
    /// `∪_(x ∈ S) e` (`range` is `SumRange::Set`), `∪_i U_i` or `∪_(i=a)^b U_i`
    Union { vars: Vec<String>, range: SumRange, body: Expr, one_based: Vec<bool> },
    /// `{ e for x ∈ S if cond }`
    SetComp { vars: Vec<String>, range: Expr, cond: Option<Cond>, item: Expr },
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum MeshFunc {
    ElementSets,
    BoundaryMatrices,
    UnsignedBoundaryMatrices,
    NonZeros,
    /// the indicator vector of a set of elements of the given kind
    IndicatorVector(Elem),
    ValueSet,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SetOpKind {
    Union,
    Intersection,
    Difference,
}
