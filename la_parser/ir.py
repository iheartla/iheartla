from la_parser.la_types import *
import weakref


class IRNodeType(Enum):
    # expr
    INVALID = -1
    Start = 1000
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
    walk_AddSub = 11
    Subexpression = 12
    In = 13
    NotIn = 14
    Expression = 15
    BinComp = 16

    Matrix = 41
    MatrixRows = 141
    MatrixRow = 142
    MatrixRowCommas = 143
    SparseMatrix = 42
    Summation = 43
    Determinant = 44
    Transpose = 45
    Power = 46
    Solver = 47
    SparseIf = 48
    SparseOther = 49
    ExpInMatrix = 50
    NumMatrix = 51
    Derivative = 52
    Factor = 53
    Number = 54
    Integer = 55
    SparseIfs = 148


    # stmt
    Block = 200
    Assignment = 201
    IfThenElse = 202
    For = 203
    While = 204
    If = 205
    Function = 210
    WhereConditions = 211
    WhereCondition = 2111

    MatrixType = 216
    VectorType = 217
    SetType = 218
    ScalarType = 219
    FunctionType = 220


class IRNode(object):
    def __init__(self, node_type=None, parent=None):
        super().__init__()
        self.node_type = node_type
        self.la_type = None
        self.parent = None
        self.set_parent(parent)

    def set_parent(self, parent):
        if parent:
            # self.parent = weakref.ref(parent)
            self.parent = parent

    def get_ancestor(self, node_type):
        parent = self.parent
        while parent is not None:
            if parent.node_type == node_type:
                return parent
            else:
                parent = parent.parent
        return None



class StmtNode(IRNode):
    def __init__(self, node_type=None):
        super().__init__(node_type)


class ExprNode(IRNode):
    def __init__(self, node_type=None):
        super().__init__(node_type)


class StartNode(StmtNode):
    def __init__(self):
        super().__init__(IRNodeType.Start)
        self.cond = None
        self.stat = None


class WhereConditionsNode(StmtNode):
    def __init__(self):
        super().__init__(IRNodeType.WhereConditions)
        self.value = []


class WhereConditionNode(StmtNode):
    def __init__(self):
        super().__init__(IRNodeType.WhereCondition)
        self.id = None
        self.type = None
        self.desc = None


class SetTypeNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.SetType)
        self.type = None
        self.type1 = None
        self.type2 = None
        self.cnt = None


class MatrixTypeNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.MatrixType)
        self.id1 = None
        self.id2 = None
        self.type = None


class VectorTypeNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.VectorType)
        self.id1 = None
        self.type = None


class ScalarTypeNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.ScalarType)
        self.is_int = False


class FunctionTypeNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.FunctionType)
        self.params = []
        self.ret = None


class BlockNode(StmtNode):
    def __init__(self):
        super().__init__(IRNodeType.Block)
        self.stmts = []

    def add_stmt(self, stmt):
        if isinstance(stmt, BlockNode):
            self.stmts += stmt.stmts
        else:
            self.stmts.append(stmt)


class AssignNode(StmtNode):
    def __init__(self, left=None, right=None):
        super().__init__(IRNodeType.Assignment)
        self.left = left
        self.right = right
        self.op = None
        self.symbols = None


class IfNode(StmtNode):
    def __init__(self):
        super().__init__(IRNodeType.If)
        self.cond = None




class InNode(StmtNode):
    def __init__(self):
        super().__init__(IRNodeType.In)
        self.items = []
        self.set = None


class NotInNode(StmtNode):
    def __init__(self):
        super().__init__(IRNodeType.NotIn)
        self.items = []
        self.set = None


class BinCompNode(StmtNode):
    def __init__(self):
        super().__init__(IRNodeType.BinComp)
        self.left = None
        self.right = None

class NeNode(StmtNode):
    def __init__(self):
        super().__init__(IRNodeType.Ne)
        self.left = None
        self.right = None


class EqNode(StmtNode):
    def __init__(self):
        super().__init__(IRNodeType.Eq)
        self.left = None
        self.right = None

class GtNode(StmtNode):
    def __init__(self):
        super().__init__(IRNodeType.Gt)
        self.left = None
        self.right = None


class GeNode(StmtNode):
    def __init__(self):
        super().__init__(IRNodeType.Ge)
        self.left = None
        self.right = None


class LtNode(StmtNode):
    def __init__(self):
        super().__init__(IRNodeType.Lt)
        self.left = None
        self.right = None


class LeNode(StmtNode):
    def __init__(self):
        super().__init__(IRNodeType.Le)
        self.left = None
        self.right = None

####################################################


class ExpressionNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Expression)
        self.value = None
        self.sign = None

class IdNode(ExprNode):
    def __init__(self, main_id='', subs=None):
        super().__init__(IRNodeType.Id)
        self.name = None
        self.main_id = main_id
        self.subs = subs

    def contain_subscript(self):
        if self.subs is None:
            return False
        return len(self.subs) > 0

    def get_all_ids(self):
        return [self.main_id, self.subs]

    def get_main_id(self):
        return self.main_id

    def get_name(self):
        if self.contain_subscript():
            return self.main_id + '_' + ''.join(self.subs)
        else:
            return self.main_id


class AddNode(ExprNode):
    def __init__(self, left=None, right=None):
        super().__init__(IRNodeType.Add)
        self.left = left
        self.right = right


class SubNode(ExprNode):
    def __init__(self, left=None, right=None):
        super().__init__(IRNodeType.Sub)
        self.left = left
        self.right = right


class AddSubNode(ExprNode):
    def __init__(self, left=None, right=None):
        super().__init__(IRNodeType.AddSub)
        self.left = left
        self.right = right


class MulNode(ExprNode):
    def __init__(self, left=None, right=None):
        super().__init__(IRNodeType.Mul)
        self.left = left
        self.right = right


class DivNode(ExprNode):
    def __init__(self, left=None, right=None):
        super().__init__(IRNodeType.Div)
        self.left = left
        self.right = right


class MatrixNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Matrix)
        self.items = None
        self.symbol = None
        self.value = None


class MatrixRowsNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.MatrixRows)
        self.rs = None
        self.r = None


class MatrixRowNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.MatrixRow)
        self.rc = None
        self.exp = None


class MatrixRowCommasNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.MatrixRowCommas)
        self.value = None
        self.exp = None


class SummationNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Summation)
        self.sub = None
        self.exp = None
        self.id = None
        self.cond = None
        self.symbols = None
        self.symbol = None
        self.content = None


class DeterminantNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Determinant)
        self.value = None


class TransposeNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Transpose)
        self.f = None


class PowerNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Power)
        self.base = None
        self.t = None
        self.r = None
        self.power = None


class SolverNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Solver)
        self.left = None
        self.right = None


class SparseMatrixNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.SparseMatrix)
        self.ifs = None
        self.other = None
        self.id2 = None
        self.id1 = None


class SparseIfNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.SparseIf)
        self.stat = None
        self.id0 = None
        self.id1 = None
        self.id2 = None


class SparseIfsNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.SparseIfs)
        self.cond_list = []


class SparseOtherNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.SparseOther)


class ExpInMatrixNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.ExpInMatrix)
        self.value = None
        self.sign = None


class NumMatrixNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.NumMatrix)
        self.id = None
        self.id1 = None
        self.id2 = None
        self.left = None


class SubexpressionNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Subexpression)
        self.value = None


class DerivativeNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Derivative)
        self.value = None


class FactorNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Factor)
        self.op = None
        self.sub = None
        self.nm = None
        self.id = None
        self.num = None
        self.m = None
        self.s = None


class NumberNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Number)
        self.value = None


class IntegerNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Integer)
        self.value = None


class FunctionNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Function)
        self.params = []
        self.ret = None
        self.name = None




