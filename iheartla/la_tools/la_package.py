import copy
from ..la_parser.la_types import *

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
PACKAGES_FUNC_DICT = {'trigonometry': ['sin', 'asin', 'arcsin', 'cos', 'acos', 'arccos', 'tan', 'atan', 'arctan', 'atan2',
                                  'sinh', 'asinh', 'arsinh', 'cosh', 'acosh', 'arcosh', 'tanh', 'atanh', 'artanh',
                                  'cot', 'sec', 'csc'],
                 'linearalgebra': ['trace', 'tr', 'diag', 'vec', 'det', 'rank', 'null', 'orth', 'inv'],
                 TRIANGLE_MESH: [FACES_OF_EDGE, FACE_NORMAL, DIHEDRAL,
                                 GET_ADJACENT_VERTICES_V, GET_INCIDENT_EDGES_V, GET_INCIDENT_FACES_V,
                                 GET_INCIDENT_VERTICES_E, GET_INCIDENT_FACES_E, GET_DIAMOND_VERTICES_E, GET_DIAMOND_FACES_E,
                                 GET_INCIDENT_VERTICES_F, GET_INCIDENT_EDGES_F, GET_ADJACENT_FACES_F,
                                 BUILD_VERTEX_VECTOR, BUILD_EDGE_VECTOR, BUILD_FACE_VECTOR,
                                 GET_VERTICES_E, GET_EDGES_F, GET_VERTICES_F,
                                 STAR, CLOSURE, LINK, BOUNDARY, IS_COMPLEX, IS_PURE_COMPLEX,
                                 VERTICES, EDGES, FACES, TETS, DIAMOND]}
PACKAGES_SYM_DICT = {'trigonometry': ['e'],
                 TRIANGLE_MESH: [EDGES, VI, EI, FI, NEI]}
TRIANGLE_MESH_SYM_TYPE = {
# functions
FACES_OF_EDGE: make_function_type([IntType()], FaceSetType()),
FACE_NORMAL: make_function_type(),
DIHEDRAL: make_function_type(),
GET_ADJACENT_VERTICES_V: make_function_type([IntType()], VertexSetType()),
GET_INCIDENT_EDGES_V: make_function_type([IntType()], EdgeSetType()),
GET_INCIDENT_FACES_V: make_function_type([IntType()], FaceSetType()),
#
GET_INCIDENT_VERTICES_E: make_function_type([IntType()], VertexSetType()),
GET_INCIDENT_FACES_E: make_function_type([IntType()], FaceSetType()),
GET_DIAMOND_VERTICES_E: make_function_type([IntType()], VertexSetType()),
GET_DIAMOND_FACES_E: make_function_type([IntType()], FaceSetType()),
#
GET_INCIDENT_VERTICES_F: make_function_type([IntType()], VertexSetType()),
GET_INCIDENT_EDGES_F: make_function_type([IntType()], EdgeSetType()),
GET_ADJACENT_FACES_F: make_function_type([IntType()], FaceSetType()),
#
BUILD_VERTEX_VECTOR: make_function_type([VertexSetType()], VectorType()),
BUILD_EDGE_VECTOR: make_function_type([EdgeSetType()], VectorType()),
BUILD_FACE_VECTOR: make_function_type([FaceSetType()], VectorType()),
GET_VERTICES_E: make_function_type([IntType()], [IntType(), IntType()]),
GET_EDGES_F: make_function_type([IntType()], [IntType(), IntType(), IntType()]),
GET_VERTICES_F: make_function_type([IntType()], [IntType(), IntType(), IntType()]),
STAR: make_function_type([SimplicialSetType()], SimplicialSetType()),
CLOSURE: make_function_type([SimplicialSetType()], SimplicialSetType()),
LINK: make_function_type([SimplicialSetType()], SimplicialSetType()),
BOUNDARY: make_function_type([SimplicialSetType()], SimplicialSetType()),
IS_COMPLEX: make_function_type([SimplicialSetType()], IntType()),
IS_PURE_COMPLEX: make_function_type([SimplicialSetType()], IntType()),
VERTICES: make_function_type([SimplicialSetType()], VertexSetType()),
EDGES: make_function_type([SimplicialSetType()], EdgeSetType()),
FACES: make_function_type([SimplicialSetType()], FaceSetType()),
TETS: make_function_type([SimplicialSetType()], TetSetType()),
DIAMOND: make_function_type([IntType()], SimplicialSetType()),
# variables
VI: VertexSetType(),
EI: EdgeSetType(),
FI: FaceSetType(),
NEI: EdgeSetType()
}
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

def get_sym_type_from_pkg(sym, pkg):
    ret = LaVarType()
    if pkg == TRIANGLE_MESH:
        if sym in TRIANGLE_MESH_SYM_TYPE:
            ret = TRIANGLE_MESH_SYM_TYPE[sym]
    return ret