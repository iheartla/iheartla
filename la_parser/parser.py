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
from la_parser.codegen_numpy import CodeGenNumpy
from la_parser.codegen_eigen import CodeGenEigen
from la_parser.codegen_latex import CodeGenLatex
from la_parser.type_walker import *
from la_parser.ir import *
from la_parser.ir_visitor import *
from la_tools.la_msg import *
from la_tools.la_helper import *
from la_tools.parser_manager import ParserManager
import subprocess
import threading
import regex as re

## We don't need wx to run in command-line mode. This makes it optional.
try:
    import wx
except ImportError:
    class wx(object): pass
    wx.CallAfter = lambda o,*x,**y: None

import sys
import traceback
import os.path
from pathlib import Path
import tempfile
import io


_id_pattern = re.compile("[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*")
_codegen_dict = {}
def get_codegen(parser_type):
    if parser_type not in _codegen_dict:
        if parser_type == ParserTypeEnum.LATEX:
            gen = CodeGenLatex()
        elif parser_type == ParserTypeEnum.NUMPY:
            gen = CodeGenNumpy()
        elif parser_type == ParserTypeEnum.EIGEN:
            gen = CodeGenEigen()
        _codegen_dict[parser_type] = gen
    return _codegen_dict[parser_type]


def walk_model(parser_type, type_walker, node_info, func_name=None):
    gen = get_codegen(parser_type)
    #
    gen.init_type(type_walker, func_name)
    gen.visit_code(node_info)
    if parser_type != ParserTypeEnum.LATEX: # print once
        gen.print_symbols()
    return gen.content

if getattr(sys, 'frozen', False):
    # We are running in a bundle.
    GRAMMAR_DIR = Path(sys._MEIPASS) / 'la_grammar'
else:
    # We are running in a normal Python environment.
    GRAMMAR_DIR = Path(__file__).resolve().parent.parent / 'la_grammar'
# print( 'GRAMMAR_DIR:', GRAMMAR_DIR )

_grammar_content = None   # content in file
_default_key = 'default'
_parser_manager = ParserManager(GRAMMAR_DIR)
def get_compiled_parser(grammar, keys='init'):
    log_la("keys:" + keys)
    return _parser_manager.get_parser(keys, grammar)


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
        file = open(GRAMMAR_DIR/'LA.ebnf')
        simplified_file = open(GRAMMAR_DIR/'simplified_grammar.ebnf')
        grammar = file.read()
        simplified_grammar = simplified_file.read()
        global _grammar_content
        _grammar_content = grammar
        # get init parser
        parser = get_compiled_parser(simplified_grammar)
        file.close()
        simplified_file.close()
        # get default parser
        get_compiled_parser(_grammar_content, _default_key)
    except IOError:
        print("IO Error!")
    return parser


_last_parser = None
_last_parser_mtime = None
_last_parser_mutex = threading.Lock()

def get_default_parser():
    '''
    Equivalent to create_parser(), but stores the result for immediate access in the future.
    Re-creates the parser if any grammar files change.
    '''
    global _last_parser, _last_parser_mtime
    
    with _last_parser_mutex:
        ## Collect all .ebnf file modification times.
        # print( 'grammar paths:', [ str(f) for f in GRAMMAR_DIR.glob('*.ebnf') ] )
        mtimes = [os.path.getmtime(path) for path in GRAMMAR_DIR.glob('*.ebnf')]
        # print( 'mtimes:', mtimes )
        ## If the parser hasn't been created or a file has changed, re-create it.
        if _last_parser is None or any([t >= _last_parser_mtime for t in mtimes]):
            print("Creating parser...")
            start_time = time.time()
            _last_parser = create_parser()
            _last_parser_mtime = time.time()
            print("------------ %.2f seconds ------------" % (time.time() - start_time))
    
        return _last_parser


def generate_latex_code(type_walker, node_info, frame):
    tex_content = ''
    show_pdf = None
    ## Let's create a temporary directory that cleans itself up
    ## and avoids a race condition other running instances of iheartla.
    ## We will pass UpdateTexPanel a file-like object containing the bytes of the PDF.
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            tex_content = walk_model(ParserTypeEnum.LATEX, type_walker, node_info)
            template_name = str(Path(tmpdir)/"la")
            tex_file_name = "{}.tex".format(template_name)
            tex_file = open(tex_file_name, 'w')
            tex_file.write(tex_content)
            tex_file.close()
            ## xelatex places its output in the current working directory, not next to the input file.
            ## We need to pass subprocess.run() the directory where we created the tex file.
            ## If we are running in a bundle, we don't have the PATH available. Assume MacTex.
            PATH = os.environ['PATH']
            PATH = ':'.join( [ '/Library/TeX/texbin', '/usr/texbin', '/usr/local/bin', '/opt/local/bin', '/usr/bin', '/bin', PATH ] )
            ret = subprocess.run(["xelatex", "-interaction=nonstopmode", tex_file_name], capture_output=True, cwd=tmpdir, env={"PATH":PATH})
            if ret.returncode == 0:
                ## If we are running in a bundle, we don't have the PATH available. Assume MacTex.
                ## But then we may not have ghostscript `gs` available, either.
                ret = subprocess.run(["pdfcrop", "--margins", "30", "{}.pdf".format(template_name), "{}.pdf".format(template_name)], capture_output=True, cwd=tmpdir, env={"PATH":PATH})
                # If xelatex worked, we have a PDF, even if pdfcrop failed.
                # if ret.returncode == 0:
                show_pdf = io.BytesIO( open("{}.pdf".format(template_name),'rb').read() )
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


