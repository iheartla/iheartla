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

SIMPLIFIED = START + KEYWORDS + NUMBER + OPERATORS + MATRIX + BASE + TRIGONOMETRY + GEOMETRY + SHARED + ARITHMETIC + TYPES + SET_OPERATORS
#include :: "keywords.ebnf"
#include :: "number.ebnf"
#include :: "operators.ebnf"
#include :: "matrix.ebnf"
#include :: "base.ebnf"
#include :: "trigonometry.ebnf"
#include :: "shared.ebnf"

SIMPLIFIED += r"""
func_id=identifier_alone {'_' identifier_alone};

identifier_alone::IdentifierAlone
    = !KEYWORDS(  value:(/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*/) | '`' id:/[^`]*/ '`')
    | value:(KEYWORDS (/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*/))
    ;

identifier
    = identifier_with_multi_subscript
    | identifier_with_subscript
    | identifier_alone
    ;
    
# handle _ in identifier
identifier_with_multi_subscript::IdentifierSubscript
    = left:identifier_alone {'_' right+:identifier_alone }+ ({
    (',' right+:'*')
    | ({','} right+:(integer | identifier_alone)) }
    |
    {
    (',' right+:'*')
    | ({','} right+:(sub_integer|unicode_subscript)) }
    ); 
    
#function_operator::Function
    #= #name:func_id {order+:PRIME}+ {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    #| name:func_id (d:UDDOT | s:UDOT) {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    #name:func_id p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    #;
function_operator::Function
    = #name:func_id {order+:PRIME}+ {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    #| name:func_id (d:UDDOT | s:UDOT) {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    name:func_id '_' subs+:(integer|identifier_alone) {{','} subs+:(integer|identifier_alone)} {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    | name:func_id p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    | name:func_id  subs+:(sub_integer|unicode_subscript) {{','} subs+:(sub_integer|unicode_subscript)} {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    ;
"""