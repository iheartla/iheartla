from la_parser.la_types import *
import weakref


class IRNodeType(Enum):
    INVALID = -1
    # base
    Id = 0
    Double = 1
    Integer = 2
    Factor = 3
    Expression = 4
    Subexpression = 5
    Constant = 6
    # control
    Start = 50
    Block = 51
    Assignment = 52
    If = 53
    Function = 54
    # if condition
    In = 100
    NotIn = 101
    BinComp = 102
    Eq = 103
    Ne = 104
    Lt = 105
    Le = 106
    Gt = 107
    Ge = 108
    # operators
    Add = 200
    Sub = 201
    Mul = 202
    Div = 203
    AddSub = 204
    Summation = 205
    Norm = 206
    Transpose = 207
    Power = 208
    Solver = 209
    Derivative = 210
    MathFunc = 211
    # matrix
    Matrix = 300
    MatrixRows = 301
    MatrixRow = 302
    MatrixRowCommas = 303
    ExpInMatrix = 304
    SparseMatrix = 305
    SparseIfs = 306
    SparseIf = 307
    SparseOther = 308
    NumMatrix = 309
    # where block
    WhereConditions = 400
    WhereCondition = 401
    MatrixType = 402
    VectorType = 403
    SetType = 404
    ScalarType = 405
    FunctionType = 406


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
    def __init__(self, comp_type=IRNodeType.INVALID, left=None, right=None):
        super().__init__(IRNodeType.BinComp)
        self.comp_type = comp_type
        self.left = left
        self.right = right


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


class NormType(Enum):
    NormInvalid = -1
    NormFrobenius = 0
    NormNuclear = 1
    NormInteger = 2
    NormIdentifier = 3
    NormMax = 4


class NormNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Norm)
        self.value = None
        self.sub = None
        self.norm_type = NormType.NormInvalid


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


class ConstantType(Enum):
    ConstantInvalid = -1
    ConstantPi = 0


class ConstantNode(ExprNode):
    def __init__(self, c_type=ConstantType.ConstantInvalid):
        super().__init__(IRNodeType.Constant)
        self.c_type = c_type


class DerivativeNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Derivative)
        self.value = None


class MathFuncType(Enum):
    MathFuncInvalid = -1
    MathFuncSin = 0
    MathFuncAsin = 1
    MathFuncCos = 2
    MathFuncAcos = 3
    MathFuncTan = 4
    MathFuncAtan = 5
    MathFuncAtan2 = 6
    MathFuncExp = 7
    MathFuncLog = 8
    MathFuncLn = 9
    MathFuncSqrt = 10


class MathFuncNode(ExprNode):
    def __init__(self, param=None, func_type=MathFuncType.MathFuncInvalid, remain_params=[]):
        super().__init__(IRNodeType.MathFunc)
        self.param = param   # first param
        self.remain_params = remain_params  # remain params
        self.func_type = func_type


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


class DoubleNode(ExprNode):
    def __init__(self):
        super().__init__(IRNodeType.Double)
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