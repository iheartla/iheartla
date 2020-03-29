from tatsu.model import NodeWalker
from tatsu.objectmodel import Node
from la_parser.la_types import *


class WalkTypeEnum(Enum):
    RETRIEVE_EXPRESSION = 0  # default
    RETRIEVE_VAR = 1
    RETRIEVE_ROW_COUNTS = 2  # type_walker
    RETRIEVE_COL_COUNTS = 3  # type_walker


WALK_TYPE = "walk_type"
LHS = "left_hand_side"


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


def la_remove_key(key, **kwargs):
    if key in kwargs:
        del kwargs[key]


class TypeWalker(NodeWalker):
    def __init__(self):
        super().__init__()
        self.symtable = {}
        self.parameters = []
        self.subscripts = set()

    def walk_Node(self, node):
        print('Reached Node: ', node)

    def walk_object(self, o):
        raise Exception('Unexpected type %s walked', type(o).__name__)

    def walk_Start(self, node, **kwargs):
        self.walk(node.cond)
        self.walk(node.stat)

    ###################################################################
    def walk_WhereConditions(self, node, **kwargs):
        for cond in node.value:
            self.walk(cond)

    def walk_MatrixCondition(self, node, **kwargs):
        id0 = self.walk(node.id)
        id1 = self.walk(node.id1)
        id2 = self.walk(node.id2)
        element_type = ''
        if node.type:
            if node.type == 'ℝ':
                element_type = LaVarType(VarTypeEnum.SCALAR)
            elif node.type == 'ℕ':
                element_type = LaVarType(VarTypeEnum.INTEGER)
        self.symtable[id0] = LaVarType(VarTypeEnum.MATRIX, [id1, id2], desc=node.desc, element_type=element_type)
        self.handle_identifier(id0, self.symtable[id0])
        self.update_parameters(id0)
        if isinstance(id1, str):
            self.symtable[id1] = LaVarType(VarTypeEnum.INTEGER)
        if isinstance(id2, str):
            self.symtable[id2] = LaVarType(VarTypeEnum.INTEGER)

    def walk_VectorCondition(self, node, **kwargs):
        id0 = self.walk(node.id)
        id1 = self.walk(node.id1)
        element_type = ''
        if node.type:
            if node.type == 'ℝ':
                element_type = LaVarType(VarTypeEnum.SCALAR)
            elif node.type == 'ℕ':
                element_type = LaVarType(VarTypeEnum.INTEGER)
        self.symtable[id0] = LaVarType(VarTypeEnum.VECTOR, [id1], desc=node.desc, element_type=element_type)
        self.handle_identifier(id0, self.symtable[id0])
        self.update_parameters(id0)
        if isinstance(id1, str):
            self.symtable[id1] = LaVarType(VarTypeEnum.INTEGER)

    def walk_ScalarCondition(self, node, **kwargs):
        id0 = self.walk(node.id)
        self.symtable[id0] = LaVarType(VarTypeEnum.SCALAR, desc=node.desc)
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
            self.walk(stat)

    def walk_Add(self, node, **kwargs):
        left_type = self.walk(node.left)
        right_type = self.walk(node.right)
        assert left_type.var_type == right_type.var_type, 'error: walk_Add mismatch'
        return left_type

    def walk_Subtract(self, node, **kwargs):
        left_type = self.walk(node.left)
        right_type = self.walk(node.right)
        assert left_type.var_type == right_type.var_type, 'error: walk_Subtract mismatch'
        return left_type

    def walk_Multiply(self, node, **kwargs):
        left_type = self.walk(node.left)
        right_type = self.walk(node.right)
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
        left_type = self.walk(node.left)
        right_type = self.walk(node.right)
        assert (left_type.var_type == VarTypeEnum.SCALAR or left_type.var_type == VarTypeEnum.INTEGER), 'error: type mismatch'
        assert (right_type.var_type == VarTypeEnum.SCALAR or right_type.var_type == VarTypeEnum.INTEGER), 'error: type mismatch'
        return LaVarType(VarTypeEnum.SCALAR)

    def walk_Assignment(self, node, **kwargs):
        id0 = self.walk(node.left)
        right_type = self.walk(node.right)
        self.symtable[id0] = right_type
        return right_type

    def walk_Summation(self, node, **kwargs):
        return self.walk(node.exp)

    def walk_Determinant(self, node, **kwargs):
        return LaVarType(VarTypeEnum.SCALAR)

    def walk_IdentifierSubscript(self, node, **kwargs):
        right = []
        for value in node.right:
            right.append(self.walk(value))
        return self.walk(node.left) + '_' + ','.join(right)

    def walk_IdentifierAlone(self, node, **kwargs):
        return node.value

    def walk_Factor(self, node, **kwargs):
        if node.id:
            id0 = self.walk(node.id)
            assert self.symtable.get(id0) is not None, ("error: no symbol:{}".format(id0))
            return self.symtable[id0]
        elif node.num:
            return self.walk(node.num)
        elif node.sub:
            return self.walk(node.sub)
        elif node.m:
            return self.walk(node.m)
        elif node.f:
            return self.walk(node.f)
        elif node.op:
            return self.walk(node.op)

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
        return LaVarType(VarTypeEnum.MATRIX, dimensions=[rows, cols])

    def walk_MatrixRows(self, node, **kwargs):
        if la_need_ret_row_cnt(**kwargs):
            cnt = 0
            if node.r:
                cnt += len(node.r)
            if node.rs:
                for r in node.rs:
                    c = self.walk(r, **kwargs)
                    cnt += c
            return cnt
        elif la_need_ret_col_cnt(**kwargs):
            cnt = 0
            if node.r:
                for r in node.r:
                    c = self.walk(r, **kwargs)
                    if c > cnt:
                        cnt = c
            if node.rs:
                for r in node.rs:
                    c = self.walk(r, **kwargs)
                    if c > cnt:
                        cnt = c
            return cnt

    def walk_MatrixRow(self, node, **kwargs):
        if la_need_ret_col_cnt(**kwargs):
            cnt = 0
            if node.exp:
                cnt += len(node.exp)
            if node.rc:
                for rc in node.rc:
                    cnt += self.walk(rc, **kwargs)
            return cnt

    def walk_MatrixRowCommas(self, node, **kwargs):
        if la_need_ret_col_cnt(**kwargs):
            cnt = 0
            if node.exp:
                cnt += len(node.exp)
            if node.value:
                for value in node.value:
                    cnt += self.walk(value, **kwargs)
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
