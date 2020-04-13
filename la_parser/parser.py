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
from la_parser.eigen_walker import EigenWalker
from la_parser.matlab_walker import MatlabWalker
from la_parser.julia_walker import JuliaWalker
from la_parser.pytorch_walker import PytorchWalker
from la_parser.tensorflow_walker import TensorflowWalker


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
    elif parser_type == ParserTypeEnum.EIGEN:
        walker = EigenWalker()
    elif parser_type == ParserTypeEnum.MATLAB:
        walker = MatlabWalker()
    elif parser_type == ParserTypeEnum.JULIA:
        walker = JuliaWalker()
    elif parser_type == ParserTypeEnum.PYTORCH:
        walker = PytorchWalker()
    elif parser_type == ParserTypeEnum.ARMADILLO:
        walker = ArmadilloWalker()
    elif parser_type == ParserTypeEnum.TENSORFLOW:
        walker = TensorflowWalker()
    return walker.walk_model(model)


def parse_and_translate(content):
    # try:
    start_time = time.time()
    grammar = open('la_grammar/LA.ebnf').read()
    parser_type = ParserTypeEnum.NUMPY
    parser = tatsu.compile(grammar, asmodel=True)
    model = parser.parse(content, parseinfo=True)
    res = walk_model(parser_type, model)
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
