import copy

from tatsu.exceptions import (
    FailedCut,
    FailedParse
)
from .codegen import *
from .codegen_numpy import CodeGenNumpy
from .codegen_eigen import CodeGenEigen
from .codegen_latex import CodeGenLatex
from .codegen_mathjax import CodeGenMathjax
from .codegen_macromathjax import CodeGenMacroMathjax
from .codegen_mathml import CodeGenMathML
from .codegen_matlab import CodeGenMatlab
from .type_walker import *
from ..de_companion.de_helper import *
from .ir_mutator import *
from .ir_visitor import *
from ..la_tools.la_msg import *
from ..la_tools.config_manager import *
from ..la_tools.la_helper import *
from ..la_tools.parser_manager import ParserManager
from ..la_tools.module_manager import CacheModuleManager
from ..la_tools.babyheartdown import heartdown2lines
import subprocess
import threading
import regex as re
from ..la_grammar import *

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
_builtin_module_path = Path(__file__).parent.parent / 'mesh'    # default module path, fixed
_module_path = Path(__file__).parent.parent / 'mesh'            # default module path, can be updated as the same directory of the source file

class VarData(object):
    def __init__(self, params=None, lhs=None, ret=None):
        super().__init__()
        self.params = params
        self.lhs = lhs
        self.ret = ret


def get_codegen(parser_type):
    if parser_type not in _codegen_dict:
        if parser_type == ParserTypeEnum.LATEX:
            gen = CodeGenLatex()
        elif parser_type == ParserTypeEnum.NUMPY:
            gen = CodeGenNumpy()
        elif parser_type == ParserTypeEnum.EIGEN:
            gen = CodeGenEigen()
        elif parser_type == ParserTypeEnum.MATHJAX:
            gen = CodeGenMathjax()
        elif parser_type == ParserTypeEnum.MACROMATHJAX:
            gen = CodeGenMacroMathjax()
        elif parser_type == ParserTypeEnum.MATHML:
            gen = CodeGenMathML()
        elif parser_type == ParserTypeEnum.MATLAB:
            gen = CodeGenMatlab()
        _codegen_dict[parser_type] = gen
    return _codegen_dict[parser_type]


def walk_model(parser_type, type_walker, node_info, func_name=None, struct=False, class_only=CLASS_ONLY):
    gen = get_codegen(parser_type)
    #
    gen.init_type(type_walker, func_name)
    # gen.class_only = class_only
    code_frame = gen.visit_code(node_info)
    if parser_type != ParserTypeEnum.LATEX:  # print once
        gen.print_symbols()
    if struct:
        return code_frame
    return code_frame.get_code()

def walk_model_frame(parser_type, type_walker, node_info, func_name=None):
    gen = get_codegen(parser_type)
    #
    gen.init_type(type_walker, func_name)
    code_frame = gen.visit_code(node_info)
    if parser_type != ParserTypeEnum.LATEX:  # print once
        gen.print_symbols()
    return code_frame

if getattr(sys, 'frozen', False):
    # We are running in a bundle.
    GRAMMAR_DIR = Path(sys._MEIPASS) / 'la_grammar'
else:
    # We are running in a normal Python environment.
    GRAMMAR_DIR = Path(__file__).resolve().parent.parent / 'la_grammar'
# print( 'GRAMMAR_DIR:', GRAMMAR_DIR )

_grammar_content = None  # content in file
_default_key = 'default'
_parser_manager = ParserManager.getInstance(GRAMMAR_DIR)


def get_compiled_parser(grammar, keys='init', extra_dict={}):
    # log_la("keys:" + keys)
    return _parser_manager.get_parser(keys, grammar, extra_dict)


_type_walker = None
_ir_mutator = None


def get_type_walker():
    global _type_walker
    if _type_walker:
        _type_walker.reset()
    else:
        _type_walker = TypeWalker()
    return _type_walker


def get_ir_mutator(type_walker, func_name=CLASS_NAME):
    global _ir_mutator
    if not _ir_mutator:
        _ir_mutator = IRMutator()
    _ir_mutator.init_type(type_walker, func_name)
    return _ir_mutator


def log_la(content):
    LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT).debug(content)


