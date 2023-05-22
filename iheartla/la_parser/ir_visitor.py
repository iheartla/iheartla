from .ir import *
from .la_data import *
from ..la_tools.la_logger import *
from ..la_tools.la_helper import *
from ..la_tools.la_package import *
import unicodedata


class IRBaseVisitor(object):
    def __init__(self):
        super().__init__()

    def visit(self, node, **kwargs):
        type_func = {
            # base
            IRNodeType.Id: "visit_id",
            IRNodeType.Double: "visit_double",
            IRNodeType.Fraction: "visit_fraction",
            IRNodeType.Integer: "visit_integer",
            IRNodeType.Factor: "visit_factor",
            IRNodeType.Expression: "visit_expression",
            IRNodeType.Subexpression: "visit_sub_expr",
            IRNodeType.Constant: "visit_constant",
            IRNodeType.Cast: "visit_cast",
            # control
            IRNodeType.Start: "visit_start",
            IRNodeType.Block: "visit_block",
            IRNodeType.Assignment: "visit_assignment",
            IRNodeType.If: "visit_if",
            IRNodeType.Function: "visit_function",
            IRNodeType.LocalFunc: "visit_local_func",
            IRNodeType.Equation: "visit_equation",
            IRNodeType.Destructuring: "visit_destructuring",
            # if condition
            IRNodeType.Condition: "visit_condition",
            IRNodeType.In: "visit_in",
            IRNodeType.NotIn: "visit_not_in",
            IRNodeType.BinComp: "visit_bin_comp",
            # operators
            IRNodeType.Add: "visit_add",
            IRNodeType.Sub: "visit_sub",
            IRNodeType.Mul: "visit_mul",
            IRNodeType.Div: "visit_div",
            IRNodeType.Union: "visit_union",
            IRNodeType.Intersection: "visit_intersection",
            IRNodeType.Difference: "visit_difference",
            IRNodeType.AddSub: "visit_add_sub",
            IRNodeType.Summation: "visit_summation",
            IRNodeType.UnionSequence: "visit_union_sequence",
            IRNodeType.Norm: "visit_norm",
            IRNodeType.Transpose: "visit_transpose",
            IRNodeType.PseudoInverse: "visit_pseudoinverse",
            IRNodeType.Squareroot: "visit_squareroot",
            IRNodeType.Power: "visit_power",
            IRNodeType.Solver: "visit_solver",
            IRNodeType.Derivative: "visit_derivative",
            IRNodeType.MathFunc: "visit_math_func",
            IRNodeType.GPFunction: "visit_gp_func",
            IRNodeType.Optimize: "visit_optimize",
            IRNodeType.Domain: "visit_domain",
            IRNodeType.Integral: "visit_integral",
            IRNodeType.InnerProduct: "visit_inner_product",
            IRNodeType.FroProduct: "visit_fro_product",
            IRNodeType.HadamardProduct: "visit_hadamard_product",
            IRNodeType.CrossProduct: "visit_cross_product",
            IRNodeType.KroneckerProduct: "visit_kronecker_product",
            IRNodeType.DotProduct: "visit_dot_product",
            #
            IRNodeType.Divergence: "visit_divergence",
            IRNodeType.Gradient: "visit_gradient",
            IRNodeType.Laplace: "visit_laplace",
            IRNodeType.Partial: "visit_partial",
            IRNodeType.Size: "visit_size",
            # matrix
            IRNodeType.Matrix: "visit_matrix",
            IRNodeType.MatrixRows: "visit_matrix_rows",
            IRNodeType.MatrixRow: "visit_matrix_row",
            IRNodeType.MatrixRowCommas: "visit_matrix_row_commas",
            IRNodeType.ExpInMatrix: "visit_exp_in_matrix",
            IRNodeType.MultiConds: "visit_multi_conditionals",
            IRNodeType.SparseMatrix: "visit_sparse_matrix",
            IRNodeType.SparseIfs: "visit_sparse_ifs",
            IRNodeType.SparseIf: "visit_sparse_if",
            IRNodeType.SparseOther: "visit_sparse_other",
            IRNodeType.NumMatrix: "visit_num_matrix",
            IRNodeType.Vector: "visit_vector",
            IRNodeType.Set: "visit_set",
            IRNodeType.ToMatrix: "visit_to_matrix",
            IRNodeType.ToDouble: "visit_to_double",
            IRNodeType.ElementConvert: "visit_element_convert",
            #
            IRNodeType.MatrixIndex: "visit_matrix_index",
            IRNodeType.VectorIndex: "visit_vector_index",
            IRNodeType.SequenceIndex: "visit_sequence_index",
            IRNodeType.SeqDimIndex: "visit_seq_dim_index",
            IRNodeType.TupleIndex: "visit_tuple_index",
            IRNodeType.SetIndex: "visit_set_index",
            # where block
            IRNodeType.ParamsBlock: "visit_params_block",
            IRNodeType.WhereConditions: "visit_where_conditions",
            IRNodeType.WhereCondition: "visit_where_condition",
            IRNodeType.MatrixType: "visit_matrix_type",
            IRNodeType.VectorType: "visit_vector_type",
            IRNodeType.SetType: "visit_set_type",
            IRNodeType.ScalarType: "visit_scalar_type",
            IRNodeType.FunctionType: "visit_function_type",
            IRNodeType.MappingType: "visit_mapping_type",
            IRNodeType.TupleType: "visit_tuple_type",
            IRNodeType.NamedType: "visit_named_type",
            # derivatives
            IRNodeType.Import: "visit_import",
            # differential equations
            IRNodeType.OdeFirstOrder: "visit_first_order_ode",
        }
        func = getattr(self, type_func[node.node_type], None)
        if func:
            return func(node, **kwargs)
        else:
            print("invalid node type")

    def visit_id(self, node, **kwargs):
        return node.get_name()

    def visit_add(self, node, **kwargs):
        return self.visit(node.left, **kwargs) + '+' + self.visit(node.right, **kwargs)

    def visit_sub(self, node, **kwargs):
        return self.visit(node.left, **kwargs) + '-' + self.visit(node.right, **kwargs)

    def visit_mul(self, node, **kwargs):
        return self.visit(node.left, **kwargs) + ' ' + self.visit(node.right, **kwargs)

    def visit_div(self, node, **kwargs):
        return self.visit(node.left, **kwargs) + '/' + self.visit(node.right, **kwargs)

    def visit_add_sub(self, node, **kwargs):
        return self.visit(node.left, **kwargs) + " {} ".format(node.op) + self.visit(node.right, **kwargs)

    def visit_sub_expr(self, node, **kwargs):
        return '(' + self.visit(node.value, **kwargs) + ')'

    def visit_cast(self, node, **kwargs):
        pass

    def visit_condition(self, node, **kwargs):
        pass

    def visit_in(self, node, **kwargs):
        pass

    def visit_not_in(self, node, **kwargs):
        pass

    def visit_expression(self, node, **kwargs):
        value = self.visit(node.value, **kwargs)
        if node.sign:
            value = node.sign + value
        return value

    ####################################################
    def visit_matrix(self, node, **kwargs):
        pass

    def visit_vector(self, node, **kwargs):
        pass

    def visit_to_matrix(self, node, **kwargs):
        pass

    def visit_to_double(self, node, **kwargs):
        pass

    def visit_element_convert(self, node, **kwargs):
        pass

    def visit_sparse_matrix(self, node, **kwargs):
        pass

    def visit_summation(self, node, **kwargs):
        pass

    def visit_union_sequence(self, node, **kwargs):
        pass

    def visit_determinant(self, node, **kwargs):
        pass

    def visit_transpose(self, node, **kwargs):
        pass

    def visit_squareroot(self, node, **kwargs):
        pass

    def visit_power(self, node, **kwargs):
        pass

    def visit_divergence(self, node, **kwargs):
        pass

    def visit_gradient(self, node, **kwargs):
        pass

    def visit_laplace(self, node, **kwargs):
        pass

    def visit_solver(self, node, **kwargs):
        pass

    def visit_sparse_if(self, node, **kwargs):
        pass

    def visit_sparse_ifs(self, node, **kwargs):
        pass

    def visit_function(self, node, **kwargs):
        pass

    def visit_local_func(self, node, **kwargs):
        pass

    def visit_sparse_other(self, node, **kwargs):
        pass

    def visit_matrix_rows(self, node, **kwargs):
        pass

    def visit_matrix_row(self, node, **kwargs):
        pass

    def visit_matrix_row_commas(self, node, **kwargs):
        pass

    def visit_exp_in_matrix(self, node, **kwargs):
        pass

    def visit_num_matrix(self, node, **kwargs):
        pass

    def visit_matrix_index(self, node, **kwargs):
        pass

    def visit_vector_index(self, node, **kwargs):
        pass

    def visit_sequence_index(self, node, **kwargs):
        pass

    def visit_seq_dim_index(self, node, **kwargs):
        pass

    def visit_derivative(self, node, **kwargs):
        pass

    def visit_partial(self, node, **kwargs):
        pass

    def visit_size(self, node, **kwargs):
        pass

    def visit_factor(self, node, **kwargs):
        if node.id:
            return self.visit(node.id, **kwargs)
        elif node.num:
            return self.visit(node.num, **kwargs)
        elif node.sub:
            return self.visit(node.sub, **kwargs)
        elif node.m:
            return self.visit(node.m, **kwargs)
        elif node.v:
            return self.visit(node.v, **kwargs)
        elif node.s:
            return self.visit(node.s, **kwargs)
        elif node.nm:
            return self.visit(node.nm, **kwargs)
        elif node.op:
            return self.visit(node.op, **kwargs)
        elif node.c:
            return self.visit(node.c, **kwargs)

    def visit_double(self, node, **kwargs):
        return str(node.value)

    def visit_fraction(self, node, **kwargs):
        return str(node.unicode)

    def visit_integer(self, node, **kwargs):
        return str(node.value)

    ####################################################
    def visit_start(self, node, **kwargs):
        pass

    def visit_block(self, node, **kwargs):
        pass

    def visit_assignment(self, node, **kwargs):
        pass

    def visit_equation(self, node, **kwargs):
        pass

    def visit_if(self, node, **kwargs):
        pass

    ####################################################
    def visit_import(self, node, **kwargs):
        pass

    def visit_first_order_ode(self, node, **kwargs):
        pass

    ####################################################
    def walk_object(self, o):
        raise Exception('Unexpected type %s walked: %s', type(o).__name__, o)
    ###################################################################


