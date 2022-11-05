GEOMETRY = r"""
### geometry function
# triangle_mesh function

faces_of_edge_func::FacesOfEdgeFunc
    = name:/faces_of_edge/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
dihedral_func::DihedralFunc
    = name:/dihedral/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
face_normal_func::FaceNormalFunc
    = name:/face_normal/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
# dec operators
star_func::StarFunc
    = name:/star/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
closure_func::ClosureFunc
    = name:/closure/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
link_func::LinkFunc
    = name:/link/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
boundary_func::BoundaryFunc
    = name:/boundary/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
isComplex_func::IsComplexFunc
    = name:/isComplex/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
isPureComplex_func::IsPureComplexFunc
    = name:/isPureComplex/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
"""