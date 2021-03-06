from .ir_visitor import *


class IRPrinter(IRVisitor):
    def __init__(self, parse_type=None):
        super().__init__(parse_type=parse_type)