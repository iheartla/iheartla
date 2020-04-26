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
from la_parser.latex_walker import LatexWalker
from la_parser.numpy_walker import NumpyWalker
from la_parser.ir import *
from la_parser.ir_visitor import *
import subprocess

class ParserTypeEnum(Enum):
    LATEX = 1
    NUMPY = 2
    EIGEN = 3
    MATLAB = 4
    JULIA = 5
    PYTORCH = 6
    ARMADILLO = 7
    TENSORFLOW = 8


def walk_model(parser_type, model):
    if parser_type == ParserTypeEnum.LATEX:
        walker = LatexWalker()
    elif parser_type == ParserTypeEnum.NUMPY:
        walker = NumpyWalker()
    return walker.walk_model(model)

def create_parser():
    grammar = open('la_grammar/LA.ebnf').read()
    parser = tatsu.compile(grammar, asmodel=True)
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
    mtimes = [ os.path.getmtime(path) for path in Path('la_grammar').glob('*.ebnf') ]
    # print( 'mtimes:', mtimes )
    ## If the parser hasn't been created or a file has changed, re-create it.
    if _last_parser is None or any([ t >= _last_parser_mtime for t in mtimes ]):
        print( "Creating parser..." )
        start_time = time.time()
        _last_parser = create_parser()
        _last_parser_mtime = time.time()
        print("------------ %.2f seconds ------------" % (time.time() - start_time))
    
    return _last_parser

def parse_and_translate(content):
    # try:
    start_time = time.time()
    parser = get_parser()
    model = parser.parse(content, parseinfo=True)
    parser_type = ParserTypeEnum.NUMPY
    res = walk_model(parser_type, model)
    try:
        show_pdf = False
        tex_content = walk_model(ParserTypeEnum.LATEX, model)
        tex_file_name = "la.tex"
        tex_file = open(tex_file_name, 'w')
        tex_file.write(tex_content)
        tex_file.close()
        ret = subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_file_name], capture_output=False)
        if ret.returncode == 0:
            show_pdf = True
    except subprocess.SubprocessError:
        show_pdf = False
    finally:
        if show_pdf:
            pass

    result = (res, 0)
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
