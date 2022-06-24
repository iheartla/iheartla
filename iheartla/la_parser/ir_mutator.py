from .ir_visitor import *


class IRMutator(IRVisitor):
    def __init__(self, parse_type=None):
        super().__init__(parse_type=parse_type)

    def visit_code(self, node, **kwargs):
        return node