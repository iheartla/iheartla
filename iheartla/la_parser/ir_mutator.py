from .ir_visitor import *

class MutatorVisitType(IntEnum):
    MutatorVisitInvalid = -1
    MutatorVisitFirst = 0
    MutatorVisitSecond = 1


class IRMutator(IRVisitor):
    def __init__(self, parse_type=None):
        super().__init__(parse_type=parse_type)
        self.visiting_solver = False
        self.unknown_sym = None
        self.substitution_dict = {}
        self.reverse_dict = {}
        self.cur_v_type = MutatorVisitType.MutatorVisitFirst

    def is_first_visit(self):
        return self.visiting_solver and self.cur_v_type == MutatorVisitType.MutatorVisitFirst

    def get_used_var(self, node):
        if node.raw_text not in self.substitution_dict:
            new_var = self.generate_var_name("new")
            self.substitution_dict[new_var] = node.raw_text
            self.reverse_dict[node.raw_text] = new_var
        else:
            new_var = self.reverse_dict[node.raw_text]
        return new_var

    def visit_code(self, node, **kwargs):
        return self.visit(node, **kwargs)

    def visit_start(self, node, **kwargs):
        self.visit(node.stat, **kwargs)
        return node

    def visit_block(self, node, **kwargs):
        for index in range(len(node.stmts)):
            if node.stmts[index].is_node(IRNodeType.Equation):
                node.stmts[index] = self.visit(node.stmts[index], **kwargs)
        return node

    def visit_equation(self, node, **kwargs):
        self.visiting_solver = True
        self.unknown_sym = node.unknown_id.get_main_id()
        lhs = self.visit(node.left, **kwargs)
        rhs = self.visit(node.right, **kwargs)
        print("current equation: {} = {}".format(lhs, rhs))
        self.cur_v_type = MutatorVisitType.MutatorVisitSecond
        return node

    def visit_expression(self, node, **kwargs):
        if self.is_first_visit():
            if not node.contain_sym(self.unknown_sym):
                return self.get_used_var(node)
            return self.visit(node.value, **kwargs)
        return node

    def visit_factor(self, node, **kwargs):
        if self.is_first_visit():
            if not node.contain_sym(self.unknown_sym):
                return self.get_used_var(node)
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

    def visit_add(self, node, **kwargs):
        if self.is_first_visit():
            if not node.contain_sym(self.unknown_sym):
                return self.get_used_var(node)
            left = self.visit(node.left, **kwargs)
            right = self.visit(node.right, **kwargs)
            return left + ' + ' + right
        return ''

    def visit_sub(self, node, **kwargs):
        if self.is_first_visit():
            if not node.contain_sym(self.unknown_sym):
                return self.get_used_var(node)
            left = self.visit(node.left, **kwargs)
            right = self.visit(node.right, **kwargs)
            return left + ' - ' + right
        return ''

    def visit_mul(self, node, **kwargs):
        if self.is_first_visit():
            if not node.contain_sym(self.unknown_sym):
                return self.get_used_var(node)
            left = self.visit(node.left, **kwargs)
            right = self.visit(node.right, **kwargs)
            return left + ' * ' + right
        return ''

    def visit_div(self, node, **kwargs):
        if self.is_first_visit():
            if not node.contain_sym(self.unknown_sym):
                return self.get_used_var(node)
            left = self.visit(node.left, **kwargs)
            right = self.visit(node.right, **kwargs)
            return left + ' / ' + right
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
        return content

    def visit_IdentifierAlone(self, node, **kwargs):
        if node.value:
            value = node.value
        else:
            value = '`' + node.id + '`'
        return value