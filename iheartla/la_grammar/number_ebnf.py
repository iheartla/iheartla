NUMBER = r"""
# number definition

exponent::Exponent
    = exp:/[E][+-]?/ pow:{digit}+
    ;

mantissa::Mantissa
    = (d:{digit}* '.' f:{digit}+) | (d:{digit}+ '.')
    ;

floating_point::Float
    = m:mantissa e:[exponent]
    ;

double::Double
    = i:integer exp:exponent
    | f:floating_point
    ;

number
    =
    | double
    | integer
    ;
"""