GEOMETRY = r"""
### geometry function
# triangle_mesh function
FACES_OF_EDGE = /faces_of_edge/;
DIHEDRAL = /dihedral/;
FACE_NORMAL = /face_normal/;
GET_ADJACENT_VERTICES_V = /get_adjacent_vertices_v/;
GET_INCIDENT_EDGES_V = /get_incident_edges_v/;
GET_INCIDENT_FACES_V = /get_incident_faces_v/;
GET_INCIDENT_VERTICES_E = /get_incident_vertices_e/;
GET_INCIDENT_FACES_E = /get_incident_faces_e/;
GET_DIAMOND_VERTICES_E = /get_diamond_vertices_e/;
GET_DIAMOND_FACES_E = /get_diamond_faces_e/;
GET_INCIDENT_VERTICES_F = /get_incident_vertices_f/;
GET_INCIDENT_EDGES_F = /get_incident_edges_f/;
GET_ADJACENT_FACES_F = /get_adjacent_faces_f/;
BUILD_VERTEX_VECTOR = /build_vertex_vector/;
BUILD_EDGE_VECTOR = /build_edge_vector/;
BUILD_FACE_VECTOR = /build_face_vector/;
STAR = /star/;
CLOSURE = /closure/;
LINK = /link/;
BOUNDARY = /boundary/;
IS_COMPLEX = /is_complex/;
IS_PURE_COMPLEX = /is_pure_complex/;
GET_VERTICES_E = /get_vertices_e/;
GET_VERTICES_F = /get_vertices_f/;
GET_EDGES_F = /get_edges_f/;
DIAMOND = /diamond/;

faces_of_edge_func::FacesOfEdgeFunc
    = name:FACES_OF_EDGE'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
dihedral_func::DihedralFunc
    = name:DIHEDRAL'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
face_normal_func::FaceNormalFunc
    = name:FACE_NORMAL'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_adjacent_vertices_v_func::GetAdjacentVerticesVFunc
    = name:GET_ADJACENT_VERTICES_V'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_incident_edges_v_func::GetIncidentEdgesVFunc
    = name:GET_INCIDENT_EDGES_V'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_incident_faces_v_func::GetIncidentFacesVFunc
    = name:GET_INCIDENT_FACES_V'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_incident_vertices_e_func::GetIncidentVerticesEFunc
    = name:GET_INCIDENT_VERTICES_E'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_incident_faces_e_func::GetIncidentFacesEFunc
    = name:GET_INCIDENT_FACES_E'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_diamond_vertices_e_func::GetDiamondVerticesEFunc
    = name:GET_DIAMOND_VERTICES_E'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_diamond_faces_e_func::GetDiamondFacesEFunc
    = name:GET_DIAMOND_FACES_E'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_incident_vertices_f_func::GetIncidentVerticesFFunc
    = name:GET_INCIDENT_VERTICES_F'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_incident_edges_f_func::GetIncidentEdgesFFunc
    = name:GET_INCIDENT_EDGES_F'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
get_adjacent_faces_f_func::GetAdjacentFacesFFunc
    = name:GET_ADJACENT_FACES_F'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
build_vertex_vector_func::BuildVertexVectorFunc
    = name:BUILD_VERTEX_VECTOR'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
build_edge_vector_func::BuildEdgeVectorFunc
    = name:BUILD_EDGE_VECTOR'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
build_face_vector_func::BuildFaceVectorFunc
    = name:BUILD_FACE_VECTOR'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
    
# dec operators
star_func::StarFunc
    = name:STAR'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
closure_func::ClosureFunc
    = name:CLOSURE'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
link_func::LinkFunc
    = name:LINK'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
boundary_func::BoundaryFunc
    = name:BOUNDARY'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
isComplex_func::IsComplexFunc
    = name:IS_COMPLEX'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
isPureComplex_func::IsPureComplexFunc
    = name:IS_PURE_COMPLEX'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
get_vertices_e_func::GetVerticesEFunc
    = name:GET_VERTICES_E'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
get_vertices_f_func::GetVerticesFFunc
    = name:GET_VERTICES_F'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
get_edges_f_func::GetEdgesFFunc
    = name:GET_EDGES_F'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
vertices_func::VerticesFunc
    = name:VERTICES'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
edges_func::EdgesFunc
    = name:EDGES'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
faces_func::FacesFunc
    = name:FACES'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
tets_func::TetsFunc
    = name:TETS'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;
diamond_func::DiamondFunc
    = name:DIAMOND'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;

"""