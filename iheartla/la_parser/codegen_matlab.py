from .codegen import *
from .type_walker import *
import keyword


class CodeGenMatlab(CodeGen):
    def __init__(self):
        super().__init__(ParserTypeEnum.MATLAB)

    def init_type(self, type_walker, func_name):
        super().init_type(type_walker, func_name)
        self.new_id_prefix = ''
        #self.pre_str = '''%{{\n{}\n%}}\n'''.format(self.la_content)
        #self.pre_str += "\n\n"
        self.post_str = ''''''

    def get_dim_check_str(self):
        check_list = []
        if len(self.get_cur_param_data().same_dim_list) > 0:
            check_list = super().get_dim_check_str()
            check_list = ['    assert( {} );'.format(stat) for stat in check_list]
        return check_list

    def get_arith_dim_check_str(self):
        check_list = []
        if len(self.get_cur_param_data().arith_dim_list) > 0:
            check_list = ['    assert( mod({}, 1) == 0.0 );'.format(dims) for dims in self.get_cur_param_data().arith_dim_list]
        return check_list

    def get_set_checking_str(self):
        check_list = []
        if len(self.get_cur_param_data().set_checking) > 0:
            for key, value in self.get_cur_param_data().set_checking.items():
                check_list.append('    assert( ismember({}, {}) );'.format(key, value))
        return check_list

    def randn_str(self,sizes=[]):
        if len(sizes) == 0:
            return "randn()"
        elif len(sizes) == 1:
            return 'randn({},1)'.format(sizes[0])
        else: #len(sizes) > 1:
            return 'randn({})'.format(",".join([str(s) for s in sizes]))

    def randi_str(self,rand_int_max,sizes=[]):
        if len(sizes) == 0:
            return "randi({})".format(rand_int_max)
        elif len(sizes) == 1:
            return 'randi({},{},1)'.format(rand_int_max,sizes[0])
        else: #len(sizes) > 1:
            return 'randi({},{})'.format(rand_int_max,",".join([str(s) for s in sizes]))

    def get_rand_test_str(self, la_type, rand_int_max):
        rand_test = ''
        if la_type.is_matrix():
            element_type = la_type.element_type
            if isinstance(element_type, LaVarType) and element_type.is_scalar() and element_type.is_int:
                #rand_test = 'randi({}, {}, {});'.format(rand_int_max, la_type.rows, la_type.cols)
                rand_test = self.randi_str(rand_int_max,[la_type.rows, la_type.cols])
            else:
                #rand_test = 'randn({}, {});'.format(la_type.rows, la_type.cols)
                rand_test = self.randn_str([la_type.rows, la_type.cols])
        elif la_type.is_vector():
            element_type = la_type.element_type
            if isinstance(element_type, LaVarType) and element_type.is_scalar() and element_type.is_int:
                #rand_test = 'randi({}, {});'.format(rand_int_max, la_type.rows)
                rand_test = self.randi_str(rand_int_max,[la_type.rows])
            else:
                #rand_test = 'randn({},1);'.format(la_type.rows)
                rand_test = self.randn_str([la_type.rows])
        elif la_type.is_scalar():
            #rand_test = 'randn();'
            rand_test = self.randn_str()
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
        #Alec: I don't know what this is doing in python...
        #
        #if func_type.ret_template():
        #    for ret_dim in func_type.ret_symbols:
        #        param_i = func_type.template_symbols[ret_dim]
        #        if func_type.params[param_i].is_vector():
        #            dim_definition.append('        {} = {}{}.shape[0]'.format(ret_dim, self.param_name_test, param_i))
        #        elif func_type.params[param_i].is_matrix():
        #            if ret_dim == func_type.params[param_i].rows:
        #                dim_definition.append(
        #                    '        {} = {}{}.shape[0]'.format(ret_dim, self.param_name_test, param_i))
        #            else:
        #                dim_definition.append(
        #                    '        {} = {}{}.shape[1]'.format(ret_dim, self.param_name_test, param_i))
        for index in range(len(func_type.params)):
            param_list.append('{}{}'.format(self.param_name_test, index))
        anon_str = "   {} = @({}) ".format(var_name, ', '.join(param_list))
        # Multi-line anonymous functions are not possible in Matlab.
        test_indent = ''
        test_content.append(test_indent + "    {} = @{}Func;".format(var_name, var_name + ""))
        test_content.append(test_indent + "    rseed = randi(2^32);")
        ret_list = []
        content_list = []
        for cur_index in range(len(func_type.ret)):
            cur_name = self.generate_var_name('ret')
            ret_list.append(cur_name)
            if func_type.ret[cur_index].is_set():
                content_list += self.get_set_test_list(cur_name, self.generate_var_name("dim"), 'i',
                                                       func_type.ret[cur_index], rand_int_max,
                                                       '            ')
            else:
                content_list.append(test_indent + "        {} = {};".format(cur_name, self.get_rand_test_str(
                    func_type.ret[cur_index], rand_int_max)))

        test_content.append(test_indent + "    function [{}] =  {}({})".format(', '.join(ret_list), var_name + "Func",
                                                                               ', '.join(param_list)))
        test_content.append(test_indent + "        rng(rseed);")
        test_content += dim_definition
        test_content += content_list
        test_content.append(test_indent + "    end")
        # ret_list = []
        # content_list = []
        # for cur_index in range(len(func_type.ret)):
        #     cur_name = self.generate_var_name('ret')
        #     ret_list.append(cur_name)
        #     if func_type.ret[cur_index].is_set():
        #         test_content += self.get_set_test_list(cur_name, self.generate_var_name("dim"), 'i', func_type.ret, rand_int_max, '        ')
        #     else:
        #         test_content.append(self.get_rand_test_str(func_type.ret[cur_index], rand_int_max)+";")
        #
        # # if func_type.ret.is_set():
        # #     test_content += self.get_set_test_list('tmp', self.generate_var_name("dim"), 'i', func_type.ret, rand_int_max, '        ')
        # #     #test_content.append('        return tmp')
        # # else:
        # #     anon_str += self.get_rand_test_str(func_type.ret, rand_int_max)+";"
        # test_content.append(anon_str)
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
                        test_content.append('randi({}, {}, {})'.format(rand_int_max, ele_type.rows, ele_type.cols))
                    else:
                        test_content.append('randn({}, {})'.format(ele_type.rows, ele_type.cols))
            else:
                if ele_type.sparse:
                    test_content.append('sparse.random({}, {}, dtype=np.float64, density=0.25)'.format(ele_type.rows, ele_type.cols))
                else:
                    test_content.append('randi({}, {})'.format(ele_type.rows, ele_type.cols))
        elif ele_type.is_vector():
            element_type = ele_type.element_type
            if isinstance(element_type, LaVarType):
                if element_type.is_scalar() and element_type.is_int:
                    test_content.append('randi({}, {})'.format(rand_int_max, ele_type.rows))
                else:
                    test_content.append('randn({}, 1)'.format(ele_type.rows))
            else:
                    test_content.append('randn({}, 1)'.format(ele_type.rows))
        elif ele_type.is_scalar():
            if ele_type.is_int:
                test_content.append('randi({})'.format(rand_int_max))
            else:
                test_content.append('randn()')
        return ','.join(test_content)

    def get_set_test_list(self, parameter, dim_name, ind_name, la_type, rand_int_max, test_indent='    '):
        test_content = []
        test_content.append('{} = [];'.format(parameter))
        test_content.append('{} = randi({});'.format(dim_name, rand_int_max))
        test_content.append('for {} = 1:{} '.format(ind_name, dim_name))
        gen_list = []
        for i in range(la_type.size):
            if la_type.type_list[i].is_set():
                # sub element is also a set
                new_set_name = parameter+"_"+str(i)
                gen_list.append(new_set_name)
                test_content += self.get_set_test_list(new_set_name, dim_name+"_"+str(i), ind_name+"_"+str(i), la_type.type_list[i], rand_int_max, pre)
            else:
                gen_list.append(self.get_type_test_in_set(la_type.type_list[i], rand_int_max))
        test_content.append('    {} = [{};'.format(parameter, parameter) + ', '.join(gen_list) + '];')
        test_content.append('end')
        test_content = ['{}{}'.format(test_indent, line) for line in test_content]
        return test_content

    def visit_id(self, node, **kwargs):
        content = node.get_name()
        content = self.filter_symbol(content)
        if content in self.name_convention_dict:
            content = self.name_convention_dict[content]
        if self.convert_matrix and node.contain_subscript():
            if len(node.subs) == 2:
                if self.get_sym_type(node.main_id).is_matrix():
                    if self.get_sym_type(node.main_id).sparse:
                        content = "{}({}, {})".format(node.main_id, node.subs[0], node.subs[1])
                    else:
                        content = "{}({}, {})".format(node.main_id, node.subs[0], node.subs[1])
        return CodeNodeInfo(content)

    def get_result_name(self):
        #return self.get_result_type()
        # It's awkward for the variable _name_ to be called xyzType
        # In MATLAB, the returns must be named, so if we're using a struct like
        # the other targets, then just call it output
        # 
        # Return a struct is not very matlibberish. Should consider return
        # values in LIFO order
        return "output"

    def get_module_str(self):
        def_struct = ''
        init_struct = ''
        init_var = ''
        if len(self.module_list) > 0:
            for module in self.module_list:
                def_struct += self.update_prelist_str([module.frame.struct], '    ')
                if len(module.params) > 0:
                    init_struct += "    {}_ = {}({});\n".format(module.name, module.name,
                                                                        ', '.join(module.params))
                else:
                    init_struct += "    {}_ = {}();\n".format(module.name, module.name)
                for cur_index in range(len(module.syms)):
                    sym = module.syms[cur_index]
                    if self.symtable[module.r_syms[cur_index]].is_function():
                        init_var += self.copy_func_impl(sym, module.r_syms[cur_index], module.name,
                                                                 self.symtable[module.r_syms[cur_index]])
                    else:
                        init_var += "        {} = {}_.{};\n".format(module.r_syms[cur_index], module.name, sym)
        return def_struct + init_struct + init_var

    def copy_func_impl(self, sym, r_syms, module_name, func_type):
        """implement function from other modules"""
        content_list = []
        if not func_type.is_overloaded():
            content_list.append("    {} = {}_.{};\n".format(r_syms, module_name, sym))
        else:
            for c_index in range(len(func_type.func_list)):
                c_type = func_type.func_list[c_index]
                c_name = func_type.fname_list[c_index]
                p_name = func_type.pre_fname_list[c_index]
                content_list.append("    {} = @{}_.{};\n".format(c_name, module_name, p_name))
        return ''.join(content_list)

    def get_struct_definition(self, init_content):
        ret_name = self.get_result_name()
        assign_list = []
        for parameter in self.lhs_list:
            if parameter in self.symtable and self.get_sym_type(parameter) is not None:
                assign_list.append("    {}.{} = {};".format(ret_name, parameter, parameter))
        for parameter in self.local_func_syms:
            assign_list.append("    {}.{} = @{};".format(ret_name, parameter, parameter))
        return "\n".join(assign_list) + self.get_used_params_content() + '\n'

    def get_ret_struct(self):
        return "{}({})".format(self.get_result_name(), ', '.join(self.lhs_list))

    def gen_same_seq_test(self):
        # dynamic seq
        test_content = []
        visited_sym_set = set()
        rand_int_max = 10
        subs_list = self.get_intersect_list()
        if len(subs_list) > 0:
            rand_name_dict = {}
            rand_def_dict = {}
            for keys in self.seq_dim_dict:
                new_name = self.generate_var_name(keys)
                rand_name_dict[keys] = new_name
                rand_def_dict[keys] = '            {} = randi({});'.format(new_name, rand_int_max)
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
                        cur_test_content.append('        for i = 1:{}'.format(self.get_sym_type(cur_sym).size))
                    dim_dict = new_seq_dim_dict[cur_sym]
                    defined_content.append('        {} = {{}};'.format(cur_sym, self.get_sym_type(cur_sym).size))
                    if self.get_sym_type(cur_sym).element_type.is_vector():
                        # determined
                        if self.get_sym_type(cur_sym).element_type.is_integer_element():
                            cur_block_content.append('            {} = [{}; randi({}, {})];'.format(cur_sym, cur_sym, rand_int_max, rand_name_dict[dim_dict[1]]))
                        else:
                            cur_block_content.append('            {} = [{}; randn({})];'.format(cur_sym, cur_sym, rand_name_dict[dim_dict[1]]))
                    else:
                        # matrix
                        row_str = self.get_sym_type(cur_sym).element_type.rows if not self.get_sym_type(cur_sym).element_type.is_dynamic_row() else rand_name_dict[dim_dict[1]]
                        col_str = self.get_sym_type(cur_sym).element_type.cols if not self.get_sym_type(cur_sym).element_type.is_dynamic_col() else rand_name_dict[dim_dict[2]]
                        if self.get_sym_type(cur_sym).element_type.is_integer_element():
                            cur_block_content.append('            {} = [{}; randi({}, {}, {})];'.format(cur_sym, cur_sym, rand_int_max, row_str, col_str))
                        else:
                            cur_block_content.append('            {} = [{}; randn({}, {})];'.format(cur_sym, cur_sym, row_str, col_str))
                cur_test_content = defined_content + cur_test_content + cur_block_content
                cur_test_content.append('        end')
                test_content += cur_test_content
        return visited_sym_set, test_content

    def gen_dim_content(self, rand_int_max=10):
        test_indent = "    "
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
                                    test_content.append(test_indent+"    {} = {};".format(key, self.randi_str(rand_int_max)))
                                else:
                                    test_content.append(test_indent+"    {} = {};".format(key, int_dim))
                                for same_key in cur_set:
                                    if same_key != key:
                                        dim_defined_list.append(same_key)
                                        if not isinstance(same_key, int):
                                            if int_dim == -1:
                                                test_content.append(test_indent+"    {} = {};".format(same_key, key))
                                            else:
                                                test_content.append(test_indent+"    {} = {};".format(same_key, int_dim))
                                break
                    else:
                        has_defined = True
                if not has_defined:
                    test_content.append(test_indent+"    {} = {};".format(key, self.randi_str(rand_int_max)))
                # +1 because sizes in matlab are 1-indexed
                if self.get_cur_param_data().symtable[target].is_sequence() and self.get_cur_param_data().symtable[target].element_type.is_dynamic():
                    if target_dict[target] == 0:
                        dim_content += "    {} = size({}, 1);\n".format(key, target)
                    else:
                        dim_content += "    {} = size({}{{1}}, {});\n".format(key, target, target_dict[target])
                else:
                    dim_content += "    {} = size({}, {});\n".format(key, target, target_dict[target]+1)
        return dim_defined_dict, test_content, dim_content

    def get_used_params_content(self):
        """Copy Parameters that are used in local functions as struct members"""
        assign_list = []
        for param in self.used_params:
            assign_list.append("    {}.{} = {};".format(self.get_result_name(), param, param))
        if len(assign_list) > 0:
            return '\n' + '    \n'.join(assign_list)
        else:
            return ''

    def get_param_content(self, test_indent, type_declare, test_generated_sym_set, rand_func_name):
        test_content = []
        doc = []
        test_function = [test_indent+"function [{}] = {}()".format(', '.join(self.parameters), rand_func_name)]
        type_checks = []
        rand_int_max = 10
        for parameter in self.parameters:
            if self.get_sym_type(parameter).desc:
                show_doc = True
                doc.append('    :param :{} :{}'.format(parameter, self.get_sym_type(parameter).desc))
            if self.get_sym_type(parameter).is_sequence():
                ele_type = self.get_sym_type(parameter).element_type
                data_type = ele_type.element_type
                if ele_type.is_matrix() and ele_type.sparse:
                    type_checks.append('    assert {}.shape == ({},)'.format(parameter, self.get_sym_type(parameter).size))
                    # Alec: I don't understand what this was doing for python,
                    # so I don't know if it would be important for matlab
                    # type_declare.append('    {} = np.asarray({})'.format(parameter, parameter))
                    test_content.append(test_indent+'    {} = [];'.format(parameter))
                    test_content.append(test_indent+'    for i = 1:{}'.format(self.get_sym_type(parameter).size))
                    if isinstance(data_type, LaVarType) and data_type.is_scalar() and data_type.is_int:
                        test_content.append(test_indent+
                            '        {}.append(sparse.random({}, {}, dtype=np.integer, density=0.25))'.format(parameter, ele_type.rows, ele_type.cols))
                    else:
                        test_content.append(test_indent+
                            '        {}.append(sparse.random({}, {}, dtype=np.float64, density=0.25))'.format(parameter, ele_type.rows,
                                                                                            ele_type.cols))
                else:
                    #size_str = ""
                    sizes = []
                    if ele_type.is_matrix():
                        if not ele_type.is_dynamic():
                            type_checks.append('    assert( isequal(size({}), [{}, {}, {}]) );'.format(parameter, self.get_sym_type(parameter).size, ele_type.rows, ele_type.cols))
                            #size_str = '{}, {}, {}'.format(self.get_sym_type(parameter).size, ele_type.rows, ele_type.cols)
                            sizes = [self.get_sym_type(parameter).size, ele_type.rows, ele_type.cols]
                        else:
                            if parameter not in test_generated_sym_set:
                                row_str = 'randi({})'.format(rand_int_max) if ele_type.is_dynamic_row() else ele_type.rows
                                col_str = 'randi({})'.format(rand_int_max) if ele_type.is_dynamic_col() else ele_type.cols
                                # sizes = [self.get_sym_type(parameter).size, row_str, col_str]
                                test_content.append('        {} = {{}};'.format(parameter))
                                test_content.append('        for i = 1:{}'.format(self.get_sym_type(parameter).size))
                                if ele_type.is_integer_element():
                                    test_content.append('            {} = [{}; randi({}, {}, {})];'.format(parameter, parameter, rand_int_max, row_str, col_str))
                                else:
                                    test_content.append('            {} = [{}; randn({}, {})];'.format(parameter, parameter, row_str, col_str))
                                test_content.append('        end')
                    elif ele_type.is_vector():
                        # type_checks.append('    assert {}.shape == ({}, {}, 1)'.format(parameter, self.get_sym_type(parameter).size, ele_type.rows))
                        # size_str = '{}, {}, 1'.format(self.get_sym_type(parameter).size, ele_type.rows)
                        if not ele_type.is_dynamic():
                            type_checks.append('    assert( isequal(size({}), [{}, {}]) );'.format(parameter, self.get_sym_type(parameter).size, ele_type.rows))
                            #size_str = '{}, {}'.format(self.get_sym_type(parameter).size, ele_type.rows)
                            sizes = [self.get_sym_type(parameter).size, ele_type.rows]
                        else:
                            if parameter not in test_generated_sym_set:
                                test_content.append('        {} = {{}};'.format(parameter))
                                test_content.append('        for i = 1:{}'.format(self.get_sym_type(parameter).size))
                                if ele_type.is_integer_element():
                                    test_content.append('            {} = [{}; randi({}, randi({}))];'.format(parameter, parameter, rand_int_max, rand_int_max))
                                else:
                                    test_content.append('            {} = [{}; randn(randi({}))];'.format(parameter, parameter, rand_int_max))
                                test_content.append('        end')
                                # sizes = [self.get_sym_type(parameter).size, 'randi({})'.format(rand_int_max)]
                    elif ele_type.is_scalar():
                        # Alec: is scalar? but then should
                        # self.get_sym_type(parameter).size always be 1? What's
                        # meant by "scalar" here?
                        #
                        # Force inputs to be treated as column vectors
                        type_declare.append('    {} = reshape({},[],1);'.format(parameter,parameter));
                        type_checks.append('    assert( size({},1) == {} );'.format(parameter, self.get_sym_type(parameter).size))
                        #size_str = '{}'.format(self.get_sym_type(parameter).size)
                        sizes = [self.get_sym_type(parameter).size]
                    if isinstance(data_type, LaVarType):
                        if data_type.is_scalar() and data_type.is_int:
                            #type_declare.append('    {} = np.asarray({}, dtype=np.int)'.format(parameter, parameter))
                            if parameter not in test_generated_sym_set and not ele_type.is_dynamic():
                                test_content.append('        {} = {};'.format(parameter, self.randi_str(rand_int_max,sizes)))
                        elif ele_type.is_set():
                            test_content.append('        {} = {{}};'.format(parameter))
                            test_content.append('        for i = 1:{}'.format(self.get_sym_type(parameter).size))
                            set_content = self.get_set_test_list("{}_tmp".format(parameter),
                                                                 self.generate_var_name("dim"), 'j', ele_type,
                                                                 rand_int_max, '    ')
                            set_content = ["        {}".format(line) for line in set_content]
                            test_content += set_content
                            test_content.append('            {} = [{}, {}];'.format(parameter, parameter, "{}_tmp".format(parameter)))
                            #test_content.append('    {} = np.asarray({})'.format(parameter, parameter))
                            test_content.append('        end')
                        else:
                            #type_declare.append('    {} = np.asarray({}, dtype=np.float64)'.format(parameter, parameter))
                            if parameter not in test_generated_sym_set and not ele_type.is_dynamic():
                                test_content.append('        {} = {};'.format(parameter, self.randn_str(sizes)))
                    else:
                        if ele_type.is_function():
                            test_content.append('        {} = {{}};'.format(parameter))
                            func_content = self.get_func_test_str("{}_f".format(parameter), ele_type, rand_int_max)
                            func_content = ["    {}".format(line) for line in func_content]
                            test_content += func_content
                            test_content.append('        for i = 1:{}'.format(self.get_sym_type(parameter).size))
                            test_content.append('            {}{{end+1,1}} = {};'.format(parameter, "{}_f".format(parameter)))
                            test_content.append('        end')
                            #test_content.append('    {} = np.asarray({})'.format(parameter, parameter))
                        else:
                            #type_declare.append('    {} = np.asarray({}, dtype={})'.format(parameter, parameter, "np.integer" if ele_type.is_integer_element() else "np.float64"))
                            test_content.append('        {} = {};'.format(parameter, self.randn_str(sizes)))
            elif self.get_sym_type(parameter).is_matrix():
                element_type = self.get_sym_type(parameter).element_type
                if isinstance(element_type, LaVarType):
                    if self.get_sym_type(parameter).sparse:
                        if element_type.is_scalar() and element_type.is_int:
                            test_content.append(test_indent+
                                '    {} = sparse.random({}, {}, dtype=np.integer, density=0.25)'.format(parameter, self.get_sym_type(parameter).rows,
                                                                          self.get_sym_type(parameter).cols))
                        else:
                            test_content.append(test_indent+
                                '    {} = sparse.random({}, {}, dtype=np.float64, density=0.25)'.format(parameter, self.get_sym_type(parameter).rows,
                                                                        self.get_sym_type(parameter).cols))
                    else:
                        # dense
                        if element_type.is_scalar() and element_type.is_int:
                            # Alec: I don't understand what this was doing for python,
                            # so I don't know if it would be important for matlab
                            #type_declare.append('    {} = np.asarray({}, dtype=np.integer)'.format(parameter, parameter))
                            test_content.append(test_indent+'    {} = randi({}, {}, {});'.format(parameter, rand_int_max, self.get_sym_type(parameter).rows, self.get_sym_type(parameter).cols))
                        else:
                            # Alec: I don't understand what this was doing for python,
                            # so I don't know if it would be important for matlab
                            #type_declare.append('    {} = np.asarray({}, dtype=np.float64)'.format(parameter, parameter))
                            test_content.append(test_indent+'    {} = randn({}, {});'.format(parameter, self.get_sym_type(parameter).rows, self.get_sym_type(parameter).cols))
                else:
                    if self.get_sym_type(parameter).sparse:
                        test_content.append(test_indent+
                            '    {} = sparse.random({}, {}, dtype=np.float64, density=0.25)'.format(parameter, self.get_sym_type(parameter).rows,
                                                                      self.get_sym_type(parameter).cols))
                    else:
                        type_checks.append('    {} = np.asarray({})'.format(parameter, parameter))
                        test_content.append(test_indent+'    {} = randn({}, {});'.format(parameter, self.get_sym_type(parameter).rows, self.get_sym_type(parameter).cols))
                type_checks.append('    assert( isequal(size({}), [{}, {}]) );'.format(parameter, self.get_sym_type(parameter).rows, self.get_sym_type(parameter).cols))
            elif self.get_sym_type(parameter).is_vector():
                element_type = self.get_sym_type(parameter).element_type
                type_declare.append('    {} = reshape({},[],1);'.format(parameter, parameter))
                if isinstance(element_type, LaVarType):
                    if element_type.is_scalar() and element_type.is_int:
                        #type_declare.append('    {} = np.asarray({}, dtype=np.integer)'.format(parameter, parameter))
                        test_content.append(test_indent+'    {} = randi({}, {});'.format(parameter, rand_int_max, self.get_sym_type(parameter).rows))
                    else:
                        #type_declare.append('    {} = np.asarray({}, dtype=np.float64)'.format(parameter, parameter))
                        test_content.append(test_indent+'    {} = randn({},1);'.format(parameter, self.get_sym_type(parameter).rows))
                else:
                    #type_declare.append('    {} = np.asarray({})'.format(parameter, parameter))
                    test_content.append(test_indent+'    {} = randn({},1)'.format(parameter, self.get_sym_type(parameter).rows))
                type_checks.append('    assert( numel({}) == {} );'.format(parameter, self.get_sym_type(parameter).rows))
                # type_checks.append('    assert {}.shape == ({}, 1)'.format(parameter, self.get_sym_type(parameter).rows))
                # test_content.append(test_indent+'    {} = {}.reshape(({}, 1))'.format(parameter, parameter, self.get_sym_type(parameter).rows))
            elif self.get_sym_type(parameter).is_scalar():
                type_checks.append('    assert(numel({}) == 1);'.format(parameter))
                if self.get_sym_type(parameter).is_int:
                    test_function.append(test_indent+'    {} = randi({});'.format(parameter, rand_int_max))
                else:
                    test_function.append(test_indent+'    {} = randn();'.format(parameter))
            elif self.get_sym_type(parameter).is_set():
                # turning off this check until deciding how sets will be
                # stored.
                #
                #type_checks.append('    assert isinstance({}, list) and len({}) > 0'.format(parameter, parameter))
                if self.get_sym_type(parameter).size > 1:
                    type_checks.append('    assert(size({},2) == {})'.format(parameter, self.get_sym_type(parameter).size))
                test_content += self.get_set_test_list(parameter, self.generate_var_name("dim"), 'i',
                                                       self.get_sym_type(parameter),
                                                       rand_int_max, '        ')
            elif self.get_sym_type(parameter).is_function():
                param_list = []
                dim_definition = []
                if self.get_sym_type(parameter).ret_template():
                    for ret_dim in self.get_sym_type(parameter).ret_symbols:
                        param_i = self.get_sym_type(parameter).template_symbols[ret_dim]
                        if self.get_sym_type(parameter).params[param_i].is_vector():
                            dim_definition.append('            {} = size({}{}, 1);'.format(ret_dim, self.param_name_test, param_i))
                        elif self.get_sym_type(parameter).params[param_i].is_matrix():
                            if ret_dim == self.get_sym_type(parameter).params[param_i].rows:
                                dim_definition.append('            {} = size({}{}, 1);'.format(ret_dim, self.param_name_test, param_i))
                            else:
                                dim_definition.append('            {} = size({}{}, 2);'.format(ret_dim, self.param_name_test, param_i))
                for index in range(len(self.get_sym_type(parameter).params)):
                    param_list.append('{}{}'.format(self.param_name_test, index))
                test_content.append(test_indent+"    {} = @{};".format(parameter,parameter+"Func"))
                test_content.append(test_indent+"    rseed = randi(2^32);")
                ret_list = []
                content_list = []
                for cur_index in range(len(self.get_sym_type(parameter).ret)):
                    cur_name = self.generate_var_name('ret')
                    ret_list.append(cur_name)
                    if self.get_sym_type(parameter).ret[cur_index].is_set():
                       content_list += self.get_set_test_list(cur_name, self.generate_var_name("dim"), 'i', self.get_sym_type(parameter).ret[cur_index], rand_int_max, '            ')
                    else:
                       content_list.append(test_indent+"        {} = {};".format(cur_name, self.get_rand_test_str(self.get_sym_type(parameter).ret[cur_index], rand_int_max)))

                test_content.append(test_indent+"    function [{}] =  {}({})".format(', '.join(ret_list), parameter+"Func", ', '.join(param_list)))
                test_content.append(test_indent+"        rng(rseed);")
                test_content += dim_definition
                test_content += content_list
                test_content.append(test_indent+"    end\n")
                # test_content.append(test_indent+'    {} = lambda {}: {}'.format(parameter, ', '.join(param_list), self.get_rand_test_str(self.get_sym_type(parameter).ret, rand_int_max)))
        return type_checks, doc, test_content, test_function

    def visit_block(self, node, **kwargs):
        type_declare = []
        show_doc = False
        rand_func_name = "generateRandomData"
        test_indent = "    "
        rand_int_max = 10
        # get dimension content
        dim_defined_dict, test_content, dim_content = self.gen_dim_content()
        # Handle sequences first
        test_generated_sym_set, seq_test_list = self.gen_same_seq_test()
        test_content += seq_test_list
        # get params content
        type_checks, doc, param_test_content, test_function = \
            self.get_param_content(test_indent, type_declare, test_generated_sym_set, rand_func_name)
        test_content += param_test_content
        #
        declaration_content = 'function {} = {}({})\n'.format(self.get_result_name(), self.func_name, ', '.join(self.parameters))
        comment_content = '% {} = {}({})\n%\n'.format(self.get_result_name(), self.func_name, ', '.join(self.parameters))
        comment_content += '%    {}'.format(  ('\n%    ').join(self.la_content.split('\n') ))
        comment_content += "\n"
        #if show_doc:
        #    content += '    %{\n' + '\n'.join(doc) + '\n    %}\n'

        content = ""
        # test
        test_function += test_content
        test_function.append(test_indent+'end')
        if not self.class_only:
            if len(self.parameters) > 0:
                content += '    if nargin==0\n'
                content += "        warning('generating random input data');\n"
                content += "        [{}] = {}();\n".format(', '.join(self.parameters), rand_func_name)
                content += '    end\n'
                content += '\n'.join(test_function)
                content += '\n\n'
        #else:
        #    # Alec: I don't understand what/when this would be doing something 
        #    content += "        {}();\n".format(rand_func_name)

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
        stats_content = self.get_module_str()
        for index in range(len(node.stmts)):
            ret_str = ''
            cur_stats_content = ''
            if index == len(node.stmts) - 1:
                if not node.stmts[index].is_node(IRNodeType.Assignment) and not node.stmts[index].is_node(IRNodeType.Destructuring) and not node.stmts[index].is_node(IRNodeType.Equation):
                    if node.stmts[index].is_node(IRNodeType.LocalFunc):
                        self.visit(node.stmts[index], **kwargs)
                        continue
                    elif node.stmts[index].is_node(IRNodeType.OdeFirstOrder):
                        cur_stats_content += self.visit(node.stmts[index], **kwargs).content
                        continue
                    kwargs[LHS] = self.ret_symbol
                    ret_str = "    " + self.ret_symbol + ' = '
            else:
                if not node.stmts[index].is_node(IRNodeType.Assignment) and not node.stmts[index].is_node(IRNodeType.Destructuring) and not node.stmts[index].is_node(IRNodeType.Equation):
                    # meaningless
                    if node.stmts[index].is_node(IRNodeType.LocalFunc):
                        self.visit(node.stmts[index], **kwargs)
                    elif node.stmts[index].is_node(IRNodeType.OdeFirstOrder):
                        cur_stats_content += self.visit(node.stmts[index], **kwargs).content
                    continue
            stat_info = self.visit(node.stmts[index], **kwargs)
            if stat_info.pre_list:
                cur_stats_content += "".join(stat_info.pre_list)
            cur_stats_content += ret_str + stat_info.content
            if index in node.meshset_list:
                mesh_content += cur_stats_content
            else:
                stats_content += cur_stats_content
            if index == len(node.stmts) - 1:
                if type(node.stmts[index]).__name__ != 'AssignNode':
                    stats_content += ';\n'
        mesh_dim_list = []
        for mesh, data in self.mesh_dict.items():
            mesh_dim_list.append("    {} = {}.n_vertices();\n".format(data.la_type.vi_size, mesh))
            mesh_dim_list.append("    {} = {}.n_edges();\n".format(data.la_type.ei_size, mesh))
            mesh_dim_list.append("    {} = {}.n_faces();\n".format(data.la_type.fi_size, mesh))
        stats_content += self.local_func_def + self.get_struct_definition('')
        content += stats_content

        content += "end\n"
        # convert special string in identifiers
        declaration_content = self.trim_content(declaration_content)
        content = self.trim_content(content)
        self.code_frame.struct = declaration_content + comment_content + ''.join(mesh_dim_list) + self.trim_content(mesh_content) + content
        return declaration_content + comment_content + ''.join(mesh_dim_list) + self.trim_content(mesh_content) + content

    def visit_summation(self, node, **kwargs):
        self.push_scope(node.scope_name)
        expr_sign = '-' if node.sign else ''
        target_var = []
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
                        name_convention[var] = "{}({}, {})".format(var_ids[0], var_ids[1][0], var_ids[1][1])
                    else:
                        name_convention[var] = "{}({})".format(var_ids[0], var_ids[1][0])
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
        # self.add_name_conventions(name_convention)
        #
        assign_id = node.symbol
        cond_content = ""
        if node.cond:
            cond_info = self.visit(node.cond, **kwargs)
            cond_content = "if " + cond_info.content + "\n"
        kwargs[WALK_TYPE] = WalkTypeEnum.RETRIEVE_EXPRESSION
        content = []
        exp_info = self.visit(node.exp)
        exp_str = exp_info.content
        assign_id_type = self.get_sym_type(assign_id)
        if assign_id_type.is_matrix():
            content.append("{} = zeros({}, {});\n".format(assign_id, assign_id_type.rows, assign_id_type.cols))
        elif assign_id_type.is_vector():
            content.append("{} = zeros({},1);\n".format(assign_id, assign_id_type.rows))
        elif assign_id_type.is_sequence():
            ele_type = assign_id_type.element_type
            content.append("{} = zeros({}, {}, {});\n".format(assign_id, assign_id_type.size, ele_type.rows, ele_type.cols))
        else:
            content.append("{} = 0;\n".format(assign_id))
        if node.enum_list:
            range_info = self.visit(node.range, **kwargs)
            range_name = self.generate_var_name('range')
            index_name = self.generate_var_name('index')
            content.append('{} = {};\n'.format(range_name, range_info.content))
            content.append('for {} = 1:length({})\n'.format(index_name, range_name))
            extra_content = ''
            if len(node.enum_list) == 1:
                content.append('    {} = {}({});\n'.format(node.enum_list[0], range_name, index_name))
            else:
                for i in range(len(node.enum_list)):
                    content.append('    {} = {}({}, {});\n'.format(node.enum_list[i], range_name, index_name, i+1))
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
            content.append(str("    " + assign_id + " = " + assign_id + " + " + expr_sign + exp_str + ';\n'))
            content[0] = "    " + content[0]
            content.append('end\n')
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
                "for {} = {}:{}\n".format(sub, lower_info.content, upper_info.content))
        else:
            # implicit range
            if self.get_sym_type(target_var[0]).is_matrix():
                if sub == sym_info[0]:
                    content.append("for {} = 1:size({},1)\n".format(sub, target_var[0]))
                else:
                    content.append("for {} = 1:size({},2)\n".format(sub, target_var[0]))
            elif self.get_sym_type(target_var[0]).is_sequence():
                sym_list = node.sym_dict[target_var[0]]
                sub_index = sym_list.index(sub)
                if sub_index == 0:
                    size_str = "{}, 1".format(target_var[0])
                elif sub_index == 1:
                    if self.get_sym_type(target_var[0]).element_type.is_dynamic_row():
                        size_str = "{}{{{}}}, 1".format(self.convert_bound_symbol(target_var[0]), sym_list[0])
                    else:
                        size_str = "{}".format(self.get_sym_type(target_var[0]).element_type.rows)
                else:
                    if self.get_sym_type(target_var[0]).element_type.is_dynamic_col():
                        size_str = "{}{{{}}}, 2".format(self.convert_bound_symbol(target_var[0]), sym_list[0])
                    else:
                        size_str = "{}".format(self.get_sym_type(target_var[0]).element_type.cols)
                content.append("for {} = 1:size({})\n".format(sub, size_str))
            else:
                content.append("for {} = 1:size({},1)\n".format(sub, self.convert_bound_symbol(target_var[0])))
        if exp_info.pre_list:   # catch pre_list
            list_content = "".join(exp_info.pre_list)
            # content += exp_info.pre_list
            list_content = list_content.split('\n')
            for index in range(len(list_content)):
                if index != len(list_content)-1:
                    content.append(list_content[index] + '\n')
        # exp_str
        if len(node.extra_list) > 0:
            for et in node.extra_list:
                extra_info = self.visit(et, **kwargs)
                content += [self.update_prelist_str([extra_info.content], '    ')]
        # only one sub for now
        indent = str("    ")
        if node.cond:
            content.append("    " + cond_content)
            indent += "  "
        content.append(str(indent + assign_id + " = " + assign_id + " + " + expr_sign + exp_str + ';\n'))
        content[0] = "    " + content[0]
        if node.cond:
            content.append("    end\n")
        content.append("end\n")
        self.pop_scope()
        return CodeNodeInfo(assign_id, pre_list=["    ".join(content)])

    def visit_union_sequence(self, node, **kwargs):
        self.push_scope(node.scope_name)
        target_var = []
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
                        name_convention[var] = "{}({}, {})".format(var_ids[0], var_ids[1][0], var_ids[1][1])
                    else:
                        name_convention[var] = "{}({})".format(var_ids[0], var_ids[1][0])
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
        # self.add_name_conventions(name_convention)
        #
        assign_id = node.symbol
        cond_content = ""
        if node.cond:
            cond_info = self.visit(node.cond, **kwargs)
            cond_content = "if " + cond_info.content + "\n"
        kwargs[WALK_TYPE] = WalkTypeEnum.RETRIEVE_EXPRESSION
        content = []
        exp_info = self.visit(node.exp)
        exp_str = exp_info.content
        assign_id_type = self.get_sym_type(assign_id)
        content.append("{} = [];\n".format(assign_id))
        if node.enum_list:
            range_info = self.visit(node.range, **kwargs)
            index_name = self.generate_var_name('index')
            content.append('for {} = 1:size({}, 1)\n'.format(index_name, range_info.content))
            extra_content = ''
            for i in range(len(node.enum_list)):
                content.append('    {} = {}({}, {});\n'.format(node.enum_list[i], range_info.content, index_name, i+1))
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
            content.append(str("    " + assign_id + " = " + "union({}, {})".format(assign_id, exp_str) + ';\n'))
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
                "for {} = {}:{}\n".format(sub, lower_info.content, upper_info.content))
        else:
            # implicit range
            content.append("for {} = 1:size({},1)\n".format(sub, self.convert_bound_symbol(target_var[0])))
        if exp_info.pre_list:   # catch pre_list
            list_content = "".join(exp_info.pre_list)
            # content += exp_info.pre_list
            list_content = list_content.split('\n')
            for index in range(len(list_content)):
                if index != len(list_content)-1:
                    content.append(list_content[index] + '\n')
        # exp_str
        if len(node.extra_list) > 0:
            for et in node.extra_list:
                extra_info = self.visit(et, **kwargs)
                content += [self.update_prelist_str([extra_info.content], '    ')]
        # only one sub for now
        indent = str("    ")
        if node.cond:
            content.append("    " + cond_content)
            indent += "  "
        content.append(str(indent + assign_id + " = " + "union({}, {})".format(assign_id, exp_str) + ';\n'))
        content[0] = "    " + content[0]
        if node.cond:
            content.append("    end\n")
        content.append("end\n")
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
        content = ""
        type_declare = []
        rand_func_name = "generateRandomData"
        test_indent = "    "
        # get dimension content
        dim_defined_dict, test_content, dim_content = self.gen_dim_content()
        # Handle sequences first
        test_generated_sym_set, seq_test_list = self.gen_same_seq_test()
        test_content += seq_test_list
        # get params content
        type_checks, doc, param_test_content, test_function = \
            self.get_param_content(test_indent, type_declare, test_generated_sym_set, rand_func_name)
        test_content += param_test_content
        #
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
        content += extra_expr
        name_list = []
        for cur_index in range(len(node.expr)):
            ret_n_list = []
            if node.expr[cur_index].la_type.is_tuple():
                for i in range(node.expr[cur_index].la_type.size):
                    ret_n_list.append(self.generate_var_name('ret'))
                name_list += ret_n_list
            else:
                cur_ret_name = self.generate_var_name('ret')
                ret_n_list.append(cur_ret_name)
                name_list.append(cur_ret_name)
            expr_info = self.visit(node.expr[cur_index], **kwargs)
            if len(expr_info.pre_list) > 0:
                content += self.update_prelist_str(expr_info.pre_list, "    ")
            if not node.expr[0].is_node(IRNodeType.MultiConds):
                if node.expr[cur_index].la_type.is_tuple():
                    tuple_name = self.generate_var_name('tuple')
                    content += '        {} = {};\n'.format(tuple_name, expr_info.content)
                    for i in range(node.expr[cur_index].la_type.size):
                        content += '        {} = {}({});\n'.format(ret_n_list[i], tuple_name, i+1)
                else:
                    content += '        {} = {};\n'.format(','.join(ret_n_list), expr_info.content)
        content += '    end\n\n'
        self.local_func_def += "    function [{}] = {}({})\n".format(', '.join(name_list), node.identity_name, ", ".join(param_list)) + content
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
            content = "abs({})".format(value)
        elif type_info.la_type.is_vector():
            if node.norm_type == NormType.NormDet:
                content = "det({})".format(value)
            elif node.norm_type == NormType.NormInteger:
                if node.sub is None:
                    content = "norm({}, {})".format(value, 2)
                else:
                    content = "norm({}, {})".format(value, node.sub)
            elif node.norm_type == NormType.NormMax:
                content = "norm({}, inf)".format(value)
            elif node.norm_type == NormType.NormIdentifier:
                sub_info = self.visit(node.sub, **kwargs)
                pre_list += sub_info.pre_list
                if node.sub.la_type.is_scalar():
                    content = "norm({}, {})".format(value, sub_info.content)
                else:
                    content = "sqrt(({})' * {} * ({}))".format(value, sub_info.content, value)
        elif type_info.la_type.is_matrix():
            if node.norm_type == NormType.NormDet:
                content = "det({})".format(value)
            elif node.norm_type == NormType.NormFrobenius:
                content = "norm({}, 'fro')".format(value)
            elif node.norm_type == NormType.NormNuclear:
                content = "norm(svd({}),1)".format(value)
        elif type_info.la_type.is_set():
            content = "size({}, 1)".format(value)
        return CodeNodeInfo(content, pre_list)

    def visit_transpose(self, node, **kwargs):
        f_info = self.visit(node.f, **kwargs)
        #if node.f.la_type.is_vector():
        #    f_info.content = "reshape({},1,[])".format(f_info.content)
        #else:
        #    f_info.content = "{}'".format(f_info.content)
        f_info.content = "{}'".format(f_info.content)
        return f_info

    def visit_pseudoinverse(self, node, **kwargs):
        f_info = self.visit(node.f, **kwargs)
        f_info.content = "pinv({})".format(f_info.content)
        return f_info

    def visit_squareroot(self, node, **kwargs):
        f_info = self.visit(node.value, **kwargs)
        f_info.content = "sqrt({})".format(f_info.content)
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
            base_info.content = "{}'".format(base_info.content)
        elif node.r:
            if node.la_type.is_scalar():
                base_info.content = "1 / ({})".format(base_info.content)
            else:
                base_info.content = "inv({})".format(base_info.content)
        else:
            power_info = self.visit(node.power, **kwargs)
            if node.base.la_type.is_scalar():
                base_info.content = "{}.^{}".format(base_info.content, power_info.content)
            else:
                base_info.content = "{}^{}".format(base_info.content, power_info.content)
        return base_info

    def visit_solver(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.pre_list += right_info.pre_list
        # parenthesis are important! we're replacing a "power" (higher
        # precedence than multiplication) with a "division" (equal precedence
        # with multiplication)
        left_info.content = "(({})\({}))".format(left_info.content, right_info.content)
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
            pre_list.append('    else\n')
            if func_ret:
                pre_list.append('        {} = {};\n'.format('ret', other_info.content))
            else:
                pre_list.append('        {} = {};\n'.format(name, other_info.content))
        pre_list.append('    end\n')
        return CodeNodeInfo(cur_m_id, pre_list)

    def visit_sparse_matrix(self, node, **kwargs):
        op_type = kwargs[ASSIGN_TYPE]
        lhs = kwargs[LHS]
        type_info = node
        cur_m_id = type_info.symbol
        pre_list = []
        index_var = type_info.la_type.index_var
        value_var = type_info.la_type.value_var
        pre_list.append("    {} = zeros(2,0);\n".format(index_var))
        pre_list.append("    {} = zeros(1,0);\n".format(value_var))
        if_info = self.visit(node.ifs, **kwargs)
        pre_list += if_info.content
        # assignment
        if op_type == '=':
            pre_list.append("    {} = sparse({}(1,:),{}(2,:),{},{},{});\n".format(cur_m_id, index_var, index_var, value_var, self.get_sym_type(cur_m_id).rows,
                                                          self.get_sym_type(cur_m_id).cols))
        elif op_type == '+=':
            # left_ids = self.get_all_ids(lhs)
            # left_subs = left_ids[1]
            pre_list.append(
                "    {} = scipy.sparse.coo_matrix(({}+{}.data.tolist(), np.hstack((np.asarray({}).T, np.asarray(({}.row, {}.col))))), shape=({}, {}))\n".format(cur_m_id, value_var, cur_m_id,
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
            ret = ["    for {} = 1:{}\n".format(subs[0], sparse_node.la_type.rows),
                   "        for {} = 1:{}\n".format(subs[1], sparse_node.la_type.cols)]
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
                ret += '            end\n'
                ret += "        end\n"
                ret += "    end\n"
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
            stat_content = stat_content.replace('_{}{}'.format(subs[0], subs[1]), '({},{})'.format(subs[0], subs[1]))
            if node.loop:
                content += stat_info.pre_list
                content.append(cond_info.content)
                content.append('    {}(1:2,end+1) = [{};{}];\n'.format(sparse_node.la_type.index_var, subs[0], subs[1]))
                content.append('    {}(end+1) = {};\n'.format(sparse_node.la_type.value_var, stat_content))
                content.append('end\n')
            else:
                content.append('{} {}\n'.format("if" if node.first_in_list else "elseif",cond_info.content))
                # https://www.mathworks.com/matlabcentral/answers/392985-why-does-is-take-o-n-2-to-append-elements-in-matlab-when-it-takes-o-n-amortized-time-in-theory#comment_1520858
                content.append('    {}(1:2,end+1) = [{};{}];\n'.format(sparse_node.la_type.index_var, subs[0], subs[1]))
                content.append('    {}(end+1) = {};\n'.format(   sparse_node.la_type.value_var, stat_content))
            self.convert_matrix = False
        else:
            cond_info = self.visit(node.cond, **kwargs)
            stat_info = self.visit(node.stat, **kwargs)
            content = cond_info.pre_list
            stat_content = stat_info.content
            content.append('{} {}\n'.format("if" if node.first_in_list else "elseif", cond_info.content))
            content += stat_info.pre_list
            if assign_node is None:
                content.append("    ret = {};\n".format(stat_content))
            else:
                content.append("    {} = {};\n".format(self.visit(assign_node.left[0], **kwargs).content, stat_content))
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
        content = '[{}]'.format("; ".join(ret))
        return CodeNodeInfo(content, pre_list=pre_list)

    def visit_set(self, node, **kwargs):
        self.push_scope(node.scope_name)
        cur_m_id = node.symbol
        ret = []
        pre_list = []
        if node.enum_list and len(node.enum_list) > 0:
            pre_list.append('    {} = [];\n'.format(cur_m_id))
            #
            range_info = self.visit(node.range, **kwargs)
            range_name = self.generate_var_name('range')
            pre_list.append('    {} = {};\n'.format(range_name, range_info.content))
            index_name = self.generate_var_name('index')
            pre_list.append('    for {} = 1:length({})\n'.format(index_name, range_name))
            extra_content = ''
            for i in range(len(node.enum_list)):
                pre_list.append(
                    '        {} = {}({});\n'.format(node.enum_list[i], range_name, index_name))
            exp_pre_list = []
            exp_info = self.visit(node.items[0], **kwargs)
            if exp_info.pre_list:  # catch pre_list
                list_content = "".join(exp_info.pre_list)
                # content += exp_info.pre_list
                list_content = list_content.split('\n')
                for index in range(len(list_content)):
                    if index != len(list_content) - 1:
                        exp_pre_list.append(list_content[index] + '\n')
            #
            pre_list += exp_pre_list
            if node.cond:
                cond_info = self.visit(node.cond, **kwargs)
                cond_content = "        if " + cond_info.content + "\n"
                pre_list += cond_content
                pre_list.append("            {} = [{}; {}];\n".format(cur_m_id, cur_m_id, exp_info.content))
                pre_list.append("        end\n")
            else:
                pre_list.append("        {} = [{}; {}];\n".format(cur_m_id, cur_m_id, exp_info.content))
            pre_list.append("    end\n")
            content = cur_m_id
        else:
            for item in node.items:
                item_info = self.visit(item, **kwargs)
                ret.append(item_info.content)
                pre_list += item_info.pre_list
            content = '[{}]'.format(", ".join(ret))
        self.pop_scope()
        return CodeNodeInfo(content, pre_list=pre_list)

    def visit_to_matrix(self, node, **kwargs):
        node_info = self.visit(node.item, **kwargs)
        node_info.content = "reshape({}, [{}, 1])".format(node_info.content, node.item.la_type.rows)
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
                                func_name = 'zeros'
                            elif ret[i][j] == '1':
                                func_name = 'ones'
                            elif 'I' in ret[i][j] and 'I' not in self.symtable:
                                # todo: assert in type checker
                                assert dims[0] == dims[1], "I must be square matrix"
                                ret[i][j] = ret[i][j].replace('I', 'speye({})'.format(dims[0]))
                                continue
                            else:
                                func_name = ret[i][j] + ' * ones'
                            if dims[1] == 1:
                                # vector
                                ret[i][j] = '{}({}, 1)'.format(func_name, dims[0])
                            else:
                                ret[i][j] = '{}({}, {})'.format(func_name, dims[0], dims[1])
                for j in range(len(ret[i])):
                    # vector type needs to be reshaped as matrix inside block matrix
                    if node.la_type.item_types and node.la_type.item_types[i][j].la_type.is_vector():
                        ret[i][j] = 'reshape({}, [{}, 1])'.format(ret[i][j], node.la_type.item_types[i][j].la_type.rows)
                all_rows.append('[' + ', '.join(ret[i]) + ']')
            # matrix
            #if self.get_sym_type(cur_m_id).sparse and self.get_sym_type(cur_m_id).block:
            #    m_content += 'sparse.bmat([{}])'.format(', '.join(all_rows))
            #    if len(ret) > 1 and len(ret[0]) > 1:
            #        content += '{} = {}\n'.format(cur_m_id, m_content)
            #    elif len(ret) == 1 and len(ret[0]) != 1:  # one row one col -> vstack
            #        # single row
            #        content += '{} = sparse.hstack(({}))\n'.format(cur_m_id, ', '.join(ret[0]))
            #    else:
            #        # single col
            #        for i in range(len(ret)):
            #            ret[i] = ''.join(ret[i])
            #        content += '{} = sparse.vstack(({}))\n'.format(cur_m_id, ', '.join(ret))
            #else:
            #    # dense
            m_content += '[{}]'.format('; '.join(all_rows))
            #Alec: why would we ever not output the assignment?
            #if len(ret) > 1 and len(ret[0]) > 1:
            content += '{} = {};\n'.format(cur_m_id, m_content)
            #elif len(ret) == 1 and len(ret[0]) != 1:  # one row one col -> vstack
            #    # single row
            #    content += '{} = np.hstack(({}))\n'.format(cur_m_id, ', '.join(ret[0]))
            #else:
            #    # single col
            #    for i in range(len(ret)):
            #        ret[i] = ''.join(ret[i])
            #    content += '{} = np.vstack(({}))\n'.format(cur_m_id, ', '.join(ret))
        else:
            # dense
            content += '{} = zeros({}, {});\n'.format(cur_m_id, self.get_sym_type(cur_m_id).rows,
                                                          self.get_sym_type(cur_m_id).cols)
            for i in range(len(ret)):
                content += "    {}({},:) = [{}];\n".format(cur_m_id, i+1, ', '.join(ret[i]))
        #####################
        pre_list = [content]
        if ret_info.pre_list:
            pre_list = ret_info.pre_list + pre_list
        return CodeNodeInfo(cur_m_id, pre_list)

    def visit_num_matrix(self, node, **kwargs):
        post_s = ''
        if node.id:
            func_name = "speye"
        else:
            if node.left == '0':
                func_name = "zeros"
            elif node.left == '1' or node.left == '𝟙':
                func_name = "ones"
            # else:
            #     func_name = "({} * np.ones".format(left_info.content)
            #     post_s = ')'
        id1_info = self.visit(node.id1, **kwargs)
        if node.id2:
            id2_info = self.visit(node.id2, **kwargs)
            content = "{}({}, {})".format(func_name, id1_info.content, id2_info.content)
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
                row_content = "{}".format(row_info.content)
            if node.col_index is not None:
                col_info = self.visit(node.col_index, **kwargs)
                if node.col_index.la_type.index_type:
                    col_content = col_info.content
                else:
                    col_content = "{}".format(col_info.content)
                if self.get_sym_type(main_info.content).sparse:
                    content = "{}({}, {})".format(main_info.content, row_content, col_content)
                else:
                    content = "{}({}, {})".format(main_info.content, row_content, col_content)
            else:
                content = "{}({}, :)'".format(main_info.content, row_content)
        else:
            col_info = self.visit(node.col_index, **kwargs)
            if node.col_index.la_type.index_type:
                content = "{}(:, {})".format(main_info.content, col_info.content)
            else:
                content = "{}(:, {})".format(main_info.content, col_info.content)
        return CodeNodeInfo(content)

    def visit_vector_index(self, node, **kwargs):
        main_info = self.visit(node.main, **kwargs)
        index_info = self.visit(node.row_index, **kwargs)
        if node.row_index.la_type.index_type:
            return CodeNodeInfo("{}({})".format(main_info.content, index_info.content))
        else:
            return CodeNodeInfo("{}({})".format(main_info.content, index_info.content))

    def visit_set_index(self, node, **kwargs):
        main_info = self.visit(node.main, **kwargs)
        index_info = self.visit(node.row_index, **kwargs)
        if node.row_index.la_type.index_type:
            return CodeNodeInfo("{}({})".format(main_info.content, index_info.content))
        else:
            return CodeNodeInfo("{}({})".format(main_info.content, index_info.content))

    def visit_tuple_index(self, node, **kwargs):
        main_info = self.visit(node.main, **kwargs)
        index_info = self.visit(node.row_index, **kwargs)
        if node.row_index.la_type.index_type:
            return CodeNodeInfo("{}({})".format(main_info.content, index_info.content))
        else:
            return CodeNodeInfo("{}({})".format(main_info.content, index_info.content))

    def visit_sequence_index(self, node, **kwargs):
        # Alec: cells in matlab are rarely used for numeric types that would
        # otherwise fit into an array. So below I'm going to use the types are
        # really matrices. I'm guessing this will cause issues eventually for
        # "ragged arrays".
        # 
        # https://github.com/pressureless/linear_algebra/issues/34
        main_info = self.visit(node.main, **kwargs)
        main_index_content = self.visit(node.main_index, **kwargs).content
        if node.slice_matrix:
            if node.row_index is not None:
                row_content = self.visit(node.row_index, **kwargs).content
                if self.get_sym_type(main_info.content).is_dynamic():
                    content = "{}{{{}}}({}, :)".format(main_info.content, main_index_content, row_content)
                else:
                    content = "{}({})({}, :)".format(main_info.content, main_index_content, row_content)
            else:
                col_content = self.visit(node.col_index, **kwargs).content
                if self.get_sym_type(main_info.content).is_dynamic():
                    content = "{}{{{}}}(:, {})".format(main_info.content, main_index_content, col_content)
                else:
                    content = "{}({})(:, {})".format(main_info.content, main_index_content, col_content)
        else:
            if node.row_index is not None:
                row_content = self.visit(node.row_index, **kwargs).content
                if node.col_index is not None:
                    col_content = self.visit(node.col_index, **kwargs).content
                    if self.get_sym_type(main_info.content).is_dynamic():
                        content = "{}{{{}}}({},{})".format(main_info.content, main_index_content, row_content,
                                                        col_content)
                    else:
                        content = "{}({},{},{})".format(main_info.content, main_index_content, row_content,
                                                         col_content)
                else:
                    if self.get_sym_type(main_info.content).is_dynamic():
                        content = "{}{{{}}}({})".format(main_info.content, main_index_content, row_content)
                    else:
                        content = "{}({},{})".format(main_info.content, main_index_content, row_content)
            else:
                if self.get_sym_type(main_info.content).is_dynamic():
                    content = "{}{{{}}}".format(main_info.content, main_index_content)
                else:
                    if node.la_type.is_vector():
                        # This is ugly if we're visiting the lefthand side of an
                        # equality expression
                        content = "{}({},:)'".format(main_info.content, main_index_content)
                    elif node.la_type.is_matrix():
                        content = "squeeze({}({},:,:))".format(main_info.content, main_index_content)
                    elif node.la_type.is_scalar():
                        content = "{}({})".format(main_info.content, main_index_content)
                    else:
                        content = "{}{{{}}}".format(main_info.content, main_index_content)
        return CodeNodeInfo(content)

    def visit_seq_dim_index(self, node, **kwargs):
        main_index_info = self.visit(node.main_index, **kwargs)
        if node.is_row_index():
            content = "size({}({}), 1)".format(node.real_symbol, main_index_info.content)
        else:
            content = "size({}({}), 2)".format(node.real_symbol, main_index_info.content)
        return CodeNodeInfo(content)

    def visit_add_sub(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = left_info.content + ' +- ' + right_info.content
        left_info.pre_list += right_info.pre_list
        return left_info

    def visit_mul(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        l_info = node.left
        r_info = node.right
        mul = ' * '
        if l_info.la_type.is_matrix() or l_info.la_type.is_vector():
            if r_info.la_type.is_matrix() or r_info.la_type.is_vector():
                mul = ' * '
        left_info.content = left_info.content + mul + right_info.content
        left_info.pre_list += right_info.pre_list
        return left_info

    def visit_div(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = left_info.content + ' / ' + right_info.content
        left_info.pre_list += right_info.pre_list
        return left_info

    def visit_union(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = "union({}, {})".format(left_info.content, right_info.content)
        return left_info

    def visit_intersection(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = "intersect({}, {})".format(left_info.content, right_info.content)
        return left_info

    def visit_difference(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = "setdiff({}, {})".format(left_info.content, right_info.content)
        return left_info

    def visit_cast(self, node, **kwargs):
        value_info = self.visit(node.value, **kwargs)
        if node.la_type.is_scalar():
            #value_info.content = "({}).item()".format(value_info.content)
            # seems like a python/eigen problem. what else is being cast?
            value_info.content = "{}".format(value_info.content)
        return value_info

    def visit_equation(self, node, **kwargs):
        return CodeNodeInfo("")

    def visit_destructuring(self, node, **kwargs):
        right_info = self.visit(node.right[0], **kwargs)
        rhs = self.generate_var_name("rhs")
        lhs_list = []
        for cur_index in range(len(node.left)):
            id0_info = self.visit(node.left[cur_index], **kwargs)
            lhs_list.append(id0_info.content)
            # expr = ''
            # if node.cur_type == DestructuringType.DestructuringSet:
            #     expr = '{}({})'.format(rhs, cur_index+1)
            # elif node.cur_type == DestructuringType.DestructuringSequence:
            #     expr = '{}({})'.format(rhs, cur_index+1)
            # elif node.cur_type == DestructuringType.DestructuringVector:
            #     expr = '{}({})'.format(rhs, cur_index+1)
            # elif node.cur_type == DestructuringType.DestructuringTuple or node.cur_type == DestructuringType.DestructuringList:
            #     expr = '{}({})'.format(rhs, cur_index+1)
            # content += "    {} = {};\n".format(id0_info.content, expr)
        content = "    [{}] = {};\n".format(', '.join(lhs_list), right_info.content)
        return CodeNodeInfo(content, right_info.pre_list)

    def visit_assignment(self, node, **kwargs):
        if node.cur_type == AssignType.AssignTypeSolver:
            return CodeNodeInfo("")
        type_info = node
        # visit matrix first
        placeholder = "{}_{}\n".format(self.comment_placeholder, node.parse_info.line)
        self.comment_dict[placeholder] = self.update_prelist_str([node.raw_text], '    % ')
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
            lhs_content = ', '.join(lhs_list)
            if len(lhs_list) > 1:
                lhs_content = "[{}]".format(lhs_content)
            content += "    {} = {};\n".format(lhs_content, right_info.content)
        else:
            if len(node.left) > 1 and len(node.right) == 1:
                # only accept direct assignment, without subscript
                rhs_node = node.right[0]
                tuple_name = self.generate_var_name("tuple")
                right_info = self.visit(rhs_node, **kwargs)
                if right_info.pre_list:
                    content += self.update_prelist_str(right_info.pre_list, "    ")
                # content += "    {} = {};\n".format(tuple_name, right_info.content)
                var_list = []
                for cur_index in range(len(node.left)):
                    left_info = self.visit(node.left[cur_index], **kwargs)
                    var_list.append(left_info.content)
                    # content += "    {} = {}({});\n".format(left_info.content, tuple_name, cur_index+1)
                    self.declared_symbols.add(node.left[cur_index].get_main_id())
                content += "    [{}] = {};\n".format(','.join(var_list), right_info.content)
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
                                    content += "    {} = zeros(2,0);\n".format(self.get_sym_type(sequence).index_var)
                                    content += "    {} = zeros(1,0);\n".format(self.get_sym_type(sequence).value_var)
                                content += "    for {} = 1:{}\n".format(left_subs[0], self.get_sym_type(sequence).rows)
                                if right_info.pre_list:
                                    content += self.update_prelist_str(right_info.pre_list, "    ")
                                # https://www.mathworks.com/matlabcentral/answers/392985-why-does-is-take-o-n-2-to-append-elements-in-matlab-when-it-takes-o-n-amortized-time-in-theory#comment_1520858
                                content += "        {}(1:2,end+1) = [{};{}];\n".format(self.get_sym_type(sequence).index_var, left_subs[0], left_subs[0])
                                content += "        {}(end+1) = {};\n".format(self.get_sym_type(sequence).value_var, right_info.content)
                                content += "    end\n"
                                content += "    {} = sparse({}(1,:),{}(2,:),{},{},{});\n".format(
                                    sequence,
                                    self.get_sym_type(sequence).index_var,
                                    self.get_sym_type(sequence).index_var,
                                    self.get_sym_type(sequence).value_var,
                                    self.get_sym_type( sequence).rows,
                                    self.get_sym_type( sequence).cols)
                            else:  # L_ij
                                if right_info.pre_list:
                                    content += "".join(right_info.pre_list)
                                # sparse mat assign
                                right_exp += '    ' + sequence + ' = ' + right_info.content + ';\n'
                                content += right_exp
                        elif left_subs[0] == left_subs[1]:
                            # L_ii
                            content = ""
                            content += "    for {} = 1:{}\n".format(left_subs[0], self.get_sym_type(sequence).rows)
                            if right_info.pre_list:
                                content += self.update_prelist_str(right_info.pre_list, "    ")
                            content += "        {}({}, {}) = {};\n".format(sequence, left_subs[0], left_subs[0], right_info.content)
                            content += "    end\n"
                        else:
                            for right_var in type_info.symbols:
                                if sub_strs in right_var:
                                    var_ids = self.get_all_ids(right_var)
                                    right_info.content = right_info.content.replace(right_var, "{}({}, {})".format(var_ids[0], var_ids[1][0], var_ids[1][1]))
                            if left_subs[0] == '*':
                                right_exp += "    {}(:, {}) = {}".format(self.get_main_id(left_id), left_subs[1], right_info.content)
                            elif left_subs[1] == '*':
                                right_exp += "    {}({}, :) = {}".format(self.get_main_id(left_id), left_subs[0], right_info.content)
                            else:
                                right_exp += "    {}({}, {}) = {}".format(self.get_main_id(left_id), left_subs[0], left_subs[1], right_info.content)
                            if self.get_sym_type(sequence).is_matrix():
                                if node.op == '=':
                                    # declare
                                    content += "    {} = zeros({}, {});\n".format(sequence,
                                                                                      self.get_sym_type(sequence).rows,
                                                                                      self.get_sym_type(sequence).cols)
                            if left_subs[0] == '*':
                                content += "    for {} = 1:{}\n".format(left_subs[1], self.get_sym_type(sequence).cols)
                                if right_info.pre_list:
                                    content += self.update_prelist_str(right_info.pre_list, "    ")
                                content += "    " + right_exp + ';\n'
                                content += "    end\n"
                            elif left_subs[1] == '*':
                                content += "    for {} = 1:{}\n".format(left_subs[0], self.get_sym_type(sequence).rows)
                                if right_info.pre_list:
                                    content += self.update_prelist_str(right_info.pre_list, "    ")
                                content += "    " + right_exp + ';\n'
                                content += "    end\n"
                            else:
                                content += "    for {} = 1:{}\n".format(left_subs[0], self.get_sym_type(sequence).rows)
                                content += "        for {} = 1:{}\n".format(left_subs[1], self.get_sym_type(sequence).cols)
                                if right_info.pre_list:
                                    content += self.update_prelist_str(right_info.pre_list, "        ")
                                content += "        " + right_exp + ';\n'
                                content += "        end\n"
                                content += "    end\n"
                                # content += '\n'
                    elif len(left_subs) == 1: # sequence only
                        sequence = left_ids[0]  # y left_subs[0]
                        # replace sequence
                        for right_var in type_info.symbols:
                            if self.contain_subscript(right_var):
                                var_ids = self.get_all_ids(right_var)
                                right_info.content = right_info.content.replace(right_var, "{}[{}]".format(var_ids[0], var_ids[1][0]))

                        # ugly hack to deal with visit_sequence_index using ' on lists
                        # of vectors sotred in rows of matrix... Similar problem will
                        # happen for matrices and squeeze.
                        left_content = left_info.content
                        right_content = right_info.content
                        if left_content[-1] == "'":
                            left_content = left_content[:-1]
                            right_content = "({})'".format(right_content);
                        right_exp += "    {} = {}".format(left_content,right_content);
                        ele_type = self.get_sym_type(sequence).element_type
                        if self.get_sym_type(sequence).is_sequence():
                            if ele_type.is_matrix():
                                content += "    {} = zeros({}, {}, {});\n".format(sequence, self.get_sym_type(sequence).size, ele_type.rows, ele_type.cols)
                            elif ele_type.is_vector():
                                content += "    {} = zeros({}, {});\n".format(sequence, self.get_sym_type(sequence).size, ele_type.rows)
                            else:
                                content += "    {} = zeros({},1);\n".format(sequence, self.get_sym_type(sequence).size)
                            content += "    for {} = 1:{}\n".format(left_subs[0], self.get_sym_type(sequence).size)
                        else:
                            # vector
                            content += "    {} = zeros({},1);\n".format(sequence, self.get_sym_type(sequence).rows)
                            content += "    for {} = 1:{}\n".format(left_subs[0], self.get_sym_type(sequence).rows)
                        if right_info.pre_list:
                            content += self.update_prelist_str(right_info.pre_list, "    ")
                        content += "    " + right_exp+";\n"
                        content += "    end\n"
                #
                else:
                    if right_info.pre_list:
                        content += "".join(right_info.pre_list)
                    op = ' = '
                    if node.op == '+=':
                        op = ' += '
                    if not node.right[cur_index].is_node(IRNodeType.MultiConds):
                        right_exp += '    ' + self.get_main_id(left_id) + op + right_info.content
                    if right_exp != '':
                        content += right_exp + ';\n'
                la_remove_key(LHS, **kwargs)
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
                content = ' && '.join(content_list)
            else:
                content = ' || '.join(content_list)
            return CodeNodeInfo(content=content, pre_list=pre_list)
        return self.visit(node.cond_list[0])

    def visit_in(self, node, **kwargs):
        item_list = []
        pre_list = []
        right_info = self.visit(node.set, **kwargs)
        if node.set.la_type.index_type:
            for item in node.items:
                item_info = self.visit(item, **kwargs)
                item_content = item_info.content
                if not item.la_type.index_type:
                    item_content = "{}".format(item_info.content)
                item_list.append(item_content)
        else:
            for item in node.items:
                item_info = self.visit(item, **kwargs)
                if not item.la_type.index_type:
                    item_content = "{}".format(item_info.content)
                else:
                    item_content = "{}+1".format(item_info.content)
                item_list.append(item_content)
        if node.loop:
            index_name = self.generate_var_name('index')
            content = 'for {} = 1:size({}, 1)\n'.format(index_name, right_info.content)
            content += '    {} = {}({}, 1);\n'.format(item_list[0], right_info.content, index_name)
            content += '    {} = {}({}, 2);\n'.format(item_list[1], right_info.content, index_name)
        else:
            content = 'ismember([' + ', '.join(item_list) + '],' + right_info.content+",'rows')"
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
                    item_content = "{}".format(item_info.content)
                item_list.append(item_content)
        else:
            for item in node.items:
                item_info = self.visit(item, **kwargs)
                if not item.la_type.index_type:
                    item_content = "{}".format(item_info.content)
                else:
                    item_content = "{}+1".format(item_info.content)
                item_list.append(item_content)
        content = '~ismember([' + ', '.join(item_list) + '],' + right_info.content+",'rows')"
        return CodeNodeInfo(content=content, pre_list=pre_list)

    def get_bin_comp_str(self, comp_type):
        op = ''
        if comp_type == IRNodeType.Eq:
            op = '=='
        elif comp_type == IRNodeType.Ne:
            op = '~='
        elif comp_type == IRNodeType.Lt:
            op = '<'
        elif comp_type == IRNodeType.Le:
            op = '<='
        elif comp_type == IRNodeType.Gt:
            op = '>'
        elif comp_type == IRNodeType.Ge:
            op = '>='
        return op

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
        return CodeNodeInfo("")

    def visit_laplace(self, node, **kwargs):
        return CodeNodeInfo("")

    def visit_partial(self, node, **kwargs):
        return CodeNodeInfo("")

    def visit_first_order_ode(self, node, **kwargs):
        self.visiting_diff_eq = True
        target_name = self.generate_var_name("target")
        content = "    function ret = {}({}, {})\n".format(target_name, node.param, node.func)
        content += "        ret = {};\n".format(self.visit(node.expr, **kwargs).content)
        content += "    end\n"
        content += "    function ret = {}(d{})\n".format(node.func, node.param)
        if len(node.init_list) > 0:
            self.visiting_diff_init = True
            lhs = []
            rhs = []
            for eq_node in node.init_list:
                for l_index in range(len(eq_node.left)):
                    lhs.append(self.visit(eq_node.left[l_index]).content)
                    rhs.append(self.visit(eq_node.right[l_index]).content)
            self.visiting_diff_init = False
            content += "        [{}, {}] = ode23(@{}, [{}, d{}], [{}]);\n".format(node.param, node.func, target_name, lhs[0], node.param, rhs[0])
            content += "        ret = {}(length({}));\n".format(node.func, node.func)
            content += "    end\n"
        self.visiting_diff_eq = False
        return CodeNodeInfo(content)

    def visit_optimize(self, node, **kwargs):
        self.opt_key = node.key
        id_list = []
        pack_list = []
        unpack_list = []
        init_str_list = []
        base_str_list = []
        for cur_index in range(len(node.base_list)):
            cur_la_type = node.base_type_list[cur_index].la_type
            id_info = self.visit(node.base_list[cur_index], **kwargs)
            id_list.append(id_info.content)
            if cur_la_type.is_scalar():
                init_value = 0
                base_str = "    {} = optimvar('{}');\n".format(id_info.content, id_info.content)
            elif cur_la_type.is_vector():
                init_value = "zeros({},1)".format(cur_la_type.rows)
                base_str = "    {} = optimvar('{}', {});\n".format(id_info.content, id_info.content, cur_la_type.rows)
            elif cur_la_type.is_matrix():
                init_value = "zeros({}*{},1)".format(cur_la_type.rows, cur_la_type.cols)
                base_str = "    {} = optimvar('{}', {}, {});\n".format(id_info.content, id_info.content, cur_la_type.rows, cur_la_type.cols)
                name_convention = {id_info.content: "reshape({}, [{}, {}])".format(id_info.content, cur_la_type.rows, cur_la_type.cols)}
                self.add_name_conventions(name_convention)
            base_str_list.append(base_str)
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
        prob_name = self.generate_var_name('prob')
        pre_list += base_str_list
        constraint_list.append("{} = optimproblem;".format(prob_name))
        for cond_index in range(len(node.cond_list)):
            cond_node = node.cond_list[cond_index]
            if cond_node.cond.node_type == IRNodeType.BinComp:
                if cond_node.cond.comp_type == IRNodeType.Gt or cond_node.cond.comp_type == IRNodeType.Ge:
                    constraint_list.append("{}.Constraints.cons{} = {} >= {};".format(prob_name, cond_index+1, self.visit(cond_node.cond.left, **kwargs).content,
                                                                                     self.visit(cond_node.cond.right, **kwargs).content))
                elif cond_node.cond.comp_type == IRNodeType.Lt or cond_node.cond.comp_type == IRNodeType.Le:
                    constraint_list.append("{}.Constraints.cons{} = {} <= {};".format(prob_name, cond_index+1, self.visit(cond_node.cond.left, **kwargs).content,
                                                                                     self.visit(cond_node.cond.right, **kwargs).content))
                # elif cond_node.cond.comp_type == IRNodeType.Eq:
                #     constraint_list.append("{{'type': 'eq', 'fun': lambda {}: {}-{}}}".format(id_info.content,
                #                                                                               self.visit(cond_node.cond.left, **kwargs).content,
                #                                                                               self.visit(cond_node.cond.right, **kwargs).content))
                # elif cond_node.cond.comp_type == IRNodeType.Ne:
                #     constraint_list.append("{{'type': 'ineq', 'fun': lambda {}: np.power({}-{}, 2)}}".format(id_info.content,
                #                                                                               self.visit(cond_node.cond.left, **kwargs).content,
                #                                                                               self.visit(cond_node.cond.right, **kwargs).content))
            elif cond_node.cond.node_type == IRNodeType.In:
                v_set = self.visit(cond_node.cond.set, **kwargs).content
                opt_func = self.generate_var_name(category)
                pre_list.append("    function ret = {}({})\n".format(opt_func, opt_param))
                pre_list.append("        {} = 1\n".format(opt_ret))
                pre_list.append("        for i = 1:numel({}):\n".format(v_set))
                pre_list.append("            {} *= ({}[0] - {}[i])\n".format(opt_ret, opt_param, v_set))
                pre_list.append("        ret = {}\n".format(opt_ret))
                constraint_list.append("{{'type': 'eq', 'fun': {}}}".format(opt_func))

        # constraint
        constraints_param = ""
        if len(node.cond_list) > 0:
            cons = self.generate_var_name('cons')
            # pre_list.append("    {} = ({})\n".format(cons, ','.join(constraint_list)))
            pre_list += ["    {}\n".format(cons) for cons in constraint_list]
            # constraints_param = ", constraints={}".format(cons)
        target_func = self.generate_var_name('target')
        exp = exp_info.content
        # Handle optimization type
        if node.opt_type == OptimizeType.OptimizeMax or node.opt_type == OptimizeType.OptimizeArgmax:
            exp = "-({})".format(exp)

        if len(exp_info.pre_list) > 0:
            pre_list.append("    function ret = {}({})\n".format(target_func, id_info.content))
            for pre in exp_info.pre_list:
                lines = pre.split('\n')
                for line in lines:
                    if line != "":
                        pre_list.append("    {}\n".format(line))
            pre_list.append("        ret = {};\n".format(exp))
            pre_list.append("    end\n")
            target_func = "@{}".format(target_func)
        else:
            # simple expression
            if len(node.cond_list) == 0:
                pre_list.append("    {} = @({}) {};\n".format(target_func, id_info.content, exp))
        # ret name
        opt_name = self.generate_var_name("optimize")
        if len(node.cond_list) > 0:
            # unfinished implementation
            pre_list.append("    {}.Objective = {};\n".format(prob_name, exp))
            opt_exp = "solve({})".format(prob_name)
            if node.opt_type == OptimizeType.OptimizeArgmin or node.opt_type == OptimizeType.OptimizeArgmax:
                content = "{}.{}".format(opt_name, id_info.content)
            else:
                content = opt_name
            if node.opt_type == OptimizeType.OptimizeMax:
                content = "-"+content
        else:
            # no constraints
            opt_exp = "fminunc({},{})".format(target_func, init_value)
            if node.opt_type == OptimizeType.OptimizeMax or node.opt_type == OptimizeType.OptimizeArgmax:
                opt_exp = "-"+opt_exp
            content = opt_name
        if node.opt_type == OptimizeType.OptimizeArgmin or node.opt_type == OptimizeType.OptimizeArgmax:
            pre_list.append("    [{}, ~] = {};\n".format(opt_name, opt_exp))
        else:
            pre_list.append("    [~, {}] = {};\n".format(opt_name, opt_exp))
        if cur_la_type.is_matrix():
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
        # Awkwardly 'ArrayValued',true means that the function will get called
        # with scalar input, otherwise MATLAB assumes the function is written in
        # a vectorized way and surely ours will not be without intentionally
        # guaranteeing that.
        func_content = "@({}) {}".format(base_info.content, exp_info.content);
        content = "integral({}, {}, {},'ArrayValued',true)".format(func_content, lower_info.content, upper_info.content)
        return CodeNodeInfo(content, pre_list=pre_list)

    def visit_inner_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        # It's not clear if this will get called for tensor dot product. If so
        # then this code will fail.
        if node.sub:
            sub_info = self.visit(node.sub, **kwargs)
            content = "({})' * ({}) * ({})".format(right_info.content, sub_info.content, left_info.content)
        else:
            content = "({})' * ({})".format(right_info.content, left_info.content)
        return CodeNodeInfo(content, pre_list=left_info.pre_list+right_info.pre_list)

    def visit_fro_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("sum({}(:).*{}(:))".format(left_info.content, right_info.content), pre_list=left_info.pre_list+right_info.pre_list)

    def visit_hadamard_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("{}.*{}".format(left_info.content, right_info.content), pre_list=left_info.pre_list+right_info.pre_list)

    def visit_cross_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("cross({}, {})".format(left_info.content, right_info.content), pre_list=left_info.pre_list+right_info.pre_list)

    def visit_kronecker_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("kron({}, {})".format(left_info.content, right_info.content), pre_list=left_info.pre_list+right_info.pre_list)

    def visit_dot_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("dot({},{})".format(left_info.content, right_info.content), pre_list=left_info.pre_list+right_info.pre_list)

    def visit_math_func(self, node, **kwargs):
        content = ''
        param_info = self.visit(node.param, **kwargs)
        params_content = param_info.content
        pre_list = param_info.pre_list
        if node.func_type == MathFuncType.MathFuncSin:
            content = 'sin'
        elif node.func_type == MathFuncType.MathFuncAsin:
            content = 'asin'
        elif node.func_type == MathFuncType.MathFuncCos:
            content = 'cos'
        elif node.func_type == MathFuncType.MathFuncAcos:
            content = 'acos'
        elif node.func_type == MathFuncType.MathFuncTan:
            content = 'tan'
        elif node.func_type == MathFuncType.MathFuncAtan:
            content = 'atan'
        elif node.func_type == MathFuncType.MathFuncSinh:
            content = 'sinh'
        elif node.func_type == MathFuncType.MathFuncAsinh:
            content = 'asinh'
        elif node.func_type == MathFuncType.MathFuncCosh:
            content = 'cosh'
        elif node.func_type == MathFuncType.MathFuncAcosh:
            content = 'acosh'
        elif node.func_type == MathFuncType.MathFuncTanh:
            content = 'tanh'
        elif node.func_type == MathFuncType.MathFuncAtanh:
            content = 'atanh'
        elif node.func_type == MathFuncType.MathFuncCot:
            content = '1./tan'
        elif node.func_type == MathFuncType.MathFuncSec:
            content = '1./cos'
        elif node.func_type == MathFuncType.MathFuncCsc:
            content = '1./sin'
        elif node.func_type == MathFuncType.MathFuncAtan2:
            content = 'atan2'
            remain_info = self.visit(node.remain_params[0], **kwargs)
            params_content += ', ' + remain_info.content
            pre_list += remain_info.pre_list
        elif node.func_type == MathFuncType.MathFuncExp:
            content = 'exp'
        elif node.func_type == MathFuncType.MathFuncLog:
            content = 'log'
        elif node.func_type == MathFuncType.MathFuncLog2:
            content = 'log2'
        elif node.func_type == MathFuncType.MathFuncLog10:
            content = 'log10'
        elif node.func_type == MathFuncType.MathFuncLn:
            content = 'log'
        elif node.func_type == MathFuncType.MathFuncSqrt:
            content = 'sqrt'
        elif node.func_type == MathFuncType.MathFuncTrace:
            content = 'trace'
        elif node.func_type == MathFuncType.MathFuncDiag:
            content = 'diag'
        elif node.func_type == MathFuncType.MathFuncVec:
            return CodeNodeInfo("reshape({},[],1)".format(params_content))  # column-major
        elif node.func_type == MathFuncType.MathFuncDet:
            content = 'det'
        elif node.func_type == MathFuncType.MathFuncRank:
            content = 'rank'
        elif node.func_type == MathFuncType.MathFuncNull:
            content = 'null'
        elif node.func_type == MathFuncType.MathFuncOrth:
            content = 'orth'
        elif node.func_type == MathFuncType.MathFuncInv:
            content = 'inv'
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
                f_name = 'max'
                if node.func_type == MathFuncType.MathFuncMin:
                    f_name = 'min'
                content = "{}({})".format(f_name, params_content)
            return CodeNodeInfo(content, pre_list=pre_list)
        return CodeNodeInfo("{}({})".format(content, params_content), pre_list=pre_list)

    def visit_constant(self, node, **kwargs):
        content = ''
        if node.c_type == ConstantType.ConstantPi:
            content = 'pi'
        elif node.c_type == ConstantType.ConstantE:
            content = 'exp(1)'
        elif node.c_type == ConstantType.ConstantInf:
            content = 'inf'
        return CodeNodeInfo(content)

    ###################################################################
