from .de_keywords_ebnf import DKEYWORDS
from .de_number_ebnf import DNUMBER
from .de_operators_ebnf import DOPERATORS
from .de_matrix_ebnf import DMATRIX
from .de_base_ebnf import DBASE
from .de_trigonometry_ebnf import DTRIGONOMETRY
from .de_shared_ebnf import DSHARED
from .de_arithmetic_ebnf import DARITHMETIC
from .de_types_ebnf import DTYPES
from .de_geometry_ebnf import DGEOMETRY
from .de_set_ebnf import DSET_OPERATORS
from .de_ebnf import DSTART
DGRAMMAR = r"""
@@grammar::LA
"""
DSIMPLIFIED_LIST = [DGRAMMAR, DSTART, DKEYWORDS, DNUMBER, DOPERATORS, DMATRIX, DBASE, DTRIGONOMETRY, DSHARED, DARITHMETIC, DTYPES, DSET_OPERATORS]
DSIMPLIFIED = "\n\n".join(DSIMPLIFIED_LIST) + "\n\n"
#include :: "keywords.ebnf"
#include :: "number.ebnf"
#include :: "operators.ebnf"
#include :: "matrix.ebnf"
#include :: "base.ebnf"
#include :: "trigonometry.ebnf"
#include :: "shared.ebnf"

DSIMPLIFIED += r"""
func_id
    =
    INVERSEVEC
    | identifier_alone {'_' (identifier_alone | integer) | unicode_subscript}
    ;

# be careful on ?: inside the parenthesis
identifier_alone::IdentifierAlone
    = !KEYWORDS(  value:(/[A-Za-z\p{Ll}\p{Lu}\p{Lo}](?![\u0308\u0307])\p{M}*(?:[A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}](?![\u0308\u0307])\p{M}*)*/|/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*(?=[\u0308\u0307])(?:[A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*(?=[\u0308\u0307]))*/) | '`' id:/[^`]*/ '`')
    | value:(PREFIX_KEYWORD (/[A-Za-z\p{Ll}\p{Lu}\p{Lo}](?![\u0308\u0307])\p{M}*(?:[A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}](?![\u0308\u0307])\p{M}*)*/|/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*(?=[\u0308\u0307])(?:[A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*(?=[\u0308\u0307]))*/))
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
    | name:func_id {order+:PRIME}+ {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    | name:func_id (d:UDDOT | s:UDOT) {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
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