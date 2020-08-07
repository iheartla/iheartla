from la_parser.ir import *
from la_tools.la_logger import *
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
        self.ids_dict = {}  # identifiers with subscripts
        self.ret_symbol = None
        self.content = ''
        self.parse_type = parse_type
        self.logger = LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT)
        self.name_convention_dict = {}  # eg:i -> i[0]
        self.func_name = 'myExpression'

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
            ret = "_{}_{}".format(base, index)
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
        if func_name is not None:
            self.func_name = func_name
        # self.print_symbols()

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
            # control
            IRNodeType.Start: "visit_start",
            IRNodeType.Block: "visit_block",
            IRNodeType.Assignment: "visit_assignment",
            IRNodeType.If: "visit_if",
            IRNodeType.Function: "visit_function",
            # if condition
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
            # where block
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
        pass

    def visit_sub(self, node, **kwargs):
        pass

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
        pass

    def visit_in(self, node, **kwargs):
        pass

    def visit_not_in(self, node, **kwargs):
        pass

    def visit_expression(self, node, **kwargs):
        pass

    ####################################################
    def visit_matrix(self, node, **kwargs):
        pass

    def visit_sparse_matrix(self, node, **kwargs):
        pass

    def visit_summation(self, node, **kwargs):
        pass

    def visit_determinant(self, node, **kwargs):
        pass

    def visit_transpose(self, node, **kwargs):
        pass

    def visit_power(self, node, **kwargs):
        pass

    def visit_solver(self, node, **kwargs):
        pass

    def visit_sparse_if(self, node, **kwargs):
        pass

    def visit_sparse_ifs(self, node, **kwargs):
        pass

    def visit_sparse_other(self, node, **kwargs):
        pass

    def visit_exp_in_matrix(self, node, **kwargs):
        pass

    def visit_num_matrix(self, node, **kwargs):
        pass

    def visit_derivative(self, node, **kwargs):
        pass

    def visit_factor(self, node, **kwargs):
        pass

    def visit_double(self, node, **kwargs):
        pass

    def visit_integer(self, node, **kwargs):
        pass

    ####################################################
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
        return False

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

    def convert_unicode(self, name):
        if '`' not in name:
            return name
        content = name.replace('`', '')
        new_list = []
        pre_unicode = False
        for e in content:
            if e.isalnum() or e == '_':
                if pre_unicode:
                    new_list.append('_')
                    pre_unicode = False
                new_list.append(e)
            elif e.isspace():
                new_list.append('_')
            else:
                try:
                    if not pre_unicode:
                        new_list.append('_')
                    new_list.append(unicodedata.name(e).lower().replace(' ', '_'))
                    pre_unicode = True
                except KeyError:
                    continue
        return ''.join(new_list)

    def trim_content(self, content):
        # convert special string in identifiers
        res = content
        ids_list = list(self.symtable.keys()) + list(self.tmp_symtable.keys())
        for ids in self.ids_dict.keys():
            all_ids = self.get_all_ids(ids)
            ids_list += all_ids[1]
        names_dict = []
        for special in ids_list:
            if '`' not in special:
                continue
            new_str = self.convert_unicode(special)
            new_str = new_str.replace('-', '_')
            if new_str != special:
                while new_str in names_dict or new_str in self.symtable.keys() or self.is_keyword(new_str):
                    new_str = '_' + new_str
                names_dict.append(new_str)
                res = res.replace(special, new_str)
        return res

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

    def get_main_id(self, identifier):
        if identifier in self.ids_dict:
            return self.ids_dict[identifier].get_main_id()
        if self.contain_subscript(identifier):
            ret = self.get_all_ids(identifier)
            return ret[0]
        return identifier