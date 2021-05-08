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
        if len(self.same_dim_list) > 0:
            check_list = super().get_dim_check_str()
            check_list = ['    assert( {} );'.format(stat) for stat in check_list]
        return check_list

    def get_rand_test_str(self, la_type, rand_int_max):
        rand_test = ''
        if la_type.is_matrix():
            element_type = la_type.element_type
            if isinstance(element_type, LaVarType) and element_type.is_scalar() and element_type.is_int:
                rand_test = 'randi({}, {}, {});'.format(rand_int_max, la_type.rows, la_type.cols)
            else:
                rand_test = 'randn({}, {});'.format(la_type.rows, la_type.cols)
        elif la_type.is_vector():
            element_type = la_type.element_type
            if isinstance(element_type, LaVarType) and element_type.is_scalar() and element_type.is_int:
                rand_test = 'randi({}, {});'.format(rand_int_max, la_type.rows)
            else:
                rand_test = 'randn({},1);'.format(la_type.rows)
        elif la_type.is_scalar():
            rand_test = 'randn();'
        return rand_test

    def get_set_test_list(self, parameter, la_type, rand_int_max, pre='    '):
        test_content = []
        test_content.append(test_indent+'{} = [];'.format(parameter))
        test_content.append(test_indent+'{}_0 = randi(1, {});'.format(parameter, rand_int_max))
        test_content.append(test_indent+'for i = 1:{}_0)'.format(parameter))
        gen_list = []
        for i in range(la_type.size):
            if la_type.int_list[i]:
                gen_list.append('randi({});'.format(rand_int_max))
            else:
                gen_list.append('randn();')
        test_content.append(test_indent+'    {}.append(('.format(parameter) + ', '.join(gen_list) + '))')
        test_content = ['{}{}'.format(pre, line) for line in test_content]
        return test_content

    def visit_id(self, node, **kwargs):
        content = node.get_name()
        content = self.filter_symbol(content)
        if content in self.name_convention_dict:
            content = self.name_convention_dict[content]
        if self.convert_matrix and node.contain_subscript():
            if len(node.subs) == 2:
                if self.symtable[node.main_id].is_matrix():
                    if self.symtable[node.main_id].sparse:
                        content = "{}.tocsr()[{}, {}]".format(node.main_id, node.subs[0], node.subs[1])
                    else:
                        content = "{}({}, {})".format(node.main_id, node.subs[0], node.subs[1])
        return CodeNodeInfo(content)

    def get_struct_definition(self):
        ret_type = self.get_result_type()
        assign_list = []
        for parameter in self.lhs_list:
            assign_list.append("    {}.{} = {};\n".format(ret_type, parameter, parameter))
        return "\n".join(assign_list)

    def get_ret_struct(self):
        return "{}({})".format(self.get_result_type(), ', '.join(self.lhs_list))

    def visit_block(self, node, **kwargs):
        type_checks = []
        type_declare = []
        doc = []
        show_doc = False
        rand_func_name = "generateRandomData"
        test_content = []
        test_indent = "    "
        test_function = [test_indent+"function [{}] = {}()".format(', '.join(self.parameters), rand_func_name)]
        rand_int_max = 10
        main_content = []
        dim_content = ""
        dim_defined_list = []
        if self.dim_dict:
            for key, target_dict in self.dim_dict.items():
                if key in self.parameters:
                    continue
                target = list(target_dict.keys())[0]
                has_defined = False
                if len(self.same_dim_list) > 0:
                    if key not in dim_defined_list:
                        for cur_set in self.same_dim_list:
                            if key in cur_set:
                                int_dim = self.get_int_dim(cur_set)
                                has_defined = True
                                if int_dim == -1:
                                    test_content.append(test_indent+"    {} = randi({});".format(key, rand_int_max))
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
                    test_content.append(test_indent+"    {} = randi({});".format(key, rand_int_max))
                # +1 because sizes in matlab are 1-indexed
                dim_content += "    {} = size({}, {});\n".format(key, target, target_dict[target]+1)
        for parameter in self.parameters:
            if self.symtable[parameter].desc:
                show_doc = True
                doc.append('    :param :{} :{}'.format(parameter, self.symtable[parameter].desc))
            if self.symtable[parameter].is_sequence():
                ele_type = self.symtable[parameter].element_type
                data_type = ele_type.element_type
                if ele_type.is_matrix() and ele_type.sparse:
                    type_checks.append('    assert {}.shape == ({},)'.format(parameter, self.symtable[parameter].size))
                    # Alec: I don't understand what this was doing for python,
                    # so I don't know if it would be important for matlab
                    # type_declare.append('    {} = np.asarray({})'.format(parameter, parameter))
                    test_content.append(test_indent+'    {} = [];'.format(parameter))
                    test_content.append(test_indent+'    for i = 1:{}'.format(self.symtable[parameter].size))
                    if isinstance(data_type, LaVarType) and data_type.is_scalar() and data_type.is_int:
                        test_content.append(test_indent+
                            '        {}.append(sparse.random({}, {}, dtype=np.integer, density=0.25))'.format(parameter, ele_type.rows, ele_type.cols))
                    else:
                        test_content.append(test_indent+
                            '        {}.append(sparse.random({}, {}, dtype=np.float64, density=0.25))'.format(parameter, ele_type.rows,
                                                                                            ele_type.cols))
                else:
                    size_str = ""
                    if ele_type.is_matrix():
                        type_checks.append('    assert( isequal(size({}), [{}, {}, {}]) );'.format(parameter, self.symtable[parameter].size, ele_type.rows, ele_type.cols))
                        size_str = '{}, {}, {}'.format(self.symtable[parameter].size, ele_type.rows, ele_type.cols)
                    elif ele_type.is_vector():
                        # type_checks.append('    assert {}.shape == ({}, {}, 1)'.format(parameter, self.symtable[parameter].size, ele_type.rows))
                        # size_str = '{}, {}, 1'.format(self.symtable[parameter].size, ele_type.rows)
                        type_checks.append('    assert( isequal(size({}), [{}, {}]) );'.format(parameter, self.symtable[parameter].size, ele_type.rows))
                        size_str = '{}, {}, '.format(self.symtable[parameter].size, ele_type.rows)
                    elif ele_type.is_scalar():
                        # Alec: is scalar? but then should
                        # self.symtable[parameter].size always be 1? What's
                        # meant by "scalar" here?
                        # 
                        # Force inputs to be treated as column vectors
                        type_declare.append('    {} = reshape({},[],1);'.format(parameter,parameter));
                        type_checks.append('    assert( size({},1) == {} );'.format(parameter, self.symtable[parameter].size))
                        size_str = '{}'.format(self.symtable[parameter].size)
                    if isinstance(data_type, LaVarType):
                        if data_type.is_scalar() and data_type.is_int:
                            # type_declare.append('    {} = np.asarray({}, dtype=np.int)'.format(parameter, parameter))
                            test_content.append(test_indent+'    {} = randi({}, {});'.format(parameter, rand_int_max, size_str))
                        else:
                            # type_declare.append('    {} = np.asarray({}, dtype=np.float64)'.format(parameter, parameter))
                            test_content.append(test_indent+'    {} = randn({},1);'.format(parameter, size_str))
                    else:
                        # Alec: I don't understand what this was doing for python,
                        # so I don't know if it would be important for matlab
                        #type_declare.append('    {} = np.asarray({})'.format(parameter, parameter))
                        test_content.append(test_indent+'    {} = randn({},1);'.format(parameter, size_str))
            elif self.symtable[parameter].is_matrix():
                element_type = self.symtable[parameter].element_type
                if isinstance(element_type, LaVarType):
                    if self.symtable[parameter].sparse:
                        if element_type.is_scalar() and element_type.is_int:
                            test_content.append(test_indent+
                                '    {} = sparse.random({}, {}, dtype=np.integer, density=0.25)'.format(parameter, self.symtable[parameter].rows,
                                                                          self.symtable[parameter].cols))
                        else:
                            test_content.append(test_indent+
                                '    {} = sparse.random({}, {}, dtype=np.float64, density=0.25)'.format(parameter, self.symtable[parameter].rows,
                                                                        self.symtable[parameter].cols))
                    else:
                        # dense
                        if element_type.is_scalar() and element_type.is_int:
                            # Alec: I don't understand what this was doing for python,
                            # so I don't know if it would be important for matlab
                            #type_declare.append('    {} = np.asarray({}, dtype=np.integer)'.format(parameter, parameter))
                            test_content.append(test_indent+'    {} = randi({}, {}, {});'.format(parameter, rand_int_max, self.symtable[parameter].rows, self.symtable[parameter].cols))
                        else:
                            # Alec: I don't understand what this was doing for python,
                            # so I don't know if it would be important for matlab
                            #type_declare.append('    {} = np.asarray({}, dtype=np.float64)'.format(parameter, parameter))
                            test_content.append(test_indent+'    {} = randn({}, {});'.format(parameter, self.symtable[parameter].rows, self.symtable[parameter].cols))
                else:
                    if self.symtable[parameter].sparse:
                        test_content.append(test_indent+
                            '    {} = sparse.random({}, {}, dtype=np.float64, density=0.25)'.format(parameter, self.symtable[parameter].rows,
                                                                      self.symtable[parameter].cols))
                    else:
                        type_checks.append('    {} = np.asarray({})'.format(parameter, parameter))
                        test_content.append(test_indent+'    {} = randn({}, {});'.format(parameter, self.symtable[parameter].rows, self.symtable[parameter].cols))
                type_checks.append('    assert( isequal(size({}), [{}, {}]) );'.format(parameter, self.symtable[parameter].rows, self.symtable[parameter].cols))
            elif self.symtable[parameter].is_vector():
                element_type = self.symtable[parameter].element_type
                if isinstance(element_type, LaVarType):
                    if element_type.is_scalar() and element_type.is_int:
                        #type_declare.append('    {} = np.asarray({}, dtype=np.integer)'.format(parameter, parameter))
                        test_content.append(test_indent+'    {} = randi({}, {});'.format(parameter, rand_int_max, self.symtable[parameter].rows))
                    else:
                        #type_declare.append('    {} = np.asarray({}, dtype=np.float64)'.format(parameter, parameter))
                        test_content.append(test_indent+'    {} = randn({},1);'.format(parameter, self.symtable[parameter].rows))
                else:
                    #type_declare.append('    {} = np.asarray({})'.format(parameter, parameter))
                    test_content.append(test_indent+'    {} = randn({},1)'.format(parameter, self.symtable[parameter].rows))
                type_checks.append('    assert( size({}) == {}) );'.format(parameter, self.symtable[parameter].rows))
                # type_checks.append('    assert {}.shape == ({}, 1)'.format(parameter, self.symtable[parameter].rows))
                # test_content.append(test_indent+'    {} = {}.reshape(({}, 1))'.format(parameter, parameter, self.symtable[parameter].rows))
            elif self.symtable[parameter].is_scalar():
                type_checks.append('    assert np.ndim({}) == 0'.format(parameter))
                if self.symtable[parameter].is_int:
                    test_function.append('    {} = randi({});'.format(parameter, rand_int_max))
                else:
                    test_function.append('    {} = randn();'.format(parameter))
            elif self.symtable[parameter].is_set():
                type_checks.append('    assert isinstance({}, list) and len({}) > 0'.format(parameter, parameter))
                if self.symtable[parameter].size > 1:
                    type_checks.append('    assert len({}[0]) == {}'.format(parameter, self.symtable[parameter].size))
                test_content.append(test_indent+'    {} = [];'.format(parameter))
                test_content.append(test_indent+'    {}_0 = randi(1, {});'.format(parameter, rand_int_max))
                test_content.append(test_indent+'    for i = 1:{}_0 '.format(parameter))
                gen_list = []
                for i in range(self.symtable[parameter].size):
                    if self.symtable[parameter].int_list[i]:
                        gen_list.append('randi({});'.format(rand_int_max))
                    else:
                        gen_list.append('randn();')
                test_content.append(test_indent+'        {}.append(('.format(parameter) + ', '.join(gen_list) + '))')
            elif self.symtable[parameter].is_function():
                param_list = []
                dim_definition = []
                if self.symtable[parameter].ret_template():
                    for ret_dim in self.symtable[parameter].ret_symbols:
                        param_i = self.symtable[parameter].template_symbols[ret_dim]
                        if self.symtable[parameter].params[param_i].is_vector():
                            dim_definition.append('        {} = {}{}.shape[0]'.format(ret_dim, self.param_name_test, param_i))
                        elif self.symtable[parameter].params[param_i].is_matrix():
                            if ret_dim == self.symtable[parameter].params[param_i].rows:
                                dim_definition.append('        {} = {}{}.shape[0]'.format(ret_dim, self.param_name_test, param_i))
                            else:
                                dim_definition.append('        {} = {}{}.shape[1]'.format(ret_dim, self.param_name_test, param_i))
                for index in range(len(self.symtable[parameter].params)):
                    param_list.append('{}{}'.format(self.param_name_test, index))
                test_content.append(test_indent+"    def {}({}):".format(parameter, ', '.join(param_list)))
                test_content += dim_definition
                if self.symtable[parameter].ret.is_set():
                    test_content += self.get_set_test_list('tmp', self.symtable[parameter].ret, rand_int_max, '        ')
                    test_content.append(test_indent+'        return tmp')
                else:
                    test_content.append(test_indent+"        return {}".format(self.get_rand_test_str(self.symtable[parameter].ret, rand_int_max)))
                # test_content.append(test_indent+'    {} = lambda {}: {}'.format(parameter, ', '.join(param_list), self.get_rand_test_str(self.symtable[parameter].ret, rand_int_max)))

            # main_content.append('    print("{}:", {})'.format(parameter, parameter))
        content = 'function {} = {}({})\n'.format(self.get_result_type(), self.func_name, ', '.join(self.parameters))
        content += '% {} = {}({})\n%\n'.format(self.get_result_type(), self.func_name, ', '.join(self.parameters))
        content += '%    {}'.format(  ('\n%    ').join(self.la_content.split('\n') ))
        content += "\n"
        #if show_doc:
        #    content += '    %{\n' + '\n'.join(doc) + '\n    %}\n'

        if len(self.parameters) > 0:
            content += '    if nargin==0\n'
            content += "        warning('generating random input data');\n"
            content += "        [{}] = {}();\n".format(', '.join(self.parameters), rand_func_name)
            content += '    end\n'
        #else:
        #    # Alec: I don't understand what/when this would be doing something 
        #    content += "        {}();\n".format(rand_func_name)

        # merge content
        if len(type_declare) > 0:
            content += '\n'.join(type_declare) + '\n\n'
        content += dim_content
        type_checks += self.get_dim_check_str()
        if len(type_checks) > 0:
            content += '\n'.join(type_checks) + '\n\n'
        #
        # statements
        stats_content = ""
        for index in range(len(node.stmts)):
            ret_str = ''
            if index == len(node.stmts) - 1:
                if type(node.stmts[index]).__name__ != 'AssignNode':
                    kwargs[LHS] = self.ret_symbol
                    ret_str = "    " + self.ret_symbol + ' = '
            else:
                if type(node.stmts[index]).__name__ != 'AssignNode':
                    # meaningless
                    continue
            stat_info = self.visit(node.stmts[index], **kwargs)
            if stat_info.pre_list:
                stats_content += "".join(stat_info.pre_list)
            stats_content += ret_str + stat_info.content + ';\n'

        content += stats_content
        content += self.get_struct_definition()
        # test
        test_function += test_content
        test_function.append(test_indent+'end')

        # Alec: outputting a function-file. Call with no arguments  for fake
        # data
        #main_content.append("{}({})".format(self.func_name, ', '.join(self.parameters)))

        content = '\n'.join(main_content) + '\n' + content + '\n\n' + '\n'.join(test_function)
        # convert special string in identifiers
        content += '\nend\n'
        content = self.trim_content(content)
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
        if self.symtable[assign_id].is_matrix():
            content.append("{} = zeros({}, {});\n".format(assign_id, self.symtable[assign_id].rows, self.symtable[assign_id].cols))
        elif self.symtable[assign_id].is_vector():
            content.append("{} = zeros({});\n".format(assign_id, self.symtable[assign_id].rows))
        elif self.symtable[assign_id].is_sequence():
            ele_type = self.symtable[assign_id].element_type
            content.append("{} = zeros({}, {}, {});\n".format(assign_id, self.symtable[assign_id].size, ele_type.rows, ele_type.cols))
        else:
            content.append("{} = 0;\n".format(assign_id))
        if self.symtable[target_var[0]].is_matrix() and self.symtable[target_var[0]].sparse:
            content.append("for {} = 1:size({}, 1)\n".format(sub, target_var[0]))
        else:
            content.append("for {} = 1:size({}, 1)\n".format(sub, target_var[0]))
        if exp_info.pre_list:   # catch pre_list
            list_content = "".join(exp_info.pre_list)
            # content += exp_info.pre_list
            list_content = list_content.split('\n')
            for index in range(len(list_content)):
                if index != len(list_content)-1:
                    content.append(list_content[index] + '\n')
        # only one sub for now
        indent = str("    ");
        if node.cond:
            content.append("    " + cond_content)
            indent += "  "
        content.append(str(indent + assign_id + " = " + assign_id + " + " + exp_str + ';\n'))
        content[0] = "    " + content[0]
        content.append("end\n")
        return CodeNodeInfo(assign_id, pre_list=["    ".join(content)])

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
            f_info.content = "reshape({}.T, [1, {}])".format(f_info.content, node.f.la_type.rows)
        else:
            f_info.content = "{}'".format(f_info.content)
        return f_info

    def visit_squareroot(self, node, **kwargs):
        f_info = self.visit(node.value, **kwargs)
        f_info.content = "sqrt({})".format(f_info.content)
        return f_info

    def visit_power(self, node, **kwargs):
        base_info = self.visit(node.base, **kwargs)
        if node.t:
            base_info.content = "{}'".format(base_info.content)
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
            pre_list.append("    {} = scipy.sparse.coo_matrix(({}, np.asarray({}).T), shape=({}, {}))\n".format(cur_m_id, value_var, index_var, self.symtable[cur_m_id].rows,
                                                          self.symtable[cur_m_id].cols))
        elif op_type == '+=':
            # left_ids = self.get_all_ids(lhs)
            # left_subs = left_ids[1]
            pre_list.append(
                "    {} = scipy.sparse.coo_matrix(({}+{}.data.tolist(), np.hstack((np.asarray({}).T, np.asarray(({}.row, {}.col))))), shape=({}, {}))\n".format(cur_m_id, value_var, cur_m_id,
                                                                                                    index_var, cur_m_id, cur_m_id,
                                                                                                    self.symtable[
                                                                                                        cur_m_id].rows,
                                                                                                    self.symtable[
                                                                                                        cur_m_id].cols))

        return CodeNodeInfo(cur_m_id, pre_list)

    def visit_sparse_ifs(self, node, **kwargs):
        assign_node = node.get_ancestor(IRNodeType.Assignment)
        sparse_node = node.get_ancestor(IRNodeType.SparseMatrix)
        subs = assign_node.left.subs
        ret = ["    for {} in range(1, {}+1):\n".format(subs[0], sparse_node.la_type.rows),
               "        for {} in range(1, {}+1):\n".format(subs[1], sparse_node.la_type.cols)]
        pre_list = []
        for cond in node.cond_list:
            cond_info = self.visit(cond, **kwargs)
            for index in range(len(cond_info.content)):
                cond_info.content[index] = '            ' + cond_info.content[index]
            ret += cond_info.content
            pre_list += cond_info.pre_list
        return CodeNodeInfo(ret, pre_list)

    def visit_sparse_if(self, node, **kwargs):
        self.convert_matrix = True
        assign_node = node.get_ancestor(IRNodeType.Assignment)
        sparse_node = node.get_ancestor(IRNodeType.SparseMatrix)
        subs = assign_node.left.subs
        cond_info = self.visit(node.cond, **kwargs)
        stat_info = self.visit(node.stat, **kwargs)
        content = []
        stat_content = stat_info.content
        # replace '_ij' with '(i,j)'
        stat_content = stat_content.replace('_{}{}'.format(subs[0], subs[1]), '({},{})'.format(subs[0], subs[1]))
        content.append('if {}:\n'.format(cond_info.content))
        content.append('    {}.append(({}, {}))\n'.format(sparse_node.la_type.index_var, subs[0], subs[1]))
        content.append('    {}.append({})\n'.format(sparse_node.la_type.value_var, stat_content))
        self.convert_matrix = False
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
                                ret[i][j] = ret[i][j].replace('I', 'eye({})'.format(dims[0]))
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
            if self.symtable[cur_m_id].sparse and self.symtable[cur_m_id].block:
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
                    content += '{} = {};\n'.format(cur_m_id, m_content)
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
            content += '{} = zeros({}, {});\n'.format(cur_m_id, self.symtable[cur_m_id].rows,
                                                          self.symtable[cur_m_id].cols)
            for i in range(len(ret)):
                content += "    {}({}) = [{}];\n".format(cur_m_id, i, ', '.join(ret[i]))
        #####################
        pre_list = [content]
        if ret_info.pre_list:
            pre_list = ret_info.pre_list + pre_list
        return CodeNodeInfo(cur_m_id, pre_list)

    def visit_num_matrix(self, node, **kwargs):
        post_s = ''
        if node.id:
            func_name = "eye"
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
                if self.symtable[main_info.content].sparse:
                    content = "{}.tocsr()[{}, {}]".format(main_info.content, row_content, col_content)
                else:
                    content = "{}[{}, {}]".format(main_info.content, row_content, col_content)
            else:
                content = "{}({}, :)".format(main_info.content, row_content)
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

    def visit_sequence_index(self, node, **kwargs):
        # Alec: cells in matlab are rarely used for numeric types that would
        # otherwise fit into an array. So below I'm going to use the types are
        # really matrices. I'm guessing this will cause issues eventually for
        # "ragged arrays".
        # 
        # https://github.com/pressureless/linear_algebra/issues/34
        main_info = self.visit(node.main, **kwargs)
        main_index_info = self.visit(node.main_index, **kwargs)
        if node.main_index.la_type.index_type:
            main_index_content = main_index_info.content
        else:
            main_index_content = "{}".format(main_index_info.content)
        if node.slice_matrix:
            if node.row_index is not None:
                row_info = self.visit(node.row_index, **kwargs)
                if node.row_index.la_type.index_type:
                    row_content = row_info.content
                else:
                    row_content = "{}".format(row_info.content)
                content = "{}({})({}, :)".format(main_info.content, main_index_content, row_content)
            else:
                col_info = self.visit(node.col_index, **kwargs)
                if node.col_index.la_type.index_type:
                    col_content = col_info.content
                else:
                    col_content = "{}".format(col_info.content)
                content = "{}({})(:, {})".format(main_info.content, main_index_content, col_content)
        else:
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
                    content = "{}({})({}, {})".format(main_info.content, main_index_content, row_content,
                                                      col_content)
                else:
                    content = "{}({})({})".format(main_info.content, main_index_content, row_content)
            else:
                content = "{}({})".format(main_info.content, main_index_content)
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
        content = ""
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
                if self.symtable[sequence].is_matrix() and self.symtable[sequence].sparse:
                    if left_subs[0] == left_subs[1]:  # L_ii
                        content = ""
                        if self.symtable[sequence].diagonal:
                            # add definition
                            content += "    {} = [];\n".format(self.symtable[sequence].index_var)
                            content += "    {} = [];\n".format(self.symtable[sequence].value_var)
                        content += "    for {} = 1:({}+1)\n".format(left_subs[0], self.symtable[sequence].rows)
                        if right_info.pre_list:
                            content += self.update_prelist_str(right_info.pre_list, "    ")
                        content += "        {}.append(({} - 1, {} - 1))\n".format(self.symtable[sequence].index_var, left_subs[0], left_subs[0])
                        content += "        {}.append({})\n".format(self.symtable[sequence].value_var, right_info.content)
                        content += "    {} = scipy.sparse.coo_matrix(({}, np.asarray({}).T), shape=({}, {}))\n".format(sequence,
                                                                                                            self.symtable[sequence].value_var,
                                                                                                            self.symtable[sequence].index_var,
                                                                                                            self.symtable[
                                                                                                                sequence].rows,
                                                                                                            self.symtable[
                                                                                                                sequence].cols)
                    else:  # L_ij
                        if right_info.pre_list:
                            content += "".join(right_info.pre_list)
                        # sparse mat assign
                        right_exp += '    ' + sequence + ' = ' + right_info.content
                        content += right_exp
                elif left_subs[0] == left_subs[1]:
                    # L_ii
                    content = ""
                    content += "    for {} = 1:({}+1)\n".format(left_subs[0], self.symtable[sequence].rows)
                    if right_info.pre_list:
                        content += self.update_prelist_str(right_info.pre_list, "    ")
                    content += "        {}[{}][{}] = {}".format(sequence, left_subs[0], left_subs[0], right_info.content)
                else:
                    for right_var in type_info.symbols:
                        if sub_strs in right_var:
                            var_ids = self.get_all_ids(right_var)
                            right_info.content = right_info.content.replace(right_var, "{}[{}][{}]".format(var_ids[0], var_ids[1][0], var_ids[1][1]))
                    right_exp += "    {}[{}][{}] = {}".format(self.get_main_id(left_id), left_subs[0], left_subs[1], right_info.content)
                    if self.symtable[sequence].is_matrix():
                        if node.op == '=':
                            # declare
                            content += "    {} = zeros({}, {});\n".format(sequence,
                                                                              self.symtable[sequence].rows,
                                                                              self.symtable[sequence].cols)
                    content += "    for {} = 1:{}+1\n".format(left_subs[0], self.symtable[sequence].rows)
                    content += "        for {} = 1:{}+1:\n".format(left_subs[1], self.symtable[sequence].cols)
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
                ele_type = self.symtable[sequence].element_type
                if self.symtable[sequence].is_sequence():
                    if ele_type.is_matrix():
                        content += "    {} = zeros({}, {}, {});\n".format(sequence, self.symtable[sequence].size, ele_type.rows, ele_type.cols)
                    elif ele_type.is_vector():
                        content += "    {} = zeros({}, {});\n".format(sequence, self.symtable[sequence].size, ele_type.rows)
                    else:
                        content += "    {} = zeros({});\n".format(sequence, self.symtable[sequence].size)
                    content += "    for {} = 1:{}+1\n".format(left_subs[0], self.symtable[sequence].size)
                else:
                    # vector
                    content += "    {} = zeros({});\n".format(sequence, self.symtable[sequence].rows)
                    content += "    for {} = 1:{}+1\n".format(left_subs[0], self.symtable[sequence].rows)
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
            right_exp += '    ' + self.get_main_id(left_id) + op + right_info.content
            content += right_exp
        content += ';\n'
        la_remove_key(LHS, **kwargs)
        return CodeNodeInfo(content)

    def visit_if(self, node, **kwargs):
        ret_info = self.visit(node.cond)
        # ret_info.content = "if " + ret_info.content + ":\n"
        return ret_info

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
            init_value = "zeros({})".format(node.base_type.la_type.rows)
        elif node.base_type.la_type.is_matrix():
            init_value = "zeros({}*{})".format(node.base_type.la_type.rows, node.base_type.la_type.cols)
            name_convention = {id_info.content: "reshape({}, [{}, {}])".format(id_info.content, node.base_type.la_type.rows, node.base_type.la_type.cols)}
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
                pre_list.append("        for i in range(len({})):\n".format(v_set))
                pre_list.append("            {} *= ({}[0] - {}[i])\n".format(opt_ret, opt_param, v_set))
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
        content = "integral({}, {}, {})".format("lambda {}: {}".format(base_info.content, exp_info.content), lower_info.content, upper_info.content)
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
        return CodeNodeInfo("np.kron({}, {})".format(left_info.content, right_info.content), pre_list=left_info.pre_list+right_info.pre_list)

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
