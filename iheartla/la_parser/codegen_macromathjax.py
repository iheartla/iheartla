from .codegen import *
from .codegen_mathjax import CodeGenMathjax
from .type_walker import *
from ..la_tools.la_helper import filter_subscript
import regex as re
from textwrap import dedent
import base64


class CodeGenMacroMathjax(CodeGenMathjax):
    def __init__(self):
        super().__init__(ParserTypeEnum.MACROMATHJAX)

    def init_type(self, type_walker, func_name):
        super().init_type(type_walker, func_name)
        self.code_frame.pre_str = self.pre_str
        self.code_frame.post_str = self.post_str

    def convert_content(self, symbol):
        # avoid error in js
        return symbol.replace('\\', "\\\\\\\\").replace('`', '').replace('"', '\\\\"').replace("'", "\\\\'")

    def visit_assignment(self, node, **kwargs):
        sym_list = []
        for sym in node.symbols:
            sym_list.append("'{}'".format(self.convert_content(filter_subscript(sym))))
        sym_list = list(set(sym_list))
        sym_list.append("'{}'".format(self.convert_content(node.left[0].get_main_id())))
        if node.right[0].node_type == IRNodeType.Optimize:
            content = self.visit(node.right[0], **kwargs)
        else:
            self.visiting_lhs = True
            lhs_list = []
            for cur_index in range(len(node.left)):
                lhs_list.append(self.visit(node.left[cur_index], **kwargs))
            self.visiting_lhs = False
            rhs_list = []
            for cur_index in range(len(node.right)):
                rhs_list.append(self.visit(node.right[cur_index], **kwargs))
            content = ','.join(lhs_list) + " & = " + ','.join(rhs_list)
        json = r"""{{"onclick":"event.stopPropagation(); onClickEq(this, '{}', [{}], false, [], [], '{}');"}}""".format(self.func_name, ', '.join(sym_list), base64.urlsafe_b64encode(node.raw_text.encode("utf-8")).decode("utf-8"))
        content = content + "\\\\" + "\\eqlabel{{ {} }}{{}}".format(json) + "\n"
        self.code_frame.expr += content
        self.code_frame.expr_dict[node.raw_text] = content
        return content

    def visit_optimize(self, node, **kwargs):
        assign_node = node.get_ancestor(IRNodeType.Assignment)
        content = super(CodeGenMacroMathjax, self).visit_optimize(node, **kwargs)
        if not assign_node:
            sym_list = []
            for sym in node.symbols:
                sym_list.append("'{}'".format(self.convert_content(filter_subscript(sym))))
            sym_list = list(set(sym_list))
            json = r"""{{"onclick":"event.stopPropagation(); onClickEq(this, '{}', [{}], false, [], [], '{}', false);"}}""".format(
                self.func_name, ', '.join(sym_list),
                base64.urlsafe_b64encode(node.raw_text.encode("utf-8")).decode("utf-8"))
            content = content + "\\\\" + "\\eqlabel{{ {} }}{{}}".format(json) + "\n"
            self.code_frame.expr += content
            self.code_frame.expr_dict[node.raw_text] = content
        return content

    def visit_local_func(self, node, **kwargs):
        self.local_func_parsing = True
        self.visiting_func_name = True
        func_name = self.visit(node.name, **kwargs)
        self.visiting_func_name = False
        self.local_func_name = self.convert_content(filter_subscript(node.name.get_name()))
        params_str = ''
        # raw local params
        local_param_list = []
        if len(node.params) > 0:
            for index in range(len(node.params)):
                local_param_list.append("'{}'".format(self.convert_content(filter_subscript(node.params[index].get_name()))))
                params_str += self.visit(node.params[index], **kwargs)
                if index < len(node.params)-1:
                    params_str += node.separators[index] + ''
        if node.def_type == LocalFuncDefType.LocalFuncDefParenthesis:
            def_params = '\\left( ' + params_str + ' \\right)'
        else:
            def_params = '\\left[ ' + params_str + ' \\right]'
        expr_list = []
        for cur_index in range(len(node.expr)):
            expr_list.append(self.visit(node.expr[cur_index], **kwargs))
        content = func_name + def_params + " & = " + ', '.join(expr_list)
        sym_list = []
        for sym in node.symbols:
            sym_list.append("'{}'".format(self.convert_content(filter_subscript(sym))))
        sym_list = list(set(sym_list))
        sym_list.append("'{}'".format(self.convert_content(node.name.get_main_id())))
        json = r"""{{"onclick":"event.stopPropagation(); onClickEq(this, '{}', [{}], true, '{}', [{}], '{}');"}}""".format(
            self.func_name, ', '.join(sym_list), self.local_func_name, ', '.join(local_param_list), base64.urlsafe_b64encode(node.raw_text.encode("utf-8")).decode("utf-8"))
        saved_content = content + "\\\\" + "\\eqlabel{{ {} }}{{}}".format(json) + "\n"
        self.code_frame.expr += saved_content + '\n'
        self.code_frame.expr_dict[node.raw_text] = saved_content
        if len(node.defs) > 0:
            par_list = []
            for par in node.defs:
                par_list.append(self.visit(par, **kwargs))
            # content += "\\intertext{{{}}} ".format('where') + ', '.join(par_list)
            content += ' \\text{{ where }}  ' + ', '.join(par_list)
            self.local_func_parsing = False
        self.local_func_parsing = True
        return content

    def visit_id(self, node, **kwargs):
        id_str = "{}-{}".format(self.func_name, self.convert_content(node.get_name()))
        sub_str = ''
        if node.contain_subscript():
            subs_list = []
            for subs in node.subs:
                subs_list.append(self.convert_unicode(subs))
            sub_str = '_{' + ','.join(subs_list) + '}'
            content = self.convert_unicode(node.main_id)
        else:
            content = self.convert_unicode(node.get_name())
        if 'is_sub' in kwargs:
            return content + sub_str
        use_type = "use"
        if self.visiting_lhs or self.visiting_func_name:
            use_type = "def"
        local_param = False
        local_func_name = ''
        if self.local_func_parsing:
            local_param = self.is_local_param(node.get_name())
            local_func_name = self.local_func_name
        json = """{{"onclick":"event.stopPropagation(); onClickSymbol(this, '{}', '{}', '{}', {}, '{}')", "id":"{}", "sym":"{}", "func":"{}",  "localFunc":"{}", "type":"{}", "case":"equation"}}""" \
            .format(self.convert_content(node.get_main_id()), self.func_name, use_type, 'true' if local_param else 'false', local_func_name, id_str, self.convert_content(node.get_main_id()), self.func_name, local_func_name, use_type)
        content = "\\idlabel{{ {} }}{{ {{{}}} }}".format(json, content)
        return content + sub_str


