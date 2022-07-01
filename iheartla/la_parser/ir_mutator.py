import copy
import sympy
from .ir_visitor import *
from .ir_iterator import *

class MutatorVisitType(IntEnum):
    MutatorVisitInvalid = -1
    MutatorVisitNormal = 0
    MutatorVisitOde = 1
    MutatorVisitPde = 2


def convert_sympy_ast(ast, node_dict):
    if type(ast).__name__ == 'Add':
        cur_nodes = []
        for cur_index in range(len(ast.args)):
            cur_nodes.append(convert_sympy_ast(ast.args[cur_index], node_dict))
        return make_addition(cur_nodes)
    elif type(ast).__name__ == 'Mul':
        cur_nodes = []
        for cur_index in range(len(ast.args)):
            cur_nodes.append(convert_sympy_ast(ast.args[cur_index], node_dict))
        return make_mul(cur_nodes)
    elif type(ast).__name__ == 'Pow':
        return PowerNode(base=convert_sympy_ast(ast.args[0], node_dict), power=convert_sympy_ast(ast.args[1], node_dict))
    elif type(ast).__name__ == 'Rational':
        return DivNode(left=convert_sympy_ast(ast.args[0], node_dict), right=convert_sympy_ast(ast.args[1], node_dict))
    elif type(ast).__name__ == 'Symbol':
        return copy.deepcopy(node_dict[ast])
    elif type(ast).__name__ == 'NegativeOne':
        return IntegerNode(value=-1)
    elif type(ast).__name__ == 'Integer':
        return IntegerNode(value=ast)
    elif type(ast).__name__ == 'One':
        return IntegerNode(value=1)
    print("ast: {}".format(ast))
    return ast


def is_sympy_one(ast):
    return type(ast).__name__ == 'One'


def make_addition(nodes):
    if len(nodes) == 2:
        return AddNode(nodes[0], nodes[1], la_type=nodes[0].la_type)
    else:
        return AddNode(nodes[0], make_addition(nodes[1:]), la_type=nodes[0].la_type)

def make_mul(nodes):
    if len(nodes) == 2:
        return MulNode(nodes[0], nodes[1], la_type=nodes[0].la_type)
    else:
        return MulNode(nodes[0], make_mul(nodes[1:]), la_type=nodes[0].la_type)