def create_parser():
    parser = None
    try:
        # file = open(GRAMMAR_DIR/'LA.ebnf')
        # simplified_file = open(GRAMMAR_DIR/'simplified_grammar.ebnf')
        # grammar = file.read()
        grammar = LA
        # simplified_grammar = simplified_file.read()
        simplified_grammar = SIMPLIFIED
        global _grammar_content
        _grammar_content = grammar
        # get init parser
        parser = get_compiled_parser(simplified_grammar)
        # file.close()
        # simplified_file.close()
        # get default parser
        get_compiled_parser(_grammar_content, _default_key)
    except IOError:
        print("IO Error!")
    return parser


def get_default_parser():
    return create_parser()


def generate_latex_code(type_walker, node_info, frame):
    tex_content = ''
    show_pdf = None

    def get_pdf(tmpdir):
        tex_content = walk_model(ParserTypeEnum.LATEX, type_walker, node_info)
        template_name = str(Path(tmpdir) / "la")
        tex_file_name = "{}.tex".format(template_name)
        tex_file = open(tex_file_name, 'w')
        tex_file.write(tex_content)
        tex_file.close()
        ## xelatex places its output in the current working directory, not next to the input file.
        ## We need to pass subprocess.run() the directory where we created the tex file.
        ## If we are running in a bundle, we don't have the PATH available. Assume MacTex.
        env = copy.copy(os.environ)
        env['PATH'] = ':'.join(
            ['/Library/TeX/texbin', '/usr/texbin', '/usr/local/bin', '/opt/local/bin', '/usr/bin', '/bin',
             os.environ['PATH']])
        ret = subprocess.run(["xelatex", "-interaction=nonstopmode", tex_file_name], capture_output=True, cwd=tmpdir,
                             env=env)
        if ret.returncode == 0:
            ## If we are running in a bundle, we don't have the PATH available. Assume MacTex.
            ## But then we may not have ghostscript `gs` available, either.
            ret = subprocess.run(
                ["pdfcrop", "--margins", "30", "{}.pdf".format(template_name), "{}.pdf".format(template_name)],
                capture_output=True, cwd=tmpdir, env=env)
            # If xelatex worked, we have a PDF, even if pdfcrop failed.
            # if ret.returncode == 0:
            show_pdf = io.BytesIO(open("{}.pdf".format(template_name), 'rb').read())
        else:
            show_pdf = None
        return tex_content, show_pdf

    ## Let's create a temporary directory that cleans itself up
    ## and avoids a race condition other running instances of iheartla.
    ## We will pass UpdateTexPanel a file-like object containing the bytes of the PDF.
    with tempfile.TemporaryDirectory() as tmpdir:
        if DEBUG_MODE:
            tex_content, show_pdf = get_pdf(tmpdir)
            wx.CallAfter(frame.UpdateTexPanel, tex_content, show_pdf)
        else:
            try:
                tex_content, show_pdf = get_pdf(tmpdir)
            except subprocess.SubprocessError as e:
                tex_content = str(e)
            except FailedParse as e:
                tex_content = str(e)
            except FailedCut as e:
                tex_content = str(e)
            except Exception as e:
                tex_content = str(e)
                exc_info = sys.exc_info()
                traceback.print_exc()
                tex_content = str(exc_info[2])
            finally:
                wx.CallAfter(frame.UpdateTexPanel, tex_content, show_pdf)

def get_start_node(model):
    # type walker
    type_walker = get_type_walker()
    start_node = type_walker.walk(model, pre_walk=True)
    return type_walker, start_node

def get_compiled_module(module_name, parser_type, class_only):
    # compile module content
    # Init parser
    module_file = "{}/{}.hlang".format(_builtin_module_path, module_name)
    if not Path(module_file).exists():
        # if not in builtin directory, then find it from the input directory
        module_file = "{}/{}.hlang".format(_module_path, module_name)
    cur_time = os.path.getmtime(Path(module_file))
    tmp_type_walker = None
    if CACHE_MODULE:
        # check 
        tmp_type_walker, pre_frame = CacheModuleManager.getInstance().get_compiled_module(module_name, ParserTypeDict[parser_type], cur_time)
    if tmp_type_walker is None:
        print("Not found, regenerate type walker")
        # regenerate
        module_content = read_from_file(module_file)
        parser = get_default_parser()
        new_model = parser.parse(module_content, parseinfo=True)
        tmp_type_walker, tmp_start_node = parse_ir_node(module_content, new_model, parser_type, class_only=class_only)
        pre_frame = walk_model_frame(parser_type, tmp_type_walker, tmp_start_node, module_name)
        if CACHE_MODULE:
            # save
            CacheModuleManager.getInstance().save_compiled_module(tmp_type_walker, pre_frame, module_name, ParserTypeDict[parser_type], cur_time)
    else:
        print("Saved module found: {}".format(module_name))
    return tmp_type_walker, pre_frame

