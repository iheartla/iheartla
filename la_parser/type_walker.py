from tatsu.model import NodeWalker
from tatsu.objectmodel import Node
from la_parser.la_types import *


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

    def walk_Start(self, node):
        self.walk(node.cond)
        self.walk(node.stat)

    ###################################################################
    def walk_WhereConditions(self, node):
        for cond in node.value:
            self.walk(cond)

    def walk_MatrixCondition(self, node):
        id0 = self.walk(node.id)
        id1 = self.walk(node.id1)
        id2 = self.walk(node.id2)
        self.symtable[id0] = LaVarType(VarTypeEnum.MATRIX, [id1, id2], desc=node.desc)
        self.handleIdentifier(id0, self.symtable[id0])
        self.update_parameters(id0)
        if isinstance(id1, str):
            self.symtable[id1] = LaVarType(VarTypeEnum.INTEGER)
        if isinstance(id2, str):
            self.symtable[id2] = LaVarType(VarTypeEnum.INTEGER)

    def walk_VectorCondition(self, node):
        id0 = self.walk(node.id)
        id1 = self.walk(node.id1)
        self.symtable[id0] = LaVarType(VarTypeEnum.VECTOR, id1, desc=node.desc)
        self.handleIdentifier(id0, self.symtable[id0])
        self.update_parameters(id0)
        if isinstance(id1, str):
            self.symtable[id1] = LaVarType(VarTypeEnum.INTEGER)

    def walk_ScalarCondition(self, node):
        id0 = self.walk(node.id)
        self.symtable[id0] = LaVarType(VarTypeEnum.SCALAR, desc=node.desc)
        self.handleIdentifier(id0, self.symtable[id0])
        self.update_parameters(id0)

    def update_parameters(self, identifier):
        if self.containSubscript(identifier):
            arr = self.getSubscripts(identifier)
            self.parameters.append(arr[0])
        else:
            self.parameters.append(identifier)

    ###################################################################
    def walk_Statements(self, node):
        for stat in node.value:
            self.walk(stat)

    def walk_Add(self, node):
        left_type = self.walk(node.left)
        right_type = self.walk(node.right)
        if left_type.var_type != right_type.var_type:
            print("error: walk_Add mismatch")
        return left_type

    def walk_Subtract(self, node):
        left_type = self.walk(node.left)
        right_type = self.walk(node.right)
        if left_type.var_type != right_type.var_type:
            print("error: walk_Subtract mismatch")
        return left_type

    def walk_Multiply(self, node):
        left_type = self.walk(node.left)
        right_type = self.walk(node.right)
        if left_type == VarTypeEnum.SCALAR:
            return right_type
        elif left_type == VarTypeEnum.MATRIX:
            pass
        elif left_type == VarTypeEnum.VECTOR:
            pass
        elif left_type == VarTypeEnum.SEQUENCE:
            pass
        return right_type

    def walk_Assignment(self, node):
        id0 = self.walk(node.left)
        right_type = self.walk(node.right)
        self.symtable[id0] = right_type
        return right_type

    def walk_Summation(self, node):
        return self.walk(node.exp)

    def walk_IdentifierSubscript(self, node):
        right = []
        for value in node.right:
            right.append(self.walk(value))
        return self.walk(node.left) + '_' + ','.join(right)

    def walk_IdentifierAlone(self, node):
        return node.value

    def walk_Factor(self, node):
        if node.id:
            id0 = self.walk(node.id)
            if self.symtable.get(id0) is None:
                print("error: no symbol" + id0)
            return self.symtable[id0]
        elif node.num:
            return self.walk(node.num)
        elif node.sub:
            return self.walk(node.sub)
        elif node.m:
            return self.walk(node.m)
        elif node.f:
            return self.walk(node.f)

    def walk_Number(self, node):
        return LaVarType(VarTypeEnum.SCALAR, desc=node.value)

    def walk_Integer(self, node):
        value = ''.join(node.value)
        return LaVarType(VarTypeEnum.INTEGER, desc=node.value)

    def walk_Matrix(self, node):
        return LaVarType(VarTypeEnum.MATRIX)

    def walk_MatrixRows(self, node):
        pass

    def walk_MatrixRow(self, node):
        pass

    def walk_MatrixRowCommas(self, node):
        pass
    ###################################################################
    def containSubscript(self, identifier):
        return identifier.find("_") != -1

    def getSubscripts(self, identifier):
        res = identifier.split('_')
        return [res[0], res[1].split(',')]

    def handleIdentifier(self, identifier, id_type):
        if self.containSubscript(identifier):
            arr = self.getSubscripts(identifier)
            self.symtable[arr[0]] = LaVarType(VarTypeEnum.SEQUENCE, dimensions=arr[1], element_type=id_type,
                                              desc=id_type.desc)
            for val in arr[1]:
                self.subscripts.add(val)
                if self.symtable.get(val) is None:
                    self.symtable[val] = LaVarType(VarTypeEnum.INTEGER)

