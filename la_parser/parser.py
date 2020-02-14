from pprint import pprint
from tatsu.objectmodel import Node
from tatsu.semantics import ModelBuilderSemantics
from tatsu.codegen import ModelRenderer
from tatsu.codegen import CodeGenerator
from tatsu.ast import AST
import tatsu
import sys

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
    {left} / {right}'''


class SingleLineStatement(ModelRenderer):
    template = '''\
    {value}'''


class SingleLineSeparator(ModelRenderer):
    template = '''\
    {value}'''


class AllContent(ModelRenderer):
    template = '''\
    {left::\n:}\n{right}'''


def parse_and_translate(content):
    grammar = open('LA.ebnf').read()
    parser = tatsu.compile(grammar, asmodel=True)
    model = parser.parse(content, parseinfo=True)
    postfix = PostfixCodeGenerator().render(model)
    return postfix

