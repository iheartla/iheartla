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
    Optimize = 212
    Domain = 213
    Integral = 214
    InnerProduct = 215
    FroProduct = 216
    HadamardProduct = 217
    CrossProduct = 218
    KroneckerProduct = 219
    DotProduct = 220
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
    Vector = 310
    #
    MatrixIndex = 320
    VectorIndex = 321
    SequenceIndex = 322
    # where block
    ParamsBlock = 399
    WhereConditions = 400
    WhereCondition = 401
    MatrixType = 402
    VectorType = 403
    SetType = 404
    ScalarType = 405
    FunctionType = 406
    # Derivatives
    Import = 500


class IRNode(object):
    def __init__(self, node_type=None, parent=None, parse_info=None, raw_text=None):
        super().__init__()
        self.node_type = node_type
        self.la_type = None
        self.parent = None
        self.set_parent(parent)
        self.parse_info = parse_info
        self.raw_text = raw_text

    def set_parent(self, parent):
        if parent:
            self.parent = weakref.ref(parent)

    def get_ancestor(self, node_type):
        if self.parent is not None:
            parent = self.parent()
            while parent is not None:
                if parent.node_type == node_type:
                    return parent
                else:
                    parent = parent.parent()
        return None


class StmtNode(IRNode):
    def __init__(self, node_type=None, parse_info=None, raw_text=None):
        super().__init__(node_type, parse_info=parse_info, raw_text=raw_text)


class ExprNode(IRNode):
    def __init__(self, node_type=None, parse_info=None, raw_text=None):
        super().__init__(node_type, parse_info=parse_info, raw_text=raw_text)


class StartNode(StmtNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Start, parse_info=parse_info, raw_text=raw_text)
        self.cond = None
        self.given_cond = None
        self.stat = None
        self.directives = []
        self.vblock = []

    def get_stat_list(self):
        stat_list = []
        index_list = []
        for index in range(len(self.vblock)):
            vblock = self.vblock[index]
            if isinstance(vblock, list):
                stat_list += vblock
                index_list.append(index)
        return stat_list, index_list

    def get_package_dict(self):
        package_func_dict = {}
        for directive in self.directives:
            if directive.package in package_func_dict:
                package_func_dict[directive.package] = list(set(package_func_dict[directive.package] + directive.names))
            else:
                package_func_dict[directive.package] = list(set(directive.names))
            package_func_dict[directive.package].sort()
        return package_func_dict


class ParamsBlockNode(StmtNode):
    def __init__(self, parse_info=None, raw_text=None, annotation=None, conds=None):
        super().__init__(IRNodeType.ParamsBlock, parse_info=parse_info, raw_text=raw_text)
        self.annotation = annotation
        self.conds = conds


class WhereConditionsNode(StmtNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.WhereConditions, parse_info=parse_info, raw_text=raw_text)
        self.value = []


class WhereConditionNode(StmtNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.WhereCondition, parse_info=parse_info, raw_text=raw_text)
        self.id = None
        self.type = None
        self.desc = None


class SetTypeNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.SetType, parse_info=parse_info, raw_text=raw_text)
        self.type = None
        self.type1 = None
        self.type2 = None
        self.cnt = None


class MatrixTypeNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.MatrixType, parse_info=parse_info, raw_text=raw_text)
        self.id1 = None
        self.id2 = None
        self.type = None


class VectorTypeNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.VectorType, parse_info=parse_info, raw_text=raw_text)
        self.id1 = None
        self.type = None


class ScalarTypeNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.ScalarType, parse_info=parse_info, raw_text=raw_text)
        self.is_int = False


class FunctionTypeNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.FunctionType, parse_info=parse_info, raw_text=raw_text)
        self.empty = None
        self.params = []
        self.separators = []
        self.ret = None


class ImportNode(StmtNode):
    def __init__(self, package=None, names=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Import, parse_info=parse_info, raw_text=raw_text)
        self.package = package
        self.names = names


class BlockNode(StmtNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Block, parse_info=parse_info, raw_text=raw_text)
        self.stmts = []

    def add_stmt(self, stmt):
        if isinstance(stmt, BlockNode):
            self.stmts += stmt.stmts
        else:
            self.stmts.append(stmt)


class AssignNode(StmtNode):
    def __init__(self, left=None, right=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Assignment, parse_info=parse_info, raw_text=raw_text)
        self.left = left   # IdNode,MatrixIndexNode,VectorIndexNode,VectorIndexNode
        self.right = right
        self.op = None
        self.symbols = None


class IfNode(StmtNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.If, parse_info=parse_info, raw_text=raw_text)
        self.cond = None


class InNode(StmtNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.In, parse_info=parse_info, raw_text=raw_text)
        self.items = []
        self.set = None


class NotInNode(StmtNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.NotIn, parse_info=parse_info, raw_text=raw_text)
        self.items = []
        self.set = None


class BinCompNode(StmtNode):
    def __init__(self, comp_type=IRNodeType.INVALID, left=None, right=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.BinComp, parse_info=parse_info, raw_text=raw_text)
        self.comp_type = comp_type
        self.left = left
        self.right = right


####################################################


class ExpressionNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Expression, parse_info=parse_info, raw_text=raw_text)
        self.value = None
        self.sign = None


class IdNode(ExprNode):
    def __init__(self, main_id='', subs=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Id, parse_info=parse_info, raw_text=raw_text)
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

    def convert_to_vector_index(self):
        vector_index_node = VectorIndexNode()
        vector_index_node.main = self.main_id
        vector_index_node.row_index = self.subs[0]
        return vector_index_node

    def convert_to_sequence_index(self):
        seq_index_node = SequenceIndexNode()
        seq_index_node.main = self.main_id
        seq_index_node.main_index = self.subs[0]
        return seq_index_node


class AddNode(ExprNode):
    def __init__(self, left=None, right=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Add, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right


class SubNode(ExprNode):
    def __init__(self, left=None, right=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Sub, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right


class AddSubNode(ExprNode):
    def __init__(self, left=None, right=None):
        super().__init__(IRNodeType.AddSub)
        self.left = left
        self.right = right


class MulOpType(Enum):
    # in case there'll be more valid symbols
    MulOpInvalid = -1
    MulOpDot = 0


class MulNode(ExprNode):
    def __init__(self, left=None, right=None, parse_info=None, raw_text=None, op=MulOpType.MulOpInvalid):
        super().__init__(IRNodeType.Mul, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right
        self.op = op


class DivOpType(Enum):
    DivOpInvalid = -1
    DivOpSlash = 0
    DivOpUnicode = 1


class DivNode(ExprNode):
    def __init__(self, left=None, right=None, parse_info=None, raw_text=None, op=DivOpType.DivOpSlash):
        super().__init__(IRNodeType.Div, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right
        self.op = op


class MatrixNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Matrix, parse_info=parse_info, raw_text=raw_text)
        self.items = None
        self.symbol = None
        self.value = None


class VectorNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Vector, parse_info=parse_info, raw_text=raw_text)
        self.items = []
        self.symbol = None


class MatrixRowsNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.MatrixRows, parse_info=parse_info, raw_text=raw_text)
        self.rs = None
        self.r = None


class MatrixRowNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.MatrixRow, parse_info=parse_info, raw_text=raw_text)
        self.rc = None
        self.exp = None


class MatrixRowCommasNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.MatrixRowCommas, parse_info=parse_info, raw_text=raw_text)
        self.value = None
        self.exp = None


class SummationNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Summation, parse_info=parse_info, raw_text=raw_text)
        self.sub = None
        self.exp = None
        self.id = None
        self.cond = None
        self.symbols = None
        self.symbol = None
        self.content = None
        self.sym_dict = None


class OptimizeType(Enum):
    OptimizeInvalid = -1
    OptimizeMin = 0
    OptimizeMax = 1
    OptimizeArgmin = 2
    OptimizeArgmax = 3


class OptimizeNode(ExprNode):
    def __init__(self, opt_type=OptimizeType.OptimizeInvalid, cond_list=[], exp=None, base=None, base_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Optimize, parse_info=parse_info, raw_text=raw_text)
        self.opt_type = opt_type
        self.cond_list = cond_list
        self.exp = exp
        self.base = base
        self.base_type = base_type


class DomainNode(ExprNode):
    def __init__(self, lower=None, upper=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Domain, parse_info=parse_info, raw_text=raw_text)
        self.upper = upper
        self.lower = lower


class IntegralNode(ExprNode):
    def __init__(self, domain=None, exp=None, base=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Integral, parse_info=parse_info, raw_text=raw_text)
        self.domain = domain
        self.exp = exp
        self.base = base


class InnerProductNode(ExprNode):
    def __init__(self, left=None, right=None, sub=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.InnerProduct, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right
        self.sub = sub


class FroProductNode(ExprNode):
    def __init__(self, left=None, right=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.FroProduct, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right


class HadamardProductNode(ExprNode):
    def __init__(self, left=None, right=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.HadamardProduct, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right


class CrossProductNode(ExprNode):
    def __init__(self, left=None, right=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.CrossProduct, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right


class KroneckerProductNode(ExprNode):
    def __init__(self, left=None, right=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.KroneckerProduct, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right


class DotProductNode(ExprNode):
    def __init__(self, left=None, right=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.DotProduct, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right


class NormType(Enum):
    NormInvalid = -1
    NormFrobenius = 0
    NormNuclear = 1
    NormInteger = 2
    NormIdentifier = 3
    NormMax = 4


class NormNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Norm, parse_info=parse_info, raw_text=raw_text)
        self.value = None
        self.sub = None
        self.norm_type = NormType.NormInvalid


class TransposeNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Transpose, parse_info=parse_info, raw_text=raw_text)
        self.f = None


class PowerNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Power, parse_info=parse_info, raw_text=raw_text)
        self.base = None
        self.t = None
        self.r = None
        self.power = None


class SolverNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Solver, parse_info=parse_info, raw_text=raw_text)
        self.left = None
        self.right = None


class SparseMatrixNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.SparseMatrix, parse_info=parse_info, raw_text=raw_text)
        self.ifs = None
        self.other = None
        self.id2 = None
        self.id1 = None


class SparseIfNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.SparseIf, parse_info=parse_info, raw_text=raw_text)
        self.stat = None
        self.id0 = None
        self.id1 = None
        self.id2 = None


class SparseIfsNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.SparseIfs, parse_info=parse_info, raw_text=raw_text)
        self.cond_list = []


class SparseOtherNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.SparseOther, parse_info=parse_info, raw_text=raw_text)


class ExpInMatrixNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.ExpInMatrix, parse_info=parse_info, raw_text=raw_text)
        self.value = None
        self.sign = None


class NumMatrixNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.NumMatrix, parse_info=parse_info, raw_text=raw_text)
        self.id = None
        self.id1 = None
        self.id2 = None
        self.left = None


class MatrixIndexNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.MatrixIndex, parse_info=parse_info, raw_text=raw_text)
        self.main = None
        self.row_index = None
        self.col_index = None
        self.subs = None

    def contain_subscript(self):
        return True

    def get_all_ids(self):
        return [self.main.get_main_id(), [self.row_index.get_main_id(), self.col_index.get_main_id()]]

    def get_main_id(self):
        return self.main.get_main_id()


class VectorIndexNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.VectorIndex, parse_info=parse_info, raw_text=raw_text)
        self.main = None
        self.row_index = None

    def contain_subscript(self):
        return True

    def get_all_ids(self):
        return [self.main.get_main_id(), [self.row_index.get_main_id()]]

    def get_main_id(self):
        return self.main.get_main_id()


class SequenceIndexNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.SequenceIndex, parse_info=parse_info, raw_text=raw_text)
        self.main = None
        self.main_index = None
        self.row_index = None
        self.col_index = None
        self.slice_matrix = False

    def contain_subscript(self):
        return True

    def get_all_ids(self):
        if self.row_index:
            return [self.main.get_main_id(), [self.main_index.get_main_id(), self.row_index.get_main_id(), self.col_index.get_main_id()]]
        else:
            return [self.main.get_main_id(), [self.main_index.get_main_id()]]

    def get_main_id(self):
        return self.main.get_main_id()


class SubexpressionNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Subexpression, parse_info=parse_info, raw_text=raw_text)
        self.value = None


class ConstantType(Enum):
    ConstantInvalid = -1
    ConstantPi = 0
    ConstantE = 1


class ConstantNode(ExprNode):
    def __init__(self, c_type=ConstantType.ConstantInvalid, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Constant, parse_info=parse_info, raw_text=raw_text)
        self.c_type = c_type


class DerivativeNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Derivative, parse_info=parse_info, raw_text=raw_text)
        self.value = None


class MathFuncType(IntEnum):
    MathFuncInvalid = -1
    MathFuncSin = 0
    MathFuncAsin = 1
    MathFuncCos = 2
    MathFuncAcos = 3
    MathFuncTan = 4
    MathFuncAtan = 5
    MathFuncSinh = 6
    MathFuncAsinh = 7
    MathFuncCosh = 8
    MathFuncAcosh = 9
    MathFuncTanh = 10
    MathFuncAtanh = 11
    MathFuncCot = 12
    MathFuncSec = 13
    MathFuncCsc = 14
    #
    MathFuncAtan2 = 15
    MathFuncExp = 16
    MathFuncLog = 17
    MathFuncLn = 18
    MathFuncSqrt = 19


class MathFuncNode(ExprNode):
    def __init__(self, param=None, func_type=MathFuncType.MathFuncInvalid, remain_params=[], func_name=None, separator=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.MathFunc, parse_info=parse_info, raw_text=raw_text)
        self.param = param   # first param
        self.remain_params = remain_params  # remain params
        self.func_type = func_type
        self.func_name = func_name
        self.separator = separator
        if param is not None:
            self.parse_info = param.parse_info


class FactorNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Factor, parse_info=parse_info, raw_text=raw_text)
        self.op = None
        self.sub = None
        self.nm = None
        self.id = None
        self.num = None
        self.m = None
        self.v = None
        self.s = None


class DoubleNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Double, parse_info=parse_info, raw_text=raw_text)
        self.value = None


class IntegerNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Integer, parse_info=parse_info, raw_text=raw_text)
        self.value = None


class FunctionNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Function, parse_info=parse_info, raw_text=raw_text)
        self.params = []
        self.separators = []
        self.ret = None
        self.name = None