def get_new_parser(start_node, current_content, type_walker, skipped_module=False, parser_type=ParserTypeEnum.EIGEN, class_only=CLASS_ONLY):
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
                if DEBUG_PARSER:
                    current_content = current_content.replace("pi;", "pi|e;")
                    current_content = current_content.replace("BUILTIN_KEYWORDS;", "BUILTIN_KEYWORDS|e;")
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
            if DEBUG_PARSER:
                keyword_index = current_content.find('predefined_built_operators;')
                current_content = current_content[:keyword_index] + '|'.join(key_names) + '|' + current_content[
                                                                                                keyword_index:]
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
    if len(dependent_modules) > 0 and not skipped_module:
        record("dependent_modules")
        for module in dependent_modules:
            try:
                parse_info = module.module.parse_info
                err_msg = "Invalid module:{}".format(module.module.get_name())
                # get compiled content
                tmp_type_walker, pre_frame = get_compiled_module(module.module.get_name(), parser_type, class_only)
                name_list = []
                r_name_list = []
                par_list = []
                if len(tmp_type_walker.parameters) != len(module.params):
                    err_msg = "Parameters doesn't match, need {} while given {}".format(len(tmp_type_walker.parameters),
                                                                                        len(module.params))
                    raise
                par_mapping_dict = {}
                for cur_index in range(len(module.params)):
                    par = module.params[cur_index]
                    par_list.append(par.get_name())
                    par_mapping_dict[tmp_type_walker.parameters[cur_index]] = par.get_name()
                # check whether the dimensions or other properties (mesh owner) depend on parameters
                replace_sym_dims(tmp_type_walker.symtable, par_mapping_dict)
                sig_dict = {}
                # check import all
                if module.import_all:
                    sym_names = list(tmp_type_walker.symtable.keys())
                    module.names = [IdNode(name) for name in sym_names]
                    for name in sym_names:
                        module.r_dict[name] = name
                #
                for sym in module.names:
                    if sym.get_name() not in tmp_type_walker.symtable:
                        parse_info = sym.parse_info
                        err_msg = "Symbol {} doesn't exist in module {}".format(sym.get_name(),
                                                                                module.module.get_name())
                        raise
                    r_sym = module.r_dict[sym.get_name()]
                    existed_syms_dict[r_sym] = copy.deepcopy(tmp_type_walker.symtable[sym.get_name()])
                    name_list.append(sym.get_name())
                    r_name_list.append(r_sym)
                    # handle func onverloading
                    if existed_syms_dict[r_sym].is_overloaded():
                        existed_syms_dict[r_sym].pre_fname_list = existed_syms_dict[r_sym].fname_list
                        if r_sym == sym.get_name():
                            # at this step, only set unchanged func names
                            sig_dict.update(tmp_type_walker.get_sym_sig_dict([sym.get_name()]))
                module_list.append(
                    CodeModule(frame=pre_frame, name=module.module.get_name(), syms=name_list, r_syms=r_name_list,
                               params=par_list, func_sig_dict=sig_dict))
                module_param_list.append(copy.deepcopy(tmp_type_walker.parameters))
                module_sym_list.append(copy.deepcopy(tmp_type_walker.symtable))
            except:
                assert False, get_err_msg_info(parse_info, err_msg)
    #
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
        if DEBUG_PARSER:
            current_content = current_content.replace("func_id='!!!';", "func_id={};".format(func_rule))
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
        if DEBUG_PARSER:
            current_content = current_content.replace("= !KEYWORDS(",
                                                      "= const:({}) | (!(KEYWORDS | {} )".format(keys_rule, keys_rule))
    # get new parser
    record("Get new parser")
    parser = get_compiled_parser(current_content, parse_key, extra_dict)
    return parser, existed_syms_dict, module_list, dependent_modules, module_param_list, module_sym_list


def parse_ir_node(content, model, parser_type=ParserTypeEnum.EIGEN, start_node=None, type_walker=None, class_only=CLASS_ONLY):
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
    parser, existed_syms_dict, module_list, dependent_modules, module_param_list, module_sym_list = get_new_parser(start_node, current_content, type_walker, False, parser_type, class_only=class_only)
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
    if type_walker.need_mutator:
        start_node = get_ir_mutator(type_walker).visit_code(start_node)
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


def clean_parsers():
    _parser_manager.clean_parsers()


def parse_and_translate(content, frame, parser_type=None, func_name=None):
    record("parse_and_translate")
    def get_parse_result(parser_type):
        parser = get_default_parser()
        #
        model = parser.parse(content, parseinfo=True)
        # type walker
        type_walker, start_node = parse_ir_node(content, model, parser_type, class_only=CLASS_ONLY)
        # parsing Latex at the same time
        latex_thread = threading.Thread(target=generate_latex_code, args=(type_walker, start_node, frame,))
        latex_thread.start()
        # other type
        if parser_type is None:
            parser_type = ParserTypeEnum.NUMPY
        # if ConfMgr.getInstance().has_de:
        #     code_frame = walk_model(parser_type, type_walker, start_node, func_name, struct=True, class_only=CLASS_ONLY)
        #     if parser_type == ParserTypeEnum.EIGEN:
        #         code_frame.include += "#include <igl/readOFF.h>\n"
        #     res = code_frame.desc + code_frame.include + code_frame.struct
        # else:
        res = walk_model(parser_type, type_walker, start_node, func_name, class_only=CLASS_ONLY)
        return res, 0
    if DEBUG_MODE:
        result = get_parse_result(parser_type)
        wx.CallAfter(frame.UpdateMidPanel, result)
    else:
        try:
            result = get_parse_result(parser_type)
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
            wx.CallAfter(frame.UpdateMidPanel, result)
            if result[1] != 0:
                print(result[0])
    return result


def get_file_name(path_name):
    return Path(path_name).stem


def compile_la_content(la_content,
                       parser_type=ParserTypeEnum.NUMPY | ParserTypeEnum.EIGEN | ParserTypeEnum.LATEX | ParserTypeEnum.MATHJAX | ParserTypeEnum.MATLAB | ParserTypeEnum.MACROMATHJAX,
                       func_name=None,
                       path=None,
                       struct=False,
                       get_json=False,
                       get_vars=False,
                       class_only=CLASS_ONLY):
    set_source_name(func_name)
    if path:
        global _module_path
        _module_path = Path(path)
    parser = get_default_parser()
    record("First parsing, before")
    if True:
    # try:
        model = parser.parse(la_content, parseinfo=True)
        ret = {}
        json = ''
        var_data = ''
        #
        record("First type walker, before")
        type_walker, start_node = get_start_node(model)
        record("First type walker, after")
        if len(start_node.directives) > 0 and len(start_node.get_module_directives()) > 0:
            # dependent modules
            for cur_type in [ParserTypeEnum.NUMPY, ParserTypeEnum.EIGEN, ParserTypeEnum.MATLAB, ParserTypeEnum.LATEX, ParserTypeEnum.MATHJAX,  ParserTypeEnum.MATHML, ParserTypeEnum.MACROMATHJAX]:
                if parser_type & cur_type:
                    type_walker, start_node = parse_ir_node(la_content, model, cur_type)
                    if get_vars and var_data == '':
                        var_data = VarData(type_walker.parameters, type_walker.lhs_list, type_walker.ret_symbol)
                    cur_content = walk_model(cur_type, type_walker, start_node, func_name, struct, class_only=class_only)
                    ret[cur_type] = cur_content
                    if get_json and json == '':
                        json = type_walker.gen_json_content()
        else:
            # free
            record("compile_la_content, free")
            type_walker, start_node = parse_ir_node(la_content, model, parser_type=ParserTypeEnum.EIGEN, start_node=start_node, type_walker=type_walker)
            for cur_type in [ParserTypeEnum.NUMPY, ParserTypeEnum.EIGEN, ParserTypeEnum.MATLAB, ParserTypeEnum.LATEX, ParserTypeEnum.MATHJAX,  ParserTypeEnum.MATHML, ParserTypeEnum.MACROMATHJAX]:
                if parser_type & cur_type:
                    if get_vars and var_data == '':
                        var_data = VarData(type_walker.parameters, type_walker.lhs_list, type_walker.ret_symbol)
                    cur_content = walk_model(cur_type, type_walker, start_node, func_name, struct, class_only=class_only)
                    record("compile {}".format(str(cur_type)))
                    ret[cur_type] = cur_content
                    if get_json and json == '':
                        json = type_walker.gen_json_content()
    # except FailedParse as e:
    #     ret = LaMsg.getInstance().get_parse_error(e)
    # except FailedCut as e:
    #     ret = "FailedCut: {}".format(str(e))
    # except AssertionError as e:
    #     ret = "{}".format(e.args[0])
    # except Exception as e:
    #     ret = "Exception: {}".format(str(e))
    # except:
    #     ret = str(sys.exc_info()[0])
    # finally:
    if get_json:
        if get_vars:
            return ret, json, var_data
        return ret, json
    else:
        if get_vars:
            return ret, var_data
        return ret


def compile_la_file(la_file, parser_type=ParserTypeEnum.NUMPY | ParserTypeEnum.EIGEN | ParserTypeEnum.LATEX,
                       class_only=CLASS_ONLY, conf_file=None):
    """
    used for command line
    """
    # Alec: maybe this compile_la_file should just call compile_la_content after
    # reading the content?
    # ConfMgr.getInstance().set_source(la_file)
    # ConfMgr.getInstance().set_conf(conf_file)
    # ConfMgr.getInstance().parse()
    if la_file == "-":
        content = "\n".join(sys.stdin.readlines())
        base_name = CLASS_NAME
    else:
        content = read_from_file(la_file)
        base_name = get_file_name(la_file)
        global _module_path
        _module_path = os.path.dirname(Path(la_file))
    content = heartdown2lines(content)
    # print("head:", head, ", name:", name, "parser_type", parser_type, ", base_name:", base_name)
    try:
        def write_output(content, file_name):
            if la_file == "-":
                print("{}".format(content))
                print("\n")
            else:
                save_to_file(content, file_name)
        type2suffix = {
            ParserTypeEnum.NUMPY: ".py",
            ParserTypeEnum.EIGEN: ".h",
            ParserTypeEnum.LATEX: ".tex",
            ParserTypeEnum.MATHJAX: ".tex",
            ParserTypeEnum.MATLAB: ".m"
        }
        # Alec: in matlab a .m file can either be a "script" or a "function".
        #
        # A function-file should have a main function with the same name as the
        # file. Within that function there can be sub-functions.
        #
        # A script-file can have funtions (and sub functions) as long as they
        # *do not* have the same name as the file.
        #
        # For now, I'm making the assumption that we output a function-file called
        # *.m with a main function called * and a sub function
        # generateRandomData. When called with no arguments (nargin == 0),
        # it will issue a warning and run with random data.
        cur_contents = compile_la_content(content, parser_type, base_name, class_only=class_only)
        for cur_type, cur_content in cur_contents.items():
            cur_file_name = Path(la_file).with_suffix(type2suffix[cur_type])
            write_output(cur_content, cur_file_name)
    except FailedParse as e:
        print(LaMsg.getInstance().get_parse_error(e))
        raise
    except FailedCut as e:
        print("FailedCut: {}".format(str(e)))
        raise
    except AssertionError as e:
        print("{}".format(e.args[0]))
        raise
    except Exception as e:
        print("Exception: {}".format(str(e)))
        raise
    except:
        print(str(sys.exc_info()[0]))


def parse_la(content, parser_type):
    """
    used for testing
    """
    _parser_manager.set_test_mode()
    parser = get_default_parser()
    model = parser.parse(content, parseinfo=True)
    type_walker, node_info = parse_ir_node(content, model)
    res = walk_model(parser_type, type_walker, node_info)
    return res


def parse_in_background(content, frame, parse_type, path_name=None):
    """
    used for the GUI
    """
    CacheModuleManager.getInstance().reset_post()
    delete_ast_files()  # delete previous visualized pdfs
    func_name = None
    if path_name is not None:
        func_name = get_file_name(path_name)
    latex_thread = threading.Thread(target=parse_and_translate, args=(heartdown2lines(content), frame, parse_type, func_name,))
    latex_thread.start()


def create_parser_background():
    create_thread = threading.Thread(target=get_default_parser)
    create_thread.start()
