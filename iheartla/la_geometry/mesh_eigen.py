from .gp_funcs import *
impl_faces_of_edge = r"""std::tuple< int, int > faces_of_edge(int i, int j){
    std::tuple< int, int > ret;
    return ret;
}
"""
impl_face_normal = r"""int face_normal(int i, int j){
    return 0;
}
"""
impl_dihedral = r"""double dihedral(int i, int j, int k, int l){
    return 0;
}
"""

MESH_EIGEN_DICT = {FACE_OF_EDGES: impl_faces_of_edge,
                   FACE_NORMAL: impl_face_normal,
                   DIHEDRAL: impl_dihedral}