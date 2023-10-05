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
    VertexPositions = 27
    FaceMatrix = 28
    # dec
    Star = 100
    Closure = 101
    Link = 102
    Boundary = 103
    IsComplex = 104
    IsPureComplex = 105
    #
    MeshSets = 200
    BoundaryMatrices = 201
    UnsignedBoundaryMatrices = 202
    CanonicalVertexOrderings = 203
    NonZeros = 204
    IndicatorVector = 205
    ValueSet = 206

class MeshData(object):
    def __init__(self, v=None, e=None, f=None, t=None, la_type=None):
        # track the symbols in this assignment: v,e,f = meshset(T)
        self.v = v
        self.e = e
        self.f = f
        self.t = t
        self.la_type = la_type

    def init_dims(self, dim_list):
        if len(dim_list) >= 3:
            self.v = dim_list[0]
            self.e = dim_list[1]
            self.f = dim_list[2]
        if len(dim_list) > 3:
            self.t = dim_list[3]

# dimension name
VI_SIZE = 'vi_size'
EI_SIZE = 'ei_size'
FI_SIZE = 'fi_size'
TI_SIZE = 'ti_size'
#
MESH_CLASS = 'TriangleMesh'
MESH_HELPER = 'MeshConnectivity'
EdgeMesh = "EdgeMesh"
FaceMesh = "FaceMesh"
CellMesh = "CellMesh"
MESH_MAPPING_DICT = {
                MeshTypeEnum.EdgeMesh: EdgeMesh,
                MeshTypeEnum.FaceMesh: FaceMesh,
                MeshTypeEnum.CellMesh: CellMesh
                }
# MeshHelper function
NonZeros = 'NonZeros'
ValueSet = 'ValueSet'
IndicatorVector = 'IndicatorVector'
CanonicalVertexOrderings = 'CanonicalVertexOrderings'
MeshSets = 'ElementSets'
BoundaryMatrices = 'BoundaryMatrices'
UnsignedBoundaryMatrices = 'UnsignedBoundaryMatrices'
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
VERTICES_TO_VECTOR = 'vertices_to_vector'
EDGES_TO_VECTOR = 'edges_to_vector'
FACES_TO_VECTOR = 'faces_to_vector'
TETS_TO_VECTOR = 'tets_to_vector'
VECTOR_TO_VERTICES = 'vector_to_vertices'
VECTOR_TO_EDGES = 'vector_to_edges'
VECTOR_TO_FACES = 'vector_to_faces'
VERTEX_POSITIONS = 'vertex_positions'
FACE_MATRIX = 'face_matrix'
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
                 'linearalgebra': ['trace', 'tr', 'diag', 'inversevec', 'vec⁻¹', 'vec', 'det', 'rank', 'null', 'orth', 'inv', 'svd'],
                 MESH_HELPER: [MeshSets, BoundaryMatrices, UnsignedBoundaryMatrices,
                               NonZeros, IndicatorVector, ValueSet]
                      }
PACKAGES_SYM_DICT = {'trigonometry': ['e'],
                 MESH_HELPER: []}
