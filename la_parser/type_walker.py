from tatsu.model import NodeWalker
from tatsu.objectmodel import Node
from la_parser.la_types import *


class WalkTypeEnum(Enum):
    RETRIEVE_EXPRESSION = 0   # default
    RETRIEVE_VAR = 1
    RETRIEVE_ROW_COUNTS = 2   # type_walker
    RETRIEVE_COL_COUNTS = 3   # type_walker
    RETRIEVE_MATRIX_STAT = 4  # code_walker: matrix statement


WALK_TYPE = "walk_type"
LHS = "left_hand_side"
CUR_INDENT = "cur_indent"


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
        assert left_type.var_type == right_type.var_type, 'error: walk_Add mismatch'
        return left_type

    def walk_Subtract(self, node, **kwargs):
        left_type = self.walk(node.left, **kwargs)
        right_type = self.walk(node.right, **kwargs)
        assert left_type.var_type == right_type.var_type, 'error: walk_Subtract mismatch'
        return left_type

    def walk_Multiply(self, node, **kwargs):
        left_type = self.walk(node.left, **kwargs)
        right_type = self.walk(node.right, **kwargs)
        assert left_type.var_type is not VarTypeEnum.SEQUENCE and right_type.var_type is not VarTypeEnum.SEQUENCE, 'error: sequence can not be operated'
        if left_type.var_type == VarTypeEnum.SCALAR:
            return right_type
        elif left_type.var_type == VarTypeEnum.INTEGER:
            return right_type
        elif left_type.var_type == VarTypeEnum.MATRIX:
            if right_type.var_type == VarTypeEnum.SCALAR:
                return left_type
            if right_type.var_type == VarTypeEnum.INTEGER:
                return left_type
            elif right_type.var_type == VarTypeEnum.MATRIX:
                assert left_type.dimensions[1] == right_type.dimensions[0], 'error: dimension mismatch'
                return LaVarType(VarTypeEnum.MATRIX, [left_type.dimensions[0], right_type.dimensions[1]])
            elif right_type.var_type == VarTypeEnum.VECTOR:
                assert left_type.dimensions[1] == right_type.dimensions[0], 'error: dimension mismatch'
                return LaVarType(VarTypeEnum.VECTOR, [left_type.dimensions[0]])
        elif left_type.var_type == VarTypeEnum.VECTOR:
            if right_type.var_type == VarTypeEnum.SCALAR:
                return left_type
            if right_type.var_type == VarTypeEnum.INTEGER:
                return left_type
            elif right_type.var_type == VarTypeEnum.MATRIX:
                assert 1 == right_type.dimensions[0], 'error: dimension mismatch'
                return LaVarType(VarTypeEnum.MATRIX, [left_type.dimensions[0], right_type.dimensions[1]])
            elif right_type.var_type == VarTypeEnum.VECTOR:
                assert left_type.dimensions[1] == right_type.dimensions[0], 'error: dimension mismatch'
                return LaVarType(VarTypeEnum.MATRIX, [left_type.dimensions[0]])
        return right_type

    def walk_Divide(self, node, **kwargs):
        left_type = self.walk(node.left, **kwargs)
        right_type = self.walk(node.right, **kwargs)
        assert (left_type.var_type == VarTypeEnum.SCALAR or left_type.var_type == VarTypeEnum.INTEGER), 'error: type mismatch'
        assert (right_type.var_type == VarTypeEnum.SCALAR or right_type.var_type == VarTypeEnum.INTEGER), 'error: type mismatch'
        return LaVarType(VarTypeEnum.SCALAR)

    def walk_Assignment(self, node, **kwargs):
        id0 = self.walk(node.left, **kwargs)
        kwargs[LHS] = id0
        self.matrix_index = 0
        right_type = self.walk(node.right, **kwargs)
        la_remove_key(LHS, **kwargs)
        self.symtable[id0] = right_type
        return right_type

    def walk_Summation(self, node, **kwargs):
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
        return LaVarType(VarTypeEnum.SCALAR)

    def walk_Integer(self, node, **kwargs):
        value = ''.join(node.value)
        return int(value)

    def walk_Matrix(self, node, **kwargs):
        kwargs[WALK_TYPE] = WalkTypeEnum.RETRIEVE_ROW_COUNTS
        rows = self.walk(node.value, **kwargs)
        kwargs[WALK_TYPE] = WalkTypeEnum.RETRIEVE_COL_COUNTS
        cols = self.walk(node.value, **kwargs)
        if LHS in kwargs:
            lhs = kwargs[LHS]
            new_id = "{}_{}".format(lhs, self.matrix_index)
            self.matrix_index += 1
            self.symtable[new_id] = LaVarType(VarTypeEnum.MATRIX, dimensions=[rows, cols])
            if lhs in self.m_dict:
                cnt = self.m_dict[lhs]
                self.m_dict[lhs] = cnt + 1
            else:
                self.m_dict[lhs] = 1
        return LaVarType(VarTypeEnum.MATRIX, dimensions=[rows, cols])

    def walk_MatrixRows(self, node, **kwargs):
        if la_need_ret_row_cnt(**kwargs):
            cnt = 0
            if node.r:
                cnt += 1
            if node.rs:
                c = self.walk(node.rs, **kwargs)
                cnt += c
            return cnt
        elif la_need_ret_col_cnt(**kwargs):
            cnt = 0
            if node.r:
                c = self.walk(node.r, **kwargs)
                if c > cnt:
                    cnt = c
            if node.rs:
                c = self.walk(node.rs, **kwargs)
                if c > cnt:
                    cnt = c
            return cnt

    def walk_MatrixRow(self, node, **kwargs):
        if la_need_ret_col_cnt(**kwargs):
            cnt = 0
            if node.exp:
                cnt += 1
            if node.rc:
                cnt += self.walk(node.rc, **kwargs)
            return cnt

    def walk_MatrixRowCommas(self, node, **kwargs):
        if la_need_ret_col_cnt(**kwargs):
            cnt = 0
            if node.exp:
                cnt += 1
            if node.value:
                cnt += self.walk(node.value, **kwargs)
            return cnt

    ###################################################################
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