def parse_ir_node(content, model):
    global _grammar_content
    current_content = _grammar_content
    # type walker
    type_walker = get_type_walker()
    start_node = type_walker.walk(model, pre_walk=True)
    # deal with function
    func_dict = type_walker.get_func_symbols()
    multi_list = []
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
    if len(multi_list) > 0:
        multi_list = sorted(multi_list, key=len, reverse=True)
        keys_rule = "'" + "'|'".join(multi_list) + "'"
        log_la("keys_rule:" + keys_rule)
        parse_key += "keys_rule:{};".format(keys_rule)
        current_content = current_content.replace("= !KEYWORDS(", "= const:({}) | (!(KEYWORDS | {} )".format(keys_rule, keys_rule))
    if len(func_dict.keys()) > 0:
        key_list = list(func_dict.keys())
        extra_list = []
        for key in key_list:
            if '`' not in key:
                extra_list.append('`{}`'.format(key))
        key_list += extra_list
        func_rule = "'" + "'|'".join(key_list) + "'"
        log_la("func_rule:" + func_rule)
        current_content = current_content.replace("func_id='!!!';", "func_id={};".format(func_rule))
        parse_key += "func symbol:{}, func sig:{}".format(','.join(func_dict.keys()), ";".join(func_dict.values()))
    # deal with packages
    if len(start_node.directives) > 0:
        # include directives
        package_name_dict = start_node.get_package_dict()
        key_names = []
        for package in package_name_dict:
            name_list = package_name_dict[package]
            if 'e' in name_list:
                current_content = current_content.replace("pi;", "pi|e;")
                current_content = current_content.replace("BUILTIN_KEYWORDS;", "BUILTIN_KEYWORDS|e;")
                name_list.remove('e')
                parse_key += 'e;'
            for name in name_list:
                key_names.append("{}_func".format(name))
        if len(key_names) > 0:
            # add new rules
            keyword_index = current_content.find('predefined_built_operators\n')
            current_content = current_content[:keyword_index] + '|'.join(key_names) + '|' + current_content[keyword_index:]
            parse_key += ';'.join(key_names)
    # get new parser
    parser = get_compiled_parser(current_content, parse_key)
    model = parser.parse(content, parseinfo=True)
    # second parsing
    type_walker.reset_state(content)   # reset
    start_node = type_walker.walk(model)
    return type_walker, start_node


def clean_parsers():
    _parser_manager.clean_parsers()


def parse_and_translate(content, frame, parser_type=None, func_name=None):
    try:
        start_time = time.time()
        parser = get_default_parser()
        model = parser.parse(content, parseinfo=True)
        # type walker
        type_walker, start_node = parse_ir_node(content, model)
        # parsing Latex at the same time
        latex_thread = threading.Thread(target=generate_latex_code, args=(type_walker, start_node, frame,))
        latex_thread.start()
        # other type
        if parser_type is None:
            parser_type = ParserTypeEnum.NUMPY
        res = walk_model(parser_type, type_walker, start_node, func_name)
        result = (res, 0)
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


def compile_la_file(la_file, parser_type):
    """
    used for command line
    """
    content = read_from_file(la_file)
    base_name = get_file_name(la_file)
    # print("head:", head, ", name:", name, "parser_type", parser_type, ", base_name:", base_name)
    parser = get_default_parser()
    model = parser.parse(content, parseinfo=True)
    type_walker, start_node = parse_ir_node(content, model)
    if parser_type & ParserTypeEnum.NUMPY:
        numpy_file = Path(la_file).with_suffix( ".py" )
        numpy_content = walk_model(ParserTypeEnum.NUMPY, type_walker, start_node, func_name=base_name)
        save_to_file(numpy_content, numpy_file)
    if parser_type & ParserTypeEnum.EIGEN:
        eigen_file = Path(la_file).with_suffix( ".cpp" )
        eigen_content = walk_model(ParserTypeEnum.EIGEN, type_walker, start_node, func_name=base_name)
        save_to_file(eigen_content, eigen_file)
    if parser_type & ParserTypeEnum.LATEX:
        tex_file = Path(la_file).with_suffix( ".tex" )
        tex_content = walk_model(ParserTypeEnum.LATEX, type_walker, start_node, func_name=base_name)
        save_to_file(tex_content, tex_file)


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