from enum import Enum


class VarTypeEnum(Enum):
    INVALID = 0
    SEQUENCE = 1
    MATRIX = 2
    VECTOR = 3
    SCALAR = 4
    INTEGER = 5
    REAL = 6


class MatrixAttrEnum(Enum):
    SYMMETRIC = 1
    DIAGONAL = 2


class LaVarType(object):
    def __init__(self, var_type, dimensions=0, desc=None, attrs=None, element_type=None, element_subscript=[]):
        super().__init__()
        self.var_type = var_type
        self.dimensions = dimensions
        self.desc = desc
        self.attrs = attrs
        self.element_type = element_type
        self.element_subscript = element_subscript


class MatrixAttrs(object):
    def __init__(self, need_exp=False, diagonal=False, sparse=False):
        super().__init__()
        self.need_exp = need_exp  # need expression
        self.diagonal = diagonal
        self.sparse = sparse


class SummationAttrs(object):
    def __init__(self, subs=None, var_list=None):
        super().__init__()
        self.subs = subs
        self.var_list = var_list


class NodeInfo(object):
    def __init__(self, la_type=None, content=None, symbols=[]):
        super().__init__()
        self.la_type = la_type
        self.content = content
        self.symbols = symbols  # symbols covered by the node


class CodeNodeInfo(object):
    def __init__(self, content=None, pre_list=[]):
        super().__init__()
        self.content = content
        self.pre_list = pre_list
