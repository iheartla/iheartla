NUMBER = r"""
# number definition

exponent::Exponent
    = 
    exp:/[E][+-]?/ pow:{digit}+
    ;

mantissa::Mantissa
    = 
    (d:{digit}* '.' f:{digit}+) | (d:{digit}+ '.')
    ;

floating_point::Float
    = 
    m:mantissa e:[exponent]
    ;

double::Double
    = 
    i:integer exp:exponent
    | f:floating_point
    ;

fraction::Fraction
    = 
    value:/[\u00BC-\u00BE\u2150-\u215E]/
    ;

number
    =
    | double
    | fraction
    | integer
    ;
"""