MESH_HELPER_FUNC_MAPPING = {
MeshSets: GPType.MeshSets,
BoundaryMatrices: GPType.BoundaryMatrices,
UnsignedBoundaryMatrices: GPType.UnsignedBoundaryMatrices,
CanonicalVertexOrderings: GPType.CanonicalVertexOrderings,
NonZeros: GPType.NonZeros,
ValueSet: GPType.ValueSet,
IndicatorVector: GPType.IndicatorVector,
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
VERTICES_TO_VECTOR: GPType.BuildVertexVector,
EDGES_TO_VECTOR: GPType.BuildEdgeVector,
FACES_TO_VECTOR: GPType.BuildFaceVector,
#
VECTOR_TO_VERTICES: GPType.VectorToVertex,
VECTOR_TO_EDGES: GPType.VectorToEdge,
VECTOR_TO_FACES: GPType.VectorToFace,
VERTEX_POSITIONS: GPType.VertexPositions,
FACE_MATRIX: GPType.FaceMatrix,
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
MESH_HELPER_SYM_TYPE = {
MeshSets: make_function_type([MeshType()], [VertexSetType(), EdgeSetType(), FaceSetType()]),
BoundaryMatrices: make_function_type([MeshType()], [MatrixType(), MatrixType()]),
UnsignedBoundaryMatrices: make_function_type([MeshType()], [MatrixType(), MatrixType()]),
CanonicalVertexOrderings: make_function_type([MeshType()], [MatrixType(), MatrixType()]),
# NonZeros: OverloadingFunctionType(func_list=[make_function_type([MatrixType(element_type=VertexType())], [VertexSetType()]),
#                                               make_function_type([MatrixType(element_type=EdgeType())], [EdgeSetType()]),
#                                               make_function_type([MatrixType(element_type=FaceType())], [FaceSetType()]),
#                                               make_function_type([MatrixType(element_type=TetType())], [TetSetType()])],
#                                    fname_list=['{}_0'.format(NonZeros),
#                                                '{}_1'.format(NonZeros),
#                                                '{}_2'.format(NonZeros),
#                                                '{}_3'.format(NonZeros)]),
NonZeros: make_function_type([MatrixType(element_type=ScalarType(is_int=True))], [SetType(int_list=[True], type_list=[ScalarType(is_int=True)])]),
# ValueSet: OverloadingFunctionType(func_list=[make_function_type([MatrixType(element_type=VertexType()), ScalarType(is_int=True)], [VertexSetType()]),
#                                               make_function_type([MatrixType(element_type=EdgeType()), ScalarType(is_int=True)], [EdgeSetType()]),
#                                               make_function_type([MatrixType(element_type=FaceType()), ScalarType(is_int=True)], [FaceSetType()]),
#                                               make_function_type([MatrixType(element_type=TetType()), ScalarType(is_int=True)], [TetSetType()])],
#                                    fname_list=['{}_0'.format(ValueSet),
#                                                '{}_1'.format(ValueSet),
#                                                '{}_2'.format(ValueSet),
#                                                '{}_3'.format(ValueSet)]),
ValueSet: make_function_type([MatrixType(element_type=ScalarType(is_int=True)), ScalarType(is_int=True)], [SetType(int_list=[True], type_list=[ScalarType(is_int=True)])]),
IndicatorVector: OverloadingFunctionType(func_list=[make_function_type([VertexSetType()], [MatrixType(cols=1, sparse=True, element_type=VertexType())]),
                                              make_function_type([EdgeSetType()], [MatrixType(cols=1, sparse=True, element_type=EdgeType())]),
                                              make_function_type([FaceSetType()], [MatrixType(cols=1, sparse=True, element_type=FaceType())]),
                                              make_function_type([TetSetType()], [MatrixType(cols=1, sparse=True, element_type=TetType())])],
                                   fname_list=['{}_0'.format(IndicatorVector),
                                               '{}_1'.format(IndicatorVector),
                                               '{}_2'.format(IndicatorVector),
                                               '{}_3'.format(IndicatorVector)]),
# functions
FACES_OF_EDGE: make_function_type([MeshType(),EdgeType()], [FaceSetType()]),
FACE_NORMAL: make_function_type(),
DIHEDRAL: make_function_type(),
GET_ADJACENT_VERTICES_V: make_function_type([MeshType(),VertexType()], [VertexSetType()]),
GET_INCIDENT_EDGES_V: make_function_type([MeshType(),VertexType()], [EdgeSetType()]),
GET_INCIDENT_FACES_V: make_function_type([MeshType(),VertexType()], [FaceSetType()]),
#
GET_INCIDENT_VERTICES_E: make_function_type([MeshType(),EdgeType()], [VertexSetType()]),
GET_INCIDENT_FACES_E: make_function_type([MeshType(),EdgeType()], [FaceSetType()]),
GET_DIAMOND_VERTICES_E: make_function_type([MeshType(),EdgeType()], [VertexSetType()]),
GET_DIAMOND_FACES_E: make_function_type([MeshType(),EdgeType()], [FaceType(), FaceType()]),
#
GET_INCIDENT_VERTICES_F: make_function_type([MeshType(),FaceType()], [VertexSetType()]),
GET_INCIDENT_EDGES_F: make_function_type([MeshType(),FaceType()], [EdgeSetType()]),
GET_ADJACENT_FACES_F: make_function_type([MeshType(),FaceType()], [FaceSetType()]),
#
VERTICES_TO_VECTOR: make_function_type(),  # must be a valid function type for preprocessing
EDGES_TO_VECTOR: make_function_type(),
FACES_TO_VECTOR: make_function_type(),
#
VECTOR_TO_VERTICES: make_function_type(),
VECTOR_TO_EDGES: make_function_type(),
VECTOR_TO_FACES: make_function_type(),
VERTEX_POSITIONS: make_function_type(),
FACE_MATRIX: make_function_type(),
#
GET_VERTICES_E: make_function_type([MeshType(),EdgeType()], [VertexType(), VertexType()]),
GET_EDGES_F: make_function_type([MeshType(),FaceType()], [EdgeType(), EdgeType(), EdgeType()]),
GET_VERTICES_F: make_function_type([MeshType(),FaceType()], [VertexType(), VertexType(), VertexType()]),
#
STAR: make_function_type([MeshType(),SimplicialSetType()], [SimplicialSetType()]),
CLOSURE: make_function_type([MeshType(),SimplicialSetType()], [SimplicialSetType()]),
LINK: make_function_type([MeshType(),SimplicialSetType()], [SimplicialSetType()]),
BOUNDARY: make_function_type([MeshType(),SimplicialSetType()], [SimplicialSetType()]),
IS_COMPLEX: make_function_type([MeshType(),SimplicialSetType()], [IntType()]),
IS_PURE_COMPLEX: make_function_type([MeshType(),SimplicialSetType()], [IntType()]),
#
VERTICES: make_function_type([MeshType(),SimplicialSetType()], [VertexSetType()]),
EDGES: make_function_type([MeshType(),SimplicialSetType()], [EdgeSetType()]),
FACES: make_function_type([MeshType(),SimplicialSetType()], [FaceSetType()]),
TETS: make_function_type([MeshType(),SimplicialSetType()], [TetSetType()]),
DIAMOND: make_function_type([MeshType(),EdgeType()], [SimplicialSetType()]),
# variables
VI: VertexSetType(),
EI: EdgeSetType(),
FI: FaceSetType(),
NEI: EdgeSetType(),
BM1: None,
BM2: None,
BM3: None
}
# need extra info
MESH_HELPER_DYNAMIC_TYPE_LIST = [BM1, BM2, BM3, VERTICES_TO_VECTOR, EDGES_TO_VECTOR, FACES_TO_VECTOR,
                                   VECTOR_TO_VERTICES, VECTOR_TO_EDGES, VECTOR_TO_FACES, VERTEX_POSITIONS, FACE_MATRIX,
                                   MeshSets, BoundaryMatrices, UnsignedBoundaryMatrices, CanonicalVertexOrderings, IndicatorVector]
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
CLASS_PACKAGES = [MESH_HELPER]

# for builtin packages, the overloading functions may have different names in different backends
BACKEND_OVERLOADING_DICT = {
    ParserTypeEnum.EIGEN : {
NonZeros:'nonzeros',
        '{}_0'.format(NonZeros): '{}_0'.format(NonZeros),
        '{}_1'.format(NonZeros): '{}_1'.format(NonZeros),
        '{}_2'.format(NonZeros): '{}_2'.format(NonZeros),
        '{}_3'.format(NonZeros): '{}_3'.format(NonZeros),
        '{}_0'.format(IndicatorVector): VERTICES_TO_VECTOR,
        '{}_1'.format(IndicatorVector): EDGES_TO_VECTOR,
        '{}_2'.format(IndicatorVector): FACES_TO_VECTOR,
        '{}_3'.format(IndicatorVector): TETS_TO_VECTOR,
ValueSet:'ValueSet',
    },
    ParserTypeEnum.NUMPY : {
NonZeros:'nonzeros',
        '{}_0'.format(NonZeros): '{}_0'.format(NonZeros),
        '{}_1'.format(NonZeros): '{}_1'.format(NonZeros),
        '{}_2'.format(NonZeros): '{}_2'.format(NonZeros),
        '{}_3'.format(NonZeros): '{}_3'.format(NonZeros),
        '{}_0'.format(IndicatorVector): VERTICES_TO_VECTOR,
        '{}_1'.format(IndicatorVector): EDGES_TO_VECTOR,
        '{}_2'.format(IndicatorVector): FACES_TO_VECTOR,
        '{}_3'.format(IndicatorVector): TETS_TO_VECTOR,
    },
    ParserTypeEnum.MATLAB : {
NonZeros:'NonZeros',
        '{}_0'.format(NonZeros): '{}_0'.format(NonZeros),
        '{}_1'.format(NonZeros): '{}_1'.format(NonZeros),
        '{}_2'.format(NonZeros): '{}_2'.format(NonZeros),
        '{}_3'.format(NonZeros): '{}_3'.format(NonZeros),
        '{}_0'.format(IndicatorVector): VERTICES_TO_VECTOR,
        '{}_1'.format(IndicatorVector): EDGES_TO_VECTOR,
        '{}_2'.format(IndicatorVector): FACES_TO_VECTOR,
        '{}_3'.format(IndicatorVector): TETS_TO_VECTOR,
    },
}

def get_sym_type_from_pkg(sym, pkg, mesh_type=None):
    ret = LaVarType()
    if pkg == MESH_HELPER:
        if sym in MESH_HELPER_SYM_TYPE:
            if sym in MESH_HELPER_DYNAMIC_TYPE_LIST:
                if mesh_type:
                    if sym == BM1:
                        ret = MatrixType(rows=mesh_type.vi_size, cols=mesh_type.ei_size, sparse=True, element_type=ScalarType(is_int=True), owner=mesh_type.owner)
                    elif sym == BM2:
                        ret = MatrixType(rows=mesh_type.ei_size, cols=mesh_type.fi_size, sparse=True, element_type=ScalarType(is_int=True), owner=mesh_type.owner)
                    elif sym == BM3:
                        ret = MatrixType(rows=mesh_type.fi_size, cols=mesh_type.ti_size, sparse=True, element_type=ScalarType(is_int=True), owner=mesh_type.owner)
                    elif sym == VERTICES_TO_VECTOR:
                        ret = make_function_type([MeshType(),VertexSetType()], [VectorType(rows=mesh_type.vi_size)])
                    elif sym == EDGES_TO_VECTOR:
                        ret = make_function_type([MeshType(),EdgeSetType()], [VectorType(rows=mesh_type.ei_size)])
                    elif sym == FACES_TO_VECTOR:
                        ret = make_function_type([MeshType(),FaceSetType()], [VectorType(rows=mesh_type.fi_size)])
                    elif sym == VECTOR_TO_VERTICES:
                        ret = make_function_type([MeshType(),VectorType(rows=mesh_type.vi_size)], [VertexSetType()])
                    elif sym == VECTOR_TO_EDGES:
                        ret = make_function_type([MeshType(),VectorType(rows=mesh_type.ei_size)], [EdgeSetType()])
                    elif sym == VECTOR_TO_FACES:
                        ret = make_function_type([MeshType(),VectorType(rows=mesh_type.fi_size)], [FaceSetType()])
                    elif sym == VERTEX_POSITIONS:
                        ret = make_function_type([MeshType()], [MatrixType(rows=mesh_type.vi_size, cols=3)])
                    elif sym == FACE_MATRIX:
                        ret = make_function_type([MeshType()], [MatrixType(rows=mesh_type.fi_size, cols=3)])
                    elif sym == CanonicalVertexOrderings:
                        ret = make_function_type([MeshType()], [
                            VectorType(rows=mesh_type.vi_size, element_type=VertexType()),
                            MatrixType(rows=mesh_type.ei_size, cols=2, element_type=EdgeType()),
                            MatrixType(rows=mesh_type.fi_size, cols=3, element_type=FaceType())])
                    elif sym == IndicatorVector:
                        ret = OverloadingFunctionType(func_list=[make_function_type([VertexSetType()], [MatrixType(rows=mesh_type.vi_size, cols=1, sparse=True, element_type=VertexType(), owner=mesh_type.owner)]),
                                              make_function_type([EdgeSetType()], [MatrixType(rows=mesh_type.ei_size, cols=1, sparse=True, element_type=EdgeType(), owner=mesh_type.owner)]),
                                              make_function_type([FaceSetType()], [MatrixType(rows=mesh_type.fi_size, cols=1, sparse=True, element_type=FaceType(), owner=mesh_type.owner)]),
                                              make_function_type([TetSetType()], [MatrixType(rows=mesh_type.ti_size, cols=1, sparse=True, element_type=TetType(), owner=mesh_type.owner)])],
                                   fname_list=['{}_0'.format(IndicatorVector),
                                               '{}_1'.format(IndicatorVector),
                                               '{}_2'.format(IndicatorVector),
                                               '{}_3'.format(IndicatorVector)])
                    elif sym == MeshSets:
                        if mesh_type.cur_mesh == MeshTypeEnum.FaceMesh:
                            ret = make_function_type([MeshType()], [VertexSetType(length=mesh_type.vi_size, owner=mesh_type.owner), EdgeSetType(length=mesh_type.ei_size, owner=mesh_type.owner), FaceSetType(length=mesh_type.fi_size, owner=mesh_type.owner)])
                        elif mesh_type.cur_mesh == MeshTypeEnum.CellMesh:
                            ret = make_function_type([MeshType()], [VertexSetType(length=mesh_type.vi_size, owner=mesh_type.owner), EdgeSetType(length=mesh_type.ei_size, owner=mesh_type.owner), FaceSetType(length=mesh_type.fi_size, owner=mesh_type.owner), TetSetType(length=mesh_type.ti_size, owner=mesh_type.owner)])
                        elif mesh_type.cur_mesh == MeshTypeEnum.EdgeMesh:
                            ret = make_function_type([MeshType()], [VertexSetType(length=mesh_type.vi_size, owner=mesh_type.owner), EdgeSetType(length=mesh_type.ei_size, owner=mesh_type.owner)])
                    elif sym == BoundaryMatrices:
                        if mesh_type.cur_mesh == MeshTypeEnum.FaceMesh:
                            ret = make_function_type([MeshType()], [MatrixType(rows=mesh_type.vi_size, cols=mesh_type.ei_size, sparse=True, element_type=ScalarType(is_int=True), owner=mesh_type.owner), MatrixType(rows=mesh_type.ei_size, cols=mesh_type.fi_size, sparse=True, element_type=ScalarType(is_int=True), owner=mesh_type.owner)])
                        elif mesh_type.cur_mesh == MeshTypeEnum.CellMesh:
                            ret = make_function_type([MeshType()], [MatrixType(rows=mesh_type.vi_size, cols=mesh_type.ei_size, sparse=True, element_type=ScalarType(is_int=True), owner=mesh_type.owner), MatrixType(rows=mesh_type.ei_size, cols=mesh_type.fi_size, sparse=True, element_type=ScalarType(is_int=True), owner=mesh_type.owner), MatrixType(rows=mesh_type.fi_size, cols=mesh_type.ti_size, sparse=True, element_type=ScalarType(is_int=True), owner=mesh_type.owner)])
                        elif mesh_type.cur_mesh == MeshTypeEnum.EdgeMesh:
                            ret = make_function_type([MeshType()], [MatrixType(rows=mesh_type.vi_size, cols=mesh_type.ei_size, sparse=True, element_type=ScalarType(is_int=True), owner=mesh_type.owner)])
                    elif sym == UnsignedBoundaryMatrices:
                        if mesh_type.cur_mesh == MeshTypeEnum.FaceMesh:
                            ret = make_function_type([MeshType()], [MatrixType(rows=mesh_type.vi_size, cols=mesh_type.ei_size, sparse=True, element_type=ScalarType(is_int=True), owner=mesh_type.owner), MatrixType(rows=mesh_type.ei_size, cols=mesh_type.fi_size, sparse=True, element_type=ScalarType(is_int=True), owner=mesh_type.owner)])
                        elif mesh_type.cur_mesh == MeshTypeEnum.CellMesh:
                            ret = make_function_type([MeshType()], [MatrixType(rows=mesh_type.vi_size, cols=mesh_type.ei_size, sparse=True, element_type=ScalarType(is_int=True), owner=mesh_type.owner), MatrixType(rows=mesh_type.ei_size, cols=mesh_type.fi_size, sparse=True, element_type=ScalarType(is_int=True), owner=mesh_type.owner), MatrixType(rows=mesh_type.fi_size, cols=mesh_type.ti_size, sparse=True, element_type=ScalarType(is_int=True), owner=mesh_type.owner)])
                        elif mesh_type.cur_mesh == MeshTypeEnum.EdgeMesh:
                            ret = make_function_type([MeshType()], [MatrixType(rows=mesh_type.vi_size, cols=mesh_type.ei_size, sparse=True, element_type=ScalarType(is_int=True), owner=mesh_type.owner)])
                else:
                    ret = MESH_HELPER_SYM_TYPE[sym]
            else:
                ret = MESH_HELPER_SYM_TYPE[sym]
    return ret