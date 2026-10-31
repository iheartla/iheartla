//! The typed program that the checker produces and the backends consume.
//!
//! Every expression carries its type. Names are I❤LA names (backends make
//! them valid in their language). Subscripts are 1-based as in I❤LA.

use crate::dims::Dim;
use crate::ty::Ty;

#[derive(Clone, Debug)]
pub struct Program {
    pub source: String,
    /// parameters, in declaration order (the generated constructor's order)
    pub params: Vec<Param>,
    /// dimension symbols and where to read them
    pub dims: Vec<DimSym>,
    /// equalities between dimensions to check at run time (e.g. a dimension
    /// used by two parameters)
    pub dim_checks: Vec<(Dim, Dim)>,
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
    pub name: String,
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
    /// an item of a sequence of functions `f_i(x)`
    SeqItem(String, Expr),
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
    Optimize { kind: OptKind, vars: Vec<(String, Ty)>, objective: Expr, constraints: Vec<Cond> },
    /// `{a, b}` or `{e for i ∈ S if c}`
    SetLit(Vec<Expr>),
    /// `#x`: size
    Size(Expr),
}
