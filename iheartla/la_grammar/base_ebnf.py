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

identifier
    = identifier_with_subscript
    | identifier_alone
    ;

identifier_with_subscript::IdentifierSubscript
    = (left:identifier_alone '_' right+:(integer | '*' | identifier_alone) {
    (',' right+:'*')
    | ({','} right+:(integer | identifier_alone)) } )
    |
    ( left:identifier_alone right+:sub_integer {
    (',' right+:'*')
    | ({','} right+:(sub_integer)) } )
    ;


keyword_str
    = /[A-Za-z][A-Za-z0-9]*/
    ;
    
multi_str::IdentifierAlone
    = (  value:/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*/ | '`' id:/[^`]*/ '`')
    ;

description
    = /[^`;\n\r\f]*/
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