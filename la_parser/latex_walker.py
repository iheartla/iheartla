from la_parser.base_walker import *


class LatexWalker(BaseNodeWalker):
    def __init__(self):
        super().__init__(ParserTypeEnum.LATEX)
        self.pre_str = '''\\documentclass[12pt]{article}\n\\usepackage{mathdots}\n\\usepackage[bb=boondox]{mathalfa}\n\\usepackage{mathtools}\n\\usepackage{amssymb}\n\\begin{document}\n\\[\n'''
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
        return self.walk(node.left, **kwargs) + '_{' + ','.join(right) + '}'

    def walk_IdentifierAlone(self, node, **kwargs):
        if node.value:
            value = node.value
        else:
            value = '`' + node.id + '`'
        return value

    def walk_Start(self, node, **kwargs):
        return self.walk(node.stat, **kwargs) + "\n\\]\n\nwhere\n\n\\begin{itemize}\n" + self.walk(node.cond, **kwargs) + '\\end{itemize}\n'

    def walk_Statements(self, node, **kwargs):
        ret = []
        if node.stats:
            ret.append(self.walk(node.stats, **kwargs))
        ret.append(self.walk(node.stat, **kwargs))
        return '\\]\n\\[\n'.join(ret)

    def walk_WhereConditions(self, node, **kwargs):
        ret = []
        for val in node.value:
            ret.append(self.walk(val, **kwargs))
        return ''.join(ret)

    def walk_MatrixCondition(self, node, **kwargs):
        id0 = self.walk(node.id, **kwargs)
        id1 = self.walk(node.id1, **kwargs)
        id2 = self.walk(node.id2, **kwargs)
        type_str = '\\mathbb{R}'
        if node.type == 'ℤ':
            type_str = '\\mathbb{Z}'
        content = "\\item ${} \\in {}^{{ {} \\times {} }}".format(id0, type_str, id1, id2)
        if node.desc:
            desc = self.walk(node.desc, **kwargs)
            content += ":${}\n".format(desc)
        else:
            content += "$\n"
        return content

    def walk_VectorCondition(self, node, **kwargs):
        id0 = self.walk(node.id, **kwargs)
        id1 = self.walk(node.id1, **kwargs)
        type_str = '\\mathbb{R}'
        if node.type == 'ℤ':
            type_str = '\\mathbb{Z}'
        content = "\\item ${} \\in {}^{{ {}}}".format(id0, type_str, id1)
        if node.desc:
            desc = self.walk(node.desc, **kwargs)
            content += ":${}\n".format(desc)
        else:
            content += "$\n"
        return content

    def walk_ScalarCondition(self, node, **kwargs):
        id0 = self.walk(node.id, **kwargs)
        content = "\\item ${} \\in \\mathbb{{R}}".format(id0)
        if node.desc:
            desc = self.walk(node.desc, **kwargs)
            content += ":${}\n".format(desc)
        else:
            content += "$\n"
        return content

    def walk_SetCondition(self, node, **kwargs):
        id0 = self.walk(node.id, **kwargs)
        content = "\\item ${} \\in".format(id0)
        int_list = []
        cnt = 1
        if node.type:
            for t in node.type:
                if t == 'ℤ':
                    int_list.append('\\mathbb{Z}')
                else:
                    int_list.append('\\mathbb{R}')
            content += " \\times ".join(int_list)
        elif node.type1:
            cnt = self.walk(node.cnt, **kwargs)
            if node.type1 == 'ℤ':
                content += '\\mathbb{{Z}}^{{ {} }}'.format(cnt)
            else:
                content += '\\mathbb{{Z}}^{{ {} }}'.format(cnt)
        elif node.type2:
            cnt = 2
            if node.type2 == 'ℤ²':
                content += '\\mathbb{{Z}}^{{2}}'
            else:
                content += '\\mathbb{{Z}}^{{2}}'
        if node.desc:
            desc = self.walk(node.desc, **kwargs)
            content += ":${}\n".format(desc)
        else:
            content += "$\n"
        return content

    def walk_Assignment(self, node, **kwargs):
        return self.walk(node.left, **kwargs) + " = " + self.walk(node.right, **kwargs)

    def walk_Expression(self, node, **kwargs):
        value = self.walk(node.value, **kwargs)
        if node.sign:
            value = node.sign + value
        return value

    def walk_Add(self, node, **kwargs):
        return self.walk(node.left, **kwargs) + " + " + self.walk(node.right, **kwargs)

    def walk_Subtract(self, node, **kwargs):
        return self.walk(node.left, **kwargs) + " - " + self.walk(node.right, **kwargs)

    def walk_AddSub(self, node, **kwargs):
        return self.walk(node.left, **kwargs) + " \\pm " + self.walk(node.right, **kwargs)

    def walk_Multiply(self, node, **kwargs):
        return self.walk(node.left, **kwargs) + " \\cdot " + self.walk(node.right, **kwargs)

    def walk_Divide(self, node, **kwargs):
        return "\\frac{" + self.walk(node.left, **kwargs) + "}{" + self.walk(node.right, **kwargs) + "}"

    def walk_Summation(self, node, **kwargs):
        if node.cond:
            sub = '{' + self.walk(node.cond, **kwargs) + '}'
        else:
            sub = self.walk(node.sub)
        return "\\sum_" + sub + " " + self.walk(node.exp, **kwargs)

    def walk_IfCondition(self, node, **kwargs):
        ret_info = self.walk(node.cond)
        # ret_info = "if " + ret_info + ":\n"
        return ret_info

    def walk_NeCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        return left_info + ' != ' + right_info

    def walk_EqCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        return left_info + ' == ' + right_info

    def walk_InCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        return left_info + ' in ' + right_info

    def walk_NotInCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        return left_info + 'not in' + right_info

    def walk_GreaterCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        return left_info + ' > ' + right_info

    def walk_GreaterEqualCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        return left_info + ' >= ' + right_info

    def walk_LessCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        return left_info + ' < ' + right_info

    def walk_LessEqualCondition(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        return left_info + ' <= ' + right_info

    def walk_SingleValueModel(self, node, **kwargs):
        return self.walk(node.value, **kwargs)

    def walk_Subexpression(self, node, **kwargs):
        return '(' + self.walk(node.value, **kwargs) + ')'

    def walk_SparseMatrix(self, node, **kwargs):
        if node.id1:
            id1_info = self.walk(node.id1, **kwargs)
            id2_info = self.walk(node.id2, **kwargs)
        ifs = self.walk(node.ifs, **kwargs)
        if node.other:
            other = self.walk(node.other, **kwargs)
            content = '{} {} \\\\ {} & otherwise {}'.format("\\begin{cases}", ifs, other, "\\end{cases}")
        else:
            content = '{} {} \\\\ {} '.format("\\begin{cases}", ifs, "\\end{cases}")
        return content

    def walk_SparseIfs(self, node, **kwargs):
        content = ''
        if node.ifs:
            content += self.walk(node.ifs, **kwargs) + "\\\\"
        if node.value:
            content += self.walk(node.value, **kwargs)
        return content

    def walk_SparseIf(self, node, **kwargs):
        id0_info = self.walk(node.id0, **kwargs)
        id1_info = self.walk(node.id1, **kwargs)
        id2_info = self.walk(node.id2, **kwargs)
        stat_info = self.walk(node.stat, **kwargs)
        return '{} & \\text{{if}} ({}, {}) \\in {} '.format(stat_info, id0_info, id1_info, id2_info)

    def walk_SparseOther(self, node, **kwargs):
        content = ''
        return CodeNodeInfo('    '.join(content))

    def walk_NumMatrix(self, node, **kwargs):
        id1_info = self.walk(node.id1, **kwargs)
        if node.id:
            content = "I_{{ {} }}".format(id1_info)
        else:
            content = "\\mathbb{{ {} }}".format(node.left)
            if node.id2:
                id2_info = self.walk(node.id2, **kwargs)
                content = "{}_{{ {},{} }}".format(content, id1_info, id2_info)
            else:
                content = "{}_{{ {} }}".format(content, id1_info)
        return content

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
        value = self.walk(node.value, **kwargs)
        if node.sign:
            value = node.sign + value
        return value

    def walk_Power(self, node, **kwargs):
        base_info = self.walk(node.base, **kwargs)
        if node.t:
            base_info = "{}^T".format(base_info)
        elif node.r:
            base_info = base_info + "^{-1}"
        else:
            power_info = self.walk(node.power, **kwargs)
            base_info = base_info + '^' + power_info
        return base_info

    def walk_Solver(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        return left_info + ' \setminus ' + right_info

    def walk_Transpose(self, node, **kwargs):
        return self.walk(node.f, **kwargs)

    def walk_Derivative(self, node, **kwargs):
        return "\\partial" + self.walk(value, **kwargs)

    def walk_InnerProduct(self, node, **kwargs):
        return self.walk(left, **kwargs) + " " + self.walk(right, **kwargs)
