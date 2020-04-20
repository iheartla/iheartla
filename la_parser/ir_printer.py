from la_parser.ir_visitor import *


class IRPrinter(IRVisitor):
    def __init__(self):
        super().__init__()