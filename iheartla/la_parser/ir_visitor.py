import re
from .ir import *
from ..la_tools.la_logger import *
from ..la_tools.la_helper import *
import unicodedata


class IRVisitor(object):
    def __init__(self, parse_type=None):
        super().__init__()
        self.pre_str = ''
        self.post_str = ''
        self.symtable = {}
        self.tmp_symtable = {}
        self.def_dict = {}
        self.parameters = set()
        self.subscripts = {}
        self.dim_dict = {}
        self.sub_name_dict = {}
        self.name_cnt_dict = {}
        self.same_dim_list = []
        self.ids_dict = {}  # identifiers with subscripts
        self.ret_symbol = None
        self.unofficial_method = False  # matrix pow only(eigen)
        self.content = ''
        self.parse_type = parse_type
        self.logger = LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT)
        self.name_convention_dict = {}  # eg:i -> i[0]
        self.func_name = 'myExpression'
        self.param_name_test = 'p'  # param name for test function
        self.convert_matrix = False
        self.lhs_list = []
        self.pattern = re.compile("[A-Za-z]+")
        self.la_content = ''
        self.new_id_prefix = ''  # _
        self.uni_num_dict = {'₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4', '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
                             '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9'}
        self.common_symbol_dict = { 'Α': 'Alpha', 'Β': 'Beta', 'Γ': 'Gamma', 'Δ': 'Delta', 'Ε': 'Epsilon', 'Ζ': 'Zeta', 'Η': 'Eta', 'Θ': 'Theta', 'Ι': 'Iota', 'Κ': 'Kappa', 'Λ': 'Lambda', 'Μ': 'Mu', 'Ν': 'Nu', 'Ξ': 'Xi', 'Ο': 'Omicron', 'Π': 'Pi', 'Ρ': 'Rho', 'Σ': 'Sigma', '∑': 'Sigma', 'Τ': 'Tau', 'Υ': 'Upsilon', 'Φ': 'Phi', 'Χ': 'Chi', 'Ψ': 'Psi', 'Ω': 'Omega', 'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta', 'ε': 'epsilon', 'ζ': 'zeta', 'η': 'eta', 'θ': 'theta', 'ι': 'iota', 'κ': 'kappa', 'λ': 'lambda', 'μ': 'mu', 'ν': 'nu', 'ξ': 'xi', 'ο': 'omicron', 'π': 'pi', 'ρ': 'rho', 'ς': 'sigma', 'σ': 'sigma', 'τ': 'tau', 'υ': 'upsilon', 'ϕ': 'phi', 'φ': 'phi', 'χ': 'chi', 'ψ': 'psi', 'ω': 'omega', 'ᵢ': '_i', 'ⱼ': '_j', 'ₖ': '_k', '\u0302': '_hat'}
        self.declared_symbols = set()

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

    def generate_var_name(self, base):
        index = -1
        if base in self.name_cnt_dict:
            index = self.name_cnt_dict[base]
        index += 1
        valid = False
        ret = ""
        while not valid:
            ret = "{}{}_{}".format(self.new_id_prefix, base, index)
            if ret not in self.symtable:
                valid = True
            index += 1
        self.name_cnt_dict[base] = index - 1
        return ret

    def print_symbols(self):
        self.logger.info("symtable:")
        for (k, v) in self.symtable.items():
            dims = ""
            if v.var_type == VarTypeEnum.MATRIX:
                if v.sparse:
                    dims = ", sparse, rows:{}, cols:{}".format(v.rows, v.cols)
                else:
                    dims = ", rows:{}, cols:{}".format(v.rows, v.cols)
            elif v.var_type == VarTypeEnum.VECTOR:
                dims = ", rows:{}".format(v.rows)
            elif v.var_type == VarTypeEnum.SEQUENCE or v.var_type == VarTypeEnum.SET:
                dims = ", size:{}".format(v.size)
            self.logger.info(k + ':' + str(v.var_type) + dims)
        self.logger.info("parameters:\n" + str(self.parameters))
        self.logger.info("subscripts:\n" + str(self.subscripts))
        self.logger.info("dim_dict:\n" + str(self.dim_dict))
        self.logger.info("sub_name_dict:\n" + str(self.sub_name_dict) + '\n')

    def init_type(self, type_walker, func_name):
        self.symtable = type_walker.symtable
        self.tmp_symtable = type_walker.tmp_symtable
        for key in self.symtable.keys():
            self.def_dict[key] = False
        self.parameters = type_walker.parameters
        self.subscripts = type_walker.subscripts
        self.dim_dict = type_walker.dim_dict
        self.ids_dict = type_walker.ids_dict
        self.sub_name_dict = type_walker.sub_name_dict
        self.name_cnt_dict = type_walker.name_cnt_dict
        self.ret_symbol = type_walker.ret_symbol
        self.unofficial_method = type_walker.unofficial_method
        self.lhs_list = type_walker.lhs_list
        self.la_content = type_walker.la_content
        self.same_dim_list = type_walker.same_dim_list
        if func_name is not None:
            self.func_name = func_name
        # self.print_symbols()
        self.declared_symbols.clear()

    def visit_code(self, node, **kwargs):
        self.content = ''
        self.content = self.pre_str + self.visit(node) + self.post_str

    def visit(self, node, **kwargs):
        type_func = {
            # base
            IRNodeType.Id: "visit_id",
            IRNodeType.Double: "visit_double",
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
            IRNodeType.AddSub: "visit_add_sub",
            IRNodeType.Summation: "visit_summation",
            IRNodeType.Norm: "visit_norm",
            IRNodeType.Transpose: "visit_transpose",
            IRNodeType.Squareroot: "visit_squareroot",
            IRNodeType.Power: "visit_power",
            IRNodeType.Solver: "visit_solver",
            IRNodeType.Derivative: "visit_derivative",
            IRNodeType.MathFunc: "visit_math_func",
            IRNodeType.Optimize: "visit_optimize",
            IRNodeType.Domain: "visit_domain",
            IRNodeType.Integral: "visit_integral",
            IRNodeType.InnerProduct: "visit_inner_product",
            IRNodeType.FroProduct: "visit_fro_product",
            IRNodeType.HadamardProduct: "visit_hadamard_product",
            IRNodeType.CrossProduct: "visit_cross_product",
            IRNodeType.KroneckerProduct: "visit_kronecker_product",
            IRNodeType.DotProduct: "visit_dot_product",
            # matrix
            IRNodeType.Matrix: "visit_matrix",
            IRNodeType.MatrixRows: "visit_matrix_rows",
            IRNodeType.MatrixRow: "visit_matrix_row",
            IRNodeType.MatrixRowCommas: "visit_matrix_row_commas",
            IRNodeType.ExpInMatrix: "visit_exp_in_matrix",
            IRNodeType.SparseMatrix: "visit_sparse_matrix",
            IRNodeType.SparseIfs: "visit_sparse_ifs",
            IRNodeType.SparseIf: "visit_sparse_if",
            IRNodeType.SparseOther: "visit_sparse_other",
            IRNodeType.NumMatrix: "visit_num_matrix",
            IRNodeType.Vector: "visit_vector",
            IRNodeType.ToMatrix: "visit_to_matrix",
            #
            IRNodeType.MatrixIndex: "visit_matrix_index",
            IRNodeType.VectorIndex: "visit_vector_index",
            IRNodeType.SequenceIndex: "visit_sequence_index",
            # where block
            IRNodeType.ParamsBlock: "visit_params_block",
            IRNodeType.WhereConditions: "visit_where_conditions",
            IRNodeType.WhereCondition: "visit_where_condition",
            IRNodeType.MatrixType: "visit_matrix_type",
            IRNodeType.VectorType: "visit_vector_type",
            IRNodeType.SetType: "visit_set_type",
            IRNodeType.ScalarType: "visit_scalar_type",
            IRNodeType.FunctionType: "visit_function_type",
            # derivatives
            IRNodeType.Import: "visit_import",
        }
        func = getattr(self, type_func[node.node_type], None)
        if func:
            return func(node, **kwargs)
        else:
            print("invalid node type")

    def visit_id(self, node, **kwargs):
        pass

    def visit_add(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = left_info.content + ' + ' + right_info.content
        left_info.pre_list += right_info.pre_list
        return left_info

    def visit_sub(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = left_info.content + ' - ' + right_info.content
        left_info.pre_list += right_info.pre_list
        return left_info

    def visit_mul(self, node, **kwargs):
        pass

    def visit_div(self, node, **kwargs):
        pass

    def visit_eq(self, node, **kwargs):
        pass

    def visit_ne(self, node, **kwargs):
        pass

    def visit_lt(self, node, **kwargs):
        pass

    def visit_le(self, node, **kwargs):
        pass

    def visit_gt(self, node, **kwargs):
        pass

    def visit_ge(self, node, **kwargs):
        pass

    def visit_add_sub(self, node, **kwargs):
        pass

    def visit_sub_expr(self, node, **kwargs):
        value_info = self.visit(node.value, **kwargs)
        value_info.content = '(' + value_info.content + ')'
        return value_info

    def visit_cast(self, node, **kwargs):
        pass

    def visit_condition(self, node, **kwargs):
        pass

    def visit_in(self, node, **kwargs):
        pass

    def visit_not_in(self, node, **kwargs):
        pass

    def visit_expression(self, node, **kwargs):
        exp_info = self.visit(node.value, **kwargs)
        if node.sign:
            exp_info.content = '-' + exp_info.content
        return exp_info

    ####################################################
    def visit_matrix(self, node, **kwargs):
        pass

    def visit_vector(self, node, **kwargs):
        pass

    def visit_to_matrix(self, node, **kwargs):
        return self.visit(node.item, **kwargs)

    def visit_sparse_matrix(self, node, **kwargs):
        pass

    def visit_summation(self, node, **kwargs):
        pass

    def visit_determinant(self, node, **kwargs):
        pass

    def visit_transpose(self, node, **kwargs):
        pass

    def visit_squareroot(self, node, **kwargs):
        pass

    def visit_power(self, node, **kwargs):
        pass

    def visit_solver(self, node, **kwargs):
        pass

    def visit_sparse_if(self, node, **kwargs):
        pass

    def visit_sparse_ifs(self, node, **kwargs):
        pass

    def visit_function(self, node, **kwargs):
        name_info = self.visit(node.name, **kwargs)
        pre_list = []
        params = []
        if node.params:
            for param in node.params:
                param_info = self.visit(param, **kwargs)
                params.append(param_info.content)
                pre_list += param_info.pre_list
        content = "{}({})".format(name_info.content, ', '.join(params))
        return CodeNodeInfo(content, pre_list)

    def visit_sparse_other(self, node, **kwargs):
        pass

    def visit_matrix_rows(self, node, **kwargs):
        ret = []
        pre_list = []
        if node.rs:
            rs_info = self.visit(node.rs, **kwargs)
            ret = ret + rs_info.content
            pre_list += rs_info.pre_list
        if node.r:
            r_info = self.visit(node.r, **kwargs)
            ret.append(r_info.content)
            pre_list += r_info.pre_list
        return CodeNodeInfo(ret, pre_list)

    def visit_matrix_row(self, node, **kwargs):
        ret = []
        pre_list = []
        if node.rc:
            rc_info = self.visit(node.rc, **kwargs)
            ret += rc_info.content
            pre_list += rc_info.pre_list
        if node.exp:
            exp_info = self.visit(node.exp, **kwargs)
            ret.append(exp_info.content)
            pre_list += exp_info.pre_list
        return CodeNodeInfo(ret, pre_list)

    def visit_matrix_row_commas(self, node, **kwargs):
        ret = []
        pre_list = []
        if node.value:
            value_info = self.visit(node.value, **kwargs)
            ret += value_info.content
            pre_list += value_info.pre_list
        if node.exp:
            exp_info = self.visit(node.exp, **kwargs)
            ret.append(exp_info.content)
            pre_list += exp_info.pre_list
        return CodeNodeInfo(ret, pre_list)

    def visit_exp_in_matrix(self, node, **kwargs):
        exp_info = self.visit(node.value, **kwargs)
        if node.sign:
            exp_info.content = '-' + exp_info.content
        return exp_info

    def visit_num_matrix(self, node, **kwargs):
        pass

    def visit_matrix_index(self, node, **kwargs):
        pass

    def visit_vector_index(self, node, **kwargs):
        pass

    def visit_sequence_index(self, node, **kwargs):
        pass

    def visit_derivative(self, node, **kwargs):
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
        elif node.nm:
            return self.visit(node.nm, **kwargs)
        elif node.op:
            return self.visit(node.op, **kwargs)
        elif node.c:
            return self.visit(node.c, **kwargs)

    def visit_double(self, node, **kwargs):
        content = str(node.value)
        return CodeNodeInfo(content)

    def visit_integer(self, node, **kwargs):
        content = str(node.value)
        return CodeNodeInfo(content)

    ####################################################
    def visit_start(self, node, **kwargs):
        return self.visit(node.stat, **kwargs)

    def visit_block(self, node, **kwargs):
        pass

    def visit_assignment(self, node, **kwargs):
        pass

    def visit_if(self, node, **kwargs):
        pass

    ####################################################
    def visit_import(self, node, **kwargs):
        pass

    ####################################################
    def walk_object(self, o):
        raise Exception('Unexpected type %s walked: %s', type(o).__name__, o)
    ###################################################################

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
        for cur_set in self.same_dim_list:
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

    def convert_unicode(self, name):
        if '`' not in name and self.parse_type != ParserTypeEnum.MATLAB:
            return name
        content = name.replace('`', '')
        new_list = []
        pre_unicode = False
        for e in content:
            if self.parse_type == ParserTypeEnum.NUMPY or self.parse_type == ParserTypeEnum.MATLAB:
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
                if  self.parse_type == ParserTypeEnum.MATLAB and e in self.common_symbol_dict:
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
        ret = re.sub("_+", "_", ''.join(new_list)).rstrip("_")
        return ret

    def trim_content(self, content):
        # convert special string in identifiers
        res = content
        ids_list = list(self.symtable.keys()) + list(self.tmp_symtable.keys())
        for ids in self.ids_dict.keys():
            all_ids = self.get_all_ids(ids)
            ids_list += all_ids[1]
        names_dict = []
        # This is conducting the replacements at the output string level rather
        # than the variable name level. If one name appears in another (e.g., φ
        # in `x(φ)` then this leads to clashes, hence the awkward sort.
        ids_list.sort(key=len,reverse=True)
        for special in ids_list:
            if '`' not in special and self.parse_type != ParserTypeEnum.MATLAB:
                continue
            # don't convert numbers...
            if special.isnumeric():
                continue
            new_str = self.convert_unicode(special)
            new_str = new_str.replace('-', '_')
            if new_str != special:
                while new_str in names_dict or new_str in self.symtable.keys() or self.is_keyword(new_str):
                    new_str = '_' + new_str
                names_dict.append(new_str)
                res = res.replace(special, new_str)
        return res

    def filter_symbol(self, symbol):
        if '`' in symbol:
            new_symbol = symbol.replace('`', '')
            if not self.pattern.fullmatch(new_symbol) or is_keyword(new_symbol):
                new_symbol = symbol
        else:
            new_symbol = symbol
        return new_symbol

    def contain_subscript(self, identifier):
        if identifier in self.ids_dict:
            return self.ids_dict[identifier].contain_subscript()
        return False

    def get_all_ids(self, identifier):
        if identifier in self.ids_dict:
            return self.ids_dict[identifier].get_all_ids()
        res = identifier.split('_')
        subs = []
        for index in range(len(res[1])):
            subs.append(res[1][index])
        return [res[0], subs]

    def get_result_type(self):
        return self.func_name + "ResultType"

    def get_main_id(self, identifier):
        if identifier in self.ids_dict:
            return self.ids_dict[identifier].get_main_id()
        if self.contain_subscript(identifier):
            ret = self.get_all_ids(identifier)
            return ret[0]
        return identifier
