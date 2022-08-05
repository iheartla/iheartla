KEYS = r"""
TRACE = /trace/;
TR = /tr/;
VEC = /vec/;
DIAG = /diag/;
INV = /inv/;
DET = /det/;
RANK = /rank/;
NULL = /null/;
ORTH = /orth/;
QR = /qr/;
DERIVATIVE = /𝕕/;
PARTIAL = /∂/;
WHERE = /where/;
GIVEN = /given/;
SUM = /sum/ | /∑/;
MIN = /min/;
MAX = /max/;
ARGMIN = /argmin/;
ARGMAX = /argmax/;
INT = /int/;
SPARSE = /sparse/;
IF = /if/;
OTHERWISE = /otherwise/;
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
WITH = /with/;
INITIAL = /initial/;
AND = /and/;
OR = /or/;
DELTA = /[Δδ𝛿]/;
NABLA = /∇/;
PRIME = /'/;
UDOT = /[\u0307]/;   
UDDOT = /[\u0308]/;   
SOLVE = /solve/ | /Solve/ | /SOLVE/;
SUBSET = /⊂/;
AS = /as/;
"""

KEYWORDS = KEYS + r"""
BUILTIN_KEYWORDS
    =
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
    | IN
    | EXP
    | LOG
    | LN
    | SQRT
    | SUBJECT_TO
    | FROM
    | PI
    | '|'
    | /ℝ/|/ℤ/ | /ᵀ/
    #| SIN | COS | ASIN | ARCSIN | ACOS | ARCCOS | TAN | ATAN | ARCTAN | ATAN2
    | WITH
    | INITIAL
    | AND
    | OR
    | DELTA | NABLA | DERIVATIVE | PARTIAL
    | SOLVE
    | PRIME
    | SUBSET
    | AS
    ;
"""