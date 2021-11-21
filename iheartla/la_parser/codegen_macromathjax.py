from .codegen import *
from .codegen_mathjax import CodeGenMathjax
from .type_walker import *


class CodeGenMacroMathjax(CodeGenMathjax):
    def __init__(self):
        super().__init__(ParserTypeEnum.MACROMATHJAX)

    def init_type(self, type_walker, func_name):
        super().init_type(type_walker, func_name)
        self.code_frame.pre_str = self.pre_str
        self.code_frame.post_str = self.post_str

    def visit_assignment(self, node, **kwargs):
        sym_list = ''
        for sym in node.symbols:
            sym_list += "'{}'".format(sym) + ','
        sym_list += "'{}'".format(node.left.get_main_id())
        content = ''
        if node.right.node_type == IRNodeType.Optimize:
            content = self.visit(node.right, **kwargs)
        else:
            content = self.visit(node.left, **kwargs) + " & = " + self.visit(node.right, **kwargs)
        json = r"""{{"onclick":"event.stopPropagation(); onClickEq(this, '{}', [{}]);"}}""".format(self.func_name, sym_list)
        content = "\\arialabel{{ {} }}{{ {} }}".format(json, content)
        self.code_frame.expr += content + "\\\\\n"
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
        self.code_frame.expr += content + '\n'
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
        id_str = "{}-{}".format(self.func_name, node.get_name())
        if node.contain_subscript():
            subs_list = []
            for subs in node.subs:
                subs_list.append(self.convert_unicode(subs))
            content = self.convert_unicode(node.main_id) + '_{' + ','.join(subs_list) + '}'
        else:
            content = self.convert_unicode(node.get_name())
        json = """{{"onclick":"event.stopPropagation(); onClickSymbol(this, '{}','{}')", "id":"{}", "sym":"{}"}}""" \
            .format(node.get_name(), self.func_name, id_str, node.get_name())
        content = "\\arialabel{{ {} }}{{ {} }}".format(json, content)
        return content


