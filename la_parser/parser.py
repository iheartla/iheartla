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
    PUSH {value}'''


class Assignment(ModelRenderer):
    template = '''\
    {left}
    {right}
    ASSIGNMENT'''


class Add(ModelRenderer):
    template = '''\
    {left}
    {right}
    ADD'''


class Subtract(ModelRenderer):
    template = '''\
    {left}
    {right}
    SUB'''


class Multiply(ModelRenderer):
    template = '''\
    {left}
    {right}
    MUL'''


class Divide(ModelRenderer):
    template = '''\
    {left}
    {right}
    DIV'''


def parse_and_translate(content):
    grammar = open('LA.ebnf').read()
    parser = tatsu.compile(grammar, asmodel=True)
    model = parser.parse(content)
    postfix = PostfixCodeGenerator().render(model)
    return postfix


