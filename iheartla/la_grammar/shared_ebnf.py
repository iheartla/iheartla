SHARED = r"""
Directive
    = import
    ;

import::Import
    = names+:multi_str {{hspace} ',' {hspace} names+:multi_str } {hspace} FROM  {hspace}+ package:multi_str {hspace} 
    {'(' {{hspace} params+:identifier_alone {{hspace} separators+:params_separator {hspace} params+:identifier_alone}} {hspace} ')'} {hspace}
    ;

where_conditions::WhereConditions
    = {hspace} value+:where_condition {{separator_with_space}+ value+:where_condition}
    ;

where_condition::WhereCondition
    = id+:identifier {{hspace} ',' {hspace} id+:identifier} {hspace} (':'| IN) {hspace} type:la_type {{hspace} index:'index'} { {hspace} ':' {hspace} desc:description}
    ;
    
where_condition_terse::WhereCondition
    = id+:identifier {{hspace} ',' {hspace} id+:identifier} {hspace} (':'| IN) {hspace} type:la_type {{hspace} index:'index'}
    ;

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

#######################################################################################################################

valid_block
    = Directive | params_block | statements 
    ;


params_block::ParamsBlock
    = {annotation:(WHERE | GIVEN ) {separator_with_space}+} conds:where_conditions
    ;

builtin_operators
    =
    predefined_built_operators;

statements::Statements
    =
    #| stats:statements {separator_with_space}+ stat:statement
    stat:statement
    ;

statement
    =
    | local_func
    | assignment
    | right_hand_side
    ;


expression::Expression
    =
    | value:addition
    | value:subtraction
    | value:add_sub_operator
    | sign:['-'] value:term
    ;

assignment::Assignment
    =
    left+:identifier {{hspace} ',' {hspace} left+:identifier} {hspace} op:'=' {hspace} {separator_with_space} right+:right_hand_side {{hspace} ',' {hspace} right+:expression}
    | left+:identifier {{hspace} ',' {hspace} left+:identifier} {hspace} op:'+=' {hspace} {separator_with_space} right+:right_hand_side {{hspace} ',' {hspace} right+:expression}
    | {SOLVE '_(' {hspace} v:where_condition_terse {hspace}')' {hspace}+} lexpr:expression {hspace} op:'=' {hspace} rexpr:expression 
    ;
    
#### name:(func_id | identifier)
local_func::LocalFunc
    = name:identifier def_p:'(' {{hspace} params+:identifier_alone {{hspace} separators+:params_separator {hspace} params+:identifier_alone}} {hspace} ')' {hspace} 
    op:'=' {hspace} expr+:right_hand_side {{hspace} ',' {hspace} expr+:right_hand_side} [{hspace} line] {hspace} (WHERE | GIVEN ) {hspace} defs+:where_condition {{hspace} ',' {hspace} defs+:where_condition}
    | name:identifier '[' {{hspace} params+:identifier_alone {{hspace} separators+:params_separator {hspace} params+:identifier_alone}} {hspace} ']' {hspace}
     op:'=' {hspace} expr+:right_hand_side {{hspace} ',' {hspace} expr+:right_hand_side} [{hspace} line] {hspace} (WHERE | GIVEN ) {hspace} defs+:where_condition {{hspace} ',' {hspace} defs+:where_condition}
     ;


right_hand_side
    =
    | expression
    | optimize_operator
    | multi_cond_expr
    ;

term
    =
    | multiplication
    | division
    | factor
    ;


factor::Factor
    =
    op:operations
    | sub:subexpression
    | nm:number_matrix
    | id0:identifier
    | num:number
    | m:matrix
    | v:vector
    | c:constant
    ;
    
sub_factor
    = 
    subexpression
    | identifier_alone
    | number
    | constant
    ;

constant
    =
    pi;

KEYWORDS
    = BUILTIN_KEYWORDS;

subexpression::Subexpression
    =
    '(' {hspace} value:expression {hspace} ')'
    ;
    
#######################################################################################################################
if_condition::IfCondition
    = se:if_condition {hspace} OR {hspace} other:and_condition
    | single:and_condition
    ;

and_condition::AndCondition
    = se:and_condition {hspace} AND {hspace} other:atom_condition
    | atom:atom_condition
    ;

atom_condition::AtomCondition
    =
    | '(' {hspace} p:if_condition {hspace} ')'
    | cond:not_equal
    | cond:equal
    | cond:in
    | cond:not_in
    | cond:greater
    | cond:greater_equal
    | cond:less
    | cond:less_equal
    ;

in::InCondition
    = '(' {hspace} left+:expression {hspace} {',' {hspace} left+:expression {hspace}} ')' {hspace} IN {hspace} right:(function_operator | identifier)
    | left+:expression {hspace} IN {hspace} right:(function_operator | identifier)
    ;

not_in::NotInCondition
    = '(' {hspace} left+:expression {hspace} {',' {hspace} left+:expression {hspace}} ')' {hspace} '∉' {hspace} right:(function_operator | identifier)
    | left+:expression {hspace} '∉' {hspace} right:(function_operator | identifier)
    ;

not_equal::NeCondition
    = left:expression {hspace} op:('≠' | '!=') {hspace} right:expression
    ;

equal::EqCondition
    = left:expression {hspace} op:('==' | '=') {hspace} right:expression
    ;

greater::GreaterCondition
    = left:expression {hspace} op:'>' {hspace} right:expression
    ;

greater_equal::GreaterEqualCondition
    = left:expression {hspace} op:('>=' | '≥'| '⩾') {hspace} right:expression
    ;

less::LessCondition
    = left:expression {hspace} op:'<' {hspace} right:expression
    ;

less_equal::LessEqualCondition
    = left:expression {hspace} op:('<=' | '≤'| '⩽') {hspace} right:expression
    ;
"""