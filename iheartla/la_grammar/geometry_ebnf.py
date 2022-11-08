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
    
get_adjacent_vertices_v_func::GetAdjacentVerticesVFunc
    = name:/get_adjacent_vertices_v/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_incident_edges_v_func::GetIncidentEdgesVFunc
    = name:/get_incident_edges_v/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_incident_faces_v_func::GetIncidentFacesVFunc
    = name:/get_incident_faces_v/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_incident_vertices_e_func::GetIncidentVerticesEFunc
    = name:/get_incident_vertices_e/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_incident_faces_e_func::GetIncidentFacesEFunc
    = name:/get_incident_faces_e/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_diamond_vertices_e_func::GetDiamondVerticesEFunc
    = name:/get_diamond_vertices_e/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_incident_vertices_f_func::GetIncidentVerticesFFunc
    = name:/get_incident_vertices_f/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_incident_edges_f_func::GetIncidentEdgesFFunc
    = name:/get_incident_edges_f/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_adjacent_faces_f_func::GetAdjacentFacesFFunc
    = name:/get_adjacent_faces_f/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
build_vertex_vector_func::BuildVertexVectorFunc
    = name:/build_vertex_vector/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
build_edge_vector_func::BuildEdgeVectorFunc
    = name:/build_edge_vector/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
build_face_vector_func::BuildFaceVectorFunc
    = name:/build_face_vector/'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
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