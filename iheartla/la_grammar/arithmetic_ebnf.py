ARITHMETIC = r"""
arithmetic_expression::ArithExpression
    = 
    | value:arithmetic_addition
    | value:arithmetic_subtraction
    | sign:['-'] value:arithmetic_term
    ;
    
arithmetic_addition::ArithAdd
    =
    left:arithmetic_expression {hspace} op:'+' {hspace} right:arithmetic_term
    ;
    
arithmetic_subtraction::ArithSubtract
    =
    left:arithmetic_expression {hspace} op:'-' {hspace} right:arithmetic_term
    ;
    
arithmetic_term
    =
    | arithmetic_multiplication
    | arithmetic_division
    | arithmetic_factor
    ;
    
arithmetic_multiplication::ArithMultiply
    =
    left:arithmetic_term {hspace} op:'⋅' {hspace} right:arithmetic_factor
    | left:arithmetic_term {hspace} right:arithmetic_factor
    ;

arithmetic_division::ArithDivide
    =
    left:arithmetic_term {hspace} op:('/'|'÷') {hspace} right:arithmetic_factor
    ;
    
arithmetic_factor::ArithFactor
    =
    sub:arithmetic_subexpression
    | size:size_op
    | id0:identifier
    | num:number
    ;

arithmetic_subexpression::ArithSubexpression
    =
    '(' {hspace} value:arithmetic_expression {hspace} ')'
    ;
"""