from la_parser.codegen import *
from la_parser.type_walker import *


class CodeGenLatex(CodeGen):
    def __init__(self):
        super().__init__(ParserTypeEnum.LATEX)
        self.pre_str = '''\\documentclass[12pt]{article}\n\\usepackage{mathdots}\n\\usepackage[bb=boondox]{mathalfa}\n\\usepackage{mathtools}\n\\usepackage{amssymb}\n\\usepackage{ctex}\n\\setmainfont{Linux Libertine O}\n\\begin{document}\n\\[\n'''
        self.post_str = '''\n\end{document}'''

    def convert_unicode(self, name):
        if '`' not in name:
            return name
        text = name.replace('`', '')
        special_list = ['_', '&', '^', '%', '$', '#', '{', '}']
        text = text.replace('\\', '\\textbackslash{}')
        for special in special_list:
            text = text.replace(special, '\\{}'.format(special))
        value = "\\textit{{{}}}".format(text)
        return value

    def visit_id(self, node, **kwargs):
        if node.contain_subscript():
            subs_list = []
            for subs in node.subs:
                subs_list.append(self.convert_unicode(subs))
            return self.convert_unicode(node.main_id) + '_{' + ','.join(subs_list) + '}'
        return self.convert_unicode(node.get_name())

    def visit_MatrixVdots(self, node, **kwargs):
        return "\\vdots"

    def visit_MatrixCdots(self, node, **kwargs):
        return "\\cdots"

    def visit_MatrixIddots(self, node, **kwargs):
        return "\\iddots"

    def visit_MatrixDdots(self, node, **kwargs):
        return "\\ddots"

    def visit_factor(self, node, **kwargs):
        if node.id:
            return self.visit(node.id, **kwargs)
        elif node.num:
            return self.visit(node.num, **kwargs)
        elif node.sub:
            return self.visit(node.sub, **kwargs)
        elif node.m:
            return self.visit(node.m, **kwargs)
        elif node.nm:
            return self.visit(node.nm, **kwargs)
        elif node.op:
            return self.visit(node.op, **kwargs)
        elif node.s:
            return self.visit(node.s, **kwargs)

    def visit_double(self, node):
        return str(node.value)

    def visit_integer(self, node):
        return str(node.value)

    def visit_IdentifierSubscript(self, node, **kwargs):
        right = []
        for value in node.right:
            right.append(self.visit(value, **kwargs))
        return self.visit(node.left, **kwargs) + '_{' + ','.join(right) + '}'

    def visit_IdentifierAlone(self, node, **kwargs):
        if node.value:
            value = node.value
        else:
            special_list = ['_', '&', '^', '%', '$', '#', '{', '}']
            text = node.id
            text = text.replace('\\', '\\textbackslash{}')
            for special in special_list:
                text = text.replace(special, '\\{}'.format(special))
            value = "\\textit{{{}}}".format(text)
        return value

    def visit_start(self, node, **kwargs):
        return self.visit(node.stat, **kwargs) + "\n\\]\n\nwhere\n\n\\begin{itemize}\n" + self.visit(node.cond,
                                                                                                   **kwargs) + '\\end{itemize}\n'

    def visit_block(self, node, **kwargs):
        ret = []
        for stmt in node.stmts:
            ret.append(self.visit(stmt, **kwargs))
        return '\\]\n\\[\n'.join(ret)

    def visit_where_conditions(self, node, **kwargs):
        ret = []
        for val in node.value:
            ret.append(self.visit(val, **kwargs))
        return ''.join(ret)

    def visit_where_condition(self, node, **kwargs):
        id0 = self.visit(node.id, **kwargs)
        type_content = self.visit(node.type, **kwargs)
        content = "\\item ${} \\in {}".format(id0, type_content)
        if node.desc:
            content += ":${}\n".format(node.desc)
        else:
            content += "$\n"
        return content

    def visit_matrix_type(self, node, **kwargs):
        id1 = self.visit(node.id1, **kwargs)
        id2 = self.visit(node.id2, **kwargs)
        type_str = '\\mathbb{R}'
        if node.type == 'ℤ':
            type_str = '\\mathbb{Z}'
        content = "{}^{{ {} \\times {} }}".format(type_str, id1, id2)
        return content

    def visit_vector_type(self, node, **kwargs):
        id1 = self.visit(node.id1, **kwargs)
        type_str = '\\mathbb{R}'
        if node.type == 'ℤ':
            type_str = '\\mathbb{Z}'
        content = "{}^{{ {}}}".format(type_str, id1)
        return content

    def visit_scalar_type(self, node, **kwargs):
        content = "\\mathbb{{R}}"
        if node.is_int:
            content = "\\mathbb{{Z}}"
        return content

    def visit_set_type(self, node, **kwargs):
        content = ''
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
            cnt = self.visit(node.cnt, **kwargs)
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
        return content

    def visit_function_type(self, node, **kwargs):
        params = []
        if node.params:
            for param in node.params:
                params.append(self.visit(param, **kwargs))
        ret = self.visit(node.ret, **kwargs)
        if len(params) == 0:
            params_str = '\\varnothing'
        else:
            params_str = ', '.join(params)
        return params_str + '\\rightarrow ' + ret

    def visit_assignment(self, node, **kwargs):
        return self.visit(node.left, **kwargs) + " = " + self.visit(node.right, **kwargs)

    def visit_expression(self, node, **kwargs):
        value = self.visit(node.value, **kwargs)
        if node.sign:
            value = node.sign + value
        return value

    def visit_add(self, node, **kwargs):
        return self.visit(node.left, **kwargs) + " + " + self.visit(node.right, **kwargs)

    def visit_sub(self, node, **kwargs):
        return self.visit(node.left, **kwargs) + " - " + self.visit(node.right, **kwargs)

    def visit_add_sub(self, node, **kwargs):
        return self.visit(node.left, **kwargs) + " \\pm " + self.visit(node.right, **kwargs)

    def visit_mul(self, node, **kwargs):
        return self.visit(node.left, **kwargs) + " \\cdot " + self.visit(node.right, **kwargs)

    def visit_div(self, node, **kwargs):
        return "\\frac{" + self.visit(node.left, **kwargs) + "}{" + self.visit(node.right, **kwargs) + "}"

    def visit_summation(self, node, **kwargs):
        if node.cond:
            sub = '{' + self.visit(node.cond, **kwargs) + '}'
        else:
            sub = self.visit(node.sub)
        return "\\sum_" + sub + " " + self.visit(node.exp, **kwargs)

    def visit_function(self, node, **kwargs):
        params = []
        if node.params:
            for param in node.params:
                params.append(self.visit(param, **kwargs))
        return self.visit(node.name, **kwargs) + '(' + ', '.join(params) + ')'

    def visit_if(self, node, **kwargs):
        ret_info = self.visit(node.cond)
        # ret_info = "if " + ret_info + ":\n"
        return ret_info

    def visit_in(self, node, **kwargs):
        item_list = []
        for item in node.items:
            item_info = self.visit(item, **kwargs)
            item_list.append(item_info)
        right_info = self.visit(node.set, **kwargs)
        return '({}) \\in {} '.format(', '.join(item_list), right_info)

    def visit_not_in(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return left_info + 'not in' + right_info

    def visit_bin_comp(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return left_info + ' {} '.format(self.get_bin_comp_str(node.comp_type)) + right_info

    def visit_sub_expr(self, node, **kwargs):
        return '(' + self.visit(node.value, **kwargs) + ')'

    def visit_sparse_matrix(self, node, **kwargs):
        if node.id1:
            id1_info = self.visit(node.id1, **kwargs)
            id2_info = self.visit(node.id2, **kwargs)
        ifs = self.visit(node.ifs, **kwargs)
        if node.other:
            other = self.visit(node.other, **kwargs)
            content = '{} {} {} & otherwise {}'.format("\\begin{cases}", ifs, other, "\\end{cases}")
        else:
            content = '{} {} {} '.format("\\begin{cases}", ifs, "\\end{cases}")
        return content

    def visit_sparse_ifs(self, node, **kwargs):
        content = ''
        for cond in node.cond_list:
            content += (self.visit(cond, **kwargs) + " \\\\")
        return content

    def visit_sparse_if(self, node, **kwargs):
        stat_info = self.visit(node.stat, **kwargs)
        cond_info = self.visit(node.cond, **kwargs)
        return '{} & \\text{{if}}  {}'.format(stat_info, cond_info)

    def visit_sparse_other(self, node, **kwargs):
        content = ''
        return CodeNodeInfo('    '.join(content))

    def visit_num_matrix(self, node, **kwargs):
        id1_info = self.visit(node.id1, **kwargs)
        if node.id:
            content = "I_{{ {} }}".format(id1_info)
        else:
            content = "\\mathbb{{ {} }}".format(node.left)
            if node.id2:
                id2_info = self.visit(node.id2, **kwargs)
                content = "{}_{{ {},{} }}".format(content, id1_info, id2_info)
            else:
                content = "{}_{{ {} }}".format(content, id1_info)
        return content

    def visit_matrix(self, node, **kwargs):
        return '\\begin{bmatrix}\n' + self.visit(node.value, **kwargs) + '\\end{bmatrix}'

    def visit_MatrixRows(self, node, **kwargs):
        ret = []
        for val in node.value:
            ret.append(self.visit(val, **kwargs))
        return ''.join(ret)

    def visit_matrix_rows(self, node, **kwargs):
        ret = []
        if node.rs:
            ret.append(self.visit(node.rs, **kwargs))
        if node.r:
            ret.append(self.visit(node.r, **kwargs))
        return ''.join(ret)

    def visit_matrix_row(self, node, **kwargs):
        ret = []
        if node.rc:
            ret.append(self.visit(node.rc, **kwargs))
        if node.exp:
            ret.append(self.visit(node.exp, **kwargs))
        return ' & '.join(ret) + "\\\\\n"

    def visit_matrix_row_commas(self, node, **kwargs):
        ret = []
        if node.value:
            ret.append(self.visit(node.value, **kwargs))
        if node.exp:
            ret.append(self.visit(node.exp, **kwargs))
        return ' & '.join(ret)

    def visit_exp_in_matrix(self, node, **kwargs):
        value = self.visit(node.value, **kwargs)
        if node.sign:
            value = node.sign + value
        return value

    def visit_power(self, node, **kwargs):
        base_info = self.visit(node.base, **kwargs)
        if node.t:
            base_info = "{}^T".format(base_info)
        elif node.r:
            base_info = base_info + "^{-1}"
        else:
            power_info = self.visit(node.power, **kwargs)
            base_info = base_info + '^' + power_info
        return base_info

    def visit_solver(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return left_info + ' \setminus ' + right_info

    def visit_norm(self, node, **kwargs):
        if node.value.la_type.var_type == VarTypeEnum.SCALAR:
            return "|{}|".format(self.visit(node.value, **kwargs))
        return "\\|{}\\|".format(self.visit(node.value, **kwargs))

    def visit_transpose(self, node, **kwargs):
        return self.visit(node.f, **kwargs)

    def visit_derivative(self, node, **kwargs):
        return "\\partial" + self.visit(value, **kwargs)

    def visit_inner_product(self, node, **kwargs):
        return self.visit(left, **kwargs) + " " + self.visit(right, **kwargs)
