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
from la_parser.base_walker import ParserTypeEnum
from la_parser.latex_walker import LatexWalker
from la_parser.numpy_walker import NumpyWalker
from la_parser.eigen_walker import EigenWalker
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


def create_parser():
    parser = None
    try:
        file = open('la_grammar/LA.ebnf')
        grammar = file.read()
        parser = tatsu.compile(grammar, asmodel=True)
        file.close()
    except IOError:
        print("IO Error!")
    return parser


_last_parser = None
_last_parser_mtime = None


def get_parser():
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
        ret = subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_file_name], capture_output=False)
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


def parse_and_translate(content, frame, parser_type=None):
    # try:
    start_time = time.time()
    parser = get_parser()
    model = parser.parse(content, parseinfo=True)
    # type walker
    type_walker = TypeWalker()
    node_info = type_walker.walk(model)
    # parsing Latex at the same time
    latex_thread = threading.Thread(target=generate_latex_code, args=(type_walker, node_info, frame,))
    latex_thread.start()
    # other type
    if parser_type is None:
        parser_type = ParserTypeEnum.NUMPY
    res = walk_model(parser_type, type_walker, node_info)
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


def parse_la(content, parser_type):
    parser = get_parser()
    model = parser.parse(content, parseinfo=True)
    type_walker = TypeWalker()
    node_info = type_walker.walk(model)
    res = walk_model(parser_type, type_walker, node_info)
    return res


def parse_in_background(content, frame, parse_type):
    latex_thread = threading.Thread(target=parse_and_translate, args=(content, frame, parse_type,))
    latex_thread.start()


def create_parser_background():
    create_thread = threading.Thread(target=get_parser)
    create_thread.start()