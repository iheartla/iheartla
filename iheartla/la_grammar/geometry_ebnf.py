GEOMETRY = r"""
### geometry function
# triangle_mesh function

faces_of_edge_func::FacesOfEdgeFunc
    = /faces_of_edge/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
dihedral_func::FacesOfEdgeFunc
    = /dihedral/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
"""