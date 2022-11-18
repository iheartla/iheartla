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
START = r"""
@@grammar::LA
@@whitespace :: /(?!.*)/     #parse whitespace manually
@@left_recursion::True

start::Start
    = {{separator_with_space} {hspace} vblock+:valid_block {separator_with_space}}+ {blank} $
    ;
"""
LA = START + KEYWORDS + NUMBER + OPERATORS + MATRIX + BASE + TRIGONOMETRY + GEOMETRY + SHARED + ARITHMETIC + TYPES + SET_OPERATORS
#include :: "keywords.ebnf"
#include :: "number.ebnf"
#include :: "operators.ebnf"
#include :: "matrix.ebnf"
#include :: "base.ebnf"
#include :: "trigonometry.ebnf"
#include :: "shared.ebnf"
LA += r"""
func_id='!!!';

identifier_alone::IdentifierAlone
    = !KEYWORDS( value:(/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*/) | '`' id:/[^`]*/ '`')
    | value:(KEYWORDS (/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*/))
    #= const:('abc'|'sss') | (!(KEYWORDS |'abc'|'sss' ) value:/[A-Za-z\p{Ll}|\p{Lu}|\p{Lo}]/ | '`' id:/[^`]*/ '`')
    ;

identifier
    = identifier_with_subscript
    | identifier_alone
    ;

function_operator::Function
    = #name:func_id {order+:PRIME}+ {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    #| name:func_id (d:UDDOT | s:UDOT) {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    (
    name:func_id {'_' subs+:(integer|identifier_alone) {{','} subs+:(integer|identifier_alone)}} 
    | name:func_id  {subs+:(sub_integer|unicode_subscript) {{','} subs+:(sub_integer|unicode_subscript)}}
    )
    {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    ;
"""