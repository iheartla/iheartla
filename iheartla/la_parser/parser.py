from pprint import pprint
import time
from tatsu.objectmodel import Node
from tatsu.semantics import ModelBuilderSemantics
from tatsu.ast import AST
import tatsu
from tatsu.exceptions import (
    FailedCut,
    FailedExpectingEndOfText,
    FailedLeftRecursion,
    FailedLookahead,
    FailedParse,
    FailedPattern,
    FailedRef,
    FailedSemantics,
    FailedKeywordSemantics,
    FailedToken,
    OptionSucceeded
)
from enum import Enum
from .codegen import *
from .codegen_numpy import CodeGenNumpy
from .codegen_eigen import CodeGenEigen
from .codegen_latex import CodeGenLatex
from .codegen_mathjax import CodeGenMathjax
from .codegen_matlab import CodeGenMatlab
from .type_walker import *
from .ir import *
from .ir_visitor import *
from ..la_tools.la_msg import *
from ..la_tools.la_helper import *
from ..la_tools.parser_manager import ParserManager
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
_module_path = Path.home() / 'Downloads'


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
        elif parser_type == ParserTypeEnum.MATLAB:
            gen = CodeGenMatlab()
        _codegen_dict[parser_type] = gen
    return _codegen_dict[parser_type]


def walk_model(parser_type, type_walker, node_info, func_name=None):
    gen = get_codegen(parser_type)
    #
    gen.init_type(type_walker, func_name)
    code_frame = gen.visit_code(node_info)
    if parser_type != ParserTypeEnum.LATEX:  # print once
        gen.print_symbols()
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
_parser_manager = ParserManager(GRAMMAR_DIR)


def get_compiled_parser(grammar, keys='init', extra_dict={}):
    log_la("keys:" + keys)
    return _parser_manager.get_parser(keys, grammar, extra_dict)


_type_walker = None


def get_type_walker():
    global _type_walker
    if _type_walker:
        _type_walker.reset()
    else:
        _type_walker = TypeWalker()
    return _type_walker


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


def parse_ir_node(content, model, parser_type=ParserTypeEnum.EIGEN):
    global _grammar_content
    current_content = _grammar_content
    # type walker
    type_walker = get_type_walker()
    start_node = type_walker.walk(model, pre_walk=True)
    # deal with function
    func_dict = type_walker.get_func_symbols()
    multi_list = []
    extra_dict = {}
    parse_key = _default_key
    for parameter in type_walker.parameters:
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
    for par in start_node.get_module_pars_list():
        if _id_pattern.fullmatch(par):
            continue  # valid single identifier
        multi_list.append(par)
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
    if len(func_dict.keys()) > 0:
        key_list = list(func_dict.keys())
        extra_list = []
        for key in key_list:
            if '`' not in key:
                extra_list.append('`{}`'.format(key))
        key_list += extra_list
        key_list = [re.escape(item).replace('/', '\\/') for item in key_list]
        func_rule = "/" + "/|/".join(key_list) + "/"
        extra_dict['funcs'] = key_list
        log_la("func_rule:" + func_rule)
        if DEBUG_PARSER:
            current_content = current_content.replace("func_id='!!!';", "func_id={};".format(func_rule))
        parse_key += "func symbol:{}, func sig:{}".format(','.join(func_dict.keys()), ";".join(func_dict.values()))
    # deal with packages
    dependent_modules = []
    if len(start_node.directives) > 0:
        dependent_modules = start_node.get_module_directives()
        # include directives
        package_name_dict = start_node.get_package_dict()
        package_name_list = []
        key_names = []
        for package in package_name_dict:
            name_list = package_name_dict[package]
            if 'e' in name_list:
                if DEBUG_PARSER:
                    current_content = current_content.replace("pi;", "pi|e;")
                    current_content = current_content.replace("BUILTIN_KEYWORDS;", "BUILTIN_KEYWORDS|e;")
                name_list.remove('e')
                parse_key += 'e;'
                package_name_list.append('e')
            for name in name_list:
                key_names.append("{}_func".format(name))
        package_name_list += key_names
        if len(key_names) > 0:
            # add new rules
            if DEBUG_PARSER:
                keyword_index = current_content.find('predefined_built_operators;')
                current_content = current_content[:keyword_index] + '|'.join(key_names) + '|' + current_content[
                                                                                                keyword_index:]
            parse_key += ';'.join(key_names)
        extra_dict['pkg'] = package_name_list
    # get new parser
    parser = get_compiled_parser(current_content, parse_key, extra_dict)
    model = parser.parse(content, parseinfo=True)
    # dependent modules
    existed_syms_dict = {}
    module_list = []
    if len(dependent_modules) > 0:
        for module in dependent_modules:
            try:
                parse_info = module.module.parse_info
                err_msg = "Invalid module:{}".format(module.module.get_name())
                module_file = "{}/{}.ihla".format(_module_path, module.module.get_name())
                module_content = read_from_file(module_file)
                # Init parser
                parser = get_default_parser()
                new_model = parser.parse(module_content, parseinfo=True)
                tmp_type_walker, tmp_start_node = parse_ir_node(module_content, new_model, parser_type)
                pre_frame = walk_model_frame(parser_type, tmp_type_walker, tmp_start_node, module.module.get_name())
                name_list = []
                par_lsit = []
                for sym in module.names:
                    existed_syms_dict[sym.get_name()] = copy.deepcopy(tmp_type_walker.symtable[sym.get_name()])
                    name_list.append(sym.get_name())
                for par in module.params:
                    par_lsit.append(par.get_name())
                module_list.append(CodeModule(frame=pre_frame, name=module.module.get_name(), syms=name_list, params=par_lsit))
            except:
                assert False, get_err_msg_info(parse_info, err_msg)
    # second parsing
    type_walker.reset_state(content)  # reset
    type_walker.symtable.update(existed_syms_dict)
    start_node = type_walker.walk(model)
    start_node.module_list = module_list
    start_node.module_syms = existed_syms_dict
    return type_walker, start_node


def clean_parsers():
    _parser_manager.clean_parsers()


def parse_and_translate(content, frame, parser_type=None, func_name=None):
    start_time = time.time()
    def get_parse_result(parser_type):
        parser = get_default_parser()
        model = parser.parse(content, parseinfo=True)
        # type walker
        type_walker, start_node = parse_ir_node(content, model, parser_type)
        # parsing Latex at the same time
        latex_thread = threading.Thread(target=generate_latex_code, args=(type_walker, start_node, frame,))
        latex_thread.start()
        # other type
        if parser_type is None:
            parser_type = ParserTypeEnum.NUMPY
        res = walk_model(parser_type, type_walker, start_node, func_name)
        return res, 0
    if DEBUG_MODE:
        result = get_parse_result(parser_type)
        wx.CallAfter(frame.UpdateMidPanel, result)
        print("------------ %.2f seconds ------------" % (time.time() - start_time))
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
            tex = "Exception: {}".format(str(e))
            result = (tex, 1)
        except:
            tex = str(sys.exc_info()[0])
            result = (tex, 1)
        finally:
            wx.CallAfter(frame.UpdateMidPanel, result)
            print("------------ %.2f seconds ------------" % (time.time() - start_time))
            if result[1] != 0:
                print(result[0])
    return result


def get_file_name(path_name):
    return Path(path_name).stem


def compile_la_content(la_content,
                       parser_type=ParserTypeEnum.NUMPY | ParserTypeEnum.EIGEN | ParserTypeEnum.LATEX | ParserTypeEnum.MATHJAX | ParserTypeEnum.MATLAB,
                       func_name=None):
    parser = get_default_parser()
    try:
        model = parser.parse(la_content, parseinfo=True)
        ret = []
        for cur_type in [ParserTypeEnum.NUMPY, ParserTypeEnum.EIGEN, ParserTypeEnum.LATEX, ParserTypeEnum.MATHJAX, ParserTypeEnum.MATLAB]:
            if parser_type & cur_type:
                type_walker, start_node = parse_ir_node(la_content, model, cur_type)
                cur_content = walk_model(cur_type, type_walker, start_node, func_name)
                ret.append(cur_content)
    except FailedParse as e:
        ret = LaMsg.getInstance().get_parse_error(e)
    except FailedCut as e:
        ret = "FailedCut: {}".format(str(e))
    except AssertionError as e:
        ret = "{}".format(e.args[0])
    except Exception as e:
        ret = "Exception: {}".format(str(e))
    except:
        ret = str(sys.exc_info()[0])
    finally:
        return ret


def compile_la_file(la_file, parser_type=ParserTypeEnum.NUMPY | ParserTypeEnum.EIGEN | ParserTypeEnum.LATEX):
    """
    used for command line
    """
    # Alec: maybe this compile_la_file should just call compile_la_content after
    # reading the content?
    if la_file == "-":
        content = "\n".join(sys.stdin.readlines())
        base_name = "iheartla"
    else:
        content = read_from_file(la_file)
        base_name = get_file_name(la_file)
        global _module_path
        _module_path = os.path.dirname(Path(la_file))
    # print("head:", head, ", name:", name, "parser_type", parser_type, ", base_name:", base_name)
    try:
        def write_output(content, file_name):
            if la_file == "-":
                print("{}".format(content))
                print("\n")
            else:
                save_to_file(content, file_name)
        cur_types = [ParserTypeEnum.NUMPY, ParserTypeEnum.EIGEN, ParserTypeEnum.LATEX, ParserTypeEnum.MATHJAX,
                         ParserTypeEnum.MATLAB]
        cur_suffix = [".py", ".cpp", ".tex", ".tex", ".m"]
        for cur_index in range(len(cur_types)):
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
            cur_file_name = Path(la_file).with_suffix(cur_suffix[cur_index])
            cur_content = compile_la_content(content, cur_types[cur_index], base_name)
            write_output(cur_content[0], cur_file_name)
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
    func_name = None
    if path_name is not None:
        func_name = get_file_name(path_name)
    latex_thread = threading.Thread(target=parse_and_translate, args=(content, frame, parse_type, func_name,))
    latex_thread.start()


def create_parser_background():
    create_thread = threading.Thread(target=get_default_parser)
    create_thread.start()
