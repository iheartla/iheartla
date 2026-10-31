//! Builtin packages (la_tools/la_package.py): trigonometry, linearalgebra and
//! the MeshConnectivity helper, with the types of their functions.

use crate::dims::Dim;
use crate::ir::GPType;
use crate::types::{MeshKind, T};

pub const VI_SIZE: &str = "vi_size";
pub const EI_SIZE: &str = "ei_size";
pub const FI_SIZE: &str = "fi_size";
pub const TI_SIZE: &str = "ti_size";
pub const MESH_CLASS: &str = "TriangleMesh";
pub const MESH_HELPER: &str = "MeshConnectivity";
pub const EDGE_MESH: &str = "EdgeMesh";
pub const FACE_MESH: &str = "FaceMesh";
pub const CELL_MESH: &str = "CellMesh";

pub const NON_ZEROS: &str = "NonZeros";
pub const VALUE_SET: &str = "ValueSet";
pub const INDICATOR_VECTOR: &str = "IndicatorVector";
pub const CANONICAL_VERTEX_ORDERINGS: &str = "CanonicalVertexOrderings";
pub const MESH_SETS: &str = "ElementSets";
pub const BOUNDARY_MATRICES: &str = "BoundaryMatrices";
pub const UNSIGNED_BOUNDARY_MATRICES: &str = "UnsignedBoundaryMatrices";
pub const FACES_OF_EDGE: &str = "faces_of_edge";
pub const DIHEDRAL: &str = "dihedral";
pub const FACE_NORMAL: &str = "face_normal";
pub const GET_ADJACENT_VERTICES_V: &str = "get_adjacent_vertices_v";
pub const GET_INCIDENT_EDGES_V: &str = "get_incident_edges_v";
pub const GET_INCIDENT_FACES_V: &str = "get_incident_faces_v";
pub const GET_INCIDENT_VERTICES_E: &str = "get_incident_vertices_e";
pub const GET_INCIDENT_FACES_E: &str = "get_incident_faces_e";
pub const GET_DIAMOND_VERTICES_E: &str = "get_diamond_vertices_e";
pub const GET_DIAMOND_FACES_E: &str = "get_diamond_faces_e";
pub const GET_INCIDENT_VERTICES_F: &str = "get_incident_vertices_f";
pub const GET_INCIDENT_EDGES_F: &str = "get_incident_edges_f";
pub const GET_ADJACENT_FACES_F: &str = "get_adjacent_faces_f";
pub const VERTICES_TO_VECTOR: &str = "vertices_to_vector";
pub const EDGES_TO_VECTOR: &str = "edges_to_vector";
pub const FACES_TO_VECTOR: &str = "faces_to_vector";
pub const TETS_TO_VECTOR: &str = "tets_to_vector";
pub const VECTOR_TO_VERTICES: &str = "vector_to_vertices";
pub const VECTOR_TO_EDGES: &str = "vector_to_edges";
pub const VECTOR_TO_FACES: &str = "vector_to_faces";
pub const VERTEX_POSITIONS: &str = "vertex_positions";
pub const FACE_MATRIX: &str = "face_matrix";
pub const STAR: &str = "star";
pub const CLOSURE: &str = "closure";
pub const LINK: &str = "link";
pub const BOUNDARY: &str = "boundary";
pub const IS_COMPLEX: &str = "is_complex";
pub const IS_PURE_COMPLEX: &str = "is_pure_complex";
pub const GET_VERTICES_E: &str = "get_vertices_e";
pub const GET_VERTICES_F: &str = "get_vertices_f";
pub const GET_EDGES_F: &str = "get_edges_f";
pub const VERTICES: &str = "vertices";
pub const EDGES: &str = "edges";
pub const FACES: &str = "faces";
pub const TETS: &str = "tets";
pub const DIAMOND: &str = "diamond";
pub const VI: &str = "Vi";
pub const EI: &str = "Ei";
pub const FI: &str = "Fi";
pub const NEI: &str = "nEi";
pub const BM1: &str = "bm1";
pub const BM2: &str = "bm2";
pub const BM3: &str = "bm3";

pub const TRIGONOMETRY: &[&str] = &[
    "sin", "asin", "arcsin", "cos", "acos", "arccos", "tan", "atan", "arctan", "atan2", "sinh", "asinh", "arsinh",
    "cosh", "acosh", "arcosh", "tanh", "atanh", "artanh", "cot", "sec", "csc",
];
pub const LINEARALGEBRA: &[&str] =
    &["trace", "tr", "diag", "inversevec", "vec⁻¹", "vec", "det", "rank", "null", "orth", "inv", "svd"];
