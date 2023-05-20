BASE = r"""
#base
hspace
    = 
    /[ \t]/
    ;

line
    = 
    '\n' | '\r' | '\f'
    ;

lines
    = 
    {line}+
    ;

identifier_with_subscript::IdentifierSubscript
    = 
    (left:identifier_alone '_' right+:(integer | '*' | identifier_alone) {
    (',' right+:'*')
    | ({','} right+:(integer | identifier_alone)) } )
    |
    (left:identifier_alone p:'_(' right+:(integer | '*' | identifier_alone) {
    (',' right+:'*')
    | ({','} right+:(integer | identifier_alone)) } ')' )
    |
    ( left:identifier_alone right+:(sub_integer|unicode_subscript) {
    (',' right+:'*')
    | ({','} right+:(sub_integer|unicode_subscript)) } )
    |
    (left:identifier_alone p:'_(' {hspace} exp+:('*' | expression) {
    ({hspace} ',' {hspace} exp+:'*')
    | ({hspace} ',' {hspace} exp+:expression) } {hspace} ')' )
    ;
    
identifier_with_unicode_subscript::IdentifierSubscript
    = 
    left:identifier_alone right+:(sub_integer|unicode_subscript) {
    (',' right+:'*')
    | ({','} right+:(sub_integer|unicode_subscript)) }
    ;
    
# /ₐₑₒₓₕₖₗₘₙₚₛₜ/ \u1D62(ᵢ) \u2C7C(ⱼ)
unicode_subscript::IdentifierAlone
    = 
    value:/[\u2090-\u209C\u1D62\u2C7C]/
    ;

#\u1D43(ᵃ) \u1D47(ᵇ) \u1D9C(ᶜ) \u1D48(ᵈ) \u1D49(ᵉ) \u1DA0(ᶠ) \u1D4D(ᵍ) \u02B0(ʰ) \u2071(ⁱ) \u02B2(ʲ) \u1D4F(ᵏ)
#\u02E1(ˡ) \u1D50(ᵐ) \u207F(ⁿ) \u1D52(ᵒ) \u1D56(ᵖ) \u02B3(ʳ) \u02E2(ˢ) \u1D57(ᵗ) \u1D58(ᵘ) \u1D5B(ᵛ) \u02B7(ʷ) 
#\u02E3(ˣ) \u02B8(ʸ) \u1DBB(ᶻ) \u1DA6(ᶦ) \u1DAB(ᶫ) \u1DB0(ᶰ) \u1DB8(ᶸ) 
#\u1D2C(ᴬ) \u1D2E(ᴮ) \u1D30(ᴰ) \u1D31(ᴱ) \u1D33(ᴳ) \u1D34(ᴴ) \u1D35(ᴵ) \u1D36(ᴶ) \u1D37(ᴷ) \u1D38(ᴸ) \u1D39(ᴹ)
#\u1D3A(ᴺ) \u1D3C(ᴼ) \u1D3E(ᴾ) \u1D3F(ᴿ) \u1D40(ᵀ) \u1D41(ᵁ) \u2C7D(ⱽ) \u1D42(ᵂ)
unicode_superscript::IdentifierAlone
    = 
    value:/[\u1D43\u1D47\u1D9C\u1D48\u1D49\u1DA0\u1D4D\u02B0\u2071\u02B2\u1D4F\u02E1\u1D50\u207F\u1D52\u1D56\u02B3\u02E2\u1D57\u1D58\u1D5B\u02B7\u02E3\u02B8\u1DBB\u1DA6\u1DAB\u1DB0\u1DB8\u1D2C\u1D2E\u1D30\u1D31\u1D33\u1D34\u1D35\u1D36\u1D37\u1D38\u1D39\u1D3A\u1D3C\u1D3E\u1D3F\u1D40\u1D41\u2C7D\u1D42]/
    ;

size_op::SizeOp
    = 
    POUND i:identifier
    ;
    
keyword_str
    = 
    /[A-Za-z][A-Za-z0-9]*/
    ;
    
    
multi_str::IdentifierAlone
    = 
    !KEYWORDS(  value:(/[A-Za-z_\p{Ll}\p{Lu}\p{Lo}]\p{M}*(?:[⁻¹A-Z0-9a-z_\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*/) | '`' id:/[^`]*/ '`')
    | value:(PREFIX_KEYWORD (/[A-Za-z_\p{Ll}\p{Lu}\p{Lo}]\p{M}*(?:[⁻¹A-Z0-9a-z_\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*/))
    ;

description
    = 
    /[^;\n\r\f]*/
    ;

desc_identifier
    = 
    !KEYWORDS '`' /[A-Za-z][[A-Za-z0-9]*/ '`'
    ;

separator
    =
    | line
    | ';'
    ;

separator_with_space
    = 
    {hspace} separator {hspace}
    ;

blank
    = 
    {(hspace | separator)}
    ;


# ×
params_separator
    = 
    /[,;x\u00D7]/
    ;

pi::Pi
    = 
    /π/
    ;

infinity::Infinity
    = 
    /∞/
    ;

e::E
    = 
    /e/
    ;
    
"""