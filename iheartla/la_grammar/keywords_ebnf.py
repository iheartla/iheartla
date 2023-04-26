KEYS = r"""
TRACE = /trace/;
TR = /tr/;
VEC = /vec/;
INVERSEVEC = /inversevec/ | /vec⁻¹/;
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
DELTA = /[Δ]/;
NABLA = /∇/;
PRIME = /'/;
UDOT = /[\u0307]/;   
UDDOT = /[\u0308]/;   
SOLVE = /solve/ | /Solve/ | /SOLVE/;
SUBSET = /⊂/;
AS = /as/;
POUND = /#/;
FOR = /for/;
SCALAR = /scalar/;
VECTOR = /vector/;
MATRIX = /matrix/;
VERTEXSET = /[Vv]ertex[Ss]et/;
EDGESET = /[Ee]dge[Ss]et/;
FACESET = /[Ff]ace[Ss]et/;
TETSET = /[Tt]et[Ss]et/;
SIMPLICIALSET = /[Ss]implicial[Ss]et/;
MESH = /mesh/ | /Mesh/;
TRIANGLE = /[Tt]riangle[Mm]esh/;
POLYGON = /[Pp]olygon[Mm]esh/;
POINTCLOUD = /[Pp]oint [Cc]loud/ | /[Pp]oint[Cc]loud/;
TETRAHEDRON = /[Tt]etrahedral[Mm]esh/;
POLYHEDRON = /[Pp]olyhedral[Mm]esh/;
INDEX = /index/;
VERTICES = /vertices/;
EDGES = /edges/;
FACES = /faces/;
TETS = /tets/;
TUPLE = /tuple/;
SEQUENCE = /sequence/;
SVD = /svd/;
"""

KEYWORDS = KEYS + r"""
BUILTIN_KEYWORDS
    =
    | WHERE
    | GIVEN
    | /sum/
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
    | /ℝ/|/ℤ/
    | SCALAR | VECTOR | MATRIX
    #| SIN | COS | ASIN | ARCSIN | ACOS | ARCCOS | TAN | ATAN | ARCTAN | ATAN2
    | WITH
    | INITIAL
    | AND
    | OR
    | DELTA | NABLA | DERIVATIVE 
    # | PARTIAL  can't be matched as identifiers
    | SOLVE
    | PRIME
    | SUBSET
    | AS
    | POUND
    | FOR
    | VERTEXSET
    | EDGESET
    | FACESET
    | TETSET
    | SIMPLICIALSET
    | MESH
    | TRIANGLE
    | POLYGON
    | POINTCLOUD
    | TETRAHEDRON
    | POLYHEDRON
    | SPARSE
    | INDEX
    | VERTICES
    | EDGES
    | FACES
    | TETS
    | TUPLE
    | SEQUENCE
    ;
    
NOT_PREFIX_KEYWORD
    = 
    POUND
    | DELTA
    | NABLA
    | IN
    | DERIVATIVE
    ;
    
PREFIX_KEYWORD 
    = 
    !NOT_PREFIX_KEYWORD( KEYWORDS )
    ;
"""