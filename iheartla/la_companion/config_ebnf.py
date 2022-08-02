from ..la_grammar.keywords_ebnf import KEYWORDS, KEYS
from ..la_grammar.number_ebnf import NUMBER
from ..la_grammar.operators_ebnf import OPERATORS
from ..la_grammar.matrix_ebnf import MATRIX
from ..la_grammar.base_ebnf import BASE
from ..la_grammar.types_ebnf import TYPES
from ..la_grammar.trigonometry_ebnf import TRIGONOMETRY
from ..la_grammar.shared_ebnf import SHARED
from ..la_grammar.arithmetic_ebnf import ARITHMETIC
START = r"""
@@grammar::LA
@@whitespace :: /(?!.*)/     #parse whitespace manually
@@left_recursion::True

start::Start
    = {{separator_with_space} {hspace} vblock+:valid_block {separator_with_space}}+ {blank} $
    ;

IS = /is/;
TRIANGLE = /triangle/;
MESH = /mesh/;
POINT = /point/;
CLOUD = /cloud/;
LU = /LU/;
ODE = /ODE/;
EXPLICIT = /explicit/;
IMPLICIT = /implicit/;
EULER = /euler/;
RK = /RK/;

CONF_KEYWORDS
    = IS
    | TRIANGLE
    | MESH
    | FROM
    | SOLVE | WITH | ODE | EXPLICIT | IMPLICIT | EULER | RK
    ;
"""
CONFIG = START + KEYS + BASE + ARITHMETIC + TYPES + NUMBER

CONFIG += r""" 

KEYWORDS
    = CONF_KEYWORDS;

identifier_alone::IdentifierAlone
    = !KEYWORDS( value:(/[A-Za-z\p{Ll}\p{Lu}\p{Lo}](?![\u0308\u0307])\p{M}*/|/[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*(?=[\u0308\u0307])/) | '`' id:/[^`]*/ '`')
    #= const:('abc'|'sss') | (!(KEYWORDS |'abc'|'sss' ) value:/[A-Za-z\p{Ll}|\p{Lu}|\p{Lo}]/ | '`' id:/[^`]*/ '`')
    ;

valid_block
    = definition | mapping | solver
    ;
    
definition
    = id:identifier {hspace}+ IS {hspace}+ geometry;

geometry
    = triangle_mesh
    | point_cloud
    ;
    
triangle_mesh::Triangle
    = TRIANGLE {hspace}+ MESH {hspace} '(' {hspace} v:identifier {hspace} ',' {hspace} e:identifier {hspace} ',' {hspace} f:identifier {hspace} ')'
    ;
    
point_cloud::Point
    = POINT {hspace}+ CLOUD {hspace} '(' {hspace} v:identifier {hspace}')'
    ;
    
operators::Operators
    = Divergence
    | Gradient
    | Laplacian
    ;
    
Divergence
    = /∇⋅/;
    
Gradient
    = /∇/;
    
Laplacian
    = /Δ/;
    
mapping::Mapping
   = lhs:(identifier | operators) {hspace} (':'| IN | subset:SUBSET) {hspace}
   ((params+:map_type {{hspace} separators+:params_separator {hspace} params+:map_type})|empty:'∅'|'{'{hspace}'}') 
   {hspace} ('→'|'->') {hspace} 
   ret+:map_type {{hspace} ret_separators+:params_separator {hspace} ret+:map_type} 
   {{hspace} FROM {hspace} ref:module}
    ;
    
map_type::MapType
    = params_type | identifier;

module
    = !KEYWORDS /[A-Za-z0-9_]*/ 
    ;
    
solver
    = SOLVE {hspace} target {hspace} WITH {hspace} method
    ;
    
target
    = ODE | module
    ;
    
method
    = LU
    | EXPLICIT {hspace}+ EULER
    | IMPLICIT {hspace}+ EULER
    | RK
    ;
"""