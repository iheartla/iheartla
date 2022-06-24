from .ir_visitor import *


class IRMutator(IRVisitor):
    def __init__(self, parse_type=None):
        super().__init__(parse_type=parse_type)

    def visit_code(self, node, **kwargs):
        return self.visit(node, **kwargs)

    def visit_start(self, node, **kwargs):
        self.visit(node.stat, **kwargs)
        return node

    def visit_block(self, node, **kwargs):
        for index in range(len(node.stmts)):
            if node.stmts[index].is_node(IRNodeType.Equation):
                self.visit(node.stmts[index], **kwargs)
        return node

    def visit_equation(self, node, **kwargs):
        lhs = self.visit(node.left)
        rhs = self.visit(node.right)
        return node