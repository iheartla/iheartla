import copy
from ..la_parser.la_types import *
class GPType(IntEnum):
    # Geometry processing
    Invalid = -1
    FacesOfEdge = 0
    Dihedral = 1
    FaceNormal = 2
    AdjacentVerticesV = 3
    IncidentEdgesV = 4
    IncidentFacesV = 5
    IncidentVerticesE = 6
    IncidentFacesE = 7
    DiamondVerticesE = 8
    IncidentVerticesF = 9
    IncidentEdgesF = 10
    AdjacentFacesF = 11
    BuildVertexVector = 12
    BuildEdgeVector = 13
    BuildFaceVector = 14
    GetVerticesE = 15
    GetVerticesF = 16
    GetEdgesF = 17
    Vertices = 18
    Edges = 19
    Faces = 20
    Tets = 21
    Diamond = 22
    DiamondFacesE = 23
    VectorToVertex = 24
    VectorToEdge = 25
    VectorToFace = 26
    # dec
    Star = 100
    Closure = 101
    Link = 102
    Boundary = 103
    IsComplex = 104
    IsPureComplex = 105

TRIANGLE_MESH = 'triangle_mesh'
# triangle_mesh function
FACES_OF_EDGE = 'faces_of_edge'
DIHEDRAL = 'dihedral'
FACE_NORMAL = 'face_normal'
GET_ADJACENT_VERTICES_V = 'get_adjacent_vertices_v'
GET_INCIDENT_EDGES_V = 'get_incident_edges_v'
GET_INCIDENT_FACES_V = 'get_incident_faces_v'
GET_INCIDENT_VERTICES_E = 'get_incident_vertices_e'
GET_INCIDENT_FACES_E = 'get_incident_faces_e'
GET_DIAMOND_VERTICES_E = 'get_diamond_vertices_e'
GET_DIAMOND_FACES_E = 'get_diamond_faces_e'
GET_INCIDENT_VERTICES_F = 'get_incident_vertices_f'
GET_INCIDENT_EDGES_F = 'get_incident_edges_f'
GET_ADJACENT_FACES_F = 'get_adjacent_faces_f'
BUILD_VERTEX_VECTOR = 'build_vertex_vector'
BUILD_EDGE_VECTOR = 'build_edge_vector'
BUILD_FACE_VECTOR = 'build_face_vector'
VECTOR_TO_VERTEX = 'vector_to_set'
VECTOR_TO_EDGE = 'vector_to_edge'
VECTOR_TO_FACE = 'vector_to_face'
STAR = 'star'
CLOSURE = 'closure'
LINK = 'link'
BOUNDARY = 'boundary'
IS_COMPLEX = 'is_complex'
IS_PURE_COMPLEX = 'is_pure_complex'
GET_VERTICES_E = 'get_vertices_e'
GET_VERTICES_F = 'get_vertices_f'
GET_EDGES_F = 'get_edges_f'
VERTICES = 'vertices'
EDGES = 'edges'
FACES = 'faces'
TETS = 'tets'
DIAMOND = 'diamond'

VI = 'Vi'
EI = 'Ei'
FI = 'Fi'
NEI = 'nEi'
BM1 = 'bm1'
BM2 = 'bm2'
BM3 = 'bm3'
PACKAGES_FUNC_DICT = {'trigonometry': ['sin', 'asin', 'arcsin', 'cos', 'acos', 'arccos', 'tan', 'atan', 'arctan', 'atan2',
                                  'sinh', 'asinh', 'arsinh', 'cosh', 'acosh', 'arcosh', 'tanh', 'atanh', 'artanh',
                                  'cot', 'sec', 'csc'],
                 'linearalgebra': ['trace', 'tr', 'diag', 'vec', 'det', 'rank', 'null', 'orth', 'inv'],
                 TRIANGLE_MESH: [FACES_OF_EDGE, FACE_NORMAL, DIHEDRAL,
                                 GET_ADJACENT_VERTICES_V, GET_INCIDENT_EDGES_V, GET_INCIDENT_FACES_V,
                                 GET_INCIDENT_VERTICES_E, GET_INCIDENT_FACES_E, GET_DIAMOND_VERTICES_E, GET_DIAMOND_FACES_E,
                                 GET_INCIDENT_VERTICES_F, GET_INCIDENT_EDGES_F, GET_ADJACENT_FACES_F,
                                 BUILD_VERTEX_VECTOR, BUILD_EDGE_VECTOR, BUILD_FACE_VECTOR,
                                 VECTOR_TO_VERTEX, VECTOR_TO_EDGE, VECTOR_TO_FACE,
                                 GET_VERTICES_E, GET_EDGES_F, GET_VERTICES_F,
                                 STAR, CLOSURE, LINK, BOUNDARY, IS_COMPLEX, IS_PURE_COMPLEX,
                                 VERTICES, EDGES, FACES, TETS, DIAMOND]}
