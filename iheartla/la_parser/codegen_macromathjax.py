from .codegen import *
from .codegen_mathjax import CodeGenMathjax
from .type_walker import *
import regex as re
from textwrap import dedent


class CodeGenMacroMathjax(CodeGenMathjax):
    def __init__(self):
        super().__init__(ParserTypeEnum.MACROMATHJAX)
        self.BLOCK_RE = re.compile(
                dedent(r'''(?P<main>(`[^`]*`)|([A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*)?)(\_)(?P<sub>(`[^`]*`)|([A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*)?)'''),
                re.MULTILINE | re.DOTALL | re.VERBOSE
            )

    def init_type(self, type_walker, func_name):
        super().init_type(type_walker, func_name)
        self.code_frame.pre_str = self.pre_str
        self.code_frame.post_str = self.post_str

    def filter_subscript(self, symbol):
        # x_i to x
        m = self.BLOCK_RE.fullmatch(symbol)
        if m:
            main = m.group('main')
            return main
        return symbol

    def convert_content(self, symbol):
        # avoid error in js
        return symbol.replace('\\', "\\\\\\\\").replace('`', '')

    def visit_assignment(self, node, **kwargs):
        sym_list = ''
        for sym in node.symbols:
            sym_list += "'{}'".format(self.convert_content(self.filter_subscript(sym))) + ','
        sym_list += "'{}'".format(self.convert_content(node.left.get_main_id()))
        content = ''
        if node.right.node_type == IRNodeType.Optimize:
            content = self.visit(node.right, **kwargs)
        else:
            self.visiting_lhs = True
            left_content = self.visit(node.left, **kwargs)
            self.visiting_lhs = False
            content = left_content + " & = " + self.visit(node.right, **kwargs)
        json = r"""{{"onclick":"event.stopPropagation(); onClickEq(this, '{}', [{}]);"}}""".format(self.func_name, sym_list)
        content = content + "\\\\" + "\\eqlabel{{ {} }}{{}}".format(json) + "\n"
        self.code_frame.expr += content
        self.code_frame.expr_dict[node.raw_text] = content
        return content

    def visit_local_func(self, node, **kwargs):
        params_str = ''
        if len(node.params) > 0:
            for index in range(len(node.params)):
                params_str += self.visit(node.params[index], **kwargs)
                if index < len(node.params)-1:
                    params_str += node.separators[index] + ''
        if node.def_type == LocalFuncDefType.LocalFuncDefParenthesis:
            def_params = '\\left( ' + params_str + ' \\right)'
        else:
            def_params = '\\left[ ' + params_str + ' \\right]'
        content = self.visit(node.name, **kwargs) + def_params + " & = " + self.visit(node.expr, **kwargs)
        sym_list = ''
        for sym in node.symbols:
            sym_list += "'{}'".format(self.convert_content(self.filter_subscript(sym))) + ','
        sym_list += "'{}'".format(self.convert_content(node.name.get_main_id()))
        json = r"""{{"onclick":"event.stopPropagation(); onClickEq(this, '{}', [{}]);"}}""".format(self.func_name,
                                                                                                   sym_list)
        saved_content = content + "\\\\" + "\\eqlabel{{ {} }}{{}}".format(json) + "\n"
        self.code_frame.expr += saved_content + '\n'
        self.code_frame.expr_dict[node.raw_text] = saved_content
        if len(node.defs) > 0:
            self.local_func_parsing = True
            par_list = []
            for par in node.defs:
                par_list.append(self.visit(par, **kwargs))
            # content += "\\intertext{{{}}} ".format('where') + ', '.join(par_list)
            content += ' \\text{{ where }}  ' + ', '.join(par_list)
            self.local_func_parsing = False
        return content

    def visit_id(self, node, **kwargs):
        id_str = "{}-{}".format(self.func_name, self.convert_content(node.get_name()))
        if node.contain_subscript():
            subs_list = []
            for subs in node.subs:
                subs_list.append(self.convert_unicode(subs))
            content = self.convert_unicode(node.main_id) + '_{' + ','.join(subs_list) + '}'
        else:
            content = self.convert_unicode(node.get_name())
        json = """{{"onclick":"event.stopPropagation(); onClickSymbol(this, '{}','{}', '{}')", "id":"{}", "sym":"{}", "func":"{}", "type":"{}", "case":"equation"}}""" \
            .format(self.convert_content(node.get_name()), self.func_name, "def" if self.visiting_lhs else "use", id_str, self.convert_content(node.get_name()), self.func_name, "def" if self.visiting_lhs else "use")
        content = "\\idlabel{{ {} }}{{ {{{}}} }}".format(json, content)
        return content


