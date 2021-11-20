from .codegen import *
from .codegen_latex import CodeGenLatex
from .type_walker import *


class CodeGenMathjax(CodeGenLatex):
    def __init__(self, parse_type=ParserTypeEnum.MATHJAX):
        super().__init__(parse_type)

    def init_type(self, type_walker, func_name):
        super().init_type(type_walker, func_name)
        self.uni_convert_dict = {}
        self.pre_str = r'''
\DeclareMathOperator*{\argmax}{arg\,max}
\DeclareMathOperator*{\argmin}{arg\,min}
\begin{align*}
'''[1:]
        self.post_str = r'''
\end{align*}
'''[1:]
        self.code_frame.include = self.pre_str
        self.code_frame.rand_data = self.post_str

    def visit_start(self, node, **kwargs):
        content = ""
        # for directive in node.directives:
        #     content += self.visit(directive, **kwargs)
        pre_param = False
        pre_exp = False
        # pre_align = "\\begin{center}\n\\resizebox{\\linewidth}{!}{\n\\begin{minipage}[c]{\\linewidth}\n"
        # post_align = "\\end{minipage}\n}\n\\end{center}\n"
        pre_align = ""
        post_align = ""
        for vblock in node.vblock:
            if vblock.node_type != IRNodeType.ParamsBlock:
                if pre_param or (not pre_param and not pre_exp):
                    content += pre_align
                    # content += "\\begin{align*}\n"
                # elif pre_exp:
                #     content += " \\\\\n"
                block_content = self.visit(vblock, **kwargs)
                if vblock.node_type != IRNodeType.Assignment:
                    # single expression
                    block_content = " & " + block_content
                content += block_content + " \\\\\n"
            else:
                # params
                if not (not pre_param and not pre_exp) and not vblock.annotation:
                    # params block without 'where'
                    content += "\\\\\n"
                if pre_exp:
                    # content += "\n\\end{align*}\n"
                    content += post_align
                content += self.visit(vblock, **kwargs)
            pre_param = vblock.node_type == IRNodeType.ParamsBlock
            pre_exp = vblock.node_type != IRNodeType.ParamsBlock
        if pre_exp:
            # content += "\n\\end{align*}\n"
            content += post_align
        # handle unicode special characters
        for key, value in self.uni_convert_dict.items():
            if key in content:
                content = content.replace(key, value)
        self.code_frame.main = self.pre_str + content + self.post_str
        return content

    def visit_params_block(self, node, **kwargs):
        content = self.visit(node.conds, **kwargs)
        if node.annotation:
            content = "{} \\\\".format(node.annotation) + "\n" + content
        content += "\\\\\n"
        return content