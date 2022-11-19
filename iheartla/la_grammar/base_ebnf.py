BASE = r"""
#base
hspace
    = ' ' | '\t'
    ;

line
    = '\n' | '\r' | '\f'
    ;

lines
    = {line}+
    ;

identifier_with_subscript::IdentifierSubscript
    = (left:identifier_alone '_' right+:(integer | '*' | identifier_alone) {
    (',' right+:'*')
    | ({','} right+:(integer | identifier_alone)) } )
    |
    ( left:identifier_alone right+:(sub_integer|unicode_subscript) {
    (',' right+:'*')
    | ({','} right+:(sub_integer|unicode_subscript)) } )
    ;
    
# /ₐₑₒₓₕₖₗₘₙₚₛₜ/
unicode_subscript::IdentifierAlone
    = value:/[\u2090-\u209C]/
    ;

size_op::SizeOp
    = POUND i:identifier
    ;
    
keyword_str
    = /[A-Za-z][A-Za-z0-9]*/
    ;
    
    
multi_str::IdentifierAlone
    = !KEYWORDS(  value:(/[A-Za-z_\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z_\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*/) | '`' id:/[^`]*/ '`')
    | value:(KEYWORDS (/[A-Za-z_\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z_\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*/))
    ;

description
    = /[^;\n\r\f]*/
    ;

desc_identifier
    = !KEYWORDS '`' /[A-Za-z][[A-Za-z0-9]*/ '`'
    ;

separator
    =
    | line
    | ';'
    ;

separator_with_space
    = {hspace} separator {hspace}
    ;

blank
    = {(hspace | separator)}
    ;

params_separator
    = ','|';'|'x'|'×'
    ;

pi::Pi
    = /π/
    ;

e::E
    = /e/
    ;
    
"""