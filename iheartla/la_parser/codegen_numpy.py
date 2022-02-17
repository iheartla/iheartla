from .codegen import *
from .type_walker import *
import keyword


class CodeGenNumpy(CodeGen):
    def __init__(self):
        super().__init__(ParserTypeEnum.NUMPY)

    def init_type(self, type_walker, func_name):
        super().init_type(type_walker, func_name)
        self.pre_str = '''import numpy as np\nimport scipy\nimport scipy.linalg\nfrom scipy import sparse\n'''
        self.pre_str += "from scipy.integrate import quad\n"
        self.pre_str += "from scipy.optimize import minimize\n"
        self.pre_str += "\n\n"
        self.post_str = ''''''
        self.code_frame.desc = '''"""\n{}\n"""\n'''.format(self.la_content)
        self.code_frame.include = self.pre_str

    def get_dim_check_str(self):
        check_list = []
        if len(self.get_cur_param_data().same_dim_list) > 0:
            check_list = super().get_dim_check_str()
            check_list = ['    assert {} '.format(stat) for stat in check_list]
        return check_list

    def get_arith_dim_check_str(self):
        check_list = []
        if len(self.get_cur_param_data().arith_dim_list) > 0:
            check_list = ['    assert {} == int({})'.format(dims, dims) for dims in self.get_cur_param_data().arith_dim_list]
        return check_list

    def get_rand_test_str(self, la_type, rand_int_max):
        rand_test = ''
        if la_type.is_matrix():
            element_type = la_type.element_type
            if isinstance(element_type, LaVarType) and element_type.is_scalar() and element_type.is_int:
                rand_test = 'np.random.randint({}, size=({}, {}))'.format(rand_int_max, la_type.rows, la_type.cols)
            else:
                rand_test = 'np.random.randn({}, {})'.format(la_type.rows, la_type.cols)
        elif la_type.is_vector():
            element_type = la_type.element_type
            if isinstance(element_type, LaVarType) and element_type.is_scalar() and element_type.is_int:
                rand_test = 'np.random.randint({}, size=({}))'.format(rand_int_max, la_type.rows)
            else:
                rand_test = 'np.random.randn({})'.format(la_type.rows)
        elif la_type.is_scalar():
            rand_test = 'np.random.randn()'
        return rand_test

    def get_func_test_str(self, var_name, func_type, rand_int_max):
        """
        :param var_name: lhs name
        :param func_type: la_type
        :param rand_int_max: 10
        :return:
        """
        test_content = []
        param_list = []
        dim_definition = []
        if func_type.ret_template():
            for ret_dim in func_type.ret_symbols:
                param_i = func_type.template_symbols[ret_dim]
                if func_type.params[param_i].is_vector():
                    dim_definition.append('        {} = {}{}.shape[0]'.format(ret_dim, self.param_name_test, param_i))
                elif func_type.params[param_i].is_matrix():
                    if ret_dim == func_type.params[param_i].rows:
                        dim_definition.append(
                            '        {} = {}{}.shape[0]'.format(ret_dim, self.param_name_test, param_i))
                    else:
                        dim_definition.append(
                            '        {} = {}{}.shape[1]'.format(ret_dim, self.param_name_test, param_i))
        for index in range(len(func_type.params)):
            param_list.append('{}{}'.format(self.param_name_test, index))
        test_content.append("    def {}({}):".format(var_name, ', '.join(param_list)))
        test_content += dim_definition
        if func_type.ret.is_set():
            test_content += self.get_set_test_list('tmp', self.generate_var_name("dim"), 'i', func_type.ret, rand_int_max, '        ')
            test_content.append('        return tmp')
        else:
            test_content.append(
                "        return {}".format(self.get_rand_test_str(func_type.ret, rand_int_max)))
        return test_content

    def get_set_test_list(self, parameter, dim_name, ind_name, la_type, rand_int_max, pre='    '):
        test_content = []
        test_content.append('{} = []'.format(parameter))
        test_content.append('{} = np.random.randint(1, {})'.format(dim_name, rand_int_max))
        test_content.append('for {} in range({}):'.format(ind_name, dim_name))
        gen_list = []
        for i in range(la_type.size):
            if la_type.int_list[i]:
                gen_list.append('np.random.randint({})'.format(rand_int_max))
            else:
                gen_list.append('np.random.randn()')
        test_content.append('    {}.append(('.format(parameter) + ', '.join(gen_list) + '))')
        test_content = ['{}{}'.format(pre, line) for line in test_content]
        return test_content

    def visit_id(self, node, **kwargs):
        content = node.get_name()
        prefix = False
        # if not self.is_local_param(content) and content not in self.parameters and content not in self.local_func_syms:
        # if self.local_func_parsing:
        #     if self.local_func_name != '':
        #         if content not in self.func_data_dict[self.local_func_name].params_data.parameters:
        #             prefix = True
        # else:
        #     if content not in self.main_param.parameters:
        #         prefix = True
        if content in self.lhs_list:
            prefix = True
        elif self.local_func_parsing:
            is_param = False
            if self.local_func_name != '':
                for key, value in self.func_data_dict.items():
                    if content in value.params_data.parameters:
                        is_param = True
                        break
            if not is_param and content in self.used_params:
                prefix = True
        else:
            if len(self.module_list) > 0:
                for module in self.module_list:
                    if len(module.syms) > 0 and content in module.syms:
                        prefix = True
        content = self.filter_symbol(content)
        if content in self.name_convention_dict:
            content = self.name_convention_dict[content]
        if self.convert_matrix and node.contain_subscript():
            if len(node.subs) == 2:
                if self.get_sym_type(node.main_id).is_matrix():
                    if self.get_sym_type(node.main_id).sparse:
                        content = "{}.tocsr()[{}, {}]".format(node.main_id, node.subs[0], node.subs[1])
                    else:
                        content = "{}[{}][{}]".format(node.main_id, node.subs[0], node.subs[1])
        if prefix:
            content = 'self.' + content
        return CodeNodeInfo(content)

    def get_struct_definition(self, def_str, stat_str):
        if stat_str == '':
            stat_str = '        pass\n'
        else:
            stat_str = self.update_prelist_str([stat_str], '    ')
        assign_list = []
        for parameter in self.lhs_list:
            if parameter in self.symtable and self.get_sym_type(parameter) is not None:
                assign_list.append("self.{} = {}".format(parameter, parameter))
        def_struct = ''
        init_struct = ''
        init_var = ''
        if len(self.module_list) > 0:
            for module in self.module_list:
                def_struct += self.update_prelist_str([module.frame.struct], '    ')
                if len(module.params) > 0:
                    init_struct += "        _{} = self.{}({})\n".format(module.name, module.name, ', '.join(module.params))
                else:
                    init_struct += "        _{} = self.{}()\n".format(module.name, module.name)
                for sym in module.syms:
                    init_var += "        self.{} = _{}.{}\n".format(sym, module.name, sym)
        content = ["class {}:".format(self.get_result_type()),
                   "    def __init__(self,{}".format(def_str[3:]),
                   self.get_used_params_content(),
                   ]
        if '' in content:
            content.remove('')
        end_str = self.local_func_def + def_struct
        if end_str != '':
            end_str = '\n' + end_str
        return "\n".join(content) + init_struct + init_var + stat_str + end_str

    def get_ret_struct(self):
        return "{}({})".format(self.get_result_type(), ', '.join(self.lhs_list))

    def gen_same_seq_test(self):
        # dynamic seq
        test_content = []
        visited_sym_set = set()
        rand_int_max = 10
        subs_list = self.get_intersect_list()
        if len(subs_list) > 0:
            rand_name_dict = {}
            rand_def_dict = {}
            for keys in self.get_cur_param_data().seq_dim_dict:
                new_name = self.generate_var_name(keys)
                rand_name_dict[keys] = new_name
                rand_def_dict[keys] = '        {} = np.random.randint({})'.format(new_name, rand_int_max)
            new_seq_dim_dict = self.convert_seq_dim_dict()
            def get_keys_in_set(cur_set):
                keys_list = []
                for sym in cur_set:
                    keys_list += new_seq_dim_dict[sym].values()
                return set(keys_list)
            for sym_set in subs_list:
                visited_sym_set = visited_sym_set.union(sym_set)
                cur_test_content = []
                defined_content = []
                cur_block_content = []
                first = True
                keys_set = get_keys_in_set(sym_set)
                for key in keys_set:
                    cur_block_content.append(rand_def_dict[key])
                for cur_sym in sym_set:
                    if first:
                        first = False
                        cur_test_content.append('    for i in range({}):'.format(self.get_sym_type(cur_sym).size))
                    dim_dict = new_seq_dim_dict[cur_sym]
                    defined_content.append('    {} = []'.format(cur_sym))
                    if self.get_sym_type(cur_sym).element_type.is_vector():
                        # determined
                        if self.get_sym_type(cur_sym).element_type.is_integer_element():
                            cur_block_content.append('        {}.append(np.random.randint({}, size=({})))'.format(cur_sym, rand_int_max, rand_name_dict[dim_dict[1]]))
                        else:
                            cur_block_content.append('        {}.append(np.random.randn({}))'.format(cur_sym, rand_name_dict[dim_dict[1]]))
                    else:
                        # matrix
                        row_str = self.get_sym_type(cur_sym).element_type.rows if not self.get_sym_type(cur_sym).element_type.is_dynamic_row() else rand_name_dict[dim_dict[1]]
                        col_str = self.get_sym_type(cur_sym).element_type.cols if not self.get_sym_type(cur_sym).element_type.is_dynamic_col() else rand_name_dict[dim_dict[2]]
                        if self.get_sym_type(cur_sym).element_type.is_integer_element():
                            cur_block_content.append('        {}.append(np.random.randint({}, size=({}, {})))'.format(cur_sym, rand_int_max, row_str, col_str))
                        else:
                            cur_block_content.append('        {}.append(np.random.randn({}, {}))'.format(cur_sym, row_str, col_str))
                cur_test_content = defined_content + cur_test_content + cur_block_content
                test_content += cur_test_content
        return visited_sym_set, test_content

    def get_used_params_content(self):
        """Copy Parameters that are used in local functions as struct members"""
        assign_list = []
        for param in self.used_params:
            assign_list.append("        self.{} = {}\n".format(param, param))
        return ''.join(assign_list)

    def get_param_content(self, main_content, type_declare, test_generated_sym_set, dim_defined_dict):
        type_checks = []
        rand_func_name = "generateRandomData"
        doc = []
        test_content = []
        test_function = ["def " + rand_func_name + "():"]
        rand_int_max = 10
        #
        par_des_list = []
        test_par_list = []
        for parameter in self.parameters:
            if self.get_sym_type(parameter).desc:
                show_doc = True
                doc.append('    :param :{} :{}'.format(parameter, self.get_sym_type(parameter).desc))
            if self.get_sym_type(parameter).is_sequence():
                ele_type = self.get_sym_type(parameter).element_type
                data_type = ele_type.element_type
                if ele_type.is_matrix() and ele_type.sparse:
                    type_checks.append('    assert {}.shape == ({},)'.format(parameter, self.get_sym_type(parameter).size))
                    type_declare.append('    {} = np.asarray({})'.format(parameter, parameter))
                    test_content.append('    {} = []'.format(parameter))
                    test_content.append('    for i in range({}):'.format(self.get_sym_type(parameter).size))
                    if isinstance(data_type, LaVarType) and data_type.is_scalar() and data_type.is_int:
                        test_content.append(
                            '        {}.append(sparse.random({}, {}, dtype=np.integer, density=0.25))'.format(parameter, ele_type.rows, ele_type.cols))
                    else:
                        test_content.append(
                            '        {}.append(sparse.random({}, {}, dtype=np.float64, density=0.25))'.format(parameter, ele_type.rows,
                                                                                            ele_type.cols))
                else:
                    size_str = ""
                    if ele_type.is_matrix():
                        if not ele_type.is_dynamic():
                            type_checks.append('    assert {}.shape == ({}, {}, {})'.format(parameter, self.get_sym_type(parameter).size, ele_type.rows, ele_type.cols))
                            size_str = '{}, {}, {}'.format(self.get_sym_type(parameter).size, ele_type.rows, ele_type.cols)
                        else:
                            if parameter not in test_generated_sym_set:
                                row_str = 'np.random.randint({})'.format(rand_int_max) if ele_type.is_dynamic_row() else ele_type.rows
                                col_str = 'np.random.randint({})'.format(rand_int_max) if ele_type.is_dynamic_col() else ele_type.cols
                                # size_str = '{}, {}, {}'.format(self.get_sym_type(parameter).size, row_str, col_str)
                                test_content.append('    {} = []'.format(parameter))
                                test_content.append('    for i in range({}):'.format(self.get_sym_type(parameter).size))
                                if ele_type.is_integer_element():
                                    test_content.append('        {}.append(np.random.randint({}, size=({}, {})))'.format(parameter, rand_int_max, row_str, col_str))
                                else:
                                    test_content.append('        {}.append(np.random.randn({}, {}))'.format(parameter, row_str, col_str))
                    elif ele_type.is_vector():
                        # type_checks.append('    assert {}.shape == ({}, {}, 1)'.format(parameter, self.get_sym_type(parameter).size, ele_type.rows))
                        # size_str = '{}, {}, 1'.format(self.get_sym_type(parameter).size, ele_type.rows)
                        if not ele_type.is_dynamic():
                            type_checks.append('    assert {}.shape == ({}, {}, )'.format(parameter, self.get_sym_type(parameter).size, ele_type.rows))
                            size_str = '{}, {}, '.format(self.get_sym_type(parameter).size, ele_type.rows)
                        else:
                            if parameter not in test_generated_sym_set:
                                test_content.append('    {} = []'.format(parameter))
                                test_content.append('    for i in range({}):'.format(self.get_sym_type(parameter).size))
                                if ele_type.is_integer_element():
                                    test_content.append('        {}.append(np.random.randint({}, size=(np.random.randint({}) ,)))'.format(parameter, rand_int_max, rand_int_max))
                                else:
                                    test_content.append('        {}.append(np.random.randn(np.random.randint({})))'.format(parameter, rand_int_max))
                            # size_str = '{}, np.random.randint({}), '.format(self.get_sym_type(parameter).size, rand_int_max)
                    elif ele_type.is_scalar():
                        type_checks.append('    assert {}.shape == ({},)'.format(parameter, self.get_sym_type(parameter).size))
                        size_str = '{}'.format(self.get_sym_type(parameter).size)
                    if isinstance(data_type, LaVarType):
                        if data_type.is_scalar() and data_type.is_int:
                            if ele_type.is_dynamic():
                                type_declare.append('    {} = np.asarray({})'.format(parameter, parameter))
                            else:
                                type_declare.append('    {} = np.asarray({}, dtype=np.int)'.format(parameter, parameter))
                            if parameter not in test_generated_sym_set and not ele_type.is_dynamic():
                                test_content.append('    {} = np.random.randint({}, size=({}))'.format(parameter, rand_int_max, size_str))
                        elif ele_type.is_set():
                            test_content.append('    {} = []'.format(parameter))
                            test_content.append('    for i in range({}):'.format(self.get_sym_type(parameter).size))
                            set_content = self.get_set_test_list("{}_tmp".format(parameter),
                                                                 self.generate_var_name("dim"), 'j', ele_type,
                                                                 rand_int_max, '    ')
                            set_content = ["    {}".format(line) for line in set_content]
                            test_content += set_content
                            test_content.append('        {}.append({})'.format(parameter, "{}_tmp".format(parameter)))
                            test_content.append('    {} = np.asarray({})'.format(parameter, parameter))
                        else:
                            if ele_type.is_dynamic():
                                type_declare.append('    {} = np.asarray({})'.format(parameter, parameter))
                            else:
                                type_declare.append('    {} = np.asarray({}, dtype=np.float64)'.format(parameter, parameter))
                            if parameter not in test_generated_sym_set and not ele_type.is_dynamic():
                                test_content.append('    {} = np.random.randn({})'.format(parameter, size_str))
                    else:
                        if ele_type.is_function():
                            test_content.append('    {} = []'.format(parameter))
                            test_content.append('    for i in range({}):'.format(self.get_sym_type(parameter).size))
                            func_content = self.get_func_test_str("{}_f".format(parameter), ele_type, rand_int_max)
                            func_content = ["    {}".format(line) for line in func_content]
                            test_content += func_content
                            test_content.append('        {}.append({})'.format(parameter, "{}_f".format(parameter)))
                            test_content.append('    {} = np.asarray({})'.format(parameter, parameter))
                        else:
                            if ele_type.is_dynamic():
                                type_declare.append('    {} = np.asarray({})'.format(parameter, parameter))
                            else:
                                type_declare.append('    {} = np.asarray({}, dtype={})'.format(parameter, parameter,
                                                                                               "np.integer" if ele_type.is_integer_element() else "np.float64"))
                            test_content.append('    {} = np.random.randn({})'.format(parameter, size_str))
            elif self.get_sym_type(parameter).is_matrix():
                element_type = self.get_sym_type(parameter).element_type
                if isinstance(element_type, LaVarType):
                    if self.get_sym_type(parameter).sparse:
                        if element_type.is_scalar() and element_type.is_int:
                            test_content.append(
                                '    {} = sparse.random({}, {}, dtype=np.integer, density=0.25)'.format(parameter, self.get_sym_type(parameter).rows,
                                                                          self.get_sym_type(parameter).cols))
                        else:
                            test_content.append(
                                '    {} = sparse.random({}, {}, dtype=np.float64, density=0.25)'.format(parameter, self.get_sym_type(parameter).rows,
                                                                        self.get_sym_type(parameter).cols))
                    else:
                        # dense
                        if element_type.is_scalar() and element_type.is_int:
                            type_declare.append('    {} = np.asarray({}, dtype=np.integer)'.format(parameter, parameter))
                            test_content.append('    {} = np.random.randint({}, size=({}, {}))'.format(parameter, rand_int_max, self.get_sym_type(parameter).rows, self.get_sym_type(parameter).cols))
                        else:
                            type_declare.append('    {} = np.asarray({}, dtype=np.float64)'.format(parameter, parameter))
                            test_content.append('    {} = np.random.randn({}, {})'.format(parameter, self.get_sym_type(parameter).rows, self.get_sym_type(parameter).cols))
                else:
                    if self.get_sym_type(parameter).sparse:
                        test_content.append(
                            '    {} = sparse.random({}, {}, dtype=np.float64, density=0.25)'.format(parameter, self.get_sym_type(parameter).rows,
                                                                      self.get_sym_type(parameter).cols))
                    else:
                        type_checks.append('    {} = np.asarray({})'.format(parameter, parameter))
                        test_content.append('    {} = np.random.randn({}, {})'.format(parameter, self.get_sym_type(parameter).rows, self.get_sym_type(parameter).cols))
                type_checks.append('    assert {}.shape == ({}, {})'.format(parameter, self.get_sym_type(parameter).rows, self.get_sym_type(parameter).cols))
            elif self.get_sym_type(parameter).is_vector():
                element_type = self.get_sym_type(parameter).element_type
                if isinstance(element_type, LaVarType):
                    if element_type.is_scalar() and element_type.is_int:
                        type_declare.append('    {} = np.asarray({}, dtype=np.integer)'.format(parameter, parameter))
                        test_content.append('    {} = np.random.randint({}, size=({}))'.format(parameter, rand_int_max, self.get_sym_type(parameter).rows))
                    else:
                        type_declare.append('    {} = np.asarray({}, dtype=np.float64)'.format(parameter, parameter))
                        test_content.append('    {} = np.random.randn({})'.format(parameter, self.get_sym_type(parameter).rows))
                else:
                    type_declare.append('    {} = np.asarray({})'.format(parameter, parameter))
                    test_content.append('    {} = np.random.randn({})'.format(parameter, self.get_sym_type(parameter).rows))
                type_checks.append('    assert {}.shape == ({},)'.format(parameter, self.get_sym_type(parameter).rows))
                # type_checks.append('    assert {}.shape == ({}, 1)'.format(parameter, self.get_sym_type(parameter).rows))
                # test_content.append('    {} = {}.reshape(({}, 1))'.format(parameter, parameter, self.get_sym_type(parameter).rows))
            elif self.get_sym_type(parameter).is_scalar():
                type_checks.append('    assert np.ndim({}) == 0'.format(parameter))
                if self.get_sym_type(parameter).is_int:
                    test_function.append('    {} = np.random.randint({})'.format(parameter, rand_int_max))
                else:
                    test_function.append('    {} = np.random.randn()'.format(parameter))
            elif self.get_sym_type(parameter).is_set():
                type_declare.append('    {} = frozenset({})'.format(parameter, parameter))
                # type_checks.append('    assert isinstance({}, list) and len({}) > 0'.format(parameter, parameter))
                if self.get_sym_type(parameter).size > 1:
                    type_checks.append('    assert all( len(el) == {} for el in {} )'.format(self.get_sym_type(parameter).size, parameter))
                test_content += self.get_set_test_list(parameter, self.generate_var_name("dim"), 'i', self.get_sym_type(parameter),
                                                       rand_int_max, '    ')
            elif self.get_sym_type(parameter).is_function():
                test_content += self.get_func_test_str(parameter, self.get_sym_type(parameter), rand_int_max)
            main_content.append('    print("{}:", {})'.format(parameter, parameter))
        return type_checks, doc, test_content, test_function, par_des_list, test_par_list


    def gen_dim_content(self, rand_int_max=10):
        test_content = []
        dim_content = ""
        dim_defined_dict = {}
        dim_defined_list = []
        if self.get_cur_param_data().dim_dict:
            for key, target_dict in self.get_cur_param_data().dim_dict.items():
                if key in self.parameters or key in self.get_cur_param_data().dim_seq_set:
                    continue
                target = list(target_dict.keys())[0]
                dim_defined_dict[target] = target_dict[target]
                has_defined = False
                if len(self.get_cur_param_data().same_dim_list) > 0:
                    if key not in dim_defined_list:
                        for cur_set in self.get_cur_param_data().same_dim_list:
                            if key in cur_set:
                                int_dim = self.get_int_dim(cur_set)
                                has_defined = True
                                if int_dim == -1:
                                    test_content.append("    {} = np.random.randint({})".format(key, rand_int_max))
                                else:
                                    test_content.append("    {} = {}".format(key, int_dim))
                                for same_key in cur_set:
                                    if same_key != key:
                                        dim_defined_list.append(same_key)
                                        if not isinstance(same_key, int):
                                            if int_dim == -1:
                                                test_content.append("    {} = {}".format(same_key, key))
                                            else:
                                                test_content.append("    {} = {}".format(same_key, int_dim))
                                break
                    else:
                        has_defined = True
                if not has_defined:
                    test_content.append("    {} = np.random.randint({})".format(key, rand_int_max))
                if self.get_cur_param_data().symtable[target].is_sequence() and \
                        self.get_cur_param_data().symtable[target].element_type.is_dynamic():
                    if target_dict[target] == 0:
                        dim_content += "    {} = {}.shape[0]\n".format(key, target)
                    else:
                        dim_content += "    {} = {}[0].shape[{}]\n".format(key, target, target_dict[target] - 1)
                else:
                    dim_content += "    {} = {}.shape[{}]\n".format(key, target, target_dict[target])
        return dim_defined_dict, test_content, dim_content

    def visit_block(self, node, **kwargs):
        type_declare = []
        show_doc = False
        rand_func_name = "generateRandomData"
        main_content = ["if __name__ == '__main__':"]
        if len(self.parameters) > 0:
            main_content.append("    {} = {}()".format(', '.join(self.parameters), rand_func_name))
        else:
            main_content.append("    {}()".format(rand_func_name))
        # get dimension content
        dim_defined_dict, test_content, dim_content = self.gen_dim_content()
        # Handle sequences first
        test_generated_sym_set, seq_test_list = self.gen_same_seq_test()
        test_content += seq_test_list
        #
        # get params content
        type_checks, doc, param_test_content, test_function, par_des_list, test_par_list = \
            self.get_param_content(main_content, type_declare, test_generated_sym_set, dim_defined_dict)
        #
        test_content += param_test_content
        content = ', '.join(self.parameters) + '):\n'
        if show_doc:
            content += '    \"\"\"\n' + '\n'.join(doc) + '\n    \"\"\"\n'
        # merge content
        if len(type_declare) > 0:
            content += '\n'.join(type_declare) + '\n\n'
        content += dim_content
        type_checks += self.get_dim_check_str()
        type_checks += self.get_arith_dim_check_str()
        if len(type_checks) > 0:
            content += '\n'.join(type_checks) + '\n\n'
        #
        # statements
        stats_content = ""
        for index in range(len(node.stmts)):
            ret_str = ''
            if index == len(node.stmts) - 1:
                if type(node.stmts[index]).__name__ != 'AssignNode':
                    if type(node.stmts[index]).__name__ == 'LocalFuncNode':
                        self.visit(node.stmts[index], **kwargs)
                        continue
                    kwargs[LHS] = self.ret_symbol
                    ret_str = "    self." + self.ret_symbol + ' = '
            else:
                if type(node.stmts[index]).__name__ != 'AssignNode':
                    # meaningless
                    if type(node.stmts[index]).__name__ == 'LocalFuncNode':
                        self.visit(node.stmts[index], **kwargs)
                    continue
            stat_info = self.visit(node.stmts[index], **kwargs)
            if stat_info.pre_list:
                stats_content += "".join(stat_info.pre_list)
            stats_content += ret_str + stat_info.content + '\n'

        # content += stats_content
        # content += '    return ' + self.get_ret_struct()
        # content += '\n'
        content = self.get_struct_definition(self.update_prelist_str([content], '    '), stats_content)
        # content = self.get_struct_definition(self.update_prelist_str([content], '    ')) + '\n'
        # test
        test_function += test_content
        test_function.append('    return {}'.format(', '.join(self.parameters)))
        main_content.append("    func_value = {}({})".format(self.func_name, ', '.join(self.parameters)))
        if self.ret_symbol in self.symtable and self.get_sym_type(self.ret_symbol) is not None:
            main_content.append('    print("return value: ", func_value.{})'.format(self.ret_symbol))
        self.code_frame.main = self.trim_content('\n'.join(main_content))
        self.code_frame.rand_data = self.trim_content('\n'.join(test_function))
        self.code_frame.struct = self.trim_content(content)
        content += '\n\n' + '\n'.join(test_function) + '\n\n\n' + '\n'.join(main_content)
        # convert special string in identifiers
        content = self.trim_content(content)
        return content

    def get_target_name(self, c_var):
        """check whether there's a need to prepend `self.`"""
        content = c_var
        if self.local_func_parsing:
            if c_var not in self.func_data_dict[self.local_func_name].params_data.parameters:
                content = "self.{}".format(c_var)
        else:
            if c_var not in self.main_param.parameters:
                content = "self.{}".format(c_var)
        return content

    def visit_summation(self, node, **kwargs):
        target_var = []
        sub = self.visit(node.id).content
        # name convention
        name_convention = {}
        for var in node.symbols:
            if self.contain_subscript(var):
                var_ids = self.get_all_ids(var)
                var_subs = var_ids[1]
                for var_sub in var_subs:
                    if sub == var_sub:
                        target_var.append(var_ids[0])
                if len(var_ids[1]) > 1:  # matrix
                    name_convention[var] = "{}[{}][{}]".format(var_ids[0], var_ids[1][0], var_ids[1][1])
                else:
                    name_convention[var] = "{}[{}]".format(var_ids[0], var_ids[1][0])
        for sym, subs in node.sym_dict.items():
            target_var.append(sym)
        # try to first use dim of parameters
        target_var = list(set(target_var))
        param_l = []
        remain_l = []
        for cur_v in target_var:
            if cur_v in self.main_param.parameters:
                param_l.append(cur_v)
            else:
                remain_l.append(cur_v)
        target_var = param_l + remain_l
        self.add_name_conventions(name_convention)
        #
        assign_id = node.symbol
        cond_content = ""
        if node.cond:
            cond_info = self.visit(node.cond, **kwargs)
            cond_content = "if(" + cond_info.content + "):\n"
        kwargs[WALK_TYPE] = WalkTypeEnum.RETRIEVE_EXPRESSION
        content = []
        exp_info = self.visit(node.exp)
        exp_str = exp_info.content
        assign_id_type = self.get_sym_type(assign_id)
        if assign_id_type.is_matrix():
            content.append("{} = np.zeros(({}, {}))\n".format(assign_id, assign_id_type.rows, assign_id_type.cols))
        elif assign_id_type.is_vector():
            content.append("{} = np.zeros(({}, ))\n".format(assign_id, assign_id_type.rows))
            # content.append("{} = np.zeros(({}, 1))\n".format(assign_id, self.get_sym_type(assign_id).rows))
        elif assign_id_type.is_sequence():
            ele_type = assign_id_type.element_type
            content.append("{} = np.zeros(({}, {}, {}))\n".format(assign_id, assign_id_type.size, ele_type.rows, ele_type.cols))
        else:
            content.append("{} = 0\n".format(assign_id))
        sym_info = node.sym_dict[target_var[0]]
        if self.get_sym_type(target_var[0]).is_matrix():
            if sub == sym_info[0]:
                content.append("for {} in range(1, {}.shape[0]+1):\n".format(sub, self.get_target_name(self.convert_bound_symbol(target_var[0]))))
            else:
                content.append("for {} in range(1, {}.shape[1]+1):\n".format(sub, self.get_target_name(self.convert_bound_symbol(target_var[0]))))
        elif self.get_sym_type(target_var[0]).is_sequence():
            sym_list = node.sym_dict[target_var[0]]
            sub_index = sym_list.index(sub)
            if sub_index == 0:
                size_str = "len({})".format(self.get_target_name(self.convert_bound_symbol(target_var[0])))
            elif sub_index == 1:
                if self.get_sym_type(target_var[0]).element_type.is_dynamic_row():
                    size_str = "{}[{}-1].shape[0]".format(self.get_target_name(self.convert_bound_symbol(target_var[0])), sym_list[0])
                else:
                    size_str = "{}".format(self.get_sym_type(target_var[0]).element_type.rows)
            else:
                if self.get_sym_type(target_var[0]).element_type.is_dynamic_col():
                    size_str = "{}[{}-1].shape[1]".format(self.get_target_name(self.convert_bound_symbol(target_var[0])), sym_list[0])
                else:
                    size_str = "{}".format(self.get_sym_type(target_var[0]).element_type.cols)
            content.append("for {} in range(1, {}+1):\n".format(sub, size_str))
        else:
            content.append("for {} in range(1, len({})+1):\n".format(sub, self.get_target_name(self.convert_bound_symbol(target_var[0]))))
        exp_pre_list = []
        if exp_info.pre_list:   # catch pre_list
            list_content = "".join(exp_info.pre_list)
            # content += exp_info.pre_list
            list_content = list_content.split('\n')
            for index in range(len(list_content)):
                if index != len(list_content)-1:
                    exp_pre_list.append(list_content[index] + '\n')
        # only one sub for now
        if node.cond:
            content += ["    " + pre for pre in cond_info.pre_list]
            content.append("    " + cond_content)
            content += ["    " + pre for pre in exp_pre_list]
            content.append(str("        " + assign_id + " += " + exp_str + '\n'))
        else:
            content += exp_pre_list
            content.append(str("    " + assign_id + " += " + exp_str + '\n'))
        content[0] = "    " + content[0]
        return CodeNodeInfo(assign_id, pre_list=["    ".join(content)])

    def visit_function(self, node, **kwargs):
        name_info = self.visit(node.name, **kwargs)
        pre_list = []
        params = []
        if node.params:
            for param in node.params:
                param_info = self.visit(param, **kwargs)
                params.append(param_info.content)
                pre_list += param_info.pre_list
        if name_info.content in self.local_func_def:
            func_name = 'self.' + name_info.content
        else:
            func_name = name_info.content
        content = "{}({})".format(func_name, ', '.join(params))
        return CodeNodeInfo(content, pre_list)

    def visit_local_func(self, node, **kwargs):
        self.local_func_parsing = True
        name_info = self.visit(node.name, **kwargs)
        self.local_func_name = name_info.content  # function name when visiting expressions
        param_list = []
        for parameter in node.params:
            param_info = self.visit(parameter, **kwargs)
            param_list.append(param_info.content)
        content = "    def {}(self, {}):\n".format(name_info.content, ", ".join(param_list))
        # get dimension content
        dim_defined_dict, test_content, dim_content = self.gen_dim_content()
        # Handle sequences first
        test_generated_sym_set, seq_test_list = self.gen_same_seq_test()
        test_content += seq_test_list
        #
        main_content = []
        type_declare = []
        # get params content
        type_checks, doc, param_test_content, test_function, par_des_list, test_par_list = \
            self.get_param_content(main_content, type_declare, test_generated_sym_set, dim_defined_dict)
        if len(type_declare) > 0:
            content += self.update_prelist_str(type_declare, '    ')
        if dim_content != '':
            content += self.update_prelist_str([dim_content], '    ')
        type_checks += self.get_dim_check_str()
        type_checks += self.get_arith_dim_check_str()
        if len(type_checks) > 0:
            type_checks = self.update_prelist_str(type_checks, '    ')
            content += type_checks + '\n'
        expr_info = self.visit(node.expr, **kwargs)
        if len(expr_info.pre_list) > 0:
            content += self.update_prelist_str(expr_info.pre_list, "    ")
        if node.expr.is_node(IRNodeType.MultiConds):
            content += '        return {}_ret\n'.format(name_info.content)
        else:
            content += '        return {}\n'.format(expr_info.content)
        if self.local_func_def != '':
            self.local_func_def += '\n'
        self.local_func_def += content
        self.local_func_parsing = False
        return CodeNodeInfo()

    def visit_norm(self, node, **kwargs):
        value_info = self.visit(node.value, **kwargs)
        value = value_info.content
        pre_list = value_info.pre_list
        type_info = node.value
        content = ''
        if type_info.la_type.is_scalar():
            content = "np.absolute({})".format(value)
        elif type_info.la_type.is_vector():
            if node.norm_type == NormType.NormDet:
                content = "scipy.linalg.det({})".format(value)
            elif node.norm_type == NormType.NormInteger:
                content = "np.linalg.norm({}, {})".format(value, node.sub)
            elif node.norm_type == NormType.NormMax:
                content = "np.linalg.norm({}, np.inf)".format(value)
            elif node.norm_type == NormType.NormIdentifier:
                sub_info = self.visit(node.sub, **kwargs)
                pre_list += sub_info.pre_list
                if node.sub.la_type.is_scalar():
                    content = "np.linalg.norm({}, {})".format(value, sub_info.content)
                else:
                    content = "np.sqrt(({}).T @ {} @ ({}))".format(value, sub_info.content, value)
        elif type_info.la_type.is_matrix():
            if node.norm_type == NormType.NormDet:
                content = "scipy.linalg.det({})".format(value)
            elif node.norm_type == NormType.NormFrobenius:
                content = "np.linalg.norm({}, 'fro')".format(value)
            elif node.norm_type == NormType.NormNuclear:
                content = "np.linalg.norm({}, 'nuc')".format(value)
        return CodeNodeInfo(content, pre_list)

    def visit_transpose(self, node, **kwargs):
        f_info = self.visit(node.f, **kwargs)
        if node.f.la_type.is_vector():
            f_info.content = "{}.T.reshape(1, {})".format(f_info.content, node.f.la_type.rows)
        else:
            f_info.content = "{}.T".format(f_info.content)
        return f_info

    def visit_squareroot(self, node, **kwargs):
        f_info = self.visit(node.value, **kwargs)
        f_info.content = "np.sqrt({})".format(f_info.content)
        return f_info

    def visit_power(self, node, **kwargs):
        base_info = self.visit(node.base, **kwargs)
        if node.t:
            if node.base.la_type.is_vector():
                base_info.content = "{}.T.reshape(1, {})".format(base_info.content, node.base.la_type.rows)
            else:
                base_info.content = "{}.T".format(base_info.content)
        elif node.r:
            if node.la_type.is_scalar():
                base_info.content = "1 / ({})".format(base_info.content)
            else:
                if node.base.la_type.is_matrix() and node.base.la_type.sparse:
                    base_info.content = "sparse.linalg.inv({})".format(base_info.content)
                else:
                    base_info.content = "np.linalg.inv({})".format(base_info.content)
        else:
            power_info = self.visit(node.power, **kwargs)
            if node.base.la_type.is_scalar():
                base_info.content = "np.power({}, {})".format(base_info.content, power_info.content)
            else:
                base_info.content = "np.linalg.matrix_power({}, {})".format(base_info.content, power_info.content)
        return base_info

    def visit_solver(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.pre_list += right_info.pre_list
        if (node.left.la_type.is_matrix() and node.left.la_type.sparse) or (node.right.la_type.is_matrix() and node.right.la_type.sparse):
            left_info.content = "sparse.linalg.spsolve({}, {})".format(left_info.content, right_info.content)
        else:
            left_info.content = "np.linalg.solve({}, {})".format(left_info.content, right_info.content)
        return left_info

    def visit_multi_conditionals(self, node, **kwargs):
        assign_node = node.get_ancestor(IRNodeType.Assignment)
        if assign_node is not None:
            name = self.visit(assign_node.left, **kwargs).content
        else:
            func_node = node.get_ancestor(IRNodeType.LocalFunc)
            name = self.visit(func_node.name, **kwargs).content
        type_info = node
        cur_m_id = ''
        pre_list = []
        if_info = self.visit(node.ifs, **kwargs)
        pre_list += if_info.content
        if node.other:
            other_info = self.visit(node.other, **kwargs)
            pre_list.append('    else:\n')
            pre_list.append('        {} = {}\n'.format(name, other_info.content))
        return CodeNodeInfo(cur_m_id, pre_list)


    def visit_sparse_matrix(self, node, **kwargs):
        op_type = kwargs[ASSIGN_TYPE]
        lhs = kwargs[LHS]
        type_info = node
        cur_m_id = type_info.symbol
        pre_list = []
        index_var = type_info.la_type.index_var
        value_var = type_info.la_type.value_var
        pre_list.append("    {} = []\n".format(index_var))
        pre_list.append("    {} = []\n".format(value_var))
        if_info = self.visit(node.ifs, **kwargs)
        pre_list += if_info.content
        # assignment
        if op_type == '=':
            pre_list.append("    {} = scipy.sparse.coo_matrix(({}, np.asarray({}).T), shape=({}, {}))\n".format(cur_m_id, value_var, index_var, self.get_sym_type(cur_m_id).rows,
                                                          self.get_sym_type(cur_m_id).cols))
        elif op_type == '+=':
            # left_ids = self.get_all_ids(lhs)
            # left_subs = left_ids[1]
            pre_list.append(
                "    {} = scipy.sparse.coo_matrix(({}+self.{}.data.tolist(), np.hstack((np.asarray({}).T, np.asarray((self.{}.row, self.{}.col))))), shape=({}, {}))\n".format(cur_m_id, value_var, cur_m_id,
                                                                                                    index_var, cur_m_id, cur_m_id,
                                                                                                    self.get_sym_type(
                                                                                                        cur_m_id).rows,
                                                                                                    self.get_sym_type(
                                                                                                        cur_m_id).cols))

        return CodeNodeInfo(cur_m_id, pre_list)

    def visit_sparse_ifs(self, node, **kwargs):
        assign_node = node.get_ancestor(IRNodeType.Assignment)
        if assign_node is None:
            right_node = node.get_ancestor(IRNodeType.LocalFunc).expr
        else:
            right_node = assign_node.right
        if right_node.is_node(IRNodeType.SparseMatrix):
            assign_node = node.get_ancestor(IRNodeType.Assignment)
            sparse_node = node.get_ancestor(IRNodeType.SparseMatrix)
            subs = assign_node.left.subs
            ret = ["    for {} in range(1, {}+1):\n".format(subs[0], sparse_node.la_type.rows),
                   "        for {} in range(1, {}+1):\n".format(subs[1], sparse_node.la_type.cols)]
            pre_list = []
            if node.in_cond_only:
                ret = []
                for cond in node.cond_list:
                    cond_info = self.visit(cond, **kwargs)
                    for index in range(len(cond_info.content)):
                        cond_info.content[index] = self.update_prelist_str([cond_info.content[index]], '    ')
                    ret += cond_info.pre_list
                    ret += cond_info.content
            else:
                for cond in node.cond_list:
                    cond_info = self.visit(cond, **kwargs)
                    for index in range(len(cond_info.content)):
                        cond_info.content[index] = '            ' + cond_info.content[index]
                    ret += cond_info.content
                    pre_list += cond_info.pre_list
        else:
            pre_list = []
            ret = []
            for cond in node.cond_list:
                cond_info = self.visit(cond, **kwargs)
                for index in range(len(cond_info.content)):
                    cond_info.content[index] = '    ' + cond_info.content[index]
                ret += cond_info.content
                pre_list += cond_info.pre_list
        return CodeNodeInfo(ret, pre_list)

    def visit_sparse_if(self, node, **kwargs):
        assign_node = node.get_ancestor(IRNodeType.Assignment)
        if assign_node is None:
            func_node = node.get_ancestor(IRNodeType.LocalFunc)
            right_node = func_node.expr
            left_node = func_node.name
        else:
            right_node = assign_node.right
            left_node = assign_node.left
        if right_node.is_node(IRNodeType.SparseMatrix):
            self.convert_matrix = True
            sparse_node = node.get_ancestor(IRNodeType.SparseMatrix)
            subs = assign_node.left.subs
            cond_info = self.visit(node.cond, **kwargs)
            stat_info = self.visit(node.stat, **kwargs)
            content = []
            stat_content = stat_info.content
            # replace '_ij' with '(i,j)'
            stat_content = stat_content.replace('_{}{}'.format(subs[0], subs[1]), '[{}][{}]'.format(subs[0], subs[1]))
            if node.loop:
                content += stat_info.pre_list
                content.append(cond_info.content)
                content.append('    {}.append(({}-1, {}-1))\n'.format(sparse_node.la_type.index_var, subs[0], subs[1]))
                content.append('    {}.append({})\n'.format(sparse_node.la_type.value_var, stat_content))
            else:
                content.append('{} {}:\n'.format("if" if node.first_in_list else "elif", cond_info.content))
                content.append('    {}.append(({}-1, {}-1))\n'.format(sparse_node.la_type.index_var, subs[0], subs[1]))
                content.append('    {}.append({})\n'.format(sparse_node.la_type.value_var, stat_content))
            self.convert_matrix = False
        else:
            cond_info = self.visit(node.cond, **kwargs)
            stat_info = self.visit(node.stat, **kwargs)
            content = cond_info.pre_list
            stat_content = stat_info.content
            content.append('{} {}:\n'.format("if" if node.first_in_list else "elif", cond_info.content))
            content += stat_info.pre_list
            if assign_node is None:
                content.append("    {}_ret = {}\n".format(self.visit(left_node, **kwargs).content, stat_content))
            else:
                content.append("    {} = {}\n".format(self.visit(assign_node.left, **kwargs).content, stat_content))
        return CodeNodeInfo(content)

    def visit_sparse_other(self, node, **kwargs):
        content = ''
        return CodeNodeInfo('    '.join(content))

    def visit_vector(self, node, **kwargs):
        cur_m_id = node.symbol
        ret = []
        pre_list = []
        for item in node.items:
            item_info = self.visit(item, **kwargs)
            ret.append(item_info.content)
            pre_list += item_info.pre_list
        content = 'np.hstack(({}))'.format(", ".join(ret))
        return CodeNodeInfo(content, pre_list=pre_list)

    def visit_to_matrix(self, node, **kwargs):
        node_info = self.visit(node.item, **kwargs)
        node_info.content = "({}).reshape({}, 1)".format(node_info.content, node.item.la_type.rows)
        return node_info

    def visit_matrix(self, node, **kwargs):
        content = "    "
        # lhs = kwargs[LHS]
        type_info = node
        cur_m_id = type_info.symbol
        kwargs["cur_id"] = cur_m_id
        ret_info = self.visit(node.value, **kwargs)
        ret = ret_info.content
        if type_info.la_type.block:
            all_rows = []
            m_content = ""
            for i in range(len(ret)):
                if type_info.la_type.list_dim:
                    for j in range(len(ret[i])):
                        if (i, j) in type_info.la_type.list_dim:
                            dims = type_info.la_type.list_dim[(i, j)]
                            if dims[0] == 1 and dims[1] == 1:
                                # scalar value
                                continue
                            if ret[i][j] == '0':
                                func_name = 'np.zeros'
                            elif ret[i][j] == '1':
                                func_name = 'np.ones'
                            elif 'I' in ret[i][j] and 'I' not in self.symtable:
                                # todo: assert in type checker
                                assert dims[0] == dims[1], "I must be square matrix"
                                ret[i][j] = ret[i][j].replace('I', 'np.identity({})'.format(dims[0]))
                                continue
                            else:
                                func_name = ret[i][j] + ' * np.ones'
                            if dims[1] == 1:
                                # vector
                                ret[i][j] = '{}(({}, 1))'.format(func_name, dims[0])
                            else:
                                ret[i][j] = '{}(({}, {}))'.format(func_name, dims[0], dims[1])
                for j in range(len(ret[i])):
                    # vector type needs to be reshaped as matrix inside block matrix
                    if node.la_type.item_types and node.la_type.item_types[i][j].la_type.is_vector():
                        ret[i][j] = '({}).reshape({}, 1)'.format(ret[i][j], node.la_type.item_types[i][j].la_type.rows)
                all_rows.append('[' + ', '.join(ret[i]) + ']')
            # matrix
            if self.get_sym_type(cur_m_id).sparse and self.get_sym_type(cur_m_id).block:
                m_content += 'sparse.bmat([{}])'.format(', '.join(all_rows))
                if len(ret) > 1 and len(ret[0]) > 1:
                    content += '{} = {}\n'.format(cur_m_id, m_content)
                elif len(ret) == 1 and len(ret[0]) != 1:  # one row one col -> vstack
                    # single row
                    content += '{} = sparse.hstack(({}))\n'.format(cur_m_id, ', '.join(ret[0]))
                else:
                    # single col
                    for i in range(len(ret)):
                        ret[i] = ''.join(ret[i])
                    content += '{} = sparse.vstack(({}))\n'.format(cur_m_id, ', '.join(ret))
            else:
                # dense
                m_content += 'np.block([{}])'.format(', '.join(all_rows))
                if len(ret) > 1 and len(ret[0]) > 1:
                    content += '{} = {}\n'.format(cur_m_id, m_content)
                elif len(ret) == 1 and len(ret[0]) != 1:  # one row one col -> vstack
                    # single row
                    content += '{} = np.hstack(({}))\n'.format(cur_m_id, ', '.join(ret[0]))
                else:
                    # single col
                    for i in range(len(ret)):
                        ret[i] = ''.join(ret[i])
                    content += '{} = np.vstack(({}))\n'.format(cur_m_id, ', '.join(ret))
        else:
            # dense
            content += '{} = np.zeros(({}, {}))\n'.format(cur_m_id, self.get_sym_type(cur_m_id).rows,
                                                          self.get_sym_type(cur_m_id).cols)
            for i in range(len(ret)):
                content += "    {}[{}] = [{}]\n".format(cur_m_id, i, ', '.join(ret[i]))
        #####################
        pre_list = [content]
        if ret_info.pre_list:
            pre_list = ret_info.pre_list + pre_list
        return CodeNodeInfo(cur_m_id, pre_list)

    def visit_num_matrix(self, node, **kwargs):
        post_s = ''
        if node.id:
            func_name = "np.identity"
        else:
            if node.left == '0':
                func_name = "np.zeros"
            elif node.left == '1' or node.left == '𝟙':
                func_name = "np.ones"
            # else:
            #     func_name = "({} * np.ones".format(left_info.content)
            #     post_s = ')'
        id1_info = self.visit(node.id1, **kwargs)
        if node.id2:
            id2_info = self.visit(node.id2, **kwargs)
            content = "{}(({}, {}))".format(func_name, id1_info.content, id2_info.content)
        else:
            content = "{}({})".format(func_name, id1_info.content)
        node_info = CodeNodeInfo(content+post_s)
        return node_info

    def visit_matrix_index(self, node, **kwargs):
        main_info = self.visit(node.main, **kwargs)
        if node.row_index is not None:
            row_info = self.visit(node.row_index, **kwargs)
            if node.row_index.la_type.index_type:
                row_content = row_info.content
            else:
                row_content = "{}-1".format(row_info.content)
            if node.col_index is not None:
                col_info = self.visit(node.col_index, **kwargs)
                if node.col_index.la_type.index_type:
                    col_content = col_info.content
                else:
                    col_content = "{}-1".format(col_info.content)
                if self.get_sym_type(node.main.main_id).sparse:
                    content = "{}.tocsr()[{}, {}]".format(main_info.content, row_content, col_content)
                else:
                    content = "{}[{}, {}]".format(main_info.content, row_content, col_content)
            else:
                content = "{}[{}, :]".format(main_info.content, row_content)
        else:
            col_info = self.visit(node.col_index, **kwargs)
            if node.col_index.la_type.index_type:
                content = "{}[:, {}]".format(main_info.content, col_info.content)
            else:
                content = "{}[:, {}-1]".format(main_info.content, col_info.content)
        return CodeNodeInfo(content)

    def visit_vector_index(self, node, **kwargs):
        main_info = self.visit(node.main, **kwargs)
        index_info = self.visit(node.row_index, **kwargs)
        if node.row_index.la_type.index_type:
            return CodeNodeInfo("{}[{}]".format(main_info.content, index_info.content))
        else:
            return CodeNodeInfo("{}[{}-1]".format(main_info.content, index_info.content))

    def visit_sequence_index(self, node, **kwargs):
        main_info = self.visit(node.main, **kwargs)
        main_index_info = self.visit(node.main_index, **kwargs)
        if node.main_index.la_type.index_type:
            main_index_content = main_index_info.content
        else:
            main_index_content = "{}-1".format(main_index_info.content)
        if node.slice_matrix:
            if node.row_index is not None:
                row_info = self.visit(node.row_index, **kwargs)
                if node.row_index.la_type.index_type:
                    row_content = row_info.content
                else:
                    row_content = "{}-1".format(row_info.content)
                content = "{}[{}][{}, :]".format(main_info.content, main_index_content, row_content)
            else:
                col_info = self.visit(node.col_index, **kwargs)
                if node.col_index.la_type.index_type:
                    col_content = col_info.content
                else:
                    col_content = "{}-1".format(col_info.content)
                content = "{}[{}][:, {}]".format(main_info.content, main_index_content, col_content)
        else:
            if node.row_index is not None:
                row_info = self.visit(node.row_index, **kwargs)
                if node.row_index.la_type.index_type:
                    row_content = row_info.content
                else:
                    row_content = "{}-1".format(row_info.content)
                if node.col_index is not None:
                    col_info = self.visit(node.col_index, **kwargs)
                    if node.col_index.la_type.index_type:
                        col_content = col_info.content
                    else:
                        col_content = "{}-1".format(col_info.content)
                    content = "{}[{}][{}, {}]".format(main_info.content, main_index_content, row_content,
                                                      col_content)
                else:
                    content = "{}[{}][{}]".format(main_info.content, main_index_content, row_content)
            else:
                content = "{}[{}]".format(main_info.content, main_index_content)
        return CodeNodeInfo(content)

    def visit_seq_dim_index(self, node, **kwargs):
        main_index_info = self.visit(node.main_index, **kwargs)
        if node.main_index.la_type.index_type:
            main_index_content = main_index_info.content
        else:
            main_index_content = "{}-1".format(main_index_info.content)
        if node.is_row_index():
            content = "{}[{}].shape[0]".format(node.real_symbol, main_index_content)
        else:
            content = "{}[{}].shape[1]".format(node.real_symbol, main_index_content)
        return CodeNodeInfo(content)

    def visit_mul(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        l_info = node.left
        r_info = node.right
        mul = ' * '
        if l_info.la_type.is_matrix() or l_info.la_type.is_vector():
            if r_info.la_type.is_matrix() or r_info.la_type.is_vector():
                mul = ' @ '
        left_info.content = left_info.content + mul + right_info.content
        left_info.pre_list += right_info.pre_list
        return left_info

    def visit_div(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = left_info.content + ' / ' + right_info.content
        left_info.pre_list += right_info.pre_list
        return left_info

    def visit_cast(self, node, **kwargs):
        value_info = self.visit(node.value, **kwargs)
        if node.la_type.is_scalar():
            value_info.content = "({}).item()".format(value_info.content)
        return value_info

    def visit_assignment(self, node, **kwargs):
        type_info = node
        # visit matrix first
        placeholder = "{}_{}\n".format(self.comment_placeholder, node.parse_info.line)
        self.comment_dict[placeholder] = self.update_prelist_str([node.raw_text], '    # ')
        content = placeholder
        left_info = self.visit(node.left, **kwargs)
        left_id = left_info.content
        kwargs[LHS] = left_id
        kwargs[ASSIGN_TYPE] = node.op
        # self left-hand-side symbol
        right_info = self.visit(node.right, **kwargs)
        right_exp = ""
        # if right_info.pre_list:
        #     content += "".join(right_info.pre_list)
        # y_i = stat
        if node.left.contain_subscript():
            left_ids = node.left.get_all_ids()
            left_subs = left_ids[1]
            if len(left_subs) == 2: # matrix only
                sequence = left_ids[0]  # y left_subs[0]
                sub_strs = left_subs[0] + left_subs[1]
                if self.get_sym_type(sequence).is_matrix() and self.get_sym_type(sequence).sparse:
                    if left_subs[0] == left_subs[1]:  # L_ii
                        content = ""
                        if self.get_sym_type(sequence).diagonal:
                            # add definition
                            if sequence not in self.declared_symbols:
                                content += "    {} = []\n".format(self.get_sym_type(sequence).index_var)
                                content += "    {} = []\n".format(self.get_sym_type(sequence).value_var)
                        content += "    for {} in range(1, {}+1):\n".format(left_subs[0], self.get_sym_type(sequence).rows)
                        if right_info.pre_list:
                            content += self.update_prelist_str(right_info.pre_list, "    ")
                        content += "        {}.append(({} - 1, {} - 1))\n".format(self.get_sym_type(sequence).index_var, left_subs[0], left_subs[0])
                        content += "        {}.append({})\n".format(self.get_sym_type(sequence).value_var, right_info.content)
                        content += "    self.{} = scipy.sparse.coo_matrix(({}, np.asarray({}).T), shape=({}, {}))\n".format(sequence,
                                                                                                            self.get_sym_type(sequence).value_var,
                                                                                                            self.get_sym_type(sequence).index_var,
                                                                                                            self.get_sym_type(
                                                                                                                sequence).rows,
                                                                                                            self.get_sym_type(
                                                                                                                sequence).cols)
                    else:  # L_ij
                        if right_info.pre_list:
                            content += "".join(right_info.pre_list)
                        # sparse mat assign
                        right_exp += '    self.' + sequence + ' = ' + right_info.content
                        content += right_exp
                elif left_subs[0] == left_subs[1]:
                    # L_ii
                    content = ""
                    content += "    for {} in range(1, {}+1):\n".format(left_subs[0], self.get_sym_type(sequence).rows)
                    if right_info.pre_list:
                        content += self.update_prelist_str(right_info.pre_list, "    ")
                    content += "        self.{}[{}-1][{}-1] = {}".format(sequence, left_subs[0], left_subs[0], right_info.content)
                else:
                    for right_var in type_info.symbols:
                        if sub_strs in right_var:
                            var_ids = self.get_all_ids(right_var)
                            right_info.content = right_info.content.replace(right_var, "{}[{}][{}]".format(var_ids[0], var_ids[1][0], var_ids[1][1]))
                    right_exp += "    self.{}[{}-1][{}-1] = {}".format(self.get_main_id(left_id), left_subs[0], left_subs[1], right_info.content)
                    if self.get_sym_type(sequence).is_matrix():
                        if node.op == '=':
                            # declare
                            if sequence not in self.declared_symbols:
                                content += "    self.{} = np.zeros(({}, {}))\n".format(sequence,
                                                                                  self.get_sym_type(sequence).rows,
                                                                                  self.get_sym_type(sequence).cols)
                    content += "    for {} in range(1, {}+1):\n".format(left_subs[0], self.get_sym_type(sequence).rows)
                    content += "        for {} in range(1, {}+1):\n".format(left_subs[1], self.get_sym_type(sequence).cols)
                    if right_info.pre_list:
                        content += self.update_prelist_str(right_info.pre_list, "        ")
                    content += "        " + right_exp
                    # content += '\n'
            elif len(left_subs) == 1: # sequence only
                sequence = left_ids[0]  # y left_subs[0]
                # replace sequence
                for right_var in type_info.symbols:
                    if self.contain_subscript(right_var):
                        var_ids = self.get_all_ids(right_var)
                        right_info.content = right_info.content.replace(right_var, "{}[{}]".format(var_ids[0], var_ids[1][0]))

                right_exp += "    {} = {}".format(left_info.content, right_info.content)

                ele_type = self.get_sym_type(sequence).element_type
                if self.get_sym_type(sequence).is_sequence():
                    if ele_type.is_matrix():
                        content += "    self.{} = np.zeros(({}, {}, {}))\n".format(sequence, self.get_sym_type(sequence).size, ele_type.rows, ele_type.cols)
                    elif ele_type.is_vector():
                        content += "    self.{} = np.zeros(({}, {}, ))\n".format(sequence, self.get_sym_type(sequence).size, ele_type.rows)
                        # content += "    {} = np.zeros(({}, {}, 1))\n".format(sequence, self.get_sym_type(sequence).size, ele_type.rows)
                    elif ele_type.is_function():
                        content += "    self.{} = np.zeros({}, dtype=object)\n".format(sequence, self.get_sym_type(sequence).size)
                    else:
                        content += "    self.{} = np.zeros({})\n".format(sequence, self.get_sym_type(sequence).size)
                    content += "    for {} in range(1, {}+1):\n".format(left_subs[0], self.get_sym_type(sequence).size)
                else:
                    # vector
                    content += "    self.{} = np.zeros({})\n".format(sequence, self.get_sym_type(sequence).rows)
                    content += "    for {} in range(1, {}+1):\n".format(left_subs[0], self.get_sym_type(sequence).rows)
                if right_info.pre_list:
                    content += self.update_prelist_str(right_info.pre_list, "    ")
                content += "    " + right_exp
        #
        else:
            if right_info.pre_list:
                content += "".join(right_info.pre_list)
            op = ' = '
            if node.op == '+=':
                op = ' += '
            if not node.right.is_node(IRNodeType.MultiConds):
                right_exp += '    ' + self.get_main_id(left_id) + op + right_info.content
            content += right_exp
        #content += '\n'
        la_remove_key(LHS, **kwargs)
        self.declared_symbols.add(node.left.get_main_id())
        return CodeNodeInfo(content)

    def visit_if(self, node, **kwargs):
        ret_info = self.visit(node.cond)
        # ret_info.content = "if " + ret_info.content + ":\n"
        return ret_info

    def visit_condition(self, node, **kwargs):
        if len(node.cond_list) > 1:
            pre_list = []
            content_list = []
            for condition in node.cond_list:
                info = self.visit(condition)
                pre_list += info.pre_list
                content_list.append('(' + info.content + ')')
            if node.cond_type == ConditionType.ConditionAnd:
                content = ' and '.join(content_list)
            else:
                content = ' or '.join(content_list)
            return CodeNodeInfo(content=content, pre_list=pre_list)
        return self.visit(node.cond)

    def visit_in(self, node, **kwargs):
        item_list = []
        pre_list = []
        right_info = self.visit(node.set, **kwargs)
        pre_list += right_info.pre_list
        if node.loop:
            extra_list = []
            extra_blank = True
            if node.set.la_type.index_type:
                for item in node.items:
                    item_info = self.visit(item, **kwargs)
                    item_content = item_info.content
                    extra_content = ''
                    if not item.la_type.index_type:
                        # item_content = "{}-1".format(item_info.content)
                        extra_content = '+1'
                        extra_blank = False
                    item_list.append(item_content)
                    extra_list.append(extra_content)
                    pre_list += item_info.pre_list
            else:
                for item in node.items:
                    item_info = self.visit(item, **kwargs)
                    extra_content = ''
                    item_content = "{}".format(item_info.content)
                    if item.la_type.index_type:
                        # item_content = "{}+1".format(item_info.content)
                        extra_content = '-1'
                        extra_blank = False
                    item_list.append(item_content)
                    extra_list.append(extra_content)
            if extra_blank:
                content = 'for ({}) in {}:\n'.format(', '.join(item_list), right_info.content)
            else:
                index_name = self.generate_var_name('tuple')
                content = 'for {} in {}:\n'.format(index_name, right_info.content)
                content += '    {} = {}[0]{}\n'.format(item_list[0], index_name, extra_list[0])
                content += '    {} = {}[1]{}\n'.format(item_list[1], index_name, extra_list[1])
        else:
            if node.set.la_type.index_type:
                for item in node.items:
                    item_info = self.visit(item, **kwargs)
                    item_content = item_info.content
                    if not item.la_type.index_type:
                        item_content = "{}-1".format(item_info.content)
                    item_list.append(item_content)
                    pre_list += item_info.pre_list
            else:
                for item in node.items:
                    item_info = self.visit(item, **kwargs)
                    if not item.la_type.index_type:
                        item_content = "{}".format(item_info.content)
                    else:
                        item_content = "{}+1".format(item_info.content)
                    item_list.append(item_content)
                    pre_list += item_info.pre_list
            content = '(' + ', '.join(item_list) + ') in ' + right_info.content
        return CodeNodeInfo(content=content, pre_list=pre_list)

    def visit_not_in(self, node, **kwargs):
        item_list = []
        pre_list = []
        right_info = self.visit(node.set, **kwargs)
        if node.set.la_type.index_type:
            for item in node.items:
                item_info = self.visit(item, **kwargs)
                item_content = item_info.content
                if not item.la_type.index_type:
                    item_content = "{}-1".format(item_info.content)
                item_list.append(item_content)
        else:
            for item in node.items:
                item_info = self.visit(item, **kwargs)
                if not item.la_type.index_type:
                    item_content = "{}".format(item_info.content)
                else:
                    item_content = "{}+1".format(item_info.content)
                item_list.append(item_content)
        content = '(' + ', '.join(item_list) + ') not in ' + right_info.content
        return CodeNodeInfo(content=content, pre_list=pre_list)

    def visit_bin_comp(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_content = left_info.content
        right_content = right_info.content
        if node.left.la_type.index_type and not node.right.la_type.index_type:
            left_content = "{}+1".format(left_info.content)
        if not node.left.la_type.index_type and node.right.la_type.index_type:
            right_content = "{}+1".format(right_info.content)
        left_info.content = left_content + ' {} '.format(self.get_bin_comp_str(node.comp_type)) + right_content
        left_info.pre_list += right_info.pre_list
        return left_info

    def visit_derivative(self, node, **kwargs):
        return CodeNodeInfo("")

    def visit_optimize(self, node, **kwargs):
        id_info = self.visit(node.base, **kwargs)
        if node.base_type.la_type.is_scalar():
            init_value = 0
        elif node.base_type.la_type.is_vector():
            init_value = "np.zeros({})".format(node.base_type.la_type.rows)
        elif node.base_type.la_type.is_matrix():
            init_value = "np.zeros({}*{})".format(node.base_type.la_type.rows, node.base_type.la_type.cols)
            name_convention = {id_info.content: "{}.reshape({}, {})".format(id_info.content, node.base_type.la_type.rows, node.base_type.la_type.cols)}
            self.add_name_conventions(name_convention)
        exp_info = self.visit(node.exp, **kwargs)
        category = ''
        if node.opt_type == OptimizeType.OptimizeMin:
            category = 'min'
        elif node.opt_type == OptimizeType.OptimizeMax:
            category = 'max'
        elif node.opt_type == OptimizeType.OptimizeArgmin:
            category = 'argmin'
        elif node.opt_type == OptimizeType.OptimizeArgmax:
            category = 'argmax'
        opt_param = self.generate_var_name('x')
        opt_ret = self.generate_var_name('ret')
        # Handle constraints
        pre_list = []
        constraint_list = []
        for cond_node in node.cond_list:
            if cond_node.cond.node_type == IRNodeType.BinComp:
                if cond_node.cond.comp_type == IRNodeType.Gt or cond_node.cond.comp_type == IRNodeType.Ge:
                    constraint_list.append("{{'type': 'ineq', 'fun': lambda {}: {}-{}}}".format(id_info.content,
                                                                                                self.visit(cond_node.cond.left, **kwargs).content,
                                                                                                self.visit(cond_node.cond.right, **kwargs).content))
                elif cond_node.cond.comp_type == IRNodeType.Lt or cond_node.cond.comp_type == IRNodeType.Le:
                    constraint_list.append("{{'type': 'ineq', 'fun': lambda {}: {}-{}}}".format(id_info.content,
                                                                                                self.visit(cond_node.cond.right, **kwargs).content,
                                                                                                self.visit(cond_node.cond.left, **kwargs).content))
                elif cond_node.cond.comp_type == IRNodeType.Eq:
                    constraint_list.append("{{'type': 'eq', 'fun': lambda {}: {}-{}}}".format(id_info.content,
                                                                                              self.visit(cond_node.cond.left, **kwargs).content,
                                                                                              self.visit(cond_node.cond.right, **kwargs).content))
                elif cond_node.cond.comp_type == IRNodeType.Ne:
                    constraint_list.append("{{'type': 'ineq', 'fun': lambda {}: np.power({}-{}, 2)}}".format(id_info.content,
                                                                                              self.visit(cond_node.cond.left, **kwargs).content,
                                                                                              self.visit(cond_node.cond.right, **kwargs).content))
            elif cond_node.cond.node_type == IRNodeType.In:
                v_set = self.visit(cond_node.cond.set, **kwargs).content
                opt_func = self.generate_var_name(category)
                pre_list.append("    def {}({}):\n".format(opt_func, opt_param))
                pre_list.append("        {} = 1\n".format(opt_ret))
                pre_list.append("        for i in {}:\n".format(v_set))
                pre_list.append("            {} *= ({}[0] - i)\n".format(opt_ret, opt_param, v_set))
                pre_list.append("        return {}\n".format(opt_ret))
                constraint_list.append("{{'type': 'eq', 'fun': {}}}".format(opt_func))

        # constraint
        constraints_param = ""
        if len(constraint_list) > 0:
            cons = self.generate_var_name('cons')
            pre_list.append("    {} = ({})\n".format(cons, ','.join(constraint_list)))
            constraints_param = ", constraints={}".format(cons)
        target_func = self.generate_var_name('target')
        if node.base_type.la_type.is_scalar():
            exp = exp_info.content.replace(id_info.content, "{}[0]".format(id_info.content))
        else:
            exp = exp_info.content
        # Handle optimization type
        if node.opt_type == OptimizeType.OptimizeMax or node.opt_type == OptimizeType.OptimizeArgmax:
            exp = "-({})".format(exp)

        if len(exp_info.pre_list) > 0:
            pre_list.append("    def {}({}):\n".format(target_func, id_info.content))
            for pre in exp_info.pre_list:
                lines = pre.split('\n')
                for line in lines:
                    if line != "":
                        pre_list.append("    {}\n".format(line))
            pre_list.append("        return {}\n".format(exp))
        else:
            # simple expression
            pre_list.append("    {} = lambda {}: {}\n".format(target_func, id_info.content, exp))
        #
        if node.opt_type == OptimizeType.OptimizeMin:
            content = "minimize({}, {}{}).fun".format(target_func, init_value, constraints_param)
        elif node.opt_type == OptimizeType.OptimizeMax:
            content = "-minimize({}, {}{}).fun".format(target_func, init_value, constraints_param)
        elif node.opt_type == OptimizeType.OptimizeArgmin or node.opt_type == OptimizeType.OptimizeArgmax:
            if node.base_type.la_type.is_scalar():
                content = "minimize({}, {}{}).x[0]".format(target_func, init_value, constraints_param)
            elif node.base_type.la_type.is_vector():
                content = "minimize({}, {}{}).x".format(target_func, init_value, constraints_param)
            elif node.base_type.la_type.is_matrix():
                content = "minimize({}, {}{}).x.reshape({}, {})".format(target_func,
                                                                                                init_value,
                                                                                                constraints_param,
                                                                                                node.base_type.la_type.rows,
                                                                                                node.base_type.la_type.cols)
        if node.base_type.la_type.is_matrix():
            self.del_name_conventions(name_convention)
        return CodeNodeInfo(content, pre_list=pre_list)

    def visit_domain(self, node, **kwargs):
        return CodeNodeInfo("")

    def visit_integral(self, node, **kwargs):
        pre_list = []
        lower_info = self.visit(node.domain.lower, **kwargs)
        pre_list += lower_info.pre_list
        upper_info = self.visit(node.domain.upper, **kwargs)
        pre_list += upper_info.pre_list
        exp_info = self.visit(node.exp, **kwargs)
        pre_list += exp_info.pre_list
        base_info = self.visit(node.base, **kwargs)
        pre_list += exp_info.pre_list
        content = "quad({}, {}, {})[0]".format("lambda {}: {}".format(base_info.content, exp_info.content), lower_info.content, upper_info.content)
        return CodeNodeInfo(content, pre_list=pre_list)

    def visit_inner_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        content = "np.inner({}, {})".format(left_info.content, right_info.content)
        if node.sub:
            sub_info = self.visit(node.sub, **kwargs)
            content = "({}).T @ ({}) @ ({})".format(right_info.content, sub_info.content, left_info.content)
        return CodeNodeInfo(content, pre_list=left_info.pre_list+right_info.pre_list)

    def visit_fro_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("np.dot(({}).ravel(), ({}).ravel())".format(left_info.content, right_info.content), pre_list=left_info.pre_list+right_info.pre_list)

    def visit_hadamard_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("np.multiply({}, {})".format(left_info.content, right_info.content), pre_list=left_info.pre_list+right_info.pre_list)

    def visit_cross_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("np.cross({}, {})".format(left_info.content, right_info.content), pre_list=left_info.pre_list+right_info.pre_list)

    def visit_kronecker_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        if node.la_type.is_sparse_matrix():
            content = "scipy.sparse.kron({}, {}, 'coo')".format(left_info.content, right_info.content)
        else:
            content = "np.kron({}, {})".format(left_info.content, right_info.content)
        return CodeNodeInfo(content, pre_list=left_info.pre_list+right_info.pre_list)

    def visit_dot_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("np.dot(({}).ravel(), ({}).ravel())".format(left_info.content, right_info.content), pre_list=left_info.pre_list+right_info.pre_list)

    def visit_math_func(self, node, **kwargs):
        content = ''
        param_info = self.visit(node.param, **kwargs)
        params_content = param_info.content
        pre_list = param_info.pre_list
        if node.func_type == MathFuncType.MathFuncSin:
            content = 'np.sin'
        elif node.func_type == MathFuncType.MathFuncAsin:
            content = 'np.arcsin'
        elif node.func_type == MathFuncType.MathFuncCos:
            content = 'np.cos'
        elif node.func_type == MathFuncType.MathFuncAcos:
            content = 'np.arccos'
        elif node.func_type == MathFuncType.MathFuncTan:
            content = 'np.tan'
        elif node.func_type == MathFuncType.MathFuncAtan:
            content = 'np.arctan'
        elif node.func_type == MathFuncType.MathFuncSinh:
            content = 'np.sinh'
        elif node.func_type == MathFuncType.MathFuncAsinh:
            content = 'np.arcsinh'
        elif node.func_type == MathFuncType.MathFuncCosh:
            content = 'np.cosh'
        elif node.func_type == MathFuncType.MathFuncAcosh:
            content = 'np.arccosh'
        elif node.func_type == MathFuncType.MathFuncTanh:
            content = 'np.tanh'
        elif node.func_type == MathFuncType.MathFuncAtanh:
            content = 'np.arctanh'
        elif node.func_type == MathFuncType.MathFuncCot:
            content = '1/np.tan'
        elif node.func_type == MathFuncType.MathFuncSec:
            content = '1/np.cos'
        elif node.func_type == MathFuncType.MathFuncCsc:
            content = '1/np.sin'
        elif node.func_type == MathFuncType.MathFuncAtan2:
            content = 'np.arctan2'
            remain_info = self.visit(node.remain_params[0], **kwargs)
            params_content += ', ' + remain_info.content
            pre_list += remain_info.pre_list
        elif node.func_type == MathFuncType.MathFuncExp:
            content = 'np.exp'
        elif node.func_type == MathFuncType.MathFuncLog:
            content = 'np.log'
        elif node.func_type == MathFuncType.MathFuncLog2:
            content = 'np.log2'
        elif node.func_type == MathFuncType.MathFuncLog10:
            content = 'np.log10'
        elif node.func_type == MathFuncType.MathFuncLn:
            content = 'np.log'
        elif node.func_type == MathFuncType.MathFuncSqrt:
            content = 'np.sqrt'
        elif node.func_type == MathFuncType.MathFuncTrace:
            content = 'np.trace'
        elif node.func_type == MathFuncType.MathFuncDiag:
            content = 'np.diag'
        elif node.func_type == MathFuncType.MathFuncVec:
            return CodeNodeInfo("np.matrix.flatten({}, order='F')".format(params_content))  # column-major
        elif node.func_type == MathFuncType.MathFuncDet:
            content = 'scipy.linalg.det'
        elif node.func_type == MathFuncType.MathFuncRank:
            content = 'np.linalg.matrix_rank'
        elif node.func_type == MathFuncType.MathFuncNull:
            content = 'scipy.linalg.null_space'
        elif node.func_type == MathFuncType.MathFuncOrth:
            content = 'scipy.linalg.orth'
        elif node.func_type == MathFuncType.MathFuncInv:
            content = 'scipy.linalg.inv'
        return CodeNodeInfo("{}({})".format(content, params_content), pre_list=pre_list)

    def visit_constant(self, node, **kwargs):
        content = ''
        if node.c_type == ConstantType.ConstantPi:
            content = 'np.pi'
        elif node.c_type == ConstantType.ConstantE:
            content = 'np.e'
        return CodeNodeInfo(content)

    ###################################################################
