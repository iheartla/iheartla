from .de_ir_printer import *
import copy


class DCodeGen(DIRPrinter):
    def __init__(self, parse_type=None):
        super().__init__(parse_type=parse_type)

    def init_type(self, type_walker):
        super().init_type(type_walker)

    def visit_start(self, node, **kwargs):
        content = ''
        for vblock in node.vblock:
            content += self.visit(vblock, **kwargs).content + '\n'
        # self.visit(node.stat, **kwargs)
        return CodeNodeInfo(content)

    def visit_block(self, node, **kwargs):
        ret = []
        pre_list = []
        for stmt in node.stmts:
            stmt_info = self.visit(stmt, **kwargs)
            ret.append(stmt_info.content)
            pre_list += stmt_info.pre_list
        return CodeNodeInfo('\n'.join(ret), pre_list)

    def visit_params_block(self, node, **kwargs):
        content = self.visit(node.conds, **kwargs).content
        if node.annotation:
            content = node.annotation + "\n" + content
        content += "\n"
        return CodeNodeInfo(content)

    def visit_where_conditions(self, node, **kwargs):
        ret = []
        for val in node.value:
            ret.append(self.visit(val, **kwargs).content + " \n")
        return CodeNodeInfo(''.join(ret))

    def visit_where_condition(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_id(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_add(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_sub(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_mul(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_div(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_add_sub(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_sub_expr(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_cast(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_condition(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_in(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_not_in(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_expression(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    ####################################################
    def visit_matrix(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_vector(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_to_matrix(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_to_double(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_element_convert(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_sparse_matrix(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_summation(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_union_sequence(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_determinant(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_transpose(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_squareroot(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_power(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_divergence(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_gradient(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_laplace(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_solver(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_sparse_if(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_sparse_ifs(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_function(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_local_func(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_sparse_other(self, node, **kwargs):
        pass

    def visit_matrix_rows(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_matrix_row(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_matrix_row_commas(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_exp_in_matrix(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_num_matrix(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_matrix_index(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_vector_index(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_sequence_index(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_seq_dim_index(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_derivative(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_partial(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_size(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_factor(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_double(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_fraction(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_integer(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    ###################################################

    def visit_assignment(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_equation(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_if(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    ####################################################
    def visit_import(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)

    def visit_first_order_ode(self, node, **kwargs):
        return CodeNodeInfo(node.raw_text)