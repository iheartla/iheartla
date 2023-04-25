OPERATORS = r"""
# operators
operations
    =
    | size_op
    | derivative
    | partial
    | divergence
    | gradient
    | laplacian
    | solver_operator
    | norm_operator
    | power_operator
    | inner_product_operator
    | frobenius_product_operator
    | hadamard_product_operator
    | cross_product_operator
    | kronecker_product_operator
    | set_operators
    | sum_operator
    | integral_operator
    | trans_operator
    | sqrt_operator
    | function_operator
    | builtin_operators
    | pseudoinverse_operator
    ;


addition::Add
    =
    left:expression {hspace} op:'+' {hspace} right:term
    ;


subtraction::Subtract
    =
    left:expression {hspace} op:'-' {hspace} right:term
    ;

add_sub_operator::AddSub
    =
    left:expression {hspace} op:('+-'|'±') {hspace} right:term
    ;


multiplication::Multiply
    =
    left:term {hspace} op:'⋅' {hspace} right:factor
    | left:term {hspace} right:factor
    ;


division::Divide
    =
    left:term {hspace} op:('/'|'÷') {hspace} right:factor
    ;

derivative::Derivative
    = 
    DERIVATIVE [uorder:sup_integer | '^' uorder:(identifier|number)] upper:factor f:'/' DERIVATIVE lower:identifier [lorder:sup_integer | '^' lorder:(identifier|number)]
    | DERIVATIVE [uorder:sup_integer | '^' uorder:(identifier|number)] s:'/' DERIVATIVE lower:identifier [lorder:sup_integer | '^' lorder:(identifier|number)] {hspace}+ upper:factor 
    ;
    
partial::Partial
    = 
    PARTIAL [uorder:sup_integer | '^' uorder:(identifier|number)] upper:factor f:'/' l:{PARTIAL lower+:identifier [lorder+:sup_integer | '^' lorder+:(identifier|number)]}+
    | PARTIAL [uorder:sup_integer | '^' uorder:(identifier|number)] s:'/' l:{PARTIAL lower+:identifier [lorder+:sup_integer | '^' lorder+:(identifier|number)]}+ {hspace}+ upper:factor 
    ;

divergence::Divergence
    = 
    name:NABLA {hspace} '⋅' {hspace} value:factor
    ;

gradient::Gradient
    = 
    name:NABLA '_' sub:identifier_alone {hspace}+ value:factor
    | name:NABLA sub:unicode_subscript {hspace} value:factor
    | name:NABLA {hspace} value:factor
    ;
    
laplacian::Laplace
    = 
    name:DELTA {hspace} value:factor
    ;

power_operator::Power
    = 
    base:factor t:'^T'
    | base:factor r:('^(-1)' | '⁻¹')
    | base:factor '^' power:factor
    | base:factor power:(sup_integer|unicode_superscript)
    ;

solver_operator::Solver
    = 
    left:factor {hspace} '\' {hspace} right:factor
    | left:factor {hspace} p:('^(-1)' | '⁻¹') {hspace} right:factor
    ;

sum_operator::Summation
    = 
    ((SUM | u:'∪') '_' sub:identifier_alone {hspace}+ sign:['-'] exp:term
    | (SUM | u:'∪') '_' sub:identifier_alone &'(' {hspace} sign:['-'] exp:term
    | (SUM | u:'∪') '_(' {hspace} id:identifier_alone {hspace} 'for' {hspace} cond:if_condition {hspace} ')' {hspace} sign:['-'] exp:term
    | (SUM | u:'∪') '_(' {hspace} id:identifier_alone {hspace} '=' {hspace} lower:expression {hspace}')^' upper:(identifier_alone|integer) {hspace}+ sign:['-'] exp:term
    | (SUM | u:'∪') '_(' {hspace} id:identifier_alone {hspace} '=' {hspace} lower:expression {hspace}')^(' {hspace} upper:expression {hspace}')' {hspace}+ sign:['-'] exp:term
    | (SUM | u:'∪') '_(' {hspace} enum+:identifier_alone {{hspace} {','} {hspace} enum+:identifier_alone} {hspace} IN {hspace} range:(function_operator | builtin_operators | identifier_alone) {hspace} ')' {hspace} sign:['-'] exp:term
    ) {[{hspace} line] {hspace} (WHERE | WITH ) {hspace} extra+:general_assign {{hspace} ',' {hspace} [line] {hspace} extra+:general_assign}}
    ;

optimize_operator::Optimize
    = 
    {'with' {hspace} 'initial' {hspace} init+:statement {{hspace} ';' {hspace} init+:statement} {hspace} '\n'}
    (min:MIN|max:MAX|amin:ARGMIN|amax:ARGMAX) '_(' {hspace} defs+:where_condition_terse {{hspace} ',' {hspace} defs+:where_condition_terse} {hspace}
    ')' {hspace} exp:expression 
    {{hspace} {separator} {hspace} SUBJECT_TO {hspace} {separator} {hspace} cond:multi_cond}
    ;

multi_cond::MultiCond
    = 
    {hspace} m_cond:multi_cond separator_with_space cond:atom_condition {hspace}
    | {hspace} cond:atom_condition {hspace}
    ;

integral_operator::Integral
    = 
    (INT|'∫') '_' (d:domain | (lower:sub_factor {hspace} '^' {hspace} upper:sub_factor )) {hspace} exp:expression {hspace} DERIVATIVE id:identifier_alone
    ;

domain::Domain
    = 
    '[' {hspace} lower:expression {hspace} ',' {hspace} upper:expression ']'
    ;

norm_operator::Norm
    = 
    (double:'||' {hspace} value:expression {hspace} '||'
    | double:'‖' {hspace} value:expression {hspace} '‖'
    | single:'|' {hspace} value:expression {hspace} '|')
    [
    ( ('_' sub:(integer|'*'|'∞'|identifier_alone) | sub:sub_integer) ['^' power:factor | power:sup_integer])
    | ( '_(' sub:(integer|'*'|'∞'|identifier) ')' ['^' power:factor | power:sup_integer])
    | ( ('^' power:factor | power:sup_integer) ['_' sub:(integer|'*'|'∞'|identifier_alone) | sub:sub_integer] )
    ]
    ;

inner_product_operator::InnerProduct
    = 
    (('<' {hspace} left:expression {hspace} ',' {hspace}  right:expression {hspace} '>')
    | ('⟨' {hspace} left:expression {hspace} ',' {hspace}  right:expression {hspace} '⟩'))
    {'_' sub:identifier}
    ;

frobenius_product_operator::FroProduct
    = 
    left:factor {hspace} ':' {hspace}  right:factor
    ;

hadamard_product_operator::HadamardProduct
    = 
    left:factor {hspace} '∘' {hspace}  right:factor
    ;

cross_product_operator::CrossProduct
    = 
    left:factor {hspace} '×' {hspace}  right:factor
    ;

kronecker_product_operator::KroneckerProduct
    = 
    left:factor {hspace} '⊗' {hspace}  right:factor
    ;

trans_operator::Transpose
    = 
    f:factor /ᵀ/
    ;

pseudoinverse_operator::PseudoInverse
    = 
    f:factor /⁺/
    ;
    
sqrt_operator::Squareroot
    = 
    /√/ f:factor
    ;

predefined_built_operators
    =
    | exp_func
    | log_func
    | ln_func
    | sqrt_func
    | element_convert_func
    | minmax_func
    ;
    
element_convert_func::ElementConvertFunc
    = 
    (vs:VERTEXSET | es:EDGESET | fs:FACESET | ts:TETSET | s:SIMPLICIALSET | tu:TUPLE | se:SEQUENCE
    | v:VERTICES | e:EDGES | f:FACES | t:TETS) 
    '(' {{hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression}} {hspace}')'
    ;

exp_func::ExpFunc
    = 
    EXP '(' {hspace} param:expression {hspace} ')'
    ;
    
minmax_func::MinmaxFunc
    = 
    (min:MIN|max:MAX) '(' {hspace} params+:expression {{hspace} separators+:params_separator {hspace} params+:expression} {hspace} ')'
    ;

log_func::LogFunc
    = 
    ( (f:/log[\u2082]/ | s: /log[\u2081][\u2080]/) '(' {hspace} param:expression {hspace} ')')
    | ( LOG [f:'_2' | s:'_10'] '(' {hspace} param:expression {hspace} ')')
    ;

ln_func::LnFunc
    = 
    LN '(' {hspace} param:expression {hspace} ')'
    ;

sqrt_func::SqrtFunc
    = 
    SQRT '(' {hspace} param:expression {hspace} ')'
    ;
"""