from .keywords_ebnf import KEYWORDS
from .number_ebnf import NUMBER
from .operators_ebnf import OPERATORS
from .matrix_ebnf import MATRIX
from .base_ebnf import BASE
from .trigonometry_ebnf import TRIGONOMETRY
from .shared_ebnf import SHARED
from .LA_ebnf import START
from .arithmetic_ebnf import ARITHMETIC
from ..la_grammar.types_ebnf import TYPES
from .geometry_ebnf import GEOMETRY
from .set_ebnf import SET_OPERATORS
GRAMMAR = r"""
@@grammar::LA
"""
SIMPLIFIED_LIST = [GRAMMAR, START, KEYWORDS, NUMBER, OPERATORS, MATRIX, BASE, TRIGONOMETRY, SHARED, ARITHMETIC, TYPES, SET_OPERATORS]
SIMPLIFIED = "\n\n".join(SIMPLIFIED_LIST) + "\n\n"
#include :: "keywords.ebnf"
#include :: "number.ebnf"
#include :: "operators.ebnf"
#include :: "matrix.ebnf"
#include :: "base.ebnf"
#include :: "trigonometry.ebnf"
#include :: "shared.ebnf"

SIMPLIFIED += r"""
func_id
    =
    INVERSEVEC
    | identifier_alone {'_' (identifier_alone | integer) | unicode_subscript}
    ;

identifier_alone::IdentifierAlone
    = !KEYWORDS(  value:(/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*(?:[A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*/) | '`' id:/[^`]*/ '`')
    | value:(PREFIX_KEYWORD (/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*(?:[A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*/))
    ;

identifier
    = 
    identifier_with_multi_subscript
    | identifier_with_subscript
    | identifier_alone
    ;
    
# handle _ in identifier
identifier_with_multi_subscript::IdentifierSubscript
    = 
    left:identifier_alone {'_' right+:(identifier_alone | integer | BUILTIN_KEYWORDS) }+ ({
    (',' right+:'*')
    | ({','} right+:(integer | identifier_alone)) }
    |
    {
    (',' right+:'*')
    | ({','} right+:(sub_integer|unicode_subscript)) }
    ); 
    
function_operator::Function
    = 
    name:func_id '_' subs+:(integer|identifier_alone) {{','} subs+:(integer|identifier_alone)} {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    | name:func_id p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    | name:func_id  subs+:(sub_integer|unicode_subscript) {{','} subs+:(sub_integer|unicode_subscript)} {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    ;
    
local_func::LocalFunc
    = 
    (
    name:identifier {def_p:/\(/ {{hspace} params+:identifier_alone {{hspace} separators+:params_separator {hspace} params+:identifier_alone}} {hspace} ')'} 
    | name:identifier {def_s:/\[/ {{hspace} params+:identifier_alone {{hspace} separators+:params_separator {hspace} params+:identifier_alone}} {hspace} ']'}
    ) 
    {hspace} op:'=' {hspace} expr+:right_hand_side [{hspace} line] {hspace} (WHERE | GIVEN ) {hspace} defs+:where_condition {{hspace} ',' {hspace} defs+:where_condition} {{hspace} ',' {hspace} [line]  {hspace} extra+:general_assign}
     ;
"""