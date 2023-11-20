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
DGRAMMAR = r"""
@@grammar::LA
"""
DSTART = r"""
@@whitespace :: /(?!.*)/     #parse whitespace manually
@@left_recursion::True

start::Start
    = 
    {{separator_with_space} {hspace} vblock+:valid_block {separator_with_space}}+ {blank} $
    ;
"""
DE_LIST = [DGRAMMAR, DSTART, DKEYWORDS, DNUMBER, DOPERATORS, DMATRIX, DBASE, DTRIGONOMETRY, DSHARED, DARITHMETIC, DTYPES, DSET_OPERATORS]
DE = "\n\n".join(DE_LIST) + "\n\n"
#include :: "keywords.ebnf"
#include :: "number.ebnf"
#include :: "operators.ebnf"
#include :: "matrix.ebnf"
#include :: "base.ebnf"
#include :: "trigonometry.ebnf"
#include :: "shared.ebnf"
DE += r"""
func_id
    =
    '!!!'
    ;

identifier_alone::IdentifierAlone
    = 
    !KEYWORDS( value:(/[A-Za-z\p{Ll}\p{Lu}\p{Lo}](?![\u0308\u0307])\p{M}*/|/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*(?=[\u0308\u0307])/) | '`' id:/[^`]*/ '`')
    | value:(PREFIX_KEYWORD (/[A-Za-z\p{Ll}\p{Lu}\p{Lo}](?![\u0308\u0307])\p{M}*/|/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*(?=[\u0308\u0307])/))
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
    | name:func_id {order+:PRIME}+ {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
    | name:func_id (d:UDDOT | s:UDOT) {p:'(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'}
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