//! I❤LA types. Unlike the Python compiler's mutable type objects, these are
//! plain values: an expression's type is computed once and never changes.

use crate::dims::{is_same_expr, Dim};
use std::fmt;

/// The element kind of a scalar: a number, or an index of a mesh element.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub enum Elem {
    #[default]
    Real,
    Int,
    Vertex,
    Edge,
    Face,
    Tet,
    /// an index stored 0-based (the `index` attribute): 1-based as a subscript
    Index,
}

impl Elem {
    pub fn is_int(self) -> bool {
        self != Elem::Real
    }
    /// A vertex, edge, face or tetrahedron (an index into a mesh's elements).
    pub fn is_mesh_element(self) -> bool {
        matches!(self, Elem::Vertex | Elem::Edge | Elem::Face | Elem::Tet)
    }
    /// Stored 0-based (an `index` value or a mesh element): used as a
    /// subscript without subtracting 1.
    pub fn is_zero_based(self) -> bool {
        self == Elem::Index || self.is_mesh_element()
    }
    pub fn of(int: bool) -> Elem {
        if int {
            Elem::Int
        } else {
            Elem::Real
        }
    }
    /// Arithmetic on two elements: integer only if both are.
    pub fn join(self, other: Elem) -> Elem {
        Elem::of(self.is_int() && other.is_int())
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum MeshKind {
    Edge,
    Face,
    Cell,
}

#[derive(Clone, Debug, PartialEq)]
pub enum Ty {
    Scalar(Elem),
    /// a column vector
    Vector { rows: Dim, elem: Elem },
    Matrix { rows: Dim, cols: Dim, elem: Elem, sparse: bool },
    /// a sequence `x_i`: `size` items of `elem` (the size of each item may
    /// vary: `dynamic`, e.g. `x_i ∈ ℝ^(n_i)`)
    Seq { size: Dim, elem: Box<Ty> },
    /// a set of tuples (one element type per tuple component), or of mesh
    /// elements
    Set { elems: Vec<Elem>, length: Dim },
    /// a set of vectors (`{x_v - p for v ∈ N}`), kept in increasing
    /// lexicographic order; its size is the dimension `@size:<name>`
    VecSet { rows: Dim, elem: Elem },
    Tuple(Vec<Ty>),
    Func { params: Vec<Ty>, rets: Vec<Ty> },
    Mesh(MeshKind),
}

pub use Ty::*;

impl Ty {
    pub fn real() -> Ty {
        Scalar(Elem::Real)
    }
    pub fn int() -> Ty {
        Scalar(Elem::Int)
    }
    pub fn vector(rows: impl Into<Dim>) -> Ty {
        Vector { rows: rows.into(), elem: Elem::Real }
    }
    pub fn matrix(rows: impl Into<Dim>, cols: impl Into<Dim>) -> Ty {
        Matrix { rows: rows.into(), cols: cols.into(), elem: Elem::Real, sparse: false }
    }

    pub fn is_scalar(&self) -> bool {
        matches!(self, Scalar(_))
    }
    pub fn is_vector(&self) -> bool {
        matches!(self, Vector { .. })
    }
    pub fn is_matrix(&self) -> bool {
        matches!(self, Matrix { .. })
    }
    pub fn is_seq(&self) -> bool {
        matches!(self, Seq { .. })
    }
    pub fn is_set(&self) -> bool {
        matches!(self, Set { .. })
    }
    pub fn is_func(&self) -> bool {
        matches!(self, Func { .. })
    }
    pub fn is_tuple(&self) -> bool {
        matches!(self, Tuple(_))
    }
    pub fn is_sparse(&self) -> bool {
        matches!(self, Matrix { sparse: true, .. })
    }

    /// The scalar element kind (of a scalar, vector or matrix).
    pub fn elem(&self) -> Elem {
        match self {
            Scalar(e) | Vector { elem: e, .. } | Matrix { elem: e, .. } => *e,
            Seq { elem, .. } => elem.elem(),
            Set { elems, .. } if elems.len() == 1 => elems[0],
            VecSet { elem, .. } => *elem,
            _ => Elem::Real,
        }
    }
    pub fn is_int(&self) -> bool {
        self.elem().is_int()
    }
    pub fn with_elem(&self, e: Elem) -> Ty {
        match self.clone() {
            Scalar(_) => Scalar(e),
            Vector { rows, .. } => Vector { rows, elem: e },
            Matrix { rows, cols, sparse, .. } => Matrix { rows, cols, elem: e, sparse },
            other => other,
        }
    }

    /// Rows of a vector or matrix (1 for scalars).
    pub fn rows(&self) -> Dim {
        match self {
            Vector { rows, .. } | Matrix { rows, .. } => rows.clone(),
            Scalar(_) => Dim::Int(1),
            Seq { size, .. } => size.clone(),
            _ => Dim::None,
        }
    }
    /// Columns of a matrix (1 for vectors and scalars).
    pub fn cols(&self) -> Dim {
        match self {
            Matrix { cols, .. } => cols.clone(),
            Vector { .. } | Scalar(_) => Dim::Int(1),
            _ => Dim::None,
        }
    }

    /// Structural equality of types with symbolic dimension comparison.
    pub fn same(&self, other: &Ty) -> bool {
        match (self, other) {
            (Scalar(a), Scalar(b)) => a.is_int() == b.is_int() || true,
            (Vector { rows: a, .. }, Vector { rows: b, .. }) => is_same_expr(a, b),
            (Matrix { rows: r1, cols: c1, .. }, Matrix { rows: r2, cols: c2, .. }) => {
                is_same_expr(r1, r2) && is_same_expr(c1, c2)
            }
            (Seq { size: a, elem: x }, Seq { size: b, elem: y }) => is_same_expr(a, b) && x.same(y),
            (Set { elems: a, .. }, Set { elems: b, .. }) => a.len() == b.len(),
            (VecSet { rows: a, .. }, VecSet { rows: b, .. }) => is_same_expr(a, b),
            (Tuple(a), Tuple(b)) => a.len() == b.len() && a.iter().zip(b).all(|(x, y)| x.same(y)),
            (Func { params: p1, rets: r1 }, Func { params: p2, rets: r2 }) => {
                p1.len() == p2.len() && r1.len() == r2.len()
            }
            (Mesh(a), Mesh(b)) => a == b,
            _ => false,
        }
    }

    /// A short description for error messages.
    pub fn desc(&self) -> String {
        match self {
            Scalar(_) => "scalar".into(),
            Vector { rows, .. } => format!("vector({rows})"),
            Matrix { rows, cols, .. } => format!("matrix({rows}, {cols})"),
            Seq { .. } => "sequence".into(),
            Set { .. } => "set".into(),
            VecSet { .. } => "set of vectors".into(),
            Tuple(_) => "tuple".into(),
            Func { .. } => "function".into(),
            Mesh(_) => "mesh".into(),
        }
    }
}

impl fmt::Display for Ty {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let e = |e: &Elem| if e.is_int() { "ℤ" } else { "ℝ" };
        match self {
            Scalar(x) => write!(f, "{}", e(x)),
            Vector { rows, elem } => write!(f, "{}^{}", e(elem), rows),
            Matrix { rows, cols, elem, .. } => write!(f, "{}^({}×{})", e(elem), rows, cols),
            Seq { size, elem } => write!(f, "sequence({size}) of {elem}"),
            Set { elems, .. } => write!(f, "{{{}}}", elems.iter().map(e).collect::<Vec<_>>().join("×")),
            VecSet { rows, elem } => write!(f, "{{{}^{}}}", e(elem), rows),
            Tuple(v) => write!(f, "({})", v.iter().map(|t| t.to_string()).collect::<Vec<_>>().join(", ")),
            Func { params, rets } => write!(
                f,
                "{} → {}",
                params.iter().map(|t| t.to_string()).collect::<Vec<_>>().join(", "),
                rets.iter().map(|t| t.to_string()).collect::<Vec<_>>().join(", ")
            ),
            Mesh(k) => write!(f, "{k:?}Mesh"),
        }
    }
}
