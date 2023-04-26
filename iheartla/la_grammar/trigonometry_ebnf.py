TRIGONOMETRY = r"""
### trigonometry function

sin_func::SinFunc
    = 
    SIN {('^' power:integer) | power:sup_integer} '(' {hspace} param:expression {hspace} ')'
    ;

asin_func::AsinFunc
    = 
    name:ASIN {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

arcsin_func::AsinFunc
    = 
    name:ARCSIN {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

cos_func::CosFunc
    = 
    COS {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

acos_func::AcosFunc
    = 
    name:ACOS {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

arccos_func::AcosFunc
    = 
    name:ARCCOS {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

tan_func::TanFunc
    = 
    TAN {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

atan_func::AtanFunc
    = 
    name:ATAN {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

arctan_func::AtanFunc
    = 
    name:ARCTAN {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

sinh_func::SinhFunc
    = 
    SINH {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

asinh_func::AsinhFunc
    = 
    name:ASINH {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

arsinh_func::AsinhFunc
    = 
    name:ARSINH {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

cosh_func::CoshFunc
    = 
    COSH {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

acosh_func::AcoshFunc
    = 
    name:ACOSH {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

arcosh_func::AcoshFunc
    = 
    name:ARCOSH {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

tanh_func::TanhFunc
    = 
    TANH {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

atanh_func::AtanhFunc
    = 
    name:ATANH {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

artanh_func::AtanhFunc
    = 
    name:ARTANH {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

cot_func::CotFunc
    = 
    COT {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

sec_func::SecFunc
    = 
    SEC {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

csc_func::CscFunc
    = 
    CSC {('^' power:integer) | power:sup_integer}  '(' {hspace} param:expression {hspace} ')'
    ;

atan2_func::Atan2Func
    = 
    ATAN2 '(' {hspace} param:expression {hspace} separator:params_separator {hspace} second:expression {hspace} ')'
    ;

### linear algebra function
trace_func::TraceFunc
    = 
    name:TRACE '(' {hspace} param:expression {hspace} ')'
    ;

tr_func::TraceFunc
    = 
    name:TR '(' {hspace} param:expression {hspace} ')'
    ;

diag_func::DiagFunc
    = 
    DIAG '(' {hspace} param:expression {{hspace} separator:params_separator {hspace} extra+:expression} {hspace} ')'
    ;

vec_func::VecFunc
    = 
    VEC '(' {hspace} param:expression {hspace} ')'
    ;

inversevec_func::InverseVecFunc
    =
    name:INVERSEVEC '(' {hspace} origin:expression {hspace} separator:params_separator {hspace} param:expression {hspace} ')'
    | name:INVERSEVEC s:'_' origin:(integer|identifier_alone) '('{hspace} param:expression {hspace} ')'
    ;

det_func::DetFunc
    = 
    DET '(' {hspace} param:expression {hspace} ')'
    ;

rank_func::RankFunc
    = 
    RANK '(' {hspace} param:expression {hspace} ')'
    ;

null_func::NullFunc
    = 
    NULL '(' {hspace} param:expression {hspace} ')'
    ;

orth_func::OrthFunc
    = 
    ORTH '(' {hspace} param:expression {hspace} ')'
    ;

inv_func::InvFunc
    = 
    INV '(' {hspace} param:expression {hspace} ')'
    ;

svd_func::SvdFunc
    =
    SVD '(' {hspace} param:expression {hspace} ')'
    ;
"""