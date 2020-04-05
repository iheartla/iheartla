from tatsu.model import NodeWalker
from tatsu.objectmodel import Node
from la_parser.la_types import *


class TypeInferenceEnum(Enum):
    INF_ADD = 0
    INF_SUB = 1
    INF_MUL = 2
    INF_DIV = 3
    INF_MATRIX_ROW = 4


class WalkTypeEnum(Enum):
    RETRIEVE_EXPRESSION = 0   # default
    RETRIEVE_VAR = 1
    RETRIEVE_ROW_COUNTS = 2   # type_walker
    RETRIEVE_COL_COUNTS = 3   # type_walker
    RETRIEVE_MATRIX_STAT = 4  # code_walker: matrix statement


WALK_TYPE = "walk_type"
LHS = "left_hand_side"
CUR_INDENT = "cur_indent"
INSIDE_MATRIX = "inside_matrix"


def la_need_ret_vars(**kwargs):
    if WALK_TYPE in kwargs and kwargs[WALK_TYPE] == WalkTypeEnum.RETRIEVE_VAR:
        return True
    return False


def la_need_ret_row_cnt(**kwargs):
    if WALK_TYPE in kwargs and kwargs[WALK_TYPE] == WalkTypeEnum.RETRIEVE_ROW_COUNTS:
        return True
    return False


def la_need_ret_col_cnt(**kwargs):
    if WALK_TYPE in kwargs and kwargs[WALK_TYPE] == WalkTypeEnum.RETRIEVE_COL_COUNTS:
        return True
    return False


def la_need_ret_matrix(**kwargs):
    if WALK_TYPE in kwargs and kwargs[WALK_TYPE] == WalkTypeEnum.RETRIEVE_MATRIX_STAT:
        return True
    return False


