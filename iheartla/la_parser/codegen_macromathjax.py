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
        content = ''
        if node.right.node_type == IRNodeType.Optimize:
            content = self.visit(node.right, **kwargs)
        else:
            content = self.visit(node.left, **kwargs) + " & = " + self.visit(node.right, **kwargs)
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


