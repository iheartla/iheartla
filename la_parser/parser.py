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


class PostfixCodeGenerator(CodeGenerator):
    def __init__(self):
        super(PostfixCodeGenerator, self).__init__(modules=[THIS_MODULE])


class Number(ModelRenderer):
    template = '''\
    {value}'''


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


class SingleLineStatement(ModelRenderer):
    template = '''\
    {value}'''


class SingleLineSeparator(ModelRenderer):
    template = '''\
    {value}'''


class AllContent(ModelRenderer):
    template = '''\
    {left::\n:}\n{right}'''


class Subexpression(ModelRenderer):
    template = '''({value})'''


class Matrix(ModelRenderer):
    template = '''\
    \\begin{{bmatrix}}
    {value::&:}\n
    \end{{bmatrix}}
    '''

class Derivative(ModelRenderer):
    template = '''\
    \\partial {value}
    '''

class InnerProduct(ModelRenderer):
    template = '''\
    {left}  {right} 
    '''

def parse_and_translate(content):
    # try:
    grammar = open('la_grammar/LA.ebnf').read()
    parser = tatsu.compile(grammar, asmodel=True)
    # print content
    # print content.encode('utf-8')
    model = parser.parse(content.encode('utf-8'), parseinfo=True)
    print 'model:', isinstance(model, Node)
    print 'cl:', model.__class__.__name__
    print 'class:', isinstance(model.ast, AST)
    print model.ast['left']
    print model.ast['right']
    postfix = PostfixCodeGenerator().render(model)
    postfix = '''\documentclass[12pt]{article}\n\usepackage{mathtools}\n\\begin{document}\n\[''' + postfix + '''\]\n\end{document}'''
    result = (postfix, 0)
    return result
    # except FailedParse as e:
    #     postfix = str(e)
    #     result = (postfix, 1)
    # except FailedCut as e:
    #     postfix = str(e)
    #     result = (postfix, 1)
    # except:
    #     pass
    #     postfix = str(sys.exc_info()[0])
    #     result = (postfix, 1)
    # finally:
    #     print postfix
    #     return result
