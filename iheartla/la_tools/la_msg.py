from enum import Enum
from tatsu.util import re
from .la_helper import is_new_tatsu_version


class LaMsgTypeEnum(Enum):
    DEFAULT = 0
    PARSE_ERROR = 1
    TYPE_ERROR = 2


class LaMsg(object):
    __instance = None
    @staticmethod
    def getInstance():
        if LaMsg.__instance is None:
            LaMsg()
        return LaMsg.__instance

    def __init__(self):
        if LaMsg.__instance is not None:
            raise Exception("Class LaMsg is a singleton!")
        else:
            self.rule_convention_dict = {
                # base.ebnf
                "identifier_with_subscript": "identifier with subscript",
                "identifier_alone": "identifier",
                "pi": "pi",
                # LA.ebnf
                "statements": "statement",
                "import": "import",
                "where_conditions": "where conditions",
                "where_condition": "where condition",
                "matrix_type": "matrix type",
                "vector_type": "vector type",
                "scalar_type": "scalar type",
                "set_type": "set type",
                "function_type": "function type",
                "expression": "expression",
                "if_condition": "if condition",
                "in": "in condition",
                "not_in": "not in condition",
                "not_equal": "not equal condition",
                "equal": "equal condition",
                "greater": "greater condition",
                "greater_equal": "greater or equal condition",
                "less": "less condition",
                "less_equal": "less or equal condition",
                # matrix.ebnf
                "matrix": "matrix",
                "sparse_matrix": "sparse matrix",
                "sparse_if_conditions": "if conditions for sparse matrix",
                "sparse_if_condition": "if condition for sparse matrix",
                "rows": "rows for matrix",
                "row": "row for matrix",
                "row_with_commas": "row for matrix",
                "expr_in_matrix": "expression in matrix",
                "addition_in_matrix": "addition in matrix",
                "subtraction_in_matrix": "subtraction in matrix",
                "multiplication_in_matrix": "multiplication in matrix",
                "division_in_matrix": "division in matrix",
                "frobenius_product_in_matrix_operator": "frobenius product",
                "hadamard_product_in_matrix_operator": "hadamard product",
                "cross_product_in_matrix_operator": "cross product",
                "kronecker_product_in_matrix_operator": "kronecker product",
                "trans_in_matrix_operator": "transpose",
                "pseudoinverse_in_matrix_operator": "pseudoinverse",
                "sqrt_in_matrix_operator": "squareroot",
                "sum_in_matrix_operator": "sum",
                "power_in_matrix_operator": "power",
                "solver_in_matrix_operator": "solver",
                "number_matrix": "number matrix",
                # operators.ebnf
                "addition": "addition",
                "subtraction": "subtraction",
                "add_sub_operator": "add_sub_operator",
                "multiplication": "multiplication",
                "division": "division",
                "derivative_operator": "derivative",
                "power_operator": "power",
                "solver_operator": "solver",
                "sum_operator": "sum",
                "optimize_operator": "optimize",
                "multi_cond": "multi",
                "domain": "domain",
                "norm_operator": "norm",
                "inner_product_operator": "inner product",
                "frobenius_product_operator": "frobenius product",
                "hadamard_product_operator": "hadamard product",
                "cross_product_operator": "cross product",
                "kronecker_product_operator": "kronecker product",
                "trans_operator": "transpose",
                "sqrt_operator": "squareroot operator",
                "function_operator": "function",
                "exp_func": "exponential",
                "log_func": "log",
                "ln_func": "ln",
                "sqrt_func": "sqrt",
                # number.ebnf
                "integer": "integer",
                "exponent": "exponent",
                "mantissa": "mantissa",
                "floating_point": "floating point",
                "double": "double",
                # trigonometry.ebnf
                "sin_func": "sin function",
                "asin_func": "asin function",
                "cos_func": "cos function",
                "acos_func": "acos function",
                "tan_func": "tan function",
                "atan_func": "atan function",
                "sinh_func": "sinh function",
                "asinh_func": "asinh function",
                "cosh_func": "cosh function",
                "acosh_func": "acosh function",
                "tanh_func": "tanh function",
                "atanh_func": "atanh function",
                "cot_func": "cot function",
                "sec_func": "sec function",
                "csc_func": "csc function",
                "atan2_func": "atan2 function",
                # linear algebra function
                "trace_func": "trace function",
                "tr_func": "trace function",
                "diag_func": "diagonal function",
                "vec_func": "vectorization function",
                "det_func": "determinant function",
                "rank_func": "rank function",
                "null_func": "null space function",
                "orth_func": "orthogonal space function",
                "inv_func": "inverse function",
            }
            self.cur_name = ''
            self.cur_line = 0
            self.cur_col = 0
            self.cur_msg = ''
            self.cur_code = ''
            LaMsg.__instance = self

    def get_line_desc(self, line_info):
        self.cur_line = line_info.line
        self.cur_col = line_info.col
        return "Error on line {} at column {}".format(line_info.line + 1, line_info.col + 1)

    def get_line_desc_with_col(self, line, col):
        self.cur_line = line
        self.cur_col = col
        return "Error on line {} at column {}".format(line + 1, col + 1)

    def get_pos_marker(self, column):
        return ''.join([' '] * column) + '^\n'

    def get_parse_error(self, err):
        if is_new_tatsu_version():
            line_info = err.tokenizer.line_info(err.pos)
        else:
            line_info = err.buf.line_info(err.pos)
        converted_name = None
        for rule in reversed(err.stack):
            if rule in self.rule_convention_dict:
                converted_name = self.rule_convention_dict[rule]
                break
        self.cur_msg = "Failed to parse {}".format(converted_name)
        content = "{}. {}: {}\n".format(self.get_line_desc(line_info), self.cur_msg, err.message)
        content += line_info.text
        self.cur_code = line_info.text
        content += self.get_pos_marker(line_info.col)
        # from TatSu/tatsu/exceptions.py 
        # info = err.tokenizer.line_info(err.pos)
        # template = "{}({}:{}) {} :\n{}\n{}^"
        # text = info.text.rstrip()
        # leading = re.sub(r'[^\t]', ' ', text)[:info.col]
        # text = text.expandtabs()
        # leading = leading.expandtabs()
        # content = template.format(info.filename,
        #                        info.line + 1, info.col + 1,
        #                        err.message.rstrip(),
        #                        text,
        #                        leading)
        return content


def get_err_msg_info(parse_info, error_msg):
    if parse_info:
        line_info = get_line_info(parse_info)
        return get_err_msg(line_info, line_info.col, error_msg)
    else:
        return error_msg


def get_err_msg(line_info, col, error_msg):
    line_msg = LaMsg.getInstance().get_line_desc_with_col(line_info.line, col)
    raw_text = line_info.text
    if raw_text[-1] != '\n':
        raw_text += '\n'
    LaMsg.getInstance().cur_msg = error_msg
    LaMsg.getInstance().cur_code = line_info.text
    return "{}. {}.\n{}{}".format(line_msg, error_msg, raw_text, LaMsg.getInstance().get_pos_marker(col))


def get_line_info(parse_info):
    return get_parse_info_buffer(parse_info).line_info(parse_info.pos)


def get_parse_info_buffer(parse_info):
    if is_new_tatsu_version():
        return parse_info.tokenizer
    return parse_info.buffer


def set_source_name(name):
    LaMsg.getInstance().cur_name = name