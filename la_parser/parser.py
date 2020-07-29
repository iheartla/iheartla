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
import subprocess
import threading
import wx
import sys
import traceback
import ntpath


def walk_model(parser_type, type_walker, node_info):
    if parser_type == ParserTypeEnum.LATEX:
        gen = CodeGenLatex()
    elif parser_type == ParserTypeEnum.NUMPY:
        gen = CodeGenNumpy()
    elif parser_type == ParserTypeEnum.EIGEN:
        gen = CodeGenEigen()
    #
    gen.init_type(type_walker)
    gen.visit_code(node_info)
    if parser_type != ParserTypeEnum.LATEX: # print once
        gen.print_symbols()
    return gen.content

_grammar_content = None
_compiled_parser = {}
def get_compiled_parser(grammar):
    global _compiled_parser
    if grammar in _compiled_parser:
        return _compiled_parser[grammar]
    parser = tatsu.compile(grammar, asmodel=True)
    _compiled_parser[grammar] = parser
    return parser

def create_parser():
    parser = None
    try:
        file = open('la_grammar/LA.ebnf')
        grammar = file.read()
        global _grammar_content
        _grammar_content = grammar
        parser = get_compiled_parser(grammar)
        file.close()
    except IOError:
        print("IO Error!")
    return parser


_last_parser = None
_last_parser_mtime = None


def get_default_parser():
    '''
    Equivalent to create_parser(), but stores the result for immediate access in the future.
    Re-creates the parser if any grammar files change.
    '''
    global _last_parser, _last_parser_mtime
    ## Collect all .ebnf file modification times.
    from pathlib import Path
    import os
    # print( 'grammar paths:', [ str(f) for f in Path('la_grammar').glob('*.ebnf') ] )
    mtimes = [os.path.getmtime(path) for path in Path('la_grammar').glob('*.ebnf')]
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
    try:
        tex_content = walk_model(ParserTypeEnum.LATEX, type_walker, node_info)
        tex_file_name = "la.tex"
        tex_file = open(tex_file_name, 'w')
        tex_file.write(tex_content)
        tex_file.close()
        ret = subprocess.run(["xelatex", "-interaction=nonstopmode", tex_file_name], capture_output=False)
        if ret.returncode == 0:
            tex_content = None
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
        wx.CallAfter(frame.UpdateTexPanel, tex_content)


def parse_ir_node(content, model):
    # type walker
    type_walker = TypeWalker()
    start_node = type_walker.walk(model)
    if len(start_node.directives) > 0:
        # include directives
        package_name_dict = start_node.get_package_dict()
        key_names = []
        for package in package_name_dict:
            for name in package_name_dict[package]:
                key_names.append("{}_func".format(name))
        global _grammar_content
        # remove derivatives grammar
        current_content = _grammar_content.replace('| {separator_with_space} directive+:Directive {{separator_with_space}+ directive+:Directive}\n    |', '')
        # add new rules
        keyword_index = current_content.find('predefined_built_operators\n')
        current_content = current_content[:keyword_index] + '|'.join(key_names) + '|' + current_content[keyword_index:]
        # print(current_content)
        # get new parser
        parser = get_compiled_parser(current_content)
        model = parser.parse(content, parseinfo=True)
        start_node = type_walker.walk(model)
    return type_walker, start_node


def parse_and_translate(content, frame, parser_type=None):
    # try:
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
    res = walk_model(parser_type, type_walker, start_node)
    result = (res, 0)
    wx.CallAfter(frame.UpdateMidPanel, result)
    print("------------ %.2f seconds ------------" % (time.time() - start_time))
    return result
    # except FailedParse as e:
    #     tex = str(e)
    #     result = (tex, 1)
    # except FailedCut as e:
    #     tex = str(e)
    #     result = (tex, 1)
    # except:
    #     pass
    #     tex = str(sys.exc_info()[0])
    #     result = (tex, 1)
    # finally:
    #     print tex
    #     return result


def save_to_file(content, file_name):
    try:
        file = open(file_name, 'w')
        file.write(content)
        file.close()
    except IOError:
        print("IO Error!")


def read_from_file(file_name):
    try:
        file = open(file_name, 'r')
        content = file.read()
        file.close()
    except IOError:
        content = ''
        print("IO Error!")
    return content


def compile_la_file(la_file, parser_type):
    content = read_from_file(la_file)
    head, tail = ntpath.split(la_file)
    name = tail or ntpath.basename(head)
    base_name = name.rsplit('.', 1)[0]
    # print("head:", head, ", name:", name, "parser_type", parser_type, ", base_name:", base_name)
    parser = get_default_parser()
    model = parser.parse(content, parseinfo=True)
    type_walker, start_node = parse_ir_node(content, model)
    if parser_type & ParserTypeEnum.NUMPY:
        numpy_file = base_name + ".py"
        numpy_content = walk_model(ParserTypeEnum.NUMPY, type_walker, start_node)
        save_to_file(numpy_content, numpy_file)
    if parser_type & ParserTypeEnum.EIGEN:
        eigen_file = base_name + ".cpp"
        eigen_content = walk_model(ParserTypeEnum.EIGEN, type_walker, start_node)
        save_to_file(eigen_content, eigen_file)
    if parser_type & ParserTypeEnum.LATEX:
        tex_file = base_name + ".tex"
        tex_content = walk_model(ParserTypeEnum.LATEX, type_walker, start_node)
        save_to_file(tex_content, tex_file)


def parse_la(content, parser_type):
    parser = get_default_parser()
    model = parser.parse(content, parseinfo=True)
    type_walker, node_info = parse_ir_node(content, model)
    res = walk_model(parser_type, type_walker, node_info)
    return res


def parse_in_background(content, frame, parse_type):
    latex_thread = threading.Thread(target=parse_and_translate, args=(content, frame, parse_type,))
    latex_thread.start()


def create_parser_background():
    create_thread = threading.Thread(target=get_default_parser)
    create_thread.start()