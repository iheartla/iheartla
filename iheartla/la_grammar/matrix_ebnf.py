MATRIX = r"""
#matrix
matrix::Matrix
    = 
    '[' {hspace} value:rows {hspace} ']'
    | '⎡' {hspace} value:rows {hspace} '⎦'
    ;

vector::Vector            
    = 
    '(' {hspace} exp+:expression {{hspace} ',' {hspace} exp+:expression}+ {hspace} ')'
    ;

set::Set            
    = 
    '{' {hspace} exp+:expression {{hspace} ',' {hspace} exp+:expression} {hspace} '}'
    | '{' {hspace} exp+:expression {hspace} f:(FOR|/∀/) {hspace} enum+:identifier_alone {{hspace} {','} {hspace} enum+:identifier_alone} {hspace} 
    IN {hspace} range:(function_operator | builtin_operators | identifier_alone) {hspace} {IF {hspace} cond:if_condition {hspace}}  '}'
    | '{' {hspace} exp+:expression {hspace} o:/\|/ {hspace} enum+:identifier_alone {{hspace} {','} {hspace} enum+:identifier_alone} {hspace} 
    IN {hspace} range:(function_operator | builtin_operators | identifier_alone) {hspace} {',' {hspace} cond:if_condition {hspace}}   '}'
    ;
    
multi_cond_expr::MultiCondExpr
    = 
    '{' {hspace} ifs:multi_if_conditions
    [{separator_with_space}+ {hspace} other:expression {hspace} OTHERWISE ]
    ;
    
multi_if_conditions::MultiIfs
    = 
    ifs:multi_if_conditions {separator_with_space}+ value:single_if_condition
    | value:single_if_condition
    ;

single_if_condition::SingleIf
    = 
    stat:expression {hspace} IF {hspace} cond:if_condition
    | cond:if_condition  {hspace} ':' {hspace} stat:expression
    ;

rows::MatrixRows
    =
    | rs:rows {separator_with_space}+ r:row {hspace}
    | rs:rows {separator_with_space}+
    | r:row {hspace}
    ;

row::MatrixRow
    = 
    '|' {hspace} value+:row {hspace} '|'
    | rc:row_with_commas {hspace} exp:expr_in_matrix
    | rc:row_with_commas
    | exp:expr_in_matrix
    ;

row_with_commas::MatrixRowCommas
    =
    | value:row_with_commas {hspace} exp:expr_in_matrix ({hspace} ',' | {hspace}+)
    | {hspace} exp:expr_in_matrix ({hspace} ',' | {hspace}+)
    ;

expr_in_matrix::ExpInMatrix
    =
    | value:addition_in_matrix
    | value:subtraction_in_matrix
    | sign:['-'] value:term_in_matrix
    ;

addition_in_matrix::Add
    =
    left:expr_in_matrix op:'+' right:term_in_matrix
    ;


subtraction_in_matrix::Subtract
    =
    left:expr_in_matrix op:'-' right:term_in_matrix
    ;


term_in_matrix
    =
    | multiplication_in_matrix
    | division_in_matrix
    | factor_in_matrix
    ;

multiplication_in_matrix::Multiply
    = 
    left:term_in_matrix op:'⋅' right:factor_in_matrix
    | left:term_in_matrix right:factor_in_matrix
    ;

division_in_matrix::Divide
    =
    left:term_in_matrix  op:('/'|'÷') right:factor_in_matrix
    ;

number_matrix::NumMatrix
    = 
    left:('0' | '1' | '𝟙') '_' id1:(integer | identifier) {',' id2:(integer | identifier)}
    | left:/[01\u1D7D9]/ id1:sub_integer {',' id2:sub_integer}
    | left:('0' | '1' | '𝟙') '_' '(' {hspace}  id1:(integer | identifier) { {hspace} (','|'×') {hspace} id2:(integer | identifier)} {hspace} ')'
    #| id:'I' '_' id1:(integer | identifier)
    #| id:/[I]/ id1:sub_integer
    ;

factor_in_matrix::Factor
    =
    | op:operations_in_matrix
    | sub:subexpression
    | nm:number_matrix
    | id0:identifier
    | num:number
    | m:matrix
    | v:vector
    | s:set
    | c:constant
    ;

operations_in_matrix
    =
    | solver_in_matrix_operator
    | norm_operator
    | power_in_matrix_operator
    | inner_product_operator
    | frobenius_product_in_matrix_operator
    | hadamard_product_in_matrix_operator
    | cross_product_in_matrix_operator
    | kronecker_product_in_matrix_operator
    | sum_in_matrix_operator
    | integral_operator
    | trans_in_matrix_operator
    | sqrt_in_matrix_operator
    | function_operator
    | builtin_operators
    | pseudoinverse_in_matrix_operator
    ;

power_in_matrix_operator::Power
    = 
    base:factor_in_matrix t:'^T'
    | base:factor_in_matrix r:('^(-1)' | '⁻¹')
    | base:factor_in_matrix '^' power:factor_in_matrix
    | base:factor_in_matrix power:sup_integer
    ;


frobenius_product_in_matrix_operator::FroProduct
    = 
    left:factor_in_matrix  ':' right:factor_in_matrix
    ;

hadamard_product_in_matrix_operator::HadamardProduct
    = 
    left:factor_in_matrix  '∘'  right:factor_in_matrix
    ;

cross_product_in_matrix_operator::CrossProduct
    = 
    left:factor_in_matrix '×'   right:factor_in_matrix
    ;

kronecker_product_in_matrix_operator::KroneckerProduct
    = 
    left:factor_in_matrix '⊗' right:factor_in_matrix
    ;

trans_in_matrix_operator::Transpose
    = 
    f:factor_in_matrix /ᵀ/
    ;

pseudoinverse_in_matrix_operator::PseudoInverse
    = 
    f:factor_in_matrix /⁺/
    ;
    
sqrt_in_matrix_operator::Squareroot
    = 
    /√/ f:factor_in_matrix
    ;

solver_in_matrix_operator::Solver
    = 
    left:factor_in_matrix '\' right:factor_in_matrix
    | left:factor_in_matrix p:('^(-1)' | '⁻¹') right:factor_in_matrix
    ;

sum_in_matrix_operator::Summation
    = 
    SUM '_' sub:identifier_alone &'(' {hspace} exp:term_in_matrix
    | SUM '_(' {hspace} id:identifier_alone {hspace} 'for' {hspace} cond:if_condition {hspace} ')' exp:term_in_matrix
    | SUM '_(' {hspace} enum+:identifier_alone {{hspace} ',' {hspace} enum+:identifier_alone} {hspace} IN {hspace} range:(function_operator | identifier_alone) {hspace} ')' exp:term
    ;
"""