class IRMutator(IRIterator):
    def __init__(self):
        super().__init__()
        self.visiting_solver = False
        self.unknown_sym = None
        self.reverse_dict = {}
        self.node_dict = {}
        self.sympy_dict = {}
        self.cur_v_type = MutatorVisitType.MutatorVisitNormal
        self.cur_func_var = ''

    def init_type(self, type_walker, func_name):
        self.reset()
        super(IRMutator, self).init_type(type_walker, func_name)

    def reset(self):
        self.visiting_solver = False
        self.unknown_sym = None
        self.reverse_dict.clear()
        self.node_dict.clear()
        self.sympy_dict.clear()
        self.cur_v_type = MutatorVisitType.MutatorVisitNormal
        self.cur_func_var = ''

    def is_normal_visit(self):
        return self.visiting_solver and self.cur_v_type == MutatorVisitType.MutatorVisitNormal

    def is_ode_visit(self):
        return self.visiting_solver and self.cur_v_type == MutatorVisitType.MutatorVisitOde

    def get_used_var(self, node):
        signature = node.get_signature()
        print("node raw_text: {}, signature:{}, self.reverse_dict:{}, self.sympy_dict:{}".format(node.raw_text, signature, self.reverse_dict, self.sympy_dict))
        if signature not in self.reverse_dict:
            new_var = self.generate_var_name("new")
            self.reverse_dict[signature] = new_var
            self.sympy_dict[new_var] = sympy.Symbol(new_var, commutative=True)
            self.node_dict[self.sympy_dict[new_var]] = node
        else:
            new_var = self.reverse_dict[signature]
        return self.sympy_dict[new_var]

    def get_sympy_var(self, sym, node):
        if sym not in self.sympy_dict:
            self.sympy_dict[sym] = sympy.Symbol(sym, commutative=True)
            self.node_dict[self.sympy_dict[sym]] = node
        return self.sympy_dict[sym]

    def visit_code(self, node, **kwargs):
        return self.visit(node, **kwargs)

    def visit_start(self, node, **kwargs):
        self.visit(node.stat, **kwargs)
        return node

    def visit_block(self, node, **kwargs):
        # gather initial expr
        new_stmts = []
        eq_index_list = []
        init_stmts = []
        for index in range(len(node.stmts)):
            if node.stmts[index].is_node(IRNodeType.Equation):
                if node.stmts[index].is_formal_eq():
                    eq_index_list.append(len(new_stmts))
                    new_stmts.append(node.stmts[index])
                else:
                    init_stmts.append(node.stmts[index])
            else:
                new_stmts.append(node.stmts[index])
        if len(init_stmts) > 0:
            for cur_index in range(len(init_stmts)):
                for eq_index in eq_index_list:
                    if init_stmts[cur_index].contain_sym(new_stmts[eq_index].get_solved_name()):
                        new_stmts[eq_index].add_init(init_stmts[cur_index])
                        break
        node.stmts = new_stmts
        # visit
        for index in range(len(node.stmts)):
            if node.stmts[index].is_node(IRNodeType.Equation):
                node.stmts[index] = self.visit(node.stmts[index], **kwargs)
        return node

    def visit_equation(self, node, **kwargs):
        self.visiting_solver = True
        self.unknown_sym = node.unknown_id.get_main_id()
        if node.eq_type == EqTypeEnum.DEFAULT:
            # pattern: A x = b
            x = sympy.Symbol(node.unknown_id.get_main_id(), commutative=True)
            self.sympy_dict[node.unknown_id.get_main_id()] = x
            lhs = self.visit(node.left, **kwargs)
            rhs = self.visit(node.right, **kwargs)
            print("current equation: {} = {}".format(lhs, rhs))
            A = Wild(self.generate_var_name("A"), exclude=[x])
            b = Wild(self.generate_var_name("b"), exclude=[x])
            res = (lhs-(rhs)).match(A*x - b)
            print("res: {}".format(res))
            if res and len(res) > 0:
                lnode = convert_sympy_ast(res[A], self.node_dict)
                rnode = convert_sympy_ast(res[b], self.node_dict)
                assign_node = AssignNode([copy.deepcopy(node.unknown_id)], [], parse_info=node.parse_info, raw_text=node.raw_text)
                if self.symtable[node.unknown_id.get_main_id()].is_scalar():
                    div_node = DivNode(rnode, lnode, la_type=ScalarType(), parse_info=node.parse_info, raw_text=node.raw_text)
                    assign_node.right.append(SubexpressionNode(value=div_node, la_type=div_node.la_type, parse_info=node.parse_info, raw_text=node.raw_text))
                else:
                    solver_node = SolverNode(la_type=self.symtable[node.unknown_id.get_main_id()], parse_info=node.parse_info, raw_text=node.raw_text)
                    solver_node.left = lnode
                    solver_node.right = rnode
                    assign_node.right.append(SubexpressionNode(value=solver_node, la_type=solver_node.la_type, parse_info=node.parse_info, raw_text=node.raw_text))
                return assign_node
        elif node.eq_type & EqTypeEnum.ODE:
            self.cur_v_type = MutatorVisitType.MutatorVisitOde
            print("ode")
            lhs = self.visit(node.left, **kwargs)
            rhs = self.visit(node.right, **kwargs)
            print("current equation: {} = {}, solved: {}".format(lhs, rhs, self.cur_func_var))
            A = Wild(self.generate_var_name("A"), exclude=[self.cur_func_var])
            b = Wild(self.generate_var_name("b"), exclude=[self.cur_func_var])
            res = (lhs - (rhs)).match(A * self.cur_func_var - b)
            print("res: {}".format(res))
            if res and len(res) > 0:
                lnode = convert_sympy_ast(res[A], self.node_dict)
                rnode = convert_sympy_ast(res[b], self.node_dict)
                if is_sympy_one(res[A]):
                    fraction = rnode
                else:
                    fraction = DivNode(rnode, lnode)
                ode_node = OdeFirstOrderNode(func=self.unknown_sym, expr=fraction, la_type=self.symtable[node.unknown_id.get_main_id()],
                                                parse_info=node.parse_info, raw_text=node.raw_text)
                ode_node.init_list = node.init_list
                ode_node.param = node.params_dict[0][0]
                return ode_node
        elif node.eq_type & EqTypeEnum.PDE:
            print("pde")
        self.visiting_solver = False
        return node

    def visit_expression(self, node, **kwargs):
        if self.is_normal_visit():
            if not node.contain_sym(self.unknown_sym):
                return self.get_used_var(node)
            return self.visit(node.value, **kwargs)
        elif self.is_ode_visit():
            return self.visit(node.value, **kwargs)
        return node

    def visit_factor(self, node, **kwargs):
        if self.is_normal_visit():
            if not node.contain_sym(self.unknown_sym):
                return self.get_used_var(node)
        # elif self.is_ode_visit():
            # if not node.contain_sym(self.unknown_sym):
            #     return self.get_used_var(node)
            # return self.visit(node.value, **kwargs)
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

    def visit_function(self, node, **kwargs):
        if self.is_normal_visit():
            pass
        elif self.is_ode_visit():
            return self.get_used_var(node)

    def visit_add(self, node, **kwargs):
        if self.is_normal_visit():
            if not node.contain_sym(self.unknown_sym):
                return self.get_used_var(node)
        left = self.visit(node.left, **kwargs)
        right = self.visit(node.right, **kwargs)
        return left + right

    def visit_sub(self, node, **kwargs):
        if self.is_normal_visit():
            if not node.contain_sym(self.unknown_sym):
                return self.get_used_var(node)
        left = self.visit(node.left, **kwargs)
        right = self.visit(node.right, **kwargs)
        return left - right

    def visit_mul(self, node, **kwargs):
        if self.is_normal_visit():
            if not node.contain_sym(self.unknown_sym):
                return self.get_used_var(node)
        left = self.visit(node.left, **kwargs)
        right = self.visit(node.right, **kwargs)
        return left * right

    def visit_div(self, node, **kwargs):
        if self.is_normal_visit():
            if not node.contain_sym(self.unknown_sym):
                return self.get_used_var(node)
        left = self.visit(node.left, **kwargs)
        right = self.visit(node.right, **kwargs)
        return left / right

    def visit_derivative(self, node, **kwargs):
        if self.is_ode_visit():
            name = self.get_used_var(node)
            self.cur_func_var = name
            return name
        return ''

    def visit_id(self, node, **kwargs):
        content = node.get_name()
        content = self.filter_symbol(content)
        if content in self.name_convention_dict:
            content = self.name_convention_dict[content]
        if self.convert_matrix and node.contain_subscript():
            if len(node.subs) == 2:
                if self.get_sym_type(node.main_id).is_matrix():
                    if self.get_sym_type(node.main_id).sparse:
                        content = "{}.coeff({}, {})".format(node.main_id, node.subs[0], node.subs[1])
                    else:
                        content = "{}({}, {})".format(node.main_id, node.subs[0], node.subs[1])
        return self.get_sympy_var(content, node)

    def visit_IdentifierAlone(self, node, **kwargs):
        if node.value:
            value = node.value
        else:
            value = '`' + node.id + '`'
        return self.get_sympy_var(value, node)

    def visit_integer(self, node, **kwargs):
        return sympy.Integer(node.value)