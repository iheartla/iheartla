from .gp_funcs import *
impl_faces_of_edge = r"""int faces_of_edge(int i, int j){
    return i+j;
}
"""
impl_face_normal = r"""int face_normal(int i, int j){
    return i+j;
}
"""

MESH_EIGEN_DICT = {FACE_OF_EDGES: impl_faces_of_edge,
                   FACE_NORMAL: impl_face_normal}