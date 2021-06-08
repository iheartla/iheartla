from .keywords_ebnf import KEYWORDS
from .number_ebnf import NUMBER
from .operators_ebnf import OPERATORS
from .matrix_ebnf import MATRIX
from .base_ebnf import BASE
from .trigonometry_ebnf import TRIGONOMETRY
from .shared_ebnf import SHARED
from .arithmetic_ebnf import ARITHMETIC
START = r"""
@@grammar::LA
@@whitespace :: /(?!.*)/     #parse whitespace manually
@@left_recursion::True

start::Start
    = {separator_with_space} {hspace} {directive+:Directive {{separator_with_space}+ directive+:Directive} {separator_with_space}+}
    {{separator_with_space} {hspace} vblock+:valid_block {separator_with_space}}+ {blank} $
    ;
"""
LA = START + KEYWORDS + NUMBER + OPERATORS + MATRIX + BASE + TRIGONOMETRY + SHARED + ARITHMETIC
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
    = !KEYWORDS( value:/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*/ | '`' id:/[^`]*/ '`')
    #= const:('abc'|'sss') | (!(KEYWORDS |'abc'|'sss' ) value:/[A-Za-z\p{Ll}|\p{Lu}|\p{Lo}]/ | '`' id:/[^`]*/ '`')
    ;
"""