class IRVisitor(IRBaseVisitor):
    def __init__(self, parse_type=None):
        super().__init__()
        self.pre_str = ''
        self.post_str = ''
        self.def_dict = {}
        self.local_func_parsing = False
        self.local_func_name = ''  # function name when visiting expressions
        # self.parameters = set()
        # self.subscripts = {}
        # self.dim_dict = {}
        # self.seq_dim_dict = {}
        # self.sub_name_dict = {}
        self.name_cnt_dict = {}
        # self.same_dim_list = []
        # self.arith_dim_list = []
        # self.ids_dict = {}  # identifiers with subscripts
        # self.dim_seq_set = set()  # sequence of dimension for ragged list
        self.ret_symbol = None
        self.unofficial_method = False  # matrix pow only(eigen)
        self.has_opt = False  # whether opt expr exists
        self.need_mutator = False
        self.has_derivative = False
        self.content = ''
        self.local_func_def = ''
        self.local_func_syms = []
        self.local_func_dict = {}
        self.extra_symtable = {}
        self.scope_list = ['global']
        self.visiting_opt = False  # optimization
        self.opt_key = ''
        self.opt_dict = {}
        self.parse_type = parse_type
        self.logger = LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT)
        self.name_convention_dict = {}  # eg:i -> i[0]
        self.func_name = 'myExpression'
        self.param_name_test = 'p'  # param name for test function
        self.convert_matrix = False
        self.visiting_lhs = False
        self.visiting_func_name = False
        self.visiting_diff_eq = False
        self.visiting_diff_init = False
        self.visiting_sum = False
        self.class_only = False
        self.lhs_list = []
        self.lhs_on_der = [] # symbol defined with gradient or hessian
        self.module_list = []
        self.module_syms = {}
        self.builtin_module_dict = {}
        self.pattern = re.compile("[A-Za-z]+")
        self.la_content = ''
        self.new_id_prefix = ''  # _
        self.uni_num_dict = {'₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4', '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
                             '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9'}
        # These are especially important in targets like MATLAB which have a very restrictive (≈ASCII) character set for variable names:
        #
        # remove (,) otherwise they result in giant variable names, e.g., `x(a,b)` → x_left_parenthesis_a_comma_b_right_parenthesis
        # Greek symbols to English words, e.g., θ → theta
        # subscripts to underscore letter, e.g., ᵢ → _i
        # common math decorations to English names, e.g., v̄ → v_bar, rather than unicode names , e.g., v̄ → v_combining_macron 
        # ^ is translated into _, .e.g, s^k → s_k
        # ℓ → ell rather than script_small_l
        self.comment_placeholder = 'iheartlacomment'
        self.comment_dict = {}
        self.common_symbol_dict = {
            ',': '', '(':'',')':'', 'Α': 'Alpha', 'Β': 'Beta', 'Γ': 'Gamma', 'Δ': 'Delta', 'Ε': 'Epsilon', 'Ζ': 'Zeta', 'Η': 'Eta', 'Θ': 'Theta', 'Ι': 'Iota', 'Κ': 'Kappa', 'Λ': 'Lambda', 'Μ': 'Mu', 'Ν': 'Nu', 'Ξ': 'Xi', 'Ο': 'Omicron', 'Π': 'Pi', 'Ρ': 'Rho', 'Σ': 'Sigma', '∑': 'Sigma', 'Τ': 'Tau', 'Υ': 'Upsilon', 'Φ': 'Phi', 'Χ': 'Chi', 'Ψ': 'Psi', 'Ω': 'Omega', 'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta', 'ε': 'epsilon', 'ζ': 'zeta', 'η': 'eta', 'θ': 'theta', 'ι': 'iota', 'κ': 'kappa', 'λ': 'lambda', 'μ': 'mu', 'ν': 'nu', 'ξ': 'xi', 'ο': 'omicron', 'π': 'pi', 'ρ': 'rho', 'ς': 'sigma', 'σ': 'sigma', 'τ': 'tau', 'υ': 'upsilon', 'ϕ': 'phi', 'φ': 'phi', 'χ': 'chi', 'ψ': 'psi', 'ω': 'omega', 'ₐ':'_a','ᵢ': '_i', 'ⱼ': '_j', 'ₖ': '_k', 'ₘ': '_m', 'ₙ': '_n','ᵣ': '_r', 'ₛ': '_s', '\u0302': '_hat', '\u0303': '_tilde', '\u0304': '_bar', '\u0305': '_wide_bar', '\u0307': '_dot', '\u0308': '_double_dot', '\u030C': '_check', '\u20D7': '_vec', 'ã': 'a_tilde', '^': '_', 'ℓ': 'ell',
            '𝐀': 'bold_A', '𝐁': 'bold_B', '𝐂': 'bold_C', '𝐃': 'bold_D', '𝐄': 'bold_E', '𝐅': 'bold_F', '𝐆': 'bold_G', '𝐇': 'bold_H', '𝐈': 'bold_I', '𝐉': 'bold_J', '𝐊': 'bold_K', '𝐋': 'bold_L', '𝐌': 'bold_M', '𝐍': 'bold_N', '𝐎': 'bold_O', '𝐏': 'bold_P', '𝐐': 'bold_Q', '𝐑': 'bold_R', '𝐒': 'bold_S', '𝐓': 'bold_T', '𝐔': 'bold_U', '𝐕': 'bold_V', '𝐖': 'bold_W', '𝐗': 'bold_X', '𝐘': 'bold_Y', '𝐙': 'bold_Z', '𝐚': 'bold_a', '𝐛': 'bold_b', '𝐜': 'bold_c', '𝐝': 'bold_d', '𝐞': 'bold_e', '𝐟': 'bold_f', '𝐠': 'bold_g', '𝐡': 'bold_h', '𝐢': 'bold_i', '𝐣': 'bold_j', '𝐤': 'bold_k', '𝐥': 'bold_l', '𝐦': 'bold_m', '𝐧': 'bold_n', '𝐨': 'bold_o', '𝐩': 'bold_p', '𝐪': 'bold_q', '𝐫': 'bold_r', '𝐬': 'bold_s', '𝐭': 'bold_t', '𝐮': 'bold_u', '𝐯': 'bold_v', '𝐰': 'bold_w', '𝐱': 'bold_x', '𝐲': 'bold_y', '𝐳': 'bold_z',
            '𝟎': 'bold_0', '𝟏': 'bold_1', '𝟐': 'bold_2', '𝟑': 'bold_3', '𝟒': 'bold_4', '𝟓': 'bold_5', '𝟔': 'bold_6', '𝟕': 'bold_7', '𝟖': 'bold_8', '𝟗': 'bold_9',
            '𝚨': 'bold_Alpha', '𝚩': 'bold_Beta', '𝚪': 'bold_Gamma', '𝚫': 'bold_Delta', '𝚬': 'bold_Epsilon', '𝚭': 'bold_Zeta', '𝚮': 'bold_Eta', '𝚯': 'bold_Theta', '𝚰': 'bold_Iota', '𝚱': 'bold_Kappa', '𝚲': 'bold_Lamda', '𝚳': 'bold_Mu', '𝚴': 'bold_Nu', '𝚵': 'bold_Xi', '𝚶': 'bold_Omicron', '𝚷': 'bold_Pi', '𝚸': 'bold_Rho', '𝚹': 'bold_Theta', '𝚺': 'bold_Sigma', '𝚻': 'bold_Tau', '𝚼': 'bold_Upsilon', '𝚽': 'bold_Phi', '𝚾': 'bold_Chi', '𝚿': 'bold_Psi', '𝛀': 'bold_Omega', '𝛁': 'bold_nabla', '𝛂': 'bold_alpha', '𝛃': 'bold_beta', '𝛄': 'bold_gamma', '𝛅': 'bold_delta', '𝛆': 'bold_epsilon', '𝛇': 'bold_zeta', '𝛈': 'bold_eta', '𝛉': 'bold_theta', '𝛊': 'bold_iota', '𝛋': 'bold_kappa', '𝛌': 'bold_lamda', '𝛍': 'bold_mu', '𝛎': 'bold_nu', '𝛏': 'bold_xi', '𝛐': 'bold_omicron', '𝛑': 'bold_pi', '𝛒': 'bold_rho', '𝛓': 'bold_sigma', '𝛔': 'bold_sigma', '𝛕': 'bold_tau', '𝛖': 'bold_upsilon', '𝛗': 'bold_phi', '𝛘': 'bold_chi', '𝛙': 'bold_psi', '𝛚': 'bold_omega', '𝛛': 'bold_partial_differential', '𝛜': 'bold_epsilon', '𝛝': 'bold_theta', '𝛞': 'bold_kappa', '𝛟': 'bold_phi', '𝛠': 'bold_rho', '𝛡': 'bold_pi',
            '𝐴': 'italic_A', '𝐵': 'italic_B', '𝐶': 'italic_C', '𝐷': 'italic_D', '𝐸': 'italic_E', '𝐹': 'italic_F', '𝐺': 'italic_G', '𝐻': 'italic_H', '𝐼': 'italic_I', '𝐽': 'italic_J', '𝐾': 'italic_K', '𝐿': 'italic_L', '𝑀': 'italic_M', '𝑁': 'italic_N', '𝑂': 'italic_O', '𝑃': 'italic_P', '𝑄': 'italic_Q', '𝑅': 'italic_R', '𝑆': 'italic_S', '𝑇': 'italic_T', '𝑈': 'italic_U', '𝑉': 'italic_V', '𝑊': 'italic_W', '𝑋': 'italic_X', '𝑌': 'italic_Y', '𝑍': 'italic_Z', '𝑎': 'italic_a', '𝑏': 'italic_b', '𝑐': 'italic_c', '𝑑': 'italic_d', '𝑒': 'italic_e', '𝑓': 'italic_f', '𝑔': 'italic_g', '𝑖': 'italic_i', '𝑗': 'italic_j', '𝑘': 'italic_k', '𝑙': 'italic_l', '𝑚': 'italic_m', '𝑛': 'italic_n', '𝑜': 'italic_o', '𝑝': 'italic_p', '𝑞': 'italic_q', '𝑟': 'italic_r', '𝑠': 'italic_s', '𝑡': 'italic_t', '𝑢': 'italic_u', '𝑣': 'italic_v', '𝑤': 'italic_w', '𝑥': 'italic_x', '𝑦': 'italic_y', '𝑧': 'italic_z',
            '𝚤': 'italic_dotless_i', '𝚥': 'italic_dotless_j',
            '𝛢': 'italic_Alpha', '𝛣': 'italic_Beta', '𝛤': 'italic_Gamma', '𝛥': 'italic_Delta', '𝛦': 'italic_Epsilon', '𝛧': 'italic_Zeta', '𝛨': 'italic_Eta', '𝛩': 'italic_Theta', '𝛪': 'italic_Iota', '𝛫': 'italic_Kappa', '𝛬': 'italic_Lamda', '𝛭': 'italic_Mu', '𝛮': 'italic_Nu', '𝛯': 'italic_Xi', '𝛰': 'italic_Omicron', '𝛱': 'italic_Pi', '𝛲': 'italic_Rho', '𝛳': 'italic_Theta', '𝛴': 'italic_Sigma', '𝛵': 'italic_Tau', '𝛶': 'italic_Upsilon', '𝛷': 'italic_Phi', '𝛸': 'italic_Chi', '𝛹': 'italic_Psi', '𝛺': 'italic_Omega', '𝛻': 'italic_nabla', '𝛼': 'italic_alpha', '𝛽': 'italic_beta', '𝛾': 'italic_gamma', '𝛿': 'italic_delta', '𝜀': 'italic_epsilon', '𝜁': 'italic_zeta', '𝜂': 'italic_eta', '𝜃': 'italic_theta', '𝜄': 'italic_iota', '𝜅': 'italic_kappa', '𝜆': 'italic_lamda', '𝜇': 'italic_mu', '𝜈': 'italic_nu', '𝜉': 'italic_xi', '𝜊': 'italic_omicron', '𝜋': 'italic_pi', '𝜌': 'italic_rho', '𝜍': 'italic_sigma', '𝜎': 'italic_sigma', '𝜏': 'italic_tau', '𝜐': 'italic_upsilon', '𝜑': 'italic_phi', '𝜒': 'italic_chi', '𝜓': 'italic_psi', '𝜔': 'italic_omega', '𝜕': 'italic_partial_differential', '𝜖': 'italic_epsilon', '𝜗': 'italic_theta', '𝜘': 'italic_kappa', '𝜙': 'italic_phi', '𝜚': 'italic_rho', '𝜛': 'italic_pi',
            '𝑨': 'bf_it_A', '𝑩': 'bf_it_B', '𝑪': 'bf_it_C', '𝑫': 'bf_it_D', '𝑬': 'bf_it_E', '𝑭': 'bf_it_F', '𝑮': 'bf_it_G', '𝑯': 'bf_it_H', '𝑰': 'bf_it_I', '𝑱': 'bf_it_J', '𝑲': 'bf_it_K', '𝑳': 'bf_it_L', '𝑴': 'bf_it_M', '𝑵': 'bf_it_N', '𝑶': 'bf_it_O', '𝑷': 'bf_it_P', '𝑸': 'bf_it_Q', '𝑹': 'bf_it_R', '𝑺': 'bf_it_S', '𝑻': 'bf_it_T', '𝑼': 'bf_it_U', '𝑽': 'bf_it_V', '𝑾': 'bf_it_W', '𝑿': 'bf_it_X', '𝒀': 'bf_it_Y', '𝒁': 'bf_it_Z', '𝒂': 'bf_it_a', '𝒃': 'bf_it_b', '𝒄': 'bf_it_c', '𝒅': 'bf_it_d', '𝒆': 'bf_it_e', '𝒇': 'bf_it_f', '𝒈': 'bf_it_g', '𝒉': 'bf_it_h', '𝒊': 'bf_it_i', '𝒋': 'bf_it_j', '𝒌': 'bf_it_k', '𝒍': 'bf_it_l', '𝒎': 'bf_it_m', '𝒏': 'bf_it_n', '𝒐': 'bf_it_o', '𝒑': 'bf_it_p', '𝒒': 'bf_it_q', '𝒓': 'bf_it_r', '𝒔': 'bf_it_s', '𝒕': 'bf_it_t', '𝒖': 'bf_it_u', '𝒗': 'bf_it_v', '𝒘': 'bf_it_w', '𝒙': 'bf_it_x', '𝒚': 'bf_it_y', '𝒛': 'bf_it_z',
            '𝒜': 'sc_A', '𝒞': 'sc_C', '𝒟': 'sc_D', '𝒢': 'sc_G', '𝒥': 'sc_J', '𝒦': 'sc_K', '𝒩': 'sc_N', '𝒪': 'sc_O', '𝒫': 'sc_P', '𝒬': 'sc_Q', '𝒮': 'sc_S', '𝒯': 'sc_T', '𝒰': 'sc_U', '𝒱': 'sc_V', '𝒲': 'sc_W', '𝒳': 'sc_X', '𝒴': 'sc_Y', '𝒵': 'sc_Z', '𝒶': 'sc_a', '𝒷': 'sc_b', '𝒸': 'sc_c', '𝒹': 'sc_d', '𝒻': 'sc_f', '𝒽': 'sc_h', '𝒾': 'sc_i', '𝒿': 'sc_j', '𝓀': 'sc_k', '𝓁': 'ell', '𝓂': 'sc_m', '𝓃': 'sc_n', '𝓅': 'sc_p', '𝓆': 'sc_q', '𝓇': 'sc_r', '𝓈': 'sc_s', '𝓉': 'sc_t', '𝓊': 'sc_u', '𝓋': 'sc_v', '𝓌': 'sc_w', '𝓍': 'sc_x', '𝓎': 'sc_y', '𝓏': 'sc_z',
            '𝓐': 'bf_sc_A', '𝓑': 'bf_sc_B', '𝓒': 'bf_sc_C', '𝓓': 'bf_sc_D', '𝓔': 'bf_sc_E', '𝓕': 'bf_sc_F', '𝓖': 'bf_sc_G', '𝓗': 'bf_sc_H', '𝓘': 'bf_sc_I', '𝓙': 'bf_sc_J', '𝓚': 'bf_sc_K', '𝓛': 'bf_sc_L', '𝓜': 'bf_sc_M', '𝓝': 'bf_sc_N', '𝓞': 'bf_sc_O', '𝓟': 'bf_sc_P', '𝓠': 'bf_sc_Q', '𝓡': 'bf_sc_R', '𝓢': 'bf_sc_S', '𝓣': 'bf_sc_T', '𝓤': 'bf_sc_U', '𝓥': 'bf_sc_V', '𝓦': 'bf_sc_W', '𝓧': 'bf_sc_X', '𝓨': 'bf_sc_Y', '𝓩': 'bf_sc_Z', '𝓪': 'bf_sc_a', '𝓫': 'bf_sc_b', '𝓬': 'bf_sc_c', '𝓭': 'bf_sc_d', '𝓮': 'bf_sc_e', '𝓯': 'bf_sc_f', '𝓰': 'bf_sc_g', '𝓱': 'bf_sc_h', '𝓲': 'bf_sc_i', '𝓳': 'bf_sc_j', '𝓴': 'bf_sc_k', '𝓵': 'bf_ell', '𝓶': 'bf_sc_m', '𝓷': 'bf_sc_n', '𝓸': 'bf_sc_o', '𝓹': 'bf_sc_p', '𝓺': 'bf_sc_q', '𝓻': 'bf_sc_r', '𝓼': 'bf_sc_s', '𝓽': 'bf_sc_t', '𝓾': 'bf_sc_u', '𝓿': 'bf_sc_v', '𝔀': 'bf_sc_w', '𝔁': 'bf_sc_x', '𝔂': 'bf_sc_y', '𝔃': 'bf_sc_z',
            '𝔄': 'frak_A', '𝔅': 'frak_B', '𝔇': 'frak_D', '𝔈': 'frak_E', '𝔉': 'frak_F', '𝔊': 'frak_G', '𝔍': 'frak_J', '𝔎': 'frak_K', '𝔏': 'frak_L', '𝔐': 'frak_M', '𝔑': 'frak_N', '𝔒': 'frak_O', '𝔓': 'frak_P', '𝔔': 'frak_Q', '𝔖': 'frak_S', '𝔗': 'frak_T', '𝔘': 'frak_U', '𝔙': 'frak_V', '𝔚': 'frak_W', '𝔛': 'frak_X', '𝔜': 'frak_Y', '𝔞': 'frak_a', '𝔟': 'frak_b', '𝔠': 'frak_c', '𝔡': 'frak_d', '𝔢': 'frak_e', '𝔣': 'frak_f', '𝔤': 'frak_g', '𝔥': 'frak_h', '𝔦': 'frak_i', '𝔧': 'frak_j', '𝔨': 'frak_k', '𝔩': 'frak_l', '𝔪': 'frak_m', '𝔫': 'frak_n', '𝔬': 'frak_o', '𝔭': 'frak_p', '𝔮': 'frak_q', '𝔯': 'frak_r', '𝔰': 'frak_s', '𝔱': 'frak_t', '𝔲': 'frak_u', '𝔳': 'frak_v', '𝔴': 'frak_w', '𝔵': 'frak_x', '𝔶': 'frak_y', '𝔷': 'frak_z',
            '𝔸': 'bb_A', '𝔹': 'bb_B', '𝔻': 'bb_D', '𝔼': 'bb_E', '𝔽': 'bb_F', '𝔾': 'bb_G', '𝕀': 'bb_I', '𝕁': 'bb_J', '𝕂': 'bb_K', '𝕃': 'bb_L', '𝕄': 'bb_M', '𝕆': 'bb_O', '𝕊': 'bb_S', '𝕋': 'bb_T', '𝕌': 'bb_U', '𝕍': 'bb_V', '𝕎': 'bb_W', '𝕏': 'bb_X', '𝕐': 'bb_Y', '𝕒': 'bb_a', '𝕓': 'bb_b', '𝕔': 'bb_c', '𝕕': 'bb_d', '𝕖': 'bb_e', '𝕗': 'bb_f', '𝕘': 'bb_g', '𝕙': 'bb_h', '𝕚': 'bb_i', '𝕛': 'bb_j', '𝕜': 'bb_k', '𝕝': 'bb_l', '𝕞': 'bb_m', '𝕟': 'bb_n', '𝕠': 'bb_o', '𝕡': 'bb_p', '𝕢': 'bb_q', '𝕣': 'bb_r', '𝕤': 'bb_s', '𝕥': 'bb_t', '𝕦': 'bb_u', '𝕧': 'bb_v', '𝕨': 'bb_w', '𝕩': 'bb_x', '𝕪': 'bb_y', '𝕫': 'bb_z',
            '𝕬': 'bf_frak_A', '𝕭': 'bf_frak_B', '𝕮': 'bf_frak_C', '𝕯': 'bf_frak_D', '𝕰': 'bf_frak_E', '𝕱': 'bf_frak_F', '𝕲': 'bf_frak_G', '𝕳': 'bf_frak_H', '𝕴': 'bf_frak_I', '𝕵': 'bf_frak_J', '𝕶': 'bf_frak_K', '𝕷': 'bf_frak_L', '𝕸': 'bf_frak_M', '𝕹': 'bf_frak_N', '𝕺': 'bf_frak_O', '𝕻': 'bf_frak_P', '𝕼': 'bf_frak_Q', '𝕽': 'bf_frak_R', '𝕾': 'bf_frak_S', '𝕿': 'bf_frak_T', '𝖀': 'bf_frak_U', '𝖁': 'bf_frak_V', '𝖂': 'bf_frak_W', '𝖃': 'bf_frak_X', '𝖄': 'bf_frak_Y', '𝖅': 'bf_frak_Z', '𝖆': 'bf_frak_a', '𝖇': 'bf_frak_b', '𝖈': 'bf_frak_c', '𝖉': 'bf_frak_d', '𝖊': 'bf_frak_e', '𝖋': 'bf_frak_f', '𝖌': 'bf_frak_g', '𝖍': 'bf_frak_h', '𝖎': 'bf_frak_i', '𝖏': 'bf_frak_j', '𝖐': 'bf_frak_k', '𝖑': 'bf_frak_l', '𝖒': 'bf_frak_m', '𝖓': 'bf_frak_n', '𝖔': 'bf_frak_o', '𝖕': 'bf_frak_p', '𝖖': 'bf_frak_q', '𝖗': 'bf_frak_r', '𝖘': 'bf_frak_s', '𝖙': 'bf_frak_t', '𝖚': 'bf_frak_u', '𝖛': 'bf_frak_v', '𝖜': 'bf_frak_w', '𝖝': 'bf_frak_x', '𝖞': 'bf_frak_y', '𝖟': 'bf_frak_z',
            '𝖠': 'ss_A', '𝖡': 'ss_B', '𝖢': 'ss_C', '𝖣': 'ss_D', '𝖤': 'ss_E', '𝖥': 'ss_F', '𝖦': 'ss_G', '𝖧': 'ss_H', '𝖨': 'ss_I', '𝖩': 'ss_J', '𝖪': 'ss_K', '𝖫': 'ss_L', '𝖬': 'ss_M', '𝖭': 'ss_N', '𝖮': 'ss_O', '𝖯': 'ss_P', '𝖰': 'ss_Q', '𝖱': 'ss_R', '𝖲': 'ss_S', '𝖳': 'ss_T', '𝖴': 'ss_U', '𝖵': 'ss_V', '𝖶': 'ss_W', '𝖷': 'ss_X', '𝖸': 'ss_Y', '𝖹': 'ss_Z', '𝖺': 'ss_a', '𝖻': 'ss_b', '𝖼': 'ss_c', '𝖽': 'ss_d', '𝖾': 'ss_e', '𝖿': 'ss_f', '𝗀': 'ss_g', '𝗁': 'ss_h', '𝗂': 'ss_i', '𝗃': 'ss_j', '𝗄': 'ss_k', '𝗅': 'ss_l', '𝗆': 'ss_m', '𝗇': 'ss_n', '𝗈': 'ss_o', '𝗉': 'ss_p', '𝗊': 'ss_q', '𝗋': 'ss_r', '𝗌': 'ss_s', '𝗍': 'ss_t', '𝗎': 'ss_u', '𝗏': 'ss_v', '𝗐': 'ss_w', '𝗑': 'ss_x', '𝗒': 'ss_y', '𝗓': 'ss_z',
            '𝗔': 'ss_bf_A', '𝗕': 'ss_bf_B', '𝗖': 'ss_bf_C', '𝗗': 'ss_bf_D', '𝗘': 'ss_bf_E', '𝗙': 'ss_bf_F', '𝗚': 'ss_bf_G', '𝗛': 'ss_bf_H', '𝗜': 'ss_bf_I', '𝗝': 'ss_bf_J', '𝗞': 'ss_bf_K', '𝗟': 'ss_bf_L', '𝗠': 'ss_bf_M', '𝗡': 'ss_bf_N', '𝗢': 'ss_bf_O', '𝗣': 'ss_bf_P', '𝗤': 'ss_bf_Q', '𝗥': 'ss_bf_R', '𝗦': 'ss_bf_S', '𝗧': 'ss_bf_T', '𝗨': 'ss_bf_U', '𝗩': 'ss_bf_V', '𝗪': 'ss_bf_W', '𝗫': 'ss_bf_X', '𝗬': 'ss_bf_Y', '𝗭': 'ss_bf_Z', '𝗮': 'ss_bf_a', '𝗯': 'ss_bf_b', '𝗰': 'ss_bf_c', '𝗱': 'ss_bf_d', '𝗲': 'ss_bf_e', '𝗳': 'ss_bf_f', '𝗴': 'ss_bf_g', '𝗵': 'ss_bf_h', '𝗶': 'ss_bf_i', '𝗷': 'ss_bf_j', '𝗸': 'ss_bf_k', '𝗹': 'ss_bf_l', '𝗺': 'ss_bf_m', '𝗻': 'ss_bf_n', '𝗼': 'ss_bf_o', '𝗽': 'ss_bf_p', '𝗾': 'ss_bf_q', '𝗿': 'ss_bf_r', '𝘀': 'ss_bf_s', '𝘁': 'ss_bf_t', '𝘂': 'ss_bf_u', '𝘃': 'ss_bf_v', '𝘄': 'ss_bf_w', '𝘅': 'ss_bf_x', '𝘆': 'ss_bf_y', '𝘇': 'ss_bf_z',
            '𝘈': 'ss_it_A', '𝘉': 'ss_it_B', '𝘊': 'ss_it_C', '𝘋': 'ss_it_D', '𝘌': 'ss_it_E', '𝘍': 'ss_it_F', '𝘎': 'ss_it_G', '𝘏': 'ss_it_H', '𝘐': 'ss_it_I', '𝘑': 'ss_it_J', '𝘒': 'ss_it_K', '𝘓': 'ss_it_L', '𝘔': 'ss_it_M', '𝘕': 'ss_it_N', '𝘖': 'ss_it_O', '𝘗': 'ss_it_P', '𝘘': 'ss_it_Q', '𝘙': 'ss_it_R', '𝘚': 'ss_it_S', '𝘛': 'ss_it_T', '𝘜': 'ss_it_U', '𝘝': 'ss_it_V', '𝘞': 'ss_it_W', '𝘟': 'ss_it_X', '𝘠': 'ss_it_Y', '𝘡': 'ss_it_Z', '𝘢': 'ss_it_a', '𝘣': 'ss_it_b', '𝘤': 'ss_it_c', '𝘥': 'ss_it_d', '𝘦': 'ss_it_e', '𝘧': 'ss_it_f', '𝘨': 'ss_it_g', '𝘩': 'ss_it_h', '𝘪': 'ss_it_i', '𝘫': 'ss_it_j', '𝘬': 'ss_it_k', '𝘭': 'ss_it_l', '𝘮': 'ss_it_m', '𝘯': 'ss_it_n', '𝘰': 'ss_it_o', '𝘱': 'ss_it_p', '𝘲': 'ss_it_q', '𝘳': 'ss_it_r', '𝘴': 'ss_it_s', '𝘵': 'ss_it_t', '𝘶': 'ss_it_u', '𝘷': 'ss_it_v', '𝘸': 'ss_it_w', '𝘹': 'ss_it_x', '𝘺': 'ss_it_y', '𝘻': 'ss_it_z',
            '𝘼': 'ss_bf_it_A', '𝘽': 'ss_bf_it_B', '𝘾': 'ss_bf_it_C', '𝘿': 'ss_bf_it_D', '𝙀': 'ss_bf_it_E', '𝙁': 'ss_bf_it_F', '𝙂': 'ss_bf_it_G', '𝙃': 'ss_bf_it_H', '𝙄': 'ss_bf_it_I', '𝙅': 'ss_bf_it_J', '𝙆': 'ss_bf_it_K', '𝙇': 'ss_bf_it_L', '𝙈': 'ss_bf_it_M', '𝙉': 'ss_bf_it_N', '𝙊': 'ss_bf_it_O', '𝙋': 'ss_bf_it_P', '𝙌': 'ss_bf_it_Q', '𝙍': 'ss_bf_it_R', '𝙎': 'ss_bf_it_S', '𝙏': 'ss_bf_it_T', '𝙐': 'ss_bf_it_U', '𝙑': 'ss_bf_it_V', '𝙒': 'ss_bf_it_W', '𝙓': 'ss_bf_it_X', '𝙔': 'ss_bf_it_Y', '𝙕': 'ss_bf_it_Z', '𝙖': 'ss_bf_it_a', '𝙗': 'ss_bf_it_b', '𝙘': 'ss_bf_it_c', '𝙙': 'ss_bf_it_d', '𝙚': 'ss_bf_it_e', '𝙛': 'ss_bf_it_f', '𝙜': 'ss_bf_it_g', '𝙝': 'ss_bf_it_h', '𝙞': 'ss_bf_it_i', '𝙟': 'ss_bf_it_j', '𝙠': 'ss_bf_it_k', '𝙡': 'ss_bf_it_l', '𝙢': 'ss_bf_it_m', '𝙣': 'ss_bf_it_n', '𝙤': 'ss_bf_it_o', '𝙥': 'ss_bf_it_p', '𝙦': 'ss_bf_it_q', '𝙧': 'ss_bf_it_r', '𝙨': 'ss_bf_it_s', '𝙩': 'ss_bf_it_t', '𝙪': 'ss_bf_it_u', '𝙫': 'ss_bf_it_v', '𝙬': 'ss_bf_it_w', '𝙭': 'ss_bf_it_x', '𝙮': 'ss_bf_it_y', '𝙯': 'ss_bf_it_z',
            '𝙰': 'mono_A', '𝙱': 'mono_B', '𝙲': 'mono_C', '𝙳': 'mono_D', '𝙴': 'mono_E', '𝙵': 'mono_F', '𝙶': 'mono_G', '𝙷': 'mono_H', '𝙸': 'mono_I', '𝙹': 'mono_J', '𝙺': 'mono_K', '𝙻': 'mono_L', '𝙼': 'mono_M', '𝙽': 'mono_N', '𝙾': 'mono_O', '𝙿': 'mono_P', '𝚀': 'mono_Q', '𝚁': 'mono_R', '𝚂': 'mono_S', '𝚃': 'mono_T', '𝚄': 'mono_U', '𝚅': 'mono_V', '𝚆': 'mono_W', '𝚇': 'mono_X', '𝚈': 'mono_Y', '𝚉': 'mono_Z', '𝚊': 'mono_a', '𝚋': 'mono_b', '𝚌': 'mono_c', '𝚍': 'mono_d', '𝚎': 'mono_e', '𝚏': 'mono_f', '𝚐': 'mono_g', '𝚑': 'mono_h', '𝚒': 'mono_i', '𝚓': 'mono_j', '𝚔': 'mono_k', '𝚕': 'mono_l', '𝚖': 'mono_m', '𝚗': 'mono_n', '𝚘': 'mono_o', '𝚙': 'mono_p', '𝚚': 'mono_q', '𝚛': 'mono_r', '𝚜': 'mono_s', '𝚝': 'mono_t', '𝚞': 'mono_u', '𝚟': 'mono_v', '𝚠': 'mono_w', '𝚡': 'mono_x', '𝚢': 'mono_y', '𝚣': 'mono_z',
            '𝜜': 'bf_it_Alpha', '𝜝': 'bf_it_Beta', '𝜞': 'bf_it_Gamma', '𝜟': 'bf_it_Delta', '𝜠': 'bf_it_Epsilon', '𝜡': 'bf_it_Zeta', '𝜢': 'bf_it_Eta', '𝜣': 'bf_it_Theta', '𝜤': 'bf_it_Iota', '𝜥': 'bf_it_Kappa', '𝜦': 'bf_it_Lamda', '𝜧': 'bf_it_Mu', '𝜨': 'bf_it_Nu', '𝜩': 'bf_it_Xi', '𝜪': 'bf_it_Omicron', '𝜫': 'bf_it_Pi', '𝜬': 'bf_it_Rho', '𝜭': 'bf_it_Theta', '𝜮': 'bf_it_Sigma', '𝜯': 'bf_it_Tau', '𝜰': 'bf_it_Upsilon', '𝜱': 'bf_it_Phi', '𝜲': 'bf_it_Chi', '𝜳': 'bf_it_Psi', '𝜴': 'bf_it_Omega', '𝜵': 'bf_it_nabla', '𝜶': 'bf_it_alpha', '𝜷': 'bf_it_beta', '𝜸': 'bf_it_gamma', '𝜹': 'bf_it_delta', '𝜺': 'bf_it_epsilon', '𝜻': 'bf_it_zeta', '𝜼': 'bf_it_eta', '𝜽': 'bf_it_theta', '𝜾': 'bf_it_iota', '𝜿': 'bf_it_kappa', '𝝀': 'bf_it_lamda', '𝝁': 'bf_it_mu', '𝝂': 'bf_it_nu', '𝝃': 'bf_it_xi', '𝝄': 'bf_it_omicron', '𝝅': 'bf_it_pi', '𝝆': 'bf_it_rho', '𝝇': 'bf_it_sigma', '𝝈': 'bf_it_sigma', '𝝉': 'bf_it_tau', '𝝊': 'bf_it_upsilon', '𝝋': 'bf_it_phi', '𝝌': 'bf_it_chi', '𝝍': 'bf_it_psi', '𝝎': 'bf_it_omega', '𝝏': 'bf_it_partial_differential', '𝝐': 'bf_it_epsilon', '𝝑': 'bf_it_theta', '𝝒': 'bf_it_kappa', '𝝓': 'bf_it_phi', '𝝔': 'bf_it_rho', '𝝕': 'bf_it_pi',
            '𝝖': 'ss_bf_Alpha', '𝝗': 'ss_bf_Beta', '𝝘': 'ss_bf_Gamma', '𝝙': 'ss_bf_Delta', '𝝚': 'ss_bf_Epsilon', '𝝛': 'ss_bf_Zeta', '𝝜': 'ss_bf_Eta', '𝝝': 'ss_bf_Theta', '𝝞': 'ss_bf_Iota', '𝝟': 'ss_bf_Kappa', '𝝠': 'ss_bf_Lamda', '𝝡': 'ss_bf_Mu', '𝝢': 'ss_bf_Nu', '𝝣': 'ss_bf_Xi', '𝝤': 'ss_bf_Omicron', '𝝥': 'ss_bf_Pi', '𝝦': 'ss_bf_Rho', '𝝧': 'ss_bf_Theta', '𝝨': 'ss_bf_Sigma', '𝝩': 'ss_bf_Tau', '𝝪': 'ss_bf_Upsilon', '𝝫': 'ss_bf_Phi', '𝝬': 'ss_bf_Chi', '𝝭': 'ss_bf_Psi', '𝝮': 'ss_bf_Omega', '𝝯': 'ss_bf_nabla', '𝝰': 'ss_bf_alpha', '𝝱': 'ss_bf_beta', '𝝲': 'ss_bf_gamma', '𝝳': 'ss_bf_delta', '𝝴': 'ss_bf_epsilon', '𝝵': 'ss_bf_zeta', '𝝶': 'ss_bf_eta', '𝝷': 'ss_bf_theta', '𝝸': 'ss_bf_iota', '𝝹': 'ss_bf_kappa', '𝝺': 'ss_bf_lamda', '𝝻': 'ss_bf_mu', '𝝼': 'ss_bf_nu', '𝝽': 'ss_bf_xi', '𝝾': 'ss_bf_omicron', '𝝿': 'ss_bf_pi', '𝞀': 'ss_bf_rho', '𝞁': 'ss_bf_sigma', '𝞂': 'ss_bf_sigma', '𝞃': 'ss_bf_tau', '𝞄': 'ss_bf_upsilon', '𝞅': 'ss_bf_phi', '𝞆': 'ss_bf_chi', '𝞇': 'ss_bf_psi', '𝞈': 'ss_bf_omega', '𝞉': 'ss_bf_partial_differential', '𝞊': 'ss_bf_epsilon', '𝞋': 'ss_bf_theta', '𝞌': 'ss_bf_kappa', '𝞍': 'ss_bf_phi', '𝞎': 'ss_bf_rho', '𝞏': 'ss_bf_pi',
            '𝞐': 'ss_bf_it_Alpha', '𝞑': 'ss_bf_it_Beta', '𝞒': 'ss_bf_it_Gamma', '𝞓': 'ss_bf_it_Delta', '𝞔': 'ss_bf_it_Epsilon', '𝞕': 'ss_bf_it_Zeta', '𝞖': 'ss_bf_it_Eta', '𝞗': 'ss_bf_it_Theta', '𝞘': 'ss_bf_it_Iota', '𝞙': 'ss_bf_it_Kappa', '𝞚': 'ss_bf_it_Lamda', '𝞛': 'ss_bf_it_Mu', '𝞜': 'ss_bf_it_Nu', '𝞝': 'ss_bf_it_Xi', '𝞞': 'ss_bf_it_Omicron', '𝞟': 'ss_bf_it_Pi', '𝞠': 'ss_bf_it_Rho', '𝞡': 'ss_bf_it_Theta', '𝞢': 'ss_bf_it_Sigma', '𝞣': 'ss_bf_it_Tau', '𝞤': 'ss_bf_it_Upsilon', '𝞥': 'ss_bf_it_Phi', '𝞦': 'ss_bf_it_Chi', '𝞧': 'ss_bf_it_Psi', '𝞨': 'ss_bf_it_Omega', '𝞩': 'ss_bf_it_nabla', '𝞪': 'ss_bf_it_alpha', '𝞫': 'ss_bf_it_beta', '𝞬': 'ss_bf_it_gamma', '𝞭': 'ss_bf_it_delta', '𝞮': 'ss_bf_it_epsilon', '𝞯': 'ss_bf_it_zeta', '𝞰': 'ss_bf_it_eta', '𝞱': 'ss_bf_it_theta', '𝞲': 'ss_bf_it_iota', '𝞳': 'ss_bf_it_kappa', '𝞴': 'ss_bf_it_lamda', '𝞵': 'ss_bf_it_mu', '𝞶': 'ss_bf_it_nu', '𝞷': 'ss_bf_it_xi', '𝞸': 'ss_bf_it_omicron', '𝞹': 'ss_bf_it_pi', '𝞺': 'ss_bf_it_rho', '𝞻': 'ss_bf_it_sigma', '𝞼': 'ss_bf_it_sigma', '𝞽': 'ss_bf_it_tau', '𝞾': 'ss_bf_it_upsilon', '𝞿': 'ss_bf_it_phi', '𝟀': 'ss_bf_it_chi', '𝟁': 'ss_bf_it_psi', '𝟂': 'ss_bf_it_omega', '𝟃': 'ss_bf_it_partial_differential', '𝟄': 'ss_bf_it_epsilon', '𝟅': 'ss_bf_it_theta', '𝟆': 'ss_bf_it_kappa', '𝟇': 'ss_bf_it_phi', '𝟈': 'ss_bf_it_rho', '𝟉': 'ss_bf_it_pi',
            '𝟊': 'bf_Digamma', '𝟋': 'bf_digamma',
            '𝟘': 'bb_0', '𝟙': 'bb_1', '𝟚': 'bb_2', '𝟛': 'bb_3', '𝟜': 'bb_4', '𝟝': 'bb_5', '𝟞': 'bb_6', '𝟟': 'bb_7', '𝟠': 'bb_8', '𝟡': 'bb_9',
            '𝟢': 'ss_0', '𝟣': 'ss_1', '𝟤': 'ss_2', '𝟥': 'ss_3', '𝟦': 'ss_4', '𝟧': 'ss_5', '𝟨': 'ss_6', '𝟩': 'ss_7', '𝟪': 'ss_8', '𝟫': 'ss_9',
            '𝟬': 'ss_bf_0', '𝟭': 'ss_bf_1', '𝟮': 'ss_bf_2', '𝟯': 'ss_bf_3', '𝟰': 'ss_bf_4', '𝟱': 'ss_bf_5', '𝟲': 'ss_bf_6', '𝟳': 'ss_bf_7', '𝟴': 'ss_bf_8', '𝟵': 'ss_bf_9',
            '𝟶': 'mono_0', '𝟷': 'mono_1', '𝟸': 'mono_2', '𝟹': 'mono_3', '𝟺': 'mono_4', '𝟻': 'mono_5', '𝟼': 'mono_6', '𝟽': 'mono_7', '𝟾': 'mono_8', '𝟿': 'mono_9'
            }
        self.special_symbol_dict = {'∂':'dee', '⁰':'0', '¹':'1', '²':'2', 'ᵀ':'T'}  # Python and MATLAB can use some Unicode symbols, the symbols from this dict must be converted by all backends
        self.declared_symbols = set()
        self.used_params = []
        self.der_vars = [] # variables in derivatives
        self.der_vars_mapping = {}  # mapping to new names
        self.opt_syms = []
        self.mesh_dict = {}
        self.duplicate_func_list = []    # overloaded func types incompatible in cpp
        self.mesh_type_list = []    # different mesh types in current file

    def add_name_conventions(self, con_dict):
        for key, value in con_dict.items():
            self.logger.debug("name:{} -> {}".format(key, value))
            if key in self.name_convention_dict:
                self.logger.debug("{} already exists".format(key))
            self.name_convention_dict[key] = value

    def del_name_conventions(self, con_dict):
        for key in con_dict:
            self.logger.debug("del name:{}".format(key))
            if key in self.name_convention_dict:
                del self.name_convention_dict[key]

    def is_local_param(self, sym):
        valid = False
        for k, v in self.local_func_dict.items():
            if len(v) > 0:
                if sym in v:
                    valid = True
                    break
        return valid

    def convert_seq_dim_dict(self):
        seq_dict = {}
        for key, value_dict in self.get_cur_param_data().seq_dim_dict.items():
            for sym, index_list in value_dict.items():
                if sym not in seq_dict:
                    seq_dict[sym] = {}
                for index_str in index_list:
                    seq_dict[sym][index_str] = key
        return seq_dict

    def get_intersect_list(self):
        seq_set = self.get_dynamic_seq_set()
        subs_list = []
        for subs, subs_dict in self.get_cur_param_data().subscripts.items():
            subs_set = set(subs_dict)
            intersection = subs_set.intersection(seq_set)
            if len(intersection) > 1:
                subs_list.append(intersection)
        return subs_list

    def get_dynamic_seq_set(self):
        dym_seq_list = []
        for key, value in self.get_cur_param_data().seq_dim_dict.items():
            dym_seq_list += value.keys()
        return set(dym_seq_list)

    def get_same_seq_list(self, name):
        same_seq_list = []
        for key, value in self.get_cur_param_data().seq_dim_dict.items():
            if name in value:
                same_seq_list.append(value)
        return same_seq_list

    def get_same_seq_symbols(self, name):
        same_symbols = []
        for key, value in self.get_cur_param_data().seq_dim_dict.items():
            if name in value:
                same_symbols += value.keys()
        same_symbols = set(same_symbols)
        same_symbols.remove(name)
        return same_symbols

    @property
    def parameters(self):
        return self.get_cur_param_data().parameters

    @parameters.setter
    def parameters(self, value):
        self.get_cur_param_data().parameters = value

    @property
    def symtable(self):
        return self.get_cur_param_data().symtable

    @symtable.setter
    def symtable(self, value):
        self.get_cur_param_data().symtable = value

    def get_sym_type(self, sym):
        """
        find the type for a symbol, uses local scope if possible, otherwise uses global symtable
        :param sym: symbol name
        :return: la type
        """
        node_type = LaVarType(VarTypeEnum.INVALID)
        resolved = False
        for cur_index in range(len(self.scope_list)):
            cur_scope = self.scope_list[len(self.scope_list) - 1 - cur_index]
            if cur_scope == 'global':
                cur_symtable = self.main_param.symtable
            else:
                cur_symtable = self.func_data_dict[cur_scope].params_data.symtable
            if sym in cur_symtable:
                node_type = cur_symtable[sym]
                resolved = True
                break
        if not resolved:
            if sym in self.extra_symtable:
                node_type = self.extra_symtable[sym]
        return node_type

    def get_cur_param_data(self, func_name=''):
        # either main where/given block or local function block
        # if func_name != '':
        #     if func_name in self.func_data_dict:
        #         return self.func_data_dict[func_name].params_data
        # if self.local_func_parsing:
        #     if self.local_func_name in self.func_data_dict:
        #         return self.func_data_dict[self.local_func_name].params_data
        # return self.main_param
        cur_scope = self.scope_list[-1]
        if cur_scope != 'global':
            return self.func_data_dict[cur_scope].params_data
        return self.main_param

    def generate_var_name(self, base='sym'):
        index = -1
        if base in self.name_cnt_dict:
            index = self.name_cnt_dict[base]
        index += 1
        valid = False
        ret = ""
        while not valid:
            if index == 0:
                ret = "{}{}".format(self.new_id_prefix, base)
            else:
                ret = "{}{}_{}".format(self.new_id_prefix, base, index)
            if ret not in self.symtable:
                valid = True
            index += 1
        self.name_cnt_dict[base] = index - 1
        return ret

    def push_scope(self, scope):
        self.scope_list.append(scope)

    def pop_scope(self):
        # be careful on the position
        self.scope_list.pop()

    def print_symbols(self):
        la_debug("CodeGen ==================================================================================================================")
        self.logger.info("symtable")
        def get_type_desc(v):
            extra = ''
            if v.var_type == VarTypeEnum.MATRIX:
                if v.sparse:
                    extra = ", sparse, rows:{}, cols:{}".format(v.rows, v.cols)
                else:
                    extra = ", rows:{}, cols:{}".format(v.rows, v.cols)
            elif v.var_type == VarTypeEnum.VECTOR:
                extra = ", rows:{}".format(v.rows)
            elif v.var_type == VarTypeEnum.SEQUENCE or v.var_type == VarTypeEnum.SET:
                extra = ", size:{}".format(v.size)
            elif v.var_type == VarTypeEnum.FUNCTION:
                par_list = []
                for par in v.params:
                    par_list.append(get_type_desc(par))
                ret_list = []
                for cur_ret in v.ret:
                    ret_list.append(get_type_desc(cur_ret))
                extra = ": " + '; '.join(par_list) + ' -> ' + '; '.join(ret_list)
            return str(v.var_type) + extra
        for (k, v) in self.symtable.items():
            if v is not None:
                self.logger.info(k + ':' + get_type_desc(v))
        param_data_list = []
        param_data_list += self.func_data_dict.values()
        param_data_list.append(self.main_param)
        self.logger.info("param_data_list cnt: {}\n".format(len(param_data_list)))
        for param_data in param_data_list:
            if isinstance(param_data, LocalFuncData):
                self.logger.info("local function name:" + str(param_data.name))
                param_data = param_data.params_data
            else:
                self.logger.info("Main param:")
            self.logger.info("symtable:")
            for k, v in param_data.symtable.items():
                self.logger.info("{} : {}".format(k, v.get_signature()))
            self.logger.info("parameters: {}".format(param_data.parameters, hex(id(param_data.parameters))))
            self.logger.info("subscripts: {}".format(param_data.subscripts, hex(id(param_data.subscripts))))
            self.logger.info("dim_dict: {}".format(param_data.dim_dict, hex(id(param_data.dim_dict))))
            self.logger.info("seq_dim_dict: {}".format(param_data.seq_dim_dict, hex(id(param_data.seq_dim_dict))))
            self.logger.info("dim_seq_set: {}".format(param_data.dim_seq_set, hex(id(param_data.dim_seq_set))))
            self.logger.info("same_dim_list: {}".format(param_data.same_dim_list, hex(id(param_data.same_dim_list))))
            self.logger.info("sub_name_dict: {}\n".format(param_data.sub_name_dict, hex(id(param_data.sub_name_dict))))
        self.logger.info("used params:{}".format(self.used_params))
        self.logger.info("der vars:{}".format(self.der_vars))
        self.logger.info("optimized variables:{}".format(self.opt_syms))
        self.logger.info("der_defined_lhs_list:{}".format(self.der_defined_lhs_list))
        self.logger.info("lhs_list:{}".format(self.lhs_list))
        self.logger.info("lhs_on_der:{}".format(self.lhs_on_der))

    def init_type(self, type_walker, func_name):
        self.main_param = type_walker.main_param
        # self.symtable = self.main_param.symtable
        # self.parameters = self.main_param.parameters
        for key in self.symtable.keys():
            self.def_dict[key] = False
        self.func_data_dict = type_walker.func_data_dict  # local function name -> LocalFuncData
        self.name_cnt_dict = type_walker.name_cnt_dict
        self.ret_symbol = type_walker.ret_symbol
        self.unofficial_method = type_walker.unofficial_method
        self.has_opt = type_walker.has_opt
        self.has_derivative = type_walker.has_derivative
        self.need_mutator = type_walker.need_mutator
        self.lhs_list = type_walker.lhs_list
        self.la_content = type_walker.la_content
        self.local_func_syms = type_walker.local_func_syms
        self.local_func_dict = type_walker.local_func_dict
        self.extra_symtable = type_walker.extra_symtable
        self.opt_dict = type_walker.opt_dict
        self.used_params = type_walker.used_params
        self.der_vars = type_walker.der_vars
        self.der_defined_lhs_list = type_walker.der_defined_lhs_list
        self.lhs_on_der = type_walker.lhs_on_der            # symbol defined with gradient or hessian
        self.der_vars_mapping.clear()
        for param in self.der_vars:
            if self.get_sym_type(param).is_scalar():
                self.der_vars_mapping[param] = param    
            else:
                self.der_vars_mapping[param] = self.generate_var_name("new_{}".format(param))    # new variable with var type
        self.builtin_module_dict = type_walker.builtin_module_dict
        self.opt_syms = type_walker.opt_syms
        self.mesh_dict = type_walker.mesh_dict
        self.class_only = type_walker.class_only
        self.mesh_type_list = type_walker.mesh_type_list
        if func_name is not None:
            self.func_name = func_name.replace(' ','')
        else:
            self.func_name = CLASS_NAME
        # self.print_symbols()
        self.declared_symbols.clear()
        self.local_func_def = ''
        self.comment_dict.clear()
        self.duplicate_func_list.clear()

    def visit_code(self, node, **kwargs):
        self.content = self.pre_str + self.visit(node) + self.post_str

    def visit_to_matrix(self, node, **kwargs):
        return self.visit(node.item, **kwargs)
    def visit_to_double(self, node, **kwargs):
        return self.visit(node.item, **kwargs)

    def visit_double(self, node, **kwargs):
        content = str(node.value)
        return CodeNodeInfo(content)

    def visit_fraction(self, node, **kwargs):
        return CodeNodeInfo("({}/{})".format(node.numerator, node.denominator))

    def visit_integer(self, node, **kwargs):
        if node.value < 0:
            content = "({})".format(node.value)
        else:
            content = str(node.value)
        return CodeNodeInfo(content)

    def is_main_scope(self):
        return self.scope_list[-1] == 'global'

    def is_keyword(self, name):
        return is_keyword(name, parser_type=self.parse_type)

    def get_bin_comp_str(self, comp_type):
        op = ''
        if comp_type == IRNodeType.Eq:
            op = '=='
        elif comp_type == IRNodeType.Ne:
            op = '!='
        elif comp_type == IRNodeType.Lt:
            op = '<'
        elif comp_type == IRNodeType.Le:
            op = '<='
        elif comp_type == IRNodeType.Gt:
            op = '>'
        elif comp_type == IRNodeType.Ge:
            op = '>='
        return op

    def get_int_dim(self, dim_list):
        for cur_dim in dim_list:
            if isinstance(cur_dim, int):
                return cur_dim
        return -1

    def get_dim_check_str(self):
        check_list = []
        for cur_set in self.get_cur_param_data().same_dim_list:
            cur_list = list(cur_set)
            for cur_index in range(1, len(cur_list)):
                check_list.append("{} == {}".format(cur_list[0], cur_list[cur_index]))
        return check_list

    def update_prelist_str(self, pre_list, prefix):
        lines = []
        for line in pre_list:
            split_list = line.split('\n')
            for split in split_list:
                if split != '':
                    lines.append(split)
        return prefix + "\n{}".format(prefix).join(lines) + '\n'

    def convert_bound_symbol(self, name):
        if name in self.get_cur_param_data().dim_seq_set:
            main_dict = self.get_cur_param_data().dim_dict[name]
            for key, value in main_dict.items():
                return key
        return name

    def convert_unicode(self, name):
        if not self.has_special_symbol(name) and '`' not in name and self.parse_type != ParserTypeEnum.MATLAB:
            return name
        remove_list = ['`$', '$`', '`', '(', ')', '{', '}', '\\', '-']
        for rm in remove_list:
            name = name.replace(rm, '')
        new_list = []
        pre_unicode = False
        if name.isnumeric() or name[0].isnumeric():
            name = "num{}".format(name)
        for e in name:
            if e in self.special_symbol_dict:
                new_list.append(self.special_symbol_dict[e])
                continue
            if self.parse_type == ParserTypeEnum.NUMPY or self.parse_type == ParserTypeEnum.MATLAB or self.parse_type == ParserTypeEnum.EIGEN:
                # make sure identifier is valid in numpy
                if e.isnumeric() and e in self.uni_num_dict:
                    e = self.uni_num_dict[e]
            if ((self.parse_type != ParserTypeEnum.MATLAB or e.isascii()) and e.isalnum()) or e == '_':
                if pre_unicode:
                    new_list.append('_')
                    pre_unicode = False
                new_list.append(e)
            elif e.isspace():
                new_list.append('')
            else:
                if self.parse_type == ParserTypeEnum.MATLAB and e in self.common_symbol_dict:
                    new_list.append(self.common_symbol_dict[e])
                else:
                    try:
                        if not pre_unicode:
                            new_list.append('_')
                        new_list.append(unicodedata.name(e).lower().replace(' ', '_'))
                    except KeyError:
                        continue
                new_list.append('_')
                pre_unicode = True
        if len(new_list) > 0 and new_list[0].isnumeric():
            new_list.insert(0, '_')
        ret = re.sub("_+", "_", ''.join(new_list)).strip("_")
        return ret

    def fill_comment(self, content):
        for k, v in self.comment_dict.items():
            comment_re = re.compile(
                dedent(r'''(?P<prefix>[ \t]*){}'''.format(k)),
                re.DOTALL | re.VERBOSE
                )
            for m in comment_re.finditer(content):
                if m.group('prefix'):
                    content = content.replace(m.group(), self.update_prelist_str([v], m.group('prefix'))[:-1] )
                else:
                    content = content.replace(m.group(), v)
                continue
        return content

    def has_special_symbol(self, target):
        for k in list(self.special_symbol_dict.keys()):
            if k in target:
                return True
        return False
    def trim_content(self, content):
        # convert special string in identifiers
        res = content
        ids_list = list(self.symtable.keys())
        for ids in self.get_cur_param_data().ids_dict.keys():
            all_ids = self.get_all_ids(ids)
            # these can contain asterisks from vector/matrix slicing 
            ids_list += all_ids[1]
        for key, func_data in self.func_data_dict.items():
            ids_list += list(func_data.params_data.symtable.keys())
        names_dict = []
        # purge asterisks (and make unique, why not)
        ids_list = [x for x in list(set(ids_list)) if x != '*']
        # This is conducting the replacements at the output string level rather
        # than the variable name level. If one name appears in another (e.g., φ
        # in `x(φ)` then this leads to clashes, hence the awkward sort.
        ids_list.sort(key=len,reverse=True)
        def replace_str(full, target):
            new_str = self.convert_unicode(target)
            new_str = new_str.replace('-', '_')
            if new_str != target:
                while new_str in names_dict or new_str in self.symtable.keys() or self.is_keyword(new_str):
                    if self.parse_type == ParserTypeEnum.MATLAB:
                        new_str = new_str + '_'
                    else:
                        new_str = '_' + new_str
                names_dict.append(new_str)
                full = full.replace(target, new_str)
            return full
        for special in ids_list:
            if self.has_special_symbol(special):
                res = replace_str(res, special)
                continue
            if '`' not in special and self.parse_type != ParserTypeEnum.MATLAB:
                continue
            # don't convert numbers...
            if special.isnumeric():
                continue
            res = replace_str(res, special)
        return self.fill_comment(res)

    def filter_symbol(self, symbol):
        if '`' in symbol:
            new_symbol = symbol.replace('`', '')
            if new_symbol.isnumeric():
                new_symbol = "num{}".format(new_symbol)
            else:
                if not self.pattern.fullmatch(new_symbol) or is_keyword(new_symbol):
                    new_symbol = symbol
        else:
            new_symbol = symbol
        return new_symbol

    def contain_subscript(self, identifier):
        if identifier in self.get_cur_param_data().ids_dict:
            return self.get_cur_param_data().ids_dict[identifier].contain_subscript()
        return False

    def get_all_ids(self, identifier):
        if identifier in self.get_cur_param_data().ids_dict:
            return self.get_cur_param_data().ids_dict[identifier].get_all_ids()
        res = identifier.split('_')
        subs = []
        for index in range(len(res[1])):
            subs.append(res[1][index])
        return [res[0], subs]

    def get_result_type(self):
        # return self.func_name + "ResultType"
        return self.func_name

    def get_main_id(self, identifier):
        if identifier in self.get_cur_param_data().ids_dict:
            return self.get_cur_param_data().ids_dict[identifier].get_main_id()
        if self.contain_subscript(identifier):
            ret = self.get_all_ids(identifier)
            return ret[0]
        return identifier