PACKAGES_SYM_DICT = {'trigonometry': ['e'],
                 TRIANGLE_MESH: [EDGES, VI, EI, FI, NEI, BM1, BM2, BM3]}
TRIANGLE_MESH_FUNC_MAPPING = {
FACES_OF_EDGE: GPType.FacesOfEdge,
FACE_NORMAL: GPType.FaceNormal,
DIHEDRAL: GPType.Dihedral,
GET_ADJACENT_VERTICES_V: GPType.AdjacentVerticesV,  #
GET_INCIDENT_EDGES_V: GPType.IncidentEdgesV,  #
GET_INCIDENT_FACES_V: GPType.IncidentFacesV,  #
#
GET_INCIDENT_VERTICES_E: GPType.IncidentVerticesE,
GET_INCIDENT_FACES_E: GPType.IncidentFacesE,
GET_DIAMOND_VERTICES_E: GPType.DiamondVerticesE,
GET_DIAMOND_FACES_E: GPType.DiamondFacesE,
#
GET_INCIDENT_VERTICES_F: GPType.IncidentVerticesF,
GET_INCIDENT_EDGES_F: GPType.IncidentEdgesF,
GET_ADJACENT_FACES_F: GPType.AdjacentFacesF,
#
BUILD_VERTEX_VECTOR: GPType.BuildVertexVector,
BUILD_EDGE_VECTOR: GPType.BuildEdgeVector,
BUILD_FACE_VECTOR: GPType.BuildFaceVector,
#
VECTOR_TO_VERTEX: GPType.VectorToVertex,
VECTOR_TO_EDGE: GPType.VectorToEdge,
VECTOR_TO_FACE: GPType.VectorToFace,
GET_VERTICES_E: GPType.GetVerticesE,
GET_EDGES_F: GPType.GetEdgesF,
GET_VERTICES_F: GPType.GetVerticesF,
STAR: GPType.Star,
CLOSURE: GPType.Closure,
LINK: GPType.Link,
BOUNDARY: GPType.Boundary,
IS_COMPLEX: GPType.IsComplex,
IS_PURE_COMPLEX: GPType.IsPureComplex,
VERTICES: GPType.Vertices,
EDGES: GPType.Edges,
FACES: GPType.Faces,
TETS: GPType.Tets,
DIAMOND:GPType.Diamond,
}
TRIANGLE_MESH_SYM_TYPE = {
# functions
FACES_OF_EDGE: make_function_type([EdgeType()], [FaceSetType()]),
FACE_NORMAL: make_function_type(),
DIHEDRAL: make_function_type(),
GET_ADJACENT_VERTICES_V: make_function_type([VertexType()], [VertexSetType()]),
GET_INCIDENT_EDGES_V: make_function_type([VertexType()], [EdgeSetType()]),
GET_INCIDENT_FACES_V: make_function_type([VertexType()], [FaceSetType()]),
#
GET_INCIDENT_VERTICES_E: make_function_type([EdgeType()], [VertexSetType()]),
GET_INCIDENT_FACES_E: make_function_type([EdgeType()], [FaceSetType()]),
GET_DIAMOND_VERTICES_E: make_function_type([EdgeType()], [VertexSetType()]),
GET_DIAMOND_FACES_E: make_function_type([EdgeType()], [VertexType(), VertexType()]),
#
GET_INCIDENT_VERTICES_F: make_function_type([FaceType()], [VertexSetType()]),
GET_INCIDENT_EDGES_F: make_function_type([FaceType()], [EdgeSetType()]),
GET_ADJACENT_FACES_F: make_function_type([FaceType()], [FaceSetType()]),
#
BUILD_VERTEX_VECTOR: make_function_type(),  # must be a valid function type for preprocessing
BUILD_EDGE_VECTOR: make_function_type(),
BUILD_FACE_VECTOR: make_function_type(),
#
VECTOR_TO_VERTEX: make_function_type(),
VECTOR_TO_EDGE: make_function_type(),
VECTOR_TO_FACE: make_function_type(),
#
GET_VERTICES_E: make_function_type([EdgeType()], [VertexType(), VertexType()]),
GET_EDGES_F: make_function_type([FaceType()], [EdgeType(), EdgeType(), EdgeType()]),
GET_VERTICES_F: make_function_type([FaceType()], [VertexType(), VertexType(), VertexType()]),
#
STAR: make_function_type([SimplicialSetType()], [SimplicialSetType()]),
CLOSURE: make_function_type([SimplicialSetType()], [SimplicialSetType()]),
LINK: make_function_type([SimplicialSetType()], [SimplicialSetType()]),
BOUNDARY: make_function_type([SimplicialSetType()], [SimplicialSetType()]),
IS_COMPLEX: make_function_type([SimplicialSetType()], [IntType()]),
IS_PURE_COMPLEX: make_function_type([SimplicialSetType()], [IntType()]),
#
VERTICES: make_function_type([SimplicialSetType()], [VertexSetType()]),
EDGES: make_function_type([SimplicialSetType()], [EdgeSetType()]),
FACES: make_function_type([SimplicialSetType()], [FaceSetType()]),
TETS: make_function_type([SimplicialSetType()], [TetSetType()]),
DIAMOND: make_function_type([EdgeType()], [SimplicialSetType()]),
# variables
VI: VertexSetType(),
EI: EdgeSetType(),
FI: FaceSetType(),
NEI: EdgeSetType(),
BM1: None,
BM2: None,
BM3: None
}
TRIANGLE_MESH_DYNAMIC_TYPE_LIST = [BM1, BM2, BM3, BUILD_VERTEX_VECTOR, BUILD_EDGE_VECTOR, BUILD_FACE_VECTOR,
                                   VECTOR_TO_VERTEX, VECTOR_TO_EDGE, VECTOR_TO_FACE]
