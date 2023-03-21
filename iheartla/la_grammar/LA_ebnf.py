from .keywords_ebnf import KEYWORDS
from .number_ebnf import NUMBER
from .operators_ebnf import OPERATORS
from .matrix_ebnf import MATRIX
from .base_ebnf import BASE
from .trigonometry_ebnf import TRIGONOMETRY
from .shared_ebnf import SHARED
from .arithmetic_ebnf import ARITHMETIC
from ..la_grammar.types_ebnf import TYPES
from .geometry_ebnf import GEOMETRY
from .set_ebnf import SET_OPERATORS
GRAMMAR = r"""
@@grammar::LA
"""
START = r"""
@@whitespace :: /(?!.*)/     #parse whitespace manually
@@left_recursion::True

start::Start
    = 
    {{separator_with_space} {hspace} vblock+:valid_block {separator_with_space}}+ {blank} $
    ;
"""
LA_LIST = [GRAMMAR, START, KEYWORDS, NUMBER, OPERATORS, MATRIX, BASE, TRIGONOMETRY, SHARED, ARITHMETIC, TYPES, SET_OPERATORS]
LA = "\n\n".join(LA_LIST) + "\n\n"
#include :: "keywords.ebnf"
#include :: "number.ebnf"
#include :: "operators.ebnf"
#include :: "matrix.ebnf"
#include :: "base.ebnf"
#include :: "trigonometry.ebnf"
#include :: "shared.ebnf"
LA += r"""
func_id
    =
    '!!!'
    ;

identifier_alone::IdentifierAlone
    = 
    !KEYWORDS( value:(/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*/) | '`' id:/[^`]*/ '`')
    | value:(PREFIX_KEYWORD (/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*/))
    #= const:('abc'|'sss') | (!(KEYWORDS |'abc'|'sss' ) value:/[A-Za-z\p{Ll}|\p{Lu}|\p{Lo}]/ | '`' id:/[^`]*/ '`')
    ;

identifier
    = 
    identifier_with_subscript
    | identifier_alone
    ;

function_operator::Function
    = 
    name:func_id '_' subs+:(integer|identifier_alone) {{','} subs+:(integer|identifier_alone)} {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    | name:func_id p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    | name:func_id  subs+:(sub_integer|unicode_subscript) {{','} subs+:(sub_integer|unicode_subscript)} {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    ;
    
# It's so weird that the commented rules below won't work, I guess identifier_alone and unicode_subscript must be combined
local_func::LocalFunc
    = 
    (
    name:identifier_with_unicode_subscript {def_p:/\(/ {{hspace} params+:identifier_alone {{hspace} separators+:params_separator {hspace} params+:identifier_alone}} {hspace} ')'}
    | name:identifier_with_unicode_subscript {def_s:/\[/ {{hspace} params+:identifier_alone {{hspace} separators+:params_separator {hspace} params+:identifier_alone}} {hspace} ']'}
    | name:identifier_alone {'_' subs+:identifier_alone {{','} subs+:identifier_alone}} {def_p:/\(/ {{hspace} params+:identifier_alone {{hspace} separators+:params_separator {hspace} params+:identifier_alone}} {hspace} ')'} 
    #| name:identifier_alone {subs+:unicode_subscript {{','} subs+:unicode_subscript}} {def_p:/\(/ {{hspace} params+:identifier_alone {{hspace} separators+:params_separator {hspace} params+:identifier_alone}} {hspace} ')'}
    | name:identifier_alone {'_' subs+:identifier_alone {{','} subs+:identifier_alone}} {def_s:/\[/ {{hspace} params+:identifier_alone {{hspace} separators+:params_separator {hspace} params+:identifier_alone}} {hspace} ']'} 
    #| name:identifier_alone {subs+:unicode_subscript {{','} subs+:unicode_subscript}} {def_s:/\[/ {{hspace} params+:identifier_alone {{hspace} separators+:params_separator {hspace} params+:identifier_alone}} {hspace} ']'}
    ) 
    {hspace} op:'=' {hspace} expr+:right_hand_side [{hspace} line] {hspace} (WHERE | GIVEN ) {hspace} defs+:where_condition {{hspace} ',' {hspace} defs+:where_condition} {{hspace} ',' {hspace} [line] {hspace} extra+:general_assign}
     ;
"""