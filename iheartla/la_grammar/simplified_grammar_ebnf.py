from .keywords_ebnf import KEYWORDS
from .number_ebnf import NUMBER
from .operators_ebnf import OPERATORS
from .matrix_ebnf import MATRIX
from .base_ebnf import BASE
from .trigonometry_ebnf import TRIGONOMETRY
from .shared_ebnf import SHARED
from .LA_ebnf import START

SIMPLIFIED = START + KEYWORDS + NUMBER + OPERATORS + MATRIX + BASE + TRIGONOMETRY + SHARED
#include :: "keywords.ebnf"
#include :: "number.ebnf"
#include :: "operators.ebnf"
#include :: "matrix.ebnf"
#include :: "base.ebnf"
#include :: "trigonometry.ebnf"
#include :: "shared.ebnf"

SIMPLIFIED += r"""
func_id=identifier_alone;

identifier_alone::IdentifierAlone
    = !KEYWORDS(  value:/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*/ | '`' id:/[^`]*/ '`')
    ;
"""