import copy
from tatsu.model import NodeWalker
from tatsu.objectmodel import Node
from .la_types import *
from ..la_tools.la_logger import *
from ..la_tools.la_msg import *
from ..la_tools.la_helper import *
from ..la_tools.la_package import *
import regex as re
from ..la_tools.la_helper import filter_subscript
from .light_walker import SolverParamWalker
from .ir_iterator import IRSumIndexVisitor
## Make the visualizer
try: from ..la_tools.la_visualizer import LaVisualizer
except ImportError:
    # if DEBUG_MODE:
    #     print( "Skipping visualizer." )
    class LaVisualizer(object):
        def visualize(self, node, pre_walk=True): pass

from .ir import *
from .la_data import *
from enum import Enum, IntFlag


class WalkTypeEnum(Enum):
    RETRIEVE_EXPRESSION = 0   # default
    RETRIEVE_VAR = 1

class DependenceData(object):
    def __init__(self, module='', initialized_list=[], name_list=[]):
        self.module = module
        self.name_list = name_list
        self.initialized_list = initialized_list

class BuiltinModuleData(object):
    def __init__(self, module='', instance_name='', params_list=None, name_list=None, r_dict=None):
        self.module = module   # MeshHelper
        self.instance_name = instance_name  #
        self.name_list = name_list
        self.params_list = params_list
        self.r_dict = r_dict
        self.inverse_dict = {}
        if self.r_dict:
            for k,v in self.r_dict.items():
                self.inverse_dict[v] = k

class EquationData(object):
    def __init__(self, name='', parameters=[], definition=[], dependence=[], symtable={}, desc_dict={}, la_content='', func_data_dict={}, expr_dict={}, opt_syms=[]):
        self.name = name
        self.undescribed_list = []
        self.parameters = parameters  # parameters for source file
        self.definition = definition  # lhs symbols
        self.dependence = dependence
        self.symtable = symtable
        self.desc_dict = desc_dict
        self.original_desc_dict = copy.deepcopy(desc_dict)
        self.la_content = la_content
        self.func_data_dict = func_data_dict
        self.opt_syms = opt_syms
        self.expr_dict = {}
        # for key in self.desc_dict.keys():
        #     self.desc_dict[key] = self.desc_dict[key].replace('"', '\"')
        # remove subscript in symbol
        for key, value in expr_dict.items():
            self.expr_dict[key] = [filter_subscript(val) for val in value]
        # gather all symbols: params, definitions, local func names, local params
        self.sym_list = list(self.parameters) + list(self.definition) + list(self.opt_syms)
        for key, value in self.func_data_dict.items():
            self.sym_list.append(key)
            self.sym_list += list(value.params_data.symtable.keys())
        for dep_data in self.dependence:
            self.sym_list += dep_data.name_list
        self.sym_list = list(set(self.sym_list))
        #
        self.generated_list = copy.deepcopy(self.sym_list)
        self.generated_list = [sym.replace('`$', '').replace('$`', '').replace('`', '') for sym in self.generated_list]
        #
        self.generated_list = list(set(self.generated_list))
        self.subset_dict = {}
        # for i in range(len(self.generated_list)):
        #     for j in range(len(self.generated_list)):
        #         if i != j and self.generated_list[i] in self.generated_list[j]:
        #             PROSE_RE = re.compile(
        #                 dedent(r'''(?<!(    # negative begins
        #                                             (\\(proselabel|prosedeflabel)({{([a-z0-9\p{{Ll}}\p{{Lu}}\p{{Lo}}\p{{M}}\s]+)}})?{{([a-z\p{{Ll}}\p{{Lu}}\p{{Lo}}\p{{M}}_{{()\s]*)))
        #                                             |
        #                                             ([a-zA-Z]+)
        #                                             ) # negative ends
        #                                             ({})
        #                                             (?![a-zA-Z]+)'''.format(self.escape_sym(self.generated_list[i]))),
        #                 re.MULTILINE | re.DOTALL | re.VERBOSE
        #             )
        #             for target in PROSE_RE.finditer(self.generated_list[j]):
        #                 if self.generated_list[i] not in self.subset_dict:
        #                     self.subset_dict[self.generated_list[i]] = [self.generated_list[j]]
        #                 else:
        #                     self.subset_dict[self.generated_list[i]].append(self.generated_list[j])
        #                 break
        self.generated_list = sorted(self.generated_list, key=len, reverse=True)
        # print("subset_dict:")
        # for key, value in self.subset_dict.items():
        #     print("{} : {}".format(key, value))

    def reset_desc_dict(self):
        self.desc_dict = copy.deepcopy(self.original_desc_dict)

    def escape_sym(self, sym):
        """
        Escape special characters in regular expression
        """
        escape_list = ['\\', '(', ')', '{', '}', '^', '+', '-', '.', '*', ' ']
        for es in escape_list:
            sym = sym.replace(es, '\\' + es)
        return sym

    def trim(self, content):
        # print("before:{}, after:{}".format(content, content.replace('"', '\\"').replace("'", "\\'")))
        # content = content.replace('"', '\\"').replace("'", "\\'")
        content = content.replace('\\', '\\\\\\\\').replace('"', '\\"').replace("'", "\\'")
        return content

    def gen_json_content(self):
        content = ''
        undesc_list = ['''"{}"'''.format(self.trim(sym)) for sym in self.undescribed_list]
        param_list = []
        for param in self.parameters:
            if param in self.desc_dict:
                param_list.append('''{{"sym":"{}", "type_info":{}, "desc":"{}"}}'''.format(self.trim(param), self.symtable[param].get_json_content(), base64_encode(self.desc_dict[param])))
            else:
                param_list.append('''{{"sym":"{}", "type_info":{}}}'''.format(self.trim(param), self.symtable[param].get_json_content()))
        def_list = []
        for lhs in self.definition:
            if lhs in self.desc_dict:
                def_list.append('''{{"sym":"{}", "type_info":{}, "desc":"{}"}}'''.format(self.trim(lhs), self.symtable[lhs].get_json_content(), base64_encode(self.desc_dict[lhs])))
            else:
                def_list.append('''{{"sym":"{}", "type_info":{}}}'''.format(self.trim(lhs), self.symtable[lhs].get_json_content()))
        for opt_var in self.opt_syms:
            if opt_var not in self.parameters and opt_var not in self.definition:
                if opt_var in self.desc_dict:
                    def_list.append('''{{"sym":"{}", "type_info":{}, "desc":"{}"}}'''.format(self.trim(opt_var),
                                                                                             self.symtable[
                                                                                                 opt_var].get_json_content(),
                                                                                             base64_encode(
                                                                                                 self.desc_dict[opt_var])))
                else:
                    def_list.append('''{{"sym":"{}", "type_info":{}}}'''.format(self.trim(opt_var),
                                                                                self.symtable[opt_var].get_json_content()))
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
                                                                                             base64_encode(self.desc_dict[sym])))
                else:
                    sym_list.append('''{{"sym":"{}", "type_info":{}}}'''.format(self.trim(sym),
                                                                                self.symtable[sym].get_json_content()))
            dependence_list.append('''{{"module":"{}", "syms":[{}], "initialization":[{}]}}'''.format(dep_data.module, ','.join(sym_list), ','.join(init_list)))
        #
        func_list = []
        for k, v in self.func_data_dict.items():
            if k in self.desc_dict:
                def_list.append('''{{"sym":"{}", "type_info":{}, "desc":"{}"}}'''.format(self.trim(k), self.symtable[k].get_json_content(), base64_encode(self.desc_dict[k])))
            else:
                def_list.append('''{{"sym":"{}", "type_info":{}}}'''.format(self.trim(k), self.symtable[k].get_json_content()))
            local_param_list = []
            for local_param in v.params_data.parameters:
                if local_param in self.desc_dict:
                    local_param_list.append('''{{"sym":"{}", "type_info":{}, "desc":"{}"}}'''.format(self.trim(local_param), v.params_data.symtable[local_param].get_json_content(), base64_encode(self.desc_dict[local_param])))
                else:
                    local_param_list.append('''{{"sym":"{}", "type_info":{}}}'''.format(self.trim(local_param), v.params_data.symtable[local_param].get_json_content()))
            func_list.append('''{{"name":"{}", "parameters":[{}]}}'''.format(self.trim(k), ','.join(local_param_list)))
        # self.la_content = self.la_content.replace('\n', '\\\\n')
        content = '''"parameters":[{}], "definition":[{}], "local_func":[{}], "dependence":[{}], "undesc_list":[{}]'''.format(','.join(param_list), ','.join(def_list), ','.join(func_list), ','.join(dependence_list), ','.join(undesc_list))
        # content = content.replace('\\', '\\\\\\\\')
        content = content.replace('\n', '\\\\n')
        content = content.replace('`', '')
        # content = content.replace('\\\\\\\\"', '\\\\"')
        # content = content.replace("\\\\\\\\'", "\\\\'")
        # content = content.replace('"', '\\"').replace("'", "\\'")
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

class RecursiveException(Exception):
    "Raised when the function is not defined yet"
    pass

