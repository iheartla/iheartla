from enum import Enum


class VarTypeEnum(Enum):
    INVALID = 0
    SEQUENCE = 1
    MATRIX = 2
    VECTOR = 3
    SCALAR = 4
    INTEGER = 5


class MatrixAttrEnum(Enum):
    SYMMETRIC = 1
    DIAGONAL = 2


class LaVarType(object):
    def __init__(self, var_type, dimensions=0, desc='', attrs=[], element_type='', element_subscript=[]):
        super().__init__()
        self.var_type = var_type
        self.dimensions = dimensions
        self.desc = desc
        self.attrs = attrs
        self.element_type = element_type
        self.element_subscript = element_subscript

