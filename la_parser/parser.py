from pprint import pprint
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
from la_parser.latex_walker import LatexCodeGenerator
from la_parser.numpy_walker import NumpyWalker
from la_parser.eigen_walker import EigenWalker
from la_parser.matlab_walker import MatlabWalker
from la_parser.julia_walker import JuliaWalker
from la_parser.pytorch_walker import PytorchWalker
from la_parser.tensorflow_walker import TensorflowWalker


class ParserType(Enum):
    LATEX = 1
    NUMPY = 2
    EIGEN = 3
    MATLAB = 4
    JULIA = 5
    PYTORCH = 6
    ARMADILLO = 7
    TENSORFLOW = 8


def walk_model(parser_type, model):
    if parser_type == ParserType.NUMPY:
        walker = NumpyWalker()
    elif parser_type == ParserType.EIGEN:
        walker = EigenWalker()
    elif parser_type == ParserType.MATLAB:
        walker = MatlabWalker()
    elif parser_type == ParserType.JULIA:
        walker = JuliaWalker()
    elif parser_type == ParserType.PYTORCH:
        walker = PytorchWalker()
    elif parser_type == ParserType.ARMADILLO:
        walker = ArmadilloWalker()
    elif parser_type == ParserType.TENSORFLOW:
        walker = TensorflowWalker()
    return walker.walk_model(model)


def parse_and_translate(content):
    # try:
    grammar = open('la_grammar/LA.ebnf').read()
    parser_type = ParserType.LATEX
    result = ('', 0)
    parser = tatsu.compile(grammar, asmodel=True)
    model = parser.parse(content, parseinfo=True)
    if parser_type == ParserType.LATEX:
        tex = LatexCodeGenerator().render(model)
        tex = '''\\documentclass[12pt]{article}\n\\usepackage{mathdots}\n\\usepackage{mathtools}\n\\begin{document}\n\\[\n''' + tex + '''\n\]\n\end{document}'''
        result = (tex, 0)
    else:
        res = walk_model(parser_type, model)
        result = (res, 0)
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