def la_is_inside_matrix(**kwargs):
    if INSIDE_MATRIX in kwargs and kwargs[INSIDE_MATRIX] is True:
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
        self.subscripts = set()
        self.matrix_index = 0    # index of matrix in a single assignment statement
        self.m_dict = {}         # lhs:count
        self.node_dict = {}      # node:var_name
        self.name_cnt_dict = {}

    def generate_var_name(self, base):
        index = -1
        if base in self.name_cnt_dict:
            index = self.name_cnt_dict[base]
        index += 1
        self.name_cnt_dict[base] = index
        return "_{}_{}".format(base, index)

    def walk_Node(self, node):
        print('Reached Node: ', node)

    def walk_object(self, o):
        raise Exception('Unexpected type %s walked', type(o).__name__)

    def walk_Start(self, node, **kwargs):
        self.walk(node.cond, **kwargs)
        self.walk(node.stat, **kwargs)

    ###################################################################
    def walk_WhereConditions(self, node, **kwargs):
        for cond in node.value:
            self.walk(cond, **kwargs)

    def walk_MatrixCondition(self, node, **kwargs):
        id0 = self.walk(node.id, **kwargs)
        id1 = self.walk(node.id1, **kwargs)
        id2 = self.walk(node.id2, **kwargs)
        ret = node.text.split(':')
        desc = ':'.join(ret[1:len(ret)])
        element_type = ''
        if node.type:
            if node.type == 'ℝ':
                element_type = LaVarType(VarTypeEnum.REAL)
            elif node.type == 'ℤ':
                element_type = LaVarType(VarTypeEnum.INTEGER)
        self.symtable[id0] = LaVarType(VarTypeEnum.MATRIX, [id1, id2], desc=desc, element_type=element_type)
        self.handle_identifier(id0, self.symtable[id0])
        self.update_parameters(id0)
        if isinstance(id1, str):
            self.symtable[id1] = LaVarType(VarTypeEnum.INTEGER)
        if isinstance(id2, str):
            self.symtable[id2] = LaVarType(VarTypeEnum.INTEGER)

    def walk_VectorCondition(self, node, **kwargs):
        id0 = self.walk(node.id, **kwargs)
        id1 = self.walk(node.id1, **kwargs)
        ret = node.text.split(':')
        desc = ':'.join(ret[1:len(ret)])
        element_type = ''
        if node.type:
            if node.type == 'ℝ':
                element_type = LaVarType(VarTypeEnum.REAL)
            elif node.type == 'ℤ':
                element_type = LaVarType(VarTypeEnum.INTEGER)
        self.symtable[id0] = LaVarType(VarTypeEnum.VECTOR, [id1], desc=desc, element_type=element_type)
        self.handle_identifier(id0, self.symtable[id0])
        self.update_parameters(id0)
        if isinstance(id1, str):
            self.symtable[id1] = LaVarType(VarTypeEnum.INTEGER)

    def walk_ScalarCondition(self, node, **kwargs):
        id0 = self.walk(node.id, **kwargs)
        ret = node.text.split(':')
        desc = ':'.join(ret[1:len(ret)])
        self.symtable[id0] = LaVarType(VarTypeEnum.SCALAR, desc=desc)
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
        for stat in node.value:
            self.walk(stat, **kwargs)

    def walk_Add(self, node, **kwargs):
        left_type = self.walk(node.left, **kwargs)
        right_type = self.walk(node.right, **kwargs)
        ret_type = self.type_inference(TypeInferenceEnum.INF_ADD, left_type, right_type)
        return ret_type

    def walk_Subtract(self, node, **kwargs):
        left_type = self.walk(node.left, **kwargs)
        right_type = self.walk(node.right, **kwargs)
        ret_type = self.type_inference(TypeInferenceEnum.INF_SUB, left_type, right_type)
        return ret_type

    def walk_Multiply(self, node, **kwargs):
        left_type = self.walk(node.left, **kwargs)
        right_type = self.walk(node.right, **kwargs)
        ret_type = self.type_inference(TypeInferenceEnum.INF_MUL, left_type, right_type)
        return ret_type

    def walk_Divide(self, node, **kwargs):
        left_type = self.walk(node.left, **kwargs)
        right_type = self.walk(node.right, **kwargs)
        ret_type = self.type_inference(TypeInferenceEnum.INF_DIV, left_type, right_type)
        return ret_type

    def walk_Assignment(self, node, **kwargs):
        id0 = self.walk(node.left, **kwargs)
        kwargs[LHS] = id0
        self.matrix_index = 0
        right_type = self.walk(node.right, **kwargs)
        la_remove_key(LHS, **kwargs)
        self.symtable[id0] = right_type
        return right_type

    def walk_Summation(self, node, **kwargs):
        new_id = self.generate_var_name("sum")
        ret_type = self.walk(node.exp, **kwargs)
        self.symtable[new_id] = ret_type
        self.node_dict[node] = new_id
        return self.walk(node.exp, **kwargs)

    def walk_Determinant(self, node, **kwargs):
        return LaVarType(VarTypeEnum.SCALAR)

    def walk_IdentifierSubscript(self, node, **kwargs):
        right = []
        for value in node.right:
            right.append(self.walk(value), **kwargs)
        return self.walk(node.left, **kwargs) + '_' + ','.join(right)

    def walk_IdentifierAlone(self, node, **kwargs):
        return node.value

    def walk_Factor(self, node, **kwargs):
        if node.id:
            id0 = self.walk(node.id, **kwargs)
            assert self.symtable.get(id0) is not None, ("error: no symbol:{}".format(id0))
            if la_is_inside_matrix(**kwargs):
                return NodeInfo(self.symtable[id0], content=id0)
            else:
                return self.symtable[id0]
        elif node.num:
            return self.walk(node.num, **kwargs)
        elif node.sub:
            return self.walk(node.sub, **kwargs)
        elif node.m:
            return self.walk(node.m, **kwargs)
        elif node.f:
            return self.walk(node.f, **kwargs)
        elif node.op:
            return self.walk(node.op, **kwargs)

    def walk_Number(self, node, **kwargs):
        node_value = self.walk(node.value, **kwargs)
        ret = NodeInfo(LaVarType(VarTypeEnum.SCALAR), content=node_value)
        return ret

    def walk_Integer(self, node, **kwargs):
        value = ''.join(node.value)
        return int(value)

    def walk_Matrix(self, node, **kwargs):
        kwargs[INSIDE_MATRIX] = True
        node_info = self.walk(node.value, **kwargs)
        #check matrix validity
        rows = len(node_info.content)
        cols = 0
        for row in node_info.content:
            if len(row) > cols:
                cols = len(row)
        if LHS in kwargs:
            lhs = kwargs[LHS]
            new_id = self.generate_var_name(lhs)
            self.matrix_index += 1
            self.symtable[new_id] = LaVarType(VarTypeEnum.MATRIX, dimensions=[rows, cols])
            self.node_dict[node] = new_id
            if lhs in self.m_dict:
                cnt = self.m_dict[lhs]
                self.m_dict[lhs] = cnt + 1
            else:
                self.m_dict[lhs] = 1
        return LaVarType(VarTypeEnum.MATRIX, dimensions=[rows, cols])

    def walk_MatrixRows(self, node, **kwargs):
        ret_info = None
        rows = []
        if node.rs:
            ret_info = self.walk(node.rs, **kwargs)
            rows = rows + ret_info.content
        if node.r:
            r_info = self.walk(node.r, **kwargs)
            if ret_info is None:
                ret_info = r_info
                ret_info.content = [ret_info.content]
            else:
                rows.append(r_info.content)
                ret_info.content = rows
        return ret_info

    def walk_MatrixRow(self, node, **kwargs):
        ret_info = None
        items = []
        if node.rc:
            ret_info = self.walk(node.rc, **kwargs)
            items = items + ret_info.content
        if node.exp:
            exp_info = self.walk(node.exp, **kwargs)
            if ret_info is None:
                ret_info = exp_info
                ret_info.content = [ret_info.content]
            else:
                new_type = self.type_inference(TypeInferenceEnum.INF_MATRIX_ROW, ret_info.la_type, exp_info.la_type)
                ret_info.la_type = new_type
                items.append(exp_info.content)
                ret_info.content = items
        return ret_info

    def walk_MatrixRowCommas(self, node, **kwargs):
        ret_info = None
        items = []
        if node.value:
            ret_info = self.walk(node.value, **kwargs)
            items = items + ret_info.content
        if node.exp:
            exp_info = self.walk(node.exp, **kwargs)
            if ret_info is None:
                ret_info = exp_info
                ret_info.content = [ret_info.content]
            else:
                new_type = self.type_inference(TypeInferenceEnum.INF_MATRIX_ROW, ret_info.la_type, exp_info.la_type)
                ret_info.la_type = new_type
                items.append(exp_info.content)
                ret_info.content = items
        return ret_info

    def walk_ExpInMatrix(self, node, **kwargs):
        return self.walk(node.value, **kwargs)

    ###################################################################
    def type_inference(self, op, left_type, right_type):
        ret_type = None
        if op == TypeInferenceEnum.INF_ADD or op == TypeInferenceEnum.INF_SUB:
            assert left_type.var_type == right_type.var_type
            if left_type.var_type == VarTypeEnum.MATRIX:
                assert left_type.dimensions[0] == right_type.dimensions[0] and left_type.dimensions[1] == right_type.dimensions[1], 'error: dimension mismatch'
            elif left_type.var_type == VarTypeEnum.VECTOR:
                assert left_type.dimensions[0] == right_type.dimensions[0], 'error: dimension mismatch'
            ret_type = left_type
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
                    assert left_type.dimensions[1] == right_type.dimensions[0], 'error: dimension mismatch'
                    ret_type = LaVarType(VarTypeEnum.MATRIX, [left_type.dimensions[0], right_type.dimensions[1]])
                elif right_type.var_type == VarTypeEnum.VECTOR:
                    assert left_type.dimensions[1] == right_type.dimensions[0], 'error: dimension mismatch'
                    ret_type = LaVarType(VarTypeEnum.VECTOR, [left_type.dimensions[0]])
            elif left_type.var_type == VarTypeEnum.VECTOR:
                if right_type.var_type == VarTypeEnum.SCALAR:
                    ret_type = left_type
                if right_type.var_type == VarTypeEnum.INTEGER:
                    ret_type = left_type
                elif right_type.var_type == VarTypeEnum.MATRIX:
                    assert 1 == right_type.dimensions[0], 'error: dimension mismatch'
                    ret_type = LaVarType(VarTypeEnum.MATRIX, [left_type.dimensions[0], right_type.dimensions[1]])
                elif right_type.var_type == VarTypeEnum.VECTOR:
                    assert left_type.dimensions[1] == right_type.dimensions[0], 'error: dimension mismatch'
                    ret_type = LaVarType(VarTypeEnum.MATRIX, [left_type.dimensions[0]])
        elif op == TypeInferenceEnum.INF_DIV:
            assert (left_type.var_type == VarTypeEnum.SCALAR or left_type.var_type == VarTypeEnum.INTEGER), 'error: type mismatch'
            assert (right_type.var_type == VarTypeEnum.SCALAR or right_type.var_type == VarTypeEnum.INTEGER), 'error: type mismatch'
            ret_type = LaVarType(VarTypeEnum.SCALAR)
        elif op == TypeInferenceEnum.INF_MATRIX_ROW:
            assert left_type.var_type == right_type.var_type
            ret_type = left_type
        return ret_type

    def contain_subscript(self, identifier):
        return identifier.find("_") != -1

    def get_all_ids(self, identifier):
        res = identifier.split('_')
        return [res[0], res[1].split(',')]

    def handle_identifier(self, identifier, id_type):
        if self.contain_subscript(identifier):
            arr = self.get_all_ids(identifier)
            self.symtable[arr[0]] = LaVarType(VarTypeEnum.SEQUENCE, dimensions=arr[1], element_type=id_type,
                                              desc=id_type.desc)
            for val in arr[1]:
                self.subscripts.add(val)
                if self.symtable.get(val) is None:
                    self.symtable[val] = LaVarType(VarTypeEnum.INTEGER)
