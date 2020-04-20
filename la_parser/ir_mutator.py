from la_parser.ir_visitor import *


class IRMutator(IRVisitor):
    def __init__(self):
        super().__init__()