from tatsu.codegen import CodeGenerator
from tatsu.codegen import ModelRenderer
import sys
THIS_MODULE = sys.modules[__name__]


class LatexCodeGenerator(CodeGenerator):
    def __init__(self):
        super(LatexCodeGenerator, self).__init__(modules=[THIS_MODULE])


class Number(ModelRenderer):
    template = '''\
    {value}'''


class IdentifierSubscript(ModelRenderer):
    template = '''\
    {left}_{right::,:}'''


class Start(ModelRenderer):
    template = '''\
    {stat}\n\\]
\\[where\\]
{cond}'''


class Statements(ModelRenderer):
    template = '''\
    {value::\\]\n\\[\n:}'''


class WhereConditions(ModelRenderer):
    template = '''\
    {value::\n:}'''


class MatrixCondition(ModelRenderer):
    template = '''\
    \n\\[\n{id}:matrix({id1},{id2}):{desc}\n\\]'''


class VectorCondition(ModelRenderer):
    template = '''\
    \n\\[\n{id}:vector({id1}):{desc}\n\\]'''


class ScalarCondition(ModelRenderer):
    template = '''\
    \n\\[\n{id}:scalar:{desc}\n\\]'''


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


class Summation(ModelRenderer):
    template = '''\
    \\sum_{sub::,:} {exp}
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
    {value}\\end{{bmatrix}}
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

