from .gp_funcs import *
impl_faces_of_edge = r"""int faces_of_edge(int i, int j){
    return i+j;
}
"""

MESH_NUMPY_DICT = {FACE_OF_EDGES: impl_faces_of_edge}
