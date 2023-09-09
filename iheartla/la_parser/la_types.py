import copy
from enum import Enum, IntEnum, IntFlag


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
    MAPPING = 8
    TUPLE = 9
    OVERLOADINGFUNCTION = 10
    VERTEXTYPE = 11
    EDGETYPE = 12
    FACETYPE = 13
    TETTYPE = 14
    MESH = 15


class DynamicTypeEnum(IntFlag):
    DYN_INVALID = 0
    DYN_ROW = 1
    DYN_COL = 2
    DYN_DIM = 4

class SetTypeEnum(Enum):
    DEFAULT = 0
    # LA types
    VERTEX = 1
    EDGE = 2
    FACE = 3
    TET = 4

class LaVarType(object):
    def __init__(self, var_type=VarTypeEnum.INVALID, desc=None, element_type=None, symbol=None, index_type=False, dynamic=DynamicTypeEnum.DYN_INVALID, owner=None):
        super().__init__()
        self.var_type = var_type if var_type else VarTypeEnum.INVALID
        self.desc = desc   # only parameters need description
        self.element_type = element_type
        self.symbol = symbol
        self.index_type = index_type
        self.dynamic = dynamic  # related to type inference, no need to check if True
        self.owner = owner  # track mesh element
        if self.element_type and (self.owner and self.element_type.owner is None):
            # set owner for element type
            self.element_type.owner = self.owner

    def is_valid(self):
        return self.var_type != VarTypeEnum.INVALID

    def is_integer_element(self):
        return False

    def set_int(self, value):
        if self.element_type:
            self.element_type.set_int(value)
        else:
            self.is_int = value

    def is_dynamic(self):
        return self.dynamic != DynamicTypeEnum.DYN_INVALID

    def is_dynamic_row(self):
        return self.dynamic & DynamicTypeEnum.DYN_ROW

    def is_dynamic_col(self):
        return self.dynamic & DynamicTypeEnum.DYN_COL

    def is_dynamic_dim(self):
        return self.dynamic & DynamicTypeEnum.DYN_DIM

    def replace_sym_dims(self, mapping_dict):
        if self.owner and self.owner in mapping_dict:
            # mesh
            self.owner = mapping_dict[self.owner]
        if self.element_type:
            self.element_type.replace_sym_dims(mapping_dict)

    def set_dynamic_type(self, dynamic_type):
        self.dynamic = dynamic_type

    def add_dynamic_type(self, dynamic_type):
        if dynamic_type == DynamicTypeEnum.DYN_INVALID:
            self.dynamic = dynamic_type
        else:
            self.dynamic |= dynamic_type

    def get_dim_size(self, dim_index):
        dim_size = 0
        if self.var_type == VarTypeEnum.SEQUENCE:
            if dim_index == 0:
                dim_size = self.size
            else:
                dim_size = self.element_type.get_dim_size(dim_index-1)
        elif self.var_type == VarTypeEnum.MATRIX:
            if dim_index == 0:
                dim_size = self.rows
            else:
                dim_size = self.cols
        elif self.var_type == VarTypeEnum.VECTOR:
            if dim_index == 0:
                dim_size = self.rows
        return dim_size

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

    def is_sparse_matrix(self):
        return self.var_type == VarTypeEnum.MATRIX and self.sparse

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
        return self.var_type == VarTypeEnum.SCALAR or self.var_type == VarTypeEnum.VERTEXTYPE \
               or self.var_type == VarTypeEnum.EDGETYPE or self.var_type == VarTypeEnum.FACETYPE or self.var_type == VarTypeEnum.TETTYPE

    def is_mapping(self):
        return self.var_type == VarTypeEnum.MAPPING

    def is_int_scalar(self):
        return self.var_type == VarTypeEnum.SCALAR and self.is_integer_element()

    def is_set(self):
        return self.var_type == VarTypeEnum.SET

    def is_mesh_element_set(self):
        return self.is_vertex_set() or self.is_edge_set() or self.is_face_set() or self.is_tet_set()

    def is_vertex_type(self):
        return self.is_scalar() and self.cur_type == SetTypeEnum.VERTEX

    def is_edge_type(self):
        return self.is_scalar() and self.cur_type == SetTypeEnum.EDGE

    def is_face_type(self):
        return self.is_scalar() and self.cur_type == SetTypeEnum.FACE

    def is_tet_type(self):
        return self.is_scalar() and self.cur_type == SetTypeEnum.TET

    def is_vertex_set(self):
        return self.is_set() and self.cur_type == SetTypeEnum.VERTEX

    def is_edge_set(self):
        return self.is_set() and self.cur_type == SetTypeEnum.EDGE

    def is_face_set(self):
        return self.is_set() and self.cur_type == SetTypeEnum.FACE

    def is_tet_set(self):
        return self.is_set() and self.cur_type == SetTypeEnum.TET
    
    def is_mesh_ele_set(self):
        return self.is_set() and (self.cur_type == SetTypeEnum.VERTEX or self.cur_type == SetTypeEnum.EDGE or self.cur_type == SetTypeEnum.FACE or self.cur_type == SetTypeEnum.TET)

    def is_tuple(self):
        return self.var_type == VarTypeEnum.TUPLE

    def is_function(self):
        return self.var_type == VarTypeEnum.FUNCTION or self.var_type == VarTypeEnum.OVERLOADINGFUNCTION

    def is_overloaded(self):
        return self.var_type == VarTypeEnum.OVERLOADINGFUNCTION

    def is_mesh(self):
        return self.var_type == VarTypeEnum.MESH

    def is_same_type(self, other, omit_size=False):
        # not consider whether the element is int or not
        same = False
        if self.var_type == other.var_type:
            if self.var_type == VarTypeEnum.SEQUENCE:
                if omit_size:
                    same = self.element_type.is_same_type(other.element_type)
                else:
                    same = self.size == other.size and self.element_type.is_same_type(other.element_type)
            elif self.var_type == VarTypeEnum.MATRIX:
                if omit_size:
                    same = self.element_type.is_same_type(other.element_type)
                else:
                    same = self.rows == other.rows and self.cols == other.cols and self.element_type.is_same_type(other.element_type)
            elif self.var_type == VarTypeEnum.VECTOR:
                if omit_size:
                    same = self.rows == other.rows and self.element_type.is_same_type(other.element_type)
                else:
                    same = self.rows == other.rows
            elif self.var_type == VarTypeEnum.SET:
                same = self.cur_type == other.cur_type
            elif self.var_type == VarTypeEnum.SCALAR:
                same = self.cur_type == other.cur_type
            else:
                same = True
        return same

    def get_signature(self):
        # signature for iheartla types, as long as it can be used to differentiate
        return ''

    def get_relaxed_signature(self):
        # for matrix/vector, try to omit 0 dimensions
        return self.get_signature()
    def get_cpp_signature(self):
        # some different types in iheartla corresponding to the same types in Eigen, e.g.: ℤ^3 v.s. ℤ^(3×1)
        return self.get_signature()

    def get_json_content(self):
        return ''

    def get_raw_text(self):
        return ''