def merge_dict(dict1, dict2):
    # key:[value,]
    res = copy.deepcopy(dict1)
    for key, value in dict2.items():
        if key in res:
            res[key] += value
        else:
            res[key] = value
    return res
PACKAGES_DICT = merge_dict(PACKAGES_FUNC_DICT, PACKAGES_SYM_DICT)
CLASS_PACKAGES = [TRIANGLE_MESH]

def get_sym_type_from_pkg(sym, pkg, dim_dict=None):
    ret = LaVarType()
    if pkg == TRIANGLE_MESH:
        if sym in TRIANGLE_MESH_SYM_TYPE:
            if sym in TRIANGLE_MESH_DYNAMIC_TYPE_LIST:
                if dim_dict:
                    if sym == BM1:
                        ret = MatrixType(rows=dim_dict['vi_size'], cols=dim_dict['ei_size'])
                    elif sym == BM2:
                        ret = MatrixType(rows=dim_dict['ei_size'], cols=dim_dict['fi_size'])
                    elif sym == BM3:
                        ret = MatrixType(rows=dim_dict['fi_size'], cols=dim_dict['ti_size'])
                    elif sym == BUILD_VERTEX_VECTOR:
                        ret = make_function_type([VertexSetType()], [VectorType(rows=dim_dict['vi_size'])])
                    elif sym == BUILD_EDGE_VECTOR:
                        ret = make_function_type([EdgeSetType()], [VectorType(rows=dim_dict['ei_size'])])
                    elif sym == BUILD_FACE_VECTOR:
                        ret = make_function_type([FaceSetType()], [VectorType(rows=dim_dict['fi_size'])])
                    elif sym == VECTOR_TO_VERTEX:
                        ret = make_function_type([VectorType(rows=dim_dict['vi_size']), [VertexSetType()]])
                    elif sym == VECTOR_TO_EDGE:
                        ret = make_function_type([VectorType(rows=dim_dict['ei_size']), [EdgeSetType()]])
                    elif sym == VECTOR_TO_FACE:
                        ret = make_function_type([VectorType(rows=dim_dict['fi_size']), [FaceSetType()]])
                else:
                    ret = TRIANGLE_MESH_SYM_TYPE[sym]
            else:
                ret = TRIANGLE_MESH_SYM_TYPE[sym]
    return ret