import copy

from tatsu.exceptions import (
    FailedCut,
    FailedParse
)
from .de_codegen import *
from .de_type_walker import *
from ..de_companion.de_helper import *
from .de_ir_mutator import *
from .de_ir_visitor import *
from ..la_tools.la_msg import *
from ..la_tools.config_manager import *
from ..la_tools.la_helper import *
from ..la_tools.parser_manager import ParserManager
from ..la_tools.module_manager import CacheModuleManager
from ..la_tools.babyheartdown import heartdown2lines
import subprocess
import threading
import regex as re
from ..de_grammar import *

## We don't need wx to run in command-line mode. This makes it optional.
try:
    import wx
except ImportError:
    class wx(object): pass
    wx.CallAfter = lambda o, *x, **y: None

import sys
import traceback
import os.path
from pathlib import Path
import tempfile
import io

_id_pattern = re.compile("[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*")
_backtick_pattern = re.compile("`[^`]*`")
_codegen_dict = {}
_codegen = None
_builtin_module_path = Path(__file__).parent.parent / 'mesh'    # default module path, fixed
_module_path = Path(__file__).parent.parent / 'mesh'            # default module path, can be updated as the same directory of the source file

class VarData(object):
    def __init__(self, params=None, lhs=None, ret=None):
        super().__init__()
        self.params = params
        self.lhs = lhs
        self.ret = ret


def get_codegen():
    global _codegen
    if _codegen is None:
        _codegen = DCodeGen()
    return _codegen


def walk_model(type_walker, node_info):
    gen = get_codegen()
    gen.init_type(type_walker)
    code_frame = gen.visit_code(node_info)
    return code_frame.get_code()

if getattr(sys, 'frozen', False):
    # We are running in a bundle.
    GRAMMAR_DIR = Path(sys._MEIPASS) / 'la_grammar'
else:
    # We are running in a normal Python environment.
    GRAMMAR_DIR = Path(__file__).resolve().parent.parent / 'la_grammar'
# print( 'GRAMMAR_DIR:', GRAMMAR_DIR )

_grammar_content = None  # content in file
_default_key = 'de_default'
_parser_manager = ParserManager.getInstance(GRAMMAR_DIR)


def get_compiled_parser(grammar, keys='de_init', extra_dict={}):
    # log_la("keys:" + keys)
    return _parser_manager.get_parser(keys, grammar, extra_dict)

_type_walker = None
_ir_mutator = None


def get_type_walker():
    global _type_walker
    if _type_walker:
        _type_walker.reset()
    else:
        _type_walker = DTypeWalker()
    return _type_walker


def get_ir_mutator(type_walker, func_name=CLASS_NAME):
    global _ir_mutator
    if not _ir_mutator:
        _ir_mutator = DIRMutator()
    _ir_mutator.init_type(type_walker, func_name)
    return _ir_mutator


def log_la(content):
    LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT).debug(content)

def get_start_node(model):
    # type walker
    type_walker = get_type_walker()
    start_node = type_walker.walk(model, pre_walk=True)
    return type_walker, start_node

def get_new_parser(start_node, current_content, type_walker):
    """
    Get the new parser based on information from start_node
    :param start_node:
    :param current_content:
    :param parser_type:
    :return: new parser and others
    """
    extra_dict = {}
    parse_key = _default_key
    multi_list = []
    # deal with packages
    dependent_modules = []
    builtin_func_rdict = {}
    if len(start_node.directives) > 0:
        dependent_modules = start_node.get_module_directives()
        # include directives (builtin modules)
        package_name_dict = start_node.get_package_dict()
        package_rdict = start_node.get_package_rdict()
        package_name_list = []
        key_names = []    # imported builtin function names
        for package in package_name_dict:
            name_list = package_name_dict[package]
            r_dict = package_rdict[package]
            if 'e' in name_list:
                name_list.remove('e')
                parse_key += 'e;'
                package_name_list.append('e')
            for name in name_list:
                if not _id_pattern.fullmatch(r_dict[name]):
                    # multi-letter imported syms
                    multi_list.append(r_dict[name])
                if package == MESH_HELPER:
                    # check property, not func
                    # if name in PACKAGES_SYM_DICT[package]:
                    continue
                # add func names only
                if name == 'vec⁻¹':
                    key_names.append("inversevec_func") # add correct imported syms
                else:
                    key_names.append("{}_func".format(name)) # add correct imported syms
            for key, value in r_dict.items():
                if key != value:
                    builtin_func_rdict[key] = value
        package_name_list += key_names
        if len(key_names) > 0:
            # add new rules
            parse_key += ';'.join(key_names)
        extra_dict['pkg'] = package_name_list
        extra_dict['rename'] = builtin_func_rdict
    # get new parser
    # parser = get_compiled_parser(current_content, parse_key, extra_dict)
    # model = parser.parse(content, parseinfo=True)
    for parameter in type_walker.parameters:
        if parameter is None:
            continue
        if _id_pattern.fullmatch(parameter):
            continue  # valid single identifier
        if len(parameter) > 1 and '_' not in parameter and '`' not in parameter:
            multi_list.append(parameter)
    # multi_list += type_walker.multi_lhs_list
    for multi_lhs in type_walker.multi_lhs_list:
        if _id_pattern.fullmatch(multi_lhs):
            continue  # valid single identifier
        multi_list.append(multi_lhs)
    #
    for dim in type_walker.multi_dim_list:
        if _id_pattern.fullmatch(dim):
            continue
        multi_list.append(dim)
    # dependent modules
    existed_syms_dict = {}
    module_list = []
    module_param_list = []
    module_sym_list = []
    # deal with function
    func_dict = type_walker.get_func_symbols()
    #
    for name, la_type in existed_syms_dict.items():
        if la_type.is_function():
            func_dict[name] = "importFP;" + name
    for par in start_node.get_module_pars_list():
        if _id_pattern.fullmatch(par):
            continue  # valid single identifier
        multi_list.append(par)
    if len(func_dict.keys()) > 0:
        key_list = list(func_dict.keys())
        extra_list = []
        for key in key_list:
            if '`' not in key:
                extra_list.append('`{}`'.format(key))
        key_list += extra_list
        key_list = [re.escape(item).replace('/', '\\/') for item in key_list]
        key_list = sorted(key_list, key=len, reverse=True)
        func_rule = "/" + "/|/".join(key_list) + "/"
        extra_dict['funcs'] = key_list
        log_la("func_rule:" + func_rule)
        for f_name in key_list:
            if _id_pattern.fullmatch(f_name):
                continue  # valid single func name
            multi_list.append(f_name)
        parse_key += "func symbol:{}, func sig:{}".format(','.join(func_dict.keys()), ";".join(func_dict.values()))
    # not add backticks
    new_list = []
    for key in multi_list:
        if '`' not in key:
            new_list.append(key)
    multi_list = list(set(new_list))
    if len(multi_list) > 0:
        multi_list = [re.escape(item).replace('/', '\\/') for item in multi_list]
        multi_list = sorted(multi_list, key=len, reverse=True)
        extra_dict['ids'] = multi_list
        keys_rule = "/" + "/|/".join(multi_list) + "/"
        log_la("keys_rule:" + keys_rule)
        parse_key += "keys_rule:{};".format(keys_rule)
    # get new parser
    record("Get new parser")
    parser = get_compiled_parser(current_content, parse_key, extra_dict)
    return parser, existed_syms_dict, module_list, dependent_modules, module_param_list, module_sym_list


def parse_ir_node(content, model, start_node=None, type_walker=None, class_only=CLASS_ONLY):
    record("parse_ir_node")
    global _grammar_content
    current_content = _grammar_content
    if start_node is None:
        record("parse_ir_node, start_node")
        # type walker
        type_walker = get_type_walker()
        type_walker.class_only = class_only
        start_node = type_walker.walk(model, pre_walk=True)
    # get new parser
    parser, existed_syms_dict, module_list, dependent_modules, module_param_list, module_sym_list = get_new_parser(start_node, current_content, type_walker)
    record("Second Parsing, before")
    model = parser.parse(content, parseinfo=True)
    record("Second type walker, before")
    # second parsing
    type_walker.reset_state(content)  # reset
    type_walker.symtable.update(existed_syms_dict)
    type_walker.class_only = class_only
    # add signatures before parsing
    if len(dependent_modules) > 0:
        # check parameters type for imported custom modules
        for cur_index in range(len(module_list)):
            module = module_list[cur_index]
            type_walker.func_sig_dict.update(module.func_sig_dict)
            for s_index in range(len(module.syms)):
                sym = module.syms[s_index]
                r_sym = module.r_syms[s_index]
                # handle func onverloading
                if existed_syms_dict[r_sym].is_overloaded():
                    if r_sym != sym:
                        # regenerat
                        existed_syms_dict[r_sym].fname_list = []
                        for c_index in range(len(existed_syms_dict[r_sym].func_list)):
                            sig = get_func_signature(r_sym, existed_syms_dict[r_sym].func_list[c_index])
                            n_name = type_walker.generate_var_name(r_sym)
                            type_walker.func_sig_dict[sig] = n_name
                            existed_syms_dict[r_sym].fname_list.append(n_name)
    start_node = type_walker.walk(model)
    record("Second type walker, after")
    # if type_walker.need_mutator:
    #     start_node = get_ir_mutator(type_walker).visit_code(start_node)
    start_node.module_list = module_list
    start_node.module_syms = existed_syms_dict
    if len(dependent_modules) > 0:
        # check parameters type for imported custom modules
        for cur_index in range(len(dependent_modules)):
            module = dependent_modules[cur_index]
            params = module_param_list[cur_index]
            cur_symtable = module_sym_list[cur_index]
            for param_index in range(len(module.params)):
                par = module.params[param_index]
                assert par.get_name() in type_walker.symtable, get_err_msg_info(par.parse_info, "Symbol {} is not defined".format(par.get_name()))
                assert type_walker.symtable[par.get_name()].is_same_type(cur_symtable[params[param_index]]), \
                    get_err_msg_info(par.parse_info, "Parameter {} does not match the type".format(par.get_name()))
    type_walker.class_only = class_only
    return type_walker, start_node

def parse_de_content(content):
    def get_parse_result(content):
        parser = get_compiled_parser('', 'de_init')
        # parse de
        model = parser.parse(content, parseinfo=True)
        # type walker
        type_walker, start_node = parse_ir_node(content, model)
        #
        res = walk_model(type_walker, start_node)
        return res, 0
    try:
        result = get_parse_result(content)
    except FailedParse as e:
        tex = LaMsg.getInstance().get_parse_error(e)
        log_la("FailedParse:" + str(e))
        result = (tex, 1)
    except FailedCut as e:
        tex = "FailedCut: {}".format(str(e))
        result = (tex, 1)
    except AssertionError as e:
        tex = "{}".format(e.args[0])
        result = (tex, 1)
    except Exception as e:
        tex = "{}: {}".format(type(e).__name__, str(e))
        result = (tex, 1)
    except:
        tex = str(sys.exc_info()[0])
        result = (tex, 1)
    finally:
        if result[1] != 0:
            print(result[0])
    return result


def get_file_name(path_name):
    return Path(path_name).stem
