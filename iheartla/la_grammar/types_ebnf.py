TYPES = r"""
matrix_type::MatrixType
    = /matrix/ {hspace} '(' {hspace} id1:dimension  {hspace} ',' {hspace} id2:dimension {hspace}')'  {{hspace}+ attr+:matrix_attribute}
    | type:/[ℝℤ]/ {hspace} '^' {hspace} '(' {hspace} id1:dimension  {hspace} '×' {hspace} id2:dimension {hspace}')'  {{hspace}+ attr+:matrix_attribute}
    ;

matrix_attribute 
    = SPARSE
    ;

vector_type::VectorType
    = /vector/ {hspace} '(' {hspace} id1:dimension {hspace}')'
    | type:/[ℝℤ]/ {hspace} '^' {hspace} '(' {hspace} id1:dimension {hspace}')'
    | type:/[ℝℤ]/ {hspace} '^' {hspace} id1:dimension
    | type:/[ℝℤ]/ id1:sup_integer
    ;

scalar_type::ScalarType
    = /scalar/
    | /ℝ/
    | z:/ℤ/
    ;

set_type::SetType
    = '{' {hspace} type+:/[ℝℤ]/ {hspace} {'×' {hspace} type+:/[ℝℤ]/ {hspace} }'}'
    | '{' {hspace} type1:/[ℝℤ]/ {hspace} '^' {hspace} cnt:(integer) {hspace} '}'
    | '{' {hspace} type2:/[ℝℤ]/ cnt:[sup_integer] {hspace} '}' 
    | '{' {hspace} sub_types+:params_type {hspace} {'×' {hspace} sub_types+:params_type {hspace} } '}' 
    | '{' {hspace} homogeneous_types+:params_type {hspace} {'∨' {hspace} homogeneous_types+:params_type {hspace} }+ '}'
    ;
    
tuple_type::TupleType
    = sub_types+:params_type {hspace} {'×' {hspace} sub_types+:params_type {hspace} }+
    ;

dimension
    =
    arithmetic_expression
    ;

named_type::NamedType
    = v:/VertexSet/
    | e:/EdgeSet/
    | f:/FaceSet/
    | t:/TetSet/
    | s:/SimplicialSet/
    ;
    
la_type
    =
    | function_type
    | mapping_type
    | matrix_type
    | vector_type
    | set_type
    | tuple_type
    | scalar_type
    | named_type
    ;

params_type
    = matrix_type
    | vector_type
    | scalar_type
    | set_type
    | tuple_type
    ;

function_type::FunctionType
    = ((params+:params_type {{hspace} separators+:params_separator {hspace} params+:params_type})|empty:'∅'|'{'{hspace}'}') {hspace} ('→'|'->') {hspace} ret+:params_type {{hspace} ret_separators+:params_separator {hspace} ret+:params_type}
    ;
    

mapping_type::MappingType
    = ((params+:identifier {{hspace} separators+:params_separator {hspace} params+:identifier})|empty:'∅'|'{'{hspace}'}') {hspace} ('→'|'->') {hspace} ret_type+:params_type {{hspace} ret_separators+:params_separator {hspace} ret_type+:params_type}
    | ((params+:identifier {{hspace} separators+:params_separator {hspace} params+:identifier})|empty:'∅'|'{'{hspace}'}') {hspace} ('→'|'->') {hspace} ret+:identifier {{hspace} ret_separators+:params_separator {hspace} ret+:identifier}
    ;


#######################################################################################################################

integer::Integer
    =
    value:{digit}+
    ;

sup_integer::SupInteger
    = value:{/[\u2070\u00B9\u00B2\u00B3\u2074-\u2079]/}+
    ;

sub_integer::SubInteger
    = value:{/[\u2080-\u2089]/}+
    ;

digit
    =
    /\d/
    ;
"""