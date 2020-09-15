from tatsu.model import NodeWalker
from tatsu.objectmodel import Node
from la_parser.la_types import *
from la_tools.la_logger import *
from la_tools.la_msg import *

## Make the visualizer
try: from la_tools.la_visualizer import LaVisualizer
except ImportError:
    print( "Skipping visualizer." )
    class LaVisualizer(object):
        def visualize(self, node): pass

from la_parser.ir import *
from enum import Enum, IntFlag


class ParserTypeEnum(IntFlag):
    INVALID = 0
    DEFAULT = 7
    #
    LATEX = 1
    NUMPY = 2
    EIGEN = 4
    MATLAB = 8
    JULIA = 16
    PYTORCH = 32
    ARMADILLO = 64
    TENSORFLOW = 128


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
PARAM_INDEX = "param_index"


def la_is_inside_matrix(**kwargs):
    if INSIDE_MATRIX in kwargs and kwargs[INSIDE_MATRIX] is True:
        return True
    return False


def la_is_inside_sum(**kwargs):
    if INSIDE_SUMMATION in kwargs and kwargs[INSIDE_SUMMATION] is True:
        return True
    return False


def la_is_if(**kwargs):
    if IF_COND in kwargs and kwargs[IF_COND] is True:
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
        self.tmp_symtable = {}
        self.parameters = []
        self.subscripts = {}
        self.sub_name_dict = {}  # only for parameter checker
        self.name_cnt_dict = {}
        self.dim_dict = {}       # parameter used. h:w_i
        self.ids_dict = {}    # identifiers with subscripts
        self.unofficial_method = False
        self.visualizer = LaVisualizer()
        self.logger = LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT)
        self.la_msg = LaMsg.getInstance()
        self.ret_symbol = None
        self.packages = {'trigonometry': ['sin', 'asin', 'cos', 'acos', 'tan', 'atan', 'atan2',
                                          'sinh', 'asinh', 'cosh', 'acosh', 'tanh', 'atanh', 'cot',
                                          'sec', 'csc']}
        self.constants = ['π']
        # self.directive_parsing = True   # directives grammar

    def reset(self):
        self.reset_state()

    def reset_state(self):
        self.symtable.clear()
        self.tmp_symtable.clear()
        self.parameters = []
        self.subscripts.clear()
        self.sub_name_dict.clear()
        self.name_cnt_dict.clear()
        self.dim_dict.clear()
        self.ids_dict.clear()
        self.ret_symbol = None
        self.unofficial_method = False

    def get_func_symbols(self):
        ret = {}
        for keys in self.symtable:
            if self.symtable[keys] and self.symtable[keys].is_function():
                ret[keys] = self.symtable[keys].get_signature()
        return ret

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

    def get_op_desc(self, op):
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

    def get_type_desc(self, la_type):
        desc = "NoneType"
        if la_type.is_sequence():
            desc = "sequence"
        elif la_type.is_matrix():
            desc = "matrix"
        elif la_type.is_vector():
            desc = "vector"
        elif la_type.is_scalar():
            desc = "scalar"
        elif la_type.is_set():
            desc = "set"
        elif la_type.is_function():
            desc = "function"
        return desc

    def walk_Node(self, node):
        print('Reached Node: ', node)

    def walk_object(self, o):
        raise Exception('Unexpected type %s walked', type(o).__name__)

    def walk_Start(self, node, **kwargs):
        # self.visualizer.visualize(node)  # visualize
        ir_node = StartNode(parse_info=node.parseinfo)
        if node.directive:
            for directive in node.directive:
                ir_node.directives.append(self.walk(directive, **kwargs))
        if node.cond:
            cond_node = self.walk(node.cond, **kwargs)
            ir_node.cond = cond_node
        if 'pre_walk' in kwargs:
            return ir_node
        stat_list = self.walk(node.stat, **kwargs)
        block_node = BlockNode()
        for index in range(len(stat_list)):
            update_ret_type = False
            if index == len(stat_list) - 1:
                if type(stat_list[index]).__name__ == 'Assignment':
                    kwargs[SET_RET_SYMBOL] = True
                else:
                    # new symbol for return value
                    self.ret_symbol = "ret"
                    update_ret_type = True
                    kwargs[LHS] = self.ret_symbol
            type_info = self.walk(stat_list[index], **kwargs)
            block_node.add_stmt(type_info.ir)
            if update_ret_type:
                self.symtable[self.ret_symbol] = type_info.la_type
        ir_node.stat = block_node
        return ir_node

    ###################################################################
    def walk_WhereConditions(self, node, **kwargs):
        ir_node = WhereConditionsNode(parse_info=node.parseinfo)
        # for cond in node.value:
        #     cond_node = self.walk(cond, **kwargs)
        #     ir_node.value.append(cond_node)
        ir_list = []
        ir_index = []  # matrix, vector
        func_index = []  # function
        self.parameters = [None] * len(node.value)
        for i in range(len(node.value)):
            # walk scalar first
            if type(node.value[i].type).__name__ == "ScalarType" or type(node.value[i].type).__name__ == "SetType":
                kwargs[PARAM_INDEX] = i
                ir_list.append(self.walk(node.value[i], **kwargs))
            elif type(node.value[i].type).__name__ == "FunctionType":
                ir_list.append(None)
                func_index.append(i)
            else:
                ir_list.append(None)
                ir_index.append(i)
        # matrix, vector nodes
        if len(ir_index) > 0:
            for i in range(len(ir_index)):
                kwargs[PARAM_INDEX] = ir_index[i]
                ir_list[ir_index[i]] = self.walk(node.value[ir_index[i]], **kwargs)
        # func nodes:
        if len(func_index) > 0:
            for i in range(len(func_index)):
                kwargs[PARAM_INDEX] = func_index[i]
                ir_list[func_index[i]] = self.walk(node.value[func_index[i]], **kwargs)
        #
        ir_node.value = ir_list
        return ir_node

    def walk_WhereCondition(self, node, **kwargs):
        ir_node = WhereConditionNode(parse_info=node.parseinfo)
        id0_info = self.walk(node.id, **kwargs)
        ir_node.id = id0_info.ir
        id0 = id0_info.content
        ret = node.text.split(':')
        desc = ':'.join(ret[1:len(ret)])
        ir_node.desc = node.desc
        type_node = self.walk(node.type, **kwargs)
        type_node.la_type.desc = desc
        self.handle_identifier(id0, type_node.la_type)
        self.logger.debug("param index:{}".format(kwargs[PARAM_INDEX]))
        self.update_parameters(id0, kwargs[PARAM_INDEX])
        if type_node.la_type.is_matrix():
            id1 = type_node.la_type.rows
            id2 = type_node.la_type.cols
            if isinstance(id1, str):
                if id1 not in self.symtable:
                    self.symtable[id1] = ScalarType(is_int=True)
                if self.contain_subscript(id0):
                    self.dim_dict[id1] = [self.get_main_id(id0), 1]
                else:
                    self.dim_dict[id1] = [self.get_main_id(id0), 0]
            if isinstance(id2, str):
                if id2 not in self.symtable:
                    self.symtable[id2] = ScalarType(is_int=True)
                if self.contain_subscript(id0):
                    self.dim_dict[id2] = [self.get_main_id(id0), 2]
                else:
                    self.dim_dict[id2] = [self.get_main_id(id0), 1]
        elif type_node.la_type.is_vector():
            id1 = type_node.la_type.rows
            if isinstance(id1, str):
                if id1 not in self.symtable:
                    self.symtable[id1] = ScalarType(is_int=True)
                self.dim_dict[id1] = [self.get_main_id(id0), 0]
        ir_node.type = type_node
        return ir_node


    def walk_MatrixType(self, node, **kwargs):
        ir_node = MatrixTypeNode(parse_info=node.parseinfo)
        id1_info = self.walk(node.id1, **kwargs)
        ir_node.id1 = id1_info.ir
        id1 = id1_info.content
        id2_info = self.walk(node.id2, **kwargs)
        ir_node.id2 = id2_info.ir
        id2 = id2_info.content
        element_type = ''
        if node.type:
            ir_node.type = node.type
            if node.type == 'ℝ':
                element_type = ScalarType()
            elif node.type == 'ℤ':
                element_type = ScalarType(is_int=True)
        else:
            element_type = ScalarType()
        la_type = MatrixType(rows=id1, cols=id2, element_type=element_type)
        ir_node.la_type = la_type
        return ir_node

    def walk_VectorType(self, node, **kwargs):
        ir_node = VectorTypeNode(parse_info=node.parseinfo)
        id1_info = self.walk(node.id1, **kwargs)
        ir_node.id1 = id1_info.ir
        id1 = id1_info.content
        element_type = ''
        if node.type:
            ir_node.type = node.type
            if node.type == 'ℝ':
                element_type = ScalarType()
            elif node.type == 'ℤ':
                element_type = ScalarType(is_int=True)
        else:
            element_type = ScalarType()
        la_type = VectorType(rows=id1, element_type=element_type)
        ir_node.la_type = la_type
        return ir_node

    def walk_ScalarType(self, node, **kwargs):
        ir_node = ScalarTypeNode(parse_info=node.parseinfo)
        la_type = ScalarType()
        if node.z:
            la_type = ScalarType(is_int=True)
            ir_node.is_int = True
        ir_node.la_type = la_type
        return ir_node

    def walk_SetType(self, node, **kwargs):
        ir_node = SetTypeNode(parse_info=node.parseinfo)
        int_list = []
        cnt = 1
        if node.type:
            ir_node.type = node.type
            cnt = len(node.type)
            for t in node.type:
                if t == 'ℤ':
                    int_list.append(True)
                else:
                    int_list.append(False)
        elif node.type1:
            ir_node.type1 = node.type1
            cnt_info = self.walk(node.cnt, **kwargs)
            if isinstance(cnt_info.content, int):
                cnt = cnt_info.content
                ir_node.cnt = cnt
            if node.type1 == 'ℤ':
                int_list = [True] * cnt
            else:
                int_list = [False] * cnt
        elif node.type2:
            ir_node.type2 = node.type2
            cnt = 0
            for index in range(len(node.cnt)):
                cnt += self.get_unicode_number(node.cnt[len(node.cnt)-1-index]) * 10 ** index
            if node.type2 == 'ℤ':
                int_list = [True] * cnt
            else:
                int_list = [False] * cnt
        ir_node.la_type = SetType(size=cnt, int_list=int_list)
        return ir_node

    def get_unicode_number(self, unicode):
        # 0:\u2070,1:\u00B9,2:\u00B2,3:\u00B3,4-9:[\u2074-\u2079]
        number_dict = {'⁰':0,'¹':1,'²':2, '³':3,'⁴':4,'⁵':5,'⁶':6,'⁷':7,'⁸':8,'⁹':9 }
        return number_dict[unicode]

    def walk_FunctionType(self, node, **kwargs):
        ir_node = FunctionTypeNode(parse_info=node.parseinfo)
        ir_node.empty = node.empty
        ir_node.separators = node.separators
        params = []
        template_symbols = {}
        template_ret = []
        if node.params:
            for index in range(len(node.params)):
                param_node = self.walk(node.params[index], **kwargs)
                ir_node.params.append(param_node)
                params.append(param_node.la_type)
                if param_node.la_type.is_scalar():
                    pass
                elif param_node.la_type.is_vector():
                    if isinstance(param_node.la_type.rows, str) and param_node.la_type.rows not in self.symtable:
                        if param_node.la_type.rows not in template_symbols:
                            template_symbols[param_node.la_type.rows] = index
                elif param_node.la_type.is_matrix():
                    if isinstance(param_node.la_type.rows, str) and param_node.la_type.rows not in self.symtable:
                        if param_node.la_type.rows not in template_symbols:
                            template_symbols[param_node.la_type.rows] = index
                    if isinstance(param_node.la_type.cols, str) and param_node.la_type.cols not in self.symtable:
                        if param_node.la_type.cols not in template_symbols:
                            template_symbols[param_node.la_type.cols] = index
        ret_node = self.walk(node.ret, **kwargs)
        ir_node.ret = ret_node
        ret = ret_node.la_type
        if ret.is_vector():
            if isinstance(ret.rows, str):
                assert ret.rows in self.symtable or ret.rows in template_symbols, "vector as return value of function must have concrete dimension"
                if ret.rows in template_symbols:
                    if ret.rows not in template_ret:
                        template_ret.append(ret.rows)
        elif ret.is_matrix():
            if isinstance(ret.rows, str):
                assert ret.rows in self.symtable or ret.rows in template_symbols, "matrix as return value of function must have concrete dimension"
            if ret.rows in template_symbols:
                if ret.rows not in template_ret:
                    template_ret.append(ret.rows)
            if isinstance(ret.cols, str):
                assert ret.cols in self.symtable or ret.cols in template_symbols, "matrix as return value of function must have concrete dimension"
                if ret.cols in template_symbols:
                    if ret.cols not in template_ret:
                        template_ret.append(ret.cols)
        self.logger.debug("template_symbols:{}, template_ret:{}".format(template_symbols, template_ret))
        la_type = FunctionType(params=params, ret=ret, template_symbols=template_symbols, ret_symbols=template_ret)
        ir_node.la_type = la_type
        return ir_node

    def update_parameters(self, identifier, index):
        if self.contain_subscript(identifier):
            arr = self.get_all_ids(identifier)
            self.parameters[index] = arr[0]
        else:
            self.parameters[index] = identifier

    ###################################################################
    def walk_Import(self, node, **kwargs):
        assert node.package in self.packages, "package {} not exist".format(node.package)
        func_list = self.packages[node.package]
        for name in node.names:
            assert name in func_list, "func {} not exist".format(name)
        return ImportNode(package=node.package, names=node.names, parse_info=node.parseinfo)

    def walk_Statements(self, node, **kwargs):
        stat_list = []
        if node.stats:
            stat_list = self.walk(node.stats, **kwargs)
        stat_list.append(node.stat)
        return stat_list

    def walk_Expression(self, node, **kwargs):
        value_info = self.walk(node.value, **kwargs)
        ir_node = ExpressionNode(parse_info=node.parseinfo)
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
        ret_type = self.type_inference(TypeInferenceEnum.INF_ADD, left_info.ir, right_info.ir)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node = AddNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        return ret_info

    def walk_Subtract(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        left_type = left_info.la_type
        right_info = self.walk(node.right, **kwargs)
        right_type = right_info.la_type
        ret_type = self.type_inference(TypeInferenceEnum.INF_SUB, left_info.ir, right_info.ir)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node = SubNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        return ret_info

    def walk_AddSub(self, node, **kwargs):
        assert IF_COND in kwargs, "must be used inside if codition"
        left_info = self.walk(node.left, **kwargs)
        left_type = left_info.la_type
        right_info = self.walk(node.right, **kwargs)
        right_type = right_info.la_type
        ret_type = self.type_inference(TypeInferenceEnum.INF_ADD, left_info.ir, right_info.ir)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node = AddSubNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        return ret_info

    def walk_Multiply(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        return self.make_mul_info(left_info, right_info)

    def make_mul_info(self, left_info, right_info):
        left_type = left_info.la_type
        right_type = right_info.la_type
        ret_type = self.type_inference(TypeInferenceEnum.INF_MUL, left_info.ir, right_info.ir)
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
        return ret_info

    def walk_Divide(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        left_type = left_info.la_type
        right_info = self.walk(node.right, **kwargs)
        right_type = right_info.la_type
        ret_type = self.type_inference(TypeInferenceEnum.INF_DIV, left_info.ir, right_info.ir)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node = DivNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        return ret_info

    def walk_Subexpression(self, node, **kwargs):
        value_info = self.walk(node.value, **kwargs)
        ir_node = SubexpressionNode(parse_info=node.parseinfo)
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
        # ir
        assign_node = AssignNode(id0_info.ir, right_info.ir, parse_info=node.parseinfo)
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
                if right_info.la_type is not None and right_info.la_type.is_matrix():
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
        assign_node.symbols = right_info.symbols
        right_info.ir = assign_node
        return right_info

    def walk_Summation(self, node, **kwargs):
        kwargs[INSIDE_SUMMATION] = True
        #
        ir_node = SummationNode(parse_info=node.parseinfo)
        if node.cond:
            id_info = self.walk(node.id, **kwargs)
            ir_node.id = id_info.ir
            ir_node.cond = self.walk(node.cond, **kwargs).ir
            id_info.ir.set_parent(ir_node)
            subs = id_info.content
            if LHS in kwargs:
                lhs = kwargs[LHS]
                lhs_ids = self.get_all_ids(lhs)
                # assert lhs_ids[1][0] == lhs_ids[1][1], "multiple subscripts for sum"
        else:
            sub_info = self.walk(node.sub)
            ir_node.sub = sub_info.ir
            ir_node.id = sub_info.ir
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
        self.logger.debug("summation, symbols: {}".format(ir_node.symbols))
        return ret_info

    def walk_Optimize(self, node, **kwargs):
        opt_type = OptimizeType.OptimizeInvalid
        if node.min:
            opt_type = OptimizeType.OptimizeMin
        elif node.max:
            opt_type = OptimizeType.OptimizeMax
        elif node.amin:
            opt_type = OptimizeType.OptimizeArgmin
        elif node.amax:
            opt_type = OptimizeType.OptimizeArgmax
        base_type = self.walk(node.base_type, **kwargs)
        base_node = self.walk(node.id, **kwargs).ir
        # temporary add to symbol table : opt scope
        base_id = base_node.get_main_id()
        self.symtable[base_id] = base_type.la_type
        self.tmp_symtable[base_id] = base_type.la_type
        exp_node = self.walk(node.exp, **kwargs).ir
        cond_list = []
        if node.cond:
            cond_list = self.walk(node.cond, **kwargs)
        del self.symtable[base_id]
        #
        assert exp_node.la_type.is_scalar(), "Objective function must return a scalar"
        opt_node = OptimizeNode(opt_type, cond_list, exp_node, base_node, base_type, parse_info=node.parseinfo)
        opt_node.la_type = ScalarType()
        node_info = NodeInfo(opt_node.la_type, ir=opt_node)
        return node_info

    def walk_MultiCond(self, node, **kwargs):
        conds_list = []
        if node.m_cond:
            conds_list = self.walk(node.m_cond, **kwargs)
        conds_list.append(self.walk(node.cond, **kwargs).ir)
        return conds_list

    def walk_Domain(self, node, **kwargs):
        domain_node = DomainNode(self.walk(node.lower, **kwargs).ir, self.walk(node.upper, **kwargs).ir, parse_info=node.parseinfo)
        return domain_node

    def walk_Integral(self, node, **kwargs):
        base_node = self.walk(node.id, **kwargs).ir
        # temporary add to symbol table : opt scope
        base_id = base_node.get_main_id()
        self.symtable[base_id] = ScalarType() # scalar only
        self.tmp_symtable[base_id] = ScalarType()
        if node.d:
            domain_node = self.walk(node.d, **kwargs)
        else:
            domain_node = DomainNode(self.walk(node.lower, **kwargs).ir, self.walk(node.upper, **kwargs).ir)
        int_node = IntegralNode(domain=domain_node, exp=self.walk(node.exp, **kwargs).ir, base=base_node, parse_info=node.parseinfo)
        node_info = NodeInfo(ScalarType())
        node_info.ir = int_node
        int_node.la_type = node_info.la_type
        #
        del self.symtable[base_id]
        return node_info

    def walk_Norm(self, node, **kwargs):
        ir_node = NormNode(parse_info=node.parseinfo)
        value_info = self.walk(node.value, **kwargs)
        ir_node.value = value_info.ir
        if node.sub:
            if node.sub == 'F':
                ir_node.norm_type = NormType.NormFrobenius
            elif node.sub == '*':
                ir_node.norm_type = NormType.NormNuclear
            elif node.sub == '∞':
                ir_node.norm_type = NormType.NormMax
            else:
                sub_type = self.walk(node.sub, **kwargs)
                if sub_type.ir.node_type == IRNodeType.Integer:
                    ir_node.sub = sub_type.ir.value
                    ir_node.norm_type = NormType.NormInteger
                else:
                    # identifier
                    ir_node.norm_type = NormType.NormIdentifier
                    ir_node.sub = sub_type.ir
        else:
            # default
            if ir_node.value.la_type.is_matrix():
                ir_node.norm_type = NormType.NormFrobenius
            else:
                ir_node.norm_type = NormType.NormInteger
            ir_node.sub = 2
        #
        if ir_node.value.la_type.is_scalar():
            assert node.single is not None, "Scalar type has to use | rather than ||"
        elif ir_node.value.la_type.is_vector():
            assert node.single is None, "Vector type has to use || rather than |"
            assert ir_node.norm_type != NormType.NormFrobenius and ir_node.norm_type != NormType.NormNuclear, "Invalid norm for Vector"
            if ir_node.norm_type == NormType.NormIdentifier:
                assert ir_node.sub.la_type.is_matrix() or ir_node.sub.la_type.is_scalar(), "Subscript has to be matrix or scalar for vector type"
                if ir_node.sub.la_type.is_matrix():
                    assert ir_node.sub.la_type.rows == ir_node.sub.la_type.cols and ir_node.sub.la_type.rows == ir_node.value.la_type.rows, "Norm: dim error"
        elif ir_node.value.la_type.is_matrix():
            assert node.single is None, "MATRIX type has to use || rather than |"
            assert ir_node.norm_type == NormType.NormFrobenius or ir_node.norm_type == NormType.NormNuclear, "Invalid norm for Matrix"
            if ir_node.norm_type == NormType.NormNuclear:
                assert not ir_node.value.la_type.sparse, "Nuclear norm is invalid for sparse matrix"
        # ret type
        ret_type = ScalarType()
        ir_node.la_type = ret_type
        if node.power:
            # superscript
            power_info = self.walk(node.power, **kwargs)
            ir_node = self.create_power_node(ir_node, power_info.ir)
        node_info = NodeInfo(ret_type, symbols=value_info.symbols, ir=ir_node)
        return node_info

    def walk_InnerProduct(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        assert left_info.ir.la_type.is_vector(), "parameters must be vector"
        assert right_info.ir.la_type.is_vector(), "parameters must be vector"
        assert left_info.ir.la_type.rows == right_info.ir.la_type.rows, "the dims of vector must be the same"
        sub_node = None
        if node.sub:
            sub_node = self.walk(node.sub, **kwargs).ir
            assert sub_node.la_type.is_matrix() and sub_node.la_type.rows==sub_node.la_type.cols==left_info.ir.la_type.rows, "the dim of subscript must correspond to the vector dim"
        ir_node = InnerProductNode(left_info.ir, right_info.ir, sub_node, parse_info=node.parseinfo)
        ret_type = ScalarType()
        ir_node.la_type = ret_type
        node_info = NodeInfo(ret_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))
        return node_info

    def walk_FroProduct(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        assert left_info.la_type.is_vector() or left_info.la_type.is_matrix(), "left param must be vector or matrix"
        assert right_info.la_type.is_vector() or right_info.la_type.is_matrix(), "right param must be vector or matrix"
        ir_node = FroProductNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        ir_node.la_type = ScalarType()
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))

    def walk_HadamardProduct(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ir_node = HadamardProductNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        assert (left_info.la_type.is_vector() and right_info.la_type.is_vector()) or (left_info.la_type.is_matrix() and right_info.la_type.is_matrix()), "parameters must be matrix or vector"
        assert left_info.la_type.rows == left_info.la_type.rows, "dims of parameters must be the same"
        if left_info.la_type.is_matrix():
            assert left_info.la_type.cols == left_info.la_type.cols, "dims of parameters must be the same"
            ir_node.la_type = MatrixType(rows=left_info.la_type.rows, cols=left_info.la_type.rows)
        else:
            ir_node.la_type = VectorType(rows=left_info.la_type.rows)
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))

    def walk_CrossProduct(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        assert left_info.la_type.is_vector() or right_info.la_type.is_vector(), "params must be vectors"
        assert left_info.la_type.rows == 3 and right_info.la_type.rows == 3, "cross product is only for vectors of dim 3"
        ir_node = CrossProductNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        ir_node.la_type = VectorType(rows=left_info.la_type.rows)
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))

    def walk_KroneckerProduct(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ir_node = KroneckerProductNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        assert left_info.la_type.is_vector() or left_info.la_type.is_matrix(), "left param must be vector or matrix"
        assert right_info.la_type.is_vector() or right_info.la_type.is_matrix(), "right param must be vector or matrix"
        ir_node.la_type = MatrixType(rows=left_info.la_type.rows*right_info.la_type.rows, cols=left_info.la_type.cols*right_info.la_type.cols)
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))

    def walk_DotProduct(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ir_node = DotProductNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        assert left_info.la_type.is_vector() and right_info.la_type.is_vector(), "params must be vectors"
        assert left_info.la_type.rows == right_info.la_type.rows, "params must be same dimensional vectors"
        ir_node.la_type = ScalarType()
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))

    def create_power_node(self, base, power):
        power_node = PowerNode()
        power_node.base = base
        power_node.power = power
        assert power.la_type.is_scalar(), "power must be scalar"
        power_node.la_type = ScalarType()
        assert base.la_type.is_scalar() or base.la_type.is_matrix(), "base of power must be scalar or matrix"
        if base.la_type.is_matrix():
            assert base.la_type.rows == base.la_type.cols, "rows must be the same as cols"
            self.unofficial_method = True
            power_node.la_type = base.la_type
        return power_node

    def walk_Power(self, node, **kwargs):
        ir_node = PowerNode(parse_info=node.parseinfo)
        base_info = self.walk(node.base, **kwargs)
        ir_node.base = base_info.ir
        symbols = base_info.symbols
        if node.t:
            ir_node.t = node.t
            assert base_info.la_type.is_matrix() or base_info.la_type.is_vector()
            ir_node.la_type = MatrixType(rows=base_info.la_type.cols, cols=base_info.la_type.rows)
        elif node.r:
            ir_node.r = node.r
            assert base_info.la_type.is_matrix()
            assert base_info.la_type.rows == base_info.la_type.cols
            ir_node.la_type = MatrixType(rows=base_info.la_type.rows, cols=base_info.la_type.rows)
        else:
            power_info = self.walk(node.power, **kwargs)
            symbols = symbols.union(power_info.symbols)
            ir_node = self.create_power_node(base_info.ir, power_info.ir)
        node_info = NodeInfo(ir_node.la_type, symbols=symbols)
        node_info.ir = ir_node
        return node_info

    def walk_Solver(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ir_node = SolverNode(parse_info=node.parseinfo)
        ir_node.left = left_info.ir
        ir_node.right = right_info.ir
        assert left_info.la_type.is_matrix()
        assert right_info.la_type.is_matrix() or right_info.la_type.is_vector()
        node_type = None
        if left_info.la_type.is_matrix():
            assert left_info.la_type.rows == right_info.la_type.rows
            if right_info.la_type.is_matrix():
                node_type = MatrixType(rows=left_info.la_type.cols, cols=left_info.la_type.cols)
            elif right_info.la_type.is_vector():
                node_type = VectorType(rows=left_info.la_type.cols)
        ir_node.la_type = node_type
        node_info = NodeInfo(node_type, symbols=left_info.symbols.union(right_info.symbols))
        node_info.ir = ir_node
        return node_info

    def walk_Transpose(self, node, **kwargs):
        ir_node = TransposeNode(parse_info=node.parseinfo)
        f_info = self.walk(node.f, **kwargs)
        ir_node.f = f_info.ir
        assert f_info.la_type.is_matrix()
        node_type = MatrixType(rows=f_info.la_type.cols, cols=f_info.la_type.rows)
        node_info = NodeInfo(node_type, symbols=f_info.symbols)
        node_info.ir = ir_node
        node_info.la_type = node_type
        return node_info

    def walk_Function(self, node, **kwargs):
        if isinstance(node.name, str):
            ir_node = IdNode(node.name, parse_info=node.parseinfo)
            ir_node.la_type = self.symtable[node.name]
            name_info = NodeInfo(ir_node.la_type, ir=ir_node)
        else:
            name_info = self.walk(node.name, **kwargs)
        name_type = name_info.ir.la_type
        if name_type.is_function():
            ir_node = FunctionNode(parse_info=node.parseinfo)
            ir_node.name = name_info.ir
            convertion_dict = {}   # template -> instance
            param_list = []
            assert len(node.params) == len(name_type.params), "parameters count mismatch"
            symbols = set()
            for index in range(len(node.params)):
                param_info = self.walk(node.params[index], **kwargs)
                symbols = symbols.union(param_info.symbols)
                param_list.append(param_info.ir)
                if len(name_type.template_symbols) == 0:
                    assert name_type.params[index].is_same_type(param_info.ir.la_type), "parameter type mismatch"
                    continue
                if name_type.params[index].is_scalar():
                    assert name_type.params[index].is_same_type(param_info.ir.la_type), "parameter type mismatch"
                elif name_type.params[index].is_vector():
                    assert param_info.ir.la_type.is_vector()
                    if name_type.params[index].rows in name_type.template_symbols:
                        convertion_dict[name_type.params[index].rows] = param_info.ir.la_type.rows
                    else:
                        assert name_type.params[index].rows == param_info.ir.la_type.rows
                elif name_type.params[index].is_matrix():
                    assert param_info.ir.la_type.is_matrix()
                    if name_type.params[index].rows in name_type.template_symbols:
                        convertion_dict[name_type.params[index].rows] = param_info.ir.la_type.rows
                    else:
                        assert name_type.params[index].rows == param_info.ir.la_type.rows
                    #
                    if name_type.params[index].cols in name_type.template_symbols:
                        convertion_dict[name_type.params[index].cols] = param_info.ir.la_type.cols
                    else:
                        assert name_type.params[index].cols == param_info.ir.la_type.cols
            ir_node.params = param_list
            ir_node.separators = node.separators
            self.logger.debug("convertion_dict:{}".format(convertion_dict))
            ret_type = name_type.ret
            if name_type.ret.is_scalar():
                pass
            elif name_type.ret.is_vector():
                if name_type.ret.rows in name_type.template_symbols:
                    ret_type = VectorType()
                    ret_type.rows = convertion_dict[name_type.ret.rows]
            elif name_type.ret.is_matrix():
                ret_type = MatrixType()
                if name_type.ret.rows in name_type.template_symbols:
                    ret_type.rows = convertion_dict[name_type.ret.rows]
                else:
                    ret_type.rows = name_type.ret.rows
                if name_type.ret.cols in name_type.template_symbols:
                    ret_type.cols = convertion_dict[name_type.ret.cols]
                else:
                    ret_type.cols = name_type.ret.cols
            node_info = NodeInfo(ret_type, symbols=symbols)
            ir_node.la_type = ret_type
            node_info.ir = ir_node
            return node_info
        else:
            assert len(node.params) == 1, "not a function"
            return self.make_mul_info(name_info, self.walk(node.params[0], **kwargs))

    def walk_IfCondition(self, node, **kwargs):
        ir_node = IfNode(parse_info=node.parseinfo)
        kwargs[IF_COND] = True
        node_info = self.walk(node.cond, **kwargs)
        ir_node.cond = node_info.ir
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    def walk_InCondition(self, node, **kwargs):
        ir_node = InNode(parse_info=node.parseinfo)
        item_node = []
        for item in node.left:
            item_info = self.walk(item, **kwargs)
            item_node.append(item_info.ir)
        ir_node.items = item_node
        set_info = self.walk(node.right, **kwargs)
        ir_node.set = set_info.ir
        return NodeInfo(ir=ir_node)

    def walk_NotInCondition(self, node, **kwargs):
        ir_node = NotInNode(parse_info=node.parseinfo)
        item_node = []
        for item in node.left:
            item_info = self.walk(item, **kwargs)
            item_node.append(item_info.ir)
        ir_node.items = item_node
        set_info = self.walk(node.right, **kwargs)
        ir_node.set = set_info.ir
        return NodeInfo(VarTypeEnum.SCALAR, ir=ir_node)

    def walk_NeCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        left_type = left_info.la_type
        right_info = self.walk(node.right, **kwargs)
        right_type = right_info.la_type
        # assert left_type.var_type == right_type.var_type, "different type "
        return NodeInfo(ir=BinCompNode(IRNodeType.Ne, left_info.ir, right_info.ir, parse_info=node.parseinfo))

    def walk_EqCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        left_type = left_info.la_type
        right_info = self.walk(node.right, **kwargs)
        right_type = right_info.la_type
        # assert left_type.var_type == right_type.var_type, "different type "
        return NodeInfo(ir=BinCompNode(IRNodeType.Eq, left_info.ir, right_info.ir, parse_info=node.parseinfo))

    def walk_GreaterCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        return NodeInfo(ir=BinCompNode(IRNodeType.Gt, left_info.ir, right_info.ir, parse_info=node.parseinfo))

    def walk_GreaterEqualCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        return NodeInfo(ir=BinCompNode(IRNodeType.Ge, left_info.ir, right_info.ir, parse_info=node.parseinfo))

    def walk_LessCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        return NodeInfo(ir=BinCompNode(IRNodeType.Lt, left_info.ir, right_info.ir, parse_info=node.parseinfo))

    def walk_LessEqualCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        return NodeInfo(ir=BinCompNode(IRNodeType.Le, left_info.ir, right_info.ir, parse_info=node.parseinfo))

    def walk_IdentifierSubscript(self, node, **kwargs):
        right = []
        for value in node.right:
            v_info = self.walk(value)
            right.append(v_info.content)
        left_info = self.walk(node.left, **kwargs)
        return self.create_id_node_info(left_info.content, right)

    def create_id_node_info(self, left_content, right_content):
        content = left_content + '_' + ''.join(right_content)
        node_type = LaVarType(VarTypeEnum.INVALID, symbol=content)
        if left_content in self.symtable:
            node_type = self.symtable[left_content].element_type
        #
        ir_node = IdNode(left_content, right_content, parse_info=node.parseinfo)
        ir_node.la_type = node_type
        node_info = NodeInfo(node_type, content, {content}, ir_node)
        self.ids_dict[content] = Identifier(left_content, right_content)
        return node_info

    def walk_IdentifierAlone(self, node, **kwargs):
        node_type = LaVarType(VarTypeEnum.INVALID)
        if node.value:
            value = node.value
        else:
            value = '`' + node.id + '`'
        #
        ir_node = IdNode(value, parse_info=node.parseinfo)
        if value in self.symtable:
            node_type = self.symtable[value]
        node_type.symbol = value
        ir_node.la_type = node_type
        node_info = NodeInfo(node_type, value, {value}, ir_node)
        return node_info

    def walk_Factor(self, node, **kwargs):
        node_info = None
        ir_node = FactorNode(parse_info=node.parseinfo)
        if node.id:
            id0_info = self.walk(node.id, **kwargs)
            id0 = id0_info.content
            id0 = self.get_main_id(id0)
            if not la_is_inside_sum(**kwargs) and not la_is_if(**kwargs):  # symbols in sum don't need to be defined before todo:modify
                if id0 != 'I':  # special case
                    assert self.symtable.get(id0) is not None, "error: no symbol:{}".format(id0)
                    # pass  # todo:delete
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
            node_info.ir.set_parent(ir_node)
            ir_node.s = node_info.ir
        elif node.c:
            node_info = self.walk(node.c, **kwargs)
            node_info.ir.set_parent(ir_node)
            ir_node.c = node_info.ir
        #
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    def walk_Pi(self, node, **kwargs):
        node_info = NodeInfo(ScalarType())
        ir_node = ConstantNode(ConstantType.ConstantPi, parse_info=node.parseinfo)
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    def walk_Integer(self, node, **kwargs):
        value = ''.join(node.value)
        node_type = ScalarType(is_int=True)
        node_info = NodeInfo(node_type, content=int(value))
        #
        ir_node = IntegerNode(parse_info=node.parseinfo)
        ir_node.value = int(value)
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    def walk_Double(self, node, **kwargs):
        if node.f:
            node_value = self.walk(node.f, **kwargs)
        else:
            int_info = self.walk(node.i, **kwargs)
            node_value = "{}{}".format(int_info.ir.value, self.walk(node.exp, **kwargs))
        node_info = NodeInfo(ScalarType(), content=node_value)
        #
        ir_node = DoubleNode(parse_info=node.parseinfo)
        ir_node.value = node_value
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    def walk_Mantissa(self, node, **kwargs):
        content = ''.join(node.d) + '.'
        if node.f:
            content += ''.join(node.f)
        return content

    def walk_Exponent(self, node, **kwargs):
        return node.exp + ''.join(node.pow)

    def walk_Float(self, node, **kwargs):
        content = self.walk(node.m, **kwargs)
        if node.e:
            content += self.walk(node.e, **kwargs)
        return content

    def walk_SparseMatrix(self, node, **kwargs):
        ir_node = SparseMatrixNode(parse_info=node.parseinfo)
        if LHS in kwargs:
            lhs = kwargs[LHS]
        if ASSIGN_OP in kwargs:
            op = kwargs[ASSIGN_OP]
        all_ids = self.get_all_ids(lhs)
        # ifsNode
        ifs_info = self.walk(node.ifs, **kwargs)
        ifs_node = SparseIfsNode(parse_info=node.ifs.parseinfo)
        for ir in ifs_info.ir:
            ifs_node.cond_list.append(ir)
            ir.set_parent(ifs_node)
        ifs_node.set_parent(ir_node)
        ir_node.ifs = ifs_node
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
        return node_info

    def walk_SparseIfs(self, node, **kwargs):
        ir_list = []
        if node.value:
            node_info = self.walk(node.value, **kwargs)
            ir_list.append(node_info.ir)
        if node.ifs:
            node_info = self.walk(node.ifs, **kwargs)
            ir_list += node_info.ir
        ret_info = NodeInfo(ir=ir_list)
        return ret_info

    def walk_SparseIf(self, node, **kwargs):
        ir_node = SparseIfNode(parse_info=node.parseinfo)
        cond_info = self.walk(node.cond, **kwargs)
        ir_node.cond = cond_info.ir
        stat_info = self.walk(node.stat, **kwargs)
        ir_node.stat = stat_info.ir
        return NodeInfo(ir=ir_node)

    def walk_Matrix(self, node, **kwargs):
        ir_node = MatrixNode(parse_info=node.parseinfo)
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
                if col.is_matrix():
                    if col.sparse:
                        sparse = True
                    block = True
                elif col.is_vector():
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
        ir_node.la_type = node_info.la_type
        ir_node.symbol = node_info.symbol
        node_info.ir = ir_node
        return node_info

    def walk_MatrixRows(self, node, **kwargs):
        ir_node = MatrixRowsNode(parse_info=node.parseinfo)
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
        return ret_info

    def walk_MatrixRow(self, node, **kwargs):
        ir_node = MatrixRowNode(parse_info=node.parseinfo)
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
                new_type = self.type_inference(TypeInferenceEnum.INF_MATRIX_ROW, ret_info.ir, exp_info.ir)
                ret_info.la_type = new_type
                items.append(exp_info.la_type)
                ret_info.content = items
            ret_info.symbols = symbols.union(exp_info.symbols)
        ir_node.la_type = ret_info.la_type
        ret_info.ir = ir_node
        return ret_info

    def walk_MatrixRowCommas(self, node, **kwargs):
        ir_node = MatrixRowCommasNode(parse_info=node.parseinfo)
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
        return ret_info

    def walk_ExpInMatrix(self, node, **kwargs):
        ret_info = self.walk(node.value, **kwargs)
        ir_node = ExpInMatrixNode(parse_info=node.parseinfo)
        ir_node.value = ret_info.ir
        ir_node.sign = node.sign
        ret_info.ir = ir_node
        return ret_info

    def walk_NumMatrix(self, node, **kwargs):
        ir_node = NumMatrixNode(parse_info=node.parseinfo)
        id1_info = self.walk(node.id1, **kwargs)
        ir_node.id1 = id1_info.ir
        id1_info.ir.set_parent(ir_node)
        id1 = id1_info.content
        if node.id:
            ir_node.id = node.id
            if 'I' in self.symtable and self.symtable['I'].is_sequence():
                # I_i, sequence
                return self.create_id_node_info('I', [id1])
            if isinstance(id1, str):
                assert id1 in self.symtable, "{} unknown".format(id1)
            # 'I' symbol
            assert 'I' not in self.symtable, "You can't use 'I' with subscript since it has been defined before"
            node_type = MatrixType(rows=id1, cols=id1)
        else:
            if isinstance(id1, str):
                assert id1 in self.symtable, "{} unknown".format(id1)
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
        return node_info

    def create_math_node_info(self, func_type, param_info, remains=[]):
        param = param_info.ir
        symbols = param_info.symbols
        remain_list = []
        if MathFuncType.MathFuncInvalid < func_type < MathFuncType.MathFuncAtan2:
            assert param.la_type.is_scalar() or param.la_type.is_matrix() or param.la_type.is_vector(), "Parameters must be scalar, vector or matrix type"
        else:
            assert param.la_type.is_scalar(), "Parameters must be scalar type"
            for par_info in remains:
                par = par_info.ir
                remain_list.append(par)
                assert par.la_type.is_scalar(), "Parameters must be scalar type"
                symbols = symbols.union(par_info.symbols)
        tri_node = MathFuncNode(param, func_type, remain_list, parse_info=node.parseinfo)
        node_info = NodeInfo(param.la_type, symbols=symbols)
        tri_node.la_type = param.la_type
        node_info.ir = tri_node
        return node_info

    def create_trig_node_info(self, func_type, param_info, power):
        symbols = param_info.symbols
        param = param_info.ir
        if power:
            assert param.la_type.is_scalar(), "Parameters must be scalar type for the power"
            power_info = self.walk(power)
            symbols = symbols.union(power_info.symbols)
            math_info = self.create_math_node_info(func_type, param_info)
            ir_node = self.create_power_node(math_info.ir, power_info.ir)
            return NodeInfo(ir_node.la_type, ir=ir_node, symbols=symbols)
        else:
            return self.create_math_node_info(func_type, param_info)

    def walk_SinFunc(self, node, **kwargs):
        return self.create_trig_node_info(MathFuncType.MathFuncSin, self.walk(node.param, **kwargs), node.power)

    def walk_AsinFunc(self, node, **kwargs):
        node_info = self.create_trig_node_info(MathFuncType.MathFuncAsin, self.walk(node.param, **kwargs), node.power)
        node_info.ir.func_name = node.name
        return node_info

    def walk_CosFunc(self, node, **kwargs):
        return self.create_trig_node_info(MathFuncType.MathFuncCos, self.walk(node.param, **kwargs), node.power)

    def walk_AcosFunc(self, node, **kwargs):
        node_info = self.create_trig_node_info(MathFuncType.MathFuncAcos, self.walk(node.param, **kwargs), node.power)
        node_info.ir.func_name = node.name
        return node_info

    def walk_TanFunc(self, node, **kwargs):
        return self.create_trig_node_info(MathFuncType.MathFuncTan, self.walk(node.param, **kwargs), node.power)

    def walk_AtanFunc(self, node, **kwargs):
        node_info = self.create_trig_node_info(MathFuncType.MathFuncAtan, self.walk(node.param, **kwargs), node.power)
        node_info.ir.func_name = node.name
        return node_info

    def walk_SinhFunc(self, node, **kwargs):
        return self.create_trig_node_info(MathFuncType.MathFuncSinh, self.walk(node.param, **kwargs), node.power)

    def walk_AsinhFunc(self, node, **kwargs):
        node_info = self.create_trig_node_info(MathFuncType.MathFuncAsinh, self.walk(node.param, **kwargs), node.power)
        node_info.ir.func_name = node.name
        return node_info

    def walk_CoshFunc(self, node, **kwargs):
        return self.create_trig_node_info(MathFuncType.MathFuncCosh, self.walk(node.param, **kwargs), node.power)

    def walk_AcoshFunc(self, node, **kwargs):
        node_info = self.create_trig_node_info(MathFuncType.MathFuncAcosh, self.walk(node.param, **kwargs), node.power)
        node_info.ir.func_name = node.name
        return node_info

    def walk_TanhFunc(self, node, **kwargs):
        return self.create_trig_node_info(MathFuncType.MathFuncTanh, self.walk(node.param, **kwargs), node.power)

    def walk_AtanhFunc(self, node, **kwargs):
        node_info = self.create_trig_node_info(MathFuncType.MathFuncAtanh, self.walk(node.param, **kwargs), node.power)
        node_info.ir.func_name = node.name
        return node_info

    def walk_CotFunc(self, node, **kwargs):
        return self.create_trig_node_info(MathFuncType.MathFuncCot, self.walk(node.param, **kwargs), node.power)

    def walk_SecFunc(self, node, **kwargs):
        return self.create_trig_node_info(MathFuncType.MathFuncSec, self.walk(node.param, **kwargs), node.power)

    def walk_CscFunc(self, node, **kwargs):
        return self.create_trig_node_info(MathFuncType.MathFuncCsc, self.walk(node.param, **kwargs), node.power)

    # other math node
    def walk_Atan2Func(self, node, **kwargs):
        node_info = self.create_math_node_info(MathFuncType.MathFuncAtan2, self.walk(node.param, **kwargs), [self.walk(node.second, **kwargs)])
        node_info.ir.separator = node.separator
        return node_info

    def walk_ExpFunc(self, node, **kwargs):
        return self.create_math_node_info(MathFuncType.MathFuncExp, self.walk(node.param, **kwargs))

    def walk_LogFunc(self, node, **kwargs):
        return self.create_math_node_info(MathFuncType.MathFuncLog, self.walk(node.param, **kwargs))

    def walk_LnFunc(self, node, **kwargs):
        return self.create_math_node_info(MathFuncType.MathFuncLn, self.walk(node.param, **kwargs))

    def walk_SqrtFunc(self, node, **kwargs):
        return self.create_math_node_info(MathFuncType.MathFuncSqrt, self.walk(node.param, **kwargs))

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
                if type_array[i][j].is_matrix() or type_array[i][j].is_vector():
                    if type_array[i][j].is_matrix():
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

    def type_inference(self, op, left_info, right_info):
        left_type = left_info.la_type
        right_type = right_info.la_type
        # todo:delete
        if left_type.var_type == VarTypeEnum.INVALID:
            left_type.var_type = VarTypeEnum.SCALAR
        if right_type.var_type == VarTypeEnum.INVALID:
            right_type.var_type = VarTypeEnum.SCALAR
        # error msg
        left_line = left_info.parse_info.buffer.line_info(left_info.parse_info.pos)
        right_line = right_info.parse_info.buffer.line_info(right_info.parse_info.pos)
        error_msg = '{}. Dimension mismatch. Can\'t {} {} {} and {} {}.\n'.format(self.la_msg.get_line_desc(left_line),
                                                                            self.get_op_desc(op),
                                                                            self.get_type_desc(left_type),
                                                                            left_info.parse_info.buffer.text[left_info.parse_info.pos:left_info.parse_info.endpos],
                                                                            self.get_type_desc(right_type),
                                                                                  right_info.parse_info.buffer.text[right_info.parse_info.pos:right_info.parse_info.endpos])
        error_msg += left_line.text
        error_msg += self.la_msg.get_pos_marker(left_line.col)
        ret_type = None
        if op == TypeInferenceEnum.INF_ADD or op == TypeInferenceEnum.INF_SUB:
            ret_type = left_type  # default type
            if left_type.is_scalar():
                assert right_type.is_scalar(), error_msg
            elif left_type.is_matrix():
                assert right_type.is_matrix() or right_type.is_vector(), error_msg
                assert left_type.rows == right_type.rows and left_type.cols == right_type.cols, error_msg
                if right_type.is_matrix() and right_type.sparse:
                    ret_type.sparse = True
            elif left_type.is_vector():
                assert right_type.is_matrix() or right_type.is_vector(), error_msg
                assert left_type.rows == right_type.rows and left_type.cols == right_type.cols, error_msg
                if right_type.is_matrix():
                    ret_type = right_type
            else:
                # sequence et al.
                assert left_type.var_type == right_type.var_type, error_msg
        elif op == TypeInferenceEnum.INF_MUL:
            assert left_type.var_type != VarTypeEnum.SEQUENCE and right_type.var_type != VarTypeEnum.SEQUENCE, 'error: sequence can not be operated'
            if left_type.is_scalar():
                ret_type = right_type
            elif left_type.is_matrix():
                if right_type.is_scalar():
                    ret_type = left_type
                elif right_type.is_matrix():
                    assert left_type.cols == right_type.rows, error_msg
                    ret_type = MatrixType(rows=left_type.rows, cols=right_type.cols)
                    if left_type.sparse and right_type.sparse:
                        ret_type.sparse = True
                elif right_type.is_vector():
                    assert left_type.cols == right_type.rows, error_msg
                    if left_type.rows == 1:
                        # scalar
                        ret_type = ScalarType()
                    else:
                        ret_type = VectorType(rows=left_type.rows)
            elif left_type.is_vector():
                if right_type.is_scalar():
                    ret_type = left_type
                elif right_type.is_matrix():
                    assert 1 == right_type.rows, error_msg
                    ret_type = MatrixType(rows=left_type.rows, cols=right_type.cols)
                elif right_type.is_vector():
                    assert left_type.cols == right_type.rows, error_msg
        elif op == TypeInferenceEnum.INF_DIV:
            # assert left_type.is_scalar() and right_type.is_scalar(), error_msg
            assert left_type.is_scalar() or left_type.is_vector() or left_type.is_matrix(), error_msg
            assert right_type.is_scalar(), error_msg
            ret_type = left_type
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
        if len(res) == 1:
            return res
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
