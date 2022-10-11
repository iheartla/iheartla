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
START = r"""
@@grammar::LA
@@whitespace :: /(?!.*)/     #parse whitespace manually
@@left_recursion::True

start::Start
    = {{separator_with_space} {hspace} vblock+:valid_block {separator_with_space}}+ {blank} $
    ;
"""
LA = START + KEYWORDS + NUMBER + OPERATORS + MATRIX + BASE + TRIGONOMETRY + GEOMETRY + SHARED + ARITHMETIC + TYPES
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
    = !KEYWORDS( value:(/[A-Za-z\p{Ll}\p{Lu}\p{Lo}](?![\u0308\u0307])\p{M}*/|/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*(?=[\u0308\u0307])/) | '`' id:/[^`]*/ '`')
    #= const:('abc'|'sss') | (!(KEYWORDS |'abc'|'sss' ) value:/[A-Za-z\p{Ll}|\p{Lu}|\p{Lo}]/ | '`' id:/[^`]*/ '`')
    ;

function_operator::Function
    = name:func_id {order+:PRIME}+ {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    | name:func_id (d:UDDOT | s:UDOT) {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    | name:func_id {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    ;
"""