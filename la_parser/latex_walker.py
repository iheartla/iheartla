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

