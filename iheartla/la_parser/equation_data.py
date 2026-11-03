"""
What a compile tells H❤️rtDown about a program's symbols: its parameters, definitions, local functions and imports,
their types and descriptions, and the symbols each definition relates. Both compilers produce it: the Python compiler's
type walker, and the Rust compiler through rust_heartdown.py.
"""
import copy
from ..la_tools.la_helper import filter_subscript, base64_encode


class DependenceData(object):
    def __init__(self, module='', initialized_list=[], name_list=[]):
        self.module = module
        self.name_list = name_list
        self.initialized_list = initialized_list



class EquationData(object):
    def __init__(self, name='', parameters=[], definition=[], dependence=[], symtable={}, desc_dict={}, la_content='', func_data_dict={}, expr_dict={}, opt_syms=[]):
        self.name = name
        self.undescribed_list = []
        self.parameters = parameters  # parameters for source file
        self.definition = definition  # lhs symbols
        self.dependence = dependence
        self.symtable = symtable
        self.desc_dict = desc_dict
        self.original_desc_dict = copy.deepcopy(desc_dict)
        self.la_content = la_content
        self.func_data_dict = func_data_dict
        self.opt_syms = opt_syms
        self.expr_dict = {}
        # for key in self.desc_dict.keys():
        #     self.desc_dict[key] = self.desc_dict[key].replace('"', '\"')
        # remove subscript in symbol
        for key, value in expr_dict.items():
            self.expr_dict[key] = [filter_subscript(val) for val in value]
        # gather all symbols: params, definitions, local func names, local params
        self.sym_list = list(self.parameters) + list(self.definition) + list(self.opt_syms)
        for key, value in self.func_data_dict.items():
            self.sym_list.append(key)
            self.sym_list += list(value.params_data.symtable.keys())
        for dep_data in self.dependence:
            self.sym_list += dep_data.name_list
        self.sym_list = list(set(self.sym_list))
        #
        self.generated_list = copy.deepcopy(self.sym_list)
        self.generated_list = [sym.replace('`$', '').replace('$`', '').replace('`', '') for sym in self.generated_list]
        #
        self.generated_list = list(set(self.generated_list))
        self.subset_dict = {}
        # for i in range(len(self.generated_list)):
        #     for j in range(len(self.generated_list)):
        #         if i != j and self.generated_list[i] in self.generated_list[j]:
        #             PROSE_RE = re.compile(
        #                 dedent(r'''(?<!(    # negative begins
        #                                             (\\(proselabel|prosedeflabel)({{([a-z0-9\p{{Ll}}\p{{Lu}}\p{{Lo}}\p{{M}}\s]+)}})?{{([a-z\p{{Ll}}\p{{Lu}}\p{{Lo}}\p{{M}}_{{()\s]*)))
        #                                             |
        #                                             ([a-zA-Z]+)
        #                                             ) # negative ends
        #                                             ({})
        #                                             (?![a-zA-Z]+)'''.format(self.escape_sym(self.generated_list[i]))),
        #                 re.MULTILINE | re.DOTALL | re.VERBOSE
        #             )
        #             for target in PROSE_RE.finditer(self.generated_list[j]):
        #                 if self.generated_list[i] not in self.subset_dict:
        #                     self.subset_dict[self.generated_list[i]] = [self.generated_list[j]]
        #                 else:
        #                     self.subset_dict[self.generated_list[i]].append(self.generated_list[j])
        #                 break
        self.generated_list = sorted(self.generated_list, key=len, reverse=True)
        # print("subset_dict:")
        # for key, value in self.subset_dict.items():
        #     print("{} : {}".format(key, value))

    def reset_desc_dict(self):
        self.desc_dict = copy.deepcopy(self.original_desc_dict)

    def escape_sym(self, sym):
        """
        Escape special characters in regular expression
        """
        escape_list = ['\\', '(', ')', '{', '}', '^', '+', '-', '.', '*', ' ']
        for es in escape_list:
            sym = sym.replace(es, '\\' + es)
        return sym

    def trim(self, content):
        # print("before:{}, after:{}".format(content, content.replace('"', '\\"').replace("'", "\\'")))
        # content = content.replace('"', '\\"').replace("'", "\\'")
        content = content.replace('\\', '\\\\\\\\').replace('"', '\\"').replace("'", "\\'")
        return content

    def gen_json_content(self):
        content = ''
        undesc_list = ['''"{}"'''.format(self.trim(sym)) for sym in sorted(self.undescribed_list)]
        param_list = []
        for param in self.parameters:
            if param in self.desc_dict:
                param_list.append('''{{"sym":"{}", "type_info":{}, "desc":"{}"}}'''.format(self.trim(param), self.symtable[param].get_json_content(), base64_encode(self.desc_dict[param])))
            else:
                param_list.append('''{{"sym":"{}", "type_info":{}}}'''.format(self.trim(param), self.symtable[param].get_json_content()))
        def_list = []
        for lhs in self.definition:
            if lhs in self.desc_dict:
                def_list.append('''{{"sym":"{}", "type_info":{}, "desc":"{}"}}'''.format(self.trim(lhs), self.symtable[lhs].get_json_content(), base64_encode(self.desc_dict[lhs])))
            else:
                def_list.append('''{{"sym":"{}", "type_info":{}}}'''.format(self.trim(lhs), self.symtable[lhs].get_json_content()))
        for opt_var in self.opt_syms:
            if opt_var not in self.parameters and opt_var not in self.definition:
                if opt_var in self.desc_dict:
                    def_list.append('''{{"sym":"{}", "type_info":{}, "desc":"{}"}}'''.format(self.trim(opt_var),
                                                                                             self.symtable[
                                                                                                 opt_var].get_json_content(),
                                                                                             base64_encode(
                                                                                                 self.desc_dict[opt_var])))
                else:
                    def_list.append('''{{"sym":"{}", "type_info":{}}}'''.format(self.trim(opt_var),
                                                                                self.symtable[opt_var].get_json_content()))
        # module dependence, get the sym info
        dependence_list = []
        for dep_data in self.dependence:
            sym_list = []
            init_list = []
            for param in dep_data.initialized_list:
                init_list.append('"{}"'.format(param))
            for sym in dep_data.name_list:
                if sym in self.desc_dict:
                    sym_list.append('''{{"sym":"{}", "type_info":{}, "desc":"{}"}}'''.format(self.trim(sym),
                                                                                             self.symtable[
                                                                                                 sym].get_json_content(),
                                                                                             base64_encode(self.desc_dict[sym])))
                else:
                    sym_list.append('''{{"sym":"{}", "type_info":{}}}'''.format(self.trim(sym),
                                                                                self.symtable[sym].get_json_content()))
            dependence_list.append('''{{"module":"{}", "syms":[{}], "initialization":[{}]}}'''.format(dep_data.module, ','.join(sym_list), ','.join(init_list)))
        #
        func_list = []
        for k, v in self.func_data_dict.items():
            if k in self.desc_dict:
                def_list.append('''{{"sym":"{}", "type_info":{}, "desc":"{}"}}'''.format(self.trim(k), self.symtable[k].get_json_content(), base64_encode(self.desc_dict[k])))
            else:
                def_list.append('''{{"sym":"{}", "type_info":{}}}'''.format(self.trim(k), self.symtable[k].get_json_content()))
            local_param_list = []
            for local_param in v.params_data.parameters:
                if local_param in self.desc_dict:
                    local_param_list.append('''{{"sym":"{}", "type_info":{}, "desc":"{}"}}'''.format(self.trim(local_param), v.params_data.symtable[local_param].get_json_content(), base64_encode(self.desc_dict[local_param])))
                else:
                    local_param_list.append('''{{"sym":"{}", "type_info":{}}}'''.format(self.trim(local_param), v.params_data.symtable[local_param].get_json_content()))
            func_list.append('''{{"name":"{}", "parameters":[{}]}}'''.format(self.trim(k), ','.join(local_param_list)))
        # self.la_content = self.la_content.replace('\n', '\\\\n')
        content = '''"parameters":[{}], "definition":[{}], "local_func":[{}], "dependence":[{}], "undesc_list":[{}]'''.format(','.join(param_list), ','.join(def_list), ','.join(func_list), ','.join(dependence_list), ','.join(undesc_list))
        # content = content.replace('\\', '\\\\\\\\')
        content = content.replace('\n', '\\\\n')
        content = content.replace('`', '')
        # content = content.replace('\\\\\\\\"', '\\\\"')
        # content = content.replace("\\\\\\\\'", "\\\\'")
        # content = content.replace('"', '\\"').replace("'", "\\'")
        # print("content:{}".format(content))
        # content += ''', "source":"{}"'''.format(self.trim(self.la_content).replace('\\', '\\\\\\\\').replace('\n', '\\\\n'))   # IHLA source code
        return content
