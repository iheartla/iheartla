from .ir_visitor import *


class IRIterator(IRVisitor):
    """
    Visit expressions to gather useful info
    """
    def __init__(self):
        super().__init__()

    def visit_id(self, node, **kwargs):
        pass

    def visit_add(self, node, **kwargs):
        self.visit(node.left, **kwargs)
        self.visit(node.right, **kwargs)

    def visit_sub(self, node, **kwargs):
        self.visit(node.left, **kwargs)
        self.visit(node.right, **kwargs)

    def visit_mul(self, node, **kwargs):
        self.visit(node.left, **kwargs)
        self.visit(node.right, **kwargs)

    def visit_div(self, node, **kwargs):
        self.visit(node.left, **kwargs)
        self.visit(node.right, **kwargs)

    def visit_add_sub(self, node, **kwargs):
        self.visit(node.left, **kwargs)
        self.visit(node.right, **kwargs)

    def visit_sub_expr(self, node, **kwargs):
        self.visit(node.value, **kwargs)

    def visit_cast(self, node, **kwargs):
        if node.value:
            self.visit(node.value, **kwargs)

    def visit_condition(self, node, **kwargs):
        for condition in node.cond_list:
            self.visit(condition, **kwargs)

    def visit_in(self, node, **kwargs):
        self.visit(node.set, **kwargs)

    def visit_not_in(self, node, **kwargs):
        pass

    def visit_expression(self, node, **kwargs):
        self.visit(node.value, **kwargs)

    ####################################################
    def visit_matrix(self, node, **kwargs):
        pass

    def visit_vector(self, node, **kwargs):
        pass

    def visit_to_matrix(self, node, **kwargs):
        pass

    def visit_sparse_matrix(self, node, **kwargs):
        pass

    def visit_summation(self, node, **kwargs):
        if node.cond:
            self.visit(node.cond, **kwargs)
        self.visit(node.exp)

    def visit_determinant(self, node, **kwargs):
        pass

    def visit_transpose(self, node, **kwargs):
        self.visit(node.f, **kwargs)

    def visit_squareroot(self, node, **kwargs):
        self.visit(node.value, **kwargs)

    def visit_power(self, node, **kwargs):
        self.visit(node.base, **kwargs)
        if node.t:
            pass
        elif node.r:
            pass
        else:
            self.visit(node.power, **kwargs)

    def visit_divergence(self, node, **kwargs):
        pass

    def visit_gradient(self, node, **kwargs):
        pass

    def visit_laplace(self, node, **kwargs):
        pass

    def visit_solver(self, node, **kwargs):
        self.visit(node.left, **kwargs)
        self.visit(node.right, **kwargs)

    def visit_sparse_if(self, node, **kwargs):
        pass

    def visit_sparse_ifs(self, node, **kwargs):
        pass

    def visit_function(self, node, **kwargs):
        self.visit(node.name, **kwargs)
        if node.params:
            for param in node.params:
                self.visit(param, **kwargs)

    def visit_local_func(self, node, **kwargs):
        self.visit(node.name, **kwargs)
        for parameter in node.params:
            self.visit(parameter, **kwargs)

    def visit_sparse_other(self, node, **kwargs):
        pass

    def visit_matrix_rows(self, node, **kwargs):
        if node.rs:
            self.visit(node.rs, **kwargs)
        if node.r:
            self.visit(node.r, **kwargs)

    def visit_matrix_row(self, node, **kwargs):
        if node.rc:
            self.visit(node.rc, **kwargs)
        if node.exp:
            self.visit(node.exp, **kwargs)

    def visit_matrix_row_commas(self, node, **kwargs):
        if node.value:
            self.visit(node.value, **kwargs)
        if node.exp:
            self.visit(node.exp, **kwargs)

    def visit_exp_in_matrix(self, node, **kwargs):
        self.visit(node.value, **kwargs)

    def visit_num_matrix(self, node, **kwargs):
        self.visit(node.id1, **kwargs)
        if node.id2:
            self.visit(node.id2, **kwargs)

    def visit_matrix_index(self, node, **kwargs):
        self.visit(node.main, **kwargs)
        if node.row_index is not None:
            self.visit(node.row_index, **kwargs)
        else:
            self.visit(node.col_index, **kwargs)

    def visit_vector_index(self, node, **kwargs):
        self.visit(node.main, **kwargs)
        self.visit(node.row_index, **kwargs)

    def visit_sequence_index(self, node, **kwargs):
        self.visit(node.main, **kwargs)
        self.visit(node.main_index, **kwargs)

    def visit_seq_dim_index(self, node, **kwargs):
        self.visit(node.main_index, **kwargs)

    def visit_derivative(self, node, **kwargs):
        pass

    def visit_partial(self, node, **kwargs):
        pass

    def visit_factor(self, node, **kwargs):
        if node.id:
            self.visit(node.id, **kwargs)
        elif node.num:
            self.visit(node.num, **kwargs)
        elif node.sub:
            self.visit(node.sub, **kwargs)
        elif node.m:
            self.visit(node.m, **kwargs)
        elif node.v:
            self.visit(node.v, **kwargs)
        elif node.nm:
            self.visit(node.nm, **kwargs)
        elif node.op:
            self.visit(node.op, **kwargs)
        elif node.c:
            self.visit(node.c, **kwargs)

    def visit_double(self, node, **kwargs):
        pass

    def visit_fraction(self, node, **kwargs):
        pass

    def visit_integer(self, node, **kwargs):
        pass

    def visit_inner_product(self, node, **kwargs):
        self.visit(node.left, **kwargs)
        self.visit(node.right, **kwargs)

    def visit_fro_product(self, node, **kwargs):
        self.visit(node.left, **kwargs)
        self.visit(node.right, **kwargs)

    def visit_hadamard_product(self, node, **kwargs):
        self.visit(node.left, **kwargs)
        self.visit(node.right, **kwargs)

    def visit_cross_product(self, node, **kwargs):
        self.visit(node.left, **kwargs)
        self.visit(node.right, **kwargs)

    def visit_kronecker_product(self, node, **kwargs):
        self.visit(node.left, **kwargs)
        self.visit(node.right, **kwargs)

    def visit_dot_product(self, node, **kwargs):
        self.visit(node.left, **kwargs)
        self.visit(node.right, **kwargs)

    def visit_math_func(self, node, **kwargs):
        self.visit(node.param, **kwargs)

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
        self.visit(node.cond)

    ####################################################
    def visit_import(self, node, **kwargs):
        pass

    ####################################################
    def walk_object(self, o):
        raise Exception('Unexpected type %s walked: %s', type(o).__name__, o)
    ###################################################################


