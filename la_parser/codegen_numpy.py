from la_parser.codegen import *
from la_parser.type_walker import *
import keyword


class CodeGenNumpy(CodeGen):
    def __init__(self):
        super().__init__(ParserTypeEnum.NUMPY)

    def init_type(self, type_walker, func_name):
        super().init_type(type_walker, func_name)
        self.pre_str = '''"""\n{}\n"""\nimport numpy as np\nimport scipy\nimport scipy.linalg\nfrom scipy import sparse\n'''.format(self.la_content)
        self.pre_str += "from scipy.integrate import quad\n"
        self.pre_str += "from scipy.optimize import minimize\n"
        self.pre_str += "\n\n"
        self.post_str = ''''''

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
                        content = "{}[{}][{}]".format(node.main_id, node.subs[0], node.subs[1])
        return CodeNodeInfo(content)

    def visit_start(self, node, **kwargs):
        return self.visit(node.stat, **kwargs)

    def visit_block(self, node, **kwargs):
        type_checks = []
        type_declare = []
        doc = []
        show_doc = False
        rand_func_name = "generateRandomData"
        test_content = []
        test_function = ["def " + rand_func_name + "():"]
        rand_int_max = 10
        main_content = ["if __name__ == '__main__':"]
        if len(self.parameters) > 0:
            main_content.append("    {} = {}()".format(', '.join(self.parameters), rand_func_name))
        else:
            main_content.append("    {}()".format(rand_func_name))
        dim_content = ""
        if self.dim_dict:
            for key, value in self.dim_dict.items():
                if key in self.parameters:
                    continue
                test_content.append("    {} = np.random.randint({})".format(key, rand_int_max))
                if self.contain_subscript(value[0]):
                    main_id = self.get_main_id(value[0])
                    dim_content += "    {} = {}.shape[{}]\n".format(key, main_id, value[1]+1)
                else:
                    dim_content += "    {} = {}.shape[{}]\n".format(key, value[0], value[1])
        for parameter in self.parameters:
            if self.symtable[parameter].desc:
                show_doc = True
                doc.append('    :param :{} :{}'.format(parameter, self.symtable[parameter].desc))
            if self.symtable[parameter].is_sequence():
                ele_type = self.symtable[parameter].element_type
                data_type = ele_type.element_type
                if ele_type.is_matrix() and ele_type.sparse:
                    type_checks.append('    assert {}.shape == ({},)'.format(parameter, self.symtable[parameter].size))
                    type_declare.append('    {} = np.asarray({})'.format(parameter, parameter))
                    test_content.append('    {} = []'.format(parameter))
                    test_content.append('    for i in range({}):'.format(self.symtable[parameter].size))
                    if isinstance(data_type, LaVarType) and data_type.is_scalar() and data_type.is_int:
                        test_content.append(
                            '        {}.append(sparse.random({}, {}, dtype=np.integer))'.format(parameter, ele_type.rows, ele_type.cols))
                    else:
                        test_content.append(
                            '        {}.append(sparse.random({}, {}, dtype=np.float64))'.format(parameter, ele_type.rows,
                                                                                            ele_type.cols))
                else:
                    size_str = ""
                    if ele_type.is_matrix():
                        type_checks.append('    assert {}.shape == ({}, {}, {})'.format(parameter, self.symtable[parameter].size, ele_type.rows, ele_type.cols))
                        size_str = '{}, {}, {}'.format(self.symtable[parameter].size, ele_type.rows, ele_type.cols)
                    elif ele_type.is_vector():
                        type_checks.append('    assert {}.shape == ({}, {}, 1)'.format(parameter, self.symtable[parameter].size, ele_type.rows))
                        size_str = '{}, {}, 1'.format(self.symtable[parameter].size, ele_type.rows)
                    elif ele_type.is_scalar():
                        type_checks.append('    assert {}.shape == ({},)'.format(parameter, self.symtable[parameter].size))
                        size_str = '{}'.format(self.symtable[parameter].size)
                    if isinstance(data_type, LaVarType):
                        if data_type.is_scalar() and data_type.is_int:
                            type_declare.append('    {} = np.asarray({}, dtype=np.int)'.format(parameter, parameter))
                            test_content.append('    {} = np.random.randint({}, size=({}))'.format(parameter, rand_int_max, size_str))
                        else:
                            type_declare.append('    {} = np.asarray({}, dtype=np.float64)'.format(parameter, parameter))
                            test_content.append('    {} = np.random.randn({})'.format(parameter, size_str))
                    else:
                        type_declare.append('    {} = np.asarray({})'.format(parameter, parameter))
                        test_content.append('    {} = np.random.randn({})'.format(parameter, size_str))
            elif self.symtable[parameter].is_matrix():
                element_type = self.symtable[parameter].element_type
                if isinstance(element_type, LaVarType):
                    if self.symtable[parameter].sparse:
                        if element_type.is_scalar() and element_type.is_int:
                            test_content.append(
                                '    {} = sparse.random({}, {}, dtype=np.integer)'.format(parameter, self.symtable[parameter].rows,
                                                                          self.symtable[parameter].cols))
                        else:
                            test_content.append(
                                '    {} = sparse.random({}, {}, dtype=np.float64)'.format(parameter, self.symtable[parameter].rows,
                                                                        self.symtable[parameter].cols))
                    else:
                        # dense
                        if element_type.is_scalar() and element_type.is_int:
                            type_declare.append('    {} = np.asarray({}, dtype=np.integer)'.format(parameter, parameter))
                            test_content.append('    {} = np.random.randint({}, size=({}, {}))'.format(parameter, rand_int_max, self.symtable[parameter].rows, self.symtable[parameter].cols))
                        else:
                            type_declare.append('    {} = np.asarray({}, dtype=np.float64)'.format(parameter, parameter))
                            test_content.append('    {} = np.random.randn({}, {})'.format(parameter, self.symtable[parameter].rows, self.symtable[parameter].cols))
                else:
                    if self.symtable[parameter].sparse:
                        test_content.append(
                            '    {} = sparse.random({}, {}, dtype=np.float64)'.format(parameter, self.symtable[parameter].rows,
                                                                      self.symtable[parameter].cols))
                    else:
                        type_checks.append('    {} = np.asarray({})'.format(parameter, parameter))
                        test_content.append('    {} = np.random.randn({}, {})'.format(parameter, self.symtable[parameter].rows, self.symtable[parameter].cols))
                type_checks.append('    assert {}.shape == ({}, {})'.format(parameter, self.symtable[parameter].rows, self.symtable[parameter].cols))
            elif self.symtable[parameter].is_vector():
                element_type = self.symtable[parameter].element_type
                if isinstance(element_type, LaVarType):
                    if element_type.is_scalar() and element_type.is_int:
                        type_declare.append('    {} = np.asarray({}, dtype=np.integer)'.format(parameter, parameter))
                        test_content.append('    {} = np.random.randint({}, size=({}))'.format(parameter, rand_int_max, self.symtable[parameter].rows))
                    else:
                        type_declare.append('    {} = np.asarray({}, dtype=np.float64)'.format(parameter, parameter))
                        test_content.append('    {} = np.random.randn({})'.format(parameter, self.symtable[parameter].rows))
                else:
                    type_declare.append('    {} = np.asarray({})'.format(parameter, parameter))
                    test_content.append('    {} = np.random.randn({})'.format(parameter, self.symtable[parameter].rows))
                type_checks.append('    assert {}.shape == ({}, 1)'.format(parameter, self.symtable[parameter].rows))
                test_content.append('    {} = {}.reshape(({}, 1))'.format(parameter, parameter, self.symtable[parameter].rows))
            elif self.symtable[parameter].is_scalar():
                type_checks.append('    assert np.ndim({}) == 0'.format(parameter))
                if self.symtable[parameter].is_int:
                    test_function.append('    {} = np.random.randint({})'.format(parameter, rand_int_max))
                else:
                    test_function.append('    {} = np.random.randn()'.format(parameter))
            elif self.symtable[parameter].is_set():
                type_checks.append('    assert isinstance({}, list) and len({}) > 0'.format(parameter, parameter))
                if self.symtable[parameter].size > 1:
                    type_checks.append('    assert len({}[0]) == {}'.format(parameter, self.symtable[parameter].size))
                test_content.append('    {} = []'.format(parameter))
                test_content.append('    {}_0 = np.random.randint(1, {})'.format(parameter, rand_int_max))
                test_content.append('    for i in range({}_0):'.format(parameter))
                gen_list = []
                for i in range(self.symtable[parameter].size):
                    if self.symtable[parameter].int_list[i]:
                        gen_list.append('np.random.randint({})'.format(rand_int_max))
                    else:
                        gen_list.append('np.random.randn()')
                test_content.append('        {}.append(('.format(parameter) + ', '.join(gen_list) + '))')
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
                test_content.append("    def {}({}):".format(parameter, ', '.join(param_list)))
                test_content += dim_definition
                test_content.append("        return {}".format(self.get_rand_test_str(self.symtable[parameter].ret, rand_int_max)))
                # test_content.append('    {} = lambda {}: {}'.format(parameter, ', '.join(param_list), self.get_rand_test_str(self.symtable[parameter].ret, rand_int_max)))

            main_content.append('    print("{}:", {})'.format(parameter, parameter))
        content = 'def ' + self.func_name + '(' + ', '.join(self.parameters) + '):\n'
        if show_doc:
            content += '    \"\"\"\n' + '\n'.join(doc) + '\n    \"\"\"\n'
        # merge content
        content += '\n'.join(type_declare) + '\n\n'
        content += dim_content
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
            stats_content += ret_str + stat_info.content + '\n'

        content += stats_content
        content += '    return ' + self.ret_symbol
        content += '\n'
        # test
        test_function += test_content
        test_function.append('    return {}'.format(', '.join(self.parameters)))
        main_content.append("    func_value = {}({})".format(self.func_name, ', '.join(self.parameters)))
        main_content.append('    print("func_value: ", func_value)')
        content += '\n\n' + '\n'.join(test_function) + '\n\n\n' + '\n'.join(main_content)
        # convert special string in identifiers
        content = self.trim_content(content)
        return content

    def visit_WhereConditions(self, node, **kwargs):
        pass

    def visit_expression(self, node, **kwargs):
        exp_info = self.visit(node.value, **kwargs)
        if node.sign:
            exp_info.content = '-' + exp_info.content
        return exp_info

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
            content.append("{} = np.zeros(({}, {}))\n".format(assign_id, self.symtable[assign_id].rows, self.symtable[assign_id].cols))
        elif self.symtable[assign_id].is_vector():
            content.append("{} = np.zeros({})\n".format(assign_id, self.symtable[assign_id].rows))
        elif self.symtable[assign_id].is_sequence():
            ele_type = self.symtable[assign_id].element_type
            content.append("{} = np.zeros(({}, {}, {}))\n".format(assign_id, self.symtable[assign_id].size, ele_type.rows, ele_type.cols))
        else:
            content.append("{} = 0\n".format(assign_id))
        content.append("for {} in range(len({})):\n".format(sub, target_var[0]))
        if exp_info.pre_list:   # catch pre_list
            list_content = "".join(exp_info.pre_list)
            # content += exp_info.pre_list
            list_content = list_content.split('\n')
            for index in range(len(list_content)):
                if index != len(list_content)-1:
                    content.append(list_content[index] + '\n')
        # only one sub for now
        if node.cond:
            content.append("    " + cond_content)
            content.append(str("        " + assign_id + " += " + exp_str + '\n'))
        else:
            content.append(str("    " + assign_id + " += " + exp_str + '\n'))
        content[0] = "    " + content[0]
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
            if node.norm_type == NormType.NormInteger:
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
            if node.norm_type == NormType.NormFrobenius:
                content = "np.linalg.norm({}, 'fro')".format(value)
            elif node.norm_type == NormType.NormNuclear:
                content = "np.linalg.norm({}, 'nuc')".format(value)
        return CodeNodeInfo(content, pre_list)

    def visit_transpose(self, node, **kwargs):
        f_info = self.visit(node.f, **kwargs)
        f_info.content = "{}.T".format(f_info.content)
        return f_info

    def visit_power(self, node, **kwargs):
        base_info = self.visit(node.base, **kwargs)
        if node.t:
            base_info.content = "{}.T".format(base_info.content)
        elif node.r:
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
                "    {} = scipy.sparse.coo_matrix(({}+{}.data.tolist(), np.hstack((np.asarray({}).T, np.asarray(({}.row, {}.col))))), shape=({}, {}))\n".format(cur_m_id, value_var, self.get_main_id(lhs),
                                                                                                    index_var, self.get_main_id(lhs), self.get_main_id(lhs),
                                                                                                    self.symtable[
                                                                                                        cur_m_id].rows,
                                                                                                    self.symtable[
                                                                                                        cur_m_id].cols))

        return CodeNodeInfo(cur_m_id, pre_list)

    def visit_sparse_ifs(self, node, **kwargs):
        assign_node = node.get_ancestor(IRNodeType.Assignment)
        sparse_node = node.get_ancestor(IRNodeType.SparseMatrix)
        subs = assign_node.left.subs
        ret = ["    for {} in range({}):\n".format(subs[0], sparse_node.la_type.rows),
               "        for {} in range({}):\n".format(subs[1], sparse_node.la_type.cols)]
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
        stat_content = stat_content.replace('_{}{}'.format(subs[0], subs[1]), '[{}][{}]'.format(subs[0], subs[1]))
        content.append('if {}:\n'.format(cond_info.content))
        content.append('    {}.append(({}, {}))\n'.format(sparse_node.la_type.index_var, subs[0], subs[1]))
        content.append('    {}.append({})\n'.format(sparse_node.la_type.value_var, stat_content))
        self.convert_matrix = False
        return CodeNodeInfo(content)

    def visit_sparse_other(self, node, **kwargs):
        content = ''
        return CodeNodeInfo('    '.join(content))

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
                                ret[i][j] = '{}({})'.format(func_name, dims[0])
                            else:
                                ret[i][j] = '{}(({}, {}))'.format(func_name, dims[0], dims[1])
                all_rows.append('[' + ', '.join(ret[i]) + ']')
            m_content += 'np.block([{}])'.format(', '.join(all_rows))
            if len(ret) > 1 and len(ret[0]) > 1:
                content += '{} = {}\n'.format(cur_m_id, m_content)
            elif len(ret) == 1:
                # single row
                content += '{} = np.hstack(({}))\n'.format(cur_m_id, ', '.join(ret[0]))
            else:
                # single col
                for i in range(len(ret)):
                    ret[i] = ''.join(ret[i])
                content += '{} = np.vstack(({}))\n'.format(cur_m_id, ', '.join(ret))
        else:
            # dense
            content += '{} = np.zeros(({}, {}))\n'.format(cur_m_id, self.symtable[cur_m_id].rows,
                                                          self.symtable[cur_m_id].cols)
            for i in range(len(ret)):
                content += "    {}[{}] = [{}]\n".format(cur_m_id, i, ', '.join(ret[i]))
        #####################
        pre_list = [content]
        if ret_info.pre_list:
            pre_list = ret_info.pre_list + pre_list
        return CodeNodeInfo(cur_m_id, pre_list)

    def visit_matrix_rows(self, node, **kwargs):
        ret = []
        pre_list = []
        if node.rs:
            rs_info = self.visit(node.rs, **kwargs)
            ret = ret + rs_info.content
            pre_list += rs_info.pre_list
        if node.r:
            r_info = self.visit(node.r, **kwargs)
            ret.append(r_info.content)
            pre_list += r_info.pre_list
        return CodeNodeInfo(ret, pre_list)

    def visit_matrix_row(self, node, **kwargs):
        ret = []
        pre_list = []
        if node.rc:
            rc_info = self.visit(node.rc, **kwargs)
            ret += rc_info.content
            pre_list += rc_info.pre_list
        if node.exp:
            exp_info = self.visit(node.exp, **kwargs)
            ret.append(exp_info.content)
            pre_list += exp_info.pre_list
        return CodeNodeInfo(ret, pre_list)

    def visit_matrix_row_commas(self, node, **kwargs):
        ret = []
        pre_list = []
        if node.value:
            value_info = self.visit(node.value, **kwargs)
            ret += value_info.content
            pre_list += value_info.pre_list
        if node.exp:
            exp_info = self.visit(node.exp, **kwargs)
            ret.append(exp_info.content)
            pre_list += exp_info.pre_list
        return CodeNodeInfo(ret, pre_list)

    def visit_exp_in_matrix(self, node, **kwargs):
        exp_info = self.visit(node.value, **kwargs)
        if node.sign:
            exp_info.content = '-' + exp_info.content
        return exp_info

    def visit_num_matrix(self, node, **kwargs):
        post_s = ''
        if node.id:
            func_name = "np.identity"
        else:
            if node.left == '0':
                func_name = "np.zeros"
            elif node.left == '1':
                func_name = "np.ones"
            else:
                func_name = "({} * np.ones".format(left_info.content)
                post_s = ')'
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
            if node.col_index is not None:
                col_info = self.visit(node.col_index, **kwargs)
                content = "{}[{}, {}]".format(main_info.content, row_info.content, col_info.content)
            else:
                content = "{}[{}, :]".format(main_info.content, row_info.content)
        else:
            col_info = self.visit(node.col_index, **kwargs)
            content = "{}[:, {}]".format(main_info.content, col_info.content)
        return CodeNodeInfo(content)

    def visit_vector_index(self, node, **kwargs):
        main_info = self.visit(node.main, **kwargs)
        index_info = self.visit(node.row_index, **kwargs)
        return CodeNodeInfo("{}[{}]".format(main_info.content, index_info.content))

    def visit_sequence_index(self, node, **kwargs):
        main_info = self.visit(node.main, **kwargs)
        main_index_info = self.visit(node.main_index, **kwargs)
        if node.slice_matrix:
            if node.row_index is not None:
                row_info = self.visit(node.row_index, **kwargs)
                content = "{}[{}][{}, :]".format(main_info.content, main_index_info.content, row_info.content)
            else:
                col_info = self.visit(node.col_index, **kwargs)
                content = "{}[{}][:, {}]".format(main_info.content, main_index_info.content, col_info.content)
        else:
            if node.row_index is not None:
                row_info = self.visit(node.row_index, **kwargs)
                if node.col_index is not None:
                    col_info = self.visit(node.col_index, **kwargs)
                    content = "{}[{}][{}, {}]".format(main_info.content, main_index_info.content, row_info.content,
                                                      col_info.content)
                else:
                    content = "{}[{}][{}]".format(main_info.content, main_index_info.content, row_info.content)
            else:
                content = "{}[{}]".format(main_info.content, main_index_info.content)
        return CodeNodeInfo(content)

    def visit_add(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = left_info.content + ' + ' + right_info.content
        left_info.pre_list += right_info.pre_list
        return left_info

    def visit_sub(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = left_info.content + ' - ' + right_info.content
        left_info.pre_list += right_info.pre_list
        return left_info

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

    def visit_sub_expr(self, node, **kwargs):
        value_info = self.visit(node.value, **kwargs)
        value_info.content = '(' + value_info.content + ')'
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
        if right_info.pre_list:
            content += "".join(right_info.pre_list)
        # y_i = stat
        if self.contain_subscript(left_id):
            left_ids = self.get_all_ids(left_id)
            left_subs = left_ids[1]
            if len(left_subs) == 2: # matrix only
                sequence = left_ids[0]  # y left_subs[0]
                sub_strs = left_subs[0] + left_subs[1]
                if self.symtable[sequence].is_matrix() and self.symtable[sequence].sparse:
                    # sparse mat assign
                    right_exp += '    ' + sequence + ' = ' + right_info.content
                    content += right_exp
                elif left_subs[0] == left_subs[1]:
                    # L_ii
                    content = ""
                    content += "    for {} in range({}):\n".format(left_subs[0], self.symtable[sequence].rows)
                    if right_info.pre_list:
                        for list in right_info.pre_list:
                            lines = list.split('\n')
                            content += "    " + "\n    ".join(lines)
                    content += "    {}[{}][{}] = {}".format(sequence, left_subs[0], left_subs[0], right_info.content)
                else:
                    for right_var in type_info.symbols:
                        if sub_strs in right_var:
                            var_ids = self.get_all_ids(right_var)
                            right_info.content = right_info.content.replace(right_var, "{}[{}][{}]".format(var_ids[0], var_ids[1][0], var_ids[1][1]))
                    right_exp += "    {}[{}][{}] = {}".format(self.get_main_id(left_id), left_subs[0], left_subs[1], right_info.content)
                    if self.symtable[sequence].is_matrix():
                        if node.op == '=':
                            # declare
                            content += "    {} = np.zeros(({}, {}))\n".format(sequence,
                                                                              self.symtable[sequence].rows,
                                                                              self.symtable[sequence].cols)
                    content += "    for {} in range({}):\n".format(left_subs[0], self.symtable[sequence].rows)
                    content += "        for {} in range({}):\n".format(left_subs[1], self.symtable[sequence].cols)
                    content += "        " + right_exp
                    # content += '\n'
            elif len(left_subs) == 1: # sequence only
                sequence = left_ids[0]  # y left_subs[0]
                # replace sequence
                for right_var in type_info.symbols:
                    if self.contain_subscript(right_var):
                        var_ids = self.get_all_ids(right_var)
                        right_info.content = right_info.content.replace(right_var, "{}[{}]".format(var_ids[0], var_ids[1][0]))

                right_exp += "    {}[{}] = {}".format(self.get_main_id(left_id), left_subs[0], right_info.content)
                ele_type = self.symtable[sequence].element_type
                if ele_type.is_matrix():
                    content += "    {} = np.zeros(({}, {}, {}))\n".format(sequence, self.symtable[sequence].size, ele_type.rows, ele_type.cols)
                elif ele_type.is_vector():
                    content += "    {} = np.zeros(({}, {}, 1))\n".format(sequence, self.symtable[sequence].size, ele_type.rows)
                else:
                    content += "    {} = np.zeros({})\n".format(sequence, self.symtable[sequence].size)
                content += "    for {} in range({}):\n".format(left_subs[0], self.symtable[sequence].size)
                content += "    " + right_exp
                # content += '\n'
        #
        else:
            op = ' = '
            if node.op == '+=':
                op = ' += '
            right_exp += '    ' + self.get_main_id(left_id) + op + right_info.content
            content += right_exp
        content += '\n'
        la_remove_key(LHS, **kwargs)
        return CodeNodeInfo(content)

    def visit_function(self, node, **kwargs):
        name_info = self.visit(node.name, **kwargs)
        pre_list = []
        params = []
        if node.params:
            for param in node.params:
                param_info = self.visit(param, **kwargs)
                params.append(param_info.content)
                pre_list += param_info.pre_list
        content = "{}({})".format(name_info.content, ', '.join(params))
        return CodeNodeInfo(content, pre_list)

    def visit_if(self, node, **kwargs):
        ret_info = self.visit(node.cond)
        # ret_info.content = "if " + ret_info.content + ":\n"
        return ret_info

    def visit_in(self, node, **kwargs):
        item_list = []
        pre_list = []
        for item in node.items:
            item_info = self.visit(item, **kwargs)
            item_list.append(item_info.content)
        right_info = self.visit(node.set, **kwargs)
        content = '(' + ', '.join(item_list) + ') in ' + right_info.content
        return CodeNodeInfo(content=content, pre_list=pre_list)

    def visit_not_in(self, node, **kwargs):
        item_list = []
        pre_list = []
        for item in node.items:
            item_info = self.visit(item, **kwargs)
            item_list.append(item_info.content)
        right_info = self.visit(node.set, **kwargs)
        content = '(' + ', '.join(item_list) + ') not in ' + right_info.content
        return CodeNodeInfo(content=content, pre_list=pre_list)

    def visit_bin_comp(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = left_info.content + ' {} '.format(self.get_bin_comp_str(node.comp_type)) + right_info.content
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
        return CodeNodeInfo("np.kron({}, {})".format(left_info.content, right_info.content), pre_list=left_info.pre_list+right_info.pre_list)

    def visit_dot_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("np.dot(({}).ravel(), ({}).ravel())".format(left_info.content, right_info.content), pre_list=left_info.pre_list+right_info.pre_list)

    def visit_math_func(self, node, **kwargs):
        content = ''
        param_info = self.visit(node.param, **kwargs)
        params_content = param_info.content
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
            params_content += ', ' + self.visit(node.remain_params[0], **kwargs).content
        elif node.func_type == MathFuncType.MathFuncExp:
            content = 'np.exp'
        elif node.func_type == MathFuncType.MathFuncLog:
            content = 'np.log10'
        elif node.func_type == MathFuncType.MathFuncLn:
            content = 'np.log'
        elif node.func_type == MathFuncType.MathFuncSqrt:
            content = 'np.sqrt'
        return CodeNodeInfo("{}({})".format(content, params_content))

    def visit_factor(self, node, **kwargs):
        if node.id:
            return self.visit(node.id, **kwargs)
        elif node.num:
            return self.visit(node.num, **kwargs)
        elif node.sub:
            return self.visit(node.sub, **kwargs)
        elif node.m:
            return self.visit(node.m, **kwargs)
        elif node.nm:
            return self.visit(node.nm, **kwargs)
        elif node.op:
            return self.visit(node.op, **kwargs)
        elif node.s:
            return self.visit(node.s, **kwargs)
        elif node.c:
            return self.visit(node.c, **kwargs)

    def visit_constant(self, node, **kwargs):
        content = ''
        if node.c_type == ConstantType.ConstantPi:
            content = 'np.pi'
        elif node.c_type == ConstantType.ConstantE:
            content = 'np.e'
        return CodeNodeInfo(content)

    def visit_double(self, node, **kwargs):
        content = str(node.value)
        return CodeNodeInfo(content)

    def visit_integer(self, node, **kwargs):
        content = str(node.value)
        return CodeNodeInfo(content)

    ###################################################################