pub const MESH_HELPER_FUNCS: &[&str] =
    &[MESH_SETS, BOUNDARY_MATRICES, UNSIGNED_BOUNDARY_MATRICES, NON_ZEROS, INDICATOR_VECTOR, VALUE_SET];

/// `PACKAGES_FUNC_DICT`
pub fn package_funcs(pkg: &str) -> Option<&'static [&'static str]> {
    match pkg {
        "trigonometry" => Some(TRIGONOMETRY),
        "linearalgebra" => Some(LINEARALGEBRA),
        MESH_HELPER => Some(MESH_HELPER_FUNCS),
        _ => None,
    }
}

/// `PACKAGES_DICT` (functions plus symbols: trigonometry also exports `e`)
pub fn packages_dict(pkg: &str) -> Option<Vec<String>> {
    let mut v: Vec<String> = package_funcs(pkg)?.iter().map(|s| s.to_string()).collect();
    if pkg == "trigonometry" {
        v.push("e".into());
    }
    Some(v)
}

pub const CLASS_PACKAGES: &[&str] = &[MESH_HELPER];

/// `MESH_HELPER_FUNC_MAPPING`
pub fn mesh_helper_func_mapping(name: &str) -> Option<GPType> {
    Some(match name {
        MESH_SETS => GPType::MeshSets,
        BOUNDARY_MATRICES => GPType::BoundaryMatrices,
        UNSIGNED_BOUNDARY_MATRICES => GPType::UnsignedBoundaryMatrices,
        CANONICAL_VERTEX_ORDERINGS => GPType::CanonicalVertexOrderings,
        NON_ZEROS => GPType::NonZeros,
        VALUE_SET => GPType::ValueSet,
        INDICATOR_VECTOR => GPType::IndicatorVector,
        FACES_OF_EDGE => GPType::FacesOfEdge,
        FACE_NORMAL => GPType::FaceNormal,
        DIHEDRAL => GPType::Dihedral,
        GET_ADJACENT_VERTICES_V => GPType::AdjacentVerticesV,
        GET_INCIDENT_EDGES_V => GPType::IncidentEdgesV,
        GET_INCIDENT_FACES_V => GPType::IncidentFacesV,
        GET_INCIDENT_VERTICES_E => GPType::IncidentVerticesE,
        GET_INCIDENT_FACES_E => GPType::IncidentFacesE,
        GET_DIAMOND_VERTICES_E => GPType::DiamondVerticesE,
        GET_DIAMOND_FACES_E => GPType::DiamondFacesE,
        GET_INCIDENT_VERTICES_F => GPType::IncidentVerticesF,
        GET_INCIDENT_EDGES_F => GPType::IncidentEdgesF,
        GET_ADJACENT_FACES_F => GPType::AdjacentFacesF,
        VERTICES_TO_VECTOR => GPType::BuildVertexVector,
        EDGES_TO_VECTOR => GPType::BuildEdgeVector,
        FACES_TO_VECTOR => GPType::BuildFaceVector,
        VECTOR_TO_VERTICES => GPType::VectorToVertex,
        VECTOR_TO_EDGES => GPType::VectorToEdge,
        VECTOR_TO_FACES => GPType::VectorToFace,
        VERTEX_POSITIONS => GPType::VertexPositions,
        FACE_MATRIX => GPType::FaceMatrix,
        GET_VERTICES_E => GPType::GetVerticesE,
        GET_EDGES_F => GPType::GetEdgesF,
        GET_VERTICES_F => GPType::GetVerticesF,
        STAR => GPType::Star,
        CLOSURE => GPType::Closure,
        LINK => GPType::Link,
        BOUNDARY => GPType::Boundary,
        IS_COMPLEX => GPType::IsComplex,
        IS_PURE_COMPLEX => GPType::IsPureComplex,
        VERTICES => GPType::Vertices,
        EDGES => GPType::Edges,
        FACES => GPType::Faces,
        TETS => GPType::Tets,
        DIAMOND => GPType::Diamond,
        _ => return None,
    })
}

