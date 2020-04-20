from la_parser.la_types import *


class IRNodeType(Enum):
    # expr
    INVALID = -1
    Id = 0
    Add = 1
    Sub = 2
    Mul = 3
    Div = 4
    Eq = 5
    Ne = 6
    Lt = 7
    Le = 8
    Gt = 9
    Ge = 10
    DenseMatrix = 41
    SparseMatrix = 42
    Summation = 43
    # stmt
    Block = 60
    IfThenElse = 61
    For = 62
    While = 63


class IRNode(object):
    def __init__(self, node_type=None):
        super().__init__()
        self.node_type = node_type


class StmtNode(IRNode):
    def __init__(self, node_type=None):
        super().__init__(node_type)


class BlockNode(StmtNode):
    def __init__(self):
        super().__init__(IRNodeType.Block)
        self.stmts = []

    def add_stmt(self, stmt):
        self.stmts.append(stmt)


class ExprNode(IRNode):
    def __init__(self, node_type=None):
        super().__init__(node_type)
        self.var_type = None


class IdNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Id)
        self.name = None


class AddNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Add)
