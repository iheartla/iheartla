from enum import Enum, IntEnum


class VarTypeEnum(Enum):
    INVALID = 0
    # LA types
    SEQUENCE = 1
    MATRIX = 2
    VECTOR = 3
    SET = 4
    SCALAR = 5
    FUNCTION = 6
    INDEX = 7


class LaVarType(object):
    def __init__(self, var_type, desc=None, element_type=None, symbol=None, index_type=False):
        super().__init__()
        self.var_type = var_type
        self.desc = desc   # only parameters need description
        self.element_type = element_type
        self.symbol = symbol
        self.index_type = index_type

    def is_integer_element(self):
        return False

    def is_dim_constant(self):
        constant = False
        if self.var_type == VarTypeEnum.SEQUENCE:
            if isinstance(self.size, int):
                constant = True
        elif self.var_type == VarTypeEnum.MATRIX:
            if isinstance(self.rows, int) and isinstance(self.cols, int):
                constant = True
        elif self.var_type == VarTypeEnum.VECTOR:
            if isinstance(self.rows, int):
                constant = True
        else:
            constant = True
        return constant

    def is_matrix(self):
        return self.var_type == VarTypeEnum.MATRIX

    def is_sequence(self):
        return self.var_type == VarTypeEnum.SEQUENCE

    def is_matrix_seq(self):
        return self.var_type == VarTypeEnum.SEQUENCE and self.element_type.is_matrix()

    def is_vector_seq(self):
        return self.var_type == VarTypeEnum.SEQUENCE and self.element_type.is_vector()

    def is_scalar_seq(self):
        return self.var_type == VarTypeEnum.SEQUENCE and self.element_type.is_scalar()

    def is_vector(self):
        return self.var_type == VarTypeEnum.VECTOR
        # return self.var_type == VarTypeEnum.VECTOR or (self.var_type == VarTypeEnum.MATRIX and self.cols == 1)

    def is_scalar(self):
        return self.var_type == VarTypeEnum.SCALAR

    def is_set(self):
        return self.var_type == VarTypeEnum.SET

    def is_function(self):
        return self.var_type == VarTypeEnum.FUNCTION

    def is_same_type(self, other):
        same = False
        if self.var_type == other.var_type:
            if self.var_type == VarTypeEnum.SEQUENCE:
                same = self.element_type.is_same_type(other.element_type.is_same_type)
            elif self.var_type == VarTypeEnum.MATRIX:
                same = self.rows == other.rows and self.cols == other.cols
            elif self.var_type == VarTypeEnum.VECTOR:
                same = self.rows == other.rows
            else:
                same = True
        return same

    def get_signature(self):
        return ''


class ScalarType(LaVarType):
    def __init__(self, is_int=False, desc=None, element_type=None, symbol=None, index_type=False, is_constant=False):
        LaVarType.__init__(self, VarTypeEnum.SCALAR, desc, element_type, symbol, index_type=index_type)
        self.is_int = is_int
        self.is_constant = is_constant  # constant number

    def get_signature(self):
        if self.is_int:
            return 'scalar:integer'
        return 'scalar:double'

    def is_integer_element(self):
        return self.is_int


class SequenceType(LaVarType):
    def __init__(self, size=0, desc=None, element_type=None, symbol=None):
        LaVarType.__init__(self, VarTypeEnum.SEQUENCE, desc, element_type, symbol)
        self.size = size

    def get_signature(self):
        return "sequence,ele_type:{}".format(self.element_type.get_signature())

    def is_integer_element(self):
        return self.element_type.is_integer_element()


class MatrixType(LaVarType):
    def __init__(self, rows=0, cols=0, desc=None, element_type=ScalarType(), symbol=None, need_exp=False, diagonal=False, sparse=False, block=False, subs=None, list_dim=None, index_var=None, value_var=None, item_types=None):
        LaVarType.__init__(self, VarTypeEnum.MATRIX, desc, element_type, symbol)
        self.rows = rows
        self.cols = cols
        # attributes
        self.need_exp = need_exp      # need expression
        self.diagonal = diagonal
        self.subs = subs or []
        # block matrix
        self.block = block
        self.list_dim = list_dim      # used by block mat
        self.item_types = item_types  # type array
        # sparse matrix
        self.sparse = sparse
        self.index_var = index_var    # used by sparse mat
        self.value_var = value_var    # used by sparse mat

    def get_signature(self):
        if self.element_type:
            return "matrix,rows:{},cols:{},ele_type:{}".format(self.rows, self.cols, self.element_type.get_signature())
        else:
            return "matrix,rows:{},cols:{}".format(self.rows, self.cols)

    def is_integer_element(self):
        return self.element_type.is_integer_element()


class VectorType(LaVarType):
    def __init__(self, rows=0, desc=None, element_type=ScalarType(), symbol=None):
        LaVarType.__init__(self, VarTypeEnum.VECTOR, desc, element_type, symbol)
        self.rows = rows
        self.cols = 1

    def get_signature(self):
        if self.element_type:
            return "vector,rows:{},ele_type:{}".format(self.rows, self.element_type.get_signature())
        else:
            return "vector,rows:{}".format(self.rows)

    def is_integer_element(self):
        return self.element_type.is_integer_element()


class SetType(LaVarType):
    def __init__(self, size=0, desc=None, element_type=None, symbol=None, int_list=None):
        LaVarType.__init__(self, VarTypeEnum.SET, desc, element_type, symbol)
        self.size = size
        self.int_list = int_list     # whether the element is real number or integer

    def get_signature(self):
        return 'set'

    def is_integer_element(self):
        for value in self.int_list:
            if not value:
                return False
        return True


class IndexType(LaVarType):
    def __init__(self, desc=None, symbol=None):
        LaVarType.__init__(self, VarTypeEnum.INDEX, desc, symbol)


class FunctionType(LaVarType):
    def __init__(self, desc=None, symbol=None, params=None, ret=None, template_symbols=None, ret_symbols=None):
        LaVarType.__init__(self, VarTypeEnum.FUNCTION, desc, symbol)
        self.params = params or []
        self.ret = ret
        self.template_symbols = template_symbols or {}  # symbol: index of params
        self.ret_symbols = ret_symbols or []

    def get_signature(self):
        signature = 'func,params:'
        for param in self.params:
            signature += param.get_signature() + ';'
        signature += 'ret:'+self.ret.get_signature()
        return signature

    def ret_template(self):
        return len(self.ret_symbols) > 0


class SummationAttrs(object):
    def __init__(self, subs=None, var_list=None):
        super().__init__()
        self.subs = subs
        self.var_list = var_list


class NodeInfo(object):
    def __init__(self, la_type=None, content=None, symbols=None, ir=None):
        super().__init__()
        self.la_type = la_type
        self.content = content
        self.symbols = symbols or set()  # symbols covered by the node
        self.ir = ir


class CodeNodeInfo(object):
    def __init__(self, content=None, pre_list=None):
        super().__init__()
        self.content = content
        self.pre_list = pre_list or []


class Identifier(object):
    def __init__(self, main_id='', subs=None):
        super().__init__()
        self.main_id = main_id
        self.subs = subs or []

    def contain_subscript(self):
        return len(self.subs) > 0

    def get_all_ids(self):
        return [self.main_id, self.subs]

    def get_main_id(self):
        return self.main_id