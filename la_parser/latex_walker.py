from la_parser.base_walker import *


class LatexWalker(BaseNodeWalker):
    def __init__(self):
        super().__init__()
        self.pre_str = '''\\documentclass[12pt]{article}\n\\usepackage{mathdots}\n\\usepackage{mathtools}\n\\begin{document}\n\\[\n'''
        self.post_str = '''\n\end{document}'''

    def walk_MatrixVdots(self, node):
        return "\\vdots"

    def walk_MatrixCdots(self, node):
        return "\\cdots"

    def walk_MatrixIddots(self, node):
        return "\\iddots"

    def walk_MatrixDdots(self, node):
        return "\\ddots"

    def walk_Factor(self, node):
        if node.id:
            return self.walk(node.id)
        elif node.num:
            return self.walk(node.num)
        elif node.sub:
            return self.walk(node.sub)
        elif node.m:
            return self.walk(node.m)
        elif node.f:
            return self.walk(node.f)

    def walk_Number(self, node):
        return self.walk(node.value)

    def walk_Integer(self, node):
        return ''.join(node.value)

    def walk_IdentifierSubscript(self, node):
        right = []
        for value in node.right:
            right.append(self.walk(value))
        return self.walk(node.left) + '_' + ','.join(right)

    def walk_IdentifierAlone(self, node):
        return node.value

    def walk_Start(self, node):
        return self.walk(node.stat) + "\n\\]\n\\[where\\]\n" + self.walk(node.cond)

    def walk_Statements(self, node):
        ret = []
        for val in node.value:
            ret.append(self.walk(val))
        return '\\]\n\\[\n'.join(ret)

    def walk_WhereConditions(self, node):
        ret = []
        for val in node.value:
            ret.append(self.walk(val))
        return '\n'.join(ret)

    def walk_MatrixCondition(self, node):
        id = self.walk(node.id)
        id1 = self.walk(node.id1)
        id2 = self.walk(node.id2)
        desc = self.walk(node.desc)
        return "\n\\[\n{id}:matrix({id1},{id2}):{desc}\n\\]".format(id=id, id1=id1, id2=id2, desc=desc)

    def walk_VectorCondition(self, node):
        id = self.walk(node.id)
        id1 = self.walk(node.id1)
        desc = self.walk(node.desc)
        return "\n\\[\n{id}:vector({id1}):{desc}\n\\]".format(id=id, id1=id1, desc=desc)

    def walk_ScalarCondition(self, node):
        id = self.walk(node.id)
        desc = self.walk(node.desc)
        return "\n\\[\n{id}:scalar:{desc}\n\\]".format(id=id, desc=desc)

    def walk_Assignment(self, node):
        return self.walk(node.left) + " = " + self.walk(node.right)

    def walk_Add(self, node):
        return self.walk(node.left) + " + " + self.walk(node.right)

    def walk_Subtract(self, node):
        return self.walk(node.left) + " - " + self.walk(node.right)

    def walk_Multiply(self, node):
        return self.walk(node.left) + " * " + self.walk(node.right)

    def walk_Divide(self, node):
        return "\\frac{" + self.walk(node.left) + "}{" + self.walk(node.right) + "}"

    def walk_Summation(self, node):
        ret = []
        for val in node.sub:
            ret.append(self.walk(val))
        return "\\sum_" + ','.join(ret) + " " + self.walk(node.exp)

    def walk_SingleValueModel(self, node):
        return self.walk(node.value)

    def walk_Subexpression(self, node):
        return '(' + self.walk(node.value) + ')'

    def walk_Matrix(self, node):
        return '\\begin{bmatrix}\n' + self.walk(node.value) + '\\end{bmatrix}'

    def walk_MatrixRows(self, node):
        ret = []
        for val in node.value:
            ret.append(self.walk(val))
        return ''.join(ret)

    def walk_MatrixRows(self, node, **kwargs):
        ret = []
        if node.rs:
            ret.append(self.walk(node.rs))
        if node.r:
            ret.append(self.walk(node.r))
        return ''.join(ret)

    def walk_MatrixRow(self, node):
        ret = []
        if node.rc:
            ret.append(self.walk(node.rc))
        if node.exp:
            ret.append(self.walk(node.exp))
        return ' & '.join(ret) + "\\\\\n"

    def walk_MatrixRowCommas(self, node):
        ret = []
        if node.value:
            ret.append(self.walk(node.value))
        if node.exp:
            ret.append(self.walk(node.exp))
        return ' & '.join(ret)

    def walk_ExpInMatrix(self, node):
        return self.walk(node.value)

    def walk_Derivative(self, node):
        return "\\partial" + self.walk(value)

    def walk_InnerProduct(self, node):
        return self.walk(left) + " " + self.walk(right)
