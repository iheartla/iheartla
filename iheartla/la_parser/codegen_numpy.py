from .codegen import *
from .type_walker import *
import keyword


class CodeGenNumpy(CodeGen):
    def __init__(self):
        super().__init__(ParserTypeEnum.NUMPY)

    def init_type(self, type_walker, func_name):
        super().init_type(type_walker, func_name)
        if self.has_derivative:
            self.pre_str = "import jax.numpy as np\n"
        else:
            self.pre_str = "import numpy as np\n"
        self.pre_str += '''import scipy\nimport scipy.linalg\nfrom scipy import sparse\n'''
        self.pre_str += "from scipy.integrate import quad, solve_ivp\n"
        self.pre_str += "from scipy.optimize import minimize\n"
        # self.pre_str += "\n\n"
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

    def get_set_checking_str(self):
        check_list = []
        if len(self.get_cur_param_data().set_checking) > 0:
            for key, value in self.get_cur_param_data().set_checking.items():
                check_list.append('    assert {} in {}'.format(key, self.prefix_sym(value)))
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
        ret_list = []  # name list
        for cur_index in range(len(func_type.ret)):
            if func_type.ret[cur_index].is_set():
                ret_name = self.generate_var_name('tmp')
                test_content += self.get_set_test_list(ret_name, self.generate_var_name("dim"), 'i', func_type.ret[cur_index], rand_int_max, '        ')
                ret_list.append(ret_name)
            else:
                ret_list.append(self.get_rand_test_str(func_type.ret[cur_index], rand_int_max))
        test_content.append('        return {}'.format(', '.join(ret_list)))
        return test_content

    def get_type_test_in_set(self, ele_type, rand_int_max):
        test_content = []
        if ele_type.is_matrix():
            element_type = ele_type.element_type
            if isinstance(element_type, LaVarType):
                if ele_type.sparse:
                    if element_type.is_scalar() and element_type.is_int:
                        test_content.append('sparse.random({}, {}, dtype=np.integer, density=0.25)'.format(ele_type.rows, ele_type.cols))
                    else:
                        test_content.append('sparse.random({}, {}, dtype=np.float64, density=0.25)'.format(ele_type.rows, ele_type.cols))
                else:
                    # dense
                    if element_type.is_scalar() and element_type.is_int:
                        test_content.append('np.random.randint({}, size=({}, {}))'.format(rand_int_max, ele_type.rows, ele_type.cols))
                    else:
                        test_content.append('np.random.randn({}, {})'.format(ele_type.rows, ele_type.cols))
            else:
                if ele_type.sparse:
                    test_content.append('sparse.random({}, {}, dtype=np.float64, density=0.25)'.format(ele_type.rows, ele_type.cols))
                else:
                    test_content.append('np.random.randn({}, {})'.format(ele_type.rows, ele_type.cols))
        elif ele_type.is_vector():
            element_type = ele_type.element_type
            if isinstance(element_type, LaVarType):
                if element_type.is_scalar() and element_type.is_int:
                    test_content.append('np.random.randint({}, size=({}))'.format(rand_int_max, ele_type.rows))
                else:
                    test_content.append('np.random.randn({})'.format(ele_type.rows))
            else:
                    test_content.append('np.random.randn({})'.format(ele_type.rows))
        elif ele_type.is_scalar():
            if ele_type.is_int:
                test_content.append('np.random.randint({})'.format(rand_int_max))
            else:
                test_content.append('np.random.randn()')
        return ','.join(test_content)

    def get_set_test_list(self, parameter, dim_name, ind_name, la_type, rand_int_max, pre='    '):
        test_content = []
        test_content.append('{} = []'.format(parameter))
        test_content.append('{} = np.random.randint(1, {})'.format(dim_name, rand_int_max))
        test_content.append('for {} in range({}):'.format(ind_name, dim_name))
        gen_list = []
        for i in range(la_type.size):
            if la_type.type_list[i].is_set():
                # sub element is also a set
                new_set_name = parameter+"_"+str(i)
                gen_list.append(new_set_name)
                test_content += self.get_set_test_list(new_set_name, dim_name+"_"+str(i), ind_name+"_"+str(i), la_type.type_list[i], rand_int_max, pre)
            else:
                gen_list.append(self.get_type_test_in_set(la_type.type_list[i], rand_int_max))
        test_content.append('    {}.append(('.format(parameter) + ', '.join(gen_list) + '))')
        test_content = ['{}{}'.format(pre, line) for line in test_content]
        return test_content

    def is_module_sym(self, sym):
        exist = False
        if len(self.module_list) > 0:
            for module in self.module_list:
                if len(module.syms) > 0 and sym in module.syms:
                    exist = True
                    break
        return exist

    def prefix_sym(self, sym):
        # for usage only, not initialization
        if (sym in self.lhs_list or sym in self.local_func_dict or self.is_module_sym(sym)) and not sym.startswith("self."):
            return 'self.' + sym
        return sym
    
    def get_mesh_str(self, mesh):
        # prepend self. if necessary
        prefix = self.check_prefix(mesh)
        if prefix:
            return 'self.' + mesh
        return mesh
    
    def check_prefix(self, sym):
        # given a symbol, check whether we need to add self.
        prefix = False
        if sym in self.lhs_list:
            prefix = True
        elif self.local_func_parsing:
            is_param = False
            if self.local_func_name != '':
                for key, value in self.func_data_dict.items():
                    if sym in value.params_data.parameters:
                        is_param = True
                        break
            if not is_param and sym in self.used_params:
                prefix = True
            if not is_param:
                if self.is_module_sym(sym):
                    prefix = True
        else:
            if self.is_module_sym(sym):
                prefix = True
        return prefix

    def visit_id(self, node, **kwargs):
        content = node.get_name() 
        # if not self.is_local_param(content) and content not in self.parameters and content not in self.local_func_syms:
        # if self.local_func_parsing:
        #     if self.local_func_name != '':
        #         if content not in self.func_data_dict[self.local_func_name].params_data.parameters:
        #             prefix = True
        # else:
        #     if content not in self.main_param.parameters:
        #         prefix = True
        prefix = self.check_prefix(content)
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
                for cur_index in range(len(module.syms)):
                    sym = module.syms[cur_index]
                    if self.symtable[module.r_syms[cur_index]].is_function():
                        init_var += self.copy_func_impl(sym, module.r_syms[cur_index], module.name,
                                                                 self.symtable[module.r_syms[cur_index]])
                    else:
                        init_var += "        self.{} = _{}.{}\n".format(module.r_syms[cur_index], module.name, sym)
        if len(self.builtin_module_dict) > 0: # builtin module initialization
            for key, module_data in self.builtin_module_dict.items():
                if key in CLASS_PACKAGES:
                    class_name = key
                    if key == MESH_HELPER:
                        self.code_frame.include += 'from triangle_mesh import *\n'
                        class_name = "TriangleMesh"
                    # init_var += "        self.{} = {}({})\n".format(module_data.instance_name, class_name, ','.join(module_data.params_list))
        content = ["class {}:".format(self.get_result_type()),
                   "    def __init__(self,{}".format(def_str[3:]),
                   self.get_used_params_content(),
                   ]
        if '' in content:
            content.remove('')
        end_str = self.local_func_def + def_struct
        if end_str != '':
            end_str = '\n' + end_str
        return "\n".join(content) + init_struct + init_var + stat_str + self.get_opt_syms_content() + end_str

    def copy_func_impl(self, sym, r_syms, module_name, func_type):
        """implement function from other modules"""
        content_list = []
        if not func_type.is_overloaded():
            content_list.append("        self.{} = _{}.{}\n".format(r_syms, module_name, sym))
        else:
            for c_index in range(len(func_type.func_list)):
                c_type = func_type.func_list[c_index]
                c_name = func_type.fname_list[c_index]
                p_name = func_type.pre_fname_list[c_index]
                content_list.append("        self.{} = _{}.{}\n".format(c_name, module_name, p_name))
        return ''.join(content_list)

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

    def get_opt_syms_content(self):
        assign_list = []
        for param in self.opt_syms:
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
        init_def_str = ', '.join(self.parameters) + '):\n'
        content = ''
        if show_doc:
            content += '    \"\"\"\n' + '\n'.join(doc) + '\n    \"\"\"\n'
        # merge content
        if len(type_declare) > 0:
            content += '\n'.join(type_declare) + '\n\n'
        content += dim_content
        type_checks += self.get_dim_check_str()
        type_checks += self.get_arith_dim_check_str()
        type_checks += self.get_set_checking_str()
        if len(type_checks) > 0:
            content += '\n'.join(type_checks) + '\n\n'
        #
        # statements
        mesh_content = ""
        stats_content = ""
        for index in range(len(node.stmts)):
            ret_str = ''
            cur_stats_content = ''
            if index == len(node.stmts) - 1:
                if not node.stmts[index].is_node(IRNodeType.Assignment) and not node.stmts[index].is_node(IRNodeType.Destructuring) and not node.stmts[index].is_node(IRNodeType.Equation):
                    if node.stmts[index].is_node(IRNodeType.LocalFunc):
                        self.visit(node.stmts[index], **kwargs)
                        continue
                    elif node.stmts[index].is_node(IRNodeType.OdeFirstOrder):
                        self.visit(node.stmts[index], **kwargs)
                        continue
                    kwargs[LHS] = self.ret_symbol
                    ret_str = "    self." + self.ret_symbol + ' = '
            else:
                if not node.stmts[index].is_node(IRNodeType.Assignment) and not node.stmts[index].is_node(IRNodeType.Destructuring) and not node.stmts[index].is_node(IRNodeType.Equation):
                    # meaningless
                    if node.stmts[index].is_node(IRNodeType.LocalFunc):
                        self.visit(node.stmts[index], **kwargs)
                    elif node.stmts[index].is_node(IRNodeType.OdeFirstOrder):
                        self.visit(node.stmts[index], **kwargs)
                    continue
            stat_info = self.visit(node.stmts[index], **kwargs)
            if stat_info.pre_list:
                cur_stats_content += "".join(stat_info.pre_list)
            cur_stats_content += ret_str + stat_info.content + '\n'
            if index in node.meshset_list:
                mesh_content += cur_stats_content
            else:
                stats_content += cur_stats_content

        # content += stats_content
        # content += '    return ' + self.get_ret_struct()
        # content += '\n'
        mesh_dim_list = []
        for mesh, data in self.mesh_dict.items():
            mesh_dim_list.append("    {} = {}.n_vertices()\n".format(data.la_type.vi_size, mesh))
            mesh_dim_list.append("    {} = {}.n_edges()\n".format(data.la_type.ei_size, mesh))
            mesh_dim_list.append("    {} = {}.n_faces()\n".format(data.la_type.fi_size, mesh))
        # content += stats_content
        # content += '\n}\n'
        content = init_def_str + mesh_content + ''.join(mesh_dim_list) + content  # mesh content before dims checking
        content = self.get_struct_definition(self.update_prelist_str([content], '    '), stats_content)
        # content = self.get_struct_definition(self.update_prelist_str([content], '    ')) + '\n'
        # test
        test_function += test_content
        test_function.append('    return {}'.format(', '.join(self.parameters)))
        main_content.append("    func_value = {}({})".format(self.func_name, ', '.join(self.parameters)))
        if self.ret_symbol in self.symtable and self.get_sym_type(self.ret_symbol) is not None:
            main_content.append('    print("return value: ", func_value.{})'.format(self.ret_symbol))
        self.code_frame.include += '\n\n'
        self.code_frame.struct = self.trim_content(content)
        if not self.class_only:
            self.code_frame.main = self.trim_content('\n'.join(main_content))
            self.code_frame.rand_data = self.trim_content('\n'.join(test_function))
            content += '\n\n' + '\n'.join(test_function) + '\n\n\n' + '\n'.join(main_content)
        # convert special string in identifiers
        content = self.trim_content(content)
        return content

    def get_target_name(self, c_var):
        """check whether there's a need to prepend `self.`"""
        content = c_var
        if self.local_func_parsing:
            if c_var not in self.func_data_dict[self.local_func_name].params_data.parameters and not c_var.startswith("self."):
                content = "self.{}".format(c_var)
        else:
            if c_var not in self.main_param.parameters and not c_var.startswith("self."):
                content = "self.{}".format(c_var)
        return content

    def visit_summation(self, node, **kwargs):
        target_var = []
        self.push_scope(node.scope_name)
        expr_sign = '-' if node.sign else ''
        # sub = self.visit(node.id).content
        def set_name_conventions(sub):
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
            self.add_name_conventions(name_convention)
            return name_convention
        if node.enum_list:
            name_convention = {}
            for sub in node.enum_list:
                name_convention.update(set_name_conventions(sub))
        else:
            sub = self.visit(node.id).content
            name_convention = set_name_conventions(sub)
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
        if node.enum_list:
            range_info = self.visit(node.range, **kwargs)
            if len(node.enum_list) == 1:
                content.append('for {} in {}:\n'.format(node.enum_list[0], range_info.content))
            else:
                index_name = self.generate_var_name('tuple')
                content.append('for {} in {}:\n'.format(index_name, range_info.content))
                extra_content = ''
                for i in range(len(node.enum_list)):
                    if node.range.la_type.index_type:
                        content.append('    {} = {}[{}]{} + 1\n'.format(node.enum_list[i], index_name, i, extra_content))
                    else:
                        content.append('    {} = {}[{}]{} + 1\n'.format(node.enum_list[i], index_name, i, extra_content))
            exp_pre_list = []
            if exp_info.pre_list:  # catch pre_list
                list_content = "".join(exp_info.pre_list)
                # content += exp_info.pre_list
                list_content = list_content.split('\n')
                for index in range(len(list_content)):
                    if index != len(list_content) - 1:
                        exp_pre_list.append(list_content[index] + '\n')
            content += exp_pre_list
            # exp_str
            if len(node.extra_list) > 0:
                for et in node.extra_list:
                    extra_info = self.visit(et, **kwargs)
                content += [self.update_prelist_str([extra_info.content], '    ')]
            content.append(str("    " + assign_id + " += " + expr_sign + exp_str + '\n'))
            content[0] = "    " + content[0]
            self.del_name_conventions(name_convention)
            self.pop_scope()
            return CodeNodeInfo(assign_id, pre_list=["    ".join(content)])
        sym_info = node.sym_dict[target_var[0]]
        if node.lower:
            # explicit range
            lower_info = self.visit(node.lower, **kwargs)
            upper_info = self.visit(node.upper, **kwargs)
            content += lower_info.pre_list
            content += upper_info.pre_list
            content.append(
                "for {} in range({}, {}+1):\n".format(sub, lower_info.content, upper_info.content))
        else:
            # implicit range
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
        # exp_str
        if len(node.extra_list) > 0:
            for et in node.extra_list:
                extra_info = self.visit(et, **kwargs)
                content += [self.update_prelist_str([extra_info.content], '    ')]
        # only one sub for now
        if node.cond:
            content += ["    " + pre for pre in cond_info.pre_list]
            content.append("    " + cond_content)
            content += ["    " + pre for pre in exp_pre_list]
            content.append(str("        " + assign_id + " += " + expr_sign + exp_str + '\n'))
        else:
            content += exp_pre_list
            content.append(str("    " + assign_id + " += " + expr_sign + exp_str + '\n'))
        content[0] = "    " + content[0]
        self.pop_scope()
        return CodeNodeInfo(assign_id, pre_list=["    ".join(content)])

    def visit_union_sequence(self, node, **kwargs):
        target_var = []
        self.push_scope(node.scope_name)
        # sub = self.visit(node.id).content
        def set_name_conventions(sub):
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
            self.add_name_conventions(name_convention)
            return name_convention
        if node.enum_list:
            name_convention = {}
            for sub in node.enum_list:
                name_convention.update(set_name_conventions(sub))
        else:
            sub = self.visit(node.id).content
            name_convention = set_name_conventions(sub)
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
        content.append("{} = {{}}\n".format(assign_id))
        if node.enum_list:
            range_info = self.visit(node.range, **kwargs)
            index_name = self.generate_var_name('tuple')
            content.append('for {} in {}:\n'.format(index_name, range_info.content))
            extra_content = ''
            for i in range(len(node.enum_list)):
                if node.range.la_type.index_type:
                    content.append('    {} = {}[{}]{} + 1\n'.format(node.enum_list[i], index_name, i, extra_content))
                else:
                    content.append('    {} = {}[{}]{} + 1\n'.format(node.enum_list[i], index_name, i, extra_content))
            exp_pre_list = []
            if exp_info.pre_list:  # catch pre_list
                list_content = "".join(exp_info.pre_list)
                # content += exp_info.pre_list
                list_content = list_content.split('\n')
                for index in range(len(list_content)):
                    if index != len(list_content) - 1:
                        exp_pre_list.append(list_content[index] + '\n')
            content += exp_pre_list
            # exp_str
            if len(node.extra_list) > 0:
                for et in node.extra_list:
                    extra_info = self.visit(et, **kwargs)
                content += [self.update_prelist_str([extra_info.content], '    ')]
            content.append("    {} = frozenset.union({}, {})\n".format(assign_id, assign_id, exp_str))
            content[0] = "    " + content[0]
            self.del_name_conventions(name_convention)
            self.pop_scope()
            return CodeNodeInfo(assign_id, pre_list=["    ".join(content)])
        sym_info = node.sym_dict[target_var[0]]
        if node.lower:
            # explicit range
            lower_info = self.visit(node.lower, **kwargs)
            upper_info = self.visit(node.upper, **kwargs)
            content += lower_info.pre_list
            content += upper_info.pre_list
            content.append(
                "for {} in range({}, {}+1):\n".format(sub, lower_info.content, upper_info.content))
        else:
            # implicit range
            content.append("for {} in range(1, len({})+1):\n".format(sub, self.get_target_name(self.convert_bound_symbol(target_var[0]))))
        exp_pre_list = []
        if exp_info.pre_list:   # catch pre_list
            list_content = "".join(exp_info.pre_list)
            # content += exp_info.pre_list
            list_content = list_content.split('\n')
            for index in range(len(list_content)):
                if index != len(list_content)-1:
                    exp_pre_list.append(list_content[index] + '\n')
        # exp_str
        if len(node.extra_list) > 0:
            for et in node.extra_list:
                extra_info = self.visit(et, **kwargs)
                content += [self.update_prelist_str([extra_info.content], '    ')]
        # only one sub for now
        if node.cond:
            content += ["    " + pre for pre in cond_info.pre_list]
            content.append("    " + cond_content)
            content += ["    " + pre for pre in exp_pre_list]
            content.append("        {} = frozenset.union({}, {})\n".format(assign_id, assign_id, exp_str))
        else:
            content += exp_pre_list
            content.append("    {} = frozenset.union({}, {})\n".format(assign_id, assign_id, exp_str))
        content[0] = "    " + content[0]
        self.pop_scope()
        return CodeNodeInfo(assign_id, pre_list=["    ".join(content)])

    def visit_function(self, node, **kwargs):
        name_info = self.visit(node.name, **kwargs)
        func_name = name_info.content
        original_name = self.filter_symbol(node.name.get_main_id())
        if self.get_sym_type(original_name).is_overloaded() and node.identity_name:
            func_name = self.filter_symbol(node.identity_name)
        func_name = self.convert_overloaded_name(func_name)
        pre_list = []
        params = []
        if node.params:
            for param in node.params:
                param_info = self.visit(param, **kwargs)
                params.append(param_info.content)
                pre_list += param_info.pre_list
        if self.visiting_diff_eq:
            if self.visiting_diff_init:
                return CodeNodeInfo(','.join(params), pre_list)
            return name_info
        if (func_name in self.lhs_list or func_name in self.local_func_dict or self.is_module_sym(func_name) or self.is_module_sym(node.name.get_main_id())) and not func_name.startswith("self."):
            func_name = 'self.' + func_name
        content = "{}({})".format(func_name, ', '.join(params))
        return CodeNodeInfo(content, pre_list)

    def visit_local_func(self, node, **kwargs):
        self.local_func_parsing = True
        self.push_scope(node.scope_name)
        name_info = self.visit(node.name, **kwargs)
        self.local_func_name = node.identity_name  # function name when visiting expressions
        param_list = []
        for parameter in node.params:
            param_info = self.visit(parameter, **kwargs)
            param_list.append(param_info.content)
        content = "    def {}(self, {}):\n".format(node.identity_name, ", ".join(param_list))
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
        type_checks += self.get_set_checking_str()
        if len(type_checks) > 0:
            type_checks = self.update_prelist_str(type_checks, '    ')
            content += type_checks + '\n'
        extra_expr = ''
        # exp_str
        if len(node.extra_list) > 0:
            extra_list = []
            for et in node.extra_list:
                extra_info = self.visit(et, **kwargs)
                extra_list += [self.update_prelist_str([extra_info.content], '    ')]
            extra_expr += '\n'.join(extra_list)
        ret_list = []
        for cur_index in range(len(node.expr)):
            expr_info = self.visit(node.expr[cur_index], **kwargs)
            if len(expr_info.pre_list) > 0:
                content += self.update_prelist_str(expr_info.pre_list, "    ")
            if node.expr[cur_index].is_node(IRNodeType.MultiConds):
                ret_list.append('{}_ret'.format(name_info.content))
            else:
                ret_list.append(expr_info.content)
        content += extra_expr + '        return {}\n'.format(', '.join(ret_list))
        if self.local_func_def != '':
            self.local_func_def += '\n'
        self.local_func_def += content
        self.local_func_parsing = False
        self.pop_scope()
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
                if node.sub is None:
                    content = "np.linalg.norm({}, {})".format(value, 2)
                else:
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
        elif type_info.la_type.is_set():
            content = "len({})".format(value)
        return CodeNodeInfo(content, pre_list)

    def visit_transpose(self, node, **kwargs):
        f_info = self.visit(node.f, **kwargs)
        if node.f.la_type.is_vector():
            f_info.content = "{}.T.reshape(1, {})".format(f_info.content, node.f.la_type.rows)
        else:
            f_info.content = "{}.T".format(f_info.content)
        return f_info

    def visit_pseudoinverse(self, node, **kwargs):
        f_info = self.visit(node.f, **kwargs)
        if node.f.la_type.is_vector():
            f_info.content = "{}.T.reshape(1, {}) / ({}.dot({})) ".format(f_info.content, node.f.la_type.rows)
        else:
            f_info.content = "np.linalg.pinv({})".format(f_info.content)
        return f_info

    def visit_squareroot(self, node, **kwargs):
        f_info = self.visit(node.value, **kwargs)
        f_info.content = "np.sqrt({})".format(f_info.content)
        return f_info

    def visit_element_convert(self, node, **kwargs):
        pre_list = []
        if node.to_type == EleConvertType.EleToSimplicialSet or node.to_type == EleConvertType.EleToTuple or node.to_type == EleConvertType.EleToSequence:
            # tuple
            params = []
            for param in node.params:
                param_info = self.visit(param, **kwargs)
                params.append(param_info.content)
                pre_list += param_info.pre_list
            if node.to_type == EleConvertType.EleToSimplicialSet or node.to_type == EleConvertType.EleToTuple:
                if node.to_type == EleConvertType.EleToSimplicialSet and len(node.params) == 3:
                    # add extra empty tet set
                    params.append("[]")
                content = "[{}]".format(",".join(params))
            elif node.to_type == EleConvertType.EleToSequence:
                seq_n = self.generate_var_name("seq")
                if node.params[0].la_type.is_sequence():
                    # append new
                    pre_list.append("    {} = {}\n".format(seq_n, params[0]))
                    pre_list += ["    {}.add({})".format(seq_n, p) for p in params[1:]]
                else:
                    pre_list.append("    {} = [{}]\n".format(seq_n, ",".join(params)))
                content = seq_n
        else:
            param_info = self.visit(node.params[0], **kwargs)
            pre_list += param_info.pre_list
            content = param_info.content
        return CodeNodeInfo(content, pre_list)

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
                base_info.content = "np.power(({}).astype(float), {})".format(base_info.content, power_info.content)
            else:
                if node.base.la_type.sparse:
                    base_info.content = "({})**({})".format(base_info.content, power_info.content)
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
            name = self.visit(assign_node.left[0], **kwargs).content
            func_ret = False
        else:
            func_node = node.get_ancestor(IRNodeType.LocalFunc)
            name = self.visit(func_node.name, **kwargs).content
            func_ret = True
        type_info = node
        cur_m_id = ''
        pre_list = []
        if_info = self.visit(node.ifs, **kwargs)
        pre_list += if_info.content
        if node.other:
            other_info = self.visit(node.other, **kwargs)
            pre_list.append('    else:\n')
            if func_ret:
                pre_list.append('        {}_ret = {}\n'.format(name, other_info.content))
            else:
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
            right_node = node.get_ancestor(IRNodeType.LocalFunc).expr[0]
        else:
            right_node = assign_node.right[0]
        if right_node.is_node(IRNodeType.SparseMatrix):
            assign_node = node.get_ancestor(IRNodeType.Assignment)
            sparse_node = node.get_ancestor(IRNodeType.SparseMatrix)
            subs = assign_node.left[0].subs
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
            right_node = func_node.expr[0]
            left_node = func_node.name
        else:
            right_node = assign_node.right[0]
            left_node = assign_node.left[0]
        if right_node.is_node(IRNodeType.SparseMatrix):
            self.convert_matrix = True
            sparse_node = node.get_ancestor(IRNodeType.SparseMatrix)
            subs = assign_node.left[0].subs
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
                content.append("    {} = {}\n".format(self.visit(assign_node.left[0], **kwargs).content, stat_content))
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

    def visit_set(self, node, **kwargs):
        self.push_scope(node.scope_name)
        cur_m_id = node.symbol
        ret = []
        pre_list = []
        if node.enum_list and len(node.enum_list) > 0:
            pre_list.append('    {} = set()\n'.format(cur_m_id))
            #
            range_info = self.visit(node.range, **kwargs)
            range_name = self.generate_var_name('range')
            pre_list.append('    {} = {}\n'.format(range_name, range_info.content))
            if len(node.enum_list) == 1:
                pre_list.append('    for {} in {}:\n'.format(node.enum_list[0], range_name))
            else:
                index_name = self.generate_var_name('tuple')
                pre_list.append('    for {} in {}:\n'.format(index_name, range_name))
                extra_content = ''
                for i in range(len(node.enum_list)):
                    if node.range.la_type.index_type:
                        pre_list.append(
                            '        {} = {}[{}]{} + 1\n'.format(node.enum_list[i], index_name, i, extra_content))
                    else:
                        pre_list.append(
                            '        {} = {}[{}]{} + 1\n'.format(node.enum_list[i], index_name, i, extra_content))
            exp_pre_list = []
            exp_info = self.visit(node.items[0], **kwargs)
            if exp_info.pre_list:  # catch pre_list
                list_content = "".join(exp_info.pre_list)
                # content += exp_info.pre_list
                list_content = list_content.split('\n')
                for index in range(len(list_content)):
                    if index != len(list_content) - 1:
                        exp_pre_list.append(list_content[index] + '\n')
            pre_list += exp_pre_list
            if node.cond:
                cond_info = self.visit(node.cond, **kwargs)
                cond_content = "        if(" + cond_info.content + "):\n"
                pre_list += cond_content
                pre_list.append("            {}.add({})\n".format(cur_m_id, exp_info.content))
            else:
                pre_list.append("        {}.add({})\n".format(cur_m_id, exp_info.content))
            content = cur_m_id
        else:
            for item in node.items:
                item_info = self.visit(item, **kwargs)
                ret.append(item_info.content)
                pre_list += item_info.pre_list
            content = '{{{}}}'.format(", ".join(ret))
        self.pop_scope()
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

    def visit_set_index(self, node, **kwargs):
        main_info = self.visit(node.main, **kwargs)
        index_info = self.visit(node.row_index, **kwargs)
        if node.row_index.la_type.index_type:
            return CodeNodeInfo("list({})[{}]".format(main_info.content, index_info.content))
        else:
            return CodeNodeInfo("list({})[{}-1]".format(main_info.content, index_info.content))

    def visit_tuple_index(self, node, **kwargs):
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
        left_info.content = "({})".format(left_info.content) + ' / ' + "({})".format(right_info.content)
        left_info.pre_list += right_info.pre_list
        return left_info

    def visit_union(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = "frozenset.union({}, {})".format(left_info.content, right_info.content)
        return left_info

    def visit_intersection(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = "frozenset.intersection({}, {})".format(left_info.content, right_info.content)
        return left_info

    def visit_difference(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = "{} - {}".format(left_info.content, right_info.content)
        return left_info

    def visit_cast(self, node, **kwargs):
        value_info = self.visit(node.value, **kwargs)
        if node.la_type.is_scalar():
            value_info.content = "({}).item()".format(value_info.content)
        return value_info

    def visit_equation(self, node, **kwargs):
        return CodeNodeInfo("")

    def visit_destructuring(self, node, **kwargs):
        right_info = self.visit(node.right[0], **kwargs)
        rhs = self.generate_var_name("rhs")
        content = "    {} = {}\n".format(rhs, right_info.content)
        for cur_index in range(len(node.left)):
            id0_info = self.visit(node.left[cur_index], **kwargs)
            expr = ''
            if node.cur_type == DestructuringType.DestructuringSet:
                expr = '{}[{}]'.format(rhs, cur_index)
            elif node.cur_type == DestructuringType.DestructuringSequence:
                expr = '{}[{}]'.format(rhs, cur_index)
            elif node.cur_type == DestructuringType.DestructuringVector:
                expr = '{}[{}]'.format(rhs, cur_index)
            elif node.cur_type == DestructuringType.DestructuringTuple or node.cur_type == DestructuringType.DestructuringList:
                expr = '{}[{}]'.format(rhs, cur_index)
            content += "    {} = {}\n".format(id0_info.content, expr)
        return CodeNodeInfo(content, right_info.pre_list)

    def visit_assignment(self, node, **kwargs):
        if node.cur_type == AssignType.AssignTypeSolver:
            return CodeNodeInfo("")
        type_info = node
        # visit matrix first
        placeholder = "{}_{}\n".format(self.comment_placeholder, node.parse_info.line)
        self.comment_dict[placeholder] = self.update_prelist_str([node.raw_text], '    # ')
        content = placeholder
        if node.optimize_param:
            content = ''
            lhs_list = []
            for cur_index in range(len(node.left)):
                left_info = self.visit(node.left[cur_index], **kwargs)
                lhs_list.append(left_info.content)
            right_info = self.visit(node.right[0], **kwargs)
            if right_info.pre_list:
                content += "".join(right_info.pre_list)
            content += "    {} = {}".format(', '.join(lhs_list), right_info.content)
        else:
            if len(node.left) > 1 and len(node.right) == 1:
                # only accept direct assignment, without subscript
                rhs_node = node.right[0]
                tuple_name = self.generate_var_name("tuple")
                right_info = self.visit(rhs_node, **kwargs)
                if right_info.pre_list:
                    content += self.update_prelist_str(right_info.pre_list, "    ")
                content += "    {} = {}\n".format(tuple_name, right_info.content)
                for cur_index in range(len(node.left)):
                    left_info = self.visit(node.left[cur_index], **kwargs)
                    content += "    {} = {}[{}]\n".format(left_info.content, tuple_name, cur_index)
                    self.declared_symbols.add(node.left[cur_index].get_main_id())
                la_remove_key(LHS, **kwargs)
                return CodeNodeInfo(content)
            for cur_index in range(len(node.left)):
                left_info = self.visit(node.left[cur_index], **kwargs)
                left_id = left_info.content
                kwargs[LHS] = left_id
                kwargs[ASSIGN_TYPE] = node.op
                # self left-hand-side symbol
                right_info = self.visit(node.right[cur_index], **kwargs)
                right_exp = ""
                # if right_info.pre_list:
                #     content += "".join(right_info.pre_list)
                # y_i = stat
                if node.left[cur_index].contain_subscript() and node.change_ele_only:
                    if right_info.pre_list:
                        content = "".join(right_info.pre_list) + content
                    content += "    {} = {}\n".format(left_info.content, right_info.content)
                elif node.left[cur_index].contain_subscript():
                    left_ids = node.left[cur_index].get_all_ids()
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
                            if left_subs[0] == '*':
                                right_exp += "    self.{}[:, {}-1] = {}".format(self.get_main_id(left_id), left_subs[1], right_info.content)
                            elif left_subs[1] == '*':
                                right_exp += "    self.{}[{}-1, :] = {}".format(self.get_main_id(left_id), left_subs[0], right_info.content)
                            else:
                                right_exp += "    self.{}[{}-1][{}-1] = {}".format(self.get_main_id(left_id), left_subs[0], left_subs[1], right_info.content)
                            if self.get_sym_type(sequence).is_matrix():
                                if node.op == '=':
                                    # declare
                                    if sequence not in self.declared_symbols:
                                        content += "    self.{} = np.zeros(({}, {}))\n".format(sequence,
                                                                                          self.get_sym_type(sequence).rows,
                                                                                          self.get_sym_type(sequence).cols)
                            if left_subs[0] == '*':
                                content += "    for {} in range(1, {}+1):\n".format(left_subs[1], self.get_sym_type(sequence).cols)
                                if right_info.pre_list:
                                    content += self.update_prelist_str(right_info.pre_list, "    ")
                                content += "    " + right_exp
                            elif left_subs[1] == '*':
                                content += "    for {} in range(1, {}+1):\n".format(left_subs[0], self.get_sym_type(sequence).rows)
                                if right_info.pre_list:
                                    content += self.update_prelist_str(right_info.pre_list, "    ")
                                content += "    " + right_exp
                            else:
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
                    if not node.right[cur_index].is_node(IRNodeType.MultiConds):
                        right_exp += '    ' + self.get_main_id(left_id) + op + right_info.content
                    content += right_exp
                content += '\n'
                la_remove_key(LHS, **kwargs)
                self.declared_symbols.add(node.left[cur_index].get_main_id())
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
        return self.visit(node.cond_list[0])

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

    def visit_divergence(self, node, **kwargs):
        return CodeNodeInfo("")

    def visit_gradient(self, node, **kwargs):
        content = ""
        if node.sub:
            value_info = self.visit(node.value, **kwargs)
            sub_info = self.visit(node.sub, **kwargs)
            content = "jax.grad({})({})".format(value_info.content, sub_info.content)
        return CodeNodeInfo(content)

    def visit_laplace(self, node, **kwargs):
        return CodeNodeInfo("")

    def visit_partial(self, node, **kwargs):
        content = ""
        if node.order_type == PartialOrderType.PartialHessian:
            upper_info = self.visit(node.upper, **kwargs)
            lower_info = self.visit(node.lower_list[0], **kwargs)
            content = "jax.hessian({})({})".format(upper_info.content, lower_info.content)
        return CodeNodeInfo(content)

    def visit_first_order_ode(self, node, **kwargs):
        self.visiting_diff_eq = True
        target_name = self.generate_var_name("target")
        content = "    def {}(self, {}, {}):\n".format(target_name, node.param, node.func)
        content += "        return {}\n".format(self.visit(node.expr, **kwargs).content)
        content += "    def {}(self, d{}):\n".format(node.func, node.param)
        if len(node.init_list) > 0:
            self.visiting_diff_init = True
            lhs = []
            rhs = []
            for eq_node in node.init_list:
                for l_index in range(len(eq_node.left)):
                    lhs.append(self.visit(eq_node.left[l_index]).content)
                    rhs.append(self.visit(eq_node.right[l_index]).content)
            self.visiting_diff_init = False
            content += "        return solve_ivp(self.{}, [{}, d{}], [{}]).y[0, -1]\n".format(target_name, lhs[0], node.param, rhs[0])
        self.visiting_diff_eq = False
        self.local_func_def += content
        return CodeNodeInfo()

    def visit_optimize(self, node, **kwargs):
        self.push_scope(node.scope_name)
        self.opt_key = node.key
        cur_len = 0
        param_name = self.generate_var_name('X')
        id_list = []
        pack_list = []
        unpack_list = []
        init_str_list = []
        for cur_index in range(len(node.base_list)):
            cur_la_type = node.base_type_list[cur_index].la_type
            id_info = self.visit(node.base_list[cur_index], **kwargs)
            id_list.append(id_info.content)
            pack_str = ''
            unpack_str = ''
            init_str = ''
            if cur_la_type.is_scalar():
                pack_str = "[{}]".format(id_info.content)
                unpack_str = "{}[{}:{}][0]".format(param_name, cur_len, add_syms(cur_len, 1))
                init_str = '0'
                cur_len = add_syms(cur_len, 1)
            elif cur_la_type.is_vector():
                pack_str = id_info.content
                unpack_str = "{}[{}:{}]".format(param_name, cur_len, add_syms(cur_len, cur_la_type.rows))
                cur_len = add_syms(cur_len, cur_la_type.rows)
                init_str = 'np.zeros({})'.format(cur_la_type.rows)
            elif cur_la_type.is_matrix():
                pack_str = "np.reshape({}, -1)".format(id_info.content)
                unpack_str = "{}[{}:{}].reshape({}, {})".format(param_name, cur_len, add_syms(cur_len, mul_syms(cur_la_type.rows, cur_la_type.cols)),
                                                                cur_la_type.rows, cur_la_type.cols)
                cur_len = add_syms(cur_len, mul_syms(cur_la_type.rows, cur_la_type.cols))
                init_str = 'np.zeros(({}, {}))'.format(cur_la_type.rows, cur_la_type.cols)
            if id_info.content in node.init_syms:
                init_str = id_info.content
            pack_list.append(pack_str)
            unpack_list.append(unpack_str)
            init_str_list.append(init_str)
        #
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
        pre_list = ["    def pack({}):\n".format(', '.join(id_list)),
                    "        return np.concatenate([{}])\n".format(', '.join(pack_list)),
                    "    def unpack({}):\n".format(param_name),
                    "        return {}\n".format(', '.join(unpack_list)),
                    ]
        constraint_list = []
        for cond_node in node.cond_list:
            if cond_node.cond.node_type == IRNodeType.BinComp:
                cur_f_name = self.generate_var_name('cons')
                pre_list.append("    def {}({}):\n".format(cur_f_name, param_name))
                pre_list.append("        {} = unpack({})\n".format(', '.join(id_list), param_name))
                if cond_node.cond.comp_type == IRNodeType.Gt or cond_node.cond.comp_type == IRNodeType.Ge:
                    pre_list.append("        return {} - {}\n".format(self.visit(cond_node.cond.left, **kwargs).content,
                                                                    self.visit(cond_node.cond.right, **kwargs).content))
                    constraint_list.append("{{'type': 'ineq', 'fun': {}}}".format(cur_f_name))
                elif cond_node.cond.comp_type == IRNodeType.Lt or cond_node.cond.comp_type == IRNodeType.Le:
                    pre_list.append("        return {} - {}\n".format(self.visit(cond_node.cond.right, **kwargs).content,
                                                                    self.visit(cond_node.cond.left, **kwargs).content))
                    constraint_list.append("{{'type': 'ineq', 'fun': {}}}".format(cur_f_name))
                elif cond_node.cond.comp_type == IRNodeType.Eq:
                    pre_list.append("        return {} - {}\n".format(self.visit(cond_node.cond.left, **kwargs).content,
                                                                    self.visit(cond_node.cond.right, **kwargs).content))
                    constraint_list.append("{{'type': 'eq', 'fun': {}}}".format(cur_f_name))
                elif cond_node.cond.comp_type == IRNodeType.Ne:
                    pre_list.append("        return np.power({} - {}, 2)\n".format(self.visit(cond_node.cond.left, **kwargs).content,
                                                                    self.visit(cond_node.cond.right, **kwargs).content))
                    constraint_list.append("{{'type': 'ineq', 'fun': {}}}".format(cur_f_name))
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
            pre_list.append("    {} = ({})\n".format(cons, ', '.join(constraint_list)))
            constraints_param = ", constraints={}".format(cons)
        target_func = self.generate_var_name('target')
        # if node.base_type.la_type.is_scalar():
        #     exp = exp_info.content.replace(id_info.content, "{}[0]".format(id_info.content))
        # else:
        #     exp = exp_info.content
        exp = exp_info.content
        # Handle optimization type
        if node.opt_type == OptimizeType.OptimizeMax or node.opt_type == OptimizeType.OptimizeArgmax:
            exp = "-({})".format(exp)
        # target function
        pre_list.append("    def {}({}):\n".format(target_func, param_name))
        pre_list.append("        {} = unpack({})\n".format(', '.join(id_list), param_name))
        if len(exp_info.pre_list) > 0:
            for pre in exp_info.pre_list:
                lines = pre.split('\n')
                for line in lines:
                    if line != "":
                        pre_list.append("    {}\n".format(line))
        pre_list.append("        return {}\n".format(exp))
        init_value = "np.zeros({})".format(cur_len)
        # init list
        if len(node.init_list) > 0:
            for cur_index in range(len(node.init_list)):
                init_info = self.visit(node.init_list[cur_index], **kwargs)
                pre_list += init_info.pre_list
                pre_list.append(init_info.content)
            init_value = "pack({})".format(','.join(init_str_list))
        #
        opt_name = self.generate_var_name("opt")
        pre_list.append("    {} = minimize({}, {}{})\n".format(opt_name, target_func, init_value, constraints_param))
        pre_list.append("    {} = unpack({}.x)\n".format(', '.join(id_list), opt_name))
        content = ''
        if node.opt_type == OptimizeType.OptimizeMin:
            content = "{}.fun".format(opt_name)
        elif node.opt_type == OptimizeType.OptimizeMax:
            content = "-{}.fun".format(opt_name)
        elif node.opt_type == OptimizeType.OptimizeArgmin or node.opt_type == OptimizeType.OptimizeArgmax:
            content = "unpack({}.x)".format(opt_name)
        self.pop_scope()
        return CodeNodeInfo(content, pre_list=pre_list)

    def visit_domain(self, node, **kwargs):
        return CodeNodeInfo("")

    def visit_integral(self, node, **kwargs):
        self.push_scope(node.scope_name)
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
        self.pop_scope()
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
            if node.param.la_type.is_set():
                return CodeNodeInfo("list({})".format(params_content))  # column-major
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
        elif node.func_type == MathFuncType.MathFuncMin or node.func_type == MathFuncType.MathFuncMax:
            if node.remain_params and len(node.remain_params) > 0:
                f_name = 'max'
                if node.func_type == MathFuncType.MathFuncMin:
                    f_name = 'min'
                # multi params
                param_list = [param_info.content]
                for remain in node.remain_params:
                    remain_info = self.visit(remain, **kwargs)
                    param_list.append(remain_info.content)
                content = "{}({})".format(f_name, ', '.join(param_list))
            else:
                # one param
                f_name = 'np.amax'
                if node.func_type == MathFuncType.MathFuncMin:
                    f_name = 'np.amin'
                content = "{}({})".format(f_name, params_content)
            return CodeNodeInfo(content, pre_list=pre_list)
        return CodeNodeInfo("{}({})".format(content, params_content), pre_list=pre_list)

    def get_func_prefix(self):
        return "self.{}".format(self.builtin_module_dict[MESH_HELPER].instance_name)

    def visit_constant(self, node, **kwargs):
        content = ''
        if node.c_type == ConstantType.ConstantPi:
            content = 'np.pi'
        elif node.c_type == ConstantType.ConstantE:
            content = 'np.e'
        elif node.c_type == ConstantType.ConstantInf:
            content = 'np.inf'
        return CodeNodeInfo(content)

    ###################################################################
