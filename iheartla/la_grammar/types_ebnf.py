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
    ;

dimension
    =
    arithmetic_expression
    ;

la_type
    =
    | function_type
    | matrix_type
    | vector_type
    | set_type
    | scalar_type
    ;

params_type
    = matrix_type
    | vector_type
    | scalar_type
    | set_type
    ;

function_type::FunctionType
    = ((params+:params_type {{hspace} separators+:params_separator {hspace} params+:params_type})|empty:'∅'|'{'{hspace}'}') {hspace} ('→'|'->') {hspace} ret+:params_type {{hspace} ret_separators+:params_separator {hspace} ret+:params_type}
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