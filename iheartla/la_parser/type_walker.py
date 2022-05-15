import copy
from tatsu.model import NodeWalker
from tatsu.objectmodel import Node
from .la_types import *
from ..la_tools.la_logger import *
from ..la_tools.la_msg import *
from ..la_tools.la_helper import *
import regex as re
from ..la_tools.la_helper import filter_subscript

## Make the visualizer
try: from ..la_tools.la_visualizer import LaVisualizer
except ImportError:
    # if DEBUG_MODE:
    #     print( "Skipping visualizer." )
    class LaVisualizer(object):
        def visualize(self, node): pass

from .ir import *
from .la_data import *
from enum import Enum, IntFlag


class TypeInferenceEnum(Enum):
    INF_ADD = 0
    INF_SUB = 1
    INF_MUL = 2
    INF_DIV = 3
    INF_MATRIX_ROW = 4


class WalkTypeEnum(Enum):
    RETRIEVE_EXPRESSION = 0   # default
    RETRIEVE_VAR = 1

class DependenceData(object):
    def __init__(self, module='', initialized_list=[], name_list=[]):
        self.module = module
        self.name_list = name_list
        self.initialized_list = initialized_list


class EquationData(object):
    def __init__(self, name='', parameters=[], definition=[], dependence=[], symtable={}, desc_dict={}, la_content='', func_data_dict={}, expr_dict={}):
        self.name = name
        self.undescribed_list = []
        self.parameters = parameters  # parameters for source file
        self.definition = definition  # lhs symbols
        self.dependence = dependence
        self.symtable = symtable
        self.desc_dict = desc_dict
        self.la_content = la_content
        self.func_data_dict = func_data_dict
        self.expr_dict = {}
        # for key in self.desc_dict.keys():
        #     self.desc_dict[key] = self.desc_dict[key].replace('"', '\"')
        # remove subscript in symbol
        for key, value in expr_dict.items():
            self.expr_dict[key] = [filter_subscript(val) for val in value]
        # gather all symbols: params, definitions, local func names, local params
        self.sym_list = list(self.parameters) + list(self.definition)
        for key, value in self.func_data_dict.items():
            self.sym_list.append(key)
            self.sym_list += list(value.params_data.symtable.keys())
        for dep_data in self.dependence:
            self.sym_list += dep_data.name_list
        self.sym_list = list(set(self.sym_list))

    def gen_sym_list(self):
        sym_list = copy.deepcopy(self.sym_list)
        sym_list = [sym.replace('`$', '').replace('$`', '').replace('`', '') for sym in sym_list]
        return sorted(list(set(sym_list)), key=len, reverse=True)

    def trim(self, content):
        # print("before:{}, after:{}".format(content, content.replace('"', '\\"').replace("'", "\\'")))
        content = content.replace('"', '\\"').replace("'", "\\'")
        return content

    def gen_json_content(self):
        content = ''
        undesc_list = ['''"{}"'''.format(self.trim(sym)) for sym in self.undescribed_list]
        param_list = []
        for param in self.parameters:
            if param in self.desc_dict:
                param_list.append('''{{"sym":"{}", "type_info":{}, "desc":"{}"}}'''.format(self.trim(param), self.symtable[param].get_json_content(), self.desc_dict[param].replace('"', '\\"').replace("'", "\\'")))
            else:
                param_list.append('''{{"sym":"{}", "type_info":{}}}'''.format(self.trim(param), self.symtable[param].get_json_content()))
        def_list = []
        for lhs in self.definition:
            if lhs in self.desc_dict:
                def_list.append('''{{"sym":"{}", "type_info":{}, "desc":"{}"}}'''.format(self.trim(lhs), self.symtable[lhs].get_json_content(), self.desc_dict[lhs].replace('"', '\\"').replace("'", "\\'")))
            else:
                def_list.append('''{{"sym":"{}", "type_info":{}}}'''.format(self.trim(lhs), self.symtable[lhs].get_json_content()))
        # module dependence, get the sym info
        dependence_list = []
        for dep_data in self.dependence:
            sym_list = []
            init_list = []
            for param in dep_data.initialized_list:
                init_list.append('"{}"'.format(param))
            for sym in dep_data.name_list:
                if sym in self.desc_dict:
                    sym_list.append('''{{"sym":"{}", "type_info":{}, "desc":"{}"}}'''.format(self.trim(sym),
                                                                                             self.symtable[
                                                                                                 sym].get_json_content(),
                                                                                             self.desc_dict[
                                                                                                 sym].replace('"',
                                                                                                              '\\"').replace("'", "\\'")))
                else:
                    sym_list.append('''{{"sym":"{}", "type_info":{}}}'''.format(self.trim(sym),
                                                                                self.symtable[sym].get_json_content()))
            dependence_list.append('''{{"module":"{}", "syms":[{}], "initialization":[{}]}}'''.format(dep_data.module, ','.join(sym_list), ','.join(init_list)))
        #
        func_list = []
        for k, v in self.func_data_dict.items():
            if k in self.desc_dict:
                def_list.append('''{{"sym":"{}", "type_info":{}, "desc":"{}"}}'''.format(self.trim(k), self.symtable[k].get_json_content(), self.desc_dict[k].replace('"', '\\"').replace("'", "\\'")))
            else:
                def_list.append('''{{"sym":"{}", "type_info":{}}}'''.format(self.trim(k), self.symtable[k].get_json_content()))
            local_param_list = []
            for local_param in v.params_data.parameters:
                if local_param in self.desc_dict:
                    local_param_list.append('''{{"sym":"{}", "type_info":{}, "desc":"{}"}}'''.format(self.trim(local_param), v.params_data.symtable[local_param].get_json_content(), self.desc_dict[local_param].replace('"', '\\"').replace("'", "\\'")))
                else:
                    local_param_list.append('''{{"sym":"{}", "type_info":{}}}'''.format(self.trim(local_param), v.params_data.symtable[local_param].get_json_content()))
            func_list.append('''{{"name":"{}", "parameters":[{}]}}'''.format(self.trim(k), ','.join(local_param_list)))
        # self.la_content = self.la_content.replace('\n', '\\\\n')
        content = '''"parameters":[{}], "definition":[{}], "local_func":[{}], "dependence":[{}], "undesc_list":[{}]'''.format(','.join(param_list), ','.join(def_list), ','.join(func_list), ','.join(dependence_list), ','.join(undesc_list))
        content = content.replace('\\', '\\\\\\\\')
        content = content.replace('\n', '\\\\n')
        content = content.replace('`', '')
        content = content.replace('\\\\\\\\"', '\\\\"')
        content = content.replace("\\\\\\\\'", "\\\\'")
        # print("content:{}".format(content))
        # content += ''', "source":"{}"'''.format(self.trim(self.la_content).replace('\\', '\\\\\\\\').replace('\n', '\\\\n'))   # IHLA source code
        return content


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
        self.tmp_symtable = {}  # temporary variables in integral or optimization
        self.parameters = []
        self.name_cnt_dict = {}
        self.def_use_mode = True
        self.unofficial_method = False
        self.has_opt = False
        self.is_param_block = False  # where or given block
        self.visualizer = LaVisualizer()
        self.logger = LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT)
        self.la_msg = LaMsg.getInstance()
        self.ret_symbol = None
        self.packages = {'trigonometry': ['sin', 'asin', 'arcsin', 'cos', 'acos', 'arccos', 'tan', 'atan', 'arctan', 'atan2',
                                          'sinh', 'asinh', 'arsinh', 'cosh', 'acosh', 'arcosh', 'tanh', 'atanh', 'artanh', 'cot',
                                          'sec', 'csc', 'e'],
                         'linearalgebra': ['trace', 'tr', 'diag', 'vec', 'det', 'rank', 'null', 'orth', 'inv']}
        self.constants = ['π']
        self.pattern = re.compile("[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*")
        self.multi_lhs_list = []
        self.lhs_list = []
        # self.directive_parsing = True   # directives grammar
        self.sum_subs = []
        self.sum_sym_list = []
        self.lhs_subs = []
        self.lhs_sym_list = []
        self.sum_conds = []
        self.la_content = ''
        self.lhs_sub_dict = {}  # dict of the same subscript symbol from rhs as the subscript of lhs
        self.visiting_lhs = False
        self.dyn_dim = False
        self.pre_walk = False
        # self.arith_dim_list = []
        self.rhs_raw_str_list = []
        self.dependency_set = set()
        self.dependency_dim_dict = {}
        #
        self.local_func_syms = []  # local function names
        self.local_func_pars = []  # parameters for local functions
        self.local_func_parsing = False
        self.local_func_name = ''  # function name when visiting expressions
        self.local_func_dict = {}  # local function name -> parameter dict
        self.visiting_opt = False  # optimization
        self.opt_cur_init_list = [] # initialized vars
        self.opt_key = ''
        self.opt_dict = {}
        self.func_data_dict = {}   # local function name -> LocalFuncData
        #
        self.desc_dict = {}        # comment for parameters
        self.import_module_list = []
        self.main_param = ParamsData()
        self.used_params = []
        self.expr_dict = {}        # lhs id -> symbols in current expr

    def get_cur_param_data(self):
        # either main where/given block or local function block
        if self.local_func_parsing:
            if self.local_func_name in self.func_data_dict:
                return self.func_data_dict[self.local_func_name].params_data
            else:
                assert True, "error"
        elif self.visiting_opt:
            if self.opt_key in self.opt_dict:
                self.copy_data_to_opt()
                return self.opt_dict[self.opt_key]
            else:
                assert True, "error"
        self.main_param.symtable = self.symtable
        return self.main_param

    def copy_data_to_opt(self):
        for key, paramData in self.opt_dict.items():
            paramData.symtable.update(self.main_param.symtable)

    def filter_symbol(self, symbol):
        if '`' in symbol:
            new_symbol = symbol.replace('`', '')
            if not self.pattern.fullmatch(new_symbol) or is_keyword(new_symbol):
                new_symbol = symbol
        else:
            new_symbol = symbol
        return new_symbol

    def gen_json_content(self):
        return EquationData('', copy.deepcopy(self.parameters), copy.deepcopy(self.lhs_list),
                            copy.deepcopy(self.import_module_list),  copy.deepcopy(self.symtable),
                            copy.deepcopy(self.desc_dict), self.la_content,
                            copy.deepcopy(self.func_data_dict), copy.deepcopy(self.expr_dict))

    def is_inside_sum(self):
        return len(self.sum_subs) > 0

    def reset(self):
        self.reset_state()

    def reset_state(self, la_content=''):
        self.symtable.clear()
        self.tmp_symtable.clear()
        self.parameters.clear()
        self.name_cnt_dict.clear()
        self.ret_symbol = None
        self.unofficial_method = False
        self.has_opt = False
        self.sum_subs.clear()
        self.sum_sym_list.clear()
        self.lhs_subs.clear()
        self.lhs_sym_list.clear()
        self.sum_conds.clear()
        self.lhs_list.clear()
        self.la_content = la_content
        # self.same_dim_list.clear()
        self.rhs_raw_str_list.clear()
        # self.arith_dim_list.clear()
        self.dependency_set.clear()
        self.dependency_dim_dict.clear()
        self.local_func_syms.clear()
        self.local_func_pars.clear()
        self.local_func_parsing = False
        self.local_func_name = ''
        self.local_func_dict.clear()
        self.opt_dict.clear()
        self.func_data_dict.clear()
        self.desc_dict.clear()
        self.import_module_list.clear()
        self.main_param.reset()
        self.used_params.clear()
        self.expr_dict.clear()
        self.visiting_opt = False
        self.visiting_lhs = False
        self.opt_key = ''

    def get_func_symbols(self):
        ret = {}
        seq_func_list = []
        for keys in self.symtable:
            if self.symtable[keys]:
                if self.symtable[keys].is_function():
                    ret[keys] = self.symtable[keys].get_signature()
                elif self.symtable[keys].is_sequence() and self.symtable[keys].element_type.is_function():
                    seq_func_list.append(keys)
        # func parameters for local function
        tmp_sym_dict = {}
        for k, v in self.local_func_dict.items():
            if len(v) > 0:
                for sym, ty in v.items():
                    if ty.is_function():
                        seq_func_list.append(sym)
                        tmp_sym_dict[sym] = ty
        #
        rhs_str = '\n'.join(self.rhs_raw_str_list)
        for seq in seq_func_list:
            # special usage of ?:
            results = re.findall(r"("
                                 + seq + r"_`[^`]*`|"
                                 + seq + r"_[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*(?:[A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*|"
                                 + seq + r"_\d*)(?=\()", rhs_str)
            if seq in self.symtable:
                sig = self.symtable[seq].get_signature()
            else:
                sig = tmp_sym_dict[seq].get_signature()
            for match in results:
                ret[match] = sig + match
        for sym in self.local_func_syms:
            ret[sym] = "localF;" + sym
        for sym in tmp_sym_dict:
            ret[sym] = "localFP;" + sym
        return ret

    def generate_var_name(self, base):
        index = -1
        if base in self.name_cnt_dict:
            index = self.name_cnt_dict[base]
        index += 1
        valid = False
        ret = ""
        while not valid:
            # ret = "_{}_{}".format(base, index)
            ret = "{}_{}".format(base, index)
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

    def get_line_desc(self, node):
        # ir node
        line_info = get_parse_info_buffer(node.parse_info).line_info(node.parse_info.pos)
        return self.la_msg.get_line_desc(line_info)

    def get_node_col(self, node):
        return get_parse_info_buffer(node.parse_info).line_info(node.parse_info.pos).col

    def get_text_pos_marker(self, node):
        # ir node
        line_info = get_parse_info_buffer(node.parse_info).line_info(node.parse_info.pos)
        raw_text = line_info.text
        if raw_text[-1] != '\n':
            raw_text += '\n'
        return "{}{}".format(raw_text, self.la_msg.get_pos_marker(line_info.col))

    def get_sym_type(self, sym):
        """
        get la type by considering local function
        :param sym: symbol name
        :return: la type
        """
        node_type = LaVarType(VarTypeEnum.INVALID)
        resolved = False
        if self.local_func_parsing:
            if self.local_func_name in self.local_func_dict and sym in self.local_func_dict[self.local_func_name]:
                node_type = self.local_func_dict[self.local_func_name][sym]
                resolved = True
        if not resolved:
            if sym in self.symtable:
                node_type = self.symtable[sym]
        return node_type

    def is_sym_existed(self, sym):
        existed = False
        if self.local_func_parsing:
            if self.local_func_name in self.local_func_dict and sym in self.local_func_dict[self.local_func_name]:
                existed = True
        if not existed:
            if sym in self.symtable:
                existed = True
        return existed

    def check_sym_existence(self, sym, msg, existed=True):
        """
        :param sym: symbol name
        :param msg: error message
        :param existed: the symbol should exist or not
        :return:
        """
        resolved = False
        if existed:
            # should exist
            if self.local_func_parsing:
                if self.local_func_name in self.local_func_dict and sym in self.local_func_dict[self.local_func_name]:
                    resolved = True
            if self.visiting_opt:
                if self.opt_key in self.opt_dict and sym in self.opt_dict[self.opt_key].symtable:
                    resolved = True
            if not resolved:
                assert self.symtable.get(sym) is not None, msg
        else:
            # shouldn't exist
            if self.local_func_parsing:
                # only need to check local parameters
                if self.local_func_name in self.local_func_dict and sym in self.local_func_dict[self.local_func_name]:
                    resolved = True
                assert not resolved, msg
                return
            if self.visiting_opt:
                if self.opt_key in self.opt_dict and sym in self.opt_dict[self.opt_key].symtable:
                    resolved = True
            if not resolved:
                assert self.symtable.get(sym) is None, msg
            else:
                if self.visiting_opt and sym in self.opt_cur_init_list:
                    return
                assert False, msg

    def walk_Node(self, node):
        print('Reached Node: ', node)

    def walk_object(self, o):
        raise Exception('Unexpected type %s walked', type(o).__name__)

    def walk_Start(self, node, **kwargs):
        self.main_param.symtable = self.symtable
        self.pre_walk = True if 'pre_walk' in kwargs else False
        # self.symtable.clear()
        self.visualizer.visualize(node)  # visualize
        ir_node = StartNode(parse_info=node.parseinfo)
        # if node.directive:
        #     for directive in node.directive:
        #         ir_node.directives.append(self.walk(directive, **kwargs))
        # vblock
        vblock_list = []
        multi_lhs_list = []
        raw_param_list = []  # handle params first
        self.rhs_raw_str_list.clear()
        for vblock in node.vblock:
            if type(vblock).__name__ == 'ParamsBlock':
                raw_param_list.append(vblock)
        param_ir_list = self.extract_all_params(raw_param_list)
        #
        param_ir_index = 0
        for vblock in node.vblock:
            if type(vblock).__name__ == 'ParamsBlock':
                vblock_info = param_ir_list[param_ir_index]
                param_ir_index += 1
            elif type(vblock).__name__ == 'Import':
                directive_node = self.walk(vblock, **kwargs)
                ir_node.directives.append(directive_node)
                vblock_list.append(directive_node)
                continue
            else:
                vblock_info = self.walk(vblock, **kwargs)
            vblock_list.append(vblock_info)
            if isinstance(vblock_info, list) and len(vblock_info) > 0:  # statement list with single statement
                if type(vblock_info[0]).__name__ == 'Assignment':
                    for cur_index in range(len(vblock_info[0].left)):
                        if type(vblock_info[0].left[cur_index]).__name__ == 'IdentifierSubscript':
                            lhs_sym = self.walk(vblock_info[0].left[cur_index].left).ir.get_main_id()
                        else:
                            lhs_sym = self.walk(vblock_info[0].left[cur_index]).ir.get_main_id()
                        if lhs_sym not in self.lhs_list:
                            self.lhs_list.append(lhs_sym)
                        if len(lhs_sym) > 1:
                            multi_lhs_list.append(lhs_sym)
                        for cur_expr in vblock_info[0].right:
                            self.rhs_raw_str_list.append(cur_expr.text)
                elif type(vblock_info[0]).__name__ == 'LocalFunc':
                    if isinstance(vblock_info[0].name, str):
                        func_sym = vblock_info[0].name
                    else:
                        func_sym = self.walk(vblock_info[0].name).ir.get_main_id()
                    self.local_func_dict[func_sym] = {}
                    self.func_data_dict[func_sym] = LocalFuncData(name=func_sym)
                    self.local_func_syms.append(func_sym)
                    if self.pre_walk:
                        self.local_func_parsing = True
                        self.local_func_name = func_sym
                        if len(func_sym) > 1:
                            multi_lhs_list.append(func_sym)
                        self.is_param_block = True
                        for par_def in vblock_info[0].defs:
                            par_type = self.walk(par_def, **kwargs)
                            type_dict = par_type.get_type_dict()
                            self.local_func_dict[func_sym].update(type_dict)
                        self.local_func_parsing = False
                        self.is_param_block = False
                    for cur_expr in vblock_info[0].expr:
                        self.rhs_raw_str_list.append(cur_expr.text)
                else:
                    self.rhs_raw_str_list.append(vblock_info[0].text)
        ir_node.vblock = vblock_list
        params_list, stat_list, index_list = ir_node.get_block_list()
        # check function assignment
        if self.pre_walk:
            for index in range(len(stat_list)):
                if type(stat_list[index]).__name__ == 'Assignment':
                    # check whether rhs is function type
                    if type(stat_list[index].right).__name__ == 'Expression' and type(stat_list[index].right.value).__name__ == 'Factor' and stat_list[index].right.value.id0:
                        # specific stat: lhs = id_subs
                        try:
                            assign_node = self.walk(stat_list[index], **kwargs).ir
                            lhs_id_node = assign_node.left
                            rhs_id_node = assign_node.right.value.id
                            if rhs_id_node.la_type.is_function():
                                if lhs_id_node.contain_subscript():
                                    assert lhs_id_node.node_type == IRNodeType.SequenceIndex, get_err_msg_info(lhs_id_node.parseinfo, "Invalid assignment for function")
                        except AssertionError as e:
                            # lhs = symbol
                            continue
                elif type(stat_list[index]).__name__ == 'LocalFunc':
                    # local function defition
                    pass
        #
        self.multi_lhs_list = multi_lhs_list
        if self.pre_walk:
            return ir_node
        self.gen_block_node(stat_list, index_list, ir_node, **kwargs)
        # set properties
        self.main_param.parameters = self.parameters
        self.main_param.symtable = self.symtable
        return ir_node

    def push_environment(self):
        # save variable changes when parsing *expressions*
        self.saved_symtable = copy.deepcopy(self.symtable)
        self.saved_sum_subs = copy.deepcopy(self.sum_subs)
        self.saved_sum_sym_list = copy.deepcopy(self.sum_sym_list)
        self.saved_lhs_subs = copy.deepcopy(self.lhs_subs)
        self.saved_lhs_sym_list = copy.deepcopy(self.lhs_sym_list)
        self.saved_sum_conds = copy.deepcopy(self.sum_conds)
        self.saved_lhs_sub_dict = copy.deepcopy(self.lhs_sub_dict)
        #
        self.saved_func_data_dict = copy.deepcopy(self.func_data_dict)
        self.saved_local_func_dict = copy.deepcopy(self.local_func_dict)
        self.saved_used_params = copy.deepcopy(self.used_params)
        self.saved_opt_dict = copy.deepcopy(self.opt_dict)

    def pop_environment(self):
        self.symtable = self.saved_symtable
        self.sum_subs = self.saved_sum_subs
        self.sum_sym_list = self.saved_sum_sym_list
        self.lhs_subs = self.saved_lhs_subs
        self.sum_conds = self.saved_sum_conds
        self.lhs_sub_dict = self.saved_lhs_sub_dict
        self.local_func_dict = self.saved_local_func_dict
        self.func_data_dict = self.saved_func_data_dict
        self.opt_dict = self.saved_opt_dict
        self.used_params = self.saved_used_params
        self.local_func_parsing = False
        self.is_param_block = False

    def gen_block_node(self, stat_list, index_list, ir_node, **kwargs):
        block_node = BlockNode()
        if self.def_use_mode:
            new_list = []
            order_list = [-1] * len(stat_list)  # visited order for all statment
            cnt = 0
            retries = 0
            while cnt < len(stat_list):
                visited_list = [False] * len(stat_list)
                for cur_index in range(len(stat_list)):
                    if order_list[cur_index] == -1 and not visited_list[cur_index]:
                        cur_stat = stat_list[cur_index]
                        self.logger.debug("tried stat:{}, retries:{}".format(cur_stat.text, retries))
                        # try to parse
                        self.push_environment()
                        try:
                            update_ret_type = False
                            if cur_index == len(stat_list) - 1:
                                # last statment
                                if type(cur_stat).__name__ == 'Assignment':
                                    kwargs[SET_RET_SYMBOL] = True
                                elif type(cur_stat).__name__ != 'LocalFunc' and type(cur_stat).__name__ != 'MultiCondExpr':
                                    # new symbol for return value
                                    self.ret_symbol = "ret"
                                    update_ret_type = True
                                    kwargs[LHS] = self.ret_symbol
                                    self.lhs_list.append(self.ret_symbol)
                            type_info = self.walk(cur_stat, **kwargs)
                            ir_node.vblock[index_list[cur_index]] = type_info.ir  # latex use
                            new_list.append(type_info.ir)
                            if update_ret_type:
                                self.symtable[self.ret_symbol] = type_info.la_type
                            order_list[cur_index] = cnt
                            cnt += 1
                            retries = 0
                            self.logger.debug("expr index:{}, stat:{}".format(cnt, cur_stat.text))
                            break
                        except AssertionError as e:
                            retries += 1
                            visited_list[cur_index] = True
                            if retries > len(stat_list):
                                raise e
                            # parse failed, pop saved env
                            self.pop_environment()
                            continue
            block_node.stmts = new_list
        else:
            # previous version
            for index in range(len(stat_list)):
                update_ret_type = False
                if index == len(stat_list) - 1:
                    if type(stat_list[index]).__name__ == 'Assignment':
                        kwargs[SET_RET_SYMBOL] = True
                    elif type(stat_list[index]).__name__ != 'LocalFunc' and type(stat_list[index]).__name__ != 'MultiCondExpr':
                        # new symbol for return value
                        self.ret_symbol = "ret"
                        update_ret_type = True
                        kwargs[LHS] = self.ret_symbol
                        self.lhs_list.append(self.ret_symbol)
                type_info = self.walk(stat_list[index], **kwargs)
                ir_node.vblock[index_list[index]] = type_info.ir  # latex use
                block_node.add_stmt(type_info.ir)
                if update_ret_type:
                    self.symtable[self.ret_symbol] = type_info.la_type
        ir_node.stat = block_node

    ###################################################################
    def extract_all_params(self, raw_param_list, **kwargs):
        self.is_param_block = True
        self.dependency_set.clear()
        param_ir_list = []
        total_list = []  # all lines of params
        total_map = []
        #
        ir_index = []  # matrix, vector
        param_index = []
        func_index = []  # function
        func_param_index = []
        scalar_index = []
        scalar_param_index = []
        #
        cur_param_index = 0
        cur_line_index = 0  # line of params
        for raw_block_index in range(len(raw_param_list)):
            raw_param_node = raw_param_list[raw_block_index]
            where_conds = WhereConditionsNode(parse_info=raw_param_node.conds.parseinfo)
            where_conds.value = [None] * len(raw_param_node.conds.value)
            ir_node = ParamsBlockNode(parse_info=raw_param_node.parseinfo, annotation=raw_param_node.annotation,
                                      conds=where_conds)
            param_ir_list.append(ir_node)
            for i in range(len(raw_param_node.conds.value)):
                if type(raw_param_node.conds.value[i].type).__name__ == "ScalarType" or type(
                        raw_param_node.conds.value[i].type).__name__ == "SetType":
                    scalar_index.append(i+cur_line_index)
                    scalar_param_index.append(cur_param_index)
                elif type(raw_param_node.conds.value[i].type).__name__ == "FunctionType":
                    func_index.append(i+cur_line_index)
                    func_param_index.append(cur_param_index)
                else:
                    ir_index.append(i+cur_line_index)
                    param_index.append(cur_param_index)
                cur_param_index += len(raw_param_node.conds.value[i].id)
                total_list.append(raw_param_node.conds.value[i])
                total_map.append((raw_block_index, i))
            cur_line_index += len(raw_param_node.conds.value)
        self.parameters = [None] * cur_param_index
        # walk scalar first
        if len(scalar_index) > 0:
            for i in range(len(scalar_index)):
                kwargs[PARAM_INDEX] = scalar_param_index[i]
                total_list[scalar_index[i]] = self.walk(total_list[scalar_index[i]], **kwargs)
        # matrix, vector nodes
        if len(ir_index) > 0:
            for i in range(len(ir_index)):
                kwargs[PARAM_INDEX] = param_index[i]
                total_list[ir_index[i]] = self.walk(total_list[ir_index[i]], **kwargs)
        # func nodes:
        if len(func_index) > 0:
            for i in range(len(func_index)):
                kwargs[PARAM_INDEX] = func_param_index[i]
                total_list[func_index[i]] = self.walk(total_list[func_index[i]], **kwargs)
        # set ir back
        for i in range(len(total_list)):
            ir_index, cond_index = total_map[i]
            param_ir_list[ir_index].conds.value[cond_index] = total_list[i]
        if not self.pre_walk:
            for cur_set in self.dependency_set:
                assert cur_set in self.symtable, get_err_msg_info(self.dependency_dim_dict[cur_set], "Symbol {} not defined".format(cur_set))
        self.is_param_block = False
        return param_ir_list

    def walk_ParamsBlock(self, node, **kwargs):
        self.is_param_block = True
        where_conds = self.walk(node.conds, **kwargs)
        ir_node = ParamsBlockNode(parse_info=node.parseinfo, annotation=node.annotation, conds=where_conds)
        self.is_param_block = False
        return ir_node

    def walk_WhereConditions(self, node, **kwargs):
        ir_node = WhereConditionsNode(parse_info=node.parseinfo)
        # for cond in node.value:
        #     cond_node = self.walk(cond, **kwargs)
        #     ir_node.value.append(cond_node)
        ir_list = []
        ir_index = []  # matrix, vector
        param_index = []
        func_index = []  # function
        func_param_index = []
        prev_parameters = self.parameters
        self.parameters = [None] * sum([len(value.id) for value in node.value])
        cur_param_index = 0
        for i in range(len(node.value)):
            # walk scalar first
            if type(node.value[i].type).__name__ == "ScalarType" or type(node.value[i].type).__name__ == "SetType":
                kwargs[PARAM_INDEX] = cur_param_index
                ir_list.append(self.walk(node.value[i], **kwargs))
            elif type(node.value[i].type).__name__ == "FunctionType":
                ir_list.append(None)
                func_index.append(i)
                func_param_index.append(cur_param_index)
            else:
                ir_list.append(None)
                ir_index.append(i)
                param_index.append(cur_param_index)
            cur_param_index += len(node.value[i].id)
        # matrix, vector nodes
        if len(ir_index) > 0:
            for i in range(len(ir_index)):
                kwargs[PARAM_INDEX] = param_index[i]
                ir_list[ir_index[i]] = self.walk(node.value[ir_index[i]], **kwargs)
        # func nodes:
        if len(func_index) > 0:
            for i in range(len(func_index)):
                kwargs[PARAM_INDEX] = func_param_index[i]
                ir_list[func_index[i]] = self.walk(node.value[func_index[i]], **kwargs)
        #
        ir_node.value = ir_list
        self.parameters = prev_parameters + self.parameters
        return ir_node

    def walk_WhereCondition(self, node, **kwargs):
        ir_node = WhereConditionNode(parse_info=node.parseinfo)
        ret = node.text.split(':')
        desc = ':'.join(ret[1:len(ret)])
        if hasattr(node, 'desc'):
            ir_node.desc = node.desc
        type_node = self.walk(node.type, **kwargs)
        if node.index:
            # check index type condition
            assert type_node.la_type.is_integer_element(), get_err_msg_info(node.id[0].parseinfo, "Invalid index type: element must be integer")
            type_node.la_type.index_type = True
            if not type_node.la_type.is_scalar():
                type_node.la_type.element_type.index_type = True
        type_node.parse_info = node.parseinfo
        type_node.la_type.desc = desc
        for id_index in range(len(node.id)):
            id0_info = self.walk(node.id[id_index], **kwargs)
            ir_node.id.append(id0_info.ir)
            id0 = id0_info.content
            if hasattr(node, 'desc') and node.desc is not None:
                self.desc_dict[id0_info.ir.get_main_id()] = node.desc
            if True:
                self.handle_identifier(id0, id0_info.ir, type_node)
                # self.logger.debug("param index:{}".format(kwargs[PARAM_INDEX]))
                if not self.local_func_parsing and not self.visiting_opt:
                    # main params: due to multiple blocks
                    self.update_parameters(id0, kwargs[PARAM_INDEX]+id_index)
                if type_node.la_type.is_matrix():
                    id1 = type_node.la_type.rows
                    id2 = type_node.la_type.cols
                    if isinstance(id1, str) and not id1.isnumeric():
                        if type_node.la_type.is_dynamic_row():
                            id1 = type_node.id1.get_main_id()
                        else:
                            if id1 not in self.get_cur_param_data().symtable and type_node.la_type.rows_ir is None:
                                self.get_cur_param_data().symtable[id1] = ScalarType(is_int=True)
                        if type_node.la_type.rows_ir is None:
                            if self.contain_subscript(id0):
                                self.get_cur_param_data().update_dim_dict(id1, self.get_main_id(id0), 1)
                            else:
                                self.get_cur_param_data().update_dim_dict(id1, self.get_main_id(id0), 0)
                        else:
                            self.get_cur_param_data().arith_dim_list.append(type_node.la_type.rows)
                    if isinstance(id2, str) and not id2.isnumeric():
                        if type_node.la_type.is_dynamic_col():
                            id2 = type_node.id2.get_main_id()
                        else:
                            if id2 not in self.symtable and type_node.la_type.cols_ir is None:
                                self.get_cur_param_data().symtable[id2] = ScalarType(is_int=True)
                        if type_node.la_type.cols_ir is None:
                            if self.contain_subscript(id0):
                                self.get_cur_param_data().update_dim_dict(id2, self.get_main_id(id0), 2)
                            else:
                                self.get_cur_param_data().update_dim_dict(id2, self.get_main_id(id0), 1)
                        else:
                            self.get_cur_param_data().arith_dim_list.append(type_node.la_type.cols)
                elif type_node.la_type.is_vector():
                    id1 = type_node.la_type.rows
                    if isinstance(id1, str) and not id1.isnumeric():
                        if type_node.la_type.is_dynamic_row():
                            id1 = type_node.id1.get_main_id()
                        else:
                            if id1 not in self.get_cur_param_data().symtable and type_node.la_type.rows_ir is None:
                                self.get_cur_param_data().symtable[id1] = ScalarType(is_int=True)
                        if type_node.la_type.rows_ir is None:
                            if self.contain_subscript(id0):
                                self.get_cur_param_data().update_dim_dict(id1, self.get_main_id(id0), 1)
                            else:
                                self.get_cur_param_data().update_dim_dict(id1, self.get_main_id(id0), 0)
                        else:
                            self.get_cur_param_data().arith_dim_list.append(type_node.la_type.rows)
        ir_node.type = type_node
        return ir_node

    def get_single_factor(self, ir_node):
        single = None
        if ir_node.is_node(IRNodeType.Integer):
            single = ir_node
        elif ir_node.value.is_node(IRNodeType.Factor):
            if ir_node.value.id:
                single = ir_node.value.id
            elif ir_node.value.num:
                single = ir_node.value.num
        return single

    def walk_MatrixType(self, node, **kwargs):
        ir_node = MatrixTypeNode(parse_info=node.parseinfo)
        element_type = ''
        if node.type:
            ir_node.type = node.type
            if node.type == 'ℝ':
                element_type = ScalarType()
            elif node.type == 'ℤ':
                element_type = ScalarType(is_int=True)
        else:
            element_type = ScalarType()
        self.dyn_dim = False
        id1_info = self.walk(node.id1, **kwargs)
        dyn_rows = self.dyn_dim
        single_node = self.get_single_factor(id1_info.ir)
        rows_ir = None
        if single_node is not None:
            ir_node.id1 = single_node
        else:
            self.dependency_set.update(id1_info.symbols)
            ir_node.id1 = id1_info.ir
            rows_ir = id1_info.ir
            self.logger.debug("Param matrix, row is: {}".format(id1_info.content))
        id1 = id1_info.content
        self.dyn_dim = False
        id2_info = self.walk(node.id2, **kwargs)
        dyn_cols = self.dyn_dim
        single_node = self.get_single_factor(id2_info.ir)
        cols_ir = None
        if single_node is not None:
            ir_node.id2 = single_node
        else:
            self.dependency_set.update(id2_info.symbols)
            ir_node.id2 = id2_info.ir
            cols_ir = id2_info.ir
            self.logger.debug("Param matrix, col is: {}".format(id2_info.content))
        id2 = id2_info.content
        la_type = MatrixType(rows=id1, cols=id2, element_type=element_type, rows_ir=rows_ir, cols_ir=cols_ir)
        # if ir_node.id1.is_node(IRNodeType.Id) and ir_node.id1.contain_subscript():
        if dyn_rows:
            # assert len(ir_node.id1.subs) == 1, get_err_msg_info(ir_node.id1.parse_info, "Invalid dimension for matrix")
            la_type.add_dynamic_type(DynamicTypeEnum.DYN_ROW)
        # if ir_node.id2.is_node(IRNodeType.Id) and ir_node.id2.contain_subscript():
        if dyn_cols:
            la_type.add_dynamic_type(DynamicTypeEnum.DYN_COL)
            # assert len(ir_node.id2.subs) == 1, get_err_msg_info(ir_node.id2.parse_info, "Invalid dimension for matrix")
        if node.attr and 'sparse' in node.attr:
            la_type.sparse = True
        ir_node.la_type = la_type
        return ir_node

    def walk_VectorType(self, node, **kwargs):
        ir_node = VectorTypeNode(parse_info=node.parseinfo)
        self.dyn_dim = False
        element_type = ''
        if node.type:
            ir_node.type = node.type
            if node.type == 'ℝ':
                element_type = ScalarType()
            elif node.type == 'ℤ':
                element_type = ScalarType(is_int=True)
        else:
            element_type = ScalarType()
        id1_info = self.walk(node.id1, **kwargs)
        rows_ir = None
        single_node = self.get_single_factor(id1_info.ir)
        if single_node is not None:
            ir_node.id1 = single_node
        else:
            self.dependency_set.update(id1_info.symbols)
            ir_node.id1 = id1_info.ir
            rows_ir = id1_info.ir
            self.logger.debug("Param matrix, row is: {}".format(id1_info.content))
        id1 = id1_info.content
        la_type = VectorType(rows=id1, element_type=element_type, rows_ir=rows_ir)
        # if ir_node.id1.is_node(IRNodeType.Id) and ir_node.id1.contain_subscript():
        if self.dyn_dim:
            # assert len(ir_node.id1.subs) == 1, get_err_msg_info(ir_node.id1.parse_info, "Invalid dimension for vector")
            la_type.add_dynamic_type(DynamicTypeEnum.DYN_ROW)
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
            if node.cnt:
                cnt_info = self.walk(node.cnt, **kwargs)
                cnt = cnt_info.content
                ir_node.cnt = cnt
            if node.type2 == 'ℤ':
                int_list = [True] * cnt
            else:
                int_list = [False] * cnt
        ir_node.la_type = SetType(size=cnt, int_list=int_list, element_type = ScalarType())
        return ir_node

    def get_unicode_number(self, unicode):
        # 0:\u2070,1:\u00B9,2:\u00B2,3:\u00B3,4-9:[\u2074-\u2079]
        number_dict = {'⁰':0,'¹':1,'²':2, '³':3,'⁴':4,'⁵':5,'⁶':6,'⁷':7,'⁸':8,'⁹':9 }
        return number_dict[unicode]

    def get_unicode_sub_number(self, unicode):
        # 0-9:[\u2080-\u2089]
        number_dict = {'₀':0,'₁':1,'₂':2, '₃':3,'₄':4,'₅':5,'₆':6,'₇':7,'₈':8,'₉':9 }
        return number_dict[unicode]

    def get_unicode_fraction(self, unicode):
        fraction_dict = {'¼':[1,4],'½':[1,2],'¾':[3,4],'⅐':[1,7],'⅑':[1,9],'⅒':[1,10],'⅓':[1,3],'⅔':[2,3],
                       '⅕':[1,5],'⅖':[2,5],'⅗':[3,5],'⅘':[4,5],'⅙':[1,6],'⅚':[5,6],'⅛':[1,8],'⅜':[3,8],'⅝':[5,8],
                       '⅞':[7,8]}
        return fraction_dict[unicode]

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
        ret_list = []
        for cur_index in range(len(node.ret)):
            ret_node = self.walk(node.ret[cur_index], **kwargs)
            ir_node.ret = ret_node
            ret = ret_node.la_type
            ret_list.append(ret)
            if ret.is_vector():
                if isinstance(ret.rows, str):
                    assert ret.rows in self.symtable or ret.rows in template_symbols, get_err_msg_info(ret_node.parse_info, "Vector as return value of function must have concrete dimension")
                    if ret.rows in template_symbols:
                        if ret.rows not in template_ret:
                            template_ret.append(ret.rows)
            elif ret.is_matrix():
                if isinstance(ret.rows, str):
                    assert ret.rows in self.symtable or ret.rows in template_symbols, get_err_msg_info(ret_node.parse_info, "Matrix as return value of function must have concrete dimension")
                if ret.rows in template_symbols:
                    if ret.rows not in template_ret:
                        template_ret.append(ret.rows)
                if isinstance(ret.cols, str):
                    assert ret.cols in self.symtable or ret.cols in template_symbols, get_err_msg_info(ret_node.parse_info, "Matrix as return value of function must have concrete dimension")
                    if ret.cols in template_symbols:
                        if ret.cols not in template_ret:
                            template_ret.append(ret.cols)
        self.logger.debug("template_symbols:{}, template_ret:{}".format(template_symbols, template_ret))
        la_type = FunctionType(params=params, ret=ret_list, template_symbols=template_symbols, ret_symbols=template_ret)
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
        params = []
        params_list = []
        module = None
        package = None
        for par in node.params:
            par_info = self.walk(par, **kwargs)
            params.append(par_info.ir)
            params_list.append(par_info.ir.get_name())
        package_info = self.walk(node.package, **kwargs)
        name_list = []
        name_ir_list = []
        for cur_name in node.names:
            name_info = self.walk(cur_name, **kwargs)
            name_ir_list.append(name_info.ir)
            name_list.append(name_info.ir.get_name())
        if package_info.ir.get_name() in self.packages:
            package = package_info.ir
            func_list = self.packages[package_info.ir.get_name()]
            for name in name_list:
                assert name in func_list, get_err_msg(get_line_info(node.parseinfo),
                                                           get_line_info(node.parseinfo).text.find(name),
                                                           "Function {} not exist".format(name))
        else:
            module = package_info.ir
            self.import_module_list.append(DependenceData(module.get_name(), params_list, name_list))
        import_node = ImportNode(package=package, module=module, names=name_ir_list, separators=node.separators,
                                     params=params, parse_info=node.parseinfo)
        return import_node

    def walk_Statements(self, node, **kwargs):
        stat_list = []
        # if node.stats:
        #     stat_list = self.walk(node.stats, **kwargs)
        stat_list.append(node.stat)
        return stat_list

    def walk_Expression(self, node, **kwargs):
        value_info = self.walk(node.value, **kwargs)
        ir_node = ExpressionNode(parse_info=node.parseinfo, raw_text=node.text)
        value_info.ir.set_parent(ir_node)
        ir_node.la_type = value_info.la_type
        ir_node.value = value_info.ir
        ir_node.sign = node.sign
        value_info.ir = ir_node
        return value_info

    def walk_Add(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ret_type, need_cast = self.type_inference(TypeInferenceEnum.INF_ADD, left_info, right_info)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node = AddNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        return ret_info

    def walk_Subtract(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ret_type, need_cast = self.type_inference(TypeInferenceEnum.INF_SUB, left_info, right_info)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node = SubNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        return ret_info

    def walk_AddSub(self, node, **kwargs):
        assert IF_COND in kwargs, get_err_msg(get_line_info(node.parseinfo),
                                                   get_line_info(node.parseinfo).text.find(node.op),
                                                   "{} must be used inside if codition".format(node.op))
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ret_type, need_cast = self.type_inference(TypeInferenceEnum.INF_ADD, left_info, right_info)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node = AddSubNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, op=node.op)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        return ret_info

    def walk_Multiply(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        op_type = MulOpType.MulOpInvalid
        if node.op and node.op == '⋅':
            op_type = MulOpType.MulOpDot
            if left_info.la_type.is_vector() and right_info.la_type.is_vector() and is_same_expr(left_info.la_type.rows, right_info.la_type.rows):
                return self.walk_DotProduct(node, **kwargs)
        return self.make_mul_info(left_info, right_info, op_type, parse_info=node.parseinfo)

    def make_mul_info(self, left_info, right_info, op=MulOpType.MulOpInvalid, parse_info=None):
        ret_type, need_cast = self.type_inference(TypeInferenceEnum.INF_MUL, left_info, right_info)
        sym_set = left_info.symbols.union(right_info.symbols)
        # I in block matrix
        if ret_type is not None:
            ret_type.symbol = ""
            for sym in sym_set:
                ret_type.symbol += sym
        ret_info = NodeInfo(ret_type, symbols=sym_set)
        ir_node = MulNode(left_info.ir, right_info.ir, parse_info=left_info.ir.parse_info if parse_info is None else parse_info, op=op)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        if need_cast:
            ir_node = CastNode(value=ir_node)
        ret_info.ir = ir_node
        return ret_info

    def walk_Divide(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ret_type, need_cast = self.type_inference(TypeInferenceEnum.INF_DIV, left_info, right_info)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        op_type = DivOpType.DivOpSlash
        if node.op == '÷':
            op_type = DivOpType.DivOpUnicode
        ir_node = DivNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, op=op_type)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        return ret_info

    def walk_Subexpression(self, node, **kwargs):
        value_info = self.walk(node.value, **kwargs)
        ir_node = SubexpressionNode(parse_info=node.parseinfo, raw_text=node.text)
        ir_node.value = value_info.ir
        ir_node.la_type = value_info.la_type
        value_info.ir = ir_node
        return value_info

    def walk_LocalFunc(self, node, **kwargs):
        self.local_func_parsing = True
        if isinstance(node.name, str):
            local_func_name = node.name
        else:
            local_func_name = self.walk(node.name).ir.get_main_id()
        par_defs = []
        par_dict = {}
        self.local_func_name = local_func_name
        if len(node.defs) > 0:
            self.is_param_block = True
            for par_def in node.defs:
                par_type = self.walk(par_def, **kwargs)
                par_defs.append(par_type)
                # par_dict.update(par_type.get_type_dict())
            # self.local_func_dict[local_func_name] = par_dict
            self.is_param_block = False
            # self.func_data_dict[local_func_name].symtable = par_dict
            self.local_func_dict[local_func_name] = self.func_data_dict[local_func_name].params_data.symtable
            par_dict = self.local_func_dict[local_func_name]
        assert local_func_name not in self.symtable, get_err_msg(get_line_info(node.parseinfo),0,"Symbol {} has been defined".format(local_func_name))
        ir_node = LocalFuncNode(name=IdNode(local_func_name, parse_info=node.parseinfo), expr=[],
                                parse_info=node.parseinfo, raw_text=node.text, defs=par_defs,
                                def_type=LocalFuncDefType.LocalFuncDefParenthesis if node.def_p else LocalFuncDefType.LocalFuncDefBracket)
        ret_list = []
        expr_list = []
        cur_symbols = set()
        for cur_index in range(len(node.expr)):
            expr_info = self.walk(node.expr[cur_index], **kwargs)
            expr_info.ir.set_parent(ir_node)
            expr_list.append(expr_info.ir)
            ret_list.append(expr_info.ir.la_type)
            cur_symbols = cur_symbols.union(expr_info.symbols)
        ir_node.expr = expr_list
        param_tps = []
        par_names = []
        for index in range(len(node.params)):
            param_node = self.walk(node.params[index], **kwargs).ir
            # assert param_node.get_name() in self.parameters, get_err_msg_info(param_node.parse_info, "Parameter {} hasn't been defined".format(param_node.get_name()))
            assert param_node.get_name() in par_dict, get_err_msg_info(param_node.parse_info, "Parameter {} hasn't been defined".format(param_node.get_name()))
            ir_node.params.append(param_node)
            # param_tps.append(param_node.la_type)
            param_tps.append(par_dict[param_node.get_name()])
            par_names.append(param_node.get_name())
        self.func_data_dict[local_func_name].params_data.parameters = par_names
        ir_node.separators = node.separators
        ir_node.la_type = FunctionType(params=param_tps, ret=ret_list)
        ir_node.symbols = cur_symbols.union(set(par_names))
        self.symtable[local_func_name] = ir_node.la_type
        self.local_func_parsing = False
        self.expr_dict[local_func_name] = list(ir_node.symbols) + [local_func_name]
        return NodeInfo(ir=ir_node)

    def walk_Assignment(self, node, **kwargs):
        # ir
        assign_node = AssignNode([], [], op=node.op, parse_info=node.parseinfo, raw_text=node.text)
        if type(node.right[0]).__name__ == 'MultiCondExpr':
            assert len(node.right) == 1, get_err_msg_info(node.right[0].parseinfo, "Invalid multiple rhs")
            assert len(node.left) == 1, get_err_msg_info(node.left[0].parseinfo, "Invalid multiple lhs")
        elif type(node.right[0]).__name__ == 'Optimize':
            pass
        elif type(node.right[0].value).__name__ == 'Factor' and node.right[0].value.op and type(node.right[0].value.op).__name__ == 'Function':
            pass
        else:
            assert len(node.left) == len(node.right), get_err_msg_info(node.left[0].parseinfo, "Invalid assignment: {} lhs and {} rhs".format(len(node.left), len(node.right)))
        parse_remain_lhs_directly = False   #  multiple lhs for argmin, argmax
        la_list = []
        for cur_index in range(len(node.left)):
            self.visiting_lhs = True
            id0_info = self.walk(node.left[cur_index], **kwargs)
            assign_node.left.append(id0_info.ir)
            self.visiting_lhs = False
            id0 = id0_info.content
            if SET_RET_SYMBOL in kwargs:
                self.ret_symbol = self.get_main_id(id0)
            kwargs[LHS] = id0
            kwargs[ASSIGN_OP] = node.op
            if id0_info.ir.contain_subscript():
                left_ids = self.get_all_ids(id0)
                left_subs = left_ids[1]
                pre_subs = []
                for sub_index in range(len(left_subs)):
                    sub_sym = left_subs[sub_index]
                    self.lhs_subs.append(sub_sym)
                    self.lhs_sym_list.append({})
                    if sub_sym in pre_subs:
                        continue
                    pre_subs.append(sub_sym)
                    assert sub_sym not in self.symtable, get_err_msg_info(node.left[0].right[sub_index].parseinfo, "Subscript has been defined")
                    self.symtable[sub_sym] = ScalarType(index_type=False, is_int=True)
                    self.lhs_sub_dict[sub_sym] = []  # init empty list
            la_remove_key(LHS, **kwargs)
            la_remove_key(ASSIGN_OP, **kwargs)
            #
            if parse_remain_lhs_directly:
                self.symtable[self.get_main_id(id0)] = la_list[cur_index]
                break
            right_info = self.walk(node.right[cur_index], **kwargs)
            right_type = right_info.la_type
            if len(self.lhs_subs) > 0:
                for cur_index in range(len(self.lhs_subs)):
                    cur_sym_dict = self.lhs_sym_list[cur_index]
                    if self.get_main_id(id0) not in self.symtable:
                        assert len(cur_sym_dict) > 0, get_err_msg_info(node.left[0].right[cur_index].parseinfo, "Subscript hasn't been used on rhs")
                    # self.check_sum_subs(self.lhs_subs[cur_index], cur_sym_dict)
                    assert self.check_sum_subs(self.lhs_subs[cur_index], cur_sym_dict), get_err_msg_info(node.left[0].right[cur_index].parseinfo,
                                                                                          "Subscript has inconsistent dimensions")
            self.lhs_sym_list.clear()
            self.lhs_subs.clear()
            if right_info.ir.is_node(IRNodeType.Optimize):
                if right_info.ir.opt_type == OptimizeType.OptimizeArgmin or right_info.ir.opt_type == OptimizeType.OptimizeArgmax:
                    la_list = right_info.la_type
                    parse_remain_lhs_directly = True   # no need to parse other rhs, only lhs
                    assert len(node.left) == len(right_info.ir.base_list), get_err_msg_info(node.left[0].parseinfo, "Invalid multiple lhs")
                    assign_node.optimize_param = True
                    right_type = right_info.la_type[0]
            elif right_info.ir.value.is_node(IRNodeType.Factor) and right_info.ir.value.op and right_info.ir.value.op.is_node(IRNodeType.Function):
                if isinstance(right_info.la_type, list):
                    # multiple ret value
                    assert len(node.left) == len(right_info.la_type), get_err_msg_info(node.left[0].parseinfo, "Invalid assignment: {} lhs and {} ret value".format(len(node.left), len(right_info.la_type)))
                    la_list = right_info.la_type
                    parse_remain_lhs_directly = True
                    assign_node.optimize_param = True
                    right_type = right_info.la_type[0]
            # ir
            assign_node.right.append(right_info.ir)
            right_info.ir.set_parent(assign_node)
            id0_info.ir.set_parent(assign_node)
            # y_i = stat
            if self.contain_subscript(id0):
                left_ids = self.get_all_ids(id0)
                left_subs = left_ids[1]
                sequence = left_ids[0]    #y
                assert '*' not in left_subs, get_err_msg_info(node.parseinfo, "LHS can't have * as subscript")
                if node.op != '=':
                    assert sequence in self.symtable, get_err_msg_info(id0_info.ir.parse_info,
                                                                           "{} hasn't been defined".format(sequence))
                else:
                    if sequence in self.symtable and len(left_subs) != 2:  # matrix items
                        err_msg = "{} has been assigned before".format(id0)
                        if sequence in self.parameters:
                            err_msg = "{} is a parameter, can not be assigned".format(id0)
                        # assert False, get_err_msg_info(id0_info.ir.parse_info, err_msg)
                if len(left_subs) == 2:  # matrix
                    if right_info.ir.node_type != IRNodeType.SparseMatrix:
                        assert sequence not in self.parameters, get_err_msg_info(id0_info.ir.parse_info, "{} is a parameter, can not be assigned".format(sequence))
                    if not (right_type.is_matrix() and right_type.sparse):
                        assert right_type.is_scalar(), get_err_msg_info(right_info.ir.parse_info, "RHS has to be scalar")
                    if right_info.la_type is not None and right_info.la_type.is_matrix():
                        # sparse mat assign
                        if right_info.la_type.sparse:
                            self.symtable[sequence] = right_type
                    if sequence not in self.symtable:
                        sparse = False
                        index_var = None
                        value_var = None
                        for symbol in right_info.symbols:
                            if left_subs[0] == left_subs[1]:  # diagonal matrix
                                sparse = True
                                index_var = self.generate_var_name("{}{}{}".format(sequence, left_subs[0], left_subs[1]))
                                value_var = self.generate_var_name("{}vals".format(sequence))
                        # cal dim
                        dim_list = []
                        for cur_sub in left_subs:
                            for cur_node in self.lhs_sub_dict[cur_sub]:  # all nodes containing the subscript
                                if self.symtable[cur_node.get_main_id()].is_vector():
                                    dim = self.symtable[cur_node.get_main_id()].rows
                                elif self.symtable[cur_node.get_main_id()].is_sequence():
                                    dim = self.symtable[cur_node.get_main_id()].size
                                    if cur_node.same_as_row_sym(cur_sub):
                                        dim = self.symtable[cur_node.get_main_id()].rows
                                    elif cur_node.same_as_col_sym(cur_sub):
                                        dim = self.symtable[cur_node.get_main_id()].cols
                                elif self.symtable[cur_node.get_main_id()].is_matrix():
                                    # matrix
                                    dim = self.symtable[cur_node.get_main_id()].rows
                                    if cur_node.same_as_col_sym(cur_sub):
                                        dim = self.symtable[cur_node.get_main_id()].cols
                                break
                            dim_list.append(dim)
                        self.symtable[sequence] = MatrixType(rows=dim_list[0], cols=dim_list[1], element_type=right_type, sparse=sparse, diagonal=sparse, index_var=index_var, value_var=value_var)
                elif len(left_subs) == 1:  # sequence or vector
                    cur_sub = left_subs[0]
                    sequence_type = True   # default type: sequence
                    for cur_node in self.lhs_sub_dict[cur_sub]:  # all nodes containing the subscript
                        if self.symtable[cur_node.get_main_id()].is_vector():
                            sequence_type = False
                            dim = self.symtable[cur_node.get_main_id()].rows
                            break
                        elif self.symtable[cur_node.get_main_id()].is_sequence():
                            dim = self.symtable[cur_node.get_main_id()].size
                            if cur_node.is_node(IRNodeType.SequenceIndex):
                                if cur_node.same_as_row_sym(cur_sub):
                                    dim = self.symtable[cur_node.get_main_id()].rows
                                elif cur_node.same_as_col_sym(cur_sub):
                                    dim = self.symtable[cur_node.get_main_id()].cols
                        elif self.symtable[cur_node.get_main_id()].is_matrix():
                            # matrix
                            dim = self.symtable[cur_node.get_main_id()].rows
                            if cur_node.same_as_col_sym(cur_sub):
                                dim = self.symtable[cur_node.get_main_id()].cols
                    if right_type.is_matrix():
                        sequence_type = True
                    elif right_type.is_scalar():
                        sequence_type = False
                    if sequence_type:
                        self.symtable[sequence] = SequenceType(size=dim, element_type=right_type)
                        seq_index_node = SequenceIndexNode()
                        seq_index_node.main = self.walk(node.left[0].left, **kwargs).ir
                        seq_index_node.main_index = self.walk(node.left[0].right[0], **kwargs).ir
                        seq_index_node.la_type = right_type
                        seq_index_node.set_parent(assign_node)
                        assign_node.left[cur_index] = seq_index_node
                    else:
                        # vector
                        self.symtable[sequence] = VectorType(rows=dim)
                        vector_index_node = VectorIndexNode()
                        vector_index_node.main = self.walk(node.left[0].left, **kwargs).ir
                        vector_index_node.row_index = self.walk(node.left[0].right[0], **kwargs).ir
                        vector_index_node.set_parent(assign_node)
                        vector_index_node.la_type = right_type
                        assign_node.left[cur_index] = vector_index_node
                # remove temporary subscripts(from LHS) in symtable
                for sub_sym in left_subs:
                    if sub_sym in self.symtable:
                        # multiple same sub_sym
                        del self.symtable[sub_sym]
                if len(self.lhs_sub_dict) > 0:
                    assign_node.lhs_sub_dict = self.lhs_sub_dict
                    self.lhs_sub_dict = {}
                else:
                    self.lhs_sub_dict.clear()
            else:
                if node.op != '=':
                    assert id0 in self.symtable, get_err_msg_info(id0_info.ir.parse_info, "{} hasn't been defined".format(id0))
                else:
                    if id0 in self.symtable:
                        err_msg = "{} has been assigned before".format(id0)
                        if id0 in self.parameters:
                            err_msg = "{} is a parameter, can not be assigned".format(id0)
                        assert False, get_err_msg_info(id0_info.ir.parse_info, err_msg)
                    self.symtable[id0] = right_type
            assign_node.symbols = assign_node.symbols.union(right_info.symbols)
            self.expr_dict[id0_info.ir.get_main_id()] = list(right_info.symbols) + [id0_info.ir.get_main_id()]
        return NodeInfo(None, ir=assign_node, symbols=assign_node.symbols)

    def walk_Summation(self, node, **kwargs):
        self.logger.debug("cur sum_subs:{}, sum_conds:{}".format(self.sum_subs, self.sum_conds))
        kwargs[INSIDE_SUMMATION] = True
        #
        ir_node = SummationNode(parse_info=node.parseinfo)
        self.sum_sym_list.append({})
        if node.cond:
            id_info = self.walk(node.id, **kwargs)
            self.sum_subs.append(id_info.content)
            self.sum_conds.append(True)
            ir_node.id = id_info.ir
            id_info.ir.set_parent(ir_node)
            subs = id_info.content
            if LHS in kwargs:
                lhs = kwargs[LHS]
                lhs_ids = self.get_all_ids(lhs)
                # assert lhs_ids[1][0] == lhs_ids[1][1], "multiple subscripts for sum"
            sub_parse_info = node.id.parseinfo
            assert subs not in self.symtable, get_err_msg_info(sub_parse_info, "Subscript has been defined")
            self.symtable[subs] = ScalarType(index_type=False, is_int=True)  # add subscript to symbol table temporarily
            ir_node.cond = self.walk(node.cond, **kwargs).ir
        else:
            sub_info = self.walk(node.sub)
            self.sum_subs.append(sub_info.content)
            self.sum_conds.append(False)
            ir_node.sub = sub_info.ir
            ir_node.id = sub_info.ir
            sub_info.ir.set_parent(ir_node)
            subs = sub_info.content
            sub_parse_info = node.sub.parseinfo
            assert subs not in self.symtable, get_err_msg_info(sub_parse_info, "Subscript has been defined")
            self.symtable[subs] = ScalarType(index_type=False, is_int=True)  # add subscript to symbol table temporarily
        self.logger.debug("new sum_subs:{}, sum_conds:{}".format(self.sum_subs, self.sum_conds))
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
        self.sum_subs.pop()
        self.sum_conds.pop()
        cur_sym_dict = self.sum_sym_list.pop()
        assert len(cur_sym_dict) > 0, get_err_msg_info(sub_parse_info, "Subscript hasn't been used in summation")
        # self.check_sum_subs(subs, cur_sym_dict)
        assert self.check_sum_subs(subs, cur_sym_dict), get_err_msg_info(sub_parse_info, "Subscript has inconsistent dimensions")
        ir_node.sym_dict = cur_sym_dict
        ret_info.ir = ir_node
        del self.symtable[subs]   # remove subscript from symbol table
        self.logger.debug("cur_sym_dict: {}".format(cur_sym_dict))
        self.logger.debug("summation, symbols: {}".format(ir_node.symbols))
        return ret_info

    def check_sum_subs(self, subs, sym_dict):
        self.logger.debug("subs:{}, sym_dict:{}".format(subs, sym_dict))
        dim_set = set()
        seq_cnt = 0  #
        valid = True
        for k, v in sym_dict.items():
            cur_type = self.get_cur_param_data().symtable[k]
            for cur_index in range(len(v)):
                if v[cur_index] == subs:
                    cur_dim = cur_type.get_dim_size(cur_index)
                    if cur_type.is_sequence() and cur_index == 0:
                        if cur_dim not in dim_set:
                            seq_cnt += 1
                    dim_set.add(cur_dim)
        if len(dim_set) > seq_cnt+1 or seq_cnt > 1:
            valid = False
        else:
            if len(dim_set) > 1:
                found = False
                for cur_index in range(len(self.get_cur_param_data().same_dim_list)):
                    for ele in dim_set:
                        if ele in self.get_cur_param_data().same_dim_list[cur_index]:
                            found = True
                            self.get_cur_param_data().same_dim_list[cur_index].union(dim_set)
                            break
                    if found:
                        break
                if not found:
                    self.get_cur_param_data().same_dim_list.append(dim_set)
        self.logger.debug("dim_set:{}".format(dim_set))
        self.logger.debug("self.same_dim_list:{}".format(self.get_cur_param_data().same_dim_list))
        return valid

    def walk_Optimize(self, node, **kwargs):
        self.has_opt = True
        self.visiting_opt = True
        self.opt_key = self.generate_var_name('opt_key')
        self.opt_dict[self.opt_key] = ParamsData()
        base_id_list = []
        base_node_list = []
        base_type_list = []
        la_type_list = []
        par_defs = []
        par_dict = {}
        init_list = []
        init_syms = []
        if len(node.init) > 0:
            for cur_init in node.init:
                cur_info = self.walk(cur_init, **kwargs)
                init_list.append(cur_info.ir)
                init_syms.append(cur_info.ir.left[0].get_main_id())
        self.opt_cur_init_list = copy.deepcopy(init_syms)
        if len(node.defs) > 0:
            self.is_param_block = True
            for par_def in node.defs:
                par_type = self.walk(par_def, **kwargs)
                par_defs.append(par_type)
                for cur_index in range(len(par_type.id)):
                    base_id_list.append(par_type.id[cur_index].get_main_id())
                    base_type_list.append(par_type.type)
                    base_node_list.append(par_type.id[cur_index])
                    la_type_list.append(par_type.type.la_type)
                    # temporary add to symbol table : opt scope
                    # self.symtable[par_type.id[cur_index].get_name()] = par_type.type.la_type
                    self.tmp_symtable[par_type.id[cur_index].get_main_id()] = self.get_cur_param_data().symtable[par_type.id[cur_index].get_main_id()]
            self.is_param_block = False
            self.symtable.update(self.get_cur_param_data().symtable)
        opt_type = OptimizeType.OptimizeInvalid
        ret_type = ScalarType()
        if node.min:
            opt_type = OptimizeType.OptimizeMin
        elif node.max:
            opt_type = OptimizeType.OptimizeMax
        elif node.amin:
            opt_type = OptimizeType.OptimizeArgmin
            ret_type = la_type_list
        elif node.amax:
            opt_type = OptimizeType.OptimizeArgmax
            ret_type = la_type_list
        exp_info = self.walk(node.exp, **kwargs)
        exp_node = exp_info.ir
        cond_list = []
        if node.cond:
            cond_list = self.walk(node.cond, **kwargs)
        # for cur_id in base_id_list:
        #     del self.symtable[cur_id]
        #
        assert exp_node.la_type.is_scalar(), get_err_msg_info(exp_node.parse_info, "Objective function must return a scalar")
        opt_node = OptimizeNode(opt_type, cond_list, exp_node, base_node_list, base_type_list, parse_info=node.parseinfo, key=self.opt_key, init_list=init_list, init_syms=init_syms, def_list=par_defs)
        opt_node.la_type = ret_type
        node_info = NodeInfo(opt_node.la_type, ir=opt_node, symbols=exp_info.symbols)
        self.visiting_opt = False
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
            if node.sub == '*':
                ir_node.norm_type = NormType.NormNuclear
            elif node.sub == '∞':
                ir_node.norm_type = NormType.NormMax
            else:
                sub_type = self.walk(node.sub, **kwargs)
                if sub_type.ir.node_type == IRNodeType.Integer:
                    ir_node.sub = sub_type.ir.value
                    ir_node.norm_type = NormType.NormInteger
                else:
                    if sub_type.ir.get_name() == 'F':
                        ir_node.norm_type = NormType.NormFrobenius
                        ir_node.sub = 'F'
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
            # ir_node.sub = 2
        #
        if ir_node.value.la_type.is_scalar():
            assert node.single is not None, get_err_msg_info(node.parseinfo, "Norm error. Scalar type has to use | rather than ||")
        elif ir_node.value.la_type.is_vector():
            assert node.single is None, get_err_msg_info(node.parseinfo, "Norm error. Vector type has to use || rather than |")
            assert ir_node.norm_type != NormType.NormFrobenius and ir_node.norm_type != NormType.NormNuclear, get_err_msg(get_line_info(node.parseinfo),
                                 get_line_info(node.parseinfo).text.find('_')+1, "Norm error. Invalid norm for Vector")
            if ir_node.norm_type == NormType.NormIdentifier:
                assert ir_node.sub.la_type.is_matrix() or ir_node.sub.la_type.is_scalar(), get_err_msg(get_line_info(node.parseinfo),
                                 get_line_info(node.parseinfo).text.find('_')+1, "Norm error. Subscript has to be matrix or scalar for vector type")
                if ir_node.sub.la_type.is_matrix():
                    assert is_same_expr(ir_node.sub.la_type.rows, ir_node.sub.la_type.cols) and is_same_expr(ir_node.sub.la_type.rows, ir_node.value.la_type.rows), get_err_msg(get_line_info(node.parseinfo),
                                 get_line_info(node.parseinfo).text.find('_')+1, "Norm error. Dimension error")
        elif ir_node.value.la_type.is_matrix():
            if node.single:
                ir_node.norm_type = NormType.NormDet
            else:
                assert node.single is None, get_err_msg_info(node.parseinfo, "Norm error. MATRIX type has to use || rather than |")
                assert ir_node.norm_type == NormType.NormFrobenius or ir_node.norm_type == NormType.NormNuclear, get_err_msg(get_line_info(node.parseinfo),
                                 get_line_info(node.parseinfo).text.find('_')+1, "Norm error. Invalid norm for Matrix")
                if ir_node.norm_type == NormType.NormNuclear:
                    assert not ir_node.value.la_type.sparse, get_err_msg(get_line_info(node.parseinfo),
                                                                          get_line_info(node.parseinfo).text.find('*'),
                                                                          "Norm error. Nuclear norm is invalid for sparse matrix")

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
        assert left_info.ir.la_type.is_vector(), get_err_msg_info(left_info.ir.parse_info, "Inner product error. Parameter {} must be vector".format(node.left.text))
        assert right_info.ir.la_type.is_vector(), get_err_msg_info(right_info.ir.parse_info, "Inner product error. Parameter {} must be vector".format(node.right.text))
        assert is_same_expr(left_info.ir.la_type.rows, right_info.ir.la_type.rows), get_err_msg_info(node.parseinfo,
                                                                                        "Inner product error. Parameters {} and {} must have the same dimension".format(node.left.text, node.right.text))
        sub_node = None
        if node.sub:
            sub_node = self.walk(node.sub, **kwargs).ir
            assert sub_node.la_type.is_matrix() and sub_node.la_type.rows==sub_node.la_type.cols==left_info.ir.la_type.rows, \
                get_err_msg_info(sub_node.parse_info, "Inner product error. The dimension of subscript {} must correspond to the vector dimension".format(node.sub.text))
        ir_node = InnerProductNode(left_info.ir, right_info.ir, sub_node, parse_info=node.parseinfo)
        ret_type = ScalarType()
        ir_node.la_type = ret_type
        node_info = NodeInfo(ret_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))
        return node_info

    def walk_FroProduct(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        assert left_info.la_type.is_vector() or left_info.la_type.is_matrix(), get_err_msg_info(left_info.ir.parse_info, "Frobenius product error. Parameter {} must be vector or matrix".format(node.left.text))
        assert right_info.la_type.is_vector() or right_info.la_type.is_matrix(), get_err_msg_info(right_info.ir.parse_info, "Frobenius product error. Parameter {} must be vector or matrix".format(node.right.text))
        ir_node = FroProductNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        ir_node.la_type = ScalarType()
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))

    def walk_HadamardProduct(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ir_node = HadamardProductNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        assert left_info.la_type.is_vector() or left_info.la_type.is_matrix(), get_err_msg_info(left_info.ir.parse_info, "Hadamard product error. Parameter {} must be vector or matrix".format(node.left.text))
        assert right_info.la_type.is_vector() or right_info.la_type.is_matrix(), get_err_msg_info(right_info.ir.parse_info, "Hadamard product error. Parameter {} must be vector or matrix".format(node.right.text))
        assert is_same_expr(left_info.la_type.rows, right_info.la_type.rows), get_err_msg_info(node.parseinfo,
                                                                                        "Hadamard product error. Parameters {} and {} must have the same dimension".format(node.left.text, node.right.text))
        if left_info.la_type.is_matrix():
            assert is_same_expr(left_info.la_type.cols, right_info.la_type.cols), get_err_msg_info(node.parseinfo,
                                                                                        "Hadamard product error. Parameters {} and {} must have the same dimension".format(node.left.text, node.right.text))
            ir_node.la_type = MatrixType(rows=left_info.la_type.rows, cols=left_info.la_type.cols)
        else:
            ir_node.la_type = VectorType(rows=left_info.la_type.rows)
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))

    def walk_CrossProduct(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        assert left_info.la_type.is_vector(), get_err_msg_info(left_info.ir.parse_info, "Cross product error. Parameter {} must be vector".format(node.left.text))
        assert right_info.la_type.is_vector(), get_err_msg_info(right_info.ir.parse_info, "Cross product error. Parameter {} must be vector".format(node.right.text))
        assert left_info.la_type.rows == 3, get_err_msg_info(left_info.ir.parse_info, "Cross product error. The dimension of parameter {} must be 3".format(node.left.text))
        assert right_info.la_type.rows == 3, get_err_msg_info(right_info.ir.parse_info, "Cross product error. The dimension of parameter {} must be 3".format(node.right.text))
        ir_node = CrossProductNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        ir_node.la_type = VectorType(rows=left_info.la_type.rows)
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))

    def walk_KroneckerProduct(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ir_node = KroneckerProductNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        assert left_info.la_type.is_vector() or left_info.la_type.is_matrix(), get_err_msg_info(left_info.ir.parse_info, "Kronecker product error. Parameter {} must be vector or matrix".format(node.left.text))
        assert right_info.la_type.is_vector() or right_info.la_type.is_matrix(), get_err_msg_info(right_info.ir.parse_info, "Kronecker product error. Parameter {} must be vector or matrix".format(node.right.text))
        ir_node.la_type = MatrixType(rows=mul_dims(left_info.la_type.rows, right_info.la_type.rows), cols=mul_dims(left_info.la_type.cols, right_info.la_type.cols))
        if left_info.la_type.is_sparse_matrix() or right_info.la_type.is_sparse_matrix():
            ir_node.la_type.sparse = True
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))

    def walk_DotProduct(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ir_node = DotProductNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        assert left_info.la_type.is_vector(), get_err_msg_info(left_info.ir.parse_info, "Dot product error. Parameter {} must be vector".format(node.left.text))
        assert right_info.la_type.is_vector(), get_err_msg_info(right_info.ir.parse_info, "Dot product error. Parameter {} must be vector".format(node.right.text))
        assert is_same_expr(left_info.la_type.rows, right_info.la_type.rows), get_err_msg_info(node.parseinfo,
                                                                                        "Dot product error. Parameters {} and {} must have the same dimension".format(node.left.text, node.right.text))
        ir_node.la_type = ScalarType()
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))

    def create_power_node(self, base, power):
        power_node = PowerNode()
        power_node.base = base
        power_node.power = power
        assert power.la_type.is_scalar(), get_err_msg_info(power.parse_info, "Power must be scalar")
        power_node.la_type = ScalarType()
        assert base.la_type.is_scalar() or base.la_type.is_matrix(), get_err_msg_info(base.parse_info, "Base of power must be scalar or matrix")
        if base.la_type.is_matrix():
            assert is_same_expr(base.la_type.rows, base.la_type.cols), get_err_msg_info(base.parse_info, "Power error. Rows must be the same as columns")
            self.unofficial_method = True
            power_node.la_type = base.la_type
        return power_node

    def walk_Power(self, node, **kwargs):
        ir_node = PowerNode(parse_info=node.parseinfo)
        base_info = self.walk(node.base, **kwargs)
        ir_node.base = base_info.ir
        symbols = base_info.symbols
        if node.t:
            if 'T' in self.symtable:
                # normal pow
                power_ir = IdNode('T', parse_info=node.parseinfo)
                power_ir.la_type = self.symtable['T']
                symbols = symbols.union('T')
                ir_node = self.create_power_node(base_info.ir, power_ir)
            else:
                # transpose
                ir_node.t = node.t
                assert base_info.la_type.is_matrix() or base_info.la_type.is_vector(), get_err_msg_info(base_info.ir.parse_info,"Transpose error. The base must be a matrix or vecotr")
                sparse = False
                if base_info.la_type.is_matrix():
                    sparse = base_info.la_type.sparse
                ir_node.la_type = MatrixType(rows=base_info.la_type.cols, cols=base_info.la_type.rows, sparse=sparse)
        elif node.r:
            ir_node.r = node.r
            if base_info.la_type.is_matrix():
                assert base_info.la_type.is_matrix(), get_err_msg_info(base_info.ir.parse_info,"Inverse matrix error. The base must be a matrix")
                assert is_same_expr(base_info.la_type.rows, base_info.la_type.cols), get_err_msg_info(base_info.ir.parse_info,"Inverse matrix error. The rows should be the same as the columns")
                ir_node.la_type = MatrixType(rows=base_info.la_type.rows, cols=base_info.la_type.rows, sparse=base_info.la_type.sparse)
            else:
                assert base_info.la_type.is_scalar(), get_err_msg_info(base_info.ir.parse_info,
                                                                            "Inverse error. The base must be a matrix or scalar")
                ir_node.la_type = ScalarType()
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
        ir_node.pow = node.p
        ir_node.left = left_info.ir
        ir_node.right = right_info.ir
        assert left_info.la_type.is_matrix(), get_err_msg_info(left_info.ir.parse_info, "Parameter {} must be a matrix".format(node.left.text))
        assert right_info.la_type.is_matrix() or right_info.la_type.is_vector(), get_err_msg_info(left_info.ir.parse_info, "Parameter {} must be a matrix or vector".format(node.right.text))
        node_type = None
        if left_info.la_type.is_matrix():
            assert is_same_expr(left_info.la_type.rows, right_info.la_type.rows), get_err_msg_info(left_info.ir.parse_info, "Parameters {} and {} should have the same rows".format(node.left.text, node.right.text))
            if right_info.la_type.is_matrix():
                node_type = MatrixType(rows=left_info.la_type.cols, cols=right_info.la_type.cols, sparse=left_info.la_type.sparse and right_info.la_type.sparse)
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
        assert f_info.la_type.is_matrix() or f_info.la_type.is_vector(), get_err_msg_info(f_info.ir.parse_info,"Transpose error. The base must be a matrix or vector")
        if f_info.la_type.is_matrix():
            node_type = MatrixType(rows=f_info.la_type.cols, cols=f_info.la_type.rows, sparse=f_info.la_type.sparse)
            if f_info.la_type.is_dynamic_row():
                node_type.set_dynamic_type(DynamicTypeEnum.DYN_COL)
            if f_info.la_type.is_dynamic_col():
                node_type.set_dynamic_type(DynamicTypeEnum.DYN_ROW)
        elif f_info.la_type.is_vector():
            node_type = MatrixType(rows=1, cols=f_info.la_type.rows)
        node_info = NodeInfo(node_type, symbols=f_info.symbols)
        node_info.ir = ir_node
        node_info.la_type = node_type
        return node_info

    def walk_Squareroot(self, node, **kwargs):
        ir_node = SquarerootNode(parse_info=node.parseinfo)
        f_info = self.walk(node.f, **kwargs)
        assert f_info.la_type.is_scalar(), get_err_msg_info(f_info.ir.parse_info, "Squareroot error. The base must be a scalar")
        node_type = ScalarType()
        ir_node.value = f_info.ir
        node_info = NodeInfo(node_type, symbols=f_info.symbols)
        node_info.ir = ir_node
        node_info.la_type = node_type
        return node_info

    def walk_Function(self, node, **kwargs):
        if isinstance(node.name, str):
            if self.local_func_parsing and node.name in self.parameters and node.name not in self.used_params:
                self.used_params.append(node.name)
            if self.visiting_opt and node.name in self.parameters and node.name not in self.used_params:
                self.used_params.append(node.name)
            if contains_sub_symbol(node.name):
                split_res = split_sub_string(node.name)
                name = self.filter_symbol(split_res[0])
                ir_node = SequenceIndexNode(raw_text=node.name)
                ir_node.main = IdNode(name, parse_info=node.parseinfo)
                ir_node.main.la_type = self.symtable[name]
                ir_node.main_index = IdNode(split_res[-1], parse_info=node.parseinfo)
                if split_res[-1].isnumeric():
                    ir_node.main_index.la_type = ScalarType(is_int=True)
                else:
                    assert split_res[-1] in self.symtable, get_err_msg_info(node.parseinfo, "Subscript not defined")
                    assert self.symtable[split_res[-1]].is_int_scalar(), get_err_msg_info(node.parseinfo, "Subscript has to be integer")
                    ir_node.main_index.la_type = self.symtable[split_res[-1]]
                    self.update_sub_sym_lists(name, split_res[-1])
                ir_node.la_type = self.symtable[name].element_type
                ir_node.process_subs_dict(self.lhs_sub_dict)
            else:
                ir_node = IdNode(node.name, parse_info=node.parseinfo)
                node.name = self.filter_symbol(node.name)
                ir_node.la_type = self.get_sym_type(node.name)
            name_info = NodeInfo(ir_node.la_type, ir=ir_node)
        else:
            name_info = self.walk(node.name, **kwargs)
        name_type = name_info.ir.la_type
        if name_type.is_function():
            ir_node = FunctionNode(parse_info=node.parseinfo)
            ir_node.name = name_info.ir
            convertion_dict = {}   # template -> instance
            param_list = []
            assert len(node.params) == len(name_type.params), get_err_msg_info(node.parseinfo, "Function error. Parameters count mismatch")
            symbols = set()
            for index in range(len(node.params)):
                param_info = self.walk(node.params[index], **kwargs)
                symbols = symbols.union(param_info.symbols)
                param_list.append(param_info.ir)
                if len(name_type.template_symbols) == 0:
                    assert name_type.params[index].is_same_type(param_info.ir.la_type, True), get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch")
                    continue
                if name_type.params[index].is_scalar():
                    assert name_type.params[index].is_same_type(param_info.ir.la_type), get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch")
                elif name_type.params[index].is_vector():
                    assert param_info.ir.la_type.is_vector(), get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch")
                    if name_type.params[index].rows in name_type.template_symbols:
                        convertion_dict[name_type.params[index].rows] = param_info.ir.la_type.rows
                    else:
                        assert is_same_expr(name_type.params[index].rows, param_info.ir.la_type.rows), get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch")
                elif name_type.params[index].is_matrix():
                    assert param_info.ir.la_type.is_matrix(), get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch")
                    if name_type.params[index].rows in name_type.template_symbols:
                        convertion_dict[name_type.params[index].rows] = param_info.ir.la_type.rows
                    else:
                        assert is_same_expr(name_type.params[index].rows, param_info.ir.la_type.rows), get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch")
                    #
                    if name_type.params[index].cols in name_type.template_symbols:
                        convertion_dict[name_type.params[index].cols] = param_info.ir.la_type.cols
                    else:
                        assert is_same_expr(name_type.params[index].cols, param_info.ir.la_type.cols), get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch")
                elif name_type.params[index].is_set():
                    assert param_info.ir.la_type.is_set(), get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch")
                    assert name_type.params[index].size == param_info.ir.la_type.size, get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch")
            ir_node.params = param_list
            ir_node.separators = node.separators
            self.logger.debug("convertion_dict:{}".format(convertion_dict))
            ret_list = []
            for cur_index in range(len(name_type.ret)):
                ret_type = name_type.ret[cur_index]
                cur_type = name_type.ret[cur_index]
                if cur_type.is_scalar():
                    pass
                elif cur_type.is_vector():
                    if cur_type.rows in name_type.template_symbols:
                        ret_type = VectorType()
                        ret_type.rows = convertion_dict[cur_type.rows]
                elif cur_type.is_matrix():
                    ret_type = MatrixType()
                    if cur_type.rows in name_type.template_symbols:
                        ret_type.rows = convertion_dict[cur_type.rows]
                    else:
                        ret_type.rows = cur_type.rows
                    if cur_type.cols in name_type.template_symbols:
                        ret_type.cols = convertion_dict[cur_type.cols]
                    else:
                        ret_type.cols = cur_type.cols
                elif name_type.ret.is_set():
                    ret_type = SetType(size=name_type.ret.size, int_list=name_type.ret.int_list)
                ret_list.append(ret_type)
            ret_type = ret_list[0] if len(ret_list)==1 else ret_list # single ret type or list
            symbols.add(ir_node.name.get_name())
            node_info = NodeInfo(ret_type, symbols=symbols)
            ir_node.la_type = ret_type
            node_info.ir = ir_node
            return node_info
        else:
            assert False, "Not a function"
            # assert len(node.params) == 1, "Not a function"  # never reach
            # return self.make_mul_info(name_info, self.walk(node.params[0], **kwargs))

    def walk_IfCondition(self, node, **kwargs):
        ir_node = IfNode(parse_info=node.parseinfo)
        kwargs[IF_COND] = True
        node_info = self.walk(node.cond, **kwargs)
        ir_node.cond = node_info.ir
        ir_node.la_type = node_info.la_type
        # check special nodes
        add_sub_node = ir_node.get_child(IRNodeType.AddSub)
        if add_sub_node is not None:
            copy_node = copy.deepcopy(node_info.ir)
            assert add_sub_node.get_child(IRNodeType.AddSub) is None, get_err_msg_info(add_sub_node.parse_info, "Multiple +- symbols in a single expression")
            new_nodes = add_sub_node.split_node()
            add_sub_node.parent().value = new_nodes[0]
            #
            sec_node = copy.deepcopy(node_info.ir)
            add_node = sec_node.get_child(IRNodeType.Add)
            add_node.parent().value = new_nodes[1]
            #
            condition_node = ConditionNode(cond_type=ConditionType.ConditionOr)
            condition_node.cond_list.append(node_info.ir)
            condition_node.cond_list.append(sec_node)
            condition_node.tex_node = copy_node
            ir_node.cond = condition_node
        node_info.ir = ir_node
        return node_info

    def walk_InCondition(self, node, **kwargs):
        ir_node = InNode(parse_info=node.parseinfo)
        item_node = []
        for item in node.left:
            item_info = self.walk(item, **kwargs)
            item_node.append(item_info.ir)
            assert item_info.la_type.is_scalar(), get_err_msg_info(item_info.ir.parse_info, "Must be scalar type")
        ir_node.items = item_node
        set_info = self.walk(node.right, **kwargs)
        ir_node.set = set_info.ir
        assert set_info.la_type.is_set(), get_err_msg_info(set_info.ir.parse_info, "Must be set type")
        assert len(item_node) == set_info.la_type.size, get_err_msg_info(node.parseinfo, "Size doesn't match for set")
        return NodeInfo(ir=ir_node)

    def walk_NotInCondition(self, node, **kwargs):
        ir_node = NotInNode(parse_info=node.parseinfo)
        item_node = []
        for item in node.left:
            item_info = self.walk(item, **kwargs)
            item_node.append(item_info.ir)
            assert item_info.la_type.is_scalar(), get_err_msg_info(item_info.ir.parse_info, "Must be scalar type")
        ir_node.items = item_node
        set_info = self.walk(node.right, **kwargs)
        ir_node.set = set_info.ir
        assert set_info.la_type.is_set(), get_err_msg_info(set_info.ir.parse_info, "Must be set type")
        assert len(item_node) == set_info.la_type.size, get_err_msg_info(node.parseinfo, "Size doesn't match for set")
        return NodeInfo(VarTypeEnum.SCALAR, ir=ir_node)

    def walk_NeCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        assert left_info.la_type.is_same_type(right_info.la_type), get_err_msg(get_line_info(node.parseinfo),
                                                              get_line_info(node.parseinfo).text.find(node.op),
                                                              "Different types for comparison")
        return NodeInfo(ir=BinCompNode(IRNodeType.Ne, left_info.ir, right_info.ir, parse_info=node.parseinfo, op=node.op))

    def walk_EqCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        assert left_info.la_type.is_same_type(right_info.la_type), get_err_msg(get_line_info(node.parseinfo),
                                                              get_line_info(node.parseinfo).text.find(node.op),
                                                              "Different types for comparison")
        return NodeInfo(ir=BinCompNode(IRNodeType.Eq, left_info.ir, right_info.ir, parse_info=node.parseinfo, op=node.op))

    def walk_GreaterCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        assert left_info.la_type.is_scalar(), get_err_msg_info(left_info.ir.parse_info, "LHS has to be scalar type for comparison")
        assert right_info.la_type.is_scalar(), get_err_msg_info(right_info.ir.parse_info, "RHS has to be scalar type for comparison")
        return NodeInfo(ir=BinCompNode(IRNodeType.Gt, left_info.ir, right_info.ir, parse_info=node.parseinfo, op=node.op))

    def walk_GreaterEqualCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        assert left_info.la_type.is_scalar(), get_err_msg_info(left_info.ir.parse_info, "LHS has to be scalar type for comparison")
        assert right_info.la_type.is_scalar(), get_err_msg_info(right_info.ir.parse_info, "RHS has to be scalar type for comparison")
        return NodeInfo(ir=BinCompNode(IRNodeType.Ge, left_info.ir, right_info.ir, parse_info=node.parseinfo, op=node.op))

    def walk_LessCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        assert left_info.la_type.is_scalar(), get_err_msg_info(left_info.ir.parse_info, "LHS has to be scalar type for comparison")
        assert right_info.la_type.is_scalar(), get_err_msg_info(right_info.ir.parse_info, "RHS has to be scalar type for comparison")
        return NodeInfo(ir=BinCompNode(IRNodeType.Lt, left_info.ir, right_info.ir, parse_info=node.parseinfo, op=node.op))

    def walk_LessEqualCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        assert left_info.la_type.is_scalar(), get_err_msg_info(left_info.ir.parse_info, "LHS has to be scalar type for comparison")
        assert right_info.la_type.is_scalar(), get_err_msg_info(right_info.ir.parse_info, "RHS has to be scalar type for comparison")
        return NodeInfo(ir=BinCompNode(IRNodeType.Le, left_info.ir, right_info.ir, parse_info=node.parseinfo, op=node.op))

    def update_sub_sym_lists(self, main_sym, right_sym_list):
        self.update_sub_sym_list(main_sym, right_sym_list, False)
        self.update_sub_sym_list(main_sym, right_sym_list, True)

    def update_sub_sym_list(self, main_sym, right_sym_list, lhs):
        if lhs:
            subs_list = self.lhs_subs
            sub_sym_list = self.lhs_sym_list
        else:
            subs_list = self.sum_subs
            sub_sym_list = self.sum_sym_list
        # inside summation or lhs
        for sub_index in range(len(subs_list)):
            sub_sym = subs_list[sub_index]
            if sub_sym in right_sym_list:
                cur_dict = sub_sym_list[sub_index]
                if main_sym in cur_dict:
                    # merge same subscript
                    old_right_list = copy.deepcopy(cur_dict[main_sym])
                    # assert len(old_right_list) == len(right_sym_list), "Internal error, please report a bug"
                    if len(old_right_list) == len(right_sym_list):
                        for old_index in range(len(old_right_list)):
                            if sub_sym != old_right_list[old_index]:
                                old_right_list[old_index] = right_sym_list[old_index]
                        cur_dict[main_sym] = old_right_list
                    elif len(old_right_list) < len(right_sym_list):
                        new_right_list = copy.deepcopy(right_sym_list)
                        for old_index in range(len(old_right_list)):
                            if sub_sym == old_right_list[old_index]:
                                new_right_list[old_index] = sub_sym
                        cur_dict[main_sym] = new_right_list
                    else:
                        for new_index in range(len(right_sym_list)):
                            if sub_sym == right_sym_list[new_index]:
                                old_right_list[new_index] = sub_sym
                        cur_dict[main_sym] = old_right_list
                else:
                    cur_dict[main_sym] = right_sym_list
                sub_sym_list[sub_index] = cur_dict

    def walk_IdentifierSubscript(self, node, **kwargs):
        def get_right_list():
            # rhs only
            right_list = []
            for right in node.right:
                if right != '*':
                    r_content = self.walk(right).content
                    right_list.append(r_content)
                    if not self.visiting_lhs and not isinstance(r_content, int):
                        assert self.is_sym_existed(r_content), get_err_msg_info(right.parseinfo, "Subscript has not been defined")
                else:
                    right_list.append(right)
            return right_list
        # check first *
        if node.right[0] == '*' and len(node.right) > 1:
            raw_text = node.text
            start = raw_text.index('_*') + 2
            cur = start
            while cur < len(raw_text):
                if raw_text[cur] == ',':
                    break
                else:
                    line_info = get_line_info(node.parseinfo)
                    assert raw_text[cur] == ' ', get_err_msg(line_info, line_info.text.index('_*') + 1, "* must be used with ," )
                cur += 1
        right = []
        left_info = self.walk(node.left, **kwargs)
        if not self.is_param_block:
            if left_info.content == 'I' and not self.is_sym_existed('I'):
                right_sym_list = get_right_list()
                assert len(right_sym_list) == 1 and '*' not in right_sym_list, get_err_msg_info(left_info.ir.parse_info,
                                                                                        "Invalid identity matrix")
                ir_node = NumMatrixNode(parse_info=node.parseinfo)
                if isinstance(right_sym_list[0], str):
                    assert self.is_sym_existed(right_sym_list[0]), get_err_msg(line_info, line_info.text.index('_{}'.format(right_sym_list[0])) + 1,"{} unknown".format(right_sym_list[0]))
                ir_node.la_type = MatrixType(rows=right_sym_list[0], cols=right_sym_list[0])
                ir_node.id = left_info.ir
                ir_node.id1 = self.walk(node.right[0]).ir
                return NodeInfo(ir_node.la_type, ir=ir_node)
            elif self.is_sym_existed(left_info.content):
                right_sym_list = get_right_list()
                # update sym lists
                self.update_sub_sym_lists(left_info.content, right_sym_list)
                content_symbol = node.text.replace(' ', '').replace(',', '')
                if '_' not in content_symbol:
                    # unicode subscript
                    split_res = [left_info.content, content_symbol.replace(left_info.content, '')]
                else:
                    split_res = content_symbol.split('_')
                self.get_cur_param_data().ids_dict[content_symbol] = Identifier(split_res[0], split_res[1])
                assert self.is_sym_existed(left_info.content), get_err_msg_info(left_info.ir.parse_info,
                                                                                        "Element hasn't been defined")
                if self.get_sym_type(left_info.content).is_sequence():
                    if left_info.content in self.get_cur_param_data().dim_seq_set:
                        # index the sequence of dimension
                        ir_node = SeqDimIndexNode(parse_info=node.parseinfo)
                        ir_node.main = left_info.ir
                        main_index_info = self.walk(node.right[0])
                        ir_node.main_index = main_index_info.ir
                        main_dict = self.get_cur_param_data().dim_dict[left_info.content]
                        for key, value in main_dict.items():
                            ir_node.real_symbol = key
                            ir_node.dim_index = value
                            break
                        la_type = ScalarType(is_int=True)
                        ir_node.la_type = la_type
                        ir_node.process_subs_dict(self.lhs_sub_dict)
                        return NodeInfo(la_type, content_symbol,
                                        {node.text},
                                        ir_node)
                    la_type = self.get_sym_type(left_info.content).element_type
                    ir_node = SequenceIndexNode(parse_info=node.parseinfo)
                    ir_node.main = left_info.ir
                    main_index_info = self.walk(node.right[0])
                    ir_node.main_index = main_index_info.ir
                    if len(node.right) == 1:
                        assert node.right[0] != '*', get_err_msg(get_line_info(node.parseinfo),
                                                                  get_line_info(node.parseinfo).text.find('*'),
                                                                  "Can't use * as the index for a sequence")
                        la_type = self.get_sym_type(left_info.content).element_type
                    elif len(node.right) == 2:
                        assert self.get_sym_type(left_info.content).is_vector_seq(), get_err_msg_info(left_info.ir.parse_info,
                                                                       "Two subscripts are used for sequence of vector")
                        assert '*' not in node.right, get_err_msg(get_line_info(node.parseinfo),
                                                                  get_line_info(node.parseinfo).text.find('*'),
                                                                  "* can't be used here")
                        main_index_info = self.walk(node.right[0])
                        row_index_info = self.walk(node.right[1])
                        ir_node.main_index = main_index_info.ir
                        ir_node.row_index = row_index_info.ir
                        la_type = self.get_sym_type(left_info.content).element_type.element_type
                    elif len(node.right) == 3:
                        assert self.get_sym_type(left_info.content).is_matrix_seq(), get_err_msg_info(left_info.ir.parse_info,
                                                                                        "Triple subscripts are only used for a sequence of matrix")
                        assert node.right[0] != '*', get_err_msg(get_line_info(node.parseinfo),
                                                                  get_line_info(node.parseinfo).text.find('*'),
                                                                  "* can't be the first subscript here")
                        if '*' in node.right:
                            ir_node.slice_matrix = True
                            if node.right[1] == '*':
                                assert node.right[2] != '*', get_err_msg(get_line_info(node.parseinfo),
                                                                  get_line_info(node.parseinfo).text.find('*'),
                                                                  "Only one * is allowed as subscripts")
                                la_type = VectorType(rows=self.get_sym_type(left_info.content).element_type.rows)
                                col_index_info = self.walk(node.right[2])
                                ir_node.col_index = col_index_info.ir
                            else:
                                la_type = MatrixType(rows=1, cols=self.get_sym_type(left_info.content).element_type.cols)
                                row_index_info = self.walk(node.right[1])
                                ir_node.row_index = row_index_info.ir
                        else:
                            row_index_info = self.walk(node.right[1])
                            col_index_info = self.walk(node.right[2])
                            ir_node.main_index = main_index_info.ir
                            ir_node.row_index = row_index_info.ir
                            ir_node.col_index = col_index_info.ir
                            la_type = self.get_sym_type(left_info.content).element_type.element_type
                    ir_node.la_type = la_type
                    ir_node.process_subs_dict(self.lhs_sub_dict)
                    return NodeInfo(la_type, content_symbol,
                                             {node.text},
                                             ir_node)
                elif self.get_sym_type(left_info.content).is_matrix():
                    assert len(node.right) == 2, get_err_msg_info(left_info.ir.parse_info,
                                                                       "Two subscripts are required for matrix")
                    ir_node = MatrixIndexNode(parse_info=node.parseinfo)
                    ir_node.subs = right_sym_list
                    ir_node.main = left_info.ir
                    la_type = self.get_sym_type(left_info.content).element_type
                    if '*' in node.right:
                        if node.right[0] == '*':
                            assert node.right[1] != '*', get_err_msg(get_line_info(node.parseinfo),
                                                                  get_line_info(node.parseinfo).text.find('*'),
                                                                  "Only one * is allowed as subscripts")
                            la_type = VectorType(rows=self.get_sym_type(left_info.content).rows)
                            col_index_info = self.walk(node.right[1])
                            ir_node.col_index = col_index_info.ir
                        else:
                            la_type = VectorType(rows=self.get_sym_type(left_info.content).cols)
                            row_index_info = self.walk(node.right[0])
                            ir_node.row_index = row_index_info.ir
                    else:
                        row_index_info = self.walk(node.right[0])
                        col_index_info = self.walk(node.right[1])
                        ir_node.row_index = row_index_info.ir
                        ir_node.col_index = col_index_info.ir
                    ir_node.la_type = la_type
                    ir_node.process_subs_dict(self.lhs_sub_dict)
                    node_info = NodeInfo(la_type, content_symbol, {node.text},
                                         ir_node)
                    return node_info
                elif self.get_sym_type(left_info.content).is_vector():
                    assert len(node.right) == 1, get_err_msg_info(left_info.ir.parse_info,
                                                                                        "Only one subscript is allowed")
                    assert node.right[0] != '*', get_err_msg(get_line_info(node.parseinfo),
                                                                  get_line_info(node.parseinfo).text.find('*'),
                                                                  "Subscript can't be *")
                    index_info = self.walk(node.right[0])
                    assert index_info.la_type.is_scalar(), get_err_msg_info(index_info.ir.parse_info,
                                                                                        "Subscript must be scalar")
                    ir_node = VectorIndexNode(parse_info=node.parseinfo)
                    ir_node.main = left_info.ir
                    ir_node.row_index = index_info.ir
                    ir_node.la_type = self.get_sym_type(left_info.content).element_type
                    ir_node.process_subs_dict(self.lhs_sub_dict)
                    node_info = NodeInfo(self.get_sym_type(left_info.content).element_type, content_symbol, {node.text}, ir_node)
                    return node_info
        #
        for value in node.right:
            if value == '*':
                v_content = value
            else:
                v_content = self.walk(value).content
            right.append(str(v_content))
        return self.create_id_node_info(left_info.content, right, node.parseinfo)

    def create_id_node_info(self, left_content, right_content, parse_info=None):
        content = left_content + '_' + ''.join(right_content)
        node_type = LaVarType(VarTypeEnum.INVALID, symbol=content)
        if left_content in self.symtable:
            node_type = self.symtable[left_content].element_type
        #
        ir_node = IdNode(left_content, right_content, parse_info=parse_info)
        ir_node.la_type = node_type
        node_info = NodeInfo(node_type, content, {content}, ir_node)
        self.get_cur_param_data().ids_dict[content] = Identifier(left_content, right_content)
        return node_info

    def walk_IdentifierAlone(self, node, **kwargs):
        node_type = LaVarType(VarTypeEnum.INVALID)
        if node.value:
            value = node.value
        elif node.id:
            value = '`' + node.id + '`'
        else:
            value = node.const
        value = self.filter_symbol(value)
        #
        ir_node = IdNode(value, parse_info=node.parseinfo)
        if self.local_func_parsing and value in self.parameters and value not in self.used_params:
            self.used_params.append(value)
        if self.visiting_opt and value in self.parameters and value not in self.used_params:
            self.used_params.append(value)
        node_type = self.get_sym_type(value)
        # if value in self.symtable:
        #     node_type = self.symtable[value]
        node_type.symbol = value
        ir_node.la_type = node_type
        node_info = NodeInfo(node_type, value, {value}, ir_node)
        return node_info

    def walk_Factor(self, node, **kwargs):
        node_info = None
        ir_node = FactorNode(parse_info=node.parseinfo)
        if node.id0:
            id0_info = self.walk(node.id0, **kwargs)
            if id0_info.ir.node_type == IRNodeType.NumMatrix:
                node_info = id0_info
                ir_node.num = id0_info.ir
            else:
                id0 = id0_info.ir.get_main_id()
                if not la_is_if(**kwargs):  # symbols in sum don't need to be defined before todo:modify
                    if id0 != 'I':  # special case
                        new_symbol = self.filter_symbol(id0)
                        self.check_sym_existence(new_symbol, get_err_msg_info(id0_info.ir.parse_info,
                                                                                         "Symbol {} is not defined".format(id0)))
                        # pass  # todo:delete
                    else:
                        # I
                        if 'I' not in self.symtable:
                            if not la_is_inside_matrix(**kwargs):
                                assert id0_info.ir.contain_subscript(), get_err_msg_info(id0_info.ir.parse_info,
                                                                                        "Identity matrix must have subscript if used outside block matrix")
                            # assert la_is_inside_matrix(**kwargs),  get_err_msg_info(id0_info.ir.parse_info,
                            #                                                         "I must be used inside matrix if not defined")
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
        elif node.v:
            node_info = self.walk(node.v, **kwargs)
            ir_node.v = node_info.ir
        elif node.nm:
            node_info = self.walk(node.nm, **kwargs)
            ir_node.nm = node_info.ir
        elif node.op:
            node_info = self.walk(node.op, **kwargs)
            ir_node.op = node_info.ir
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

    def walk_E(self, node, **kwargs):
        node_info = NodeInfo(ScalarType())
        ir_node = ConstantNode(ConstantType.ConstantE, parse_info=node.parseinfo)
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    def walk_Integer(self, node, **kwargs):
        value = ''.join(node.value)
        node_type = ScalarType(is_int=True, is_constant=True)
        node_info = NodeInfo(node_type, content=int(value))
        #
        ir_node = IntegerNode(parse_info=node.parseinfo)
        ir_node.value = int(value)
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    def walk_SubInteger(self, node, **kwargs):
        value = 0
        for index in range(len(node.value)):
            value += self.get_unicode_sub_number(node.value[len(node.value) - 1 - index]) * 10 ** index
        node_type = ScalarType(is_int=True, is_constant=True)
        node_info = NodeInfo(node_type, content=int(value))
        #
        ir_node = IntegerNode(parse_info=node.parseinfo)
        ir_node.value = int(value)
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    def walk_SupInteger(self, node, **kwargs):
        value = 0
        for index in range(len(node.value)):
            value += self.get_unicode_number(node.value[len(node.value) - 1 - index]) * 10 ** index
        node_type = ScalarType(is_int=True, is_constant=True)
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

    def walk_Fraction(self, node, **kwargs):
        frac_list = self.get_unicode_fraction(node.value)
        node_info = NodeInfo(ScalarType(), content=node.text)
        ir_node = FractionNode(node.parseinfo, node.value, frac_list[0], frac_list[1])
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

    def walk_MultiCondExpr(self, node, **kwargs):
        if LHS in kwargs:
            lhs = kwargs[LHS]
        elif self.local_func_parsing:
            lhs = self.local_func_name
        if ASSIGN_OP in kwargs:
            op = kwargs[ASSIGN_OP]
        all_ids = self.get_all_ids(lhs)
        if all_ids[0] in self.symtable and self.symtable[all_ids[0]].is_matrix():
            # sparse matrix
            ir_node = SparseMatrixNode(parse_info=node.parseinfo)
            # ifsNode
            ifs_info = self.walk(node.ifs, **kwargs)
            ifs_node = SparseIfsNode(parse_info=node.ifs.parseinfo)
            first = True
            in_cond_only = True
            for ir in ifs_info.ir:
                ir.first_in_list = first
                first = False
                ifs_node.cond_list.append(ir)
                ir.set_parent(ifs_node)
                if not (ir.cond.cond.node_type == IRNodeType.In and ir.cond.cond.same_subs(all_ids[1])):
                    in_cond_only = False
            ifs_node.set_in_cond_only(in_cond_only)
            ifs_node.set_parent(ir_node)
            ir_node.ifs = ifs_node
            # otherwise
            if node.other:
                ir_node.other = self.walk(node.other, **kwargs).ir
            # definition
            index_var = self.generate_var_name("{}{}{}".format(all_ids[0], all_ids[1][0], all_ids[1][1]))
            value_var = self.generate_var_name("{}vals".format(all_ids[0]))
            if op == '=':  # require dims
                new_id = self.generate_var_name('sparse')
                id_name = new_id
                assert all_ids[0] in self.symtable, get_err_msg_info(node.parseinfo, "Sparse matrix: need dim")
                if all_ids[0] in self.parameters:
                    self.parameters.remove(all_ids[0])  # not a parameter
                    self.get_cur_param_data().remove_target_from_dim_dict(all_ids[0])
                id1 = self.symtable[all_ids[0]].rows
                if not isinstance(id1, int):
                    assert id1 in self.get_cur_param_data().dim_dict or id1 in self.parameters, get_err_msg_info(node.parseinfo, "Sparse matrix: dim {} is not defined".format(id1))
                id2 = self.symtable[all_ids[0]].cols
                if not isinstance(id2, int):
                    assert id2 in self.get_cur_param_data().dim_dict or id2 in self.parameters, get_err_msg_info(node.parseinfo, "Sparse matrix: dim {} is not defined".format(id2))
                la_type = MatrixType(rows=id1, cols=id2, sparse=True, index_var=index_var, value_var=value_var)
                self.symtable[new_id] = la_type
            elif op == '+=':
                assert all_ids[0] in self.symtable, get_err_msg_info(node.parseinfo, "{} is not defined".format(all_ids[0]))
                la_type = self.symtable[all_ids[0]]
                id_name = all_ids[0]
                id1 = self.symtable[all_ids[0]].rows
                if not isinstance(id1, int):
                    assert id1 in self.symtable, get_err_msg_info(node.parseinfo,
                                                                       "Sparse matrix: dim {} is not defined".format(id1))
                id2 = self.symtable[all_ids[0]].cols
                if not isinstance(id2, int):
                    assert id2 in self.symtable, get_err_msg_info(node.parseinfo,
                                                                       "Sparse matrix: dim {} is not defined".format(id2))
                # if node.id1:
                #     id1_info = self.walk(node.id1, **kwargs)
                #     id1 = id1_info.content
                #     ir_node.id1 = id1_info.ir
                #     id2_info = self.walk(node.id2, **kwargs)
                #     id2 = id2_info.content
                #     ir_node.id2 = id2_info.ir
                #     assert id1 == la_type.rows and id2 == la_type.cols, get_err_msg_info(node.parseinfo, "Sparse matrix: dim mismatch")

            node_info = NodeInfo(la_type)
            node_info.symbol = id_name
            ir_node.la_type = la_type
            ir_node.symbol = node_info.symbol
            node_info.ir = ir_node
        else:
            # normal multi conditionals
            symbols = set()
            ir_node = MultiCondNode(parse_info=node.parseinfo)
            # ifsNode
            ifs_info = self.walk(node.ifs, **kwargs)
            ifs_node = SparseIfsNode(parse_info=node.ifs.parseinfo)
            ifs_node.set_parent(ir_node)
            symbols = symbols.union(ifs_info.symbols)
            first = True
            for ir in ifs_info.ir:
                ir.first_in_list = first
                first = False
                ifs_node.cond_list.append(ir)
                ir.set_parent(ifs_node)
                la_type = ir.la_type
            ir_node.ifs = ifs_node
            if node.other:
                other_info = self.walk(node.other, **kwargs)
                ir_node.other = other_info.ir
                symbols = symbols.union(other_info.symbols)
            node_info = NodeInfo(la_type, symbols=symbols)
            ir_node.la_type = la_type
            node_info.ir = ir_node
        return node_info

    def walk_MultiIfs(self, node, **kwargs):
        symbols = set()
        ir_list = []
        if node.ifs:
            node_info = self.walk(node.ifs, **kwargs)
            ir_list += node_info.ir
            symbols = symbols.union(node_info.symbols)
        if node.value:
            node_info = self.walk(node.value, **kwargs)
            ir_list.append(node_info.ir)
            symbols = symbols.union(node_info.symbols)
        ret_info = NodeInfo(ir=ir_list, symbols=symbols)
        return ret_info

    def walk_SingleIf(self, node, **kwargs):
        symbols = set()
        ir_node = SparseIfNode(parse_info=node.parseinfo)
        cond_info = self.walk(node.cond, **kwargs)
        symbols = symbols.union(cond_info.symbols)
        ir_node.cond = cond_info.ir
        stat_info = self.walk(node.stat, **kwargs)
        symbols = symbols.union(stat_info.symbols)
        ir_node.stat = stat_info.ir
        ir_node.la_type = ir_node.stat.la_type
        return NodeInfo(ir=ir_node, symbols=symbols)

    def walk_Vector(self, node, **kwargs):
        symbols = set()
        ir_node = VectorNode(parse_info=node.parseinfo, raw_text=node.text)
        dim_list = []
        for exp in node.exp:
            exp_info = self.walk(exp, **kwargs)
            assert exp_info.la_type.is_scalar() or exp_info.la_type.is_vector(), get_err_msg_info(node.parseinfo, "Item in vector must be scalar or vector")
            ir_node.items.append(exp_info.ir)
            if exp_info.la_type.is_vector():
                dim_list.append(exp_info.la_type.rows)
            else:
                dim_list.append(1)
            symbols = symbols.union(exp_info.symbols)
        ir_node.la_type = VectorType(rows=self.get_sum_value(dim_list))
        node_info = NodeInfo(ir=ir_node, la_type=ir_node.la_type, symbols=symbols)
        if LHS in kwargs:
            lhs = kwargs[LHS]
            new_id = self.generate_var_name(lhs)
            self.symtable[new_id] = ir_node.la_type
            ir_node.symbol = new_id
        elif self.local_func_parsing:
            new_id = self.generate_var_name(self.local_func_name)
            self.get_cur_param_data().symtable[new_id] = ir_node.la_type
            ir_node.symbol = new_id

        return node_info

    def walk_Matrix(self, node, **kwargs):
        ir_node = MatrixNode(parse_info=node.parseinfo, raw_text=node.text)
        kwargs[INSIDE_MATRIX] = True
        node_info = self.walk(node.value, **kwargs)
        ir_node.value = node_info.ir
        # check matrix validity
        rows = len(node_info.content)
        cols = 0
        block = False
        sparse = False
        type_array = []
        for row in node_info.content:
            row_type = []
            for col in row:
                row_type.append(col.la_type)
                if col.la_type.is_matrix():
                    if col.la_type.sparse:
                        sparse = True
                    block = True
                elif col.la_type.is_vector():
                    block = True
            if len(row) > cols:
                cols = len(row)
            type_array.append(row_type)
        list_dim = None
        if block:
            # check block mat
            valid, undef_list, type_array, real_dims = self.check_bmat_validity(type_array, None)
            assert valid, get_err_msg_info(node.parseinfo,  "Block matrix error. Invalid dimensions")
            rows = real_dims[0]
            cols = real_dims[1]
            if len(undef_list) > 0:
                # need change dimension
                list_dim = {}
                for i, j in undef_list:
                    cur_ir = node_info.content[i][j]
                    if 'I' in cur_ir.raw_text:
                        pass
                    else:
                        if not (type_array[i][j].rows == 1 and type_array[i][j].cols == 1):
                            assert '0' == cur_ir.raw_text or '1' == cur_ir.raw_text, get_err_msg_info(cur_ir.parse_info, "Can not lift {}".format(cur_ir.raw_text))
                    list_dim[(i, j)] = [type_array[i][j].rows, type_array[i][j].cols]
        node_type = MatrixType(rows=rows, cols=cols, block=block, sparse=sparse, list_dim=list_dim, item_types=node_info.content)
        ret_node_info = NodeInfo(node_type, symbols=node_info.symbols)
        if LHS in kwargs:
            lhs = kwargs[LHS]
            new_id = self.generate_var_name(lhs)
            self.symtable[new_id] = MatrixType(rows=rows, cols=cols, block=block, sparse=sparse, list_dim=list_dim, item_types=node_info.content)
            ret_node_info.symbol = new_id
            ir_node.symbol = new_id
        elif self.local_func_parsing:
            new_id = self.generate_var_name(self.local_func_name)
            self.get_cur_param_data().symtable[new_id] = MatrixType(rows=rows, cols=cols, block=block, sparse=sparse, list_dim=list_dim,
                                               item_types=node_info.content)
            ret_node_info.symbol = new_id
            ir_node.symbol = new_id
        ir_node.la_type = ret_node_info.la_type
        ret_node_info.ir = ir_node
        return ret_node_info

    def walk_MatrixRows(self, node, **kwargs):
        ir_node = MatrixRowsNode(parse_info=node.parseinfo, raw_text=node.text)
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
        ir_node = MatrixRowNode(parse_info=node.parseinfo, raw_text=node.text)
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
                ret_info.content = [exp_info.ir]
            else:
                new_type, need_cast = self.type_inference(TypeInferenceEnum.INF_MATRIX_ROW, ret_info, exp_info)
                ret_info.la_type = new_type
                items.append(exp_info.ir)
                ret_info.content = items
            ret_info.symbols = symbols.union(exp_info.symbols)
        ir_node.la_type = ret_info.la_type
        ret_info.ir = ir_node
        return ret_info

    def walk_MatrixRowCommas(self, node, **kwargs):
        ir_node = MatrixRowCommasNode(parse_info=node.parseinfo, raw_text=node.text)
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
                ret_info.content = [exp_info.ir]
            else:
                new_type, need_cast = self.type_inference(TypeInferenceEnum.INF_MATRIX_ROW, ret_info, exp_info)
                ret_info.la_type = new_type
                items.append(exp_info.ir)
                ret_info.content = items
            ret_info.symbols = symbols.union(exp_info.symbols)
        ir_node.la_type = ret_info.la_type
        ret_info.ir = ir_node
        return ret_info

    def walk_ExpInMatrix(self, node, **kwargs):
        ret_info = self.walk(node.value, **kwargs)
        ir_node = ExpInMatrixNode(parse_info=node.parseinfo, raw_text=node.text)
        ir_node.value = ret_info.ir
        ir_node.sign = node.sign
        ir_node.la_type = ret_info.la_type
        ret_info.ir = ir_node
        return ret_info

    def walk_NumMatrix(self, node, **kwargs):
        ir_node = NumMatrixNode(parse_info=node.parseinfo)
        id1_info = self.walk(node.id1, **kwargs)
        ir_node.id1 = id1_info.ir
        id1_info.ir.set_parent(ir_node)
        id1 = id1_info.content
        if isinstance(id1, str):
            assert id1 in self.symtable, get_err_msg_info(id1_info.ir.parse_info, "{} unknown".format(id1))
        ir_node.left = node.left
        if node.left == '0':
            assert la_is_inside_matrix(**kwargs), get_err_msg_info(node.parseinfo, "Zero matrix can only be used inside matrix")
        if node.id2:
            id2_info = self.walk(node.id2, **kwargs)
            ir_node.id2 = id2_info.ir
            id2 = id2_info.content
            if isinstance(id2, str):
                assert id2 in self.symtable, get_err_msg_info(id2_info.ir.parse_info, "{} unknown".format(id2))
            node_type = MatrixType(rows=id1, cols=id2)
        else:
            node_type = VectorType(rows=id1)
        node_info = NodeInfo(node_type)
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    def create_math_node_info(self, func_type, param_info, remains=[]):
        param = param_info.ir
        ret_type = copy.deepcopy(param.la_type)
        symbols = param_info.symbols
        remain_list = []
        if MathFuncType.MathFuncInvalid < func_type < MathFuncType.MathFuncAtan2:
            assert param.la_type.is_scalar() or param.la_type.is_matrix() or param.la_type.is_vector(), \
                get_err_msg_info(param.parse_info, "Parameter must be scalar, vector or matrix type")
        elif func_type < MathFuncType.MathFuncTrace:
            assert param.la_type.is_scalar(), get_err_msg_info(param.parse_info, "Parameter must be scalar type")
            for par_info in remains:
                par = par_info.ir
                remain_list.append(par)
                assert par.la_type.is_scalar(), get_err_msg_info(par.parse_info, "Parameter must be scalar type")
                symbols = symbols.union(par_info.symbols)
        elif func_type == MathFuncType.MathFuncTrace:
            assert param.la_type.is_matrix() and param.la_type.rows == param.la_type.cols, get_err_msg_info(param.parse_info, "Parameter must be valid matrix type")
            ret_type = ScalarType()
        elif func_type == MathFuncType.MathFuncDiag:
            assert (param.la_type.is_matrix() and param.la_type.rows == param.la_type.cols) or param.la_type.is_vector(), get_err_msg_info(param.parse_info, "Parameter must be valid matrix or vector type")
            if param.la_type.is_matrix():
                ret_type = VectorType(rows=param.la_type.rows)
            else:
                ret_type = MatrixType(rows=param.la_type.rows, cols=param.la_type.rows)
        elif func_type == MathFuncType.MathFuncVec:
            assert param.la_type.is_matrix(), get_err_msg_info(param.parse_info, "Parameter must be valid matrix type")
            ret_type = VectorType(rows=param.la_type.rows*param.la_type.cols)
        elif func_type == MathFuncType.MathFuncDet:
            assert param.la_type.is_matrix(), get_err_msg_info(param.parse_info, "Parameter must be valid matrix type")
            ret_type = ScalarType()
        elif func_type == MathFuncType.MathFuncRank:
            assert param.la_type.is_matrix(), get_err_msg_info(param.parse_info,
                                                                    "Parameter must be valid matrix type")
            ret_type = ScalarType()
        elif func_type == MathFuncType.MathFuncNull:
            assert param.la_type.is_matrix(), get_err_msg_info(param.parse_info,
                                                                    "Parameter must be valid matrix type")
            ret_type = MatrixType(rows=param.la_type.cols, dynamic=DynamicTypeEnum.DYN_COL)  # dynamic dims
        elif func_type == MathFuncType.MathFuncOrth:
            assert param.la_type.is_matrix(), get_err_msg_info(param.parse_info,
                                                                    "Parameter must be valid matrix type")
            ret_type = MatrixType(rows=param.la_type.rows, dynamic=DynamicTypeEnum.DYN_COL)  # dynamic dims
        elif func_type == MathFuncType.MathFuncInv:
            assert param.la_type.is_matrix() and param.la_type.rows == param.la_type.cols, get_err_msg_info(param.parse_info, "Parameter must be valid matrix type")
            ret_type = MatrixType(rows=param.la_type.rows, cols=param.la_type.cols)
        tri_node = MathFuncNode(param, func_type, remain_list)
        node_info = NodeInfo(ret_type, symbols=symbols)
        tri_node.la_type = ret_type
        node_info.ir = tri_node
        return node_info

    def create_trig_node_info(self, func_type, param_info, power):
        symbols = param_info.symbols
        param = param_info.ir
        if power:
            assert param.la_type.is_scalar(), get_err_msg_info(param.parse_info, "Parameter must be scalar type for the power")
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
        func_type = MathFuncType.MathFuncLog
        if node.f:
            func_type = MathFuncType.MathFuncLog2
        elif node.s:
            func_type = MathFuncType.MathFuncLog10
        return self.create_math_node_info(func_type, self.walk(node.param, **kwargs))

    def walk_LnFunc(self, node, **kwargs):
        return self.create_math_node_info(MathFuncType.MathFuncLn, self.walk(node.param, **kwargs))

    def walk_SqrtFunc(self, node, **kwargs):
        return self.create_math_node_info(MathFuncType.MathFuncSqrt, self.walk(node.param, **kwargs))

    def walk_TraceFunc(self, node, **kwargs):
        node_info = self.create_math_node_info(MathFuncType.MathFuncTrace, self.walk(node.param, **kwargs))
        node_info.ir.func_name = node.name
        return node_info

    def walk_DiagFunc(self, node, **kwargs):
        return self.create_math_node_info(MathFuncType.MathFuncDiag, self.walk(node.param, **kwargs))

    def walk_VecFunc(self, node, **kwargs):
        return self.create_math_node_info(MathFuncType.MathFuncVec, self.walk(node.param, **kwargs))

    def walk_DetFunc(self, node, **kwargs):
        return self.create_math_node_info(MathFuncType.MathFuncDet, self.walk(node.param, **kwargs))

    def walk_RankFunc(self, node, **kwargs):
        return self.create_math_node_info(MathFuncType.MathFuncRank, self.walk(node.param, **kwargs))

    def walk_NullFunc(self, node, **kwargs):
        return self.create_math_node_info(MathFuncType.MathFuncNull, self.walk(node.param, **kwargs))

    def walk_OrthFunc(self, node, **kwargs):
        return self.create_math_node_info(MathFuncType.MathFuncOrth, self.walk(node.param, **kwargs))

    def walk_InvFunc(self, node, **kwargs):
        return self.create_math_node_info(MathFuncType.MathFuncInv, self.walk(node.param, **kwargs))
    ###################################################################
    def walk_ArithExpression(self, node, **kwargs):
        value_info = self.walk(node.value, **kwargs)
        ir_node = ExpressionNode(parse_info=node.parseinfo, raw_text=node.text)
        value_info.ir.set_parent(ir_node)
        ir_node.la_type = value_info.la_type
        ir_node.value = value_info.ir
        ir_node.sign = node.sign
        value_info.ir = ir_node
        return value_info

    def walk_ArithSubexpression(self, node, **kwargs):
        value_info = self.walk(node.value, **kwargs)
        ir_node = SubexpressionNode(parse_info=node.parseinfo, raw_text=node.text)
        ir_node.value = value_info.ir
        ir_node.la_type = value_info.la_type
        value_info.ir = ir_node
        value_info.content = '({})'.format(value_info.content)
        return value_info

    def walk_ArithAdd(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        # ret_type, need_cast = self.type_inference(TypeInferenceEnum.INF_ADD, left_info, right_info)
        ret_type = ScalarType(is_int=True)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node = AddNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        ret_info.content = '{}+{}'.format(left_info.content, right_info.content)
        return ret_info

    def walk_ArithSubtract(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ret_type = ScalarType(is_int=True)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node = SubNode(left_info.ir, right_info.ir, parse_info=node.parseinfo)
        ir_node.la_type = ret_type
        ret_info.ir = ir_node
        ret_info.content = '{}-{}'.format(left_info.content, right_info.content)
        return ret_info

    def walk_ArithMultiply(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ret_type = ScalarType(is_int=True)
        op_type = MulOpType.MulOpInvalid
        if node.op and node.op == '⋅':
            op_type = MulOpType.MulOpDot
        ir_node = MulNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, op=op_type)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node.la_type = ret_type
        ret_info.ir = ir_node
        ret_info.content = '{}*{}'.format(left_info.content, right_info.content)
        return ret_info

    def walk_ArithDivide(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ret_type = ScalarType(is_int=True)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        op_type = DivOpType.DivOpSlash
        if node.op == '÷':
            op_type = DivOpType.DivOpUnicode
        ir_node = DivNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, op=op_type)
        ir_node.la_type = ret_type
        ret_info.ir = ir_node
        ret_info.content = '{}/{}'.format(left_info.content, right_info.content)
        return ret_info

    def walk_ArithFactor(self, node, **kwargs):
        node_info = None
        ir_node = FactorNode(parse_info=node.parseinfo)
        if node.id0:
            content = node.id0.text
            def add_sym_info(sym, info):
                if sym not in self.dependency_dim_dict:
                    self.dependency_dim_dict[sym] = info
            if type(node.id0).__name__ == "IdentifierSubscript":
                self.dyn_dim = True
                assert len(node.id0.right) == 1 and node.id0.right[0] != '*', get_err_msg_info(node.id0.parseinfo, "Invalid dimension")
                index_node = SeqDimIndexNode(parse_info=node.parseinfo)
                index_node.main = self.walk(node.id0.left).ir
                add_sym_info(index_node.main.get_name(), node.parseinfo)
                main_index_info = self.walk(node.id0.right[0])
                index_node.main_index = main_index_info.ir
                # main_dict = self.dim_dict[left_info.content]
                # for key, value in main_dict.items():
                #     ir_node.real_symbol = key
                #     ir_node.dim_index = value
                #     break
                la_type = ScalarType(is_int=True)
                index_node.la_type = la_type
                ir_node.id = index_node
                node_info = NodeInfo(la_type, content, {}, index_node)
            else:
                id0_info = self.walk(node.id0, **kwargs)
                id0 = id0_info.ir.get_main_id()
                add_sym_info(id0, node.parseinfo)
                node_info = NodeInfo(id0_info.la_type, id0, id0_info.symbols, id0_info.ir)
                # node_info = NodeInfo(self.symtable[id0], id0, id0_info.symbols)
                ir_node.id = node_info.ir
        elif node.num:
            node_info = self.walk(node.num, **kwargs)
            ir_node.num = node_info.ir
        elif node.sub:
            node_info = self.walk(node.sub, **kwargs)
            ir_node.sub = node_info.ir
        #
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    ###################################################################
    def get_sum_value(self, dim_list):
        int_list = []
        str_list = []
        for d_item in dim_list:
            if isinstance(d_item, int):
                int_list.append(d_item)
            else:
                str_list.append(d_item)
        if len(int_list) > 0:
            if len(str_list) > 0:
                sum_value = "{}+{}".format('+'.join(str_list), sum(int_list))
            else:
                sum_value = sum(int_list)
        else:
            sum_value = '+'.join(str_list)
        return simpify_dims(sum_value)

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
        # only scalar value in a row or col
        if valid:
            row_dim = [i if i else 1 for i in row_dim]
            col_dim = [i if i else 1 for i in col_dim]
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
            row_sum = self.get_sum_value(row_dim)
            col_sum = self.get_sum_value(col_dim)
            real_dims = (row_sum, col_sum)
            if mat_size is not None:
                if row_sum != mat_size[0] or col_sum != mat_size[1]:
                    valid = False
        return valid, undef_list, type_array, real_dims

    def type_inference(self, op, left_info, right_info):
        need_cast = False
        left_type = left_info.ir.la_type
        right_type = right_info.ir.la_type
        # error msg
        left_line = get_parse_info_buffer(left_info.ir.parse_info).line_info(left_info.ir.parse_info.pos)
        right_line = get_parse_info_buffer(right_info.ir.parse_info).line_info(right_info.ir.parse_info.pos)
        def get_err_msg(extra_msg=''):
            line_msg = '{}. '.format(self.la_msg.get_line_desc(left_line))
            error_msg = 'Dimension mismatch. Can\'t {} {} {} and {} {}. {}\n'.format(
                                                                                self.get_op_desc(op),
                                                                                self.get_type_desc(left_type),
                                                                                get_parse_info_buffer(left_info.ir.parse_info).text[left_info.ir.parse_info.pos:left_info.ir.parse_info.endpos],
                                                                                self.get_type_desc(right_type),
                                                                                      get_parse_info_buffer(right_info.ir.parse_info).text[right_info.ir.parse_info.pos:right_info.ir.parse_info.endpos],
                                                                                extra_msg)
            raw_text = left_line.text
            if raw_text[-1] != '\n':
                raw_text += '\n'
            error_msg += raw_text
            error_msg += self.la_msg.get_pos_marker(left_line.col)
            self.la_msg.cur_msg = error_msg
            self.la_msg.cur_code = raw_text
            error_msg = line_msg + error_msg
            return error_msg
        ret_type = None
        if op == TypeInferenceEnum.INF_ADD or op == TypeInferenceEnum.INF_SUB:
            ret_type = copy.deepcopy(left_type)  # default type
            if left_type.is_scalar():
                assert right_type.is_scalar(), get_err_msg()
                ret_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
            elif left_type.is_matrix():
                assert right_type.is_matrix(), get_err_msg()
                # assert right_type.is_matrix() or right_type.is_vector(), error_msg
                if left_type.is_dynamic() or right_type.is_dynamic():
                    if left_type.is_dynamic() and right_type.is_dynamic():
                        if left_type.is_dynamic_row() and left_type.is_dynamic_col():
                            ret_type = copy.deepcopy(right_type)
                        elif left_type.is_dynamic_row():
                            if right_type.is_dynamic_row() and right_type.is_dynamic_col():
                                ret_type = copy.deepcopy(left_type)
                            elif right_type.is_dynamic_row():
                                assert is_same_expr(left_type.cols, right_type.cols), get_err_msg()
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
                                assert is_same_expr(left_type.rows, right_type.rows), get_err_msg()
                                ret_type = copy.deepcopy(left_type)
                    else:
                        if left_type.is_dynamic():
                            if left_type.is_dynamic_row() and left_type.is_dynamic_col():
                                ret_type = copy.deepcopy(right_type)
                            else:
                                if left_type.is_dynamic_row():
                                    assert is_same_expr(left_type.cols, right_type.cols), get_err_msg()
                                else:
                                    assert is_same_expr(left_type.rows, right_type.rows), get_err_msg()
                        else:
                            if right_type.is_dynamic_row() and right_type.is_dynamic_col():
                                ret_type = copy.deepcopy(left_type)
                            else:
                                if right_type.is_dynamic_row():
                                    assert is_same_expr(left_type.cols, right_type.cols), get_err_msg()
                                else:
                                    assert is_same_expr(left_type.rows, right_type.rows), get_err_msg()
                else:
                    # static
                    assert is_same_expr(left_type.rows, right_type.rows) and is_same_expr(left_type.cols, right_type.cols), get_err_msg()
                    if left_type.sparse and right_type.sparse:
                        ret_type.sparse = True
                    else:
                        ret_type.sparse = False
                ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
            elif left_type.is_vector():
                assert right_type.is_vector(), get_err_msg()
                assert is_same_expr(left_type.rows, right_type.rows), get_err_msg()
                # assert right_type.is_matrix() or right_type.is_vector(), error_msg
                # assert left_type.rows == right_type.rows and left_type.cols == right_type.cols, error_msg
                if right_type.is_matrix():
                    ret_type = copy.deepcopy(right_type)
                ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
            else:
                # sequence et al.
                assert left_type.var_type == right_type.var_type, get_err_msg()
            # index type checking
            if left_type.index_type or right_type.index_type:
                assert left_type.is_integer_element() and right_type.is_integer_element(), get_err_msg("Operand must be integer.")
                ret_type.index_type = True
                if op == TypeInferenceEnum.INF_ADD:
                    assert not (left_type.index_type and right_type.index_type), get_err_msg("They are both index types.")
                else:
                    if left_type.index_type and right_type.index_type:
                        ret_type.index_type = False
        elif op == TypeInferenceEnum.INF_MUL:
            assert left_type.var_type != VarTypeEnum.SEQUENCE and right_type.var_type != VarTypeEnum.SEQUENCE, 'error: sequence can not be operated'
            assert not left_type.index_type and not right_type.index_type, get_err_msg()
            if left_type.is_scalar():
                ret_type = copy.deepcopy(right_type)
                ret_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
            elif left_type.is_matrix():
                if right_type.is_scalar():
                    ret_type = copy.deepcopy(left_type)
                elif right_type.is_matrix():
                    assert is_same_expr(left_type.cols, right_type.rows), get_err_msg()
                    ret_type = MatrixType(rows=left_type.rows, cols=right_type.cols)
                    if left_type.sparse and right_type.sparse:
                        ret_type.sparse = True
                    # if left_type.rows == 1 and right_type.cols == 1:
                    #     ret_type = ScalarType()
                    ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
                elif right_type.is_vector():
                    assert is_same_expr(left_type.cols, right_type.rows), get_err_msg()
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
                    assert 1 == right_type.rows, get_err_msg()
                    ret_type = MatrixType(rows=left_type.rows, cols=right_type.cols)
                    new_node = ToMatrixNode(parse_info=left_info.ir.parse_info, item=left_info.ir)
                    new_node.la_type = MatrixType(rows=left_type.rows, cols=1)
                    left_info.ir = new_node
                    ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
                elif right_type.is_vector():
                    assert is_same_expr(left_type.cols, right_type.rows), get_err_msg()
                    ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
        elif op == TypeInferenceEnum.INF_DIV:
            # assert left_type.is_scalar() and right_type.is_scalar(), error_msg
            assert left_type.is_scalar() or left_type.is_vector() or left_type.is_matrix(), get_err_msg()
            assert right_type.is_scalar(), get_err_msg()
            assert not left_type.index_type and not right_type.index_type, get_err_msg()
            ret_type = copy.deepcopy(left_type)
            if left_type.is_scalar():
                ret_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
            else:
                ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
        elif op == TypeInferenceEnum.INF_MATRIX_ROW:
            # assert left_type.var_type == right_type.var_type
            ret_type = copy.deepcopy(left_type)
        return ret_type, need_cast

    def contain_subscript(self, identifier):
        if identifier in self.get_cur_param_data().ids_dict:
            return self.get_cur_param_data().ids_dict[identifier].contain_subscript()
        return False

    def get_all_ids(self, identifier):
        if identifier in self.get_cur_param_data().ids_dict:
            return self.get_cur_param_data().ids_dict[identifier].get_all_ids()
        res = identifier.split('_')
        if len(res) == 1:
            return res
        subs = []
        for index in range(len(res[1])):
            subs.append(res[1][index])
        return [res[0], subs]

    def get_main_id(self, identifier):
        if identifier in self.get_cur_param_data().ids_dict:
            return self.get_cur_param_data().ids_dict[identifier].get_main_id()
        return identifier

    # handle subscripts only (where block)
    def handle_identifier(self, identifier, ir_node, id_node):
        id_type = id_node.la_type
        if self.contain_subscript(identifier):
            arr = self.get_all_ids(identifier)
            new_var_name = None
            assert len(arr[1]) == 1, get_err_msg_info(ir_node.parse_info, "Parameter {} can't use multiple subscripts".format(arr[0]))
            val = arr[1][0]  # subscript
            assert not val.isnumeric(), get_err_msg_info(id_node.parse_info, "Parameter {} can't have constant subscript".format(arr[0]))
            if val in self.get_cur_param_data().sub_name_dict:
                new_var_name = self.get_cur_param_data().sub_name_dict[val]
            else:
                new_var_name = self.generate_var_name("dim")
                self.get_cur_param_data().sub_name_dict[val] = new_var_name
                self.get_cur_param_data().update_dim_dict(new_var_name, arr[0], 0)
            if val in self.get_cur_param_data().subscripts:
                var_list = self.get_cur_param_data().subscripts[val]
                var_list.append(arr[0])
                self.get_cur_param_data().subscripts[val] = var_list
            else:
                # first sequence
                self.get_cur_param_data().subscripts[val] = [arr[0]]
            assert arr[0] not in self.get_cur_param_data().symtable, get_err_msg_info(id_node.parse_info, "Parameter {} has been defined.".format(arr[0]))
            if id_type.is_vector():
                if id_type.is_dynamic_row():
                    if id_node.id1.is_node(IRNodeType.SeqDimIndex):
                        assert id_node.id1.main_index.get_name() == val, get_err_msg_info(id_node.id1.parse_info, "Dimension {} has different subscript".format(id_node.id1.main.get_name()))
                        row_seq_type = SequenceType(size=new_var_name, element_type=ScalarType(is_int=True), symbol=id_node.id1.get_main_id())
                        if id_node.id1.get_main_id() in self.get_cur_param_data().symtable:
                            assert self.get_cur_param_data().symtable[id_node.id1.get_main_id()].is_same_type(row_seq_type), get_err_msg_info(id_node.id1.parse_info,
                                                                                     "{} has already been defined as different type".format(
                                                                                         id_node.id1.get_main_id()))
                        else:
                            self.get_cur_param_data().symtable[id_node.id1.get_main_id()] = row_seq_type
                            self.get_cur_param_data().dim_seq_set.add(id_node.id1.get_main_id())
            elif id_type.is_matrix():
                if id_type.is_dynamic_row():
                    if id_node.id1.is_node(IRNodeType.SeqDimIndex):
                        assert id_node.id1.main_index.get_name() == val, get_err_msg_info(id_node.id1.parse_info, "Dimension {} has different subscript".format(id_node.id1.main.get_name()))
                        row_seq_type = SequenceType(size=new_var_name, element_type=ScalarType(is_int=True),
                                                    symbol=id_node.id1.get_main_id())
                        if id_node.id1.get_main_id() in self.get_cur_param_data().symtable:
                            assert self.get_cur_param_data().symtable[id_node.id1.get_main_id()].is_same_type(
                                row_seq_type), get_err_msg_info(id_node.id1.parse_info,
                                                                     "{} has already been defined as different type".format(
                                                                         id_node.id1.get_main_id()))
                        else:
                            self.get_cur_param_data().symtable[id_node.id1.get_main_id()] = row_seq_type
                            self.get_cur_param_data().dim_seq_set.add(id_node.id1.get_main_id())
                if id_type.is_dynamic_col():
                    if id_node.id2.is_node(IRNodeType.SeqDimIndex):
                        assert id_node.id1.main_index.get_name() == val, get_err_msg_info(id_node.id2.parse_info, "Dimension {} has different subscript".format(id_node.id2.main.get_name()))
                        col_seq_type = SequenceType(size=new_var_name, element_type=ScalarType(is_int=True),
                                                    symbol=id_node.id1.get_main_id())
                        if id_node.id2.get_main_id() in self.get_cur_param_data().symtable:
                            assert self.get_cur_param_data().symtable[id_node.id2.get_main_id()].is_same_type(
                                col_seq_type), get_err_msg_info(id_node.id2.parse_info,
                                                                     "{} has already been defined as different type".format(
                                                                         id_node.id2.get_main_id()))
                        else:
                            self.get_cur_param_data().symtable[id_node.id2.get_main_id()] = col_seq_type
                            self.get_cur_param_data().dim_seq_set.add(id_node.id2.get_main_id())
            self.get_cur_param_data().symtable[arr[0]] = SequenceType(size=new_var_name, element_type=id_type, desc=id_type.desc, symbol=arr[0])
        else:
            id_type.symbol = identifier
            self.check_sym_existence(identifier, get_err_msg_info(id_node.parse_info, "Parameter {} has been defined.".format(identifier)), False)
            self.get_cur_param_data().symtable[identifier] = id_type
