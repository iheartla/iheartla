from .gp_funcs import *
impl_faces_of_edge = r"""int faces_of_edge(int i, int j){
    return i+j;
}
"""
impl_face_normal = r"""int face_normal(int i, int j){
    return 0;
}
"""
impl_dihedral = r"""int dihedral(int i, int j, int k, int l){
    return 0;
}
"""

MESH_EIGEN_DICT = {FACE_OF_EDGES: impl_faces_of_edge,
                   FACE_NORMAL: impl_face_normal,
                   DIHEDRAL: impl_dihedral}