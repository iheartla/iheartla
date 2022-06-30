import copy
from tatsu.model import NodeWalker
from tatsu.objectmodel import Node
from .la_types import *
from ..la_tools.la_logger import *
from ..la_tools.la_msg import *
from ..la_tools.la_helper import *
import regex as re
from ..la_tools.la_helper import filter_subscript


class LightWalker(NodeWalker):
    def __init__(self):
        super().__init__()

    def walk_Node(self, node):
        pass

    def walk_object(self, o):
        pass

    def walk_Start(self, node, **kwargs):
        for vblock in node.vblock:
            self.walk(vblock, **kwargs)

    def walk_ParamsBlock(self, node, **kwargs):
        self.walk(node.conds, **kwargs)

    def walk_WhereConditions(self, node, **kwargs):
        for i in range(len(node.value)):
            self.walk(node.value[i], **kwargs)

    def walk_WhereCondition(self, node, **kwargs):
        self.walk(node.type, **kwargs)
        for id_index in range(len(node.id)):
            self.walk(node.id[id_index], **kwargs)

    def walk_MatrixType(self, node, **kwargs):
        self.walk(node.id1, **kwargs)
        self.walk(node.id2, **kwargs)

    def walk_VectorType(self, node, **kwargs):
        self.walk(node.id1, **kwargs)

    def walk_ScalarType(self, node, **kwargs):
        pass

    def walk_SetType(self, node, **kwargs):
        self.walk(node.cnt, **kwargs)

    def walk_FunctionType(self, node, **kwargs):
        if node.params:
            for index in range(len(node.params)):
                self.walk(node.params[index], **kwargs)
        for cur_index in range(len(node.ret)):
            self.walk(node.ret[cur_index], **kwargs)

    def walk_Import(self, node, **kwargs):
        pass

    def walk_Statements(self, node, **kwargs):
        if node.stats:
            self.walk(node.stats, **kwargs)

    def walk_Expression(self, node, **kwargs):
        self.walk(node.value, **kwargs)

    def walk_Add(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_Subtract(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_AddSub(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_Multiply(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_Divide(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_Subexpression(self, node, **kwargs):
        self.walk(node.value, **kwargs)

    def walk_LocalFunc(self, node, **kwargs):
        self.walk(node.name)
        if len(node.defs) > 0:
            for par_def in node.defs:
                self.walk(par_def, **kwargs)
        for cur_index in range(len(node.expr)):
            self.walk(node.expr[cur_index], **kwargs)
        for index in range(len(node.params)):
            self.walk(node.params[index], **kwargs)

    def walk_Assignment(self, node, **kwargs):
        if node.v:
            self.walk(node.v, **kwargs)
            self.walk(node.lexpr, **kwargs)
            self.walk(node.rexpr, **kwargs)
        else:
            for cur_index in range(len(node.left)):
                self.walk(node.left[cur_index], **kwargs)
                self.walk(node.right[cur_index], **kwargs)

    def walk_Summation(self, node, **kwargs):
        if node.cond:
            self.walk(node.id, **kwargs)
            self.walk(node.cond, **kwargs)
        else:
            if node.enum:
                for cur_id_raw in node.enum:
                    self.walk(cur_id_raw, **kwargs)
                self.walk(node.range, **kwargs)
            else:
                self.walk(node.sub, **kwargs)
        self.walk(node.exp, **kwargs)

    def walk_Optimize(self, node, **kwargs):
        if len(node.init) > 0:
            for cur_init in node.init:
                self.walk(cur_init, **kwargs)
        if len(node.defs) > 0:
            for par_def in node.defs:
                self.walk(par_def, **kwargs)
        self.walk(node.exp, **kwargs)
        if node.cond:
            self.walk(node.cond, **kwargs)

    def walk_MultiCond(self, node, **kwargs):
        if node.m_cond:
            self.walk(node.m_cond, **kwargs)
        self.walk(node.cond, **kwargs)

    def walk_Domain(self, node, **kwargs):
        self.walk(node.lower, **kwargs)
        self.walk(node.upper, **kwargs)

    def walk_Integral(self, node, **kwargs):
        self.walk(node.id, **kwargs)
        if node.d:
            self.walk(node.d, **kwargs)
        else:
            self.walk(node.lower, **kwargs)
            self.walk(node.upper, **kwargs)

    def walk_Norm(self, node, **kwargs):
        self.walk(node.value, **kwargs)
        if node.sub:
            if node.sub == '*':
                pass
            elif node.sub == '∞':
                pass
            else:
                self.walk(node.sub, **kwargs)
        if node.power:
            self.walk(node.power, **kwargs)

    def walk_InnerProduct(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)
        if node.sub:
            self.walk(node.sub, **kwargs)

    def walk_FroProduct(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_HadamardProduct(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_CrossProduct(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_KroneckerProduct(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_DotProduct(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_Derivative(self, node, **kwargs):
        pass

    def walk_Partial(self, node, **kwargs):
        pass

    def walk_Divergence(self, node, **kwargs):
        pass

    def walk_Gradient(self, node, **kwargs):
        pass

    def walk_Laplace(self, node, **kwargs):
        pass

    def walk_Power(self, node, **kwargs):
        self.walk(node.base, **kwargs)
        if node.t:
            pass
        elif node.r:
            pass
        else:
            self.walk(node.power, **kwargs)

    def walk_Solver(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_Transpose(self, node, **kwargs):
        self.walk(node.f, **kwargs)

    def walk_Squareroot(self, node, **kwargs):
        self.walk(node.f, **kwargs)

    def walk_Function(self, node, **kwargs):
        if isinstance(node.name, str):
            pass
        else:
            self.walk(node.name, **kwargs)
        for index in range(len(node.params)):
            self.walk(node.params[index], **kwargs)

    def walk_IfCondition(self, node, **kwargs):
        if node.single:
            self.walk(node.single, **kwargs)
        else:
            self.walk(node.se, **kwargs)
            self.walk(node.other, **kwargs)

    def walk_AndCondition(self, node, **kwargs):
        if node.atom:
            self.walk(node.atom, **kwargs)
        else:
            self.walk(node.se, **kwargs)
            self.walk(node.other, **kwargs)

    def walk_AtomCondition(self, node, **kwargs):
        if node.p:
            self.walk(node.p, **kwargs)
        else:
            self.walk(node.cond, **kwargs)

    def walk_InCondition(self, node, **kwargs):
        for item in node.left:
            self.walk(item, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_NotInCondition(self, node, **kwargs):
        for item in node.left:
            self.walk(item, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_NeCondition(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_EqCondition(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_GreaterCondition(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_GreaterEqualCondition(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_LessCondition(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_LessEqualCondition(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_IdentifierSubscript(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        for right in node.right:
            if right != '*':
                self.walk(right, **kwargs)

    def walk_IdentifierAlone(self, node, **kwargs):
        pass

    def walk_Factor(self, node, **kwargs):
        if node.id0:
            self.walk(node.id0, **kwargs)
        elif node.num:
            self.walk(node.num, **kwargs)
        elif node.sub:
            self.walk(node.sub, **kwargs)
        elif node.m:
            self.walk(node.m, **kwargs)
        elif node.v:
            self.walk(node.v, **kwargs)
        elif node.nm:
            self.walk(node.nm, **kwargs)
        elif node.op:
            self.walk(node.op, **kwargs)
        elif node.c:
            self.walk(node.c, **kwargs)

    def walk_Pi(self, node, **kwargs):
        pass

    def walk_E(self, node, **kwargs):
        pass

    def walk_Integer(self, node, **kwargs):
        pass

    def walk_SubInteger(self, node, **kwargs):
        pass

    def walk_SupInteger(self, node, **kwargs):
        pass

    def walk_Double(self, node, **kwargs):
        pass

    def walk_Fraction(self, node, **kwargs):
        pass

    def walk_Mantissa(self, node, **kwargs):
        pass

    def walk_Exponent(self, node, **kwargs):
        pass

    def walk_Float(self, node, **kwargs):
        pass

    def walk_MultiCondExpr(self, node, **kwargs):
        self.walk(node.ifs, **kwargs)
        if node.other:
            self.walk(node.other, **kwargs)

    def walk_MultiIfs(self, node, **kwargs):
        if node.ifs:
            self.walk(node.ifs, **kwargs)
        if node.value:
            self.walk(node.value, **kwargs)

    def walk_SingleIf(self, node, **kwargs):
        self.walk(node.cond, **kwargs)
        self.walk(node.stat, **kwargs)

    def walk_Vector(self, node, **kwargs):
        for exp in node.exp:
            self.walk(exp, **kwargs)

    def walk_Matrix(self, node, **kwargs):
        self.walk(node.value, **kwargs)

    def walk_MatrixRows(self, node, **kwargs):
        if node.rs:
            self.walk(node.rs, **kwargs)
        if node.r:
            self.walk(node.r, **kwargs)

    def walk_MatrixRow(self, node, **kwargs):
        if node.rc:
            self.walk(node.rc, **kwargs)
        if node.exp:
            self.walk(node.exp, **kwargs)

    def walk_MatrixRowCommas(self, node, **kwargs):
        if node.value:
            self.walk(node.value, **kwargs)
        if node.exp:
            self.walk(node.exp, **kwargs)

    def walk_ExpInMatrix(self, node, **kwargs):
        self.walk(node.value, **kwargs)

    def walk_NumMatrix(self, node, **kwargs):
        self.walk(node.id1, **kwargs)
        if node.id2:
            self.walk(node.id2, **kwargs)

    def walk_SinFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_AsinFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_CosFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_AcosFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_TanFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_AtanFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_SinhFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_AsinhFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_CoshFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_AcoshFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_TanhFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_AtanhFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_CotFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_SecFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_CscFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_Atan2Func(self, node, **kwargs):
        self.walk(node.param, **kwargs)
        self.walk(node.second, **kwargs)

    def walk_ExpFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_LogFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_LnFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_SqrtFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_TraceFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_DiagFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_VecFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_DetFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_RankFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_NullFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_OrthFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_InvFunc(self, node, **kwargs):
        self.walk(node.param, **kwargs)

    def walk_ArithExpression(self, node, **kwargs):
        self.walk(node.value, **kwargs)

    def walk_ArithSubexpression(self, node, **kwargs):
        self.walk(node.value, **kwargs)

    def walk_ArithAdd(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_ArithSubtract(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_ArithMultiply(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_ArithDivide(self, node, **kwargs):
        self.walk(node.left, **kwargs)
        self.walk(node.right, **kwargs)

    def walk_ArithFactor(self, node, **kwargs):
        if node.id0:
            if type(node.id0).__name__ == "IdentifierSubscript":
                self.walk(node.id0.left)
                self.walk(node.id0.right[0])
            else:
                self.walk(node.id0, **kwargs)
        elif node.num:
            self.walk(node.num, **kwargs)
        elif node.sub:
            self.walk(node.sub, **kwargs)


class SolverParamWalker(LightWalker):
    __instance = None

    @staticmethod
    def getInstance():
        if SolverParamWalker.__instance is None:
            SolverParamWalker()
        return SolverParamWalker.__instance

    def __init__(self):
        super().__init__()
        SolverParamWalker.__instance = self
        self.solved_func_params_dict = {}  # parameter list for solved function
        self.func_name = ''

    def walk_param(self, node, name, **kwargs):
        self.func_name = name
        self.solved_func_params_dict.clear()
        self.walk(node, **kwargs)
        return self.solved_func_params_dict
        
    def walk_Assignment(self, node, **kwargs):
        if node.v:
            self.walk(node.v, **kwargs)
            self.walk(node.lexpr, **kwargs)
            self.walk(node.rexpr, **kwargs)

    def walk_Function(self, node, **kwargs):
        if node.name == self.func_name:
            for index in range(len(node.params)):
                if index not in self.solved_func_params_dict:
                    self.solved_func_params_dict[index] = []
                if node.params[index].text not in self.solved_func_params_dict[index]:
                    self.solved_func_params_dict[index].append(node.params[index].text)

    def walk_Derivative(self, node, **kwargs):
        if node.upper.text == self.func_name:
            if 0 not in self.solved_func_params_dict:
                self.solved_func_params_dict[0] = []
            if node.lower.text not in self.solved_func_params_dict[0]:
                self.solved_func_params_dict[0].append(node.lower.text)
