from pprint import pprint
from tatsu.objectmodel import Node
from tatsu.semantics import ModelBuilderSemantics
from tatsu.codegen import ModelRenderer
from tatsu.codegen import CodeGenerator
from tatsu.ast import AST
import tatsu
import sys
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

THIS_MODULE = sys.modules[__name__]


class LatexCodeGenerator(CodeGenerator):
    def __init__(self):
        super(LatexCodeGenerator, self).__init__(modules=[THIS_MODULE])


class Number(ModelRenderer):
    template = '''\
    {value}'''


class Statements(ModelRenderer):
    template = '''\
    {value::\\]\n\\[\n:}'''


class Assignment(ModelRenderer):
    template = '''\
    {left} = {right}'''


class Add(ModelRenderer):
    template = '''\
    {left} + {right}'''


class Subtract(ModelRenderer):
    template = '''\
    {left} - {right}'''


class Multiply(ModelRenderer):
    template = '''\
    {left} * {right}'''


class Divide(ModelRenderer):
    template = '''\
    \\frac{{{left}}}{{{right}}}
    '''


class SingleValueModel(ModelRenderer):
    template = '''\
    {value}'''


class Subexpression(ModelRenderer):
    template = '''({value})'''


# {value::&:}\n
class Matrix(ModelRenderer):
    template = '''\
    \\begin{{bmatrix}}
    {value}\end{{bmatrix}}
    '''


class MatrixRows(ModelRenderer):
    template = '''\
    {value:::}
    '''


class MatrixRow(ModelRenderer):
    template = '''\
    {value::&:}\\\\
    '''


class MatrixRowCommas(ModelRenderer):
    template = "{value::&:}"


class Derivative(ModelRenderer):
    template = '''\
    \\partial {value}
    '''


class InnerProduct(ModelRenderer):
    template = '''\
    {left}  {right} 
    '''


class MatrixVdots(ModelRenderer):
    template = '''\
    \\vdots'''


class MatrixCdots(ModelRenderer):
    template = '''\
    \\cdots'''


class MatrixIddots(ModelRenderer):
    template = '''\
    \\iddots'''


class MatrixDdots(ModelRenderer):
    template = '''\
    \\ddots'''


def parse_and_translate(content):
    # try:
    grammar = open('la_grammar/LA.ebnf').read()
    parser = tatsu.compile(grammar, asmodel=True, trace=False)
    model = parser.parse(content, parseinfo=True)
    print('model:', isinstance(model, Node))
    print('cl:', model.__class__.__name__)
    print('class:', isinstance(model.ast, AST))
    tex = LatexCodeGenerator().render(model)
    tex = '''\\documentclass[12pt]{article}\n\\usepackage{mathdots}\n\\usepackage{mathtools}\n\\begin{document}\n\\[\n''' + tex + '''\n\]\n\end{document}'''
    # tex = '''\\documentclass[12pt]{article}\n\\usepackage{mathdots}\n\\usepackage{mathtools}\n\\begin{document}\n$\n''' + tex + '''\n$\n\end{document}'''
    result = (tex, 0)
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
