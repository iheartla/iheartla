SHARED = r"""
Directive
    = 
    import
    ;

import::Import
    = 
    (names+:import_var {{hspace} ',' {hspace} names+:import_var } | star:'*' ) {hspace} FROM  {hspace}+ package:multi_str {hspace} 
    {'(' {{hspace} params+:identifier_alone {{hspace} separators+:params_separator {hspace} params+:identifier_alone}} {hspace} ')'} {hspace}
    ;
    
import_var::ImportVar
    = 
    name:multi_str {{hspace}+ AS {hspace}+ r:multi_str}
    ;

where_conditions::WhereConditions
    = 
    {hspace} value+:where_condition {{separator_with_space}+ value+:where_condition}
    ;

where_condition
    =
    la_where_condition
    #| de_where_condition
    ;
    
attribute
    = 
    /index/ | /vertices/ | /edges/ | /faces/ | /tets/
    ;
    
la_where_condition::WhereCondition
    = 
    id+:identifier {{hspace} ',' {hspace} id+:identifier} {hspace} (belong:':'| belong:IN | subset:SUBSET) {hspace} type:la_type {{hspace} attrib:attribute} { {hspace} ':' {hspace} desc:description}
    ;
    
de_where_condition::DeWhereCondition
    = 
    id+:identifier {{hspace} ',' {hspace} id+:identifier} {hspace} subset:SUBSET {hspace} type:la_type {{hspace} attrib:attribute} { {hspace} ':' {hspace} desc:description}
    ;
    
where_condition_terse::WhereCondition
    = 
    id+:identifier {{hspace} ',' {hspace} id+:identifier} {hspace} (':'| IN | subset:SUBSET) {hspace} type:la_type {{hspace} attrib:attribute}
    ;

#######################################################################################################################

valid_block
    = 
    Directive | params_block | statements 
    ;


params_block::ParamsBlock
    = 
    {annotation:(WHERE | GIVEN ) {separator_with_space}+} conds:where_conditions
    ;

builtin_operators
    =
    predefined_built_operators
    ;

statements::Statements
    =
    #| stats:statements {separator_with_space}+ stat:statement
    stat:statement
    ;

statement
    =
    | local_func
    | destructure
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


destructure::Destructure
    = 
    left+:identifier_alone {{hspace} ',' {hspace} left+:identifier_alone}+ {hspace} op:'=' {hspace} right+:simplified_right_hand_side
    ;

assignment::Assignment
    =
    left+:identifier {{hspace} ',' {hspace} left+:identifier} {hspace} op:'=' {hspace} right+:right_hand_side
    | left+:identifier {{hspace} ',' {hspace} left+:identifier} {hspace} op:'+=' {hspace} right+:right_hand_side 
    #| {SOLVE '_(' {hspace} v+:where_condition_terse {hspace} {',' {hspace} v+:where_condition_terse {hspace}} ')' {hspace}} lexpr+:expression {hspace} op:'=' {hspace} rexpr+:expression 
    #{{hspace} ';' {hspace} lexpr+:expression {hspace} op:'=' {hspace} rexpr+:expression }
    ;

general_assign
    =
    destructure
    | general_assignment
    ;
    
general_assignment::GeneralAssignment
    = 
    left+:left_hand_side {{hspace} ',' {hspace} left+:left_hand_side} {hspace} op:'=' {hspace} right+:right_hand_side
    ;
   
simplified_right_hand_side
    =
    | expression
    #| optimize_operator
    | multi_cond_expr
    ;

right_hand_side
    =
    | expression
    | optimize_operator
    | multi_cond_expr
    ;
    
left_hand_side
    = 
    identifier
    | vector
    | matrix
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
    | s:set
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
    pi
    | infinity
    ;

KEYWORDS
    = 
    BUILTIN_KEYWORDS
    ;

subexpression::Subexpression
    =
    '(' {hspace} value:expression {hspace} ')'
    ;
    
#######################################################################################################################
if_condition::IfCondition
    = 
    se:if_condition {hspace} OR {hspace} other:and_condition
    | single:and_condition
    ;

and_condition::AndCondition
    = 
    se:and_condition {hspace} AND {hspace} other:atom_condition
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
    = 
    '(' {hspace} left+:expression {hspace} {',' {hspace} left+:expression {hspace}} ')' {hspace} IN {hspace} right:(function_operator | identifier)
    | left+:expression {hspace} IN {hspace} right:(function_operator | identifier)
    ;

not_in::NotInCondition
    = 
    '(' {hspace} left+:expression {hspace} {',' {hspace} left+:expression {hspace}} ')' {hspace} '∉' {hspace} right:(function_operator | identifier)
    | left+:expression {hspace} '∉' {hspace} right:(function_operator | identifier)
    ;

not_equal::NeCondition
    = 
    left:expression {hspace} op:('≠' | '!=') {hspace} right:expression
    ;

equal::EqCondition
    = 
    left:expression {hspace} op:('==' | '=') {hspace} right:expression
    ;

greater::GreaterCondition
    = 
    left:expression {hspace} op:'>' {hspace} right:expression
    ;

greater_equal::GreaterEqualCondition
    = 
    left:expression {hspace} op:('>=' | '≥'| '⩾') {hspace} right:expression
    ;   

less::LessCondition
    = 
    left:expression {hspace} op:'<' {hspace} right:expression
    ;

less_equal::LessEqualCondition
    = 
    left:expression {hspace} op:('<=' | '≤'| '⩽') {hspace} right:expression
    ;
"""