/// `MESH_HELPER_DYNAMIC_TYPE_LIST`
pub fn is_mesh_helper_dynamic(name: &str) -> bool {
    [
        BM1, BM2, BM3, VERTICES_TO_VECTOR, EDGES_TO_VECTOR, FACES_TO_VECTOR, VECTOR_TO_VERTICES, VECTOR_TO_EDGES,
        VECTOR_TO_FACES, VERTEX_POSITIONS, FACE_MATRIX, MESH_SETS, BOUNDARY_MATRICES, UNSIGNED_BOUNDARY_MATRICES,
        CANONICAL_VERTEX_ORDERINGS, INDICATOR_VECTOR,
    ]
    .contains(&name)
}

fn f(params: Vec<T>, ret: Vec<T>) -> T {
    T::function(params, ret)
}

fn n() -> Dim {
    Dim::None
}

fn sparse_int_matrix(rows: Dim, cols: Dim, owner: Option<String>) -> T {
    let m = T::matrix_with(rows, cols, Some(T::scalar_int(true)));
    m.set(|t| t.sparse = true);
    m.with_owner(owner)
}

fn indicator_overloads(sizes: Option<[Dim; 4]>, owner: Option<String>) -> T {
    let mk = |set: T, elem: T, rows: Dim| {
        let m = T::matrix_with(rows, Dim::Int(1), Some(elem));
        m.set(|t| t.sparse = true);
        f(vec![set], vec![m.with_owner(owner.clone())])
    };
    let [v, e, fa, t] = sizes.unwrap_or([Dim::Int(0), Dim::Int(0), Dim::Int(0), Dim::Int(0)]);
    T::overloading(
        vec![
            mk(T::vertex_set(n(), None), T::vertex(None), v),
            mk(T::edge_set(n(), None), T::edge(None), e),
            mk(T::face_set(n(), None), T::face(None), fa),
            mk(T::tet_set(n(), None), T::tet(None), t),
        ],
        Some((0..4).map(|i| format!("{INDICATOR_VECTOR}_{i}")).collect()),
    )
}

/// `MESH_HELPER_SYM_TYPE[sym]`: a fresh copy of the static type (Python
/// shares one object per name; nothing mutates these in place before they
/// are copied into a symbol table).
pub fn mesh_helper_sym_type(sym: &str) -> Option<T> {
    let mesh = || T::mesh(MeshKind::Triangle);
    let int_set = || T::set_type(1, vec![true], vec![T::scalar_int(true)], None);
    Some(match sym {
        MESH_SETS => f(vec![mesh()], vec![T::vertex_set(n(), None), T::edge_set(n(), None), T::face_set(n(), None)]),
        BOUNDARY_MATRICES | UNSIGNED_BOUNDARY_MATRICES | CANONICAL_VERTEX_ORDERINGS => {
            f(vec![mesh()], vec![T::matrix(0, 0), T::matrix(0, 0)])
        }
        NON_ZEROS => f(vec![T::matrix_with(Dim::Int(0), Dim::Int(0), Some(T::scalar_int(true)))], vec![int_set()]),
        VALUE_SET => f(
            vec![T::matrix_with(Dim::Int(0), Dim::Int(0), Some(T::scalar_int(true))), T::scalar_int(true)],
            vec![int_set()],
        ),
        INDICATOR_VECTOR => {
            let t = indicator_overloads(None, None);
            for ft in t.func_list() {
                ft.ret()[0].set(|m| m.rows = Dim::Int(0));
            }
            t
        }
        FACES_OF_EDGE => f(vec![mesh(), T::edge(None)], vec![T::face_set(n(), None)]),
        FACE_NORMAL | DIHEDRAL | VERTICES_TO_VECTOR | EDGES_TO_VECTOR | FACES_TO_VECTOR | VECTOR_TO_VERTICES
        | VECTOR_TO_EDGES | VECTOR_TO_FACES | VERTEX_POSITIONS | FACE_MATRIX => f(vec![], vec![]),
        GET_ADJACENT_VERTICES_V => f(vec![mesh(), T::vertex(None)], vec![T::vertex_set(n(), None)]),
        GET_INCIDENT_EDGES_V => f(vec![mesh(), T::vertex(None)], vec![T::edge_set(n(), None)]),
        GET_INCIDENT_FACES_V => f(vec![mesh(), T::vertex(None)], vec![T::face_set(n(), None)]),
        GET_INCIDENT_VERTICES_E => f(vec![mesh(), T::edge(None)], vec![T::vertex_set(n(), None)]),
        GET_INCIDENT_FACES_E => f(vec![mesh(), T::edge(None)], vec![T::face_set(n(), None)]),
        GET_DIAMOND_VERTICES_E => f(vec![mesh(), T::edge(None)], vec![T::vertex_set(n(), None)]),
        GET_DIAMOND_FACES_E => f(vec![mesh(), T::edge(None)], vec![T::face(None), T::face(None)]),
        GET_INCIDENT_VERTICES_F => f(vec![mesh(), T::face(None)], vec![T::vertex_set(n(), None)]),
        GET_INCIDENT_EDGES_F => f(vec![mesh(), T::face(None)], vec![T::edge_set(n(), None)]),
        GET_ADJACENT_FACES_F => f(vec![mesh(), T::face(None)], vec![T::face_set(n(), None)]),
        GET_VERTICES_E => f(vec![mesh(), T::edge(None)], vec![T::vertex(None), T::vertex(None)]),
        GET_EDGES_F => f(vec![mesh(), T::face(None)], vec![T::edge(None), T::edge(None), T::edge(None)]),
        GET_VERTICES_F => f(vec![mesh(), T::face(None)], vec![T::vertex(None), T::vertex(None), T::vertex(None)]),
        STAR | CLOSURE | LINK | BOUNDARY => f(vec![mesh(), T::simplicial_set()], vec![T::simplicial_set()]),
        IS_COMPLEX | IS_PURE_COMPLEX => f(vec![mesh(), T::simplicial_set()], vec![T::int_type()]),
        VERTICES => f(vec![mesh(), T::simplicial_set()], vec![T::vertex_set(n(), None)]),
        EDGES => f(vec![mesh(), T::simplicial_set()], vec![T::edge_set(n(), None)]),
        FACES => f(vec![mesh(), T::simplicial_set()], vec![T::face_set(n(), None)]),
        TETS => f(vec![mesh(), T::simplicial_set()], vec![T::tet_set(n(), None)]),
        DIAMOND => f(vec![mesh(), T::edge(None)], vec![T::simplicial_set()]),
        VI => T::vertex_set(n(), None),
        EI | NEI => T::edge_set(n(), None),
        FI => T::face_set(n(), None),
        BM1 | BM2 | BM3 => return Some(T::invalid()),
        _ => return None,
    })
}

/// `get_sym_type_from_pkg(sym, pkg, mesh_type)`
pub fn get_sym_type_from_pkg(sym: &str, pkg: &str, mesh_type: Option<&T>) -> T {
    if pkg != MESH_HELPER {
        return T::invalid();
    }
    let Some(static_type) = mesh_helper_sym_type(sym) else {
        return T::invalid();
    };
    let Some(mt) = mesh_type.filter(|_| is_mesh_helper_dynamic(sym)) else {
        return static_type;
    };
    let (vi, ei, fi, ti) = (mt.vi_size(), mt.ei_size(), mt.fi_size(), mt.ti_size());
    let owner = mt.owner();
    let mesh = || T::mesh(MeshKind::Triangle);
    match sym {
        BM1 => sparse_int_matrix(vi, ei, owner),
        BM2 => sparse_int_matrix(ei, fi, owner),
        BM3 => sparse_int_matrix(fi, ti, owner),
        VERTICES_TO_VECTOR => f(vec![mesh(), T::vertex_set(n(), None)], vec![T::vector(vi)]),
        EDGES_TO_VECTOR => f(vec![mesh(), T::edge_set(n(), None)], vec![T::vector(ei)]),
        FACES_TO_VECTOR => f(vec![mesh(), T::face_set(n(), None)], vec![T::vector(fi)]),
        VECTOR_TO_VERTICES => f(vec![mesh(), T::vector(vi)], vec![T::vertex_set(n(), None)]),
        VECTOR_TO_EDGES => f(vec![mesh(), T::vector(ei)], vec![T::edge_set(n(), None)]),
        VECTOR_TO_FACES => f(vec![mesh(), T::vector(fi)], vec![T::face_set(n(), None)]),
        VERTEX_POSITIONS => f(vec![mesh()], vec![T::matrix(vi, 3)]),
        FACE_MATRIX => f(vec![mesh()], vec![T::matrix(fi, 3)]),
        CANONICAL_VERTEX_ORDERINGS => f(
            vec![mesh()],
            vec![
                T::vector_with(vi, Some(T::vertex(None))),
                T::matrix_with(ei, Dim::Int(2), Some(T::edge(None))),
                T::matrix_with(fi, Dim::Int(3), Some(T::face(None))),
            ],
        ),
        INDICATOR_VECTOR => indicator_overloads(Some([vi, ei, fi, ti]), owner),
        MESH_SETS => match mt.cur_mesh() {
            MeshKind::FaceMesh => f(
                vec![mesh()],
                vec![T::vertex_set(vi, owner.clone()), T::edge_set(ei, owner.clone()), T::face_set(fi, owner)],
            ),
            MeshKind::CellMesh => f(
                vec![mesh()],
                vec![
                    T::vertex_set(vi, owner.clone()),
                    T::edge_set(ei, owner.clone()),
                    T::face_set(fi, owner.clone()),
                    T::tet_set(ti, owner),
                ],
            ),
            MeshKind::EdgeMesh => f(vec![mesh()], vec![T::vertex_set(vi, owner.clone()), T::edge_set(ei, owner)]),
            _ => T::invalid(),
        },
        BOUNDARY_MATRICES | UNSIGNED_BOUNDARY_MATRICES => match mt.cur_mesh() {
            MeshKind::FaceMesh => f(
                vec![mesh()],
                vec![sparse_int_matrix(vi, ei.clone(), owner.clone()), sparse_int_matrix(ei, fi, owner)],
            ),
            MeshKind::CellMesh => f(
                vec![mesh()],
                vec![
                    sparse_int_matrix(vi, ei.clone(), owner.clone()),
                    sparse_int_matrix(ei, fi.clone(), owner.clone()),
                    sparse_int_matrix(fi, ti, owner),
                ],
            ),
            MeshKind::EdgeMesh => f(vec![mesh()], vec![sparse_int_matrix(vi, ei, owner)]),
            _ => T::invalid(),
        },
        _ => static_type,
    }
}

/// Backend: the three code generators with their own builtin names.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum Backend {
    Latex,
    Numpy,
    Eigen,
    Matlab,
    Mathjax,
    MacroMathjax,
}

impl Backend {
    pub const ALL: [Backend; 6] =
        [Backend::Numpy, Backend::Eigen, Backend::Latex, Backend::Mathjax, Backend::Matlab, Backend::MacroMathjax];

    pub fn name(&self) -> &'static str {
        match self {
            Backend::Latex => "latex",
            Backend::Numpy => "numpy",
            Backend::Eigen => "eigen",
            Backend::Matlab => "matlab",
            Backend::Mathjax => "mathjax",
            Backend::MacroMathjax => "macromathjax",
        }
    }

    pub fn from_name(s: &str) -> Option<Backend> {
        Backend::ALL.iter().copied().find(|b| b.name() == s)
    }
}

/// `BACKEND_OVERLOADING_DICT[backend].get(name, name)`
pub fn backend_overloading_name(backend: Backend, name: &str) -> String {
    let nz = match backend {
        Backend::Eigen | Backend::Numpy => "nonzeros",
        Backend::Matlab => "NonZeros",
        _ => return name.to_string(),
    };
    if name == NON_ZEROS {
        return nz.into();
    }
    if backend == Backend::Eigen && name == VALUE_SET {
        return VALUE_SET.into();
    }
    match name {
        "IndicatorVector_0" => VERTICES_TO_VECTOR.into(),
        "IndicatorVector_1" => EDGES_TO_VECTOR.into(),
        "IndicatorVector_2" => FACES_TO_VECTOR.into(),
        "IndicatorVector_3" => TETS_TO_VECTOR.into(),
        _ => name.to_string(),
    }
}

/// `get_gp_func_impl(name, la_type)`: builtin geometry functions for Eigen.
pub fn get_gp_func_impl(name: &str, backend: Backend) -> &'static str {
    if backend != Backend::Eigen {
        return "";
    }
    match name {
        FACES_OF_EDGE => "std::tuple< int, int > faces_of_edge(int i, int j){\n    std::tuple< int, int > ret;\n    return ret;\n}\n",
        FACE_NORMAL => "int face_normal(int i, int j){\n    return 0;\n}\n",
        DIHEDRAL => "double dihedral(int i, int j, int k, int l){\n    return 0;\n}\n",
        _ => "",
    }
}
