from la_parser.ir_printer import *


class CodeGen(IRPrinter):
    def __init__(self, parse_type=None):
        super().__init__(parse_type=parse_type)