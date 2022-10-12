GEOMETRY = r"""
### geometry function
# triangle_mesh function

faces_of_edge_func::FacesOfEdgeFunc
    = name:/faces_of_edge/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
dihedral_func::FacesOfEdgeFunc
    = name:/dihedral/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
face_normal_func::FaceNormalFunc
    = name:/face_normal/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
"""