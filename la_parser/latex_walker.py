from la_parser.base_walker import *


class LatexWalker(BaseNodeWalker):
    def __init__(self):
        super().__init__()
        self.pre_str = '''\\documentclass[12pt]{article}\n\\usepackage{mathdots}\n\\usepackage{mathtools}\n\\begin{document}\n\\[\n'''
        self.post_str = '''\n\end{document}'''

    def walk_MatrixVdots(self, node, **kwargs):
        return "\\vdots"

    def walk_MatrixCdots(self, node, **kwargs):
        return "\\cdots"

    def walk_MatrixIddots(self, node, **kwargs):
        return "\\iddots"

    def walk_MatrixDdots(self, node, **kwargs):
        return "\\ddots"

    def walk_Factor(self, node, **kwargs):
        if node.id:
            return self.walk(node.id, **kwargs)
        elif node.num:
            return self.walk(node.num, **kwargs)
        elif node.sub:
            return self.walk(node.sub, **kwargs)
        elif node.m:
            return self.walk(node.m, **kwargs)
        elif node.nm:
            return self.walk(node.nm, **kwargs)
        elif node.op:
            return self.walk(node.op, **kwargs)
        elif node.s:
            return self.walk(node.s, **kwargs)

    def walk_Number(self, node, **kwargs):
        return self.walk(node.value, **kwargs)

    def walk_Integer(self, node):
        return ''.join(node.value)

    def walk_IdentifierSubscript(self, node, **kwargs):
        right = []
        for value in node.right:
            right.append(self.walk(value, **kwargs))
        return self.walk(node.left, **kwargs) + '_' + ','.join(right)

    def walk_IdentifierAlone(self, node, **kwargs):
        return node.value

    def walk_Start(self, node, **kwargs):
        return self.walk(node.stat, **kwargs) + "\n\\]\n\\[where\\]\n" + self.walk(node.cond, **kwargs)

    def walk_Statements(self, node, **kwargs):
        ret = []
        for val in node.value:
            ret.append(self.walk(val, **kwargs))
        return '\\]\n\\[\n'.join(ret)

    def walk_WhereConditions(self, node, **kwargs):
        ret = []
        for val in node.value:
            ret.append(self.walk(val, **kwargs))
        return '\n'.join(ret)

    def walk_MatrixCondition(self, node, **kwargs):
        id = self.walk(node.id, **kwargs)
        id1 = self.walk(node.id1, **kwargs)
        id2 = self.walk(node.id2, **kwargs)
        desc = self.walk(node.desc, **kwargs)
        return "\n\\[\n{id}:matrix({id1},{id2}):{desc}\n\\]".format(id=id, id1=id1, id2=id2, desc=desc)

    def walk_VectorCondition(self, node, **kwargs):
        id = self.walk(node.id, **kwargs)
        id1 = self.walk(node.id1, **kwargs)
        desc = self.walk(node.desc, **kwargs)
        return "\n\\[\n{id}:vector({id1}):{desc}\n\\]".format(id=id, id1=id1, desc=desc)

    def walk_ScalarCondition(self, node, **kwargs):
        id = self.walk(node.id, **kwargs)
        desc = self.walk(node.desc, **kwargs)
        return "\n\\[\n{id}:scalar:{desc}\n\\]".format(id=id, desc=desc)

    def walk_SetCondition(self, node, **kwargs):
        id0_info = self.walk(node.id, **kwargs)
        ret = node.text.split(':')
        desc = ':'.join(ret[1:len(ret)])
        return desc

    def walk_Assignment(self, node, **kwargs):
        return self.walk(node.left, **kwargs) + " = " + self.walk(node.right, **kwargs)

    def walk_Add(self, node, **kwargs):
        return self.walk(node.left, **kwargs) + " + " + self.walk(node.right, **kwargs)

    def walk_Subtract(self, node, **kwargs):
        return self.walk(node.left, **kwargs) + " - " + self.walk(node.right, **kwargs)

    def walk_Multiply(self, node, **kwargs):
        return self.walk(node.left, **kwargs) + " * " + self.walk(node.right, **kwargs)

    def walk_Divide(self, node, **kwargs):
        return "\\frac{" + self.walk(node.left, **kwargs) + "}{" + self.walk(node.right, **kwargs) + "}"

    def walk_Summation(self, node, **kwargs):
        ret = []
        for val in node.sub:
            ret.append(self.walk(val, **kwargs))
        return "\\sum_" + ','.join(ret) + " " + self.walk(node.exp, **kwargs)

    def walk_SingleValueModel(self, node, **kwargs):
        return self.walk(node.value, **kwargs)

    def walk_Subexpression(self, node, **kwargs):
        return '(' + self.walk(node.value, **kwargs) + ')'

    def walk_Matrix(self, node, **kwargs):
        return '\\begin{bmatrix}\n' + self.walk(node.value, **kwargs) + '\\end{bmatrix}'

    def walk_MatrixRows(self, node, **kwargs):
        ret = []
        for val in node.value:
            ret.append(self.walk(val, **kwargs))
        return ''.join(ret)

    def walk_MatrixRows(self, node, **kwargs):
        ret = []
        if node.rs:
            ret.append(self.walk(node.rs, **kwargs))
        if node.r:
            ret.append(self.walk(node.r, **kwargs))
        return ''.join(ret)

    def walk_MatrixRow(self, node, **kwargs):
        ret = []
        if node.rc:
            ret.append(self.walk(node.rc, **kwargs))
        if node.exp:
            ret.append(self.walk(node.exp, **kwargs))
        return ' & '.join(ret) + "\\\\\n"

    def walk_MatrixRowCommas(self, node, **kwargs):
        ret = []
        if node.value:
            ret.append(self.walk(node.value, **kwargs))
        if node.exp:
            ret.append(self.walk(node.exp, **kwargs))
        return ' & '.join(ret)

    def walk_ExpInMatrix(self, node, **kwargs):
        return self.walk(node.value, **kwargs)

    def walk_Derivative(self, node, **kwargs):
        return "\\partial" + self.walk(value, **kwargs)

    def walk_InnerProduct(self, node, **kwargs):
        return self.walk(left, **kwargs) + " " + self.walk(right, **kwargs)
