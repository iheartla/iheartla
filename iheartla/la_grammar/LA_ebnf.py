from .keywords_ebnf import KEYWORDS
from .number_ebnf import NUMBER
from .operators_ebnf import OPERATORS
from .matrix_ebnf import MATRIX
from .base_ebnf import BASE
from .trigonometry_ebnf import TRIGONOMETRY
from .shared_ebnf import SHARED
LA = r"""
@@grammar::LA
@@whitespace :: /(?!.*)/     #parse whitespace manually
@@left_recursion::True

start::Start
    = {separator_with_space} {directive+:Directive {{separator_with_space}+ directive+:Directive} {separator_with_space}+}
    {{separator_with_space} vblock+:valid_block {separator_with_space}}+ {blank} $
    ;
""" + KEYWORDS + NUMBER + OPERATORS + MATRIX + BASE + TRIGONOMETRY + SHARED
#include :: "keywords.ebnf"
#include :: "number.ebnf"
#include :: "operators.ebnf"
#include :: "matrix.ebnf"
#include :: "base.ebnf"
#include :: "trigonometry.ebnf"
#include :: "shared.ebnf"
LA += r"""
valid_block
    = params_block | statements
    ;


params_block::ParamsBlock
    = {annotation:(WHERE | GIVEN ) {separator_with_space}+} conds:where_conditions
    ;

builtin_operators
    =
    predefined_built_operators;

statements::Statements
    =
    #| {hspace} stats:statements {separator_with_space}+ stat:statement {hspace}
    {hspace} stat:statement {hspace}
    ;

statement
    =
    | assignment
    | right_hand_side
    ;


expression::Expression
    =
    | value:addition
    | value:subtraction
    | value:add_sub_operator
    | sign:['-'] value:term
    #| {}
    ;

assignment::Assignment
    =
    left:identifier {hspace} op:'=' {hspace} {separator_with_space} right:right_hand_side {hspace}
    | left:identifier {hspace} op:'+=' {hspace} {separator_with_space} right:right_hand_side {hspace}
    ;

right_hand_side
    =
    | expression
    | optimize_operator
    ;

term
    =
    | multiplication
    | division
    | factor
    ;

func_id='!!!';

identifier_alone::IdentifierAlone
    = !KEYWORDS( value:/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*/ | '`' id:/[^`]*/ '`')
    #= !KEYWORDS( value:/[\p{Ll}\p{Lu}\p{Lo}|\u006d|ᵢ]\p{M}*/ | '`' id:/[^`]*/ '`')
    #= !KEYWORDS( value:/[A-Za-z\p{Ll}\p{Lu}\p{Lo}\p{Lm}\p{No}]\p{M}*/ | '`' id:/[^`]*/ '`')
    #= const:('abc'|'sss') | (!(KEYWORDS |'abc'|'sss' ) value:/[A-Za-z\p{Ll}|\p{Lu}|\p{Lo}]/ | '`' id:/[^`]*/ '`')
    # !KEYWORDS value:/[^`;\n\r\f_\d]/ | '`' id:/[^`]*/ '`'
    #= !KEYWORDS value:/[A-Za-z]/ | '`' id:/[\p{L}\p{M}A-Za-z0-9\s\u2190-\u21FF\u1000-\uFFFFF]*/ '`'
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
    | s:sparse_matrix
    | c:constant
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

if_condition::IfCondition
    =
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
    = left:expression {hspace} op:('>=' | '⩾') {hspace} right:expression
    ;

less::LessCondition
    = left:expression {hspace} op:'<' {hspace} right:expression
    ;

less_equal::LessEqualCondition
    = left:expression {hspace} op:('<=' | '⩽') {hspace} right:expression
    ;
"""