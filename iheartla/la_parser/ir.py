from .la_types import *
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
    Cast = 7
    Fraction = 8
    # control
    Start = 50
    Block = 51
    Assignment = 52
    If = 53
    Function = 54
    LocalFunc = 55
    # if condition
    Condition = 99
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
    Squareroot = 221
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
    ToMatrix = 311
    MultiConds = 312
    #
    MatrixIndex = 320
    VectorIndex = 321
    SequenceIndex = 322
    SeqDimIndex = 323
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

    def is_node(self, node_type):
        return self.node_type == node_type

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
                    if parent.parent:
                        parent = parent.parent()
                    else:
                        parent = None
        return None

    def get_child(self, node_type):
        return None

class StmtNode(IRNode):
    def __init__(self, node_type=None, parse_info=None, raw_text=None):
        super().__init__(node_type, parse_info=parse_info, raw_text=raw_text)


class ExprNode(IRNode):
    def __init__(self, node_type=None, parse_info=None, raw_text=None):
        super().__init__(node_type, parse_info=parse_info, raw_text=raw_text)


class LhsNode(ExprNode):
    def __init__(self, node_type=IRNodeType.INVALID, parse_info=None, raw_text=None):
        super().__init__(node_type=node_type, parse_info=parse_info, raw_text=raw_text)
        self.lhs_sub_dict = {}  # dict of the same subscript symbol from rhs as the subscript of lhs


class StartNode(StmtNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Start, parse_info=parse_info, raw_text=raw_text)
        self.cond = None
        self.given_cond = None
        self.stat = None
        self.directives = []
        self.vblock = []
        self.dependent_modules = []
        self.module_list = []
        self.module_syms = {}

    def get_block_list(self):
        params_list = []
        stat_list = []
        index_list = []
        for index in range(len(self.vblock)):
            vblock = self.vblock[index]
            if isinstance(vblock, list):
                stat_list += vblock
                index_list.append(index)
            else:
                params_list.append(vblock)
        return params_list, stat_list, index_list

    def get_package_dict(self):
        package_func_dict = {}
        for directive in self.directives:
            if directive.package is not None:
                if directive.package.get_name() in package_func_dict:
                    package_func_dict[directive.package.get_name()] = list(set(package_func_dict[directive.package.get_name()] + directive.get_name_list()))
                else:
                    package_func_dict[directive.package.get_name()] = list(set(directive.get_name_list()))
                package_func_dict[directive.package.get_name()].sort()
        return package_func_dict

    def get_module_pars_list(self):
        module_pars_list = []
        for directive in self.directives:
            if directive.module is not None:
                for par in directive.params:
                    if par.get_name() not in module_pars_list:
                        module_pars_list.append(par.get_name())
                for sym in directive.names:
                    if sym.get_name() not in module_pars_list:
                        module_pars_list.append(sym.get_name())
        return module_pars_list

    def get_module_directives(self):
        module_list = []
        for directive in self.directives:
            if directive.module is not None:
                module_list.append(directive)
        return module_list


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
        self.id = []
        self.type = None
        self.desc = None

    def get_type_dict(self):
        ret = {}
        for name in self.id:
            ret[name.get_main_id()] = self.type.la_type
        return ret


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
    def __init__(self, package=None, module=None, names=None, separators=None, params=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Import, parse_info=parse_info, raw_text=raw_text)
        self.package = package # builtin
        self.module = module   # custom
        self.names = names     # imported symbols
        self.params = params   # parameters to initialize modules
        self.separators = separators

    def get_name_list(self):
        name_list = []
        for name in self.names:
            name_list.append(name.get_name())
        return name_list

    def get_param_list(self):
        param_list = []
        for par in self.params:
            param_list.append(par.get_name())
        return param_list



class BlockNode(StmtNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Block, parse_info=parse_info, raw_text=raw_text)
        self.stmts = []

    def add_stmt(self, stmt):
        if isinstance(stmt, BlockNode):
            self.stmts += stmt.stmts
        else:
            self.stmts.append(stmt)


class LocalFuncDefType(IntEnum):
    LocalFuncDefInvalid = -1
    LocalFuncDefParenthesis = 0
    LocalFuncDefBracket = 1


class LocalFuncNode(StmtNode):
    def __init__(self, name=None, expr=None, parse_info=None, raw_text=None, defs=[], def_type=LocalFuncDefType.LocalFuncDefParenthesis):
        super().__init__(IRNodeType.LocalFunc, parse_info=parse_info, raw_text=raw_text)
        self.name = name
        self.expr = expr
        self.op = None
        self.symbols = None
        self.def_type = def_type
        self.params = []
        self.separators = []
        self.defs = defs


class AssignNode(StmtNode):
    def __init__(self, left=None, right=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Assignment, parse_info=parse_info, raw_text=raw_text)
        self.left = left   # IdNode,MatrixIndexNode,VectorIndexNode,VectorIndexNode
        self.right = right
        self.op = None
        self.symbols = None
        self.lhs_sub_dict = {}  # dict of the same subscript symbol from rhs as the subscript of lhs


class IfNode(StmtNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.If, parse_info=parse_info, raw_text=raw_text)
        self.cond = None
        self.loop = False

    def get_child(self, node_type):
        if self.cond.is_node(node_type):
            child_node = self.cond
        else:
            child_node = self.cond.get_child(node_type)
        return child_node

    def set_loop(self, loop):
        if self.cond:
            self.cond.loop = loop


class ConditionType(IntEnum):
    ConditionInvalid = -1
    ConditionAnd = 0
    ConditionOr = 1


class ConditionNode(StmtNode):
    def __init__(self, parse_info=None, raw_text=None, cond_type=ConditionType.ConditionAnd):
        super().__init__(IRNodeType.Condition, parse_info=parse_info, raw_text=raw_text)
        self.cond_list = []
        self.cond_type = cond_type
        self.tex_node = None


class InNode(StmtNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.In, parse_info=parse_info, raw_text=raw_text)
        self.items = []
        self.set = None
        self.loop = False  # special handling

    def same_subs(self, subs):
        if len(subs) == len(self.items):
            raw_list = [item.raw_text for item in self.items]
            return set(raw_list) == set([sub for sub in subs])
        return False


class NotInNode(StmtNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.NotIn, parse_info=parse_info, raw_text=raw_text)
        self.items = []
        self.set = None


class BinCompNode(StmtNode):
    def __init__(self, comp_type=IRNodeType.INVALID, left=None, right=None, parse_info=None, raw_text=None, op=None):
        super().__init__(IRNodeType.BinComp, parse_info=parse_info, raw_text=raw_text)
        self.comp_type = comp_type
        self.left = left
        self.right = right
        self.op = op

    def get_child(self, node_type):
        if self.left.is_node(node_type):
            child_node = self.left
        elif self.right.is_node(node_type):
            child_node = self.right
        else:
            child_node = self.left.get_child(node_type)
            if child_node is None:
                child_node = self.right.get_child(node_type)
        return child_node


####################################################


class ExpressionNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Expression, parse_info=parse_info, raw_text=raw_text)
        self.value = None
        self.sign = None

    def get_child(self, node_type):
        if self.value.is_node(node_type):
            child_node = self.value
        else:
            child_node = self.value.get_child(node_type)
        return child_node


class CastNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None, value=None):
        super().__init__(IRNodeType.Cast, parse_info=parse_info, raw_text=raw_text)
        # current: 1x1 matrix -> scalar
        self.value = value
        if self.value:
            self.parse_info = value.parse_info
            self.raw_text = value.raw_text
            self.la_type = value.la_type


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

    def get_child(self, node_type):
        if self.left.is_node(node_type):
            child_node = self.left
        elif self.right.is_node(node_type):
            child_node = self.right
        else:
            child_node = self.left.get_child(node_type)
            if child_node is None:
                child_node = self.right.get_child(node_type)
        return child_node


class SubNode(ExprNode):
    def __init__(self, left=None, right=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Sub, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right

    def get_child(self, node_type):
        if self.left.is_node(node_type):
            child_node = self.left
        elif self.right.is_node(node_type):
            child_node = self.right
        else:
            child_node = self.left.get_child(node_type)
            if child_node is None:
                child_node = self.right.get_child(node_type)
        return child_node


class AddSubNode(ExprNode):
    def __init__(self, left=None, right=None, parse_info=None, raw_text=None, op='+-'):
        super().__init__(IRNodeType.AddSub, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right
        self.op = op

    def split_node(self):
        add_node = AddNode(self.left, self.right)
        add_node.set_parent(self.parent())
        sub_node = SubNode(self.left, self.right)
        sub_node.set_parent(self.parent())
        return [add_node, sub_node]

    def get_child(self, node_type):
        if self.left.is_node(node_type):
            child_node = self.left
        elif self.right.is_node(node_type):
            child_node = self.right
        else:
            child_node = self.left.get_child(node_type)
            if child_node is None:
                child_node = self.right.get_child(node_type)
        return child_node

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


class ToMatrixNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None, item=None):
        super().__init__(IRNodeType.ToMatrix, parse_info=parse_info, raw_text=raw_text)
        self.item = item


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
        self.sym_dict = None  # identifiers containing sub, used for type checking only


class OptimizeType(Enum):
    OptimizeInvalid = -1
    OptimizeMin = 0
    OptimizeMax = 1
    OptimizeArgmin = 2
    OptimizeArgmax = 3


class OptimizeNode(ExprNode):
    def __init__(self, opt_type=OptimizeType.OptimizeInvalid, cond_list=[], exp=None, base_list=[], base_type_list=[], parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Optimize, parse_info=parse_info, raw_text=raw_text)
        self.opt_type = opt_type
        self.cond_list = cond_list
        self.exp = exp
        self.base_list = base_list
        self.base_type_list = base_type_list


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
    NormDet = 5  # determinant


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


class SquarerootNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Squareroot, parse_info=parse_info, raw_text=raw_text)
        self.value = None


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
        self.pow = None   # -> pow node


class MultiCondNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.MultiConds, parse_info=parse_info, raw_text=raw_text)
        self.ifs = None
        self.other = None
        self.lhs = None


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
        self.cond = None
        self.id0 = None
        self.id1 = None
        self.id2 = None
        self.first_in_list = None
        self.loop = False  # special handling

    def set_loop(self, loop):
        self.loop = loop
        if self.cond:
            self.cond.set_loop(loop)


class SparseIfsNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.SparseIfs, parse_info=parse_info, raw_text=raw_text)
        self.cond_list = []
        self.in_cond_only = False

    def set_in_cond_only(self, value):
        self.in_cond_only = value
        if value:
            for cond in self.cond_list:
                cond.set_loop(True)


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


class IndexNode(ExprNode):
    def __init__(self, node_type=IRNodeType.INVALID, parse_info=None, raw_text=None):
        super().__init__(node_type, parse_info=parse_info, raw_text=raw_text)

    def contain_sub_sym(self, sym):
        return False

    def get_name(self):
        return self.raw_text if self.raw_text is not None else ''

    def process_subs_dict(self, subs_dict):
        if len(subs_dict) == 0:
            return
        for key in subs_dict.keys():
            if self.contain_sub_sym(key):
                subs_dict[key].append(self)
                # break


class MatrixIndexNode(IndexNode):
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

    def contain_sub_sym(self, sym):
        if self.row_index and self.row_index.node_type == IRNodeType.Id and self.row_index.get_main_id() == sym:
            return True
        if self.col_index and self.col_index.node_type == IRNodeType.Id and self.col_index.get_main_id() == sym:
            return True
        return False

    def same_as_row_sym(self, sym):
        if self.row_index and self.row_index.node_type == IRNodeType.Id and self.row_index.get_main_id() == sym:
            return True
        return False

    def same_as_col_sym(self, sym):
        if self.col_index and self.col_index.node_type == IRNodeType.Id and self.col_index.get_main_id() == sym:
            return True
        return False


class VectorIndexNode(IndexNode):
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

    def contain_sub_sym(self, sym):
        if self.row_index and self.row_index.node_type == IRNodeType.Id and self.row_index.get_main_id() == sym:
            return True
        return False


class SequenceIndexNode(IndexNode):
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

    def contain_sub_sym(self, sym):
        if self.main_index and self.main_index.node_type == IRNodeType.Id and self.main_index.get_main_id() == sym:
            return True
        if self.row_index and self.row_index.node_type == IRNodeType.Id and self.row_index.get_main_id() == sym:
            return True
        if self.col_index and self.col_index.node_type == IRNodeType.Id and self.col_index.get_main_id() == sym:
            return True
        return False

    def same_as_size_sym(self, sym):
        if self.main_index and self.main_index.node_type == IRNodeType.Id and self.main_index.get_main_id() == sym:
            return True
        return False

    def same_as_row_sym(self, sym):
        if self.row_index and self.row_index.node_type == IRNodeType.Id and self.row_index.get_main_id() == sym:
            return True
        return False

    def same_as_col_sym(self, sym):
        if self.col_index and self.col_index.node_type == IRNodeType.Id and self.col_index.get_main_id() == sym:
            return True
        return False


class SeqDimIndexNode(IndexNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.SeqDimIndex, parse_info=parse_info, raw_text=raw_text)
        self.main = None
        self.main_index = None
        self.real_symbol = None
        self.dim_index = 1  # 1 or 2

    def get_main_id(self):
        return self.main.get_main_id()

    def is_row_index(self):
        return self.dim_index == 1

    def contain_sub_sym(self, sym):
        if self.main_index and self.main_index.node_type == IRNodeType.Id and self.main_index.get_main_id() == sym:
            return True
        return False


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
    MathFuncLog2 = 18
    MathFuncLog10 = 19
    MathFuncLn = 20
    MathFuncSqrt = 21
    #
    MathFuncTrace = 22
    MathFuncDiag = 23
    MathFuncVec = 24
    MathFuncDet = 25
    MathFuncRank = 26
    MathFuncNull = 27
    MathFuncOrth = 28
    MathFuncInv = 29


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


class FractionNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None, numerator=None, denominator=None):
        super().__init__(IRNodeType.Fraction, parse_info=parse_info, raw_text=raw_text)
        self.denominator = denominator
        self.numerator = numerator
        self.unicode = raw_text


class IntegerNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None, value=None):
        super().__init__(IRNodeType.Integer, parse_info=parse_info, raw_text=raw_text)
        self.value = value


class FunctionNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Function, parse_info=parse_info, raw_text=raw_text)
        self.params = []
        self.separators = []
        self.ret = None
        self.name = None
