from la_parser.ir import *


class IRVisitor(object):
    def __init__(self):
        super().__init__()
        self.pre_str = ''
        self.post_str = ''
        self.symtable = {}
        self.def_dict = {}
        self.parameters = set()
        self.subscripts = {}
        self.node_dict = {}
        self.dim_dict = {}
        self.sub_name_dict = {}
        self.ids_dict = {}  # identifiers with subscripts
        self.ret_symbol = None
        self.stat_list = None
        self.content = ''

    def visit_code(self, node, **kwargs):
        self.content = ''
        self.content = self.pre_str + self.visit(node) + self.post_str

    def visit(self, node, **kwargs):
        type_func = {
            # base
            IRNodeType.Id: "visit_id",
            IRNodeType.Number: "visit_number",
            IRNodeType.Integer: "visit_integer",
            IRNodeType.Factor: "visit_factor",
            IRNodeType.Expression: "visit_expression",
            IRNodeType.Subexpression: "visit_sub_expr",
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
            IRNodeType.walk_AddSub: "visit_add_sub",
            IRNodeType.Summation: "visit_summation",
            IRNodeType.Determinant: "visit_determinant",
            IRNodeType.Transpose: "visit_transpose",
            IRNodeType.Power: "visit_power",
            IRNodeType.Solver: "visit_solver",
            IRNodeType.Derivative: "visit_derivative",
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

    def visit_number(self, node, **kwargs):
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

    def trim_content(self, content):
        # convert special string in identifiers
        res = content
        ids_list = list(self.symtable.keys())
        for ids in self.ids_dict.keys():
            all_ids = self.get_all_ids(ids)
            ids_list += all_ids[1]
        names_dict = []
        for special in ids_list:
            if '`' not in special:
                continue
            new_str = ''.join(e for e in special if e.isalnum() or e is '_')
            if new_str is '' or new_str[0].isnumeric():
                new_str = '_' + new_str
            if new_str is not special:
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