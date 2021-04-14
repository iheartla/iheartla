KEYWORDS = r"""
BUILTIN_KEYWORDS
    =
    | DERIVATIVE
    | WHERE
    | GIVEN
    | SUM
    | MIN
    | MAX
    | ARGMIN
    | ARGMAX
    | INT
    | IF
    | OTHERWISE
    | IS
    | IN
    | EXP
    | LOG
    | LN
    | SQRT
    | SUBJECT_TO
    | FROM
    | PI
    | '|'
    | 'ℝ'|'ℤ' | /[\u1d40]/ | 'ᵀ' | '∂'
    #| SIN | COS | ASIN | ARCSIN | ACOS | ARCCOS | TAN | ATAN | ARCTAN | ATAN2
    ;

TRACE = /trace/;
VEC = /vec/;
DIAG = /diag/;
ID = /Id/;
EIG = /eig/;
CONJ = /conj/;
RE = /Re/;
IM = /Im/;
INV = /inv/;
DET = /det/;
SVD = /svd/;
RANK = /rank/;
NULL = /null/;
ORTH = /orth/;
QR = /qr/;
DERIVATIVE = '\u2202';
VDOTS = '\u22EE';   #⋮
CDOTS = '\u22EF';   #⋯
IDDOTS = '\u22F0';  #⋰
DDOTS = '\u22F1';   #⋱
WHERE = /where/;
GIVEN = /given/;
SUM = /sum/ | /∑/;
MIN = /min/;
MAX = /max/;
ARGMIN = /argmin/;
ARGMAX = /argmax/;
INT = /int/;
SYMMETRIC = /symmetric/;
DIAGONAL = /diagonal/;
SPARSE = /sparse/;
IF = /if/;
OTHERWISE = /otherwise/;
IS = /is/;
IN = /∈/;
SIN = /sin/;
ASIN = /asin/;
ARCSIN = /arcsin/;
COS = /cos/;
ACOS = /acos/;
ARCCOS = /arccos/;
TAN = /tan/;
ATAN = /atan/;
ARCTAN = /arctan/;
SINH = /sinh/;
ASINH = /asinh/;
ARSINH = /arsinh/;
COSH = /cosh/;
ACOSH = /acosh/;
ARCOSH = /arcosh/;
TANH = /tanh/;
ATANH = /atanh/;
ARTANH = /artanh/;
COT = /cot/;
SEC = /sec/;
CSC = /csc/;
ATAN2 = /atan2/;
EXP = /exp/;
LOG = /log/;
LN = /ln/;
SQRT = /sqrt/;
SUBJECT_TO = /s.t./|/subject to/;
FROM = /from/;
PI = /π/;
"""