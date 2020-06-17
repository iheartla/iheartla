from tatsu.model import NodeWalker
from tatsu.objectmodel import Node
from la_parser.la_types import *
from la_tools.la_logger import *
from la_parser.ir import *


class TypeInferenceEnum(Enum):
    INF_ADD = 0
    INF_SUB = 1
    INF_MUL = 2
    INF_DIV = 3
    INF_MATRIX_ROW = 4


class WalkTypeEnum(Enum):
    RETRIEVE_EXPRESSION = 0   # default
    RETRIEVE_VAR = 1


WALK_TYPE = "walk_type"
LHS = "left_hand_side"
ASSIGN_OP = "assign_op"
CUR_INDENT = "cur_indent"
INSIDE_MATRIX = "inside_matrix"
ASSIGN_TYPE = "assign_type"
INSIDE_SUMMATION = "inside_summation"
IF_COND = "if_condition"
SET_RET_SYMBOL = "set_ret_symbol"


def la_is_inside_matrix(**kwargs):
    if INSIDE_MATRIX in kwargs and kwargs[INSIDE_MATRIX] is True:
        return True
    return False


def la_is_inside_sum(**kwargs):
    if INSIDE_SUMMATION in kwargs and kwargs[INSIDE_SUMMATION] is True:
        return True
    return False


def la_remove_key(keys, **kwargs):
    if isinstance(keys, list):
        for key in keys:
            if key in kwargs:
                del kwargs[key]
    elif keys in kwargs:
        del kwargs[keys]


class TypeWalker(NodeWalker):
    def __init__(self):
        super().__init__()
        self.symtable = {}
        self.parameters = []
        self.subscripts = {}
        self.sub_name_dict = {}  # only for parameter checker
        self.node_dict = {}      # node:var_name
        self.name_cnt_dict = {}
        self.dim_dict = {}       # parameter used. h:w_i
        self.ids_dict = {}    # identifiers with subscripts
        self.logger = LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT)
        self.ret_symbol = None
        self.stat_list = None

    def generate_var_name(self, base):
        index = -1
        if base in self.name_cnt_dict:
            index = self.name_cnt_dict[base]
        index += 1
        valid = False
        ret = ""
        while not valid:
            ret = "_{}_{}".format(base, index)
            if ret not in self.symtable:
                valid = True
            index += 1
        self.name_cnt_dict[base] = index - 1
        return ret

    def walk_Node(self, node):
        print('Reached Node: ', node)

    def walk_object(self, o):
        raise Exception('Unexpected type %s walked', type(o).__name__)

    def walk_Start(self, node, **kwargs):
        self.walk(node.cond, **kwargs)
        self.stat_list = self.walk(node.stat, **kwargs)
        block_nodes = BlockNode()
        for index in range(len(self.stat_list)):
            update_ret_type = False
            if index == len(self.stat_list) - 1:
                if type(self.stat_list[index]).__name__ == 'Assignment':
                    kwargs[SET_RET_SYMBOL] = True
                else:
                    # new symbol for return value
                    self.ret_symbol = "ret"
                    update_ret_type = True
                    kwargs[LHS] = self.ret_symbol
            type_info = self.walk(self.stat_list[index], **kwargs)
            block_nodes.add_stmt(type_info.ir)
            if update_ret_type:
                self.symtable[self.ret_symbol] = type_info.la_type
        return block_nodes
        return self.stat_list

    ###################################################################
    def walk_WhereConditions(self, node, **kwargs):
        for cond in node.value:
            self.walk(cond, **kwargs)

    def walk_MatrixCondition(self, node, **kwargs):
        id0_info = self.walk(node.id, **kwargs)
        id0 = id0_info.content
        id1_info = self.walk(node.id1, **kwargs)
        id1 = id1_info.content
        id2_info = self.walk(node.id2, **kwargs)
        id2 = id2_info.content
        ret = node.text.split(':')
        desc = ':'.join(ret[1:len(ret)])
        element_type = ''
        if node.type:
            if node.type == 'ℝ':
                element_type = LaVarType(VarTypeEnum.REAL)
            elif node.type == 'ℤ':
                element_type = LaVarType(VarTypeEnum.INTEGER)
        la_type = MatrixType(rows=id1, cols=id2, desc=desc, element_type=element_type)
        self.handle_identifier(id0, la_type)
        self.update_parameters(id0)
        if isinstance(id1, str):
            self.symtable[id1] = LaVarType(VarTypeEnum.INTEGER)
            if self.contain_subscript(id0):
                self.dim_dict[id1] = [self.get_main_id(id0), 1]
            else:
                self.dim_dict[id1] = [self.get_main_id(id0), 0]
        if isinstance(id2, str):
            self.symtable[id2] = LaVarType(VarTypeEnum.INTEGER)
            if self.contain_subscript(id0):
                self.dim_dict[id2] = [self.get_main_id(id0), 2]
            else:
                self.dim_dict[id2] = [self.get_main_id(id0), 1]

    def walk_VectorCondition(self, node, **kwargs):
        id0_info = self.walk(node.id, **kwargs)
        id0 = id0_info.content
        id1_info = self.walk(node.id1, **kwargs)
        id1 = id1_info.content
        ret = node.text.split(':')
        desc = ':'.join(ret[1:len(ret)])
        element_type = ''
        if node.type:
            if node.type == 'ℝ':
                element_type = LaVarType(VarTypeEnum.REAL)
            elif node.type == 'ℤ':
                element_type = LaVarType(VarTypeEnum.INTEGER)
        la_type = VectorType(rows=id1, desc=desc, element_type=element_type)
        self.handle_identifier(id0, la_type)
        self.update_parameters(id0)
        if isinstance(id1, str):
            self.symtable[id1] = LaVarType(VarTypeEnum.INTEGER)
            self.dim_dict[id1] = [self.get_main_id(id0), 0]

    def walk_ScalarCondition(self, node, **kwargs):
        id0_info = self.walk(node.id, **kwargs)
        id0 = id0_info.content
        ret = node.text.split(':')
        desc = ':'.join(ret[1:len(ret)])
        la_type = LaVarType(VarTypeEnum.SCALAR, desc=desc)
        self.handle_identifier(id0, la_type)
        self.update_parameters(id0)

    def walk_SetCondition(self, node, **kwargs):
        id0_info = self.walk(node.id, **kwargs)
        id0 = id0_info.content
        ret = node.text.split(':')
        desc = ':'.join(ret[1:len(ret)])
        int_list = []
        cnt = 1
        if node.type:
            cnt = len(node.type)
            for t in node.type:
                if t == 'ℤ':
                    int_list.append(True)
                else:
                    int_list.append(False)
        elif node.type1:
            cnt_info = self.walk(node.cnt, **kwargs)
            if isinstance(cnt_info.content, int):
                cnt = cnt_info.content
            if node.type1 == 'ℤ':
                int_list = [True] * cnt
            else:
                int_list = [False] * cnt
        elif node.type2:
            cnt = 2
            if node.type2 == 'ℤ²':
                int_list = [True] * cnt
            else:
                int_list = [False] * cnt
        self.symtable[id0] = SetType(desc=desc, size=cnt, int_list=int_list)
        self.handle_identifier(id0, self.symtable[id0])
        self.update_parameters(id0)

    def update_parameters(self, identifier, **kwargs):
        if self.contain_subscript(identifier):
            arr = self.get_all_ids(identifier)
            self.parameters.append(arr[0])
        else:
            self.parameters.append(identifier)

    ###################################################################
    def walk_Statements(self, node, **kwargs):
        block_node = BlockNode()
        stat_list = []
        if node.stats:
            stat_list = self.walk(node.stats, **kwargs)
            block_node.add_stmt(stat_list)
        stat_list.append(node.stat)
        block_node.add_stmt(self.walk(node.stat, **kwargs).ir)
        return stat_list
        # return block_node

    def walk_Expression(self, node, **kwargs):
        value_info = self.walk(node.value, **kwargs)
        ir_node = ExpressionNode()
        value_info.ir.set_parent(ir_node)
        ir_node.la_type = value_info.la_type
        ir_node.value = value_info.ir
        ir_node.sign = node.sign
        value_info.ir = ir_node
        return value_info

    def walk_Add(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        left_type = left_info.la_type
        right_info = self.walk(node.right, **kwargs)
        right_type = right_info.la_type
        ret_type = self.type_inference(TypeInferenceEnum.INF_ADD, left_type, right_type)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node = AddNode(left_info.ir, right_info.ir)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        self.node_dict[node] = ret_info
        return ret_info

    def walk_Subtract(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        left_type = left_info.la_type
        right_info = self.walk(node.right, **kwargs)
        right_type = right_info.la_type
        ret_type = self.type_inference(TypeInferenceEnum.INF_SUB, left_type, right_type)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node = SubNode(left_info.ir, right_info.ir)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        self.node_dict[node] = ret_info
        return ret_info

    def walk_AddSub(self, node, **kwargs):
        assert IF_COND in kwargs, "must be used inside if codition"
        left_info = self.walk(node.left, **kwargs)
        left_type = left_info.la_type
        right_info = self.walk(node.right, **kwargs)
        right_type = right_info.la_type
        ret_type = self.type_inference(TypeInferenceEnum.INF_ADD, left_type, right_type)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node = AddSubNode(left_info.ir, right_info.ir)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        self.node_dict[node] = ret_info
        return ret_info

    def walk_Multiply(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        left_type = left_info.la_type
        right_info = self.walk(node.right, **kwargs)
        right_type = right_info.la_type
        ret_type = self.type_inference(TypeInferenceEnum.INF_MUL, left_type, right_type)
        sym_set = left_info.symbols.union(right_info.symbols)
        # I in block matrix
        if ret_type is not None:
            ret_type.symbol = ""
            for sym in sym_set:
                ret_type.symbol += sym
        ret_info = NodeInfo(ret_type, symbols=sym_set)
        ir_node = MulNode(left_info.ir, right_info.ir)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        self.node_dict[node] = ret_info
        return ret_info

    def walk_Divide(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        left_type = left_info.la_type
        right_info = self.walk(node.right, **kwargs)
        right_type = right_info.la_type
        ret_type = self.type_inference(TypeInferenceEnum.INF_DIV, left_type, right_type)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node = DivNode(left_info.ir, right_info.ir)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        self.node_dict[node] = ret_info
        return ret_info

    def walk_Subexpression(self, node, **kwargs):
        value_info = self.walk(node.value, **kwargs)
        ir_node = SubexpressionNode()
        ir_node.value = value_info.ir
        ir_node.la_type = value_info.la_type
        value_info.ir = ir_node
        return value_info

    def walk_Assignment(self, node, **kwargs):
        id0_info = self.walk(node.left, **kwargs)
        id0 = id0_info.content
        if SET_RET_SYMBOL in kwargs:
            self.ret_symbol = self.get_main_id(id0)
        kwargs[LHS] = id0
        kwargs[ASSIGN_OP] = node.op
        right_info = self.walk(node.right, **kwargs)
        right_type = right_info.la_type

        assign_node = AssignNode(id0_info.ir, right_info.ir)
        assign_node.op = node.op
        right_info.ir.set_parent(assign_node)
        id0_info.ir.set_parent(assign_node)


        la_remove_key(LHS, **kwargs)
        la_remove_key(ASSIGN_OP, **kwargs)
        # y_i = stat
        if self.contain_subscript(id0):
            left_ids = self.get_all_ids(id0)
            left_subs = left_ids[1]
            sequence = left_ids[0]    #y
            if node.op != '=':
                assert sequence in self.symtable, "lhs should exist"
            if len(left_subs) == 2: # matrix
                if right_info.la_type is not None and right_info.la_type.var_type == VarTypeEnum.MATRIX:
                    # sparse mat assign
                    if right_info.la_type.sparse:
                        self.symtable[sequence] = right_type
                if sequence not in self.symtable:
                    for symbol in right_info.symbols:
                        if left_subs[0] in symbol and left_subs[1] in symbol:
                            main_id = self.get_main_id(symbol)
                            rows = self.symtable[main_id].rows
                            cols = self.symtable[main_id].cols
                            break
                    self.symtable[sequence] = MatrixType(rows=rows, cols=cols, element_type=right_type)
            elif len(left_subs) == 1: # sequence
                for symbol in right_info.symbols:
                    if left_subs[0] in symbol:
                        main_id = self.get_main_id(symbol)
                        dim = self.symtable[main_id].size
                        break
                self.symtable[sequence] = SequenceType(size=dim, element_type=right_type)
        else:
            if node.op != '=':
                assert id0 in self.symtable, "lhs should exist"
            else:
                self.symtable[id0] = right_type
        self.node_dict[node] = right_info
        assign_node.symbols = right_info.symbols
        right_info.ir = assign_node
        return right_info

    def walk_Summation(self, node, **kwargs):
        kwargs[INSIDE_SUMMATION] = True
        #
        ir_node = SummationNode()
        if node.cond:
            id_info = self.walk(node.id, **kwargs)
            ir_node.id = id_info.ir
            ir_node.cond = self.walk(node.cond, **kwargs).ir
            id_info.ir.set_parent(ir_node)
            subs = id_info.content
            if LHS in kwargs:
                lhs = kwargs[LHS]
                lhs_ids = self.get_all_ids(lhs)
                assert lhs_ids[1][0] == lhs_ids[1][1], "multiple subscripts for sum"
                cond_info = self.walk(node.cond, **kwargs)
                cond_info.ir.set_parent(ir_node)
        else:
            sub_info = self.walk(node.sub)
            ir_node.sub = sub_info.ir
            sub_info.ir.set_parent(ir_node)
            subs = sub_info.content
        new_id = self.generate_var_name("sum")
        ret_info = self.walk(node.exp, **kwargs)
        ir_node.exp = ret_info.ir
        ret_info.ir.set_parent(ir_node)
        ret_type = ret_info.la_type
        self.symtable[new_id] = ret_type
        ret_info.symbol = new_id
        ret_info.content = subs
        ir_node.la_type = ret_info.la_type
        ir_node.symbols = ret_info.symbols
        ir_node.symbol = ret_info.symbol
        ir_node.content = ret_info.content
        ret_info.ir = ir_node
        self.node_dict[node] = ret_info
        return ret_info

    def walk_Determinant(self, node, **kwargs):
        value_info = self.walk(node.value, **kwargs)
        ret_type = LaVarType(VarTypeEnum.SCALAR)
        node_info = NodeInfo(ret_type, symbols=value_info.symbols)
        self.node_dict[node] = node_info
        return node_info

    def walk_Power(self, node, **kwargs):
        ir_node = PowerNode()
        base_info = self.walk(node.base, **kwargs)
        ir_node.base = base_info.ir
        symbols = base_info.symbols
        if node.t:
            ir_node.t = node.t
            assert base_info.la_type.var_type == VarTypeEnum.MATRIX
            node_type = MatrixType(rows=base_info.la_type.cols, cols=base_info.la_type.rows)
        elif node.r:
            ir_node.r = node.r
            assert base_info.la_type.var_type == VarTypeEnum.MATRIX
            assert base_info.la_type.rows == base_info.la_type.cols
            node_type = MatrixType(rows=base_info.la_type.rows, cols=base_info.la_type.rows)
        else:
            power_info = self.walk(node.power, **kwargs)
            ir_node.power = power_info.ir
            symbols += power_info.symbols
            node_type = power_info.la_type
        ir_node.la_type = node_type
        node_info = NodeInfo(node_type, symbols=symbols)
        node_info.ir = ir_node
        return node_info

    def walk_Solver(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ir_node = SolverNode()
        ir_node.left = left_info.ir
        ir_node.right = right_info.ir
        assert left_info.la_type.var_type == VarTypeEnum.MATRIX
        assert right_info.la_type.var_type == VarTypeEnum.MATRIX or right_info.la_type.var_type == VarTypeEnum.VECTOR
        node_type = None
        if left_info.la_type.var_type == VarTypeEnum.MATRIX:
            assert left_info.la_type.rows == right_info.la_type.rows
            if right_info.la_type.var_type == VarTypeEnum.MATRIX:
                node_type = MatrixType(rows=left_info.la_type.cols, cols=left_info.la_type.cols)
            elif right_info.la_type.var_type == VarTypeEnum.VECTOR:
                node_type = VectorType(rows=left_info.la_type.cols)
        ir_node.la_type = node_type
        node_info = NodeInfo(node_type, symbols=left_info.symbols.union(right_info.symbols))
        node_info.ir = ir_node
        return node_info

    def walk_Transpose(self, node, **kwargs):
        ir_node = TransposeNode()
        f_info = self.walk(node.f, **kwargs)
        ir_node.f = f_info.ir
        assert f_info.la_type.var_type == VarTypeEnum.MATRIX
        node_type = MatrixType(rows=f_info.la_type.cols, cols=f_info.la_type.rows)
        node_info = NodeInfo(node_type, symbols=f_info.symbols)
        node_info.ir = ir_node
        node_info.la_type = node_type
        return node_info

    def walk_IfCondition(self, node, **kwargs):
        ir_node = IfNode()
        kwargs[IF_COND] = True
        node_info = self.walk(node.cond, **kwargs)
        ir_node.cond = node_info.ir
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    def walk_NeCondition(self, node, **kwargs):
        ir_node = NeNode()
        left_info = self.walk(node.left, **kwargs)
        ir_node.left = left_info.ir
        left_type = left_info.la_type
        right_info = self.walk(node.right, **kwargs)
        ir_node.right = right_info.ir
        right_type = right_info.la_type
        assert left_type.var_type == right_type.var_type, "different type "
        ret_info = NodeInfo(left_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node.la_type = ret_info.la_type
        ret_info.ir = ir_node
        self.node_dict[node] = ret_info
        return ret_info

    def walk_EqCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        left_type = left_info.la_type
        right_info = self.walk(node.right, **kwargs)
        right_type = right_info.la_type
        assert left_type.var_type == right_type.var_type, "different type "
        ret_info = NodeInfo(left_type, symbols=left_info.symbols.union(right_info.symbols))
        self.node_dict[node] = ret_info
        return ret_info

    def walk_InCondition(self, node, **kwargs):
        return NodeInfo(VarTypeEnum.SCALAR)

    def walk_NotInCondition(self, node, **kwargs):
        return NodeInfo(VarTypeEnum.SCALAR)

    def walk_GreaterCondition(self, node, **kwargs):
        return NodeInfo(VarTypeEnum.SCALAR)

    def walk_GreaterEqualCondition(self, node, **kwargs):
        return NodeInfo(VarTypeEnum.SCALAR)

    def walk_LessCondition(self, node, **kwargs):
        return NodeInfo(VarTypeEnum.SCALAR)

    def walk_LessEqualCondition(self, node, **kwargs):
        return NodeInfo(VarTypeEnum.SCALAR)

    def walk_IdentifierSubscript(self, node, **kwargs):
        right = []
        for value in node.right:
            v_info = self.walk(value)
            right.append(v_info.content)
        left_info = self.walk(node.left, **kwargs)
        content = left_info.content + '_' + ''.join(right)
        node_type = LaVarType(VarTypeEnum.INVALID, symbol = content)
        if left_info.content in self.symtable:
            node_type = self.symtable[left_info.content].element_type
        #
        ir_node = IdNode(left_info.content, right)
        ir_node.la_type = node_type
        node_info = NodeInfo(node_type, content, {content}, ir_node)
        self.ids_dict[content] = Identifier(left_info.content, right)
        self.node_dict[node] = node_info
        return node_info

    def walk_IdentifierAlone(self, node, **kwargs):
        node_type = LaVarType(VarTypeEnum.INVALID)
        if node.value:
            value = node.value
        else:
            value = '`' + node.id + '`'
        #
        ir_node = IdNode(value)
        if value in self.symtable:
            node_type = self.symtable[value]
        node_type.symbol = value
        ir_node.la_type = node_type
        node_info = NodeInfo(node_type, value, {value}, ir_node)
        self.node_dict[node] = node_info
        return node_info

    def walk_Factor(self, node, **kwargs):
        node_info = None
        ir_node = FactorNode()
        if node.id:
            id0_info = self.walk(node.id, **kwargs)
            id0 = id0_info.content
            id0 = self.get_main_id(id0)
            if not la_is_inside_sum(**kwargs):  # symbols in sum don't need to be defined before
                if id0 != 'I':  # special case
                    assert self.symtable.get(id0) is not None, ("error: no symbol:{}".format(id0))
                else:
                    # I
                    if 'I' not in self.symtable:
                        assert la_is_inside_matrix(**kwargs), "I must be used inside matrix if not defined"
            node_info = NodeInfo(id0_info.la_type, id0, id0_info.symbols, id0_info.ir)
            # node_info = NodeInfo(self.symtable[id0], id0, id0_info.symbols)
            ir_node.id = node_info.ir
        elif node.num:
            node_info = self.walk(node.num, **kwargs)
            ir_node.num = node_info.ir
        elif node.sub:
            node_info = self.walk(node.sub, **kwargs)
            ir_node.sub = node_info.ir
        elif node.m:
            node_info = self.walk(node.m, **kwargs)
            ir_node.m = node_info.ir
        elif node.nm:
            node_info = self.walk(node.nm, **kwargs)
            ir_node.nm = node_info.ir
        elif node.op:
            node_info = self.walk(node.op, **kwargs)
            ir_node.op = node_info.ir
        elif node.s:
            node_info = self.walk(node.s, **kwargs)
            ir_node.s = node_info.ir
        #
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        self.node_dict[node] = node_info
        return node_info

    def walk_Number(self, node, **kwargs):
        node_value = self.walk(node.value, **kwargs)
        node_info = NodeInfo(LaVarType(VarTypeEnum.SCALAR), content=node_value)
        #
        ir_node = NumberNode()
        ir_node.value = node_value.ir
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        self.node_dict[node] = node_info
        return node_info

    def walk_Integer(self, node, **kwargs):
        value = ''.join(node.value)
        node_type = LaVarType(VarTypeEnum.INTEGER)
        node_info = NodeInfo(node_type, content=int(value))
        #
        ir_node = IntegerNode()
        ir_node.value = int(value)
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        self.node_dict[node] = node_info
        return node_info

    def walk_SparseMatrix(self, node, **kwargs):
        ir_node = SparseMatrixNode()
        if LHS in kwargs:
            lhs = kwargs[LHS]
        if ASSIGN_OP in kwargs:
            op = kwargs[ASSIGN_OP]
        all_ids = self.get_all_ids(lhs)

        ifs_info = self.walk(node.ifs, **kwargs)
        ifs_info.ir.set_parent(ir_node)
        ir_node.ifs = ifs_info.ir
        # definition
        index_var = self.generate_var_name("{}{}{}".format(all_ids[0], all_ids[1][0], all_ids[1][1]))
        value_var = self.generate_var_name("{}vals".format(all_ids[0]))
        if op == '=':  # require dims
            new_id = self.generate_var_name('sparse')
            id_name = new_id
            assert node.id1 and node.id2, "sparse matrix: need dim"
            id1_info = self.walk(node.id1, **kwargs)
            id1 = id1_info.content
            ir_node.id1 = id1_info.ir
            id2_info = self.walk(node.id2, **kwargs)
            id2 = id2_info.content
            ir_node.id2 = id2_info.ir
            la_type = MatrixType(rows=id1, cols=id2, sparse=True, index_var=index_var, value_var=value_var)
            self.symtable[new_id] = la_type
        elif op == '+=':
            assert all_ids[0] in self.symtable, "{} is not defined".format(all_ids[0])
            la_type = self.symtable[all_ids[0]]
            id_name = all_ids[0]
            if node.id1:
                id1_info = self.walk(node.id1, **kwargs)
                id1 = id1_info.content
                ir_node.id1 = id1_info.ir
                id2_info = self.walk(node.id2, **kwargs)
                id2 = id2_info.content
                ir_node.id2 = id2_info.ir
                assert id1 == la_type.rows and id2 == la_type.cols, "sparse matrix: dim mismatch"

        node_info = NodeInfo(la_type)
        node_info.symbol = id_name
        ir_node.la_type = la_type
        ir_node.symbol = node_info.symbol
        node_info.ir = ir_node
        self.node_dict[node] = node_info
        return node_info

    def walk_SparseIfs(self, node, **kwargs):
        ir_node = SparseIfsNode()
        if node.value:
            node_info = self.walk(node.value, **kwargs)
            node_info.ir.set_parent(ir_node)
            ir_node.value = node_info.ir
        if node.ifs:
            node_info = self.walk(node.ifs, **kwargs)
            node_info.ir.set_parent(ir_node)
            ir_node.ifs = node_info.ir
        ret_info = NodeInfo(ir=ir_node)
        return ret_info

    def walk_SparseIf(self, node, **kwargs):
        ir_node = SparseIfNode()
        lhs = kwargs[LHS]
        all_ids = self.get_all_ids(lhs)
        id0_info = self.walk(node.id0, **kwargs)
        ir_node.id0 = id0_info.ir
        id0 = id0_info.content
        assert id0 in all_ids[1], "subscripts mismatch"
        id1_info = self.walk(node.id1, **kwargs)
        ir_node.id1 = id1_info.ir
        id1 = id1_info.content
        assert id1 in all_ids[1], "subscripts mismatch"
        id2_info = self.walk(node.id2, **kwargs)
        ir_node.id2 = id2_info.ir
        id2 = id2_info.content
        stat_info = self.walk(node.stat, **kwargs)
        ir_node.stat = stat_info.ir
        for symbol in stat_info.symbols:
            if self.contain_subscript(symbol):
                sym_ids = self.get_all_ids(symbol)
                assert sym_ids[1] == all_ids[1], "subscripts mismatch"
        return NodeInfo(ir=ir_node)

    def walk_Matrix(self, node, **kwargs):
        ir_node = MatrixNode()
        kwargs[INSIDE_MATRIX] = True
        node_info = self.walk(node.value, **kwargs)
        ir_node.value = node_info.ir
        # check matrix validity
        rows = len(node_info.content)
        cols = 0
        block = False
        sparse = False
        for row in node_info.content:
            for col in row:
                if col.var_type == VarTypeEnum.MATRIX:
                    if col.sparse:
                        sparse = True
                    block = True
                elif col.var_type == VarTypeEnum.VECTOR:
                    block = True
            if len(row) > cols:
                cols = len(row)
        list_dim = None
        if block:
            # check block mat
            valid, undef_list, type_array, real_dims = self.check_bmat_validity(node_info.content, None)
            assert valid, "block matrix: invalid dimensions"
            rows = real_dims[0]
            cols = real_dims[1]
            if len(undef_list) > 0:
                # need change dimension
                list_dim = {}
                for i, j in undef_list:
                    list_dim[(i, j)] = [type_array[i][j].rows, type_array[i][j].cols]
        node_type = MatrixType(rows=rows, cols=cols, block=block, sparse=sparse, list_dim=list_dim, item_types=node_info.content)
        node_info = NodeInfo(node_type)
        if LHS in kwargs:
            lhs = kwargs[LHS]
            new_id = self.generate_var_name(lhs)
            self.symtable[new_id] = MatrixType(rows=rows, cols=cols, block=block, sparse=sparse, list_dim=list_dim, item_types=node_info.content)
            node_info.symbol = new_id
            self.node_dict[node] = node_info
        ir_node.la_type = node_info.la_type
        ir_node.symbol = node_info.symbol
        node_info.ir = ir_node
        self.node_dict[node] = node_info
        return node_info

    def walk_MatrixRows(self, node, **kwargs):
        ir_node = MatrixRowsNode()
        ret_info = None
        rows = []
        symbols = set()
        if node.rs:
            ret_info = self.walk(node.rs, **kwargs)
            ir_node.rs = ret_info.ir
            rows = rows + ret_info.content
            symbols = ret_info.symbols
        if node.r:
            r_info = self.walk(node.r, **kwargs)
            ir_node.r = r_info.ir
            if ret_info is None:
                ret_info = r_info
                ret_info.content = [ret_info.content]
            else:
                rows.append(r_info.content)
                ret_info.content = rows
            ret_info.symbols = symbols.union(r_info.symbols)
        ir_node.la_type = ret_info.la_type
        ret_info.ir = ir_node
        self.node_dict[node] = ret_info
        return ret_info

    def walk_MatrixRow(self, node, **kwargs):
        ir_node = MatrixRowNode()
        ret_info = None
        items = []
        symbols = set()
        if node.rc:
            ret_info = self.walk(node.rc, **kwargs)
            ir_node.rc = ret_info.ir
            items = items + ret_info.content
            symbols = ret_info.symbols
        if node.exp:
            exp_info = self.walk(node.exp, **kwargs)
            ir_node.exp = exp_info.ir
            if ret_info is None:
                ret_info = exp_info
                ret_info.content = [exp_info.la_type]
            else:
                new_type = self.type_inference(TypeInferenceEnum.INF_MATRIX_ROW, ret_info.la_type, exp_info.la_type)
                ret_info.la_type = new_type
                items.append(exp_info.la_type)
                ret_info.content = items
            ret_info.symbols = symbols.union(exp_info.symbols)
        ir_node.la_type = ret_info.la_type
        ret_info.ir = ir_node
        self.node_dict[node] = ret_info
        return ret_info

    def walk_MatrixRowCommas(self, node, **kwargs):
        ir_node = MatrixRowCommasNode()
        ret_info = None
        items = []
        symbols = set()
        if node.value:
            ret_info = self.walk(node.value, **kwargs)
            ir_node.value = ret_info.ir
            items = items + ret_info.content
            symbols = ret_info.symbols
        if node.exp:
            exp_info = self.walk(node.exp, **kwargs)
            ir_node.exp = exp_info.ir
            if ret_info is None:
                ret_info = exp_info
                ret_info.content = [exp_info.la_type]
            else:
                new_type = self.type_inference(TypeInferenceEnum.INF_MATRIX_ROW, ret_info.la_type, exp_info.la_type)
                ret_info.la_type = new_type
                items.append(exp_info.la_type)
                ret_info.content = items
            ret_info.symbols = symbols.union(exp_info.symbols)
        ir_node.la_type = ret_info.la_type
        ret_info.ir = ir_node
        self.node_dict[node] = ret_info
        return ret_info

    def walk_ExpInMatrix(self, node, **kwargs):
        ret_info = self.walk(node.value, **kwargs)
        ir_node = ExpInMatrixNode()
        ir_node.value = ret_info.ir
        ir_node.sign = node.sign
        ret_info.ir = ir_node
        self.node_dict[node] = ret_info
        return ret_info

    def walk_NumMatrix(self, node, **kwargs):
        ir_node = NumMatrixNode()
        id1_info = self.walk(node.id1, **kwargs)
        ir_node.id1 = id1_info.ir
        id1_info.ir.set_parent(ir_node)
        id1 = id1_info.content
        if isinstance(id1, str):
            assert id1 in self.symtable, "{} unknown".format(id1)
        if node.id:
            ir_node.id = node.id
            # 'I' symbol
            assert 'I' not in self.symtable, "You can't use 'I' with subscript since it has been defined before"
            node_type = MatrixType(rows=id1, cols=id1)
        else:
            ir_node.left = node.left
            if node.left == '0':
                assert la_is_inside_matrix(**kwargs), "Zero matrix can only be used inside matrix"
            if node.id2:
                id2_info = self.walk(node.id2, **kwargs)
                ir_node.id2 = id2_info.ir
                id2 = id2_info.content
                if isinstance(id2, str):
                    assert id2 in self.symtable, "{} unknown".format(id2)
                node_type = MatrixType(rows=id1, cols=id2)
            else:
                node_type = VectorType(rows=id1)
        node_info = NodeInfo(node_type)
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        self.node_dict[node] = node_type
        return node_info

    ###################################################################
    def check_bmat_validity(self, type_array, mat_size):
        """
        check the validity of block matrix
        :param type_array: 2d array containing element types
        :param mat_size: the dimensions of the block matrix may be given in future
        :return: valid, index to be changed, modified type_array, dims
        """
        valid = True
        rows = len(type_array)
        cols = len(type_array[0])
        row_dim = [None] * rows  # row numbers for mat in each row
        col_dim = [None] * cols  # col numbers for mat in each col
        undef_list = []          # scalar index, dimensions need to be changed
        identity_list = []       # identity matrix without dims
        # fill dim array, check mismatch
        for i in range(rows):
            for j in range(cols):
                if type_array[i][j].var_type == VarTypeEnum.MATRIX or type_array[i][j].var_type == VarTypeEnum.VECTOR:
                    if type_array[i][j].var_type == VarTypeEnum.MATRIX:
                        cur_cols = type_array[i][j].cols
                    else:
                        cur_cols = 1  # vector
                    if row_dim[i] is None:
                        row_dim[i] = type_array[i][j].rows
                    elif row_dim[i] != type_array[i][j].rows:
                        valid = False
                        break
                    if col_dim[j] is None:
                        col_dim[j] = cur_cols
                    elif col_dim[j] != cur_cols:
                        valid = False
                        break
                else:
                    if type_array[i][j].symbol is not None and 'I' in type_array[i][j].symbol:
                        if 'I' not in self.symtable:  # identity matrix
                            identity_list.append((i, j))
                    undef_list.append((i, j))
            if not valid:
                break
        # check Identity, fills dim if possible
        self.logger.debug("identity_list: {}".format(identity_list))
        if len(identity_list) > 0:
            for (i, j) in identity_list:
                if row_dim[i] is None:
                    if col_dim[j] is not None:
                        row_dim[i] = col_dim[j]
                else:
                    if col_dim[j] is None:
                        col_dim[j] = row_dim[i]
                    else:
                        if row_dim[i] != col_dim[j]:
                            valid = False
                            break
        self.logger.debug("undef_list: {}".format(undef_list))
        self.logger.debug("row_dim: {}".format(row_dim))
        self.logger.debug("col_dim: {}".format(col_dim))
        if len(undef_list) > 0:
            remain_list = []
            remain_row_set = set()
            remain_col_set = set()
            for (i, j) in undef_list:
                if row_dim[i] is not None and col_dim[j] is not None:
                    # modify dimensions
                    type_array[i][j] = MatrixType(rows=row_dim[i], cols=col_dim[j])
                else:
                    remain_list.append((i, j))
                    if row_dim[i] is None:
                        remain_row_set.add(i)
                    if col_dim[j] is None:
                        remain_col_set.add(j)
            if len(remain_list) > 0:
                self.logger.debug("remain_list: {}".format(remain_list))
                self.logger.debug("remain_row_set: {}".format(remain_row_set))
                self.logger.debug("remain_col_set: {}".format(remain_col_set))
                if mat_size is not None and len(remain_row_set) <= 1 and len(remain_col_set) <= 1:
                    if len(remain_row_set) == 1:
                        current_sum = 0
                        set_index = remain_row_set.pop()
                        for value in row_dim:
                            if value is not None:
                                current_sum += value
                        if mat_size[0] - current_sum <= 0:
                            valid = False
                        else:
                            row_dim[set_index] = mat_size[0] - current_sum
                    if len(remain_col_set) == 1:
                        current_sum = 0
                        set_index = remain_col_set.pop()
                        for value in col_dim:
                            if value is not None:
                                current_sum += value
                        if mat_size[1] - current_sum <= 0:
                            valid = False
                        else:
                            col_dim[set_index] = mat_size[1] - current_sum
                    # still valid
                    for (i, j) in remain_list:
                        type_array[i][j] = MatrixType(rows=row_dim[i], cols=col_dim[j])
                else:
                    valid = False
        # check total dimensions bound
        real_dims = (0, 0)
        if valid:
            row_sum = sum(row_dim)
            col_sum = sum(col_dim)
            real_dims = (row_sum, col_sum)
            if mat_size is not None:
                if row_sum != mat_size[0] or col_sum != mat_size[1]:
                    valid = False
        return valid, undef_list, type_array, real_dims

    def type_inference(self, op, left_type, right_type):
        # todo:delete
        if left_type.var_type == VarTypeEnum.INVALID:
            left_type.var_type = VarTypeEnum.SCALAR
        if right_type.var_type == VarTypeEnum.INVALID:
            right_type.var_type = VarTypeEnum.SCALAR
        #
        ret_type = None
        if op == TypeInferenceEnum.INF_ADD or op == TypeInferenceEnum.INF_SUB:
            assert left_type.var_type == right_type.var_type, 'left:{}, right:{}'.format(left_type.var_type, right_type.var_type)
            ret_type = left_type
            if left_type.var_type == VarTypeEnum.MATRIX:
                assert left_type.rows == right_type.rows and left_type.cols == right_type.cols, 'error: dimension mismatch'
                if left_type.sparse or right_type.sparse:
                    ret_type.sparse = True
            elif left_type.var_type == VarTypeEnum.VECTOR:
                assert left_type.rows == right_type.rows, 'error: dimension mismatch'
        elif op == TypeInferenceEnum.INF_MUL:
            assert left_type.var_type is not VarTypeEnum.SEQUENCE and right_type.var_type is not VarTypeEnum.SEQUENCE, 'error: sequence can not be operated'
            if left_type.var_type == VarTypeEnum.SCALAR:
                ret_type = right_type
            elif left_type.var_type == VarTypeEnum.INTEGER:
                ret_type = right_type
            elif left_type.var_type == VarTypeEnum.MATRIX:
                if right_type.var_type == VarTypeEnum.SCALAR:
                    ret_type = left_type
                if right_type.var_type == VarTypeEnum.INTEGER:
                    ret_type = left_type
                elif right_type.var_type == VarTypeEnum.MATRIX:
                    assert left_type.cols == right_type.rows, 'error: dimension mismatch'
                    ret_type = MatrixType(rows=left_type.rows, cols=right_type.cols)
                    if left_type.sparse and right_type.sparse:
                        ret_type.sparse = True
                elif right_type.var_type == VarTypeEnum.VECTOR:
                    assert left_type.cols == right_type.rows, 'error: dimension mismatch'
                    ret_type = VectorType(rows=left_type.rows)
            elif left_type.var_type == VarTypeEnum.VECTOR:
                if right_type.var_type == VarTypeEnum.SCALAR:
                    ret_type = left_type
                if right_type.var_type == VarTypeEnum.INTEGER:
                    ret_type = left_type
                elif right_type.var_type == VarTypeEnum.MATRIX:
                    assert 1 == right_type.rows, 'error: dimension mismatch'
                    ret_type = MatrixType(rows=left_type.rows, cols=right_type.cols)
                elif right_type.var_type == VarTypeEnum.VECTOR:
                    assert left_type.cols == right_type.rows, 'error: dimension mismatch'
        elif op == TypeInferenceEnum.INF_DIV:
            assert (left_type.var_type == VarTypeEnum.SCALAR or left_type.var_type == VarTypeEnum.INTEGER), 'error: type mismatch'
            assert (right_type.var_type == VarTypeEnum.SCALAR or right_type.var_type == VarTypeEnum.INTEGER), 'error: type mismatch'
            ret_type = LaVarType(VarTypeEnum.SCALAR)
        elif op == TypeInferenceEnum.INF_MATRIX_ROW:
            # assert left_type.var_type == right_type.var_type
            ret_type = left_type
        return ret_type

    def contain_subscript(self, identifier):
        if identifier in self.ids_dict:
            return self.ids_dict[identifier].contain_subscript()
        return False

    def get_all_ids(self, identifier):
        if identifier in self.ids_dict:
            return self.ids_dict[identifier].get_all_ids()
        res = identifier.split('_')
        subs = []
        for index in range(len(res[1])):
            subs.append(res[1][index])
        return [res[0], subs]

    def get_main_id(self, identifier):
        if identifier in self.ids_dict:
            return self.ids_dict[identifier].get_main_id()
        return identifier

    # handle subscripts only (where block)
    def handle_identifier(self, identifier, id_type):
        if self.contain_subscript(identifier):
            arr = self.get_all_ids(identifier)
            new_var_name = None
            for val in arr[1]:
                if val in self.sub_name_dict:
                    new_var_name = self.sub_name_dict[val]
                else:
                    new_var_name = self.generate_var_name("dim")
                    self.sub_name_dict[val] = new_var_name
                    self.dim_dict[new_var_name] = [arr[0], 0]
                if val in self.subscripts:
                    var_list = self.subscripts[val]
                    var_list.append(arr[0])
                    self.subscripts[val] = var_list
                else:
                    # first sequence
                    self.subscripts[val] = [arr[0]]
            self.symtable[arr[0]] = SequenceType(size=new_var_name, element_type=id_type, desc=id_type.desc, symbol=arr[0])
        else:
            id_type.symbol = identifier
            self.symtable[identifier] = id_type