class TypeWalker(NodeWalker):
    def __init__(self):
        super().__init__()
        self.symtable = {}
        self.parameters = []
        self.name_cnt_dict = {}
        self.def_use_mode = True
        self.unofficial_method = False
        self.has_opt = False
        self.has_derivative = False  # whether hessian or gradient is used
        self.is_param_block = False  # where or given block
        self.visualizer = LaVisualizer()
        self.logger = LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT)
        self.la_msg = LaMsg.getInstance()
        self.ret_symbol = None
        self.is_generate_ret = False
        self.constants = ['π']
        self.pattern = re.compile("[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*")
        self.multi_lhs_list = []
        self.multi_dim_list = []    # P ∈ ℝ^(4 × dd)
        self.lhs_list = []
        # self.directive_parsing = True   # directives grammar
        self.sum_subs = []
        self.sum_sym_list = []
        self.lhs_subs = []
        self.lhs_sym_list = []
        self.scope_list = []
        self.sum_conds = []
        self.la_content = ''
        self.lhs_sub_dict = {}  # dict of the same subscript symbol from rhs as the subscript of lhs
        self.hessian_list = []  # save hessian definitions, try to check them in the end
        self.hessian_sum_list = []  # summation for evaluating sparse hessian
        self.visiting_lhs = False
        self.visiting_solver_eq = False  # e.g: Ax = b
        self.cur_eq_type = EqTypeEnum.DEFAULT
        self.solved_func = []
        self.need_mutator = False   # whether the node tree needs to be changed: solver
        self.unknown_sym = []
        self.mesh_type_list = []    # different mesh types in current file
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
        self.local_func_error = False
        self.local_func_name = ''  # function name when visiting expressions
        self.local_func_dict = {}  # local function name -> parameter dict
        self.visiting_opt = False  # optimization
        self.opt_cur_init_list = [] # initialized vars
        self.opt_key = ''
        self.opt_dict = {}
        self.func_data_dict = {}   # local function name -> LocalFuncData
        self.func_mapping_dict = {}# key in func_data_dict -> func name in source code
        self.func_name_dict = {}   # local function node -> local function name
        self.func_sig_dict = {}    # function signature -> identity local function name
        self.func_imported_renaming = {}  # renamed overloading func name -> imported func name
        self.extra_symtable = {}   # symtable for overloaded functions (due to renaming)
        #
        self.desc_dict = {}        # comment for parameters
        self.import_module_list = []
        self.builtin_module_dict = {}
        self.mesh_dict = {}
        self.main_param = ParamsData()
        self.used_params = []
        self.der_vars = []   # variables in derivatives
        self.der_defined_lhs_list = []   # symbol defined as gradient or hessian
        self.lhs_on_der = []             # symbol defined with gradient or hessian
        self.visiting_der = False        # whether current assign has gradient or hessian
        self.opt_syms = []
        self.expr_dict = {}        # lhs id -> symbols in current expr
        self.smooth_dict = {}
        self.mapping_dict = {}
        self.omit_assert = False

    def assert_expr(self, cond, msg):
        """
        Put assertions in the same function
        :param cond: conditional
        :param msg: message
        """
        # if cond:
        #     print("msg: {}".format(msg))
        # if not self.visiting_solver_eq:
        #     assert cond, msg
        if not self.pre_walk:
            if not self.omit_assert:
                assert cond, msg

    def get_sym_sig_dict(self, name_list):
        sig_dict = {}
        for name in name_list:
            if self.symtable[name].is_overloaded():
                for c_index in range(len(self.symtable[name].func_list)):
                    sig = get_func_signature(name, self.symtable[name].func_list[c_index])
                    sig_dict[sig] = self.func_sig_dict[sig]
        return sig_dict

    def get_cur_param_data(self):
        # either main where/given block or local function block
        cur_scope = self.scope_list[-1]
        if cur_scope != 'global':
            return self.func_data_dict[cur_scope].params_data
        self.main_param.symtable = self.symtable
        return self.main_param
        # if self.local_func_parsing:
        #     if self.local_func_name in self.func_data_dict:
        #         return self.func_data_dict[self.local_func_name].params_data
        #     else:
        #         self.assert_expr(True, "error")
        # elif self.visiting_opt:
        #     if self.opt_key in self.opt_dict:
        #         self.copy_data_to_opt()
        #         return self.opt_dict[self.opt_key]
        #     else:
        #         self.assert_expr(True, "error")
        # elif not self.is_main_scope():
        #     return self.func_data_dict[self.cur_scope].params_data
        # self.main_param.symtable = self.symtable
        # return self.main_param

    def get_param_data(self, scope):
        if scope == 'global':
            return self.main_param
        else:
            return self.func_data_dict[scope].params_data

    def get_upper_param_data(self):
        if len(self.scope_list) > 1:
            upper_scope = self.get_upper_scope()
            return self.get_param_data(upper_scope)
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
        new_lhs_list = copy.deepcopy(self.lhs_list)
        # generated ret sym is not supposed to be used in glossary
        if self.is_generate_ret and self.ret_symbol in new_lhs_list:
            new_lhs_list.remove(self.ret_symbol)
        return EquationData('', copy.deepcopy(self.parameters), new_lhs_list,
                            copy.deepcopy(self.import_module_list),  copy.deepcopy(self.symtable),
                            copy.deepcopy(self.desc_dict), self.la_content,
                            copy.deepcopy(self.func_data_dict),
                            copy.deepcopy(self.expr_dict),
                            copy.deepcopy(self.opt_syms))

    def is_inside_sum(self):
        return len(self.sum_subs) > 0

    def reset(self):
        self.reset_state()

    def reset_state(self, la_content=''):
        self.symtable.clear()
        self.parameters.clear()
        self.name_cnt_dict.clear()
        self.hessian_list.clear()
        self.ret_symbol = None
        self.is_generate_ret = False
        self.unofficial_method = False
        self.has_opt = False
        self.has_derivative = False
        self.sum_subs.clear()
        self.sum_sym_list.clear()
        self.multi_lhs_list.clear()
        self.multi_dim_list.clear()
        self.lhs_subs.clear()
        self.lhs_sym_list.clear()
        self.scope_list.clear()
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
        self.local_func_error = False
        self.local_func_name = ''
        self.local_func_dict.clear()
        self.extra_symtable.clear()
        self.func_sig_dict.clear()
        self.func_imported_renaming.clear()
        self.opt_dict.clear()
        self.func_data_dict.clear()
        self.func_mapping_dict.clear()
        self.desc_dict.clear()
        self.import_module_list.clear()
        self.builtin_module_dict.clear()
        self.mesh_dict.clear()
        self.main_param.reset()
        self.used_params.clear()
        self.der_vars.clear()
        self.der_defined_lhs_list.clear()
        self.opt_syms.clear()
        self.expr_dict.clear()
        self.visiting_opt = False
        self.visiting_lhs = False
        self.visiting_solver_eq = False
        self.solved_func.clear()
        self.mesh_type_list.clear()
        self.need_mutator = False
        self.opt_key = ''
        self.omit_assert = False

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
            c_sym = sym
            if sym in self.func_mapping_dict:
                c_sym = self.func_mapping_dict[sym]   # renamed overloading func name -> real name
            ret[c_sym] = "localF;" + c_sym
        for sym in tmp_sym_dict:
            ret[sym] = "localFP;" + sym
        for sym in self.solved_func:
            ret[sym] = "solved;" + sym
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
        # la_debug("generate_var_name: {}".format(ret))
        return ret

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

    def add_sym_type(self, sym, c_type, error_msg='',
                     is_main=False, need_check=True, to_upper=False):
        """
        :param sym: new symbol
        :param c_type: la type
        :param error_msg:
        :param is_main: whether add the symbol to main symtable
        :param need_check: whether we need to check function overloading,
        :param to_upper: add the sym to the upper scope level
        func_sig_dict
        :return:
        """
        new_sym_name = None
        target_symtable = self.get_cur_param_data().symtable
        if is_main:
            target_symtable = self.symtable
        else:
            if to_upper:
                upper_scope = self.scope_list[-2]
                if upper_scope != 'global':
                    target_symtable = self.func_data_dict[upper_scope].params_data.symtable
                else:
                    target_symtable = self.symtable
        check = False  # automatically infer check tag
        if self.scope_list[-1] == 'global':
            check = True
        if sym not in target_symtable:
            target_symtable[sym] = c_type
        elif target_symtable[sym].is_function():
            if target_symtable[sym].is_overloaded():
                # append new type
                success = target_symtable[sym].add_new_type(c_type)
                if not success:
                    self.assert_expr(False, 'Multiple functions with same signature')
            else:
                if target_symtable[sym].get_overloading_signature() != c_type.get_overloading_signature():
                    target_symtable[sym] = OverloadingFunctionType(func_list=[target_symtable[sym], c_type])
                else:
                    self.assert_expr(False, 'Multiple functions with same signature')
        else:
            self.assert_expr(False, error_msg)
        if need_check and check:
            # it's safe here since the above assertion is not triggered
            if c_type.is_function() and not c_type.is_overloaded():
                sig = get_func_signature(sym, c_type)
                la_debug("cur sig:{}".format(sig))
                la_debug("cur func_sig_dict:{}".format(self.func_sig_dict))
                if sig not in self.func_sig_dict:
                    n_name = self.generate_var_name(sym)
                    self.func_sig_dict[sig] = n_name
                    self.extra_symtable[n_name] = c_type
                    self.func_mapping_dict[n_name] = sym
                    la_debug("n_name:{}".format(n_name))
                    new_sym_name = n_name
                if not self.pre_walk:
                    la_debug("sym:{}, sig:{}".format(sym, c_type.get_signature()))
                    la_debug("self.func_sig_dict:{}".format(self.func_sig_dict))
        return new_sym_name

    def get_sym_type(self, sym):
        """
        get la type by considering local function
        :param sym: symbol name
        :return: la type
        """
        node_type = LaVarType(VarTypeEnum.INVALID)
        resolved = False
        for cur_index in range(len(self.scope_list)):
            cur_scope = self.scope_list[len(self.scope_list)-1-cur_index]
            if cur_scope == 'global':
                cur_symtable = self.symtable
            else:
                cur_symtable = self.func_data_dict[cur_scope].params_data.symtable
            if sym in cur_symtable:
                node_type = cur_symtable[sym]
                resolved = True
                break
        if not resolved:
            if sym in self.extra_symtable:
                node_type = self.extra_symtable[sym]
        return node_type

    def is_sym_existed(self, sym):
        existed = False
        for cur_index in range(len(self.scope_list)):
            cur_scope = self.scope_list[len(self.scope_list)-1-cur_index]
            if cur_scope == 'global':
                cur_symtable = self.symtable
            else:
                cur_symtable = self.func_data_dict[cur_scope].params_data.symtable
            if sym in cur_symtable:
                existed = True
                break
        if not existed:
            if sym in self.extra_symtable:
                existed = True
        return existed

    def is_sym_parameter(self, sym):
        # check whether the sym is a parameter in currect scope: local func params or main params
        is_param = False
        cur_scope = self.get_cur_scope()
        if cur_scope == 'global':
            if sym in self.parameters:
                is_param = True
        else:
            if sym in self.func_data_dict[cur_scope].params_data.parameters:
                is_param = True
            if not is_param:
                if sym in self.parameters:
                    is_param = True
        return is_param

    def check_sym_existence(self, sym, msg, existed=True):
        """
        :param sym: symbol name
        :param msg: error message
        :param existed: the symbol should exist or not
        :return:
        """
        if existed:
            resolved = False
            for cur_index in range(len(self.scope_list)):
                cur_scope = self.scope_list[len(self.scope_list) - 1 - cur_index]
                if cur_scope == 'global':
                    cur_symtable = self.symtable
                else:
                    cur_symtable = self.func_data_dict[cur_scope].params_data.symtable
                if sym in cur_symtable:
                    resolved = True
                    break
            self.assert_expr(existed == resolved, msg)
        else:
            # only check current scope
            cur_scope = self.scope_list[-1]
            if cur_scope == 'global':
                cur_symtable = self.symtable
            else:
                cur_symtable = self.func_data_dict[cur_scope].params_data.symtable
            self.assert_expr(sym not in cur_symtable, msg)

    def walk_Node(self, node):
        print('Reached Node: ', node)

    def walk_object(self, o):
        raise Exception('Unexpected type %s walked', type(o).__name__)

    def walk_Start(self, node, **kwargs):
        la_debug("TypeWalker begin ==================================================================================================================")
        self.main_param.symtable = self.symtable
        self.pre_walk = True if 'pre_walk' in kwargs else False
        self.scope_list = ['global']
        # self.symtable.clear()
        self.visualizer.visualize(node, self.pre_walk)  # visualize
        ir_node = StartNode(parse_info=node.parseinfo, raw_text=node.text)
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
        def handle_assignment(assign_node):
            for cur_index in range(len(assign_node.left)):
                if type(assign_node.left[cur_index]).__name__ == 'IdentifierSubscript':
                    lhs_sym = self.walk(assign_node.left[cur_index].left).ir.get_main_id()
                else:
                    lhs_sym = self.walk(assign_node.left[cur_index]).ir.get_main_id()
                if lhs_sym not in self.lhs_list:
                    self.lhs_list.append(lhs_sym)
                if len(lhs_sym) > 1:
                    multi_lhs_list.append(lhs_sym)
                for cur_expr in assign_node.right:
                    self.rhs_raw_str_list.append(cur_expr.text)
            if self.pre_walk and hasattr(assign_node, 'v') and assign_node.v:
                # solver
                self.visiting_solver_eq = True
                for cur_v in assign_node.v:
                    v_info = self.walk(cur_v)
                    v_id = v_info.id[0].get_main_id()
                    if v_info.type.is_node(IRNodeType.FunctionType):
                        self.solved_func.append(v_id)
                    self.lhs_list.append(v_id)
                    if len(v_id) > 1:
                        multi_lhs_list.append(v_id)
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
                if is_ast_assignment(vblock_info[0]):
                    handle_assignment(vblock_info[0])
                    # assignment inside summation, e.g.: a = sum_* ***
                    for cur_index in range(len(vblock_info[0].right)):
                        c_rhs = vblock_info[0].right[cur_index]
                        if type(c_rhs).__name__ == 'Expression' and type(c_rhs.value).__name__ == 'Factor' and c_rhs.value.op and type(c_rhs.value.op).__name__ == 'Summation':
                            for extra in c_rhs.value.op.extra:
                                handle_assignment(extra)
                elif type(vblock_info[0]).__name__ == 'LocalFunc':
                    if isinstance(vblock_info[0].name, str):
                        func_sym = vblock_info[0].name
                    else:
                        self.visiting_lhs = True
                        func_sym = self.walk(vblock_info[0].name).ir.get_main_id()
                        self.visiting_lhs = False
                    if func_sym in self.func_data_dict:
                        new_sym = self.generate_var_name(func_sym)
                        self.func_data_dict[new_sym] = LocalFuncData(name=new_sym)
                        self.func_mapping_dict[new_sym] = func_sym
                        func_sym = new_sym
                    else:
                        self.func_data_dict[func_sym] = LocalFuncData(name=func_sym)
                        self.func_mapping_dict[func_sym] = func_sym
                    la_debug("func_sym:{}".format(func_sym))
                    self.local_func_dict[func_sym] = {}
                    self.func_name_dict[vblock_info[0].text] = func_sym   # save mapping
                    self.local_func_syms.append(func_sym)
                    if self.pre_walk:
                        self.local_func_parsing = True
                        self.local_func_name = func_sym
                        if len(self.func_mapping_dict[func_sym]) > 1:
                            multi_lhs_list.append(self.func_mapping_dict[func_sym])
                        self.is_param_block = True
                        for par_def in vblock_info[0].defs:
                            par_type = self.walk(par_def, **kwargs)
                            type_dict = par_type.get_type_dict()
                            self.local_func_dict[func_sym].update(type_dict)
                            for par in type_dict.keys():
                                if len(par) > 1:
                                    multi_lhs_list.append(par)
                        # assignment inside local function, e.g.: f(x) = *** where * = ***
                        for extra in vblock_info[0].extra:
                            handle_assignment(extra)
                            for cur_index in range(len(extra.right)):
                                c_rhs = extra.right[cur_index]
                                if type(c_rhs).__name__ == 'Expression' and type(
                                        c_rhs.value).__name__ == 'Factor' and c_rhs.value.sub:
                                    # extract expression insdie subexpression
                                    c_rhs = c_rhs.value.sub.value
                                if type(c_rhs).__name__ == 'Expression' and type(
                                        c_rhs.value).__name__ == 'Factor' and c_rhs.value.op and type(
                                        c_rhs.value.op).__name__ == 'Summation':
                                    for extra in c_rhs.value.op.extra:
                                        handle_assignment(extra)
                        self.local_func_parsing = False
                        self.is_param_block = False
                    for cur_expr in vblock_info[0].expr:
                        self.rhs_raw_str_list.append(cur_expr.text)
                elif type(vblock_info[0]).__name__ == 'DeSolver':
                    # De Solver
                    self.visiting_solver_eq = True
                    v_info = self.walk(vblock_info[0].u)
                    v_id = v_info.ir.get_main_id()
                    # if v_info.ir.is_node(IRNodeType.FunctionType):
                    #     self.solved_func.append(v_id)
                    self.lhs_list.append(v_id)
                    if len(v_id) > 1:
                        multi_lhs_list.append(v_id)
                else:
                    self.rhs_raw_str_list.append(vblock_info[0].text)
        ir_node.vblock = vblock_list
        params_list, stat_list, index_list = ir_node.get_block_list()
        # check function assignment
        if self.pre_walk:
            for index in range(len(stat_list)):
                if is_ast_assignment(stat_list[index]):
                    if stat_list[index].right:
                        # check whether rhs is function type
                        rhs = stat_list[index].right[0]
                        if type(rhs).__name__ == 'Expression' and type(rhs.value).__name__ == 'Factor' and rhs.value.id0:
                            # specific stat: lhs = id_subs
                            try:
                                assign_node = self.walk(stat_list[index], **kwargs).ir
                                lhs_id_node = assign_node.left[0]
                                rhs_id_node = assign_node.right[0].value.id
                                if rhs_id_node.la_type.is_function():
                                    if lhs_id_node.contain_subscript():
                                        self.assert_expr(lhs_id_node.node_type == IRNodeType.SequenceIndex, get_err_msg_info(lhs_id_node.parse_info, "Invalid assignment for function"))
                            except Exception as e:
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
        self.convert_parameters()
        self.fill_func_names()
        self.check_sparse_hessian(ir_node.vblock)
        # set properties
        self.main_param.parameters = self.parameters
        self.main_param.symtable = self.symtable
        self.print_all()
        return ir_node

    def convert_parameters(self):
        la_debug("before convert_parameters:{}".format(self.parameters))
        # process in the end
        for c_index in range(len(self.parameters)):
            if self.get_sym_type(self.parameters[c_index]).is_function():
                if not self.get_sym_type(self.func_mapping_dict[self.parameters[c_index]]).is_overloaded():
                    # if it's not overloading, then convert the name back
                    self.parameters[c_index] = self.func_mapping_dict[self.parameters[c_index]]
        la_debug("after convert_parameters:{}".format(self.parameters))

    def fill_func_names(self):
        # refill func names in overloaded funcs
        for k,v in self.symtable.items():
            if v.is_overloaded():
                if v.fname_list is None or len(v.fname_list) != len(v.func_list):
                    # refill
                    self.symtable[k].fname_list = [self.func_sig_dict[get_func_signature(k, c_type)] for c_type in v.func_list]

    def check_sparse_hessian(self, stat_list):
        for hess in self.hessian_list:
            node = self.get_assign_node(hess.upper, stat_list)
            # clear
            self.hessian_sum_list.clear()
            need_sparse = False
            if node:
                need_sparse = self.check_assign_node(node)
            if need_sparse:
                node.need_sparse_hessian = True
                node.hessian_var = hess.lower
                node.new_hessian_name = self.generate_var_name("hess")
                node.need_sparse = True
                hess.ir_node.new_hessian_name = node.new_hessian_name
                # handle summation subscripts
                for sum in self.hessian_sum_list:
                    sum.sum_index_list = IRSumIndexVisitor.getInstance().get_sub_list(hess.lower, self.get_sym_type(hess.lower), sum)
                    la_debug("cur sum list: {}, sym:{}".format(sum.sum_index_list, hess.lower))
                # set sparse type
                # hess.ir_node.la_type.sparse = True
            print(node)

    def check_assign_node(self, node):
        # check whether the current assignment consists of a list of summations
        # return False
        return self.check_expr_node(node.right[0])
    
    def check_expr_node(self, node):
        # check whether the current expression/factor node consists of a list of summations
        factor = node
        if factor.is_node(IRNodeType.Subexpression):
            factor = factor.value
        if factor.is_node(IRNodeType.Expression):
            factor = factor.value
        if factor.is_node(IRNodeType.Factor):
            if factor.op:
                if factor.op.is_node(IRNodeType.Summation):
                    self.hessian_sum_list.append(factor.op)
                    return True
            elif factor.sub:
                return self.check_expr_node(factor.sub)
        elif factor.is_node(IRNodeType.Add):
            return self.check_expr_node(factor.left) and self.check_expr_node(factor.right)
        return False
    
    def get_assign_node(self, lhs, stat_list):
        # get assign node for a specific lhs symbol
        res = None
        for node in stat_list:
            if node.is_node(IRNodeType.Assignment):
                if node.left[0].raw_text == lhs:
                    res = node
        return res

    def print_all(self):
        la_debug("TypeWalker end ==================================================================================================================")
        la_debug("func_sig_dict:")
        for k,v in self.func_sig_dict.items():
            la_debug("{} : {}".format(v, k))
        self.logger.info("symtable:")
        for k,v in self.symtable.items():
            la_debug("{} : {}".format(k, v.get_signature()))
        self.logger.info("parameters: {}".format(self.parameters))
        self.logger.info("extra_symtable:".format())
        for k, v in self.extra_symtable.items():
            self.logger.info("{} : {}".format(k, v.get_signature()))
        self.logger.info("func_mapping_dict:{}".format(self.func_mapping_dict))
        self.logger.info("func_name_dict:".format())
        for k, v in self.func_name_dict.items():
            self.logger.info("{} : {}".format(k, v))


    def push_environment(self):
        # self.logger.debug("push_environment: {}".format(self.symtable))
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
        self.saved_extra_symtable = copy.deepcopy(self.extra_symtable)
        self.saved_used_params = copy.deepcopy(self.used_params)
        self.saved_der_vars = copy.deepcopy(self.der_vars)
        self.saved_der_defined_lhs_list = copy.deepcopy(self.der_defined_lhs_list)
        self.saved_opt_syms = copy.deepcopy(self.opt_syms)
        self.saved_opt_dict = copy.deepcopy(self.opt_dict)
        # start from main scope
        self.saved_scope_list = copy.deepcopy(self.scope_list)

    def push_scope_environment(self):
        # used for sum and local func
        self.saved_scope_func_data_dict = copy.deepcopy(self.func_data_dict)


    def pop_environment(self):
        # self.logger.debug("pop_environment: {}".format(self.saved_symtable))
        self.symtable = self.saved_symtable
        self.sum_subs = self.saved_sum_subs
        self.sum_sym_list = self.saved_sum_sym_list
        self.lhs_subs = self.saved_lhs_subs
        self.sum_conds = self.saved_sum_conds
        self.lhs_sub_dict = self.saved_lhs_sub_dict
        self.local_func_dict = self.saved_local_func_dict
        self.func_data_dict = self.saved_func_data_dict
        self.extra_symtable = self.saved_extra_symtable
        self.opt_dict = self.saved_opt_dict
        self.used_params = self.saved_used_params
        self.der_vars = self.saved_der_vars
        self.der_defined_lhs_list = self.saved_der_defined_lhs_list
        self.opt_syms = self.saved_opt_syms
        self.local_func_parsing = False
        self.is_param_block = False
        self.visiting_solver_eq = False
        self.local_func_error = False
        self.scope_list = self.saved_scope_list

    def pop_scope_environment(self):
        self.func_data_dict = self.saved_scope_func_data_dict

    def get_ordered_stat(self, stat_list):
        """
        Apply def-use to sub assignments
        :param stat_list: extra assignment inside summation and local functions
        :return: ir list with correct order
        """
        new_list = []
        tex_list = [None] * len(stat_list)
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
                    self.push_scope_environment()
                    try:
                        type_info = self.walk(cur_stat)
                        new_list.append(type_info.ir)
                        order_list[cur_index] = cnt
                        tex_list[cur_index] = type_info.ir
                        cnt += 1
                        retries = 0
                        # self.logger.debug("expr index:{}, stat:{}".format(cnt, cur_stat.text))
                        break
                    # except AssertionError as e:
                    except Exception as e:
                        self.logger.debug("failed stat:{}, e:{}".format(cur_stat.text, e))
                        retries += 1
                        visited_list[cur_index] = True
                        if retries > len(stat_list):
                            raise e
                        # parse failed, pop saved env
                        self.pop_scope_environment()
                        continue
        return new_list, tex_list

    def get_meshset_assign(self, stat_list):
        ret = []
        name = []
        for index in range(len(stat_list)):
            if is_ast_assignment(stat_list[index]):
                if stat_list[index].right:
                    rhs = stat_list[index].right[0]
                    if type(rhs).__name__ == 'Expression' and type(rhs.value).__name__ == 'Factor' and type(rhs.value.op).__name__ == 'Function':
                        if len(self.builtin_module_dict) > 0:
                            if MESH_HELPER in self.builtin_module_dict and MeshSets in self.builtin_module_dict[MESH_HELPER].r_dict:
                                if rhs.value.op.name == self.builtin_module_dict[MESH_HELPER].r_dict[MeshSets]:
                                    ret.append(index)
                                    name.append(rhs.value.op.params[0].text)
        return ret, name

    def convert_mapping_type(self):
        # Handle mapping type in current scope
        for k, c_type in self.get_cur_param_data().symtable.items():
            if c_type.is_sequence():
                v = c_type.element_type
            else:
                v = c_type
            if v.is_mapping():
                if v.src:
                    # mapping from mesh V,E,F
                    src_type = self.get_sym_type(v.src)
                    self.assert_expr(src_type.is_mesh_element_set(), "Symbol {} should be vertices/edges/faces".format(v.src))
                    self.get_cur_param_data().symtable[k] = SequenceType(size=src_type.length, element_type=v.dst)
                    la_debug("mapping conversion: {}, type:{}, length:{}".format(k, self.get_cur_param_data().symtable[k].get_signature(), self.get_cur_param_data().symtable[v.src].length))
                else:
                    # mapping from element in a set, f ∈ F
                    self.check_sym_existence(v.ele_set, "Symbol {} is not defined".format(v.ele_set))
                    set_type = self.get_sym_type(v.ele_set)
                    la_type = set_type.element_type
                    la_type.owner = set_type.owner
                    if v.subset:
                        # f ⊂ F
                        la_type = set_type
                    else:
                        self.get_cur_param_data().set_checking[k] = v.ele_set
                    self.assert_expr(set_type.is_set(), "Symbol {} should be a set".format(v.ele_set))
                    if c_type.is_sequence():
                        self.get_cur_param_data().symtable[k].element_type = la_type
                    else:
                        self.get_cur_param_data().symtable[k] = la_type
    def gen_block_node(self, stat_list, index_list, ir_node, **kwargs):
        meshset_list, name_list = self.get_meshset_assign(stat_list)
        block_node = BlockNode()
        block_node.meshset_list = meshset_list
        if self.def_use_mode:
            new_list = []
            order_list = [-1] * len(stat_list)  # visited order for all statment
            cnt = 0
            retries = 0
            if len(meshset_list) > 0:
                # parse meshset assignment first, assume mesh always comes from params
                for c_index in range(len(meshset_list)):
                    cur_index = meshset_list[c_index]
                    type_info = self.walk(stat_list[cur_index], **kwargs)
                    ir_node.vblock[index_list[cur_index]] = type_info.ir  # latex use
                    lhs_list = [lhs.get_main_id() for lhs in type_info.ir.left]
                    self.mesh_dict[name_list[c_index]].init_dims(lhs_list)
                    new_list.append(type_info.ir)
                    order_list[cur_index] = cnt
                    cnt += 1
            self.convert_mapping_type()
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
                                if is_ast_assignment(cur_stat):
                                    kwargs[SET_RET_SYMBOL] = True
                                elif type(cur_stat).__name__ != 'LocalFunc' and type(cur_stat).__name__ != 'MultiCondExpr':
                                    # new symbol for return value
                                    self.ret_symbol = "ret"
                                    update_ret_type = True
                                    self.is_generate_ret = True
                                    kwargs[LHS] = self.ret_symbol
                                    self.lhs_list.append(self.ret_symbol)
                            type_info = self.walk(cur_stat, **kwargs)
                            ir_node.vblock[index_list[cur_index]] = type_info.ir  # latex use
                            new_list.append(type_info.ir)
                            if update_ret_type:
                                self.symtable[self.ret_symbol] = type_info.la_type if not isinstance(type_info.la_type, list) else type_info.la_type[0]
                            order_list[cur_index] = cnt
                            cnt += 1
                            retries = 0
                            # self.logger.debug("expr index:{}, stat:{}".format(cnt, cur_stat.text))
                            break
                        # except AssertionError as e:
                        except Exception as e:
                            self.logger.debug("failed stat:{}, e:{}".format(cur_stat.text, e))
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
                    if is_ast_assignment(stat_list[index]):
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
                    self.symtable[self.ret_symbol] = type_info.la_type if not isinstance(type_info.la_type, list) else type_info.la_type[0]
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
                self.assert_expr(cur_set in self.symtable, get_err_msg_info(self.dependency_dim_dict[cur_set], "Symbol {} not defined".format(cur_set)))
        self.is_param_block = False
        return param_ir_list

    def walk_ParamsBlock(self, node, **kwargs):
        self.is_param_block = True
        where_conds = self.walk(node.conds, **kwargs)
        ir_node = ParamsBlockNode(parse_info=node.parseinfo, annotation=node.annotation, conds=where_conds, raw_text=node.text)
        self.is_param_block = False
        return ir_node

    def walk_WhereConditions(self, node, **kwargs):
        ir_node = WhereConditionsNode(parse_info=node.parseinfo, raw_text=node.text)
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

    def walk_DeWhereCondition(self, node, **kwargs):
        # print(node)
        pass

    def walk_WhereCondition(self, node, **kwargs):
        ir_node = WhereConditionNode(attrib=node.attrib, parse_info=node.parseinfo, raw_text=node.text)
        ret = node.text.split(':')
        desc = ':'.join(ret[1:len(ret)])
        if hasattr(node, 'desc'):
            ir_node.desc = node.desc
        type_node = self.walk(node.type, **kwargs)
        if node.attrib:
            self.assert_expr(type_node.la_type.is_integer_element(),
                             get_err_msg_info(node.id[0].parseinfo, "Invalid attribute: element must be integer"))
            if node.attrib == 'index':
                # check index type condition
                type_node.la_type.index_type = True
                if not type_node.la_type.is_scalar():
                    type_node.la_type.element_type.index_type = True
            elif node.attrib == 'vertices':
                if type_node.la_type.is_scalar():
                    type_node.la_type = VertexType()
                elif type_node.la_type.is_set() and type_node.la_type.contains_single_int():
                    type_node.la_type = VertexSetType()
                else:
                    type_node.la_type.element_type = VertexType()
            elif node.attrib == 'edges':
                if type_node.la_type.is_scalar():
                    type_node.la_type = EdgeType()
                elif type_node.la_type.is_set() and type_node.la_type.contains_single_int():
                    type_node.la_type = EdgeSetType()
                else:
                    type_node.la_type.element_type = EdgeType()
            elif node.attrib == 'faces':
                if type_node.la_type.is_scalar():
                    type_node.la_type = FaceType()
                elif type_node.la_type.is_set() and type_node.la_type.contains_single_int():
                    type_node.la_type = FaceSetType()
                else:
                    type_node.la_type.element_type = FaceType()
            elif node.attrib == 'tets':
                if type_node.la_type.is_scalar():
                    type_node.la_type = TetType()
                elif type_node.la_type.is_set() and type_node.la_type.contains_single_int():
                    type_node.la_type = TetSetType()
                else:
                    type_node.la_type.element_type = TetType()
        type_node.parse_info = node.parseinfo
        type_node.la_type.desc = desc
        for id_index in range(len(node.id)):
            id0_info = self.walk(node.id[id_index], **kwargs)
            ir_node.id.append(id0_info.ir)
            id0 = id0_info.content
            # if node.subset:
            #     # surface def
            #     if type_node.la_type.is_vector():
            #         dim = type_node.la_type.rows
            #         self.smooth_dict[id0] = dim
            if hasattr(node, 'desc') and node.desc is not None:
                self.desc_dict[id0_info.ir.get_main_id()] = node.desc
            if True:
                self.handle_identifier(id0, id0_info.ir, type_node)
                # self.logger.debug("param index:{}".format(kwargs[PARAM_INDEX]))
                if not self.local_func_parsing and not self.visiting_opt and not self.visiting_solver_eq:
                    # main params: due to multiple blocks
                    if type_node.la_type.is_function():
                        sig = get_func_signature(id0, type_node.la_type)
                        # if sig in self.func_sig_dict and type_node.la_type.is_overloaded():
                        # make sure it has func overloading
                        # handle parameters in the end, since now the final type of the sym is unknown
                        self.parameters[kwargs[PARAM_INDEX]+id_index] = self.func_sig_dict[sig]
                        # self.update_parameters(id0, kwargs[PARAM_INDEX]+id_index)
                        # else:
                        #     self.update_parameters(id0, kwargs[PARAM_INDEX] + id_index)
                    else:
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
                elif type_node.la_type.is_mapping():
                    self.mapping_dict[id0] = type_node
                    if node.subset:
                        type_node.subset = True
                        type_node.la_type.subset = True
        ir_node.type = type_node
        ir_node.belong = node.belong
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
        ir_node = MatrixTypeNode(parse_info=node.parseinfo, raw_text=node.text)
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
        ir_node = VectorTypeNode(parse_info=node.parseinfo, raw_text=node.text)
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
        if node.attr and 'sparse' in node.attr:
            la_type.sparse = True
        return ir_node

    def walk_ScalarType(self, node, **kwargs):
        ir_node = ScalarTypeNode(parse_info=node.parseinfo, raw_text=node.text)
        la_type = ScalarType()
        if node.z:
            la_type = ScalarType(is_int=True)
            ir_node.is_int = True
        ir_node.la_type = la_type
        return ir_node

    def walk_NamedType(self, node, **kwargs):
        ir_node = NamedTypeNode(name=node.text, parse_info=node.parseinfo, raw_text=node.text)
        la_type = ScalarType()
        if node.v:
            la_type = VertexSetType()
        elif node.e:
            la_type = EdgeSetType()
        elif node.f:
            la_type = FaceSetType()
        elif node.t:
            la_type = TetSetType()
        elif node.s:
            la_type = SimplicialSetType()
        elif node.m:
            # init dims later
            cur_mesh = MeshTypeEnum.DEFAULT
            if node.m.tri:
                cur_mesh = MeshTypeEnum.TRIANGLE
            elif node.m.point:
                cur_mesh = MeshTypeEnum.POINTCLOUD
            elif node.m.poly:
                cur_mesh = MeshTypeEnum.POLYGON
            elif node.m.tet:
                cur_mesh = MeshTypeEnum.TETRAHEDRON
            elif node.m.ph:
                cur_mesh = MeshTypeEnum.POLYHEDRON
            elif node.m.m:
                cur_mesh = MeshTypeEnum.TRIANGLE
            la_type = MeshType(cur_mesh=cur_mesh)
            if cur_mesh not in self.mesh_type_list:
                self.mesh_type_list.append(cur_mesh)
        ir_node.la_type = la_type
        return ir_node

    def walk_SetType(self, node, **kwargs):
        ir_node = SetTypeNode(parse_info=node.parseinfo, raw_text=node.text)
        int_list = []
        type_list = []
        cnt = 1
        if node.type:
            ir_node.type = node.type
            cnt = len(node.type)
            for t in node.type:
                if t == 'ℤ':
                    int_list.append(True)
                    type_list.append(ScalarType(is_int=True))
                else:
                    int_list.append(False)
                    type_list.append(ScalarType())
        elif node.type1:
            ir_node.type1 = node.type1
            cnt_info = self.walk(node.cnt, **kwargs)
            if isinstance(cnt_info.content, int):
                cnt = cnt_info.content
                ir_node.cnt = cnt
            if node.type1 == 'ℤ':
                int_list = [True] * cnt
                type_list = [ScalarType(is_int=True)] * cnt
            else:
                int_list = [False] * cnt
                type_list = [ScalarType()] * cnt
        elif node.type2:
            ir_node.type2 = node.type2
            if node.cnt:
                cnt_info = self.walk(node.cnt, **kwargs)
                cnt = cnt_info.content
                ir_node.cnt = cnt
            if node.type2 == 'ℤ':
                int_list = [True] * cnt
                type_list = [ScalarType(is_int=True)] * cnt
            else:
                int_list = [False] * cnt
                type_list = [ScalarType()] * cnt
        elif node.sub_types:
            ir_node.sub_types = []
            for sub_type in node.sub_types:
                type_info = self.walk(sub_type, **kwargs)
                type_list.append(type_info.la_type)
                ir_node.sub_types.append(type_info)
            cnt = len(type_list)
        elif node.homogeneous_types:
            ir_node.homogeneous_types = []
            for h_type in node.homogeneous_types:
                type_info = self.walk(h_type, **kwargs)
                type_list.append(type_info.la_type)
                ir_node.homogeneous_types.append(type_info)
            cnt = len(type_list)
        ir_node.la_type = SetType(size=cnt, int_list=int_list, type_list=type_list, element_type=ScalarType())
        return ir_node

    def walk_TupleType(self, node, **kwargs):
        ir_node = TupleTypeNode(parse_info=node.parseinfo, raw_text=node.text)
        type_list = []
        ir_node.sub_types = []
        index_type = False
        for sub_type in node.sub_types:
            type_info = self.walk(sub_type, **kwargs)
            type_list.append(type_info.la_type)
            ir_node.sub_types.append(type_info)
            index_type = type_info.la_type.index_type
        ir_node.la_type = TupleType(type_list=type_list, index_type=index_type)
        return ir_node

    def walk_FunctionType(self, node, **kwargs):
        ir_node = FunctionTypeNode(parse_info=node.parseinfo, raw_text=node.text)
        ir_node.empty = node.empty
        ir_node.separators = node.separators
        params = []
        if node.params:
            for index in range(len(node.params)):
                param_node = self.walk(node.params[index], **kwargs)
                ir_node.params.append(param_node)
                params.append(param_node.la_type) 
        ret_list = []
        for cur_index in range(len(node.ret)):
            ret_node = self.walk(node.ret[cur_index], **kwargs)
            ir_node.ret = ret_node
            ret = ret_node.la_type
            ret_list.append(ret) 
        la_type = FunctionType(params=params, ret=ret_list)
        self.check_func_template(la_type, ret_node.parse_info)
        ir_node.la_type = la_type
        return ir_node

    def walk_MappingType(self, node, **kwargs):
        ir_node = MappingTypeNode(parse_info=node.parseinfo, raw_text=node.text)
        if node.src:
            src_info = self.walk(node.src, **kwargs)
            dst_node = self.walk(node.dst, **kwargs)
            dst_type = dst_node.la_type
            self.assert_expr(dst_type.is_scalar() or dst_type.is_vector() or dst_type.is_matrix(), get_err_msg_info(node.parseinfo, "Invalid mapping type"))
            ir_node = MappingTypeNode(src=src_info.ir, dst=dst_node, parse_info=node.parseinfo, raw_text=node.text)
            ir_node.src = src_info.ir
            ir_node.dst = dst_node
            la_type = MappingType(src=src_info.ir.get_main_id(), dst=dst_node.la_type)
        else:
            sym_info = self.walk(node.s, **kwargs)
            ir_node.ele_set = sym_info.ir
            la_type = MappingType(ele_set=sym_info.ir.get_main_id())
        ir_node.la_type = la_type
        return ir_node

    def update_parameters(self, identifier, index):
        if self.contain_subscript(identifier):
            arr = self.get_all_ids(identifier)
            self.parameters[index] = arr[0]
        else:
            self.parameters[index] = identifier

    ###################################################################
    def walk_ImportVar(self, node, **kwargs):
        rname = None
        if node.r:
            rname = self.walk(node.r, **kwargs).ir
        return NodeInfo(ir=ImportVarNode(self.walk(node.name, **kwargs).ir, rname))
    def add_builtin_module_data(self, module, params_list=[], name_list=[], r_dict=None):
        if module not in self.builtin_module_dict:
            self.builtin_module_dict[module] = BuiltinModuleData(module, self.generate_var_name(module),params_list=params_list,name_list=name_list,r_dict=r_dict)
        return self.builtin_module_dict[module]
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
        r_dict = {}
        for cur_name in node.names:
            import_var = self.walk(cur_name, **kwargs).ir
            name_ir = import_var.name
            if import_var.rname:
                r_dict[name_ir.get_name()] = import_var.rname.get_name()
            else:
                r_dict[name_ir.get_name()] = name_ir.get_name()
            name_ir_list.append(name_ir)
            name_list.append(name_ir.get_name())
        import_all = False
        if node.star:
            import_all = True
        pkg_name = package_info.ir.get_name()
        if pkg_name in PACKAGES_DICT:
            package = package_info.ir
            func_list = PACKAGES_DICT[pkg_name]
            if import_all:
                name_list = func_list
                name_ir_list = [IdNode(name) for name in name_list]
                for c_name in name_list:
                    r_dict[c_name] = c_name
            else:
                # check specific name
                for name in name_list:
                    self.assert_expr(name in func_list, get_err_msg(get_line_info(node.parseinfo),
                                                               get_line_info(node.parseinfo).text.find(name),
                                                               "Function {} not exist".format(name)))
            if not self.pre_walk:
                self.add_builtin_module_data(pkg_name, params_list, name_list, r_dict)
            if pkg_name == MESH_HELPER:
                for name in name_list:
                    # self.symtable[r_dict[name]] = get_sym_type_from_pkg(name, pkg_name)
                    # add func names to symtable, for dynamic func types, ignore the dimension info for now
                    sym_type = get_sym_type_from_pkg(name, pkg_name, None)
                    using_name = r_dict[name]
                    new_sym_name = self.add_sym_type(r_dict[name], sym_type, get_err_msg_info(node.parseinfo,
                                                                            "Parameter {} has been defined.".format(
                                                                                name)))
                    self.func_imported_renaming[r_dict[name]] = name
                    if new_sym_name:
                        self.func_imported_renaming[new_sym_name] = name
                        using_name = new_sym_name
                    if sym_type.is_overloaded():
                        # update self.func_sig_dict, use predefined names if possible
                        f_size = len(sym_type.func_list)
                        if sym_type.fname_list:
                            name_list = sym_type.fname_list
                        else:
                            name_list = [self.generate_var_name(using_name) for i in range(len(using_name))]
                        for cur_f_index in range(len(sym_type.func_list)):
                            cur_f_type = sym_type.func_list[cur_f_index]
                            sig = get_func_signature(using_name, cur_f_type)
                            if sig not in self.func_sig_dict:
                                n_name = name_list[cur_f_index]
                                self.func_sig_dict[sig] = n_name
        else:
            module = package_info.ir
            self.import_module_list.append(DependenceData(module.get_name(), params_list, name_list))
        import_node = ImportNode(package=package, module=module, names=name_ir_list, separators=node.separators,
                                     params=params, r_dict=r_dict, import_all=import_all, parse_info=node.parseinfo, raw_text=node.text)
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
        if ret_type.is_set():
            # union
            ir_node = UnionNode(left_info.ir, right_info.ir, union_format=UnionFormat.UnionAdd, parse_info=node.parseinfo, raw_text=node.text)
        else:
            ir_node = AddNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, raw_text=node.text)
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
        if ret_type.is_set():
            # difference
            ir_node = DifferenceNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, raw_text=node.text)
        else:
            ir_node = SubNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, raw_text=node.text)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        return ret_info

    def walk_AddSub(self, node, **kwargs):
        self.assert_expr(IF_COND in kwargs, get_err_msg(get_line_info(node.parseinfo),
                                                   get_line_info(node.parseinfo).text.find(node.op),
                                                   "{} must be used inside if codition".format(node.op)))
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ret_type, need_cast = self.type_inference(TypeInferenceEnum.INF_ADD, left_info, right_info)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node = AddSubNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, op=node.op, raw_text=node.text)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        return ret_info

    def walk_Union(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ret_info = NodeInfo(left_info.la_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node = UnionNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, raw_text=node.text)
        ir_node.la_type = left_info.la_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        return ret_info

    def walk_Intersection(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ret_info = NodeInfo(left_info.la_type, symbols=left_info.symbols.union(right_info.symbols))
        ir_node = IntersectionNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, raw_text=node.text)
        ir_node.la_type = left_info.la_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        ret_info.ir = ir_node
        return ret_info

    def walk_Multiply(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        op_type = MulOpType.MulOpInvalid
        if hasattr(node, 'op') and node.op and node.op == '⋅':
            op_type = MulOpType.MulOpDot
            if left_info.la_type.is_vector() and right_info.la_type.is_vector() and is_same_expr(left_info.la_type.rows, right_info.la_type.rows):
                return self.walk_DotProduct(node, **kwargs)
        return self.make_mul_info(left_info, right_info, op_type, parse_info=node.parseinfo, raw_text=node.text)

    def make_mul_info(self, left_info, right_info, op=MulOpType.MulOpInvalid, parse_info=None, raw_text=None):
        ret_type, need_cast = self.type_inference(TypeInferenceEnum.INF_MUL, left_info, right_info)
        sym_set = left_info.symbols.union(right_info.symbols)
        # I in block matrix
        if ret_type is not None:
            ret_type.symbol = ""
            for sym in sym_set:
                ret_type.symbol += sym
        ret_info = NodeInfo(ret_type, symbols=sym_set)
        ir_node = MulNode(left_info.ir, right_info.ir, parse_info=left_info.ir.parse_info if parse_info is None else parse_info, op=op, raw_text=raw_text)
        ir_node.la_type = ret_type
        left_info.ir.set_parent(ir_node)
        right_info.ir.set_parent(ir_node)
        if need_cast:
            ir_node = CastNode(value=ir_node, raw_text=raw_text)
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
        ir_node = DivNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, op=op_type, raw_text=node.text)
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
        self.local_func_error = False
        local_func_name = self.func_name_dict[node.text]
        self.push_scope(local_func_name)
        def_type = LocalFuncDefType.LocalFuncDefInvalid
        if node.def_p:
            def_type = LocalFuncDefType.LocalFuncDefParenthesis
        elif node.def_s:
            def_type = LocalFuncDefType.LocalFuncDefBracket
        if isinstance(node.name, str):
            original_local_func_name = node.name
        else:
            self.visiting_lhs = True
            original_local_func_name = self.walk(node.name).ir.get_main_id()
            self.visiting_lhs = False
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
        # self.assert_expr(local_func_name not in self.symtable, get_err_msg(get_line_info(node.parseinfo),0,"Symbol {} has been defined".format(local_func_name)))
        ir_node = LocalFuncNode(name=IdNode(original_local_func_name, parse_info=node.parseinfo), expr=[],
                                parse_info=node.parseinfo, raw_text=node.text, defs=par_defs,
                                def_type=def_type, identity_name=local_func_name)
        ir_node.scope_name = local_func_name
        # handle mapping type here
        self.convert_mapping_type()
        # extra exprs
        if node.extra and len(node.extra) > 0:
            ir_node.extra_list, ir_node.tex_list = self.get_ordered_stat(node.extra)
        ret_list = []
        expr_list = []
        param_tps = []
        par_names = []
        if type(node.name).__name__ == 'IdentifierSubscript':
            for index in range(len(node.name.right)):
                param_node = self.walk(node.name.right[index], **kwargs).ir
                self.assert_expr(param_node.get_name() in par_dict, get_err_msg_info(param_node.parse_info,
                                                                                     "Parameter {} hasn't been defined".format(
                                                                                         param_node.get_name())))
                ir_node.params.append(param_node)
                # param_tps.append(param_node.la_type)
                param_tps.append(par_dict[param_node.get_name()])
                par_names.append(param_node.get_name())
                ir_node.n_subs = len(node.name.right)
        else:
            for index in range(len(node.subs)):
                param_node = self.walk(node.subs[index], **kwargs).ir
                # assert param_node.get_name() in self.parameters, get_err_msg_info(param_node.parse_info, "Parameter {} hasn't been defined".format(param_node.get_name()))
                self.assert_expr(param_node.get_name() in par_dict, get_err_msg_info(param_node.parse_info,
                                                                                     "Parameter {} hasn't been defined".format(
                                                                                         param_node.get_name())))
                ir_node.params.append(param_node)
                # param_tps.append(param_node.la_type)
                param_tps.append(par_dict[param_node.get_name()])
                par_names.append(param_node.get_name())
            ir_node.n_subs = len(node.subs)
        for index in range(len(node.params)):
            param_node = self.walk(node.params[index], **kwargs).ir
            # assert param_node.get_name() in self.parameters, get_err_msg_info(param_node.parse_info, "Parameter {} hasn't been defined".format(param_node.get_name()))
            self.assert_expr(param_node.get_name() in par_dict, get_err_msg_info(param_node.parse_info, "Parameter {} hasn't been defined".format(param_node.get_name())))
            ir_node.params.append(param_node)
            # param_tps.append(param_node.la_type)
            param_tps.append(par_dict[param_node.get_name()])
            par_names.append(param_node.get_name())
        # self.assert_expr(len(par_names) == len(par_defs), get_err_msg(get_line_info(node.parseinfo), 0,
        #                                                                    "Function {} needs {} parameters but {} defined".format(
        #                                                                        local_func_name, len(par_names), len(par_defs))))
        self.func_data_dict[local_func_name].params_data.parameters = par_names
        ir_node.separators = node.separators
        #
        cur_symbols = set()
        for cur_index in range(len(node.expr)):
            expr_info = self.walk(node.expr[cur_index], **kwargs)
            expr_info.ir.set_parent(ir_node)
            expr_list.append(expr_info.ir)
            ret_list.append(expr_info.ir.la_type)
            cur_symbols = cur_symbols.union(expr_info.symbols)
        ir_node.la_type = FunctionType(params=param_tps, ret=ret_list)
        self.check_func_template(ir_node.la_type)
        self.add_sym_type(original_local_func_name, ir_node.la_type, get_err_msg(get_line_info(node.parseinfo),0,"Symbol {} has been defined".format(local_func_name)), is_main=True)
        if self.local_func_error:
            # error happened, revisit expr
            expr_list.clear()
            ret_list.clear()
            for cur_index in range(len(node.expr)):
                expr_info = self.walk(node.expr[cur_index], **kwargs)
                expr_info.ir.set_parent(ir_node)
                expr_list.append(expr_info.ir)
                ret_list.append(expr_info.ir.la_type)
                cur_symbols = cur_symbols.union(expr_info.symbols)
        ir_node.expr = expr_list
        self.extra_symtable[local_func_name] = ir_node.la_type
        self.func_sig_dict[get_func_signature(original_local_func_name, ir_node.la_type)] = local_func_name
        ir_node.symbols = cur_symbols.union(set(par_names))
        # self.symtable[local_func_name] = ir_node.la_type
        self.local_func_parsing = False
        self.expr_dict[local_func_name] = list(ir_node.symbols) + [local_func_name]
        self.pop_scope()
        return NodeInfo(ir=ir_node)
    
    def check_func_template(self, func_type, parse_info=None):
        # check whether the current local function
        template_symbols = {}
        template_ret = []
        for index in range(len(func_type.params)):
            if func_type.params[index].is_scalar():
                pass
            elif func_type.params[index].is_vector():
                if isinstance(func_type.params[index].rows, str) and func_type.params[index].rows not in self.symtable:
                    if func_type.params[index].rows not in template_symbols:
                        template_symbols[func_type.params[index].rows] = index
            elif func_type.params[index].is_matrix():
                if isinstance(func_type.params[index].rows, str) and func_type.params[index].rows not in self.symtable:
                    if func_type.params[index].rows not in template_symbols:
                        template_symbols[func_type.params[index].rows] = index
                if isinstance(func_type.params[index].cols, str) and func_type.params[index].cols not in self.symtable:
                    if func_type.params[index].cols not in template_symbols:
                        template_symbols[func_type.params[index].cols] = index
        for cur_index in range(len(func_type.ret)):
            ret = func_type.ret[cur_index]
            if ret.is_vector():
                if isinstance(ret.rows, str):
                    self.assert_expr(ret.rows in self.symtable or ret.rows in template_symbols, get_err_msg_info(parse_info, "Vector as return value of function must have concrete dimension"))
                    if ret.rows in template_symbols:
                        if ret.rows not in template_ret:
                            template_ret.append(ret.rows)
            elif ret.is_matrix():
                if isinstance(ret.rows, str):
                    self.assert_expr(ret.rows in self.symtable or ret.rows in template_symbols, get_err_msg_info(parse_info, "Matrix as return value of function must have concrete dimension"))
                if ret.rows in template_symbols:
                    if ret.rows not in template_ret:
                        template_ret.append(ret.rows)
                if isinstance(ret.cols, str):
                    self.assert_expr(ret.cols in self.symtable or ret.cols in template_symbols, get_err_msg_info(parse_info, "Matrix as return value of function must have concrete dimension"))
                    if ret.cols in template_symbols:
                        if ret.cols not in template_ret:
                            template_ret.append(ret.cols)
        self.logger.debug("template_symbols:{}, template_ret:{}".format(template_symbols, template_ret))
        func_type.template_symbols = template_symbols
        func_type.ret_symbols = template_ret

    def get_eq_node_info(self, node, **kwargs):
        self.unknown_sym.clear()
        self.visiting_solver_eq = True
        self.need_mutator = True
        self.cur_eq_type = EqTypeEnum.DEFAULT
        eq_node = EquationNode([], [], parse_info=node.parseinfo, raw_text=node.text)
        if node.v:
            has_func = False
            for v_index in range(len(node.v)):
                v_info = self.walk(node.v[v_index], **kwargs)
                self.get_cur_param_data().symtable[v_info.id[0].get_main_id()] = v_info.type.la_type
                eq_node.unknown_id = v_info.id[0]
                self.unknown_sym.append(v_info.id[0].get_main_id())
                self.lhs_list.append(v_info.id[0].get_main_id())
                #
                if v_info.type.la_type.is_function():
                    has_func = True
            if has_func:
                params_dict = SolverParamWalker.getInstance().walk_param(node, self.unknown_sym)
                eq_node.params_dict = params_dict
                print("params_dict: {}".format(params_dict))
                if len(params_dict) > 0:
                    for key, value_list in params_dict.items():
                        for sym in value_list:
                            self.assert_expr(sym not in self.symtable, "Parameter {} has been defined".format(sym))
                            self.symtable[sym] = v_info.type.la_type.params[key]
        # elif node.u:
            # incomplete variable type
            # self.omit_assert = True
            # print(node.u)

        for l_index in range(len(node.lexpr)):
            lexpr_info = self.walk(node.lexpr[l_index], **kwargs)
            rexpr_info = self.walk(node.rexpr[l_index], **kwargs)
            eq_node.left.append(lexpr_info.ir)
            eq_node.right.append(rexpr_info.ir)
            self.assert_expr(lexpr_info.ir.la_type.is_same_type(rexpr_info.ir.la_type),
                             "Different types on lhs and rhs")
        self.visiting_solver_eq = False
        self.omit_assert = False
        eq_node.eq_type = self.cur_eq_type
        return NodeInfo(None, ir=eq_node, symbols=eq_node.symbols)

    def walk_Destructure(self, node, **kwargs):
        # multiple lhs and single rhs, rhs type doesn't depend on lhs, lhs has no subscripts
        right_info = self.walk(node.right[0], **kwargs)
        dest_node = DestructuringNode([], [right_info.ir], op=node.op, parse_info=node.parseinfo, raw_text=node.text)
        if isinstance(right_info.la_type, list):
            cur_type = DestructuringType.DestructuringList
            self.assert_expr(len(node.left) == len(right_info.la_type), get_err_msg_info(node.right[0].parseinfo, "Can only unpack all items from list: {} lhs and {} list items ".format(len(node.left), len(right_info.la_type))))
            # return a list by some builtin funcs
            rhs_type_list = right_info.la_type
        elif right_info.la_type.is_tuple():
            cur_type = DestructuringType.DestructuringTuple
            self.assert_expr(len(node.left) == len(right_info.la_type.type_list), get_err_msg_info(node.right[0].parseinfo, "Can only unpack all items from tuple: {} lhs and {} tuple items ".format(len(node.left), len(right_info.la_type.type_list))))
            # unpack tuple type
            rhs_type_list = right_info.la_type.type_list
        elif right_info.la_type.is_set():
            if right_info.la_type.length and isinstance(right_info.la_type.length, int):
                self.assert_expr(len(node.left) == right_info.la_type.length, 
                get_err_msg_info(node.right[0].parseinfo, "Can only unpack all items from set: {} lhs and {} set items ".format(len(node.left), right_info.la_type.length)))
            # set destructuring
            cur_type = DestructuringType.DestructuringSet
            rhs_type_list = len(node.left) * [right_info.la_type.element_type]
        elif right_info.la_type.is_sequence():
            if right_info.la_type.size and isinstance(right_info.la_type.size, int):
                self.assert_expr(len(node.left) == right_info.la_type.size, 
                get_err_msg_info(node.right[0].parseinfo, "Can only unpack all items from sequence: {} lhs and {} sequence items ".format(len(node.left), right_info.la_type.size)))
            # sequence destructuring
            cur_type = DestructuringType.DestructuringSequence
            rhs_type_list = len(node.left) * [right_info.la_type.element_type]
        elif right_info.la_type.is_vector():
            if right_info.la_type.rows and isinstance(right_info.la_type.rows, int):
                self.assert_expr(len(node.left) == right_info.la_type.rows, 
                get_err_msg_info(node.right[0].parseinfo, "Can only unpack all items from vector: {} lhs and {} vector items ".format(len(node.left), right_info.la_type.rows)))
            # vector destructuring
            cur_type = DestructuringType.DestructuringVector
            rhs_type_list = len(node.left) * [right_info.la_type.element_type]
        for cur_index in range(len(node.left)):
            id0_info = self.walk(node.left[cur_index], **kwargs)
            id0 = id0_info.content
            if self.is_sym_existed(id0):  #
                err_msg = "{} has been assigned before".format(id0)
                if sequence in self.parameters:
                    err_msg = "{} is a parameter, can not be assigned".format(sequence)
                self.assert_expr(False, get_err_msg_info(id0_info.ir.parse_info, err_msg))
            dest_node.left.append(id0_info.ir)
            self.get_cur_param_data().symtable[id0] = rhs_type_list[cur_index]
            if cur_index == len(node.left)-1:
                if SET_RET_SYMBOL in kwargs:
                    if self.is_main_scope():
                        self.ret_symbol = id0
        dest_node.cur_type = cur_type
        dest_node.la_list = rhs_type_list
        return NodeInfo(None, ir=dest_node, symbols=right_info.symbols)


    def walk_Assignment(self, node, **kwargs):
        self.visiting_der = False
        # ir
        if hasattr(node, 'lexpr') and node.lexpr:
            return self.get_eq_node_info(node, **kwargs)
        assign_node = AssignNode([], [], op=node.op, parse_info=node.parseinfo, raw_text=node.text)
        if type(node.right[0]).__name__ == 'MultiCondExpr':
            self.assert_expr(len(node.right) == 1, get_err_msg_info(node.right[0].parseinfo, "Invalid multiple rhs"))
            self.assert_expr(len(node.left) == 1, get_err_msg_info(node.left[0].parseinfo, "Invalid multiple lhs"))
        elif type(node.right[0]).__name__ == 'Optimize':
            pass
        elif type(node.right[0].value).__name__ == 'Factor' and node.right[0].value.op and type(node.right[0].value.op).__name__ == 'Function':
            pass
        else:
            self.assert_expr(len(node.right) == 1, get_err_msg_info(node.right[0].parseinfo, "Invalid multiple rhs"))
            # self.assert_expr(len(node.left) == len(node.right), get_err_msg_info(node.left[0].parseinfo, "Invalid assignment: {} lhs and {} rhs".format(len(node.left), len(node.right))))
        parse_remain_lhs_directly = False   #  multiple lhs for argmin, argmax
        la_list = []
        for cur_index in range(len(node.left)):
            self.visiting_lhs = True
            id0_info = self.walk(node.left[cur_index], **kwargs)
            assign_node.left.append(id0_info.ir)
            self.visiting_lhs = False
            id0 = id0_info.content
            if SET_RET_SYMBOL in kwargs:
                if self.is_main_scope():
                    self.ret_symbol = self.get_main_id(id0)
            kwargs[LHS] = id0
            kwargs[ASSIGN_OP] = node.op
            known_subscript = True   # whether subscripts are already defined
            if id0_info.ir.contain_subscript():
                left_ids = self.get_all_ids(id0)
                left_subs = left_ids[1]
                pre_subs = []
                for sub_index in range(len(left_subs)):
                    sub_sym = left_subs[sub_index]
                    if sub_sym == '*':
                        pass
                    elif isinstance(sub_sym, str) and not sub_sym.isnumeric():
                        if not self.is_sym_existed(sub_sym):
                            known_subscript = False
                        self.lhs_subs.append(sub_sym)
                        self.lhs_sym_list.append({})
                        if sub_sym in pre_subs:
                            continue
                        pre_subs.append(sub_sym)
                        self.assert_expr(not self.is_sym_existed(sub_sym), get_err_msg_info(node.left[0].right[sub_index].parseinfo, "Subscript {} has been defined".format(sub_sym)))
                        # assign types to subscripts
                        self.get_cur_param_data().symtable[sub_sym] = ScalarType(index_type=False, is_int=True)
                        self.lhs_sub_dict[sub_sym] = []  # init empty list
            la_remove_key(LHS, **kwargs)
            la_remove_key(ASSIGN_OP, **kwargs)
            #
            if parse_remain_lhs_directly:
                self.get_cur_param_data().symtable[self.get_main_id(id0)] = la_list[cur_index]
                break
            if cur_index == 0:
                # only one rhs, order matters: parse lhs first, then rhs
                right_info = self.walk(node.right[cur_index], **kwargs)
                # rhs_type_list = right_info.la_type if isinstance(right_info.la_type, list) else [right_info.la_type]
                if isinstance(right_info.la_type, list):
                    # return a list by some builtin funcs
                    rhs_type_list = right_info.la_type
                elif right_info.la_type.is_tuple():
                    if len(node.left) == len(right_info.la_type.type_list):
                        # unpack tuple type
                        rhs_type_list = right_info.la_type.type_list
                    else:
                        rhs_type_list = [right_info.la_type]
                else:
                    # make a list
                    rhs_type_list = [right_info.la_type]
                # check rhs node type
                if is_derivative_node(right_info.ir):
                    self.assert_expr(len(node.left) == 1, get_err_msg_info(node.left[0].parseinfo, "Lhs can only be one identifier"))
                    if id0 not in self.der_defined_lhs_list:
                        self.der_defined_lhs_list.append(id0)
            right_type = rhs_type_list[cur_index]
            if len(self.lhs_subs) > 0:
                for cur_s_index in range(len(self.lhs_subs)):
                    cur_sym_dict = self.lhs_sym_list[cur_s_index]
                    if not self.is_sym_existed(self.get_main_id(id0)):
                        self.assert_expr(len(cur_sym_dict) > 0, get_err_msg_info(node.left[0].parseinfo, "Subscript hasn't been used on rhs"))
                    # self.check_sum_subs(self.lhs_subs[cur_index], cur_sym_dict)
                    self.assert_expr(self.check_sum_subs(self.lhs_subs[cur_s_index], cur_sym_dict), get_err_msg_info(node.left[0].parseinfo,
                                                                                          "Subscript has inconsistent dimensions"))
            self.lhs_sym_list.clear()
            self.lhs_subs.clear()
            if right_info.ir.is_node(IRNodeType.Optimize):
                if right_info.ir.opt_type == OptimizeType.OptimizeArgmin or right_info.ir.opt_type == OptimizeType.OptimizeArgmax:
                    la_list = right_info.la_type
                    parse_remain_lhs_directly = True   # no need to parse other rhs, only lhs
                    self.assert_expr(len(node.left) == len(right_info.ir.base_list), get_err_msg_info(node.left[0].parseinfo, "Invalid multiple lhs"))
                    assign_node.optimize_param = True
                    right_type = right_info.la_type[0]
            elif hasattr(right_info.ir, 'value') and right_info.ir.value.is_node(IRNodeType.Factor) and right_info.ir.value.op and right_info.ir.value.op.is_node(IRNodeType.Function):
                if isinstance(right_info.la_type, list):
                    # multiple ret value
                    self.assert_expr(len(node.left) == len(right_info.la_type), get_err_msg_info(node.left[0].parseinfo, "Invalid assignment: {} lhs and {} ret value".format(len(node.left), len(right_info.la_type))))
                    la_list = right_info.la_type
                    parse_remain_lhs_directly = True
                    assign_node.optimize_param = True
                    right_type = right_info.la_type[0]
            # ir
            if cur_index == 0:
                # right list only has one expr
                assign_node.right.append(right_info.ir)
            right_info.ir.set_parent(assign_node)
            id0_info.ir.set_parent(assign_node)
            # y_i = stat
            if self.contain_subscript(id0) and known_subscript:
                assign_node.change_ele_only = True
                # change an element for a predefined symbol
                left_ids = self.get_all_ids(id0)
                left_subs = left_ids[1]
                sequence = left_ids[0]  # y
                self.assert_expr(right_type.is_same_type(self.get_sym_type(sequence).element_type), get_err_msg_info(id0_info.ir.parse_info,
                                                                                   "{} is assigned to different type".format(
                                                                                       sequence)))
            elif self.contain_subscript(id0):
                left_ids = self.get_all_ids(id0)
                left_subs = left_ids[1]
                sequence = left_ids[0]    #y
                if '*' in left_subs:
                    self.assert_expr(right_type.is_vector(), get_err_msg_info(node.parseinfo, "RHS must be vector type"))
                # self.assert_expr('*' not in left_subs, get_err_msg_info(node.parseinfo, "LHS can't have * as subscript"))
                if node.op != '=':
                    self.assert_expr(self.is_sym_existed(sequence), get_err_msg_info(id0_info.ir.parse_info,
                                                                           "{} hasn't been defined".format(sequence)))
                else:
                    if self.is_sym_existed(sequence) and len(left_subs) != 2:  # matrix items
                        err_msg = "{} has been assigned before".format(id0)
                        if sequence in self.parameters:
                            err_msg = "{} is a parameter, can not be assigned".format(sequence)
                        self.assert_expr(False, get_err_msg_info(id0_info.ir.parse_info, err_msg))
                if len(left_subs) == 2:  # matrix
                    if right_info.ir.node_type != IRNodeType.SparseMatrix:
                        self.assert_expr(sequence not in self.parameters, get_err_msg_info(id0_info.ir.parse_info, "{} is a parameter, can not be assigned".format(sequence)))
                    if '*' not in left_subs:
                        if not (right_type.is_matrix() and right_type.sparse):
                            self.assert_expr(right_type.is_scalar(), get_err_msg_info(right_info.ir.parse_info, "RHS has to be scalar"))
                    if right_type is not None and right_type.is_matrix():
                        # sparse mat assign
                        if right_type.sparse:
                            self.get_cur_param_data().symtable[sequence] = right_type
                    if not self.is_sym_existed(sequence):
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
                        dynamic = DynamicTypeEnum.DYN_INVALID
                        for cur_sub_index in range(len(left_subs)):
                            cur_sub = left_subs[cur_sub_index]
                            if cur_sub == '*':
                                continue
                            for cur_node in self.lhs_sub_dict[cur_sub]:  # all nodes containing the subscript
                                main_la_type = self.get_sym_type(cur_node.get_main_id())
                                if main_la_type.is_vector():
                                    dim = main_la_type.rows
                                elif main_la_type.is_sequence():
                                    dim = main_la_type.size
                                    if cur_node.same_as_size_sym(cur_sub):
                                        if main_la_type.is_dynamic_dim():
                                            if cur_sub_index == 0:
                                                dynamic = dynamic | DynamicTypeEnum.DYN_ROW
                                            else:
                                                dynamic = dynamic | DynamicTypeEnum.DYN_COL
                                    elif cur_node.same_as_row_sym(cur_sub):
                                        dim = main_la_type.element_type.rows
                                    elif cur_node.same_as_col_sym(cur_sub):
                                        dim = main_la_type.element_type.cols
                                elif main_la_type.is_matrix():
                                    # matrix
                                    dim = main_la_type.rows
                                    if cur_node.same_as_col_sym(cur_sub):
                                        dim = main_la_type.cols
                                elif self.get_sym_type(cur_node.get_main_id()).is_set():
                                    # set 
                                    dim = self.get_sym_type(cur_node.get_main_id()).length
                                    if not self.get_sym_type(cur_node.get_main_id()).length:
                                        if cur_sub_index == 0:
                                            dynamic = dynamic | DynamicTypeEnum.DYN_ROW
                                        else:
                                            dynamic = dynamic | DynamicTypeEnum.DYN_COL
                                break
                            dim_list.append(dim)
                        if '*' in left_subs:
                            # rhs is vector
                            if left_subs[0] == '*':
                                self.get_cur_param_data().symtable[sequence] = MatrixType(rows=right_type.rows, cols=dim_list[0], element_type=right_type, sparse=sparse, diagonal=sparse, index_var=index_var, value_var=value_var, dynamic=dynamic)
                            else:
                                self.get_cur_param_data().symtable[sequence] = MatrixType(rows=dim_list[0], cols=right_type.rows, element_type=right_type, sparse=sparse, diagonal=sparse, index_var=index_var, value_var=value_var, dynamic=dynamic)
                        else:
                            self.get_cur_param_data().symtable[sequence] = MatrixType(rows=dim_list[0], cols=dim_list[1], element_type=right_type, sparse=sparse, diagonal=sparse, index_var=index_var, value_var=value_var, dynamic=dynamic)
                elif len(left_subs) == 1:  # sequence or vector
                    cur_sub = left_subs[0]
                    sequence_type = True   # default type: sequence
                    cur_dyn = DynamicTypeEnum.DYN_INVALID
                    dependence = None
                    for cur_node in self.lhs_sub_dict[cur_sub]:  # all nodes containing the subscript
                        if self.get_sym_type(cur_node.get_main_id()).is_vector():
                            sequence_type = False
                            dim = self.get_sym_type(cur_node.get_main_id()).rows
                            if self.get_sym_type(cur_node.get_main_id()).is_dynamic_row():
                                cur_dyn = DynamicTypeEnum.DYN_ROW
                                dependence = cur_node.get_main_id()
                            break
                        elif self.get_sym_type(cur_node.get_main_id()).is_sequence():
                            dim = self.get_sym_type(cur_node.get_main_id()).size
                            if cur_node.is_node(IRNodeType.SequenceIndex):
                                if cur_node.same_as_row_sym(cur_sub):
                                    dim = self.get_sym_type(cur_node.get_main_id()).rows
                                elif cur_node.same_as_col_sym(cur_sub):
                                    dim = self.get_sym_type(cur_node.get_main_id()).cols
                        elif self.get_sym_type(cur_node.get_main_id()).is_matrix():
                            # matrix
                            dim = self.get_sym_type(cur_node.get_main_id()).rows
                            if cur_node.same_as_col_sym(cur_sub):
                                dim = self.get_sym_type(cur_node.get_main_id()).cols
                        elif self.get_sym_type(cur_node.get_main_id()).is_set():
                            # set 
                            dim = self.get_sym_type(cur_node.get_main_id()).length
                            if not self.get_sym_type(cur_node.get_main_id()).length:
                                cur_dyn = DynamicTypeEnum.DYN_DIM
                    if right_type.is_matrix():
                        sequence_type = True
                    elif right_type.is_scalar():
                        sequence_type = False
                    if sequence_type:
                        self.get_cur_param_data().symtable[sequence] = SequenceType(size=dim, element_type=right_type)
                        seq_index_node = SequenceIndexNode()
                        seq_index_node.main = self.walk(node.left[0].left, **kwargs).ir
                        seq_index_node.main_index = self.walk(node.left[0].right[0], **kwargs).ir
                        seq_index_node.la_type = right_type
                        seq_index_node.set_parent(assign_node)
                        assign_node.left[cur_index] = seq_index_node
                    else:
                        # vector
                        self.get_cur_param_data().symtable[sequence] = VectorType(rows=dim, dynamic=cur_dyn)
                        vector_index_node = VectorIndexNode()
                        vector_index_node.dependence = dependence
                        vector_index_node.main = self.walk(node.left[0].left, **kwargs).ir
                        vector_index_node.row_index = self.walk(node.left[0].right[0], **kwargs).ir
                        vector_index_node.set_parent(assign_node)
                        vector_index_node.la_type = right_type
                        assign_node.left[cur_index] = vector_index_node
                # remove temporary subscripts(from LHS) in symtable
                for sub_sym in left_subs:
                    if self.is_sym_existed(sub_sym):
                        # multiple same sub_sym
                        del self.get_cur_param_data().symtable[sub_sym]
                if len(self.lhs_sub_dict) > 0:
                    assign_node.lhs_sub_dict = self.lhs_sub_dict
                    self.lhs_sub_dict = {}
                else:
                    self.lhs_sub_dict.clear()
            else:
                # without subscripts
                if node.op != '=':
                    self.assert_expr(self.is_sym_existed(id0), get_err_msg_info(id0_info.ir.parse_info, "{} hasn't been defined".format(id0)))
                else:
                    if self.is_sym_existed(id0):
                        err_msg = "{} has been assigned before".format(id0)
                        if id0 in self.parameters:
                            err_msg = "{} is a parameter, can not be assigned".format(id0)
                        self.assert_expr(False, get_err_msg_info(id0_info.ir.parse_info, err_msg))
                    self.get_cur_param_data().symtable[id0] = right_type
            assign_node.symbols = assign_node.symbols.union(right_info.symbols)
            self.expr_dict[id0_info.ir.get_main_id()] = list(right_info.symbols) + [id0_info.ir.get_main_id()]
            if self.visiting_der:
                if id0_info.ir.get_main_id() not in self.lhs_on_der:
                    self.lhs_on_der.append(id0_info.ir.get_main_id())
        self.visiting_solver_eq = False
        self.visiting_der = False
        return NodeInfo(None, ir=assign_node, symbols=assign_node.symbols)

    def walk_GeneralAssignment(self, node, **kwargs):
        if len(node.right) > 1:
            self.assert_expr(len(node.left) == len(node.right), get_err_msg_info(node.parseinfo, "unmatched assignment"))
        else:
            not_all_id = False
            for lhs in node.left:
                if type(lhs).__name__ != 'IdentifierAlone':
                    not_all_id = True
            if not not_all_id:
                # treat as normal assignment
                if len(node.right) < len(node.left):
                    # multiple return value
                    pass
                return self.walk_Assignment(node, **kwargs)
            # rhs_info = self.walk(node.right[0], **kwargs)
            return self.walk_Assignment(node, **kwargs)

    def walk_DeSolver(self, node, **kwargs):
        # print(node)
        pass

    def push_scope(self, scope):
        la_debug("cur list:{}, new scope:{}".format(self.scope_list, scope))
        self.scope_list.append(scope)
        if scope not in self.func_data_dict:
            self.func_data_dict[scope] = LocalFuncData(name=scope)

    def pop_scope(self):
        # be careful on the position
        self.scope_list.pop()
        la_debug("cur scope list:{}".format(self.scope_list))

    def walk_Summation(self, node, **kwargs):
        #
        if node.u:
            ir_node = UnionSequence(parse_info=node.parseinfo, raw_text=node.text)
            new_id = self.generate_var_name("union")
        else:
            ir_node = SummationNode(parse_info=node.parseinfo, raw_text=node.text)
            ir_node.sign = node.sign
            new_id = self.generate_var_name("sum")
        self.push_scope(new_id)
        self.logger.debug("cur sum_subs:{}, sum_conds:{}".format(self.sum_subs, self.sum_conds))
        kwargs[INSIDE_SUMMATION] = True
        subs_list = []
        #
        ir_node.scope_name = new_id
        if node.cond:
            self.sum_sym_list.append({})
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
            self.assert_expr(subs not in self.symtable, get_err_msg_info(sub_parse_info, "Subscript has been defined"))
            self.add_sym_type(subs, ScalarType(index_type=False, is_int=True))
            subs_list.append(subs)
            ir_node.cond = self.walk(node.cond, **kwargs).ir
        else:
            if node.enum and len(node.enum) > 0:
                range_info = self.walk(node.range, **kwargs)
                if range_info.la_type.size == len(node.enum):
                    # (i,j ∈ E)
                    for cur_index in range(len(node.enum)):
                        cur_id_raw = node.enum[cur_index]
                        self.sum_sym_list.append({})
                        enum = self.walk(cur_id_raw)
                        subs_list.append(enum.content)
                        self.check_sym_existence(enum.content, get_err_msg_info(cur_id_raw.parseinfo, "Subscript has been defined"), False)
                        self.add_sym_type(enum.content, range_info.la_type.type_list[cur_index])
                        self.sum_subs.append(enum.content)
                else:
                    # (e ∈ E)
                    self.assert_expr(range_info.la_type.size > 1 and len(node.enum) == 1, get_err_msg_info(node.parseinfo, "Invalid size"))
                    cur_id_raw = node.enum[0]
                    self.sum_sym_list.append({})
                    enum = self.walk(cur_id_raw)
                    subs_list.append(enum.content)
                    self.check_sym_existence(enum.content, get_err_msg_info(cur_id_raw.parseinfo, "Subscript has been defined"), False)
                    self.add_sym_type(enum.content, TupleType(type_list=range_info.la_type.type_list))
                    self.sum_subs.append(enum.content)
                    ir_node.use_tuple = True
                self.sum_conds.append(False)
                ir_node.enum_list = subs_list
                ir_node.range = range_info.ir
            elif node.lower:
                # explicit ranges
                index_type = False
                self.sum_sym_list.append({})
                id_info = self.walk(node.id, **kwargs)
                self.sum_subs.append(id_info.content)
                self.sum_conds.append(False)
                ir_node.id = id_info.ir
                id_info.ir.set_parent(ir_node)
                subs = id_info.content
                # if LHS in kwargs:
                #     lhs = kwargs[LHS]
                #     lhs_ids = self.get_all_ids(lhs)
                    # assert lhs_ids[1][0] == lhs_ids[1][1], "multiple subscripts for sum"
                sub_parse_info = node.id.parseinfo
                ir_node.lower = self.walk(node.lower, **kwargs).ir
                ir_node.upper = self.walk(node.upper, **kwargs).ir
                if ir_node.lower.la_type.index_type and ir_node.upper.la_type.index_type:
                    index_type = True
                self.assert_expr(subs not in self.symtable,
                                 get_err_msg_info(sub_parse_info, "Subscript has been defined"))
                self.add_sym_type(subs, ScalarType(index_type=index_type, is_int=True))
                subs_list.append(subs)
            else:
                self.sum_sym_list.append({})
                sub_info = self.walk(node.sub)
                self.sum_subs.append(sub_info.content)
                self.sum_conds.append(False)
                ir_node.sub = sub_info.ir
                ir_node.id = sub_info.ir
                sub_info.ir.set_parent(ir_node)
                subs = sub_info.content
                sub_parse_info = node.sub.parseinfo
                self.assert_expr(subs not in self.symtable, get_err_msg_info(sub_parse_info, "Subscript has been defined"))
                self.add_sym_type(subs, ScalarType(index_type=False, is_int=True))
                subs_list.append(subs)
        self.logger.debug("new sum_subs:{}, sum_conds:{}".format(self.sum_subs, self.sum_conds))
        # extra exprs
        if node.extra and len(node.extra) > 0:
            ir_node.extra_list, ir_node.tex_list = self.get_ordered_stat(node.extra)
        ret_info = self.walk(node.exp, **kwargs)
        if node.u:
            self.assert_expr(ret_info.la_type.is_set(), get_err_msg_info(node.exp.parseinfo, "Expression must be set type"))
        ir_node.exp = ret_info.ir
        ret_info.ir.set_parent(ir_node)
        ret_type = ret_info.la_type
        self.add_sym_type(new_id, ret_type, to_upper=True)     # add the symbol to upper scope layer, pop in the end
        ret_info.symbol = new_id
        # ret_info.content = subs
        ir_node.la_type = ret_info.la_type
        ir_node.symbols = ret_info.symbols
        ir_node.symbol = ret_info.symbol
        ir_node.content = ret_info.content
        if node.enum is None or len(node.enum) == 0:
            for i in range(len(subs_list)):
                self.sum_subs.pop()
                cur_sym_dict = self.sum_sym_list.pop()
                self.assert_expr(len(cur_sym_dict) > 0, get_err_msg_info(sub_parse_info, "Subscript hasn't been used in summation"))
                # self.check_sum_subs(subs, cur_sym_dict)
                ir_node.sym_dict = cur_sym_dict
        self.sum_conds.pop()
        ret_info.ir = ir_node
        if node.enum is None or len(node.enum) == 0:
            for subs in subs_list:
                self.assert_expr(self.check_sum_subs(subs, cur_sym_dict), get_err_msg_info(sub_parse_info, "Subscript has inconsistent dimensions"))
            self.logger.debug("cur_sym_dict: {}".format(cur_sym_dict))
        self.logger.debug("summation, symbols: {}".format(ir_node.symbols))
        self.pop_scope()
        return ret_info

    def check_sum_subs(self, subs, sym_dict):
        self.logger.debug("subs:{}, sym_dict:{}".format(subs, sym_dict))
        dim_set = set()
        seq_cnt = 0  #
        valid = True
        for k, v in sym_dict.items():
            cur_type = self.get_sym_type(k)
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
        self.push_scope(self.opt_key)
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
                    if par_type.id[cur_index].get_main_id() not in self.opt_syms:
                        self.opt_syms.append(par_type.id[cur_index].get_main_id())
            self.is_param_block = False
            # self.symtable.update(self.get_cur_param_data().symtable)
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
        self.assert_expr(exp_node.la_type.is_scalar(), get_err_msg_info(exp_node.parse_info, "Objective function must return a scalar"))
        opt_node = OptimizeNode(opt_type, cond_list, exp_node, base_node_list, base_type_list, parse_info=node.parseinfo, key=self.opt_key, init_list=init_list, init_syms=init_syms, def_list=par_defs, raw_text=node.text)
        opt_node.la_type = ret_type
        opt_node.scope_name = self.opt_key
        opt_node.symbols = exp_info.symbols
        node_info = NodeInfo(opt_node.la_type, ir=opt_node, symbols=exp_info.symbols)
        self.visiting_opt = False
        for var_node in base_node_list:
            self.expr_dict[var_node.get_main_id()] = list(opt_node.symbols)
        self.pop_scope()
        return node_info

    def walk_MultiCond(self, node, **kwargs):
        conds_list = []
        if node.m_cond:
            conds_list = self.walk(node.m_cond, **kwargs)
        conds_list.append(self.walk(node.cond, **kwargs).ir)
        return conds_list

    def walk_Domain(self, node, **kwargs):
        domain_node = DomainNode(self.walk(node.lower, **kwargs).ir, self.walk(node.upper, **kwargs).ir, parse_info=node.parseinfo, raw_text=node.text)
        return domain_node

    def walk_Integral(self, node, **kwargs):
        base_node = self.walk(node.id, **kwargs).ir
        name = self.generate_var_name('integral')
        self.push_scope(name)
        # temporary add to symbol table : opt scope
        base_id = base_node.get_main_id()
        self.add_sym_type(base_id, ScalarType())
        if node.d:
            domain_node = self.walk(node.d, **kwargs)
        else:
            domain_node = DomainNode(self.walk(node.lower, **kwargs).ir, self.walk(node.upper, **kwargs).ir, raw_text=node.text)
        int_node = IntegralNode(domain=domain_node, exp=self.walk(node.exp, **kwargs).ir, base=base_node, parse_info=node.parseinfo, raw_text=node.text)
        int_node.scope_name = name
        node_info = NodeInfo(ScalarType())
        node_info.ir = int_node
        int_node.la_type = node_info.la_type
        #
        self.pop_scope()
        return node_info

    def walk_Norm(self, node, **kwargs):
        ir_node = NormNode(parse_info=node.parseinfo, raw_text=node.text)
        value_info = self.walk(node.value, **kwargs)
        ir_node.value = value_info.ir
        # ret type
        ret_type = ScalarType()
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
            self.assert_expr(node.single is not None, get_err_msg_info(node.parseinfo, "Norm error. Scalar type has to use | rather than ||"))
        elif ir_node.value.la_type.is_vector():
            self.assert_expr(node.single is None, get_err_msg_info(node.parseinfo, "Norm error. Vector type has to use || rather than |"))
            self.assert_expr(ir_node.norm_type != NormType.NormFrobenius and ir_node.norm_type != NormType.NormNuclear, get_err_msg(get_line_info(node.parseinfo),
                                 get_line_info(node.parseinfo).text.find('_')+1, "Norm error. Invalid norm for Vector"))
            if ir_node.norm_type == NormType.NormIdentifier:
                self.assert_expr(ir_node.sub.la_type.is_matrix() or ir_node.sub.la_type.is_scalar(), get_err_msg(get_line_info(node.parseinfo),
                                 get_line_info(node.parseinfo).text.find('_')+1, "Norm error. Subscript has to be matrix or scalar for vector type"))
                if ir_node.sub.la_type.is_matrix():
                    self.assert_expr(is_same_expr(ir_node.sub.la_type.rows, ir_node.sub.la_type.cols) and is_same_expr(ir_node.sub.la_type.rows, ir_node.value.la_type.rows), get_err_msg(get_line_info(node.parseinfo),
                                 get_line_info(node.parseinfo).text.find('_')+1, "Norm error. Dimension error"))
        elif ir_node.value.la_type.is_matrix():
            if node.single:
                ir_node.norm_type = NormType.NormDet
            else:
                self.assert_expr(node.single is None, get_err_msg_info(node.parseinfo, "Norm error. MATRIX type has to use || rather than |"))
                self.assert_expr(ir_node.norm_type == NormType.NormFrobenius or ir_node.norm_type == NormType.NormNuclear, get_err_msg(get_line_info(node.parseinfo),
                                 get_line_info(node.parseinfo).text.find('_')+1, "Norm error. Invalid norm for Matrix"))
                if ir_node.norm_type == NormType.NormNuclear:
                    self.assert_expr(not ir_node.value.la_type.sparse, get_err_msg(get_line_info(node.parseinfo),
                                                                          get_line_info(node.parseinfo).text.find('*'),
                                                                          "Norm error. Nuclear norm is invalid for sparse matrix"))
        elif ir_node.value.la_type.is_set():
            self.assert_expr(node.single is not None, get_err_msg_info(node.parseinfo, "Set type has to use | rather than ||"))
            ir_node.norm_type = NormType.NormSize
            ret_type = ScalarType(is_int=True)
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
        self.assert_expr(left_info.ir.la_type.is_vector(), get_err_msg_info(left_info.ir.parse_info, "Inner product error. Parameter {} must be vector".format(node.left.text)))
        self.assert_expr(right_info.ir.la_type.is_vector(), get_err_msg_info(right_info.ir.parse_info, "Inner product error. Parameter {} must be vector".format(node.right.text)))
        self.assert_expr(is_same_expr(left_info.ir.la_type.rows, right_info.ir.la_type.rows), get_err_msg_info(node.parseinfo,
                                                                                        "Inner product error. Parameters {} and {} must have the same dimension".format(node.left.text, node.right.text)))
        sub_node = None
        if node.sub:
            sub_node = self.walk(node.sub, **kwargs).ir
            self.assert_expr(sub_node.la_type.is_matrix() and sub_node.la_type.rows==sub_node.la_type.cols==left_info.ir.la_type.rows, \
                get_err_msg_info(sub_node.parse_info, "Inner product error. The dimension of subscript {} must correspond to the vector dimension".format(node.sub.text)))
        ir_node = InnerProductNode(left_info.ir, right_info.ir, sub_node, parse_info=node.parseinfo, raw_text=node.text)
        ret_type = ScalarType()
        ir_node.la_type = ret_type
        node_info = NodeInfo(ret_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))
        return node_info

    def walk_FroProduct(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        self.assert_expr(left_info.la_type.is_vector() or left_info.la_type.is_matrix(), get_err_msg_info(left_info.ir.parse_info, "Frobenius product error. Parameter {} must be vector or matrix".format(node.left.text)))
        self.assert_expr(right_info.la_type.is_vector() or right_info.la_type.is_matrix(), get_err_msg_info(right_info.ir.parse_info, "Frobenius product error. Parameter {} must be vector or matrix".format(node.right.text)))
        ir_node = FroProductNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, raw_text=node.text)
        ir_node.la_type = ScalarType()
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))

    def walk_HadamardProduct(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ir_node = HadamardProductNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, raw_text=node.text)
        self.assert_expr(left_info.la_type.is_vector() or left_info.la_type.is_matrix(), get_err_msg_info(left_info.ir.parse_info, "Hadamard product error. Parameter {} must be vector or matrix".format(node.left.text)))
        self.assert_expr(right_info.la_type.is_vector() or right_info.la_type.is_matrix(), get_err_msg_info(right_info.ir.parse_info, "Hadamard product error. Parameter {} must be vector or matrix".format(node.right.text)))
        self.assert_expr(is_same_expr(left_info.la_type.rows, right_info.la_type.rows), get_err_msg_info(node.parseinfo,
                                                                                        "Hadamard product error. Parameters {} and {} must have the same dimension".format(node.left.text, node.right.text)))
        if left_info.la_type.is_matrix():
            self.assert_expr(is_same_expr(left_info.la_type.cols, right_info.la_type.cols), get_err_msg_info(node.parseinfo,
                                                                                        "Hadamard product error. Parameters {} and {} must have the same dimension".format(node.left.text, node.right.text)))
            ir_node.la_type = MatrixType(rows=left_info.la_type.rows, cols=left_info.la_type.cols)
        else:
            ir_node.la_type = VectorType(rows=left_info.la_type.rows)
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))

    def walk_CrossProduct(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        self.assert_expr(left_info.la_type.is_vector(), get_err_msg_info(left_info.ir.parse_info, "Cross product error. Parameter {} must be vector".format(node.left.text)))
        self.assert_expr(right_info.la_type.is_vector(), get_err_msg_info(right_info.ir.parse_info, "Cross product error. Parameter {} must be vector".format(node.right.text)))
        self.assert_expr(left_info.la_type.rows == 3, get_err_msg_info(left_info.ir.parse_info, "Cross product error. The dimension of parameter {} must be 3".format(node.left.text)))
        self.assert_expr(right_info.la_type.rows == 3, get_err_msg_info(right_info.ir.parse_info, "Cross product error. The dimension of parameter {} must be 3".format(node.right.text)))
        ir_node = CrossProductNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, raw_text=node.text)
        ir_node.la_type = VectorType(rows=left_info.la_type.rows)
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))

    def walk_KroneckerProduct(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ir_node = KroneckerProductNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, raw_text=node.text)
        self.assert_expr(left_info.la_type.is_vector() or left_info.la_type.is_matrix(), get_err_msg_info(left_info.ir.parse_info, "Kronecker product error. Parameter {} must be vector or matrix".format(node.left.text)))
        self.assert_expr(right_info.la_type.is_vector() or right_info.la_type.is_matrix(), get_err_msg_info(right_info.ir.parse_info, "Kronecker product error. Parameter {} must be vector or matrix".format(node.right.text)))
        ir_node.la_type = MatrixType(rows=mul_dims(left_info.la_type.rows, right_info.la_type.rows), cols=mul_dims(left_info.la_type.cols, right_info.la_type.cols))
        if left_info.la_type.is_sparse_matrix() or right_info.la_type.is_sparse_matrix():
            ir_node.la_type.sparse = True
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))

    def walk_DotProduct(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        ir_node = DotProductNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, raw_text=node.text)
        self.assert_expr(left_info.la_type.is_vector(), get_err_msg_info(left_info.ir.parse_info, "Dot product error. Parameter {} must be vector".format(node.left.text)))
        self.assert_expr(right_info.la_type.is_vector(), get_err_msg_info(right_info.ir.parse_info, "Dot product error. Parameter {} must be vector".format(node.right.text)))
        self.assert_expr(is_same_expr(left_info.la_type.rows, right_info.la_type.rows), get_err_msg_info(node.parseinfo,
                                                                                        "Dot product error. Parameters {} and {} must have the same dimension".format(node.left.text, node.right.text)))
        ir_node.la_type = ScalarType()
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=left_info.symbols.union(right_info.symbols))

    def create_power_node(self, base, power):
        power_node = PowerNode()
        power_node.base = base
        power_node.power = power
        self.assert_expr(power.la_type.is_scalar(), get_err_msg_info(power.parse_info, "Power must be scalar"))
        power_node.la_type = ScalarType()
        self.assert_expr(base.la_type.is_scalar() or base.la_type.is_matrix(), get_err_msg_info(base.parse_info, "Base of power must be scalar or matrix"))
        if base.la_type.is_matrix():
            self.assert_expr(is_same_expr(base.la_type.rows, base.la_type.cols), get_err_msg_info(base.parse_info, "Power error. Rows must be the same as columns"))
            self.unofficial_method = True
            power_node.la_type = base.la_type
        return power_node
    
    def walk_SizeOp(self, node, **kwargs):
        i_info = self.walk(node.i, **kwargs)
        self.assert_expr(not i_info.la_type.is_scalar(), get_err_msg_info(node.i.parseinfo, "Invalid type"))
        if i_info.la_type.is_vector() or i_info.la_type.is_set():
            ret_type = ScalarType(is_int=True)
        elif i_info.la_type.is_matrix():
            ret_type = TupleType(type_list=[ScalarType(is_int=True), ScalarType(is_int=True)])
        elif i_info.la_type.is_sequence():
            if i_info.la_type.element_type.is_scalar():
                ret_type = ScalarType(is_int=True)
            elif i_info.la_type.element_type.is_vector():
                ret_type = TupleType(type_list=[ScalarType(is_int=True), ScalarType(is_int=True)])
            elif i_info.la_type.element_type.is_matrix():
                ret_type = TupleType(type_list=[ScalarType(is_int=True), ScalarType(is_int=True), ScalarType(is_int=True)])
        ir_node = SizeNode(param=i_info.ir)
        ir_node.la_type = ret_type
        return NodeInfo(ir_node.la_type, ir=ir_node)
    
    def walk_Derivative(self, node, **kwargs):
        self.visiting_der = True
        self.cur_eq_type |= EqTypeEnum.ODE
        upper_info = self.walk(node.upper, **kwargs)
        lower_info = self.walk(node.lower, **kwargs)
        ir_node = DerivativeNode(parse_info=node.parseinfo, raw_text=node.text, upper=upper_info.ir, lower=lower_info.ir)
        if node.f:
            ir_node.d_type = DerivativeType.DerivativeFraction
        else:
            ir_node.d_type = DerivativeType.DerivativeSFraction
        if node.lorder:
            lorder_info = self.walk(node.lorder, **kwargs)
            uorder_info = self.walk(node.uorder, **kwargs)
            ir_node.order = lorder_info.ir
        ir_node.la_type = upper_info.la_type
        return NodeInfo(ir_node.la_type, ir=ir_node)

    def walk_Partial(self, node, **kwargs):
        self.visiting_der = True
        self.has_derivative = True
        self.cur_eq_type &= EqTypeEnum.PDE
        upper_info = self.walk(node.upper, **kwargs)
        # self.assert_expr(upper_info.la_type.is_function(), get_err_msg_info(upper_info.ir.parse_info,"Symbol {} isn't a function".format(node.upper.text)))
        self.assert_expr(upper_info.la_type.is_scalar() or upper_info.la_type.is_vector(), get_err_msg_info(upper_info.ir.parse_info,"Only support scalar or vector types"))
        lower_list = []
        lower_name_list = []
        lower_type_list = []
        lorder_list = []
        lorder_value_list = [] 
        for l in node.l:
            lower_info = self.walk(l[1], **kwargs)
            lower_list.append(lower_info.ir)
            lower_name_list.append(l[1].text)
            # self.assert_expr(l[1].text in func_param_dict, get_err_msg_info(lower_info.ir.parse_info,"Symbol {} isn't a param of function {}".format(l[1].text, node.upper.text)))
            self.assert_expr(self.is_sym_parameter(l[1].text), get_err_msg_info(lower_info.ir.parse_info,"Symbol {} isn't a param".format(l[1].text)))
            if l[1].text not in self.used_params:
                self.used_params.append(l[1].text)
            if l[1].text not in self.der_vars:
                self.der_vars.append(l[1].text)
            lower_type_list.append(lower_info.la_type)
            if len(l) > 2:
                lorder_info = self.walk(l[-1], **kwargs)
                lorder_list.append(lorder_info.ir)
                lorder_value_list.append(str(get_unicode_number(lorder_info.content)))
            else:
                int_node = IntegerNode(value=1)
                int_node.la_type = ScalarType(is_int=True)
                lorder_list.append(int_node)
                lorder_value_list.append(str(1))
        ir_node = PartialNode(parse_info=node.parseinfo, raw_text=node.text, upper=upper_info.ir, lower_list=lower_list, lorder_list=lorder_list)
        if node.uorder:
            ir_node.order = self.walk(node.uorder, **kwargs).ir
            uorder_value = get_unicode_number(node.uorder.text)
        else:
            uorder_value = str(1)
        ret_type = ScalarType()
        if is_same_expr(uorder_value, '1'):
            # first order
            ret_type = get_derivative_type(upper_info.la_type, lower_type_list[0])
            ir_node.order_type = PartialOrderType.PartialNormal
        elif is_same_expr(uorder_value, '2'):
            # second order
            if len(lorder_list) == 1:
                # hessian
                ret_type = get_hessian_type(upper_info.la_type, lower_type_list[0])
                ir_node.order_type = PartialOrderType.PartialHessian
                self.hessian_list.append(HessianInfo(node.upper.text, lower_name_list[0], ir_node))
            pass
        self.assert_expr(is_same_expr("+".join(lorder_value_list), uorder_value), get_err_msg_info(node.parseinfo,"Order doesn't match"))
        if node.f:
            ir_node.d_type = DerivativeType.DerivativeFraction
        else:
            ir_node.d_type = DerivativeType.DerivativeSFraction
        ir_node.la_type = ret_type
        return NodeInfo(ir_node.la_type, ir=ir_node)

    def walk_Divergence(self, node, **kwargs):
        value_info = self.walk(node.value, **kwargs)
        ir_node = DivergenceNode(parse_info=node.parseinfo, value=value_info.ir, raw_text=node.text)
        ir_node.la_type = ScalarType()
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=value_info.symbols)

    def walk_Gradient(self, node, **kwargs):
        self.visiting_der = True
        value_info = self.walk(node.value, **kwargs)
        # self.assert_expr(value_info.la_type.is_function(), get_err_msg_info(value_info.ir.parse_info,"Symbol {} isn't a function".format(node.value.text)))
        self.assert_expr(value_info.la_type.is_scalar() or value_info.la_type.is_vector(), get_err_msg_info(value_info.ir.parse_info,"Only support scalar or vector types"))
        sub = None
        # func_param_dict = self.local_func_dict[node.value.text]
        if node.sub:
            sub_info = self.walk(node.sub, **kwargs)
            sub_text = get_unicode_subscript(node.sub.text)
            # self.assert_expr(sub_text in func_param_dict, get_err_msg_info(sub_info.ir.parse_info,"Symbol {} isn't a param of function {}".format(sub_text, node.value.text)))
            self.assert_expr(self.is_sym_parameter(sub_text), get_err_msg_info(sub_info.ir.parse_info,"Symbol {} isn't a param".format(sub_text)))
            if sub_text not in self.used_params:
                self.used_params.append(sub_text)
            if sub_text not in self.der_vars:
                self.der_vars.append(sub_text)
            sub = sub_info.ir
            sub_la_type = sub_info.la_type
        # else:
        #     # check func only has one param
        #     self.assert_expr(value_info.la_type.is_function(), get_err_msg_info(value_info.ir.parse_info,"Symbol {} isn't a function".format(node.value.text)))
        #     sub_la_type = value_info.la_type.params[0]
        ir_node = GradientNode(parse_info=node.parseinfo, sub=sub, value=value_info.ir, raw_text=node.text)
        ir_node.la_type = get_derivative_type(value_info.la_type, sub_la_type)
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=value_info.symbols)

    def walk_Laplace(self, node, **kwargs):
        value_info = self.walk(node.value, **kwargs)
        ir_node = LaplaceNode(parse_info=node.parseinfo, value=value_info.ir, raw_text=node.text)
        ir_node.la_type = ScalarType()
        return NodeInfo(ir_node.la_type, ir=ir_node, symbols=value_info.symbols)

    def walk_Power(self, node, **kwargs):
        ir_node = PowerNode(parse_info=node.parseinfo, raw_text=node.text)
        base_info = self.walk(node.base, **kwargs)
        ir_node.base = base_info.ir
        symbols = base_info.symbols
        if node.t or (node.power and node.power.text == 'ᵀ'):
            if 'T' in self.symtable:
                # normal pow
                power_ir = IdNode('T', parse_info=node.parseinfo, raw_text=node.text)
                power_ir.la_type = self.symtable['T']
                symbols = symbols.union('T')
                ir_node = self.create_power_node(base_info.ir, power_ir)
            else:
                # transpose
                ir_node.t = node.t
                if node.power and node.power.text == 'ᵀ':
                    ir_node.t = 'ᵀ'
                self.assert_expr(base_info.la_type.is_matrix() or base_info.la_type.is_vector(), get_err_msg_info(base_info.ir.parse_info,"Transpose error. The base must be a matrix or vecotr"))
                sparse = False
                if base_info.la_type.is_matrix():
                    sparse = base_info.la_type.sparse
                ir_node.la_type = MatrixType(rows=base_info.la_type.cols, cols=base_info.la_type.rows, sparse=sparse, element_type=copy.deepcopy(base_info.la_type.element_type), owner=base_info.la_type.owner)
        elif node.r:
            ir_node.r = node.r
            if base_info.la_type.is_matrix():
                self.assert_expr(base_info.la_type.is_matrix(), get_err_msg_info(base_info.ir.parse_info,"Inverse matrix error. The base must be a matrix"))
                self.assert_expr(is_same_expr(base_info.la_type.rows, base_info.la_type.cols), get_err_msg_info(base_info.ir.parse_info,"Inverse matrix error. The rows should be the same as the columns"))
                ir_node.la_type = MatrixType(rows=base_info.la_type.rows, cols=base_info.la_type.rows, sparse=base_info.la_type.sparse)
            else:
                self.assert_expr(base_info.la_type.is_scalar(), get_err_msg_info(base_info.ir.parse_info,
                                                                            "Inverse error. The base must be a matrix or scalar"))
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
        if left_info.la_type.is_scalar():
            ir_node = PowerNode(parse_info=node.parseinfo, raw_text=node.text)
            ir_node.base = left_info.ir
            symbols = left_info.symbols
            ir_node.r = node.p
            ir_node.la_type = ScalarType()
            node_info = NodeInfo(ir_node.la_type, symbols=symbols)
            node_info.ir = ir_node
            op_type = MulOpType.MulOpInvalid
            return self.make_mul_info(node_info, right_info, op_type, parse_info=node.parseinfo, raw_text=node.text)
        elif left_info.la_type.is_set():
            self.assert_expr(right_info.la_type.is_set(), get_err_msg_info(right_info.ir.parse_info,
                                                                             "Parameter {} must be a set".format(
                                                                                 node.right.text)))
            ret_type, need_cast = self.type_inference(TypeInferenceEnum.INF_SUB, left_info, right_info)
            ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
            ir_node = DifferenceNode(left_info.ir, right_info.ir, diff_format=DiffFormat.DiffSplit, parse_info=node.parseinfo, raw_text=node.text)
            ir_node.la_type = ret_type
            left_info.ir.set_parent(ir_node)
            right_info.ir.set_parent(ir_node)
            ret_info.ir = ir_node
            return ret_info
        ir_node = SolverNode(parse_info=node.parseinfo, raw_text=node.text)
        ir_node.pow = node.p
        ir_node.left = left_info.ir
        ir_node.right = right_info.ir
        self.assert_expr(left_info.la_type.is_matrix(), get_err_msg_info(left_info.ir.parse_info, "Parameter {} must be a matrix".format(node.left.text)))
        self.assert_expr(right_info.la_type.is_matrix() or right_info.la_type.is_vector(), get_err_msg_info(left_info.ir.parse_info, "Parameter {} must be a matrix or vector".format(node.right.text)))
        node_type = None
        if left_info.la_type.is_matrix():
            self.assert_expr(is_same_expr(left_info.la_type.rows, left_info.la_type.cols), get_err_msg_info(left_info.ir.parse_info, "Inverse matrix error. The rows should be the same as the columns"))
            self.assert_expr(is_same_expr(left_info.la_type.rows, right_info.la_type.rows), get_err_msg_info(left_info.ir.parse_info, "Parameters {} and {} should have the same rows".format(node.left.text, node.right.text)))
            if right_info.la_type.is_matrix():
                node_type = MatrixType(rows=left_info.la_type.cols, cols=right_info.la_type.cols, sparse=left_info.la_type.sparse and right_info.la_type.sparse)
            elif right_info.la_type.is_vector():
                node_type = VectorType(rows=left_info.la_type.cols)
        ir_node.la_type = node_type
        node_info = NodeInfo(node_type, symbols=left_info.symbols.union(right_info.symbols))
        node_info.ir = ir_node
        return node_info

    def walk_Transpose(self, node, **kwargs):
        ir_node = TransposeNode(parse_info=node.parseinfo, raw_text=node.text)
        f_info = self.walk(node.f, **kwargs)
        ir_node.f = f_info.ir
        self.assert_expr(f_info.la_type.is_matrix() or f_info.la_type.is_vector(), get_err_msg_info(f_info.ir.parse_info,"Transpose error. The base must be a matrix or vector"))
        if f_info.la_type.is_matrix():
            node_type = MatrixType(rows=f_info.la_type.cols, cols=f_info.la_type.rows, sparse=f_info.la_type.sparse, owner=f_info.la_type.owner)
            if f_info.la_type.is_dynamic_row():
                node_type.set_dynamic_type(DynamicTypeEnum.DYN_COL)
            if f_info.la_type.is_dynamic_col():
                node_type.set_dynamic_type(DynamicTypeEnum.DYN_ROW)
        elif f_info.la_type.is_vector():
            node_type = MatrixType(rows=1, cols=f_info.la_type.rows, owner=f_info.la_type.owner)
        node_info = NodeInfo(node_type, symbols=f_info.symbols)
        node_info.ir = ir_node
        node_info.la_type = node_type
        return node_info

    def walk_PseudoInverse(self, node, **kwargs):
        ir_node = PseudoInverseNode(parse_info=node.parseinfo)
        f_info = self.walk(node.f, **kwargs)
        ir_node.f = f_info.ir
        assert f_info.la_type.is_matrix() or f_info.la_type.is_vector(), get_err_msg_info(f_info.ir.parse_info,"Pseudoinverse error. The base must be a matrix or vector")
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
        ir_node = SquarerootNode(parse_info=node.parseinfo, raw_text=node.text)
        f_info = self.walk(node.f, **kwargs)
        self.assert_expr(f_info.la_type.is_scalar(), get_err_msg_info(f_info.ir.parse_info, "Squareroot error. The base must be a scalar"))
        node_type = ScalarType()
        ir_node.value = f_info.ir
        node_info = NodeInfo(node_type, symbols=f_info.symbols)
        node_info.ir = ir_node
        node_info.la_type = node_type
        return node_info

    def walk_Function(self, node, **kwargs):
        if isinstance(node.name, str):
            func_name = node.name
            if self.local_func_parsing and node.name in self.parameters and node.name not in self.used_params:
                self.used_params.append(node.name)
            if self.visiting_opt and node.name in self.parameters and node.name not in self.used_params:
                self.used_params.append(node.name)
            # if contains_sub_symbol(node.name):
            #     split_res = split_sub_string(node.name)
            #     name = self.filter_symbol(split_res[0])
            #     ir_node = SequenceIndexNode(raw_text=node.name)
            #     ir_node.main = IdNode(name, parse_info=node.parseinfo)
            #     ir_node.main.la_type = self.symtable[name]
            #     ir_node.main_index = IdNode(split_res[-1], parse_info=node.parseinfo)
            #     if split_res[-1].isnumeric():
            #         ir_node.main_index.la_type = ScalarType(is_int=True)
            #     else:
            #         self.assert_expr(split_res[-1] in self.symtable, get_err_msg_info(node.parseinfo, "Subscript not defined"))
            #         self.assert_expr(self.symtable[split_res[-1]].is_int_scalar(), get_err_msg_info(node.parseinfo, "Subscript has to be integer"))
            #         ir_node.main_index.la_type = self.symtable[split_res[-1]]
            #         self.update_sub_sym_lists(name, split_res[-1])
            #     ir_node.la_type = self.symtable[name].element_type
            #     ir_node.process_subs_dict(self.lhs_sub_dict)
            # else:
            ir_node = IdNode(node.name, parse_info=node.parseinfo)
            node.name = self.filter_symbol(node.name)
            ir_node.la_type = self.get_sym_type(node.name)
            name_info = NodeInfo(ir_node.la_type, ir=ir_node)
        else:
            name_info = self.walk(node.name, **kwargs)
            func_name = name_info.ir.get_main_id()
        name_type = name_info.ir.la_type
        ir_node = FunctionNode(parse_info=node.parseinfo, mode=FuncFormat.FuncNormal if node.p else FuncFormat.FuncShort, raw_text=node.text)
        ir_node.name = name_info.ir
        if node.p:
            ir_node.def_type =LocalFuncDefType.LocalFuncDefParenthesis
        # if node.order:
        #     ir_node.order = len(node.order)
        #     self.cur_eq_type |= EqTypeEnum.ODE
        # elif node.d:
        #     ir_node.order = 2
        #     ir_node.order_mode = OrderFormat.OrderDot
        #     self.cur_eq_type |= EqTypeEnum.ODE
        # elif node.s:
        #     ir_node.order = 1
        #     ir_node.order_mode = OrderFormat.OrderDot
        #     self.cur_eq_type |= EqTypeEnum.ODE
        if name_type.is_function():
            omitted = False # whether size is omitted when checking func types
            # function type is already specified in where block
            convertion_dict = {}   # template -> instance
            param_list = []
            symbols = set()
            param_node_list = []
            param_type_list = []
            # params from subscripts
            if node.subs:
                for index in range(len(node.subs)):
                    c_node = self.walk(node.subs[index], **kwargs)
                    param_node_list.append(c_node)
                    param_type_list.append(c_node.la_type)
                ir_node.n_subs = len(node.subs)
            # params inside parentheses
            for index in range(len(node.params)):
                c_node = self.walk(node.params[index], **kwargs)
                param_node_list.append(c_node)
                param_type_list.append(c_node.la_type)
            # Builtin function call
            builtin_name = func_name
            if func_name in self.func_imported_renaming:
                builtin_name = self.func_imported_renaming[func_name]
            # get dynamic func type based on parameters
            if builtin_name in MESH_HELPER_FUNC_MAPPING:
                if builtin_name in MESH_HELPER_DYNAMIC_TYPE_LIST:
                    if builtin_name == IndicatorVector:
                        # IndicatorVector can get mesh element from type owner
                        err_msg = get_err_msg_info(node.parseinfo, "Function IndicatorVector error. Can not get mesh info from the parameter")
                        self.assert_expr(param_type_list[0].owner, err_msg)
                        self.check_sym_existence(param_type_list[0].owner, err_msg)
                        mesh_t = self.get_sym_type(param_type_list[0].owner)
                    else:
                        # dynamic func type, the first parameter must be mesh type,
                        self.assert_expr(param_type_list[0].is_mesh(), get_err_msg_info(node.parseinfo,
                                                                                        "Function error. The first parameter must be mesh type"))
                        mesh_t = param_type_list[0]
                    name_type = get_sym_type_from_pkg(builtin_name, MESH_HELPER, mesh_t)
                else:
                    # Not dynamic list
                    if builtin_name == NonZeros:
                        # NonZeros requires mesh element
                        err_msg = get_err_msg_info(node.parseinfo,
                                                   "Function NonZeros error. Can not get mesh info from the parameter")
                        self.assert_expr(param_type_list[0].owner, err_msg)
                        self.check_sym_existence(param_type_list[0].owner, err_msg)
            # check overloading
            if name_type.is_overloaded():
                # get correct type for current parameters
                correct_type, omitted = name_type.get_correct_ftype(param_type_list)
                if correct_type is None:
                    la_debug("name_type:{}".format(name_type.get_signature()))
                    # try to relax conditions
                name_type = correct_type
                self.assert_expr(name_type is not None, get_err_msg_info(node.parseinfo, "Function error. Can't find function with current parameter types."))
                ir_node.identity_name = self.func_sig_dict[get_func_signature(func_name, name_type)]
            else:
                ir_node.identity_name = func_name
            self.assert_expr(len(param_node_list) == len(name_type.params) or len(node.params) == 0,
                             get_err_msg_info(node.parseinfo, "Function error. Parameters count mismatch"))
            for index in range(len(param_node_list)):
                param_info = param_node_list[index]
                symbols = symbols.union(param_info.symbols)
                param_list.append(param_info.ir)
                # owner checking
                if name_type.params[index].owner:
                    self.assert_expr(name_type.params[index].owner == param_info.ir.la_type.owner,
                                     get_err_msg_info(param_info.ir.parse_info,
                                                      "Function error. Parameter comes from different mesh: function requires {} while param {} has {}".format(name_type.params[index].owner, param_info.ir.raw_text, param_info.ir.la_type.owner)))
                if len(name_type.template_symbols) == 0:
                    self.assert_expr(name_type.params[index].is_same_type(param_info.ir.la_type, True), get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch: {} vs {}".format(name_type.params[index].get_signature(), param_info.ir.la_type.get_signature())))
                    continue
                if name_type.params[index].is_scalar():
                    self.assert_expr(name_type.params[index].is_same_type(param_info.ir.la_type), get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch"))
                elif name_type.params[index].is_vector():
                    self.assert_expr(param_info.ir.la_type.is_vector(), get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch"))
                    if name_type.params[index].rows in name_type.template_symbols:
                        convertion_dict[name_type.params[index].rows] = param_info.ir.la_type.rows
                    else:
                        self.assert_expr(is_same_expr(name_type.params[index].rows, param_info.ir.la_type.rows), get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch"))
                elif name_type.params[index].is_matrix():
                    self.assert_expr(param_info.ir.la_type.is_matrix(), get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch"))
                    if name_type.params[index].rows in name_type.template_symbols:
                        convertion_dict[name_type.params[index].rows] = param_info.ir.la_type.rows
                    else:
                        self.assert_expr(is_same_expr(name_type.params[index].rows, param_info.ir.la_type.rows), get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch"))
                    #
                    if name_type.params[index].cols in name_type.template_symbols:
                        convertion_dict[name_type.params[index].cols] = param_info.ir.la_type.cols
                    else:
                        self.assert_expr(is_same_expr(name_type.params[index].cols, param_info.ir.la_type.cols), get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch"))
                elif name_type.params[index].is_set():
                    self.assert_expr(param_info.ir.la_type.is_set(), get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch"))
                    self.assert_expr(name_type.params[index].size == param_info.ir.la_type.size, get_err_msg_info(param_info.ir.parse_info, "Function error. Parameter type mismatch"))
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
                        ret_type = copy.deepcopy(name_type.ret[cur_index])
                        ret_type.rows = convertion_dict[cur_type.rows]
                elif cur_type.is_matrix():
                    ret_type = copy.deepcopy(name_type.ret[cur_index])
                    if cur_type.rows in name_type.template_symbols:
                        ret_type.rows = convertion_dict[cur_type.rows]
                    else:
                        ret_type.rows = cur_type.rows
                    if cur_type.cols in name_type.template_symbols:
                        ret_type.cols = convertion_dict[cur_type.cols]
                    else:
                        ret_type.cols = cur_type.cols
                elif cur_type.is_set():
                    ret_type = copy.deepcopy(cur_type)
                ret_list.append(ret_type)
            ret_type = ret_list[0] if len(ret_list)==1 else ret_list # single ret type or list
            symbols.add(ir_node.name.get_name())
            node_info = NodeInfo(ret_type, symbols=symbols)
            ir_node.la_type = ret_type
            node_info.ir = ir_node
            # Builtin function call
            if builtin_name in MESH_HELPER_FUNC_MAPPING:
                if builtin_name == NonZeros:
                    # track mesh
                    ret_type.owner = param_type_list[0].owner
                tri_node = GPFuncNode(param_list, MESH_HELPER_FUNC_MAPPING[builtin_name], builtin_name, identity_name=ir_node.identity_name)
                node_info = NodeInfo(ret_type, symbols=symbols)
                tri_node.la_type = ret_type
                node_info.ir = tri_node
                return node_info
            return node_info
        else:
            # not in symtable now
            # if ir_node.name.get_name() in self.pre_func_symtable:
            #     la_type = self.pre_func_symtable[ir_node.name.get_name()]
            # else:
            #     la_type = FunctionType(cur_type=FuncType.FuncDynamic)
            # self.get_cur_param_data().symtable[ir_node.name.get_main_id()] = la_type
            # assert False, "Not a function: {}".format(node.name)
            self.local_func_error = True
            raise RecursiveException
            node_info = NodeInfo(la_type, ir=ir_node)
            return node_info
            # assert len(node.params) == 1, "Not a function"  # never reach
            # return self.make_mul_info(name_info, self.walk(node.params[0], **kwargs))

    def walk_IfCondition(self, node, **kwargs):
        condition_node = ConditionNode(cond_type=ConditionType.ConditionOr, raw_text=node.text, parse_info=node.parseinfo)
        if node.single:
            condition_node.cond_type = ConditionType.ConditionAnd
            node_info = self.walk(node.single, **kwargs)
            condition_node.cond_list.append(node_info.ir)
        else:
            se_node_info = self.walk(node.se, **kwargs)
            other_node_info = self.walk(node.other, **kwargs)
            condition_node.cond_list.append(se_node_info.ir)
            condition_node.cond_list.append(other_node_info.ir)
        #
        # ir_node = IfNode(parse_info=node.parseinfo)
        # kwargs[IF_COND] = True
        # node_info = self.walk(node.cond, **kwargs)
        # ir_node.cond = node_info.ir
        # ir_node.la_type = node_info.la_type
        # # check special nodes
        # add_sub_node = ir_node.get_child(IRNodeType.AddSub)
        # if add_sub_node is not None:
        #     copy_node = copy.deepcopy(node_info.ir)
        #     assert add_sub_node.get_child(IRNodeType.AddSub) is None, get_err_msg_info(add_sub_node.parse_info, "Multiple +- symbols in a single expression")
        #     new_nodes = add_sub_node.split_node()
        #     add_sub_node.parent().value = new_nodes[0]
        #     #
        #     sec_node = copy.deepcopy(node_info.ir)
        #     add_node = sec_node.get_child(IRNodeType.Add)
        #     add_node.parent().value = new_nodes[1]
        #     #
        #     condition_node = ConditionNode(cond_type=ConditionType.ConditionOr)
        #     condition_node.cond_list.append(node_info.ir)
        #     condition_node.cond_list.append(sec_node)
        #     condition_node.tex_node = copy_node
        #     ir_node.cond = condition_node
        # node_info.ir = ir_node
        return NodeInfo(ir=condition_node)

    def walk_AndCondition(self, node, **kwargs):
        condition_node = ConditionNode(cond_type=ConditionType.ConditionAnd, raw_text=node.text,
                                       parse_info=node.parseinfo)
        if node.atom:
            node_info = self.walk(node.atom, **kwargs)
            condition_node.cond_list.append(node_info.ir)
        else:
            se_node_info = self.walk(node.se, **kwargs)
            other_node_info = self.walk(node.other, **kwargs)
            condition_node.cond_list.append(se_node_info.ir)
            condition_node.cond_list.append(other_node_info.ir)
        return NodeInfo(ir=condition_node)

    def walk_AtomCondition(self, node, **kwargs):
        ir_node = IfNode(raw_text=node.text, parse_info=node.parseinfo)
        kwargs[IF_COND] = True
        if node.p:
            node_info = self.walk(node.p, **kwargs)
            ir_node.cond = node_info.ir
        else:
            node_info = self.walk(node.cond, **kwargs)
            ir_node.cond = node_info.ir
            # check special nodes
            add_sub_node = node_info.ir.get_child(IRNodeType.AddSub)
            if add_sub_node is not None:
                copy_node = copy.deepcopy(node_info.ir)
                self.assert_expr(add_sub_node.get_child(IRNodeType.AddSub) is None, get_err_msg_info(add_sub_node.parse_info,
                                                                                           "Multiple +- symbols in a single expression"))
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
                ir_node.tex_node = copy_node
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    def walk_InCondition(self, node, **kwargs):
        ir_node = InNode(parse_info=node.parseinfo, raw_text=node.text)
        item_node = []
        for item in node.left:
            item_info = self.walk(item, **kwargs)
            item_node.append(item_info.ir)
            self.assert_expr(item_info.la_type.is_scalar(), get_err_msg_info(item_info.ir.parse_info, "Must be scalar type"))
        ir_node.items = item_node
        set_info = self.walk(node.right, **kwargs)
        ir_node.set = set_info.ir
        self.assert_expr(set_info.la_type.is_set(), get_err_msg_info(set_info.ir.parse_info, "Must be set type"))
        if set_info.la_type.element_type.is_tuple():
            self.assert_expr(len(item_node) == len(set_info.la_type.element_type.type_list), get_err_msg_info(node.parseinfo,
                                                                                                 "Size doesn't match for set: {} vs {}".format(
                                                                                                     len(item_node),
                                                                                                     len(set_info.la_type.type_list))))
        else:
            self.assert_expr(len(item_node) == len(set_info.la_type.type_list), get_err_msg_info(node.parseinfo, "Size doesn't match for set: {} vs {}".format(len(item_node), len(set_info.la_type.type_list))))
        return NodeInfo(ir=ir_node)

    def walk_NotInCondition(self, node, **kwargs):
        ir_node = NotInNode(parse_info=node.parseinfo, raw_text=node.text)
        item_node = []
        for item in node.left:
            item_info = self.walk(item, **kwargs)
            item_node.append(item_info.ir)
            self.assert_expr(item_info.la_type.is_scalar(), get_err_msg_info(item_info.ir.parse_info, "Must be scalar type"))
        ir_node.items = item_node
        set_info = self.walk(node.right, **kwargs)
        ir_node.set = set_info.ir
        self.assert_expr(set_info.la_type.is_set(), get_err_msg_info(set_info.ir.parse_info, "Must be set type"))
        if set_info.la_type.element_type.is_tuple():
            self.assert_expr(len(item_node) == len(set_info.la_type.element_type.type_list),
                             get_err_msg_info(node.parseinfo,
                                              "Size doesn't match for set: {} vs {}".format(
                                                  len(item_node),
                                                  len(set_info.la_type.type_list))))
        else:
            self.assert_expr(len(item_node) == len(set_info.la_type.type_list), get_err_msg_info(node.parseinfo,
                                                                                                 "Size doesn't match for set: {} vs {}".format(
                                                                                                     len(item_node),
                                                                                                     len(set_info.la_type.type_list))))
        return NodeInfo(VarTypeEnum.SCALAR, ir=ir_node)

    def walk_NeCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        self.assert_expr(left_info.la_type.is_same_type(right_info.la_type), get_err_msg(get_line_info(node.parseinfo),
                                                              get_line_info(node.parseinfo).text.find(node.op),
                                                              "Different types for comparison"))
        return NodeInfo(ir=BinCompNode(IRNodeType.Ne, left_info.ir, right_info.ir, parse_info=node.parseinfo, op=node.op, raw_text=node.text))

    def walk_EqCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        self.assert_expr(left_info.la_type.is_same_type(right_info.la_type), get_err_msg(get_line_info(node.parseinfo),
                                                              get_line_info(node.parseinfo).text.find(node.op),
                                                              "Different types for comparison"))
        return NodeInfo(ir=BinCompNode(IRNodeType.Eq, left_info.ir, right_info.ir, parse_info=node.parseinfo, op=node.op, raw_text=node.text))

    def walk_GreaterCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        self.assert_expr(left_info.la_type.is_scalar(), get_err_msg_info(left_info.ir.parse_info, "LHS has to be scalar type for comparison"))
        self.assert_expr(right_info.la_type.is_scalar(), get_err_msg_info(right_info.ir.parse_info, "RHS has to be scalar type for comparison"))
        return NodeInfo(ir=BinCompNode(IRNodeType.Gt, left_info.ir, right_info.ir, parse_info=node.parseinfo, op=node.op, raw_text=node.text))

    def walk_GreaterEqualCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        self.assert_expr(left_info.la_type.is_scalar(), get_err_msg_info(left_info.ir.parse_info, "LHS has to be scalar type for comparison"))
        self.assert_expr(right_info.la_type.is_scalar(), get_err_msg_info(right_info.ir.parse_info, "RHS has to be scalar type for comparison"))
        return NodeInfo(ir=BinCompNode(IRNodeType.Ge, left_info.ir, right_info.ir, parse_info=node.parseinfo, op=node.op, raw_text=node.text))

    def walk_LessCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        self.assert_expr(left_info.la_type.is_scalar(), get_err_msg_info(left_info.ir.parse_info, "LHS has to be scalar type for comparison"))
        self.assert_expr(right_info.la_type.is_scalar(), get_err_msg_info(right_info.ir.parse_info, "RHS has to be scalar type for comparison"))
        return NodeInfo(ir=BinCompNode(IRNodeType.Lt, left_info.ir, right_info.ir, parse_info=node.parseinfo, op=node.op, raw_text=node.text))

    def walk_LessEqualCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        self.assert_expr(left_info.la_type.is_scalar(), get_err_msg_info(left_info.ir.parse_info, "LHS has to be scalar type for comparison"))
        self.assert_expr(right_info.la_type.is_scalar(), get_err_msg_info(right_info.ir.parse_info, "RHS has to be scalar type for comparison"))
        return NodeInfo(ir=BinCompNode(IRNodeType.Le, left_info.ir, right_info.ir, parse_info=node.parseinfo, op=node.op, raw_text=node.text))

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

    def walk_IdentifierWithExpr(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        self.assert_expr(not self.is_param_block, get_err_msg_info(node.parseinfo, "Can only show up on the rhs"))
        content_symbol = {}
        if self.is_sym_existed(left_info.content):
            if self.get_sym_type(left_info.content).is_sequence():
                la_type = self.get_sym_type(left_info.content).element_type
                ir_node = SequenceIndexNode(parse_info=node.parseinfo, raw_text=node.text)
                ir_node.main = left_info.ir
                main_index_info = self.walk(node.exp[0])
                ir_node.main_index = main_index_info.ir
                if len(node.exp) == 1:
                    self.assert_expr(node.exp[0] != '*', get_err_msg(get_line_info(node.parseinfo),
                                                                       get_line_info(node.parseinfo).text.find('*'),
                                                                       "Can't use * as the index for a sequence"))
                    la_type = self.get_sym_type(left_info.content).element_type
                elif len(node.exp) == 2:
                    self.assert_expr(self.get_sym_type(left_info.content).is_vector_seq(),
                                     get_err_msg_info(left_info.ir.parse_info,
                                                      "Two subscripts are used for sequence of vector"))
                    self.assert_expr('*' not in node.exp, get_err_msg(get_line_info(node.parseinfo),
                                                                        get_line_info(node.parseinfo).text.find(
                                                                            '*'),
                                                                        "* can't be used here"))
                    main_index_info = self.walk(node.exp[0])
                    row_index_info = self.walk(node.exp[1])
                    ir_node.main_index = main_index_info.ir
                    ir_node.row_index = row_index_info.ir
                    la_type = self.get_sym_type(left_info.content).element_type.element_type
                elif len(node.exp) == 3:
                    self.assert_expr(self.get_sym_type(left_info.content).is_matrix_seq(),
                                     get_err_msg_info(left_info.ir.parse_info,
                                                      "Triple subscripts are only used for a sequence of matrix"))
                    self.assert_expr(node.exp[0] != '*', get_err_msg(get_line_info(node.parseinfo),
                                                                       get_line_info(node.parseinfo).text.find('*'),
                                                                       "* can't be the first subscript here"))
                    if '*' in node.exp:
                        ir_node.slice_matrix = True
                        if node.exp[1] == '*':
                            self.assert_expr(node.exp[2] != '*', get_err_msg(get_line_info(node.parseinfo),
                                                                               get_line_info(
                                                                                   node.parseinfo).text.find('*'),
                                                                               "Only one * is allowed as subscripts"))
                            la_type = VectorType(rows=self.get_sym_type(left_info.content).element_type.rows)
                            col_index_info = self.walk(node.exp[2])
                            ir_node.col_index = col_index_info.ir
                        else:
                            la_type = MatrixType(rows=1,
                                                 cols=self.get_sym_type(left_info.content).element_type.cols)
                            row_index_info = self.walk(node.right[1])
                            ir_node.row_index = row_index_info.ir
                    else:
                        row_index_info = self.walk(node.exp[1])
                        col_index_info = self.walk(node.exp[2])
                        ir_node.main_index = main_index_info.ir
                        ir_node.row_index = row_index_info.ir
                        ir_node.col_index = col_index_info.ir
                        la_type = self.get_sym_type(left_info.content).element_type.element_type
                ir_node.la_type = la_type
                node_info = NodeInfo(la_type, content_symbol,
                                {node.text},
                                ir_node)
            elif self.get_sym_type(left_info.content).is_matrix():
                ir_node = MatrixIndexNode(parse_info=node.parseinfo, raw_text=node.text)
                ir_node.main = left_info.ir
                la_type = self.get_sym_type(left_info.content).element_type
                if '*' in node.exp:
                    if node.exp[0] == '*':
                        self.assert_expr(node.exp[1] != '*', get_err_msg(get_line_info(node.parseinfo),
                                                                           get_line_info(node.parseinfo).text.find(
                                                                               '*'),
                                                                           "Only one * is allowed as subscripts"))
                        la_type = VectorType(rows=self.get_sym_type(left_info.content).rows)
                        col_index_info = self.walk(node.exp[1])
                        ir_node.col_index = col_index_info.ir
                    else:
                        la_type = VectorType(rows=self.get_sym_type(left_info.content).cols)
                        row_index_info = self.walk(node.exp[0])
                        ir_node.row_index = row_index_info.ir
                else:
                    row_index_info = self.walk(node.exp[0])
                    col_index_info = self.walk(node.exp[1])
                    ir_node.row_index = row_index_info.ir
                    ir_node.col_index = col_index_info.ir
                ir_node.la_type = la_type
                node_info = NodeInfo(la_type, content_symbol, {node.text}, ir_node)
            elif self.get_sym_type(left_info.content).is_vector():
                self.assert_expr(len(node.exp) == 1, get_err_msg_info(left_info.ir.parse_info,
                                                                        "Only one subscript is allowed"))
                self.assert_expr(node.exp[0] != '*', get_err_msg(get_line_info(node.parseinfo),
                                                                   get_line_info(node.parseinfo).text.find('*'),
                                                                   "Subscript can't be *"))
                index_info = self.walk(node.exp[0])
                self.assert_expr(index_info.la_type.is_scalar(), get_err_msg_info(index_info.ir.parse_info,
                                                                                  "Subscript must be scalar"))
                ir_node = VectorIndexNode(parse_info=node.parseinfo, raw_text=node.text)
                ir_node.main = left_info.ir
                ir_node.row_index = index_info.ir
                ir_node.la_type = self.get_sym_type(left_info.content).element_type
                node_info = NodeInfo(self.get_sym_type(left_info.content).element_type, content_symbol, {node.text},
                                     ir_node)
        return node_info

    def walk_IdentifierSubscript(self, node, **kwargs):
        if node.exp and len(node.exp) > 0:
             return self.walk_IdentifierWithExpr(node, **kwargs)
        def get_right_list():
            # rhs only
            right_list = []
            for right in node.right:
                if right != '*':
                    r_content = self.walk(right).content
                    right_list.append(r_content)
                    if not self.visiting_lhs and not isinstance(r_content, int):
                        self.assert_expr(self.is_sym_existed(r_content), get_err_msg_info(right.parseinfo, "Subscript {} has not been defined".format(r_content)))
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
                    self.assert_expr(raw_text[cur] == ' ', get_err_msg(line_info, line_info.text.index('_*') + 1, "* must be used with ," ))
                cur += 1
        right = []
        left_info = self.walk(node.left, **kwargs)
        if not self.is_param_block:
            if left_info.content == 'I' and not self.is_sym_existed('I'):
                right_sym_list = get_right_list()
                self.assert_expr(len(right_sym_list) == 1 and '*' not in right_sym_list, get_err_msg_info(left_info.ir.parse_info,
                                                                                        "Invalid identity matrix"))
                ir_node = NumMatrixNode(parse_info=node.parseinfo, raw_text=node.text)
                if isinstance(right_sym_list[0], str):
                    self.assert_expr(self.is_sym_existed(right_sym_list[0]), get_err_msg(line_info, line_info.text.index('_{}'.format(right_sym_list[0])) + 1,"{} unknown".format(right_sym_list[0])))
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
                self.assert_expr(self.is_sym_existed(left_info.content), get_err_msg_info(left_info.ir.parse_info,
                                                                                        "Element hasn't been defined"))
                if self.get_sym_type(left_info.content).is_sequence():
                    if left_info.content in self.get_cur_param_data().dim_seq_set:
                        # index the sequence of dimension
                        ir_node = SeqDimIndexNode(parse_info=node.parseinfo, raw_text=node.text)
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
                    ir_node = SequenceIndexNode(parse_info=node.parseinfo, raw_text=node.text)
                    ir_node.main = left_info.ir
                    main_index_info = self.walk(node.right[0])
                    ir_node.main_index = main_index_info.ir
                    if len(node.right) == 1:
                        self.assert_expr(node.right[0] != '*', get_err_msg(get_line_info(node.parseinfo),
                                                                  get_line_info(node.parseinfo).text.find('*'),
                                                                  "Can't use * as the index for a sequence"))
                        la_type = self.get_sym_type(left_info.content).element_type
                    elif len(node.right) == 2:
                        self.assert_expr(self.get_sym_type(left_info.content).is_vector_seq(), get_err_msg_info(left_info.ir.parse_info,
                                                                       "Two subscripts are used for sequence of vector"))
                        self.assert_expr('*' not in node.right, get_err_msg(get_line_info(node.parseinfo),
                                                                  get_line_info(node.parseinfo).text.find('*'),
                                                                  "* can't be used here"))
                        main_index_info = self.walk(node.right[0])
                        row_index_info = self.walk(node.right[1])
                        ir_node.main_index = main_index_info.ir
                        ir_node.row_index = row_index_info.ir
                        la_type = self.get_sym_type(left_info.content).element_type.element_type
                    elif len(node.right) == 3:
                        self.assert_expr(self.get_sym_type(left_info.content).is_matrix_seq(), get_err_msg_info(left_info.ir.parse_info,
                                                                                        "Triple subscripts are only used for a sequence of matrix"))
                        self.assert_expr(node.right[0] != '*', get_err_msg(get_line_info(node.parseinfo),
                                                                  get_line_info(node.parseinfo).text.find('*'),
                                                                  "* can't be the first subscript here"))
                        if '*' in node.right:
                            ir_node.slice_matrix = True
                            if node.right[1] == '*':
                                self.assert_expr(node.right[2] != '*', get_err_msg(get_line_info(node.parseinfo),
                                                                  get_line_info(node.parseinfo).text.find('*'),
                                                                  "Only one * is allowed as subscripts"))
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
                    self.assert_expr(len(node.right) == 2, get_err_msg_info(left_info.ir.parse_info,
                                                                       "Two subscripts are required for matrix"))
                    ir_node = MatrixIndexNode(parse_info=node.parseinfo, raw_text=node.text)
                    ir_node.subs = right_sym_list
                    ir_node.main = left_info.ir
                    la_type = self.get_sym_type(left_info.content).element_type
                    if '*' in node.right:
                        if node.right[0] == '*':
                            self.assert_expr(node.right[1] != '*', get_err_msg(get_line_info(node.parseinfo),
                                                                  get_line_info(node.parseinfo).text.find('*'),
                                                                  "Only one * is allowed as subscripts"))
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
                    self.assert_expr(len(node.right) == 1, get_err_msg_info(left_info.ir.parse_info,
                                                                                        "Only one subscript is allowed"))
                    self.assert_expr(node.right[0] != '*', get_err_msg(get_line_info(node.parseinfo),
                                                                  get_line_info(node.parseinfo).text.find('*'),
                                                                  "Subscript can't be *"))
                    index_info = self.walk(node.right[0])
                    self.assert_expr(index_info.la_type.is_scalar(), get_err_msg_info(index_info.ir.parse_info,
                                                                                        "Subscript must be scalar"))
                    ir_node = VectorIndexNode(parse_info=node.parseinfo, raw_text=node.text)
                    ir_node.main = left_info.ir
                    ir_node.row_index = index_info.ir
                    ir_node.la_type = self.get_sym_type(left_info.content).element_type
                    ir_node.process_subs_dict(self.lhs_sub_dict)
                    node_info = NodeInfo(self.get_sym_type(left_info.content).element_type, content_symbol, {node.text}, ir_node)
                    return node_info
                elif self.get_sym_type(left_info.content).is_set():
                    self.assert_expr(len(node.right) == 1, get_err_msg_info(left_info.ir.parse_info,
                                                                                        "Only one subscript is allowed"))
                    self.assert_expr(node.right[0] != '*', get_err_msg(get_line_info(node.parseinfo),
                                                                  get_line_info(node.parseinfo).text.find('*'),
                                                                  "Subscript can't be *"))
                    index_info = self.walk(node.right[0])
                    self.assert_expr(index_info.la_type.is_scalar(), get_err_msg_info(index_info.ir.parse_info,
                                                                                        "Subscript must be scalar"))
                    ir_node = SetIndexNode(parse_info=node.parseinfo, raw_text=node.text)
                    ir_node.main = left_info.ir
                    ir_node.row_index = index_info.ir
                    ir_node.la_type = self.get_sym_type(left_info.content).element_type
                    ir_node.process_subs_dict(self.lhs_sub_dict)
                    node_info = NodeInfo(self.get_sym_type(left_info.content).element_type, content_symbol, {node.text}, ir_node)
                    return node_info
                elif self.get_sym_type(left_info.content).is_tuple():
                    self.assert_expr(len(node.right) == 1, get_err_msg_info(left_info.ir.parse_info,
                                                                                        "Only one subscript is allowed"))
                    self.assert_expr(node.right[0] != '*', get_err_msg(get_line_info(node.parseinfo),
                                                                  get_line_info(node.parseinfo).text.find('*'),
                                                                  "Subscript can't be *"))
                    index_info = self.walk(node.right[0])
                    self.assert_expr(index_info.la_type.is_scalar(), get_err_msg_info(index_info.ir.parse_info,
                                                                                        "Subscript must be scalar"))
                    ir_node = TupleIndexNode(parse_info=node.parseinfo, raw_text=node.text)
                    ir_node.main = left_info.ir
                    ir_node.row_index = index_info.ir
                    self.assert_expr(isinstance(ir_node.row_index.value, int), get_err_msg_info(index_info.ir.parse_info,
                                                                                        "Subscript has to be int value when indexing tuple"))
                    ir_node.la_type = self.get_sym_type(left_info.content).type_list[ir_node.row_index.value-1]
                    ir_node.process_subs_dict(self.lhs_sub_dict)
                    node_info = NodeInfo(ir_node.la_type, content_symbol, {node.text}, ir_node)
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
        ir_node = IdNode(left_content, right_content, parse_info=parse_info, raw_text=content)
        ir_node.la_type = node_type
        node_info = NodeInfo(node_type, content, {content}, ir_node)
        self.get_cur_param_data().ids_dict[content] = Identifier(left_content, right_content)
        return node_info

    def walk_IdentifierAlone(self, node, **kwargs):
        node_type = LaVarType(VarTypeEnum.INVALID)
        if node.value:
            value = node.value
            if isinstance(node.value, list):
                # prefix is a keyword
                value = ''.join(node.value)
            value = get_unicode_subscript(value)
            value = get_unicode_superscript(value)
        elif node.id:
            value = '`' + node.id + '`'
        else:
            value = node.const
        value = self.filter_symbol(value)
        #
        ir_node = IdNode(value, parse_info=node.parseinfo, raw_text=node.text)
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
        ir_node = FactorNode(parse_info=node.parseinfo, raw_text=node.text)
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
                        if not self.visiting_solver_eq:
                            self.check_sym_existence(new_symbol, get_err_msg_info(id0_info.ir.parse_info,
                                                                                             "Symbol {} is not defined".format(id0)))
                            # pass  # todo:delete
                    else:
                        # I
                        if 'I' not in self.symtable:
                            if not la_is_inside_matrix(**kwargs):
                                self.assert_expr(id0_info.ir.contain_subscript(), get_err_msg_info(id0_info.ir.parse_info,
                                                                                        "Identity matrix must have subscript if used outside block matrix"))
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
        elif node.s:
            node_info = self.walk(node.s, **kwargs)
            ir_node.s = node_info.ir
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
        ir_node = ConstantNode(ConstantType.ConstantPi, parse_info=node.parseinfo, raw_text=node.text)
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    def walk_Infinity(self, node, **kwargs):
        node_info = NodeInfo(ScalarType())
        ir_node = ConstantNode(ConstantType.ConstantInf, parse_info=node.parseinfo, raw_text=node.text)
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    def walk_E(self, node, **kwargs):
        node_info = NodeInfo(ScalarType())
        ir_node = ConstantNode(ConstantType.ConstantE, parse_info=node.parseinfo, raw_text=node.text)
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    def walk_Integer(self, node, **kwargs):
        value = ''.join(node.value)
        node_type = ScalarType(is_int=True, is_constant=True)
        node_info = NodeInfo(node_type, content=int(value))
        #
        ir_node = IntegerNode(parse_info=node.parseinfo, raw_text=node.text)
        ir_node.value = int(value)
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    def walk_SubInteger(self, node, **kwargs):
        value = 0
        for index in range(len(node.value)):
            value += get_unicode_sub_number(node.value[len(node.value) - 1 - index]) * 10 ** index
        node_type = ScalarType(is_int=True, is_constant=True)
        node_info = NodeInfo(node_type, content=int(value))
        #
        ir_node = IntegerNode(parse_info=node.parseinfo, raw_text=node.text)
        ir_node.value = int(value)
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    def walk_SupInteger(self, node, **kwargs):
        value = 0
        for index in range(len(node.value)):
            value += get_unicode_number(node.value[len(node.value) - 1 - index]) * 10 ** index
        node_type = ScalarType(is_int=True, is_constant=True)
        node_info = NodeInfo(node_type, content=int(value))
        #
        ir_node = IntegerNode(parse_info=node.parseinfo, raw_text=node.text)
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
        ir_node = DoubleNode(parse_info=node.parseinfo, raw_text=node.text)
        ir_node.value = node_value
        ir_node.la_type = node_info.la_type
        node_info.ir = ir_node
        return node_info

    def walk_Fraction(self, node, **kwargs):
        frac_list = get_unicode_fraction(node.value)
        node_info = NodeInfo(ScalarType(), content=node.text)
        ir_node = FractionNode(parse_info=node.parseinfo, numerator=frac_list[0], denominator=frac_list[1], raw_text=node.text)
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
            ir_node = SparseMatrixNode(parse_info=node.parseinfo, raw_text=node.text)
            # ifsNode
            ifs_info = self.walk(node.ifs, **kwargs)
            ifs_node = SparseIfsNode(parse_info=node.ifs.parseinfo, raw_text=node.text)
            first = True
            in_cond_only = True
            for ir in ifs_info.ir:
                ir.first_in_list = first
                first = False
                ifs_node.cond_list.append(ir)
                ir.set_parent(ifs_node)
                # if not (ir.cond.cond.node_type == IRNodeType.In and ir.cond.cond.same_subs(all_ids[1])):
                if not ir.cond.same_subs(all_ids[1]):
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
                self.assert_expr(all_ids[0] in self.symtable, get_err_msg_info(node.parseinfo, "Sparse matrix: need dim"))
                if all_ids[0] in self.parameters:
                    self.parameters.remove(all_ids[0])  # not a parameter
                    self.get_cur_param_data().remove_target_from_dim_dict(all_ids[0])
                id1 = self.symtable[all_ids[0]].rows
                if not isinstance(id1, int):
                    self.assert_expr(id1 in self.get_cur_param_data().dim_dict or id1 in self.parameters, get_err_msg_info(node.parseinfo, "Sparse matrix: dim {} is not defined".format(id1)))
                id2 = self.symtable[all_ids[0]].cols
                if not isinstance(id2, int):
                    self.assert_expr(id2 in self.get_cur_param_data().dim_dict or id2 in self.parameters, get_err_msg_info(node.parseinfo, "Sparse matrix: dim {} is not defined".format(id2)))
                la_type = MatrixType(rows=id1, cols=id2, sparse=True, index_var=index_var, value_var=value_var)
                self.symtable[new_id] = la_type
            elif op == '+=':
                self.assert_expr(all_ids[0] in self.symtable, get_err_msg_info(node.parseinfo, "{} is not defined".format(all_ids[0])))
                la_type = self.symtable[all_ids[0]]
                id_name = all_ids[0]
                id1 = self.symtable[all_ids[0]].rows
                if not isinstance(id1, int):
                    self.assert_expr(id1 in self.symtable, get_err_msg_info(node.parseinfo,
                                                                       "Sparse matrix: dim {} is not defined".format(id1)))
                id2 = self.symtable[all_ids[0]].cols
                if not isinstance(id2, int):
                    self.assert_expr(id2 in self.symtable, get_err_msg_info(node.parseinfo,
                                                                       "Sparse matrix: dim {} is not defined".format(id2)))
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
            is_int = True
            symbols = set()
            ir_node = MultiCondNode(parse_info=node.parseinfo, raw_text=node.text)
            # ifsNode
            ifs_info = self.walk(node.ifs, **kwargs)
            ifs_node = SparseIfsNode(parse_info=node.ifs.parseinfo, raw_text=node.text)
            ifs_node.set_parent(ir_node)
            symbols = symbols.union(ifs_info.symbols)
            first = True
            la_type = LaVarType()
            for ir in ifs_info.ir:
                ir.first_in_list = first
                first = False
                ifs_node.cond_list.append(ir)
                ir.set_parent(ifs_node)
                la_type = ir.la_type if ir.la_type.is_valid() else la_type
                if is_int and not la_type.is_integer_element():
                    is_int = False
            ir_node.ifs = ifs_node
            if node.other:
                if self.local_func_parsing:
                    try:
                        other_info = self.walk(node.other, **kwargs)
                        ir_node.other = other_info.ir
                        symbols = symbols.union(other_info.symbols)
                        la_type = other_info.ir.la_type if other_info.ir.la_type.is_valid() else la_type
                    except RecursiveException:
                        pass
                else:
                    other_info = self.walk(node.other, **kwargs)
                    ir_node.other = other_info.ir
                    symbols = symbols.union(other_info.symbols)
                    la_type = other_info.ir.la_type if other_info.ir.la_type.is_valid() else la_type
                if is_int and not la_type.is_integer_element():
                    is_int = False
            la_type.set_int(is_int)
            node_info = NodeInfo(la_type, symbols=symbols)
            ir_node.la_type = la_type
            node_info.ir = ir_node
        return node_info

    def walk_MultiIfs(self, node, **kwargs):
        symbols = set()
        ir_list = []
        if self.local_func_parsing:
            try:
                if node.ifs:
                    node_info = self.walk(node.ifs, **kwargs)
                    ir_list += node_info.ir
                    symbols = symbols.union(node_info.symbols)
                if node.value:
                    node_info = self.walk(node.value, **kwargs)
                    ir_list.append(node_info.ir)
                    symbols = symbols.union(node_info.symbols)
            except RecursiveException:
                pass
        else:
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
        ir_node = SparseIfNode(parse_info=node.parseinfo, raw_text=node.text)
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
        is_int = True
        for exp in node.exp:
            exp_info = self.walk(exp, **kwargs)
            self.assert_expr(exp_info.la_type.is_scalar() or exp_info.la_type.is_vector(), get_err_msg_info(node.parseinfo, "Item in vector must be scalar or vector"))
            ir_node.items.append(exp_info.ir)
            if exp_info.la_type.is_vector():
                dim_list.append(exp_info.la_type.rows)
            else:
                dim_list.append(1)
            symbols = symbols.union(exp_info.symbols)
            if is_int:
                is_int = exp_info.la_type.is_integer_element()
        ir_node.la_type = VectorType(rows=self.get_sum_value(dim_list), element_type=ScalarType(is_int=is_int))
        node_info = NodeInfo(ir=ir_node, la_type=ir_node.la_type, symbols=symbols)
        if LHS in kwargs:
            lhs = kwargs[LHS]
            new_id = self.generate_var_name(lhs)
            self.symtable[new_id] = ir_node.la_type
            ir_node.symbol = new_id
        # elif self.local_func_parsing:
        else:
            new_id = self.generate_var_name(self.local_func_name)
            self.get_cur_param_data().symtable[new_id] = ir_node.la_type
            ir_node.symbol = new_id

        return node_info

    def walk_Set(self, node, **kwargs):
        symbols = set()
        new_id = self.generate_var_name("set_def")
        enum_list = []
        ir_node = SetNode(parse_info=node.parseinfo, raw_text=node.text)
        self.push_scope(new_id)
        ir_node.scope_name = new_id
        self.assert_expr(len(node.exp) > 0, get_err_msg_info(node.parseinfo, "Empty set is not allowed."))
        f_type = None
        dynamic = DynamicTypeEnum.DYN_INVALID
        set_length = len(node.exp)
        if node.enum:
            ir_node.f = node.f
            ir_node.o = node.o
            range_info = self.walk(node.range, **kwargs)
            ir_node.range = range_info.ir
            if range_info.la_type.size == len(node.enum):
                # (i,j ∈ E)
                for cur_index in range(len(node.enum)):
                    cur_id_raw = node.enum[cur_index]
                    enum = self.walk(cur_id_raw, **kwargs)
                    enum_list.append(enum.content)
                    self.check_sym_existence(enum.content, get_err_msg_info(cur_id_raw.parseinfo, "Subscript has been defined"), False)
                    self.add_sym_type(enum.content, range_info.la_type.type_list[cur_index])
            else:
                # (e ∈ E)
                self.assert_expr(range_info.la_type.size > 1 and len(node.enum) == 1, get_err_msg_info(node.parseinfo, "Invalid size"))
                cur_id_raw = node.enum[0]
                enum = self.walk(cur_id_raw)
                enum_list.append(enum.content)
                self.check_sym_existence(enum.content, get_err_msg_info(cur_id_raw.parseinfo, "Subscript has been defined"), False)
                self.add_sym_type(enum.content, TupleType(type_list=range_info.la_type.type_list))
                ir_node.use_tuple = True
            ir_node.enum_list = enum_list
            dynamic = DynamicTypeEnum.DYN_DIM
            set_length = None
        if node.cond:
            ir_node.cond = self.walk(node.cond, **kwargs).ir
        for c_index in range(len(node.exp)):
            exp_info = self.walk(node.exp[c_index], **kwargs)
            if c_index == 0:
                f_type = exp_info.la_type
            else:
                self.assert_expr(f_type.is_same_type(exp_info.la_type), get_err_msg_info(node.parseinfo, "Different element types."))
            ir_node.items.append(exp_info.ir)
            symbols = symbols.union(exp_info.symbols)
        if f_type.is_vertex_type():
            ir_node.la_type = VertexSetType(owner=f_type.owner)
        elif f_type.is_edge_type():
            ir_node.la_type = EdgeSetType(owner=f_type.owner)
        elif f_type.is_face_type():
            ir_node.la_type = FaceSetType(owner=f_type.owner)
        elif f_type.is_tet_type():
            ir_node.la_type = TetSetType(owner=f_type.owner)
        else:
            ir_node.la_type = SetType(size=1, int_list=[True], type_list=[f_type], element_type=f_type, index_type=f_type.index_type, owner=f_type.owner, dynamic=dynamic)
        ir_node.la_type.length = set_length
        node_info = NodeInfo(ir=ir_node, la_type=ir_node.la_type, symbols=symbols)
        self.pop_scope()
        new_id = self.generate_var_name(self.local_func_name+"set")
        self.add_sym_type(new_id, ir_node.la_type)
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
        is_int = True
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
                if is_int:
                    is_int = col.la_type.is_integer_element()
            if len(row) > cols:
                cols = len(row)
            type_array.append(row_type)
        list_dim = None
        if block:
            # check block mat
            valid, undef_list, type_array, real_dims = self.check_bmat_validity(type_array, None)
            self.assert_expr(valid, get_err_msg_info(node.parseinfo,  "Block matrix error. Invalid dimensions"))
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
                            self.assert_expr('0' == cur_ir.raw_text or '1' == cur_ir.raw_text, get_err_msg_info(cur_ir.parse_info, "Can not lift {}".format(cur_ir.raw_text)))
                    list_dim[(i, j)] = [type_array[i][j].rows, type_array[i][j].cols]
        node_type = MatrixType(rows=rows, cols=cols, block=block, sparse=sparse, list_dim=list_dim, item_types=node_info.content)
        ret_node_info = NodeInfo(node_type, symbols=node_info.symbols)
        if LHS in kwargs:
            lhs = kwargs[LHS]
            new_id = self.generate_var_name(lhs)
            self.get_cur_param_data().symtable[new_id] = MatrixType(rows=rows, cols=cols, element_type=ScalarType(is_int=is_int), block=block, sparse=sparse, list_dim=list_dim, item_types=node_info.content)
            ret_node_info.symbol = new_id
            ir_node.symbol = new_id
        elif self.local_func_parsing:
            new_id = self.generate_var_name(self.local_func_name)
            self.get_cur_param_data().symtable[new_id] = MatrixType(rows=rows, cols=cols, element_type=ScalarType(is_int=is_int), block=block, sparse=sparse, list_dim=list_dim,
                                               item_types=node_info.content)
            ret_node_info.symbol = new_id
            ir_node.symbol = new_id
        ir_node.la_type = self.get_sym_type(new_id)
        ret_node_info.ir = ir_node
        ret_node_info.la_type = ir_node.la_type
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
        ir_node = NumMatrixNode(parse_info=node.parseinfo, raw_text=node.text)
        id1_info = self.walk(node.id1, **kwargs)
        ir_node.id1 = id1_info.ir
        id1_info.ir.set_parent(ir_node)
        id1 = id1_info.content
        if isinstance(id1, str):
            self.assert_expr(id1 in self.symtable, get_err_msg_info(id1_info.ir.parse_info, "{} unknown".format(id1)))
        ir_node.left = node.left
        if node.left == '0':
            self.assert_expr(la_is_inside_matrix(**kwargs), get_err_msg_info(node.parseinfo, "Zero matrix can only be used inside matrix"))
        if node.id2:
            id2_info = self.walk(node.id2, **kwargs)
            ir_node.id2 = id2_info.ir
            id2 = id2_info.content
            if isinstance(id2, str):
                self.assert_expr(id2 in self.symtable, get_err_msg_info(id2_info.ir.parse_info, "{} unknown".format(id2)))
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
            self.assert_expr(param.la_type.is_scalar() or param.la_type.is_matrix() or param.la_type.is_vector(), \
                get_err_msg_info(param.parse_info, "Parameter must be scalar, vector or matrix type"))
        elif func_type < MathFuncType.MathFuncTrace:
            self.assert_expr(param.la_type.is_scalar(), get_err_msg_info(param.parse_info, "Parameter must be scalar type"))
            for par_info in remains:
                par = par_info.ir
                remain_list.append(par)
                self.assert_expr(par.la_type.is_scalar(), get_err_msg_info(par.parse_info, "Parameter must be scalar type"))
                symbols = symbols.union(par_info.symbols)
        elif func_type == MathFuncType.MathFuncTrace:
            self.assert_expr(param.la_type.is_matrix() and param.la_type.rows == param.la_type.cols, get_err_msg_info(param.parse_info, "Parameter must be valid matrix type"))
            ret_type = ScalarType()
        elif func_type == MathFuncType.MathFuncDiag:
            self.assert_expr((param.la_type.is_matrix() and param.la_type.rows == param.la_type.cols) or param.la_type.is_vector(), get_err_msg_info(param.parse_info, "Parameter must be valid matrix or vector type"))
            if param.la_type.is_matrix():
                ret_type = VectorType(rows=param.la_type.rows)
                self.assert_expr(len(remains) == 0, get_err_msg_info(param.parse_info, "Invalid multiple parameters found"))
            else:
                ret_type = MatrixType(rows=param.la_type.rows, cols=param.la_type.rows)
                remain_list = []
                if len(remains) > 0:
                    self.assert_expr(len(remains) == 2, get_err_msg_info(param.parse_info, "Invalid multiple parameters found"))
                    for r in remains:
                        self.assert_expr(r.la_type.is_scalar(), get_err_msg_info(param.parse_info, "Invalid multiple parameters"))
                        remain_list.append(r.ir)
                    ret_type = MatrixType(dynamic=DynamicTypeEnum.DYN_ROW|DynamicTypeEnum.DYN_COL)
        elif func_type == MathFuncType.MathFuncVec:
            if param.la_type.is_matrix():
                self.assert_expr(param.la_type.is_matrix(), get_err_msg_info(param.parse_info, "Parameter must be valid matrix type"))
                ret_type = VectorType(rows=param.la_type.rows*param.la_type.cols)
            elif param.la_type.is_set():
                ret_type = VectorType(element_type=param.la_type.element_type)
            elif param.la_type.is_sequence():
                if param.la_type.element_type.is_scalar():
                    ret_type = VectorType(element_type=param.la_type.element_type, rows=param.la_type.size)
                elif param.la_type.element_type.is_vector():
                    ret_type = VectorType(element_type=param.la_type.element_type.element_type, rows=mul_dims(param.la_type.size, param.la_type.element_type.rows))
                elif param.la_type.element_type.is_matrix():
                    ret_type = VectorType(element_type=param.la_type.element_type.element_type, rows=mul_dims(mul_dims(param.la_type.size, param.la_type.element_type.rows), param.la_type.element_type.cols))
        elif func_type == MathFuncType.MathFuncInverseVec:
            self.assert_expr(param.la_type.is_vector(), get_err_msg_info(param.parse_info, "Parameter must be valid vector type"))
            if remains[0].la_type.is_matrix():
                self.assert_expr(is_same_expr(param.la_type.rows, mul_dims(remains[0].la_type.rows, remains[0].la_type.cols)), get_err_msg_info(param.parse_info, "Size mismatch"))
            elif remains[0].la_type.is_sequence():
                if remains[0].la_type.element_type.is_scalar():
                    self.assert_expr(is_same_expr(param.la_type.rows, remains[0].la_type.size), get_err_msg_info(param.parse_info, "Size mismatch"))
                elif remains[0].la_type.element_type.is_vector():
                    self.assert_expr(is_same_expr(param.la_type.rows, mul_dims(remains[0].la_type.size, remains[0].la_type.element_type.rows)), get_err_msg_info(param.parse_info, "Size mismatch"))
            ret_type = remains[0].la_type
            remain_list.append(remains[0].ir)
            symbols = symbols.union(remains[0].symbols)
        elif func_type == MathFuncType.MathFuncDet:
            self.assert_expr(param.la_type.is_matrix(), get_err_msg_info(param.parse_info, "Parameter must be valid matrix type"))
            ret_type = ScalarType()
        elif func_type == MathFuncType.MathFuncRank:
            self.assert_expr(param.la_type.is_matrix(), get_err_msg_info(param.parse_info,
                                                                    "Parameter must be valid matrix type"))
            ret_type = ScalarType()
        elif func_type == MathFuncType.MathFuncNull:
            self.assert_expr(param.la_type.is_matrix(), get_err_msg_info(param.parse_info,
                                                                    "Parameter must be valid matrix type"))
            ret_type = MatrixType(rows=param.la_type.cols, dynamic=DynamicTypeEnum.DYN_COL)  # dynamic dims
        elif func_type == MathFuncType.MathFuncOrth:
            self.assert_expr(param.la_type.is_matrix(), get_err_msg_info(param.parse_info,
                                                                    "Parameter must be valid matrix type"))
            ret_type = MatrixType(rows=param.la_type.rows, dynamic=DynamicTypeEnum.DYN_COL)  # dynamic dims
        elif func_type == MathFuncType.MathFuncInv:
            self.assert_expr(param.la_type.is_matrix() and param.la_type.rows == param.la_type.cols, get_err_msg_info(param.parse_info, "Parameter must be valid matrix type"))
            ret_type = MatrixType(rows=param.la_type.rows, cols=param.la_type.cols)
        elif func_type == MathFuncType.MathFuncMin or func_type == MathFuncType.MathFuncMax:
            ret_type = ScalarType()
            if remains and len(remains) > 0:
                # multi params
                self.assert_expr(param.la_type.is_scalar(), get_err_msg_info(param.parse_info, "Parameter must be valid scalar type for multiple params"))
                for par_info in remains:
                    par = par_info.ir
                    remain_list.append(par)
                    self.assert_expr(par.la_type.is_scalar(),
                                     get_err_msg_info(par.parse_info, "Parameter must be scalar type for multiple params"))
                    symbols = symbols.union(par_info.symbols)
            else:
                # one param
                self.assert_expr(param.la_type.is_set() or param.la_type.is_matrix() or param.la_type.is_vector() or param.la_type.is_sequence(), get_err_msg_info(param.parse_info,
                                                                             "Parameter must be valid matrix/vector/set/sequence type"))
                ret_type = param.la_type.element_type
        elif func_type == MathFuncType.MathFuncSVD:
            self.assert_expr(param.la_type.is_matrix(), get_err_msg_info(param.parse_info, "Parameter must be valid matrix type"))
            dynamic = DynamicTypeEnum.DYN_INVALID
            u_type = MatrixType(rows=param.la_type.rows, cols=param.la_type.rows,element_type=ScalarType(is_int=False))
            s_type = VectorType(rows=param.la_type.rows,element_type=ScalarType(is_int=False))
            v_type = MatrixType(rows=param.la_type.cols, cols=param.la_type.cols,element_type=ScalarType(is_int=False))
            if param.la_type.is_dynamic():
                if param.la_type.is_dynamic_row() and param.la_type.is_dynamic_col():
                    u_type.dynamic = DynamicTypeEnum.DYN_ROW | DynamicTypeEnum.DYN_COL
                    s_type.dynamic = DynamicTypeEnum.DYN_ROW
                    v_type.dynamic = DynamicTypeEnum.DYN_ROW | DynamicTypeEnum.DYN_COL
                elif param.la_type.is_dynamic_row():
                    u_type.dynamic = DynamicTypeEnum.DYN_ROW | DynamicTypeEnum.DYN_COL
                    s_type.dynamic = DynamicTypeEnum.DYN_ROW
                else:
                    s_type.dynamic = DynamicTypeEnum.DYN_ROW
                    v_type.dynamic = DynamicTypeEnum.DYN_ROW | DynamicTypeEnum.DYN_COL
            ret_type = TupleType(type_list=[u_type, s_type, v_type])
        tri_node = MathFuncNode(param, func_type, remain_list)
        node_info = NodeInfo(ret_type, symbols=symbols)
        tri_node.la_type = ret_type
        node_info.ir = tri_node
        return node_info

    def create_gp_node_info(self, func_type, node, **kwargs):
        # geometry processing node
        param_list = []
        symbols = set()
        for param in node.params:
            param_info = self.walk(param, **kwargs)
            param_list.append(param_info.ir)
            symbols = symbols.union(param_info.symbols)
        ret_type = ScalarType()
        if func_type == GPType.FacesOfEdge:
            ret_type = [ScalarType(), ScalarType()]
        elif func_type == GPType.Dihedral:
            ret_type = ScalarType()
        elif func_type == GPType.FaceNormal:
            ret_type = [ScalarType(), ScalarType()]
        elif GPType.AdjacentVerticesV <= func_type <= GPType.AdjacentFacesF:
            if func_type == GPType.DiamondVerticesE:
                self.assert_expr(len(node.params) == 2 and param_list[0].la_type.is_scalar(),
                                 'Parameter should be scalar')
                ret_type = [ScalarType(is_int=True, index_type=True), ScalarType(is_int=True, index_type=True)]
            else:
                self.assert_expr(len(node.params) == 1 and param_list[0].la_type.is_scalar(), 'Parameter should be scalar')
                ret_type = SetType(size=1, int_list=[True], type_list=[ScalarType(is_int=True, index_type=True)])
        elif GPType.BuildVertexVector <= func_type <= GPType.BuildFaceVector:
            self.assert_expr(len(node.params) == 1 and param_list[0].la_type.is_set(), 'Parameter should be set')
            if GPType.BuildVertexVector == func_type:
                ret_type = VectorType(rows=self.symtable[self.builtin_module_dict[MESH_HELPER].v].rows, element_type=ScalarType(is_int=True, index_type=True))
            elif GPType.BuildFaceVector == func_type:
                ret_type = VectorType(rows=self.symtable[self.builtin_module_dict[MESH_HELPER].f].rows, element_type=ScalarType(is_int=True, index_type=True))
            else:
                ret_type = VectorType(element_type=ScalarType(is_int=True, index_type=True))
        elif func_type == GPType.GetVerticesE:
            ret_type = [ScalarType(is_int=True, index_type=True), ScalarType(is_int=True, index_type=True)]
        elif func_type == GPType.GetVerticesF:
            ret_type = [ScalarType(is_int=True, index_type=True), ScalarType(is_int=True, index_type=True), ScalarType(is_int=True, index_type=True)]
        elif func_type == GPType.GetEdgesF:
            ret_type = [ScalarType(is_int=True, index_type=True), ScalarType(is_int=True, index_type=True), ScalarType(is_int=True, index_type=True)]
        elif GPType.Star <= func_type <= GPType.Boundary:
            ret_type = SimplicialSetType()
        elif GPType.Vertices == func_type:
            ret_type = VertexSetType()
        elif GPType.Edges == func_type:
            ret_type = EdgeSetType()
        elif GPType.Faces == func_type:
            ret_type = FaceSetType()
        elif GPType.Tets == func_type:
            ret_type = TetSetType()
        elif GPType.Diamond == func_type:
            ret_type = SimplicialSetType()
        elif GPType.DiamondFacesE == func_type:
            ret_type = [ScalarType(is_int=True, index_type=True), ScalarType(is_int=True, index_type=True)]
        tri_node = GPFuncNode(param_list, func_type, node.name)
        node_info = NodeInfo(ret_type, symbols=symbols)
        tri_node.la_type = ret_type
        node_info.ir = tri_node
        return node_info

    def create_trig_node_info(self, func_type, param_info, power):
        symbols = param_info.symbols
        param = param_info.ir
        if power:
            self.assert_expr(param.la_type.is_scalar(), get_err_msg_info(param.parse_info, "Parameter must be scalar type for the power"))
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

    def walk_MinmaxFunc(self, node, **kwargs):
        t = MathFuncType.MathFuncMax
        if node.min:
            t = MathFuncType.MathFuncMin
        params_list = [self.walk(param, **kwargs) for param in node.params]
        remain = []
        if len(node.params) > 1:
            remain = params_list[1:]
        return self.create_math_node_info(t, params_list[0], remain)

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
        extra_list = []
        if node.extra:
            for extra in node.extra:
                extra_list.append(self.walk(extra, **kwargs))
        return self.create_math_node_info(MathFuncType.MathFuncDiag, self.walk(node.param, **kwargs), extra_list)

    def walk_VecFunc(self, node, **kwargs):
        return self.create_math_node_info(MathFuncType.MathFuncVec, self.walk(node.param, **kwargs))

    def walk_InverseVecFunc(self, node, **kwargs):
        node_info = self.create_math_node_info(MathFuncType.MathFuncInverseVec, self.walk(node.param, **kwargs), [self.walk(node.origin, **kwargs)])
        node_info.ir.separator = node.separator
        node_info.ir.func_name = node.name
        node_info.ir.sub = node.s
        return node_info
    
    def walk_SvdFunc(self, node, **kwargs):
        return self.create_math_node_info(MathFuncType.MathFuncSVD, self.walk(node.param, **kwargs))

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
    def walk_FacesOfEdgeFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.FacesOfEdge, node, **kwargs)
    def walk_DihedralFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.Dihedral, node, **kwargs)
    def walk_FaceNormalFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.FaceNormal, node, **kwargs)
    def walk_GetAdjacentVerticesVFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.AdjacentVerticesV, node, **kwargs)
    def walk_GetIncidentEdgesVFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.IncidentEdgesV, node, **kwargs)
    def walk_GetIncidentFacesVFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.IncidentFacesV, node, **kwargs)
    def walk_GetIncidentVerticesEFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.IncidentVerticesE, node, **kwargs)
    def walk_GetIncidentFacesEFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.IncidentFacesE, node, **kwargs)
    def walk_GetDiamondVerticesEFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.DiamondVerticesE, node, **kwargs)
    def walk_GetDiamondFacesEFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.DiamondFacesE, node, **kwargs)
    def walk_GetIncidentVerticesFFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.IncidentVerticesF, node, **kwargs)
    def walk_GetIncidentEdgesFFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.IncidentEdgesF, node, **kwargs)
    def walk_GetAdjacentFacesFFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.AdjacentFacesF, node, **kwargs)
    def walk_BuildVertexVectorFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.BuildVertexVector, node, **kwargs)
    def walk_BuildEdgeVectorFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.BuildEdgeVector, node, **kwargs)
    def walk_BuildFaceVectorFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.BuildFaceVector, node, **kwargs)
    def walk_GetVerticesEFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.GetVerticesE, node, **kwargs)
    def walk_GetVerticesFFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.GetVerticesF, node, **kwargs)
    def walk_GetEdgesFFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.GetEdgesF, node, **kwargs)
    ###################################################################
    def walk_StarFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.Star, node, **kwargs)
    def walk_ClosureFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.Closure, node, **kwargs)
    def walk_LinkFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.Link, node, **kwargs)
    def walk_BoundaryFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.Boundary, node, **kwargs)
    def walk_IsComplexFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.IsComplex, node, **kwargs)
    def walk_IsPureComplexFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.IsPureComplex, node, **kwargs)
    def walk_VerticesFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.Vertices, node, **kwargs)
    def walk_EdgesFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.Edges, node, **kwargs)
    def walk_FacesFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.Faces, node, **kwargs)
    def walk_TetsFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.Tets, node, **kwargs)
    def walk_DiamondFunc(self, node, **kwargs):
        return self.create_gp_node_info(GPType.Diamond, node, **kwargs)
    ###################################################################
    def walk_ElementConvertFunc(self, node, **kwargs):
        param_node_list = []
        param_type_list = []
        index_type = False
        # params inside parentheses
        for index in range(len(node.params)):
            c_node = self.walk(node.params[index], **kwargs).ir
            param_node_list.append(c_node)
            param_type_list.append(c_node.la_type)
            index_type = c_node.la_type.index_type
        ir_node = ElementConvertNode(params=param_node_list, parse_info=node.parseinfo, raw_text=node.text)
        ir_node.separators = node.separators
        if node.v:
            ir_node.to_type = EleConvertType.EleToVertex
            ir_node.la_type = VertexType(owner=param_type_list[0].owner)
            ir_node.name = node.v
            self.assert_expr(len(param_node_list) == 1 and param_type_list[0].is_integer_element(), get_err_msg_info(node.parseinfo,
                                                                                                     "Function error. Can't find function with current parameter types."))
        elif node.e:
            ir_node.to_type = EleConvertType.EleToEdge
            ir_node.la_type = EdgeType(owner=param_type_list[0].owner)
            ir_node.name = node.e
            self.assert_expr(len(param_node_list) == 1 and param_type_list[0].is_integer_element(), get_err_msg_info(node.parseinfo,
                                                                                                         "Function error. Can't find function with current parameter types."))
        elif node.f:
            ir_node.to_type = EleConvertType.EleToFace
            ir_node.la_type = FaceType(owner=param_type_list[0].owner)
            ir_node.name = node.f
            self.assert_expr(len(param_node_list) == 1 and param_type_list[0].is_integer_element(), get_err_msg_info(node.parseinfo,
                                                                                                         "Function error. Can't find function with current parameter types."))
        elif node.t:
            ir_node.to_type = EleConvertType.EleToTet
            ir_node.la_type = TetType(owner=param_type_list[0].owner)
            ir_node.name = node.t
            self.assert_expr(len(param_node_list) == 1 and param_type_list[0].is_integer_element(), get_err_msg_info(node.parseinfo,
                                                                                                         "Function error. Can't find function with current parameter types."))
        elif node.vs:
            ir_node.to_type = EleConvertType.EleToVertexSet
            ir_node.la_type = VertexSetType(owner=param_type_list[0].owner)
            ir_node.name = node.vs
            self.assert_expr(len(param_node_list) == 1 and param_type_list[0].is_set(), get_err_msg_info(node.parseinfo,
                                                                     "Function error. Can't find function with current parameter types."))
        elif node.es:
            ir_node.to_type = EleConvertType.EleToEdgeSet
            ir_node.la_type = EdgeSetType(owner=param_type_list[0].owner)
            ir_node.name = node.es
            self.assert_expr(len(param_node_list) == 1 and param_type_list[0].is_set(), get_err_msg_info(node.parseinfo,
                                                                     "Function error. Can't find function with current parameter types."))
        elif node.fs:
            ir_node.to_type = EleConvertType.EleToFaceSet
            ir_node.la_type = FaceSetType(owner=param_type_list[0].owner)
            ir_node.name = node.fs
            self.assert_expr(len(param_node_list) == 1 and param_type_list[0].is_set(), get_err_msg_info(node.parseinfo,
                                                                     "Function error. Can't find function with current parameter types."))
        elif node.ts:
            ir_node.to_type = EleConvertType.EleToTetSet
            ir_node.la_type = TetSetType(owner=param_type_list[0].owner)
            ir_node.name = node.ts
            self.assert_expr(len(param_node_list) == 1 and param_type_list[0].is_set(), get_err_msg_info(node.parseinfo,
                                                                     "Function error. Can't find function with current parameter types."))
        elif node.tu:
            ir_node.to_type = EleConvertType.EleToTuple
            ir_node.la_type = TupleType(type_list=param_type_list, index_type = index_type, owner=param_type_list[0].owner)
            ir_node.name = node.tu
        elif node.se:
            ir_node.to_type = EleConvertType.EleToSequence
            if param_type_list[0].is_sequence():
                # append new
                ir_node.la_type = SequenceType(size=add_syms(param_type_list[0].size, len(param_type_list)-1), element_type=param_type_list[0].element_type, owner=param_type_list[0].owner)
            elif param_type_list[0].is_set():
                # set to sequence
                dynamic = param_type_list[0].dynamic
                set_size = param_type_list[0].size if param_type_list[0].size else param_type_list[0].length
                ir_node.la_type = SequenceType(size=set_size, element_type=param_type_list[0].element_type, owner=param_type_list[0].owner, dynamic=dynamic)
            else:
                ir_node.la_type = SequenceType(size=len(param_type_list), element_type=param_type_list[0], owner=param_type_list[0].owner)
            ir_node.name = node.se
        elif node.s:
            ir_node.to_type = EleConvertType.EleToSimplicialSet
            ir_node.la_type = SimplicialSetType()
            ir_node.name = node.s
            self.assert_expr(len(param_node_list) == 3 and param_type_list[0].is_set() and param_type_list[1].is_set() and param_type_list[2].is_set(),
                             get_err_msg_info(node.parseinfo, "Function error. Can't find function with current parameter types."))
        return NodeInfo(ir_node.la_type, ir=ir_node)

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
        ir_node = AddNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, raw_text=node.text)
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
        ir_node = SubNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, raw_text=node.text)
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
        ir_node = MulNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, op=op_type, raw_text=node.text)
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
        ir_node = DivNode(left_info.ir, right_info.ir, parse_info=node.parseinfo, op=op_type, raw_text=node.text)
        ir_node.la_type = ret_type
        ret_info.ir = ir_node
        ret_info.content = '{}/{}'.format(left_info.content, right_info.content)
        return ret_info

    def walk_ArithFactor(self, node, **kwargs):
        node_info = None
        ir_node = FactorNode(parse_info=node.parseinfo, raw_text=node.text)
        if node.id0:
            content = node.id0.text
            def add_sym_info(sym, info):
                if sym not in self.dependency_dim_dict:
                    self.dependency_dim_dict[sym] = info
            if type(node.id0).__name__ == "IdentifierSubscript":
                self.dyn_dim = True
                self.assert_expr(len(node.id0.right) == 1 and node.id0.right[0] != '*', get_err_msg_info(node.id0.parseinfo, "Invalid dimension"))
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
                if self.pre_walk:
                    if len(id0) > 1:
                        self.multi_dim_list.append(id0)
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
        if isinstance(sum_value, int):
            return sum_value
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
            if left_type is None or right_type is None:
                error_msg = 'No type info.\n'
            else:
                error_msg = 'Dimension mismatch. Can\'t {} {} {} and {} {}. {}\n'.format(
                                                                                    get_op_desc(op),
                                                                                    get_type_desc(left_type),
                                                                                    get_parse_info_buffer(left_info.ir.parse_info).text[left_info.ir.parse_info.pos:left_info.ir.parse_info.endpos],
                                                                                    get_type_desc(right_type),
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
        self.assert_expr(left_type, get_err_msg())
        self.assert_expr(right_type, get_err_msg())
        if op == TypeInferenceEnum.INF_ADD or op == TypeInferenceEnum.INF_SUB:
            ret_type = copy.deepcopy(left_type)  # default type
            if left_type.is_scalar():
                self.assert_expr(right_type.is_scalar(), get_err_msg())
                ret_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
            elif left_type.is_matrix():
                self.assert_expr(right_type.is_matrix(), get_err_msg())
                # assert right_type.is_matrix() or right_type.is_vector(), error_msg
                if left_type.is_dynamic() or right_type.is_dynamic():
                    if left_type.is_dynamic() and right_type.is_dynamic():
                        if left_type.is_dynamic_row() and left_type.is_dynamic_col():
                            ret_type = copy.deepcopy(right_type)
                        elif left_type.is_dynamic_row():
                            if right_type.is_dynamic_row() and right_type.is_dynamic_col():
                                ret_type = copy.deepcopy(left_type)
                            elif right_type.is_dynamic_row():
                                self.assert_expr(is_same_expr(left_type.cols, right_type.cols), get_err_msg())
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
                                self.assert_expr(is_same_expr(left_type.rows, right_type.rows), get_err_msg())
                                ret_type = copy.deepcopy(left_type)
                    else:
                        if left_type.is_dynamic():
                            if left_type.is_dynamic_row() and left_type.is_dynamic_col():
                                ret_type = copy.deepcopy(right_type)
                            else:
                                if left_type.is_dynamic_row():
                                    self.assert_expr(is_same_expr(left_type.cols, right_type.cols), get_err_msg())
                                else:
                                    self.assert_expr(is_same_expr(left_type.rows, right_type.rows), get_err_msg())
                        else:
                            if right_type.is_dynamic_row() and right_type.is_dynamic_col():
                                ret_type = copy.deepcopy(left_type)
                            else:
                                if right_type.is_dynamic_row():
                                    self.assert_expr(is_same_expr(left_type.cols, right_type.cols), get_err_msg())
                                else:
                                    self.assert_expr(is_same_expr(left_type.rows, right_type.rows), get_err_msg())
                else:
                    # static
                    self.assert_expr(is_same_expr(left_type.rows, right_type.rows) and is_same_expr(left_type.cols, right_type.cols), get_err_msg())
                    if left_type.sparse and right_type.sparse:
                        ret_type.sparse = True
                    else:
                        ret_type.sparse = False
                ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
            elif left_type.is_vector():
                self.assert_expr(right_type.is_vector(), get_err_msg())
                self.assert_expr(is_same_expr(left_type.rows, right_type.rows), get_err_msg())
                # assert right_type.is_matrix() or right_type.is_vector(), error_msg
                # assert left_type.rows == right_type.rows and left_type.cols == right_type.cols, error_msg
                if right_type.is_matrix():
                    ret_type = copy.deepcopy(right_type)
                ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
            elif left_type.is_set():
                self.assert_expr(right_type.is_set() and right_type.cur_type==left_type.cur_type, get_err_msg())
                ret_type = copy.deepcopy(left_type)
            else:
                # sequence et al.
                self.assert_expr(left_type.var_type == right_type.var_type, get_err_msg())
            # index type checking
            if left_type.index_type or right_type.index_type:
                self.assert_expr(left_type.is_integer_element() and right_type.is_integer_element(), get_err_msg("Operand must be integer."))
                ret_type.index_type = True
                if op == TypeInferenceEnum.INF_ADD:
                    self.assert_expr(not (left_type.index_type and right_type.index_type), get_err_msg("They are both index types."))
                else:
                    if left_type.index_type and right_type.index_type:
                        ret_type.index_type = False
        elif op == TypeInferenceEnum.INF_MUL:
            self.assert_expr(left_type.var_type != VarTypeEnum.SEQUENCE and right_type.var_type != VarTypeEnum.SEQUENCE, 'error: sequence can not be operated')
            self.assert_expr(not left_type.index_type and not right_type.index_type, get_err_msg())
            if left_type.is_dynamic() or right_type.is_dynamic():
                if left_type.is_dynamic() and right_type.is_dynamic():
                    if left_type.is_dynamic_row() and left_type.is_dynamic_col():
                        if right_type.is_dynamic_row() and right_type.is_dynamic_col():
                            ret_type = copy.deepcopy(right_type)
                        elif right_type.is_dynamic_row():
                            ret_type = copy.deepcopy(right_type)
                        else:
                            ret_type = copy.deepcopy(left_type)
                    elif left_type.is_dynamic_row():
                        if right_type.is_dynamic_row() and right_type.is_dynamic_col():
                            ret_type = copy.deepcopy(right_type)
                        elif right_type.is_dynamic_row(): 
                            ret_type = copy.deepcopy(right_type)
                        elif right_type.is_dynamic_col():
                            ret_type = copy.deepcopy(left_type) 
                            ret_type.set_dynamic_type(DynamicTypeEnum.DYN_ROW | DynamicTypeEnum.DYN_COL)  # change to static type
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
                        ret_type = copy.deepcopy(left_type)
                        if left_type.is_dynamic_row() and left_type.is_dynamic_col():
                            ret_type.cols = right_type.cols
                            ret_type.set_dynamic_type(DynamicTypeEnum.DYN_ROW)
                        elif left_type.is_dynamic_row():
                            self.assert_expr(is_same_expr(left_type.cols, right_type.rows), get_err_msg())
                        else:
                            ret_type.cols = right_type.cols
                            ret_type.set_dynamic_type(DynamicTypeEnum.DYN_INVALID)
                    else:
                        ret_type = copy.deepcopy(right_type)
                        ret_type.rows = left_type.rows
                        if right_type.is_dynamic_row() and right_type.is_dynamic_col():
                            ret_type.set_dynamic_type(DynamicTypeEnum.DYN_COL)
                        elif right_type.is_dynamic_row():
                            ret_type.set_dynamic_type(DynamicTypeEnum.DYN_INVALID)
                        else:
                            self.assert_expr(is_same_expr(left_type.cols, right_type.rows), get_err_msg())
            else:
                # static
                if left_type.is_scalar():
                    ret_type = copy.deepcopy(right_type)
                    ret_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
                elif left_type.is_matrix():
                    if right_type.is_scalar():
                        ret_type = copy.deepcopy(left_type)
                    elif right_type.is_matrix():
                        self.assert_expr(is_same_expr(left_type.cols, right_type.rows), get_err_msg())
                        ret_type = MatrixType(rows=left_type.rows, cols=right_type.cols)
                        if left_type.sparse and right_type.sparse:
                            ret_type.sparse = True
                            # check boundary matrix operations
                            if left_type.owner and right_type.owner:
                                self.assert_expr(left_type.owner == right_type.owner, get_err_msg("Matrices are not from the same mesh"))
                                ret_type.owner = left_type.owner
                        # if left_type.rows == 1 and right_type.cols == 1:
                        #     ret_type = ScalarType()
                        ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
                        if ret_type.rows == 1 and ret_type.cols == 1:
                            #
                            ret_type = ScalarType()
                            need_cast = True
                            ret_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
                    elif right_type.is_vector():
                        self.assert_expr(is_same_expr(left_type.cols, right_type.rows), get_err_msg())
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
                        self.assert_expr(1 == right_type.rows, get_err_msg())
                        ret_type = MatrixType(rows=left_type.rows, cols=right_type.cols)
                        new_node = ToMatrixNode(parse_info=left_info.ir.parse_info, item=left_info.ir)
                        new_node.la_type = MatrixType(rows=left_type.rows, cols=1)
                        left_info.ir = new_node
                        ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
                    elif right_type.is_vector():
                        self.assert_expr(is_same_expr(left_type.cols, right_type.rows), get_err_msg())
                        ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
        elif op == TypeInferenceEnum.INF_DIV:
            # assert left_type.is_scalar() and right_type.is_scalar(), error_msg
            self.assert_expr(left_type.is_scalar() or left_type.is_vector() or left_type.is_matrix(), get_err_msg())
            self.assert_expr(right_type.is_scalar(), get_err_msg())
            self.assert_expr(not left_type.index_type and not right_type.index_type, get_err_msg())
            ret_type = copy.deepcopy(left_type)
            if left_type.is_scalar():
                ret_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
            else:
                ret_type.element_type.is_int = left_type.is_integer_element() and right_type.is_integer_element()
        elif op == TypeInferenceEnum.INF_MATRIX_ROW:
            # assert left_type.var_type == right_type.var_type
            ret_type = copy.deepcopy(left_type)
        if not left_type.is_scalar() or not right_type.is_scalar():
            if left_type.is_integer_element() and not right_type.is_integer_element():
                new_node = ToDoubleValueNode(parse_info=left_info.ir.parse_info, item=left_info.ir)
                new_node.la_type = copy.deepcopy(left_type)
                if new_node.la_type.element_type:
                    new_node.la_type.element_type.is_int = True
                else:
                    new_node.la_type.is_int = True
                left_info.ir = new_node
            else:
                if not left_type.is_integer_element() and right_type.is_integer_element():
                    new_node = ToDoubleValueNode(parse_info=right_info.ir.parse_info, item=right_info.ir)
                    new_node.la_type = copy.deepcopy(right_type)
                    if new_node.la_type.element_type:
                        new_node.la_type.element_type.is_int = True
                    else:
                        new_node.la_type.is_int = True
                    right_info.ir = new_node
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

    def is_main_scope(self):
        return self.scope_list[-1] == 'global'

    def get_cur_scope(self):
        return self.scope_list[-1]
    def get_upper_scope(self):
        # upper layer scope
        return self.scope_list[-2]

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
            self.assert_expr(len(arr[1]) == 1, get_err_msg_info(ir_node.parse_info, "Parameter {} can't use multiple subscripts".format(arr[0])))
            val = arr[1][0]  # subscript
            self.assert_expr(not val.isnumeric(), get_err_msg_info(id_node.parse_info, "Parameter {} can't have constant subscript".format(arr[0])))
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
            self.assert_expr(arr[0] not in self.get_cur_param_data().symtable, get_err_msg_info(id_node.parse_info, "Parameter {} has been defined.".format(arr[0])))
            if id_type.is_vector():
                if id_type.is_dynamic_row():
                    if id_node.id1.is_node(IRNodeType.SeqDimIndex):
                        self.assert_expr(id_node.id1.main_index.get_name() == val, get_err_msg_info(id_node.id1.parse_info, "Dimension {} has different subscript".format(id_node.id1.main.get_name())))
                        row_seq_type = SequenceType(size=new_var_name, element_type=ScalarType(is_int=True), symbol=id_node.id1.get_main_id())
                        if id_node.id1.get_main_id() in self.get_cur_param_data().symtable:
                            self.assert_expr(self.get_cur_param_data().symtable[id_node.id1.get_main_id()].is_same_type(row_seq_type), get_err_msg_info(id_node.id1.parse_info,
                                                                                     "{} has already been defined as different type".format(
                                                                                         id_node.id1.get_main_id())))
                        else:
                            self.get_cur_param_data().symtable[id_node.id1.get_main_id()] = row_seq_type
                            self.get_cur_param_data().dim_seq_set.add(id_node.id1.get_main_id())
            elif id_type.is_matrix():
                if id_type.is_dynamic_row():
                    if id_node.id1.is_node(IRNodeType.SeqDimIndex):
                        self.assert_expr(id_node.id1.main_index.get_name() == val, get_err_msg_info(id_node.id1.parse_info, "Dimension {} has different subscript".format(id_node.id1.main.get_name())))
                        row_seq_type = SequenceType(size=new_var_name, element_type=ScalarType(is_int=True),
                                                    symbol=id_node.id1.get_main_id())
                        if id_node.id1.get_main_id() in self.get_cur_param_data().symtable:
                            self.assert_expr(self.get_cur_param_data().symtable[id_node.id1.get_main_id()].is_same_type(
                                row_seq_type), get_err_msg_info(id_node.id1.parse_info,
                                                                     "{} has already been defined as different type".format(
                                                                         id_node.id1.get_main_id())))
                        else:
                            self.get_cur_param_data().symtable[id_node.id1.get_main_id()] = row_seq_type
                            self.get_cur_param_data().dim_seq_set.add(id_node.id1.get_main_id())
                if id_type.is_dynamic_col():
                    if id_node.id2.is_node(IRNodeType.SeqDimIndex):
                        self.assert_expr(id_node.id1.main_index.get_name() == val, get_err_msg_info(id_node.id2.parse_info, "Dimension {} has different subscript".format(id_node.id2.main.get_name())))
                        col_seq_type = SequenceType(size=new_var_name, element_type=ScalarType(is_int=True),
                                                    symbol=id_node.id1.get_main_id())
                        if id_node.id2.get_main_id() in self.get_cur_param_data().symtable:
                            self.assert_expr(self.get_cur_param_data().symtable[id_node.id2.get_main_id()].is_same_type(
                                col_seq_type), get_err_msg_info(id_node.id2.parse_info,
                                                                     "{} has already been defined as different type".format(
                                                                         id_node.id2.get_main_id())))
                        else:
                            self.get_cur_param_data().symtable[id_node.id2.get_main_id()] = col_seq_type
                            self.get_cur_param_data().dim_seq_set.add(id_node.id2.get_main_id())
            self.get_cur_param_data().symtable[arr[0]] = SequenceType(size=new_var_name, element_type=id_type, desc=id_type.desc, symbol=arr[0])
        else:
            id_type.symbol = identifier
            if id_type.is_mesh():
                # mesh type needs to be initialized when adding to symtable
                id_type = copy.deepcopy(id_type)
                id_type.init_dims({VI_SIZE: self.generate_var_name('dimv'),
                        EI_SIZE: self.generate_var_name('dime'),
                        FI_SIZE: self.generate_var_name('dimf'),
                        TI_SIZE: self.generate_var_name('dimt')})
                id_type.owner = identifier
                self.mesh_dict[identifier] = MeshData(la_type=id_type)
                self.used_params.append(identifier)
            self.add_sym_type(identifier, id_type, get_err_msg_info(id_node.parse_info, "Parameter {} has been defined.".format(identifier)))
            # self.check_sym_existence(identifier, get_err_msg_info(id_node.parse_info, "Parameter {} has been defined.".format(identifier)), False)
            # self.get_cur_param_data().symtable[identifier] = id_type
