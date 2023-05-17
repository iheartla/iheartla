from .la_types import *
from ..la_tools.la_package import *
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
    Equation = 56
    Destructuring = 57
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
    PseudoInverse = 222
    Divergence = 223
    Gradient = 224
    Laplace = 225
    Partial = 226
    Size = 227
    Module = 228
    Geometry = 229
    GPFunction = 230
    Union = 231
    Intersection = 232
    Difference = 233
    UnionSequence = 234
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
    Set = 313
    ElementConvert = 314
    ToDouble = 315
    #
    MatrixIndex = 320
    VectorIndex = 321
    SequenceIndex = 322
    SeqDimIndex = 323
    TupleIndex = 324
    SetIndex = 325
    # where block
    ParamsBlock = 399
    WhereConditions = 400
    WhereCondition = 401
    MatrixType = 402
    VectorType = 403
    SetType = 404
    ScalarType = 405
    FunctionType = 406
    MappingType = 407
    TupleType = 408
    NamedType = 409
    # Derivatives
    Import = 500
    ImportVar = 501
    # differential equations
    OdeFirstOrder = 600


class IRNode(object):
    def __init__(self, node_type=None, parent=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__()
        self.node_type = node_type
        self._la_type = la_type if la_type else LaVarType(VarTypeEnum.INVALID)
        self.parent = None
        self.set_parent(parent)
        self.parse_info = parse_info
        self.raw_text = raw_text

    @property
    def la_type(self):
        return self._la_type

    @la_type.setter
    def la_type(self, value):
        self._la_type = value if value else LaVarType(VarTypeEnum.INVALID)

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

    def contain_sym(self, sym):
        return sym in self.raw_text

    def get_signature(self, extra=None):
        return self.raw_text

class StmtNode(IRNode):
    def __init__(self, node_type=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(node_type, la_type=la_type, parse_info=parse_info, raw_text=raw_text)


class ExprNode(IRNode):
    def __init__(self, node_type=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(node_type, la_type=la_type, parse_info=parse_info, raw_text=raw_text)


class LhsNode(ExprNode):
    def __init__(self, node_type=IRNodeType.INVALID, la_type=None, parse_info=None, raw_text=None):
        super().__init__(node_type=node_type, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.lhs_sub_dict = {}  # dict of the same subscript symbol from rhs as the subscript of lhs


class StartNode(StmtNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Start, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
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

    def get_package_rdict(self):
        package_rdict = {}
        for directive in self.directives:
            if directive.package is not None:
                if directive.package.get_name() not in package_rdict:
                    package_rdict[directive.package.get_name()] = directive.r_dict
        return package_rdict

    def get_module_pars_list(self):
        # to get multi-letter syms
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
    def __init__(self, la_type=None, parse_info=None, raw_text=None, annotation=None, conds=None):
        super().__init__(IRNodeType.ParamsBlock, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.annotation = annotation
        self.conds = conds


class WhereConditionsNode(StmtNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.WhereConditions, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.value = []


class WhereConditionNode(StmtNode):
    def __init__(self, la_type=None, attrib=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.WhereCondition, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.id = []
        self.type = None
        self.attrib = attrib
        self.desc = None
        self.belong = None

    def get_type_dict(self):
        ret = {}
        for name in self.id:
            ret[name.get_main_id()] = self.type.la_type
        return ret


class SetTypeNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.SetType, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.type = None
        self.type1 = None
        self.type2 = None
        self.cnt = None
        self.sub_types = None
        self.homogeneous_types = None


class TupleTypeNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.TupleType, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.sub_types = None


class MatrixTypeNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.MatrixType, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.id1 = None
        self.id2 = None
        self.type = None


class VectorTypeNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.VectorType, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.id1 = None
        self.type = None


class ScalarTypeNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.ScalarType, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.is_int = False


class NamedTypeNode(ExprNode):
    def __init__(self, la_type=None, name=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.NamedType, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.name = name

class FunctionTypeNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.FunctionType, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.empty = None
        self.params = []
        self.separators = []
        self.ret = None


class MappingTypeNode(ExprNode):
    def __init__(self, src=None, dst=None, ele_set=None, subset=False, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.MappingType, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.src = src
        self.dst = dst
        self.ele_set = ele_set
        self.subset = subset


class ImportNode(StmtNode):
    def __init__(self, package=None, module=None, names=None, separators=None, params=None, r_dict=None, import_all=False, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Import, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.package = package # builtin
        self.module = module   # custom
        self.names = names     # imported symbols
        self.params = params   # parameters to initialize modules
        self.separators = separators
        self.r_dict = r_dict   # A as B from XXX
        self.import_all = import_all

    def get_name_list(self):
        # original imported names
        name_list = []
        for name in self.names:
            name_list.append(name.get_name())
        return name_list

    def get_rname_list(self):
        # converted imported names
        name_list = []
        for name in self.names:
            name_list.append(self.r_dict[name.get_name()])
        return name_list

    def get_name_raw_list(self):
        name_list = []
        for name in self.names:
            raw = name.get_name()
            if raw in self.r_dict and raw != self.r_dict[raw]:
                name_list.append("{} as {}".format(raw, self.r_dict[raw]))
            else:
                name_list.append(raw)
        return name_list

    def get_param_list(self):
        param_list = []
        for par in self.params:
            param_list.append(par.get_name())
        return param_list

    def get_imported_sym(self):
        return [name.get_main_id() if name.get_main_id() not in self.r_dict else self.r_dict[name.get_main_id()] for name in self.names]


class ImportVarNode(StmtNode):
    def __init__(self, name=None, rname=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.ImportVar, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.name = name
        self.rname = rname


class BlockNode(StmtNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Block, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.stmts = []
        self.meshset_list = []    # index for meshset assignment in stmts

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
    def __init__(self, name=None, expr=None, la_type=None, parse_info=None, raw_text=None, defs=[], def_type=LocalFuncDefType.LocalFuncDefParenthesis, identity_name=None):
        super().__init__(IRNodeType.LocalFunc, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.name = name  # original name in source code
        self.identity_name = identity_name if identity_name else name   # unique name in output
        self.expr = expr
        self.op = None
        self.symbols = None
        self.def_type = def_type
        self.params = []
        self.separators = []
        self.defs = defs
        self.n_subs = 0   # number of subscripts
        self.extra_list = []  # extra assignments
        self.tex_list = []    # extra assignments for tex output
        self.scope_name = None


class DestructuringType(IntEnum):
    DestructuringTypeInvalid = -1
    DestructuringSet = 0
    DestructuringSequence = 1
    DestructuringVector = 2
    DestructuringTuple = 3
    DestructuringList = 4


class DestructuringNode(StmtNode):
    def __init__(self, left=None, right=None, op=None, la_type=None, parse_info=None, raw_text=None, cur_type=DestructuringType.DestructuringSet):
        super().__init__(IRNodeType.Destructuring, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.left = left   # IdNode 
        self.right = right
        self.op = op 
        self.cur_type = cur_type
        self.la_list = None

    def get_lhs_list(self):
        # get all new symbols
        return [lhs.get_main_id() for lhs in self.left]


class AssignType(IntEnum):
    AssignTypeInvalid = -1
    AssignTypeNormal = 0
    AssignTypeSolver = 1


class AssignNode(StmtNode):
    def __init__(self, left=None, right=None, op=None, la_type=None, parse_info=None, raw_text=None, cur_type=AssignType.AssignTypeNormal):
        super().__init__(IRNodeType.Assignment, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.left = left   # IdNode,MatrixIndexNode,VectorIndexNode,VectorIndexNode
        self.right = right
        self.op = op
        self.symbols = set()
        self.lhs_sub_dict = {}  # dict of the same subscript symbol from rhs as the subscript of lhs
        self.optimize_param = False
        self.cur_type = cur_type
        self.unknown_id = None
        self.change_ele_only = False   # change an element inside a matrix/vector/sequence
        self.need_sparse_hessian = False   # whether we need a sparse hessian for the current assignment
        self.new_hessian_name = ''         # new name
        self.hessian_var = ""              # variable in current hessian

    def get_lhs_list(self):
        # get all new symbols
        return [lhs.get_main_id() for lhs in self.left]

class EqTypeEnum(IntFlag):
    INVALID = 0
    DEFAULT = 1
    #
    NORMAL = 1
    ODE = 2
    PDE = 4


class EquationNode(StmtNode):
    def __init__(self, left=None, right=None, eq_type=EqTypeEnum.DEFAULT, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Equation, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.left = left if left is not None else []
        self.right = right if right is not None else []
        self.symbols = set()
        self.unknown_id = None
        self.eq_type = eq_type
        self.init_list = []
        self.param_dict = {}

    def is_formal_eq(self):
        # not as initial conditions
        return self.unknown_id is not None

    def get_solved_name(self):
        if self.unknown_id:
            return self.unknown_id.get_main_id()
        return ''

    def add_init(self, init):
        self.init_list.append(init)


class IfNode(StmtNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.If, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
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
    def __init__(self, la_type=None, parse_info=None, raw_text=None, cond_type=ConditionType.ConditionAnd):
        super().__init__(IRNodeType.Condition, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.cond_list = []
        self.cond_type = cond_type
        self.tex_node = None
        self.loop = False

    def get_single_in_node(self):
        # whether it only has in conditional
        if len(self.cond_list) == 1:
            if self.cond_list[0].is_node(IRNodeType.Condition):
                return self.cond_list[0].get_single_in_node()
            else:
                if self.cond_list[0].cond.is_node(IRNodeType.In):
                    return self.cond_list[0].cond
        return None

    def same_subs(self, subs):
        # check whether there's only in conditional with the same subs  
        node = self.get_single_in_node()
        if node is not None and node.same_subs(subs):
            return True
        return False

    def set_loop(self, loop):
        self.loop = loop
        for cond in self.cond_list:
            cond.set_loop(loop)


class InNode(StmtNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.In, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.items = []
        self.set = None
        self.loop = False  # special handling

    def same_subs(self, subs):
        if len(subs) == len(self.items):
            raw_list = [item.raw_text for item in self.items]
            return set(raw_list) == set([sub for sub in subs])
        return False


class NotInNode(StmtNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.NotIn, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.items = []
        self.set = None


class BinCompNode(StmtNode):
    def __init__(self, comp_type=IRNodeType.INVALID, left=None, right=None, la_type=None, parse_info=None, raw_text=None, op=None):
        super().__init__(IRNodeType.BinComp, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
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
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Expression, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.value = None
        self.sign = None

    def get_child(self, node_type):
        if self.value.is_node(node_type):
            child_node = self.value
        else:
            child_node = self.value.get_child(node_type)
        return child_node
    
    def is_id_node(self):
        # whether the current node can be simplified as an id node
        is_id = False
        if self.value.is_node(IRNodeType.Factor):
            if self.value.id:
                is_id = True
        return is_id


class CastNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None, value=None):
        super().__init__(IRNodeType.Cast, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        # current: 1x1 matrix -> scalar
        self.value = value
        if self.value:
            self.parse_info = value.parse_info
            self.raw_text = value.raw_text
            self.la_type = value.la_type


class IdNode(ExprNode):
    def __init__(self, main_id='', subs=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Id, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
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
    def __init__(self, left=None, right=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Add, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
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
    def __init__(self, left=None, right=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Sub, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
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

class UnionFormat(IntEnum):
    UnionInvalid = -1
    UnionNormal = 0  # a ∪ b
    UnionAdd = 1     # a + b
class UnionNode(ExprNode):
    def __init__(self, left=None, right=None, union_format=UnionFormat.UnionNormal, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Union, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right
        self.union_format = union_format

class IntersectionNode(ExprNode):
    def __init__(self, left=None, right=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Intersection, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right

class DiffFormat(IntEnum):
    DiffInvalid = -1
    DiffNormal = 0  # a - b
    DiffSplit = 1   # a \ b

class DifferenceNode(ExprNode):
    def __init__(self, left=None, right=None, diff_format=DiffFormat.DiffNormal, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Difference, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right
        self.diff_format = diff_format

class AddSubNode(ExprNode):
    def __init__(self, left=None, right=None, la_type=None, parse_info=None, raw_text=None, op='+-'):
        super().__init__(IRNodeType.AddSub, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
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
    def __init__(self, left=None, right=None, la_type=None, parse_info=None, raw_text=None, op=MulOpType.MulOpInvalid):
        super().__init__(IRNodeType.Mul, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right
        self.op = op


class DivOpType(Enum):
    DivOpInvalid = -1
    DivOpSlash = 0
    DivOpUnicode = 1


class DivNode(ExprNode):
    def __init__(self, left=None, right=None, la_type=None, parse_info=None, raw_text=None, op=DivOpType.DivOpSlash):
        super().__init__(IRNodeType.Div, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right
        self.op = op


class MatrixNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Matrix, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.items = None
        self.symbol = None
        self.value = None


class VectorNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Vector, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.items = []
        self.symbol = None


class SetNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Set, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.items = []
        self.symbol = None
        self.enum_list = None
        self.range = None
        self.cond = None
        self.f = None
        self.o = None
        self.scope_name = None

class EleConvertType(Enum):
    EleInvalid = -1
    EleToVertexSet = 0
    EleToEdgeSet = 1
    EleToFaceSet = 2
    EleToTetSet = 3
    EleToSimplicialSet = 4
    EleToTuple = 5
    EleToVertex = 6
    EleToEdge = 7
    EleToFace = 8
    EleToTet = 9
    EleToSequence = 10

class ElementConvertNode(ExprNode):
    def __init__(self, la_type=None, name=None, params=None, separators=None, to_type=EleConvertType.EleInvalid, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.ElementConvert, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.name = name
        self.params = params
        self.separators = separators
        self.to_type = to_type

class ToMatrixNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None, item=None):
        super().__init__(IRNodeType.ToMatrix, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.item = item

class ToDoubleValueNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None, item=None):
        super().__init__(IRNodeType.ToDouble, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.item = item


class MatrixRowsNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.MatrixRows, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.rs = None
        self.r = None


class MatrixRowNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.MatrixRow, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.rc = None
        self.exp = None


class MatrixRowCommasNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.MatrixRowCommas, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.value = None
        self.exp = None


class SummationNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Summation, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.sub = None
        self.exp = None
        self.id = None
        self.cond = None
        self.symbols = None
        self.symbol = None
        self.content = None
        self.sym_dict = {}  # identifiers containing sub, used for type checking only
        self.enum_list = None
        self.range = None
        self.extra_list = []
        self.tex_list = []    # extra assignments for tex output
        self.use_tuple = False
        self.scope_name = None
        self.lower = None
        self.upper = None
        self.sign = None
        self.sum_index_list = []  # variable subscripts used for sparse hessian


    def iter_mesh_ele(self):
        # check whether the summation is based on mesh elements: vertices, edges, faces, tets
        res = self.la_type.is_mesh_ele_set()
        return res

class UnionSequence(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.UnionSequence, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.sub = None
        self.exp = None
        self.id = None
        self.cond = None
        self.symbols = None
        self.symbol = None
        self.content = None
        self.sym_dict = {}  # identifiers containing sub, used for type checking only
        self.enum_list = None
        self.range = None
        self.extra_list = []
        self.tex_list = []    # extra assignments for tex output
        self.use_tuple = False
        self.scope_name = None
        self.lower = None
        self.upper = None

class OptimizeType(Enum):
    OptimizeInvalid = -1
    OptimizeMin = 0
    OptimizeMax = 1
    OptimizeArgmin = 2
    OptimizeArgmax = 3


class OptimizeNode(ExprNode):
    def __init__(self, opt_type=OptimizeType.OptimizeInvalid, cond_list=None, exp=None, base_list=None, base_type_list=None, la_type=None, parse_info=None, key='', init_list=None, init_syms=None, raw_text=None, def_list=None):
        super().__init__(IRNodeType.Optimize, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.opt_type = opt_type
        self.cond_list = cond_list
        self.exp = exp
        self.base_list = base_list
        self.base_type_list = base_type_list
        self.def_list = def_list   # ir node list
        self.key = key
        self.init_list = init_list
        self.init_syms = init_syms
        self.symbols = set()
        self.scope_name = None


class DomainNode(ExprNode):
    def __init__(self, lower=None, upper=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Domain, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.upper = upper
        self.lower = lower


class IntegralNode(ExprNode):
    def __init__(self, domain=None, exp=None, base=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Integral, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.domain = domain
        self.exp = exp
        self.base = base
        self.scope_name = None


class InnerProductNode(ExprNode):
    def __init__(self, left=None, right=None, sub=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.InnerProduct, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right
        self.sub = sub


class FroProductNode(ExprNode):
    def __init__(self, left=None, right=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.FroProduct, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right


class HadamardProductNode(ExprNode):
    def __init__(self, left=None, right=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.HadamardProduct, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right


class CrossProductNode(ExprNode):
    def __init__(self, left=None, right=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.CrossProduct, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right


class KroneckerProductNode(ExprNode):
    def __init__(self, left=None, right=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.KroneckerProduct, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.left = left
        self.right = right


class DotProductNode(ExprNode):
    def __init__(self, left=None, right=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.DotProduct, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
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
    NormSize = 6


class NormNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Norm, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.value = None
        self.sub = None
        self.norm_type = NormType.NormInvalid


class TransposeNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Transpose, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.f = None

class PseudoInverseNode(ExprNode):
    def __init__(self, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.PseudoInverse, parse_info=parse_info, raw_text=raw_text)
        self.f = None

class SquarerootNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Squareroot, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.value = None


class DivergenceNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None, value=None):
        super().__init__(IRNodeType.Divergence, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.value = value


class GradientNode(ExprNode):
    def __init__(self, la_type=None, sub=None, parse_info=None, raw_text=None, value=None):
        super().__init__(IRNodeType.Gradient, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.value = value
        self.sub = sub


class LaplaceNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None, value=None):
        super().__init__(IRNodeType.Laplace, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.value = value


class PowerNode(ExprNode):
    def __init__(self, base=None, power=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Power, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.base = base
        self.t = None
        self.r = None
        self.power = power


class SolverNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Solver, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.left = None
        self.right = None
        self.pow = None   # -> pow node


class OdeFirstOrderNode(ExprNode):
    def __init__(self, func=None, param=None, expr=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.OdeFirstOrder, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.func = func
        self.param = param
        self.expr = expr
        self.init_list = []


class MultiCondNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.MultiConds, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.ifs = None
        self.other = None
        self.lhs = None


class SparseMatrixNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.SparseMatrix, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.ifs = None
        self.other = None
        self.id2 = None
        self.id1 = None


class SparseIfNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.SparseIf, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
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
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.SparseIfs, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.cond_list = []
        self.in_cond_only = False

    def set_in_cond_only(self, value):
        self.in_cond_only = value
        if value:
            for cond in self.cond_list:
                cond.set_loop(True)


class SparseOtherNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.SparseOther, la_type=la_type, parse_info=parse_info, raw_text=raw_text)


class ExpInMatrixNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.ExpInMatrix, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.value = None
        self.sign = None


class NumMatrixNode(ExprNode):
    def __init__(self, id=None, id1=None, id2=None, left=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.NumMatrix, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.id = id
        self.id1 = id1
        self.id2 = id2
        self.left = left


class IndexNode(ExprNode):
    def __init__(self, node_type=IRNodeType.INVALID, la_type=None, parse_info=None, raw_text=None):
        super().__init__(node_type, la_type=la_type, parse_info=parse_info, raw_text=raw_text)

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

    def get_node_content(self, node):
        if node is None:
            content = '*'
        elif node.node_type == IRNodeType.Id:
            content = node.get_main_id()
        elif node.node_type == IRNodeType.Integer:
            content = node.value
        return content


class MatrixIndexNode(IndexNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.MatrixIndex, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.main = None
        self.row_index = None
        self.col_index = None
        self.subs = None

    def contain_subscript(self):
        return True

    def get_all_ids(self):
        return [self.main.get_main_id(), [self.get_node_content(self.row_index), self.get_node_content(self.col_index)]]

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
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.VectorIndex, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.main = None
        self.row_index = None
        self.dependence = None   # whether the rows depend on other symbol: a_i = b_i

    def contain_subscript(self):
        return True

    def get_all_ids(self):
        return [self.main.get_main_id(), [self.get_node_content(self.row_index)]]

    def get_main_id(self):
        return self.main.get_main_id()

    def contain_sub_sym(self, sym):
        if self.row_index and self.row_index.node_type == IRNodeType.Id and self.row_index.get_main_id() == sym:
            return True
        return False


class SetIndexNode(IndexNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.SetIndex, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.main = None
        self.row_index = None

    def contain_subscript(self):
        return True

    def get_all_ids(self):
        return [self.main.get_main_id(), [self.get_node_content(self.row_index)]]

    def get_main_id(self):
        return self.main.get_main_id()

    def contain_sub_sym(self, sym):
        if self.row_index and self.row_index.node_type == IRNodeType.Id and self.row_index.get_main_id() == sym:
            return True
        return False


class TupleIndexNode(IndexNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.TupleIndex, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
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
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.SequenceIndex, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.main = None
        self.main_index = None
        self.row_index = None
        self.col_index = None
        self.slice_matrix = False

    def contain_subscript(self):
        return True

    def get_all_ids(self):
        if self.row_index:
            return [self.main.get_main_id(), [self.get_node_content(self.main_index), self.get_node_content(self.row_index), self.get_node_content(self.col_index)]]
        else:
            return [self.main.get_main_id(), [self.get_node_content(self.main_index)]]

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
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.SeqDimIndex, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
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
    def __init__(self, value=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Subexpression, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.value = value


class ConstantType(Enum):
    ConstantInvalid = -1
    ConstantPi = 0
    ConstantE = 1
    ConstantInf = 2


class ConstantNode(ExprNode):
    def __init__(self, c_type=ConstantType.ConstantInvalid, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Constant, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.c_type = c_type


class DerivativeType(IntEnum):
    DerivativeInvalid = -1
    DerivativeFraction = 0   # dy/dt    ∂y/∂t
    DerivativeSFraction = 1  # d/dt y   ∂/∂t y
    DerivativePrime = 2      # y'
    DerivativeDot = 3        # ä


class PartialOrderType(IntEnum):
    PartialInvalid = -1
    PartialNormal = 0     # ∂y/∂t
    PartialHessian = 1    # ∂²y/∂t²


class DerivativeNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None, upper=None, lower=None, order=None, d_type=DerivativeType.DerivativeFraction):
        super().__init__(IRNodeType.Derivative, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.d_type = d_type
        self.upper = upper
        self.lower = lower
        self.order = order

    def get_signature(self, extra=None):
        if self.is_first_order():
            return "{}&{}".format(self.upper.raw_text, self.lower.raw_text)
        return self.raw_text

    def is_first_order(self):
        if self.order is None:
            return True
        if self.order.is_node(IRNodeType.Integer):
            return self.order.value == 1
        else:
            return self.order.raw_text == '1'
        
class HessianInfo(object):
     # mark hessian definitions
     def __init__(self, upper=None, lower=None, ir_node=None):
         self.upper = upper
         self.lower = lower
         self.ir_node = ir_node    # node ∂²y/∂s²


class PartialNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None, upper=None, lower_list=[], order=None, lorder_list=[], d_type=DerivativeType.DerivativeFraction, order_type=PartialOrderType.PartialNormal):
        super().__init__(IRNodeType.Partial, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.d_type = d_type
        self.upper = upper
        self.lower_list = lower_list
        self.lorder_list = lorder_list
        self.order = order
        self.order_type = order_type
        self.new_hessian_name = ''     # replace original content during visiting
        self.need_sparse = False

class SizeNode(ExprNode):
    def __init__(self, param=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Size, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.param = param

class ModuleNode(ExprNode):
    def __init__(self, value=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Module, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.value = value

class GeometryNode(StmtNode):
    def __init__(self, name=None, geometry=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Geometry, parse_info=parse_info, raw_text=raw_text)
        self.name = name
        self.geometry = geometry


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
    MathFuncMin = 30
    MathFuncMax = 31
    MathFuncInverseVec = 32
    MathFuncSVD = 33


class MathFuncNode(ExprNode):
    def __init__(self, param=None, func_type=MathFuncType.MathFuncInvalid, remain_params=[], func_name=None, separator=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.MathFunc, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.param = param   # first param
        self.remain_params = remain_params  # remain params
        self.func_type = func_type
        self.func_name = func_name
        self.separator = separator
        self.sub = None
        if param is not None:
            self.parse_info = param.parse_info

class GPFuncNode(ExprNode):
    def __init__(self, params=None, func_type=GPType.Invalid, func_name=None, identity_name=None, separator=None, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.GPFunction, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.params = params
        self.func_type = func_type
        self.func_name = func_name
        self.identity_name = identity_name
        self.separator = separator

class FactorNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Factor, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.op = None
        self.sub = None
        self.nm = None
        self.id = None
        self.num = None
        self.m = None
        self.v = None
        self.s = None
        self.size = None


class DoubleNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None):
        super().__init__(IRNodeType.Double, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.value = None


class FractionNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None, numerator=None, denominator=None):
        super().__init__(IRNodeType.Fraction, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.denominator = denominator
        self.numerator = numerator
        self.unicode = raw_text


class IntegerNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None, value=None):
        super().__init__(IRNodeType.Integer, la_type=ScalarType(is_int=True), parse_info=parse_info, raw_text=raw_text)
        self.value = value


class FuncFormat(IntEnum):
    FuncInvalid = -1
    FuncNormal = 0
    FuncShort = 1   # no parenthesis

class OrderFormat(IntEnum):
    OrderInvalid = -1
    OrderPrime = 0
    OrderDot = 1

class FunctionNode(ExprNode):
    def __init__(self, la_type=None, parse_info=None, raw_text=None, mode=FuncFormat.FuncNormal, order_mode=OrderFormat.OrderPrime, def_type=LocalFuncDefType.LocalFuncDefInvalid, identity_name=None):
        super().__init__(IRNodeType.Function, la_type=la_type, parse_info=parse_info, raw_text=raw_text)
        self.mode = mode
        self.params = []
        self.separators = []
        self.ret = None
        self.name = None
        self.order = None
        self.order_mode = order_mode
        self.n_subs = 0   # number of subscripts
        self.def_type = def_type
        self.identity_name = identity_name

    def get_signature(self, extra=None):
        if extra is None:
            extra = {}
        if self.order:
            if self.order == 1:
                if len(self.params) == 1:
                    return "{}&{}".format(self.name.get_main_id(), self.params[0].raw_text)
                else:
                    # no param
                    if "param" in extra:
                        return "{}&{}".format(self.name.get_main_id(), extra["param"])
            return self.name.get_main_id()
        return self.name.raw_text
    

def is_derivative_node(node):
    # whether the current node is a gradient or hessian node
    factor = node
    if factor.is_node(IRNodeType.Subexpression):
        factor = factor.value
    if factor.is_node(IRNodeType.Expression):
        factor = factor.value
    if factor.is_node(IRNodeType.Factor):
        if factor.op and (factor.op.is_node(IRNodeType.Gradient) or factor.op.is_node(IRNodeType.Derivative) or factor.op.is_node(IRNodeType.Partial)):
            return True
    return False