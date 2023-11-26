from .de_ir_visitor import *


class DIRPrinter(DIRVisitor):
    def __init__(self, parse_type=None):
        super().__init__(parse_type=parse_type)