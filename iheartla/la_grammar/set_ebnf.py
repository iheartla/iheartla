SET_OPERATORS = r"""
set_operators
    = 
    union_operator
    | intersect_operator
    ;

union_operator::Union
    = 
    left:factor {hspace} '∪' {hspace} right:factor
    ;
    
intersect_operator::Intersection
    = 
    left:factor {hspace} '∩' {hspace} right:factor
    ;
"""