class ScalarType(LaVarType):
    def __init__(self, is_int=False, desc=None, element_type=None, symbol=None, index_type=False, is_constant=False, dynamic=DynamicTypeEnum.DYN_INVALID, cur_type=SetTypeEnum.DEFAULT, owner=None):
        LaVarType.__init__(self, VarTypeEnum.SCALAR, desc, element_type, symbol, index_type=index_type, dynamic=dynamic, owner=owner)
        self.is_int = is_int
        self.is_constant = is_constant  # constant number
        self.cur_type = cur_type

    def get_signature(self):
        # if self.is_int:
        #     return 'scalar:integer'
        # return 'scalar:double'
        return self.get_raw_text()

    def is_integer_element(self):
        return self.is_int

    def get_json_content(self):
        return """{{"type": "scalar", "is_int":"{}"}}""".format(self.is_integer_element())

    def get_raw_text(self):
        return 'ℤ' if self.is_int else 'ℝ'

class IntType(ScalarType):
    def __init__(self, owner=None):
        ScalarType.__init__(self, is_int=True, owner=owner)

    def get_raw_text(self):
        return 'ℤ'

class VertexType(ScalarType):
    def __init__(self, owner=None):
        ScalarType.__init__(self, is_int=True, index_type=True, cur_type=SetTypeEnum.VERTEX, owner=owner)
        # self.var_type = VarTypeEnum.VERTEXTYPE

    def get_raw_text(self):
        return 'v:ℤ'

    def get_cpp_signature(self):
        return 'ℤ'

class EdgeType(ScalarType):
    def __init__(self, owner=None):
        ScalarType.__init__(self, is_int=True, index_type=True, cur_type=SetTypeEnum.EDGE, owner=owner)
        # self.var_type = VarTypeEnum.EDGETYPE

    def get_raw_text(self):
        return 'e:ℤ'

    def get_cpp_signature(self):
        return 'ℤ'

class FaceType(ScalarType):
    def __init__(self, owner=None):
        ScalarType.__init__(self, is_int=True, index_type=True, cur_type=SetTypeEnum.FACE, owner=owner)
        # self.var_type = VarTypeEnum.FACETYPE

    def get_raw_text(self):
        return 'f:ℤ'

    def get_cpp_signature(self):
        return 'ℤ'

class TetType(ScalarType):
    def __init__(self, owner=None):
        ScalarType.__init__(self, is_int=True, index_type=True, cur_type=SetTypeEnum.TET, owner=owner)
        # self.var_type = VarTypeEnum.TETTYPE

    def get_raw_text(self):
        return 't:ℤ'

    def get_cpp_signature(self):
        return 'ℤ'
    
class MeshTypeEnum(Enum):
    DEFAULT = 0
    TRIANGLE = 1
    POINTCLOUD = 2
    POLYGON = 3
    TETRAHEDRON = 4
    POLYHEDRON = 5
    EdgeMesh = 6
    FaceMesh = 7
    CellMesh = 8


class MeshType(LaVarType):
    def __init__(self, dim_dict=None, desc=None, owner=None, cur_mesh=MeshTypeEnum.TRIANGLE):
        LaVarType.__init__(self, VarTypeEnum.MESH, desc=desc, owner=owner)
        self.init_dims(dim_dict)
        self.cur_mesh = cur_mesh

    def init_dims(self, dim_dict=None):
        self.vi_size = dim_dict['vi_size'] if dim_dict and 'vi_size' in dim_dict else 0
        self.ei_size = dim_dict['ei_size'] if dim_dict and 'ei_size' in dim_dict else 0
        self.fi_size = dim_dict['fi_size'] if dim_dict and 'fi_size' in dim_dict else 0
        self.ti_size = dim_dict['ti_size'] if dim_dict and 'ti_size' in dim_dict else 0

    def get_raw_text(self):
        return 'mesh({},{},{},{})'.format(self.vi_size, self.ei_size, self.fi_size, self.ti_size)

    def get_relaxed_signature(self):
        return 'mesh()'

    def get_signature(self):
        return self.get_raw_text()

class SequenceType(LaVarType):
    def __init__(self, size=0, check_dim=True, desc=None, element_type=None, symbol=None, dynamic=False, owner=None):
        LaVarType.__init__(self, VarTypeEnum.SEQUENCE, desc, element_type, symbol, dynamic=dynamic, owner=owner)
        self.size = size
        self.check_dim = check_dim    # whether output assertion for dim checking

    def get_signature(self):
        return "sequence of {}".format(self.element_type.get_signature())

    def is_integer_element(self):
        return self.element_type.is_integer_element()

    def is_dynamic(self):
        return self.element_type.is_dynamic()

    def replace_sym_dims(self, mapping_dict):
        super(SequenceType, self).replace_sym_dims(mapping_dict)
        self.element_type.replace_sym_dims(mapping_dict)

    def get_json_content(self):
        return """{{"type": "sequence", "is_int":"{}", "element":{}, "size":"{}"}}""".format(self.is_integer_element(), self.element_type.get_json_content(), self.size)


class MatrixType(LaVarType):
    def __init__(self, rows=0, cols=0, desc=None, element_type=ScalarType(), symbol=None, need_exp=False, diagonal=False, sparse=False, block=False, subs=None, list_dim=None, index_var=None, value_var=None, item_types=None, index_type=False,dynamic=DynamicTypeEnum.DYN_INVALID,rows_ir=None,cols_ir=None, owner=None):
        LaVarType.__init__(self, VarTypeEnum.MATRIX, desc, element_type, symbol=symbol,index_type=index_type, dynamic=dynamic, owner=owner)
        self.rows = rows
        self.cols = cols
        self.rows_ir = rows_ir
        self.cols_ir = cols_ir
        # attributes
        self.need_exp = need_exp      # need expression
        self.diagonal = diagonal      # L_ii assignment
        self.subs = subs or []
        # block matrix
        self.block = block
        self.list_dim = list_dim      # used by block mat
        self.item_types = item_types  # type array
        # sparse matrix
        self.sparse = sparse
        self.index_var = index_var    # used by sparse mat
        self.value_var = value_var    # used by sparse mat

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k in ['item_types', 'rows_ir', 'cols_ir']:
                setattr(result, k, getattr(self, k))
            else:
                setattr(result, k, copy.deepcopy(v, memo))
        return result

    def get_signature(self):
        # if self.element_type:
        #     return "matrix,rows:{},cols:{},ele_type:{}".format(self.rows, self.cols, self.element_type.get_signature())
        # else:
        #     return "matrix,rows:{},cols:{}".format(self.rows, self.cols)
        e_sig = self.element_type.get_signature()
        return "{}^({}×{})".format(e_sig, self.rows, self.cols)

    def get_relaxed_signature(self):
        e_sig = self.element_type.get_signature()
        return "{}^(×)".format(e_sig)
    def get_cpp_signature(self):
        e_type = 'ℤ' if self.element_type.is_int else 'ℝ'
        if self.cols == 1:
            return "{}^{}".format(e_type, self.rows)
        return "{}^({}×{})".format(e_type, self.rows, self.cols)

    def is_integer_element(self):
        return self.element_type.is_integer_element()

    def replace_sym_dims(self, mapping_dict):
        super(MatrixType, self).replace_sym_dims(mapping_dict)
        if self.rows in mapping_dict:
            self.rows = mapping_dict[self.rows]
        if self.cols in mapping_dict:
            self.cols = mapping_dict[self.cols]

    def get_json_content(self):
        return """{{"type": "matrix", "is_int":"{}", "element":{}, "rows":"{}", "cols":"{}"}}""".format(self.is_integer_element(), self.element_type.get_json_content(), self.rows, self.cols)

    def get_raw_text(self):
        e_type = 'ℤ' if self.element_type.is_int else 'ℝ'
        return "{}^({}×{})".format(e_type, self.rows, self.cols)


class VectorType(LaVarType):
    def __init__(self, rows=0, desc=None, element_type=ScalarType(), sparse=False,symbol=None, dynamic=DynamicTypeEnum.DYN_INVALID, rows_ir=None, owner=None):
        LaVarType.__init__(self, VarTypeEnum.VECTOR, desc, element_type, symbol, dynamic=dynamic, owner=owner)
        self.rows = rows
        self.rows_ir = rows_ir
        self.cols = 1
        self.sparse = sparse

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k in ['rows_ir']:
                setattr(result, k, getattr(self, k))
            else:
                setattr(result, k, copy.deepcopy(v, memo))
        return result

    def get_signature(self):
        # if self.element_type:
        #     return "vector,rows:{},ele_type:{}".format(self.rows, self.element_type.get_signature())
        # else:
        #     return "vector,rows:{}".format(self.rows)
        e_sig = self.element_type.get_signature()
        return "{}^{}".format(e_sig, self.rows)

    def get_relaxed_signature(self):
        e_sig = self.element_type.get_signature()
        return "{}^".format(e_sig)

    def get_cpp_signature(self):
        e_type = 'ℤ' if self.element_type.is_int else 'ℝ'
        return "{}^{}".format(e_type, self.rows)

    def is_integer_element(self):
        return self.element_type.is_integer_element()

    def replace_sym_dims(self, mapping_dict):
        super(VectorType, self).replace_sym_dims(mapping_dict)
        if self.rows in mapping_dict:
            self.rows = mapping_dict[self.rows]

    def get_json_content(self):
        return """{{"type": "vector", "is_int":"{}", "element":{}, "rows":"{}"}}""".format(self.is_integer_element(), self.element_type.get_json_content(), self.rows)

    def get_raw_text(self):
        e_type = 'ℤ' if self.element_type.is_int else 'ℝ'
        return "{}^{}".format(e_type, self.rows)


class SetType(LaVarType):
    def __init__(self, size=0, length=None, desc=None, element_type=None, symbol=None, int_list=None, type_list=None, index_type=False, dynamic=DynamicTypeEnum.DYN_INVALID, cur_type=SetTypeEnum.DEFAULT, owner=None):
        LaVarType.__init__(self, VarTypeEnum.SET, desc, element_type, symbol, dynamic=dynamic, index_type=index_type, owner=owner)
        self.size = size
        self.int_list = int_list     # whether the element is real number or integer
        self.type_list = type_list   # subtypes in a set
        if element_type is None and type_list:
            if len(type_list) > 1:
                self.element_type = TupleType(type_list=self.type_list)
            elif len(type_list) == 1:
                self.element_type = self.type_list[0]
            self.element_type.owner = self.owner
        self.cur_type = cur_type
        self.length = length

    def get_signature(self):
        # return 'set:' + ','.join([c_type.get_signature() for c_type in self.type_list])
        return self.get_raw_text()

    def contains_single_int(self):
        return len(self.type_list) == 1 and self.type_list[0].is_int_scalar()

    def is_integer_element(self):
        if len(self.type_list) > 0:
            all_int = True
            for s_type in self.type_list:
                if not s_type.is_integer_element():
                    all_int = False
                    break
            return all_int
        for value in self.int_list:
            if not value:
                return False
        return True

    def get_json_content(self):
        return """{{"type": "set", "is_int":"{}", "element":[{}], "size":"{}"}}""".format(self.is_integer_element(), ','.join(['"{}"'.format(1 if i else 0) for i in self.int_list]), self.size)

    def get_raw_text(self):
        all_true = True
        all_false = True
        content_list = []
        for value in self.int_list:
            if value:
                content_list.append('ℤ')
                all_false = False
            else:
                content_list.append('ℝ')
                all_true = False
        if all_true:
            return "{{ ℤ^{} }}".format(self.size)
        elif all_false:
            return "{{ ℤ^{} }}".format(self.size)
        return "{{ {} }}".format('×'.join(content_list))


class VertexSetType(SetType):
    def __init__(self, length=None, owner=None):
        SetType.__init__(self, size=1, length=length, int_list=[True], type_list=[VertexType()], cur_type=SetTypeEnum.VERTEX, owner=owner)
    def get_signature(self):
        return 'vertexset:' + ','.join([c_type.get_signature() for c_type in self.type_list])

    def get_cpp_signature(self):
        return self.get_raw_text()
class EdgeSetType(SetType):
    def __init__(self, length=None, owner=None):
        SetType.__init__(self, size=1, length=length, int_list=[True], type_list=[EdgeType()], cur_type=SetTypeEnum.EDGE, owner=owner)
    def get_signature(self):
        return 'edgeset:' + ','.join([c_type.get_signature() for c_type in self.type_list])
    def get_cpp_signature(self):
        return self.get_raw_text()
class FaceSetType(SetType):
    def __init__(self, length=None, owner=None):
        SetType.__init__(self, size=1, length=length, int_list=[True], type_list=[FaceType()], cur_type=SetTypeEnum.FACE, owner=owner)
    def get_signature(self):
        return 'faceset:' + ','.join([c_type.get_signature() for c_type in self.type_list])
    def get_cpp_signature(self):
        return self.get_raw_text()
class TetSetType(SetType):
    def __init__(self, length=None, owner=None):
        SetType.__init__(self, size=1, length=length, int_list=[True], type_list=[TetType()], cur_type=SetTypeEnum.TET, owner=owner)
    def get_signature(self):
        return 'tetset:' + ','.join([c_type.get_signature() for c_type in self.type_list])
    def get_cpp_signature(self):
        return self.get_raw_text()

class TupleType(LaVarType):
    def __init__(self, desc=None, element_type=None, symbol=None, type_list=None, index_type=False, dynamic=DynamicTypeEnum.DYN_INVALID, owner=None):
        LaVarType.__init__(self, VarTypeEnum.TUPLE, desc, element_type, symbol, dynamic=dynamic, index_type=index_type, owner=owner)
        self.type_list = type_list   # subtypes in a set
        self.size = 0 if type_list is None else len(type_list)

    def get_signature(self):
        return 'tuple:' + ','.join([c_type.get_signature() for c_type in self.type_list])
    
    def is_integer_element(self):
        all_int = True
        for s_type in self.type_list:
            if not s_type.is_integer_element():
                all_int = False
                break
        return all_int

class SimplicialSetType(TupleType):
    def __init__(self, desc=None, owner=None):
        TupleType.__init__(self, desc=desc, type_list=[VertexSetType(), EdgeSetType(), FaceSetType(), TetSetType()], owner=owner)


class IndexType(LaVarType):
    def __init__(self, desc=None, symbol=None, owner=None):
        LaVarType.__init__(self, VarTypeEnum.INDEX, desc, symbol, owner=owner)



class FuncType(IntEnum):
    FuncInvalid = -1
    FuncDetermined = 0
    FuncDynamic = 1   # need to figure out the params and ret


class FunctionType(LaVarType):
    def __init__(self, desc=None, symbol=None, params=None, ret=None, template_symbols=None, ret_symbols=None, cur_type=FuncType.FuncDetermined):
        LaVarType.__init__(self, VarTypeEnum.FUNCTION, desc, symbol)
        self.params = params or []
        self.ret = ret
        self.template_symbols = template_symbols or {}  # symbol: index of params
        self.ret_symbols = ret_symbols or []
        self.cur_type = cur_type

    def get_signature(self):
        signature = get_list_signature(self.params) + ' → '
        ret_list = []
        if isinstance(self.ret, list):
            for cur_ret in self.ret:
                ret_list.append(cur_ret.get_signature())
            ret_sig = ','.join(ret_list)
        else:
            ret_sig = self.ret.get_signature()
        return signature + ret_sig

    def get_overloading_signature(self):
        return self.get_param_signature()

    def get_param_signature(self, cpp=False):
        return get_list_signature(self.params, cpp)

    def get_param_relatex_signature(self, cpp=False):
        return get_list_relatex_signature(self.params, cpp)

    def ret_template(self):
        return len(self.ret_symbols) > 0

    def get_json_content(self):
        param_list = []
        for param in self.params:
            param_list.append(param.get_json_content())
        ret_list = []
        for cur_ret in self.ret:
            ret_list.append(cur_ret.get_json_content())
        return """{{"type": "function", "params":[{}], "ret":[{}]}}""".format(','.join(param_list), ','.join(ret_list))

    def same_as(self, target):
        return target.is_function() and self.get_signature() == target.get_signature()

    def replace_sym_dims(self, mapping_dict):
        super(FunctionType, self).replace_sym_dims(mapping_dict)
        for index in range(len(self.params)):
            self.params[index].replace_sym_dims(mapping_dict)
        if isinstance(self.ret, list):
            for cur_index in range(len(self.ret)):
                self.ret[cur_index].replace_sym_dims(mapping_dict)
        else:
            self.ret.replace_sym_dims(mapping_dict)


class OverloadingFunctionType(LaVarType):
    def __init__(self, desc=None, symbol=None, func_list=None, fname_list=None, pre_fname_list=None):
        LaVarType.__init__(self, VarTypeEnum.OVERLOADINGFUNCTION, desc, symbol)
        self.func_list = func_list
        self.fname_list = fname_list  # predefined overloading names
        self.pre_fname_list = pre_fname_list # original fname list in other module

    def get_correct_ftype(self, param_list, allow_omit=True):
        # when adding new types, allow_omit is supposed to be False, when checking func call, it's True
        omitted = False  # whether size is omitted
        # given param list, get the correct function type
        param_sig = get_list_signature(param_list)
        la_debug("param_sig:{}".format(param_sig))
        for cur_func in self.func_list:
            cur_sig = cur_func.get_param_signature()
            la_debug("cur_sig:{}".format(cur_sig))
            if param_sig == cur_sig:
                return cur_func, omitted
        # no type found, relax checking conditions (omit 0 dimension in matrices/vectors)
        if allow_omit:
            omitted = True
            param_sig = get_list_relatex_signature(param_list)
            la_debug("omitted param_sig:{}".format(param_sig))
            for cur_func in self.func_list:
                cur_sig = cur_func.get_param_relatex_signature()
                la_debug("omitted cur_sig:{}".format(cur_sig))
                if param_sig == cur_sig:
                    return cur_func, omitted
        return None, omitted

    def add_new_type(self, f_type):
        success = True
        found, omitted = self.get_correct_ftype(f_type.params, allow_omit=False)
        la_debug("add_new_type, current:{}, sig:{}".format(len(self.func_list), f_type.get_signature()))
        if found is None:
            self.func_list.append(f_type)
        else:
            success = False
        return success
    def get_signature(self):
        signature = "overloadingfunc,size:{},\n".format(len(self.func_list))
        sig_list = [func.get_signature() for func in self.func_list]
        return signature + '\n'.join(sig_list)

    def has_duplicate_cpp_types(self):
        # some iheartla types have the same signatures in cpp, e.g.:{Z} vertices v.s.  {Z} edges
        cpp_sig_list = []
        ret = False
        for cur_func in self.func_list:
            cpp_sig = cur_func.get_param_signature(cpp=True)
            if cpp_sig in cpp_sig_list:
                ret = True
                break
            cpp_sig_list.append(cpp_sig)
        return ret

    def replace_sym_dims(self, mapping_dict):
        super(OverloadingFunctionType, self).replace_sym_dims(mapping_dict)
        for index in range(len(self.func_list)):
            self.func_list[index].replace_sym_dims(mapping_dict)
class MappingType(LaVarType):
    def __init__(self, desc=None, symbol=None, src=None, dst=None, ele_set=None, subset=False, owner=None):
        LaVarType.__init__(self, VarTypeEnum.MAPPING, desc, symbol, owner=owner)
        self.src = src
        self.dst = dst
        self.ele_set = ele_set
        self.subset = subset


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

# Useful functions
from ..la_tools.la_msg import *
from ..la_tools.la_helper import *


class TypeInferenceEnum(Enum):
    INF_ADD = 0
    INF_SUB = 1
    INF_MUL = 2
    INF_DIV = 3
    INF_MATRIX_ROW = 4


def get_op_desc(op):
    desc = ""
    if op == TypeInferenceEnum.INF_ADD:
        desc = "add"
    elif op == TypeInferenceEnum.INF_SUB:
        desc = "subtract"
    elif op == TypeInferenceEnum.INF_MUL:
        desc = "multiply"
    elif op == TypeInferenceEnum.INF_DIV:
        desc = "divide"
    elif op == TypeInferenceEnum.INF_MATRIX_ROW:
        desc = "place"
    return desc


def get_list_signature(param_list, cpp=False):
    # get the signatures of function parameters
    return ','.join(param.get_cpp_signature() if cpp else param.get_signature() for param in param_list)
def get_list_relatex_signature(param_list, cpp=False):
    # get the signatures of function parameters
    return ','.join(param.get_cpp_signature() if cpp else param.get_relaxed_signature() for param in param_list)

def get_func_signature(name, la_type):
    # only consider parameters
    return "{} = {}".format(name, la_type.get_overloading_signature())

def get_type_desc(la_type):
    desc = "NoneType"
    if la_type.is_sequence():
        desc = "sequence"
    elif la_type.is_matrix():
        dim_str = "{}, {}".format(la_type.rows, la_type.cols)
        if la_type.is_dynamic():
            if la_type.is_dynamic_row() and la_type.is_dynamic_col():
                dim_str = "*,*"
            elif la_type.is_dynamic_row():
                dim_str = "*,{}".format(la_type.cols)
            elif la_type.is_dynamic_col():
                dim_str = "{},*".format(la_type.rows)
        desc = "matrix({})".format(dim_str)
    elif la_type.is_vector():
        dim_str = "{}".format(la_type.rows)
        if la_type.is_dynamic_row():
            dim_str = "*"
        desc = "vector({})".format(dim_str)
    elif la_type.is_scalar():
        desc = "scalar"
    elif la_type.is_set():
        desc = "set"
    elif la_type.is_function():
        desc = "function"
    return desc


def get_derived_type(op, left_type, right_type):
    """
    Assume derived type is valid
    """
    ret_type = None
    if op == TypeInferenceEnum.INF_ADD or op == TypeInferenceEnum.INF_SUB:
        ret_type = copy.deepcopy(left_type)  # default type
        if left_type.is_scalar():
            ret_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
        elif left_type.is_matrix():
            # assert right_type.is_matrix() or right_type.is_vector(), error_msg
            if left_type.is_dynamic() or right_type.is_dynamic():
                if left_type.is_dynamic() and right_type.is_dynamic():
                    if left_type.is_dynamic_row() and left_type.is_dynamic_col():
                        ret_type = copy.deepcopy(right_type)
                    elif left_type.is_dynamic_row():
                        if right_type.is_dynamic_row() and right_type.is_dynamic_col():
                            ret_type = copy.deepcopy(left_type)
                        elif right_type.is_dynamic_row():
                            ret_type = copy.deepcopy(left_type)
                        elif right_type.is_dynamic_col():
                            ret_type = copy.deepcopy(left_type)
                            ret_type.rows = right_type.rows
                            ret_type.set_dynamic_type(DynamicTypeEnum.DYN_INVALID)  # change to static type
                    elif left_type.is_dynamic_col():
                        if right_type.is_dynamic_row() and right_type.is_dynamic_col():
                            ret_type = copy.deepcopy(left_type)
                        elif right_type.is_dynamic_row():
                            ret_type = copy.deepcopy(left_type)
                            ret_type.cols = right_type.cols
                            ret_type.set_dynamic_type(DynamicTypeEnum.DYN_INVALID)  # change to static type
                        elif right_type.is_dynamic_col():
                            ret_type = copy.deepcopy(left_type)
                else:
                    if left_type.is_dynamic():
                        if left_type.is_dynamic_row() and left_type.is_dynamic_col():
                            ret_type = copy.deepcopy(right_type)
                        else:
                            pass
                    else:
                        if right_type.is_dynamic_row() and right_type.is_dynamic_col():
                            ret_type = copy.deepcopy(left_type)
                        else:
                            pass
            else:
                # static
                if left_type.sparse:
                    if right_type.is_matrix() and right_type.sparse:
                        ret_type.sparse = True
                else:
                    ret_type.sparse = False
            ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
        elif left_type.is_vector():
            if right_type.is_matrix():
                ret_type = copy.deepcopy(right_type)
            ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
        else:
            # sequence et al.
            pass
        # index type checking
        if left_type.index_type or right_type.index_type:
            ret_type.index_type = True
            if op == TypeInferenceEnum.INF_ADD:
                pass
            else:
                if left_type.index_type and right_type.index_type:
                    ret_type.index_type = False
    elif op == TypeInferenceEnum.INF_MUL:
        if left_type.is_scalar():
            ret_type = copy.deepcopy(right_type)
            ret_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
        elif left_type.is_matrix():
            if right_type.is_scalar():
                ret_type = copy.deepcopy(left_type)
            elif right_type.is_matrix():
                ret_type = MatrixType(rows=left_type.rows, cols=right_type.cols)
                if left_type.sparse and right_type.sparse:
                    ret_type.sparse = True
                # if left_type.rows == 1 and right_type.cols == 1:
                #     ret_type = ScalarType()
                ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
            elif right_type.is_vector():
                if left_type.rows == 1:
                    # scalar
                    ret_type = ScalarType()
                    need_cast = True
                    ret_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
                else:
                    ret_type = VectorType(rows=left_type.rows)
                    ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
        elif left_type.is_vector():
            if right_type.is_scalar():
                ret_type = copy.deepcopy(left_type)
                ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
            elif right_type.is_matrix():
                ret_type = MatrixType(rows=left_type.rows, cols=right_type.cols)
                ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
            elif right_type.is_vector():
                ret_type = copy.deepcopy(left_type)
                ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
    elif op == TypeInferenceEnum.INF_DIV:
        ret_type = copy.deepcopy(left_type)
        if left_type.is_scalar():
            ret_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
        else:
            ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
    elif op == TypeInferenceEnum.INF_MATRIX_ROW:
        # assert left_type.var_type == right_type.var_type
        ret_type = copy.deepcopy(left_type)
    return ret_type

def get_derivative_type(upper_type, lower_type):
    # get the type of derivatives
    ret_type = ScalarType()
    if upper_type.is_scalar():
        if lower_type.is_scalar():
            ret_type = ScalarType()
        elif lower_type.is_vector():
            ret_type = VectorType(rows=lower_type.rows)
        elif lower_type.is_matrix():
            # ret_type = MatrixType(rows=lower_type.rows, cols=lower_type.cols)
            ret_type = VectorType(rows=mul_dims(lower_type.rows, lower_type.cols))
        elif lower_type.is_sequence():
            if lower_type.element_type.is_scalar():
                ret_type = VectorType(rows=lower_type.size)
            elif lower_type.element_type.is_vector():
                # ret_type = MatrixType(rows=lower_type.size, cols=lower_type.element_type.rows)
                ret_type = VectorType(rows=mul_dims(lower_type.size, lower_type.element_type.rows))
    elif upper_type.is_vector():
        if lower_type.is_scalar():
            ret_type = VectorType(rows=lower_type.rows)
        elif lower_type.is_vector():
            ret_type = MatrixType(rows=upper_type.rows, cols=lower_type.rows)
        elif lower_type.is_sequence():
            if lower_type.element_type.is_scalar():
                ret_type = MatrixType(rows=upper_type.rows, cols=lower_type.size)
    elif upper_type.is_matrix():
        if lower_type.is_scalar():
            ret_type = MatrixType(rows=upper_type.rows, cols=upper_type.cols)
    elif upper_type.is_sequence():
        if upper_type.element_type.is_scalar():
            if lower_type.is_scalar():
                ret_type = VectorType(rows=upper_type.size)
            elif lower_type.is_vector():
                ret_type = MatrixType(rows=upper_type.size, cols=lower_type.rows)
            elif lower_type.is_sequence() and lower_type.element_type.is_scalar():
                ret_type = MatrixType(rows=upper_type.size, cols=lower_type.size)
        elif upper_type.element_type.is_vector():
            ret_type = MatrixType(rows=upper_type.size, cols=upper_type.element_type.rows)
    return ret_type

def get_hessian_type(upper_type, lower_type):
    # get the type of hessian
    ret_type = ScalarType()
    if upper_type.is_scalar():
        if lower_type.is_vector():
            ret_type = MatrixType(rows=lower_type.rows, cols=lower_type.rows, element_type=ScalarType(), sparse=False)
        elif lower_type.is_sequence():
            ret_type = MatrixType(rows=lower_type.size, cols=lower_type.size, sparse=False)
            if lower_type.element_type.is_scalar():
                ret_type = MatrixType(rows=lower_type.size, cols=lower_type.size, sparse=False)
            elif lower_type.element_type.is_vector():
                # ret_type = MatrixType(rows=lower_type.size, cols=lower_type.element_type.rows)
                size = mul_dims(lower_type.size, lower_type.element_type.rows)
                ret_type = MatrixType(rows=size, cols=size, sparse=False)
    return ret_type

def make_function_type(params=[], ret=[]):
    return FunctionType(params=params, ret=ret)