from .codegen import *
from .type_walker import *


class CodeGenGLSL(CodeGen):
    def __init__(self):
        super().__init__(ParserTypeEnum.GLSL)

    def init_type(self, type_walker, func_name):
        super().init_type(type_walker, func_name)
        self.pre_str = '''#include <Eigen/Core>\n#include <Eigen/QR>\n#include <Eigen/Dense>\n#include <Eigen/Sparse>\n#include <iostream>\n#include <set>\n'''
        self.post_str = ''''''
        self.ret = 'ret'
        if self.unofficial_method:
            self.pre_str += '#include <unsupported/Eigen/MatrixFunctions>\n'
        if self.has_opt:
            self.pre_str += '#include <LBFGS.h>\n'
        self.pre_str += '\n'
        self.code_frame.desc = '/*\n{}\n*/\n'''.format(self.la_content)
        self.code_frame.include = self.pre_str

    def get_dim_check_str(self):
        check_list = []
        if len(self.get_cur_param_data().same_dim_list) > 0:
            check_list = super().get_dim_check_str()
            check_list = ['    assert( {} );'.format(stat) for stat in check_list]
        return check_list

    def get_arith_dim_check_str(self):
        check_list = []
        if len(self.get_cur_param_data().arith_dim_list) > 0:
            check_list = ['    assert( fmod({}, 1) == 0.0 );'.format(dims) for dims in
                          self.get_cur_param_data().arith_dim_list]
        return check_list

    def get_set_item_str(self, set_type):
        type_list = []
        for index in range(set_type.size):
            if set_type.int_list[index]:
                type_list.append('int')
            else:
                type_list.append('double')
        return "std::tuple< {} >".format(", ".join(type_list)) if len(type_list) > 1 else type_list[0]

    def get_func_params_str(self, la_type, name_required=False):
        param_list = []
        for index in range(len(la_type.params)):
            name_str = ''
            if name_required:
                name_str = " {}{}".format(self.param_name_test, index)
            param_list.append(self.get_ctype(la_type.params[index]) + name_str)
        return ', '.join(param_list)

    def get_ctype(self, la_type):
        type_str = ""
        if la_type.is_sequence():
            type_str = "std::vector<{}>".format(self.get_ctype(la_type.element_type))
        elif la_type.is_matrix():
            if la_type.sparse:
                if la_type.is_dim_constant():
                    if la_type.element_type is not None and la_type.element_type.is_scalar() and la_type.element_type.is_int:
                        type_str = "Eigen::SparseMatrix<int>"
                    else:
                        type_str = "Eigen::SparseMatrix<double>"
                else:
                    if la_type.element_type is not None and la_type.element_type.is_scalar() and la_type.element_type.is_int:
                        type_str = "Eigen::SparseMatrix<int>"
                    else:
                        type_str = "Eigen::SparseMatrix<double>"
            else:
                if la_type.is_dynamic():
                    if la_type.element_type is not None and la_type.element_type.is_scalar() and la_type.element_type.is_int:
                        type_str = "Eigen::MatrixXi"
                    else:
                        type_str = "Eigen::MatrixXd"
                else:
                    if la_type.is_dim_constant():
                        if la_type.element_type is not None and la_type.element_type.is_scalar() and la_type.element_type.is_int:
                            type_str = "Eigen::Matrix<int, {}, {}>".format(la_type.rows, la_type.cols)
                        else:
                            type_str = "Eigen::Matrix<double, {}, {}>".format(la_type.rows, la_type.cols)
                    else:
                        if la_type.element_type is not None and la_type.element_type.is_scalar() and la_type.element_type.is_int:
                            type_str = "Eigen::MatrixXi"
                        else:
                            type_str = "Eigen::MatrixXd"
        elif la_type.is_vector():
            if la_type.is_dynamic():
                if la_type.element_type is not None and la_type.element_type.is_scalar() and la_type.element_type.is_int:
                    type_str = "Eigen::VectorXi"
                else:
                    type_str = "Eigen::VectorXd"
            else:
                if la_type.is_dim_constant():
                    if la_type.element_type is not None and la_type.element_type.is_scalar() and la_type.element_type.is_int:
                        type_str = "Eigen::Matrix<int, {}, 1>".format(la_type.rows)
                    else:
                        type_str = "Eigen::Matrix<double, {}, 1>".format(la_type.rows)
                else:
                    if la_type.element_type is not None and la_type.element_type.is_scalar() and la_type.element_type.is_int:
                        type_str = "Eigen::VectorXi"
                    else:
                        type_str = "Eigen::VectorXd"
        elif la_type.is_scalar():
            if la_type.is_scalar() and la_type.is_int:
                type_str = "int"
            else:
                type_str = "double"
        elif la_type.is_set():
            type_str = "std::set<{} >".format(self.get_set_item_str(la_type))
        elif la_type.is_function():
            type_str = "std::function<{}({})>".format(self.get_ctype(la_type.ret[0]), self.get_func_params_str(la_type))
        return type_str

    def get_rand_test_str(self, la_type, rand_int_max):
        rand_test = ''
        if la_type.is_matrix():
            element_type = la_type.element_type
            if isinstance(element_type, LaVarType) and element_type.is_scalar() and element_type.is_int:
                rand_test = 'Eigen::MatrixXi::Random({}, {});'.format(la_type.rows, la_type.cols)
            else:
                rand_test = 'Eigen::MatrixXd::Random({}, {});'.format(la_type.rows, la_type.cols)
        elif la_type.is_vector():
            element_type = la_type.element_type
            if isinstance(element_type, LaVarType) and element_type.is_scalar() and element_type.is_int:
                rand_test = 'Eigen::VectorXi::Random({});'.format(la_type.rows)
            else:
                rand_test = 'Eigen::VectorXd::Random({});'.format(la_type.rows)
        elif la_type.is_scalar():
            rand_test = 'rand() % {};'.format(rand_int_max)
        return rand_test

    def get_func_test_str(self, var_name, func_type, rand_int_max):
        """
        :param var_name: lhs name
        :param func_type: la_type
        :param rand_int_max: 10
        :return:
        """
        test_content = []
        name_required = False
        dim_definition = []
        if func_type.ret_template():
            name_required = True
            for ret_dim in func_type.ret_symbols:
                param_i = func_type.template_symbols[ret_dim]
                if func_type.params[param_i].is_vector():
                    dim_definition.append(
                        '        long {} = {}{}.size();'.format(ret_dim, self.param_name_test, param_i))
                elif func_type.params[param_i].is_matrix():
                    if ret_dim == func_type.params[param_i].rows:
                        dim_definition.append(
                            '        long {} = {}{}.rows();'.format(ret_dim, self.param_name_test, param_i))
                    else:
                        dim_definition.append(
                            '        long {} = {}{}.cols();'.format(ret_dim, self.param_name_test, param_i))
        test_content.append(
            '    {} = [&]({})->{}{{'.format(var_name, self.get_func_params_str(func_type, name_required),
                                            self.get_ctype(func_type.ret[0])))
        test_content += dim_definition
        if func_type.ret[0].is_set():
            test_content.append('        {} tmp;'.format(self.get_ctype(func_type.ret[0])))
            test_content += self.get_set_test_list('tmp', self.generate_var_name("dim"), 'i', func_type.ret[0],
                                                   rand_int_max, '        ')
            test_content.append('        return tmp;')
        else:
            test_content.append(
                '        return {}'.format(self.get_rand_test_str(func_type.ret[0], rand_int_max)))
        test_content.append('    };')
        return test_content

    def get_set_test_list(self, parameter, dim_name, ind_name, la_type, rand_int_max, pre='    '):
        test_content = []
        test_content.append('const int {} = rand()%10;'.format(dim_name, rand_int_max))
        test_content.append('for(int {}=0; {}<{}; {}++){{'.format(ind_name, ind_name, dim_name, ind_name))
        gen_list = []
        for i in range(la_type.size):
            if la_type.int_list[i]:
                gen_list.append('rand()%{}'.format(rand_int_max))
            else:
                gen_list.append('rand()%10')
        if len(gen_list) > 1:
            test_content.append('    {}.insert(std::make_tuple('.format(parameter) + ', '.join(gen_list) + '));')
        else:
            test_content.append('    {}.insert({});'.format(parameter, gen_list[0]))
        test_content.append('}')
        test_content = ['{}{}'.format(pre, line) for line in test_content]
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
                        content = "{}.coeff({}, {})".format(node.main_id, node.subs[0], node.subs[1])
                    else:
                        content = "{}({}, {})".format(node.main_id, node.subs[0], node.subs[1])
        return CodeNodeInfo(content)

    def get_struct_definition(self, pre_str, def_str, stat_str):
        init_content, assign_content = self.get_used_params_content()
        item_list = []
        def_list = []
        # assign_list = []
        for parameter in self.lhs_list:
            if parameter in self.symtable and self.get_sym_type(parameter) is not None:
                # not local func
                item_list.append("    {} {};".format(self.get_ctype(self.get_sym_type(parameter)), parameter))
                def_list.append("const {} & {}".format(self.get_ctype(self.get_sym_type(parameter)), parameter))
                # assign_list.append("{}({})".format(parameter, parameter))
        def_struct = ''
        declare_modules = ''
        init_struct = ''
        init_var = ''
        imported_function = ''  # import function from other modules
        if len(self.module_list) > 0:
            init_struct += '    :\n'
            init_struct_list = []
            for parameter in self.module_syms:
                if not self.symtable[parameter].is_function():
                    item_list.append("    {} {};".format(self.get_ctype(self.get_sym_type(parameter)), parameter))
            for module in self.module_list:
                def_struct += self.update_prelist_str([module.frame.struct], '    ')
                declare_modules += "    {} _{};\n".format(module.name, module.name)
                if len(module.params) > 0:
                    init_struct_list.append("    _{}({})".format(module.name, ', '.join(module.params)))
                else:
                    init_struct_list.append("    _{}()".format(module.name))
                for sym in module.syms:
                    if self.symtable[sym].is_function():
                        imported_function += self.copy_func_impl(sym, module.name)
                    else:
                        init_var += "        {} = _{}.{};\n".format(sym, module.name, sym)
            init_struct += ',\n'.join(init_struct_list) + '\n'
        content = ["struct {} {{".format(self.get_result_type()),
                   "{}".format('\n'.join(item_list)),
                   init_content,
                   self.local_func_def,
                   # "    {}({})".format(self.get_result_type(), ',\n               '.join(def_list)),
                   # "    : {}".format(',\n    '.join(assign_list)),
                   # "    {}",
                   ]
        return "\n".join(
            content) + def_struct + declare_modules + imported_function + pre_str + init_struct + '    {\n' + def_str + assign_content + init_var + stat_str + '    }\n' + "};\n"

    def copy_func_impl(self, sym, module_name):
        """implement function from other modules"""
        ret_type = self.get_ctype(self.symtable[sym].ret)
        param_list = []
        init_list = []
        for cur_index in range(len(self.symtable[sym].params)):
            param_list.append("{} p{}".format(self.get_ctype(self.symtable[sym].params[cur_index]), cur_index))
            init_list.append("p{}".format(cur_index))
        content_list = ["    {} {}({}){{\n".format(ret_type, sym, ','.join(param_list)),
                        "        return _{}.{}({});\n".format(module_name, sym, ','.join(init_list)),
                        "    };\n"]
        return ''.join(content_list)

    def get_ret_display(self):
        # print return value in main function
        if len(self.parameters) == 0:
            main_content = ["    {} func_value;".format(self.get_result_type())]
        else:
            main_content = ["    {} func_value({});".format(self.get_result_type(), ', '.join(self.parameters))]
        if self.ret_symbol is not None:
            la_type = self.get_sym_type(self.ret_symbol)
            if la_type.is_matrix() or la_type.is_vector() or la_type.is_scalar():
                main_content.append(
                    '    std::cout<<"return value:\\n"<<func_value.{}<<std::endl;'.format(self.ret_symbol))
            elif la_type.is_sequence():
                # sequence
                if la_type.element_type.is_matrix() or la_type.element_type.is_vector() or la_type.element_type.is_scalar():
                    main_content.append('    std::cout<<"vector return value:"<<std::endl;')
                    main_content.append('    for(int i=0; i<func_value.{}.size(); i++){{'.format(self.ret_symbol))
                    main_content.append(
                        '        std::cout<<"i:"<<i<<", value:\\n"<<func_value.{}.at(i)<<std::endl;'.format(
                            self.ret_symbol))
                    main_content.append('    }')
        return main_content

    def get_ret_struct(self):
        return "{}({})".format(self.get_result_type(), ', '.join(self.lhs_list + self.local_func_syms))

    def get_used_params_content(self):
        """Copy Parameters that are used in local functions as struct members"""
        init_list = []
        assign_list = []
        for param in self.used_params:
            init_list.append("    {} {};".format(self.get_ctype(self.get_sym_type(param)), param))
            assign_list.append("        this->{} = {};\n".format(param, param))
        return '\n'.join(init_list), ''.join(assign_list)

    def get_param_content(self, main_declaration, test_generated_sym_set, dim_defined_dict):
        type_checks = []
        doc = []
        test_content = []
        test_function = ['{']
        rand_int_max = 10
        #
        par_des_list = []
        test_par_list = []
        for parameter in self.parameters:
            main_declaration.append("    {} {};".format(self.get_ctype(self.get_sym_type(parameter)), parameter))
            par_des_list.append("const {} & {}".format(self.get_ctype(self.get_sym_type(parameter)), parameter))
            test_par_list.append("{} & {}".format(self.get_ctype(self.get_sym_type(parameter)), parameter))
            if self.get_sym_type(parameter).desc:
                # show_doc = True
                doc.append('@param {} {}'.format(parameter, self.get_sym_type(parameter).desc))
            if self.get_sym_type(parameter).is_sequence():
                ele_type = self.get_sym_type(parameter).element_type
                data_type = ele_type.element_type
                integer_type = False
                if parameter not in test_generated_sym_set:
                    test_content.append('    {}.resize({});'.format(parameter, self.get_sym_type(parameter).size))
                    test_content.append('    for(int i=0; i<{}; i++){{'.format(self.get_sym_type(parameter).size))
                if isinstance(data_type, LaVarType):
                    if data_type.is_scalar() and data_type.is_int:
                        integer_type = True
                if not (parameter in dim_defined_dict and dim_defined_dict[parameter] == 0):
                    type_checks.append(
                        '    assert( {}.size() == {} );'.format(parameter, self.get_sym_type(parameter).size))
                if ele_type.is_matrix():
                    if not ele_type.is_dim_constant() and not ele_type.is_dynamic():
                        type_checks.append('    for( const auto& el : {} ) {{'.format(parameter))
                        type_checks.append('        assert( el.rows() == {} );'.format(ele_type.rows))
                        type_checks.append('        assert( el.cols() == {} );'.format(ele_type.cols))
                        type_checks.append('    }')
                    if parameter not in test_generated_sym_set:
                        sparse_view = ''
                        if ele_type.sparse:
                            sparse_view = '.sparseView()'
                        matrix_type_str = 'MatrixXi' if integer_type else 'MatrixXd'
                        row_str = ele_type.rows if not ele_type.is_dynamic_row() else 'rand()%{}'.format(rand_int_max)
                        col_str = ele_type.cols if not ele_type.is_dynamic_col() else 'rand()%{}'.format(rand_int_max)
                        test_content.append(
                            '        {}[i] = Eigen::{}::Random({}, {}){};'.format(parameter, matrix_type_str, row_str,
                                                                                  col_str, sparse_view))
                elif ele_type.is_vector():
                    if parameter not in test_generated_sym_set:
                        if not ele_type.is_dim_constant() and not ele_type.is_dynamic():
                            type_checks.append('    for( const auto& el : {} ) {{'.format(parameter))
                            type_checks.append('        assert( el.size() == {} );'.format(ele_type.rows))
                            type_checks.append('    }')
                        vector_type_str = 'VectorXi' if integer_type else 'VectorXd'
                        row_str = ele_type.rows if not ele_type.is_dynamic_row() else 'rand()%{}'.format(rand_int_max)
                        test_content.append(
                            '        {}[i] = Eigen::{}::Random({});'.format(parameter, vector_type_str, row_str))
                elif ele_type.is_scalar():
                    test_content.append(
                        '        {}[i] = rand() % {};'.format(parameter, rand_int_max))
                elif ele_type.is_function():
                    func_content = self.get_func_test_str("{}[i]".format(parameter), ele_type, rand_int_max)
                    func_content = ["    {}".format(line) for line in func_content]
                    test_content += func_content
                elif ele_type.is_set():
                    set_content = self.get_set_test_list("{}[i]".format(parameter), self.generate_var_name("dim"), 'j',
                                                         ele_type, rand_int_max, '    ')
                    set_content = ["    {}".format(line) for line in set_content]
                    test_content += set_content
                if parameter not in test_generated_sym_set:
                    test_content.append('    }')
            elif self.get_sym_type(parameter).is_matrix():
                element_type = self.get_sym_type(parameter).element_type
                sparse_view = ''
                if self.get_sym_type(parameter).sparse:
                    sparse_view = '.sparseView()'
                if isinstance(element_type, LaVarType):
                    if element_type.is_scalar() and element_type.is_int:
                        test_content.append(
                            '    {} = Eigen::MatrixXi::Random({}, {}){};'.format(parameter,
                                                                                 self.get_sym_type(parameter).rows,
                                                                                 self.get_sym_type(parameter).cols,
                                                                                 sparse_view))
                    else:
                        test_content.append(
                            '    {} = Eigen::MatrixXd::Random({}, {}){};'.format(parameter,
                                                                                 self.get_sym_type(parameter).rows,
                                                                                 self.get_sym_type(parameter).cols,
                                                                                 sparse_view))
                else:
                    test_content.append(
                        '    {} = Eigen::MatrixXd::Random({}, {}){};'.format(parameter,
                                                                             self.get_sym_type(parameter).rows,
                                                                             self.get_sym_type(parameter).cols,
                                                                             sparse_view))
                if not self.get_sym_type(parameter).is_dim_constant() or self.get_sym_type(parameter).sparse:
                    if not (parameter in dim_defined_dict and dim_defined_dict[parameter] == 0):
                        type_checks.append(
                            '    assert( {}.rows() == {} );'.format(parameter, self.get_sym_type(parameter).rows))
                    if not (parameter in dim_defined_dict and dim_defined_dict[parameter] == 1):
                        type_checks.append(
                            '    assert( {}.cols() == {} );'.format(parameter, self.get_sym_type(parameter).cols))
            elif self.get_sym_type(parameter).is_vector():
                element_type = self.get_sym_type(parameter).element_type
                if isinstance(element_type, LaVarType):
                    if element_type.is_scalar() and element_type.is_int:
                        test_content.append(
                            '    {} = Eigen::VectorXi::Random({});'.format(parameter,
                                                                           self.get_sym_type(parameter).rows))
                    else:
                        test_content.append(
                            '    {} = Eigen::VectorXd::Random({});'.format(parameter,
                                                                           self.get_sym_type(parameter).rows))
                else:
                    test_content.append(
                        '    {} = Eigen::VectorXd::Random({});'.format(parameter, self.get_sym_type(parameter).rows))
                if not self.get_sym_type(parameter).is_dim_constant():
                    if not (parameter in dim_defined_dict and dim_defined_dict[parameter] == 0):
                        type_checks.append(
                            '    assert( {}.size() == {} );'.format(parameter, self.get_sym_type(parameter).rows))
            elif self.get_sym_type(parameter).is_scalar():
                test_function.append('    {} = rand() % {};'.format(parameter, rand_int_max))
            elif self.get_sym_type(parameter).is_set():
                test_content += self.get_set_test_list(parameter, self.generate_var_name("dim"), 'i',
                                                       self.get_sym_type(parameter),
                                                       rand_int_max, '    ')
            elif self.get_sym_type(parameter).is_function():
                test_content += self.get_func_test_str(parameter, self.get_sym_type(parameter), rand_int_max)
        return type_checks, doc, test_content, test_function, par_des_list, test_par_list

    def gen_dim_content(self, rand_int_max=10):
        test_content = []
        dim_content = ""
        dim_defined_dict = {}
        dim_defined_list = []
        if self.get_cur_param_data().dim_dict:
            for key, target_dict in self.get_cur_param_data().dim_dict.items():
                if key in self.get_cur_param_data().parameters:
                    continue
                if key in self.get_cur_param_data().dim_seq_set:
                    continue
                target = list(target_dict.keys())[0]
                dim_defined_dict[target] = target_dict[target]
                #
                has_defined = False
                if len(self.get_cur_param_data().same_dim_list) > 0:
                    if key not in dim_defined_list:
                        for cur_set in self.get_cur_param_data().same_dim_list:
                            if key in cur_set:
                                int_dim = self.get_int_dim(cur_set)
                                has_defined = True
                                if int_dim == -1:
                                    test_content.append("    const int {} = rand()%{};".format(key, rand_int_max))
                                else:
                                    test_content.append("    const int {} = {};".format(key, int_dim))
                                for same_key in cur_set:
                                    if same_key != key:
                                        dim_defined_list.append(same_key)
                                        if not isinstance(same_key, int):
                                            if int_dim == -1:
                                                test_content.append("    const int {} = {};".format(same_key, key))
                                            else:
                                                test_content.append("    const int {} = {};".format(same_key, int_dim))
                                break
                    else:
                        has_defined = True
                if not has_defined:
                    test_content.append("    const int {} = rand()%{};".format(key, rand_int_max))
                if self.get_cur_param_data().symtable[target].is_sequence():
                    if target_dict[target] == 0:
                        dim_content += "    const long {} = {}.size();\n".format(key, target)
                    elif target_dict[target] == 1:
                        dim_content += "    const long {} = {}[0].rows();\n".format(key, target)
                    elif target_dict[target] == 2:
                        dim_content += "    const long {} = {}[0].cols();\n".format(key, target)
                elif self.get_cur_param_data().symtable[target].is_matrix():
                    if target_dict[target] == 0:
                        dim_content += "    const long {} = {}.rows();\n".format(key, target)
                    else:
                        dim_content += "    const long {} = {}.cols();\n".format(key, target)
                elif self.get_cur_param_data().symtable[target].is_vector():
                    dim_content += "    const long {} = {}.size();\n".format(key, target)
        return dim_defined_dict, test_content, dim_content

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
                rand_def_dict[keys] = '        int {} = rand()%{};'.format(new_name, rand_int_max)
            self.logger.info("subs_list: {}".format(subs_list))
            new_seq_dim_dict = self.convert_seq_dim_dict()
            self.logger.info("new_seq_dim_dict: {}".format(new_seq_dim_dict))

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
                self.logger.info("keys_set:{}".format(keys_set))
                for cur_sym in sym_set:
                    if first:
                        first = False
                        cur_test_content.append('    for(int i=0; i<{}; i++){{'.format(self.get_sym_type(cur_sym).size))
                    dim_dict = new_seq_dim_dict[cur_sym]
                    defined_content.append('    {}.resize({});'.format(cur_sym, self.get_sym_type(cur_sym).size))
                    if self.get_sym_type(cur_sym).element_type.is_vector():
                        vector_type_str = 'VectorXi' if self.get_sym_type(
                            cur_sym).element_type.is_integer_element() else 'VectorXd'
                        # determined
                        cur_block_content.append(
                            '        {}[i] = Eigen::{}::Random({});'.format(cur_sym, vector_type_str,
                                                                            rand_name_dict[dim_dict[1]]))
                    else:
                        # matrix
                        sparse_view = ''
                        if self.get_sym_type(cur_sym).element_type.sparse:
                            sparse_view = '.sparseView()'
                        matrix_type_str = 'MatrixXi' if self.get_sym_type(
                            cur_sym).element_type.is_integer_element() else 'MatrixXd'
                        row_str = self.get_sym_type(cur_sym).element_type.rows if not self.get_sym_type(
                            cur_sym).element_type.is_dynamic_row() else rand_name_dict[dim_dict[1]]
                        col_str = self.get_sym_type(cur_sym).element_type.cols if not self.get_sym_type(
                            cur_sym).element_type.is_dynamic_col() else rand_name_dict[dim_dict[2]]
                        cur_block_content.append(
                            '        {}[i] = Eigen::{}::Random({}, {}){};'.format(cur_sym, matrix_type_str, row_str,
                                                                                  col_str,
                                                                                  sparse_view))
                cur_test_content = defined_content + cur_test_content + cur_block_content
                cur_test_content.append('    }')
                test_content += cur_test_content
        return visited_sym_set, test_content

    def visit_block(self, node, **kwargs):
        show_doc = False
        rand_func_name = "generateRandomData"
        # main
        main_declaration = []
        main_content = ["int main(int argc, char *argv[])",
                        "{",
                        "    srand((int)time(NULL));"]
        # get dimension content
        dim_defined_dict, test_content, dim_content = self.gen_dim_content()
        # Handle sequences first
        test_generated_sym_set, seq_test_list = self.gen_same_seq_test()
        test_content += seq_test_list
        # get params content
        type_checks, doc, param_test_content, test_function, par_des_list, test_par_list = \
            self.get_param_content(main_declaration, test_generated_sym_set, dim_defined_dict)
        #
        test_content += param_test_content
        content = ""
        if show_doc:
            content += '/**\n * ' + self.func_name + '\n *\n * ' + '\n * '.join(doc) + '\n * @return {}\n */\n'.format(
                self.ret_symbol)
        ret_type = self.get_result_type()
        if len(self.parameters) == 0:
            content += self.func_name + '(' + ')\n'  # func name
            test_function.insert(0, "void {}({})".format(rand_func_name, ', '.join(test_par_list)))
        elif len(self.parameters) == 1:
            content += self.func_name + '(' + ', '.join(par_des_list) + ')\n'  # func name
            test_function.insert(0, "void {}({})".format(rand_func_name, ', '.join(test_par_list)))
        else:
            content += self.func_name + '(\n    ' + ',\n    '.join(par_des_list) + ')\n'  # func name
            test_function.insert(0, "void {}({})".format(rand_func_name, ',\n    '.join(test_par_list)))
        # merge content
        pre_content = content
        content = ''
        content += dim_content
        type_checks += self.get_dim_check_str()
        type_checks += self.get_arith_dim_check_str()
        if len(type_checks) > 0:
            content += '\n'.join(type_checks) + '\n\n'
        # statements
        stats_content = ""
        for index in range(len(node.stmts)):
            ret_str = ''
            need_semicolon = False
            if index == len(node.stmts) - 1:
                if type(node.stmts[index]).__name__ != 'AssignNode':
                    if type(node.stmts[index]).__name__ == 'LocalFuncNode':
                        self.visit(node.stmts[index], **kwargs)
                        continue
                    kwargs[LHS] = self.ret_symbol
                    ret_str = "    " + self.ret_symbol + ' = '
                    need_semicolon = True
            else:
                if type(node.stmts[index]).__name__ != 'AssignNode':
                    # meaningless
                    if type(node.stmts[index]).__name__ == 'LocalFuncNode':
                        self.visit(node.stmts[index], **kwargs)
                    continue
            stat_info = self.visit(node.stmts[index], **kwargs)
            if stat_info.pre_list:
                stats_content += "".join(stat_info.pre_list)
            if need_semicolon:
                stats_content += ret_str + stat_info.content + ';\n'
            else:
                stats_content += ret_str + stat_info.content + '\n'

        # content += stats_content
        # content += '\n}\n'
        content = self.get_struct_definition(self.update_prelist_str([pre_content], '    '),
                                             self.update_prelist_str([content], '    '),
                                             self.update_prelist_str([stats_content], '    '))
        # return value
        # ret_value = self.get_ret_struct()
        # content += '    return ' + ret_value + ';'
        # test function
        test_function += test_content
        test_function.append('}')
        # main function
        main_content += main_declaration
        main_content.append("    {}({});".format(rand_func_name, ', '.join(self.parameters)))
        main_content += self.get_ret_display()
        main_content.append('    return 0;')
        main_content.append('}')
        self.code_frame.struct = self.trim_content(content)
        if not self.class_only:
            self.code_frame.main = self.trim_content('\n'.join(main_content))
            self.code_frame.rand_data = self.trim_content('\n'.join(test_function))
            content += '\n\n' + '\n'.join(test_function) + '\n\n\n' + '\n'.join(main_content)
        # convert special string in identifiers
        content = self.trim_content(content)
        return content

    def visit_summation(self, node, **kwargs):
        target_var = []
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
                        name_convention[var] = "{}.at({})".format(var_ids[0], var_ids[1][0])
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
        #
        assign_id = node.symbol
        cond_content = ""
        if node.cond:
            cond_info = self.visit(node.cond, **kwargs)
            cond_content = "if(" + cond_info.content + "){\n"
        kwargs[WALK_TYPE] = WalkTypeEnum.RETRIEVE_EXPRESSION
        content = []
        exp_info = self.visit(node.exp)
        exp_str = exp_info.content
        assign_id_type = self.get_sym_type(assign_id)
        if assign_id_type.is_matrix():
            if assign_id_type.sparse:
                content.append("{} {}({}, {});\n".format(self.get_ctype(assign_id_type), assign_id, assign_id_type.rows,
                                                         assign_id_type.cols))
            else:
                content.append(
                    "Eigen::MatrixXd {} = Eigen::MatrixXd::Zero({}, {});\n".format(assign_id, assign_id_type.rows,
                                                                                   assign_id_type.cols))
        elif assign_id_type.is_vector():
            content.append(
                "Eigen::MatrixXd {} = Eigen::MatrixXd::Zero({}, 1);\n".format(assign_id, assign_id_type.rows))
        elif assign_id_type.is_sequence():
            ele_type = assign_id_type.element_type
            content.append(
                "Eigen::MatrixXd {} = np.zeros(({}, {}, {}))\n".format(assign_id, assign_id_type.size,
                                                                       ele_type.rows, ele_type.cols))
        else:
            content.append("double {} = 0;\n".format(assign_id))
        if node.enum_list:
            range_info = self.visit(node.range, **kwargs)
            content.append('for({} tuple : {}){{\n'.format(self.get_set_item_str(node.range.la_type), range_info.content))
            extra_content = ''
            for i in range(len(node.enum_list)):
                if node.range.la_type.index_type:
                    content.append('    int {} = std::get<{}>(tuple){} + 1;\n'.format(node.enum_list[i], i, extra_content))
                else:
                    content.append('    int {} = std::get<{}>(tuple){};\n'.format(node.enum_list[i], i, extra_content))
            exp_pre_list = []
            if exp_info.pre_list:  # catch pre_list
                list_content = "".join(exp_info.pre_list)
                # content += exp_info.pre_list
                list_content = list_content.split('\n')
                for index in range(len(list_content)):
                    if index != len(list_content) - 1:
                        exp_pre_list.append(list_content[index] + '\n')
            content += exp_pre_list
            content.append(str("    " + assign_id + " += " + exp_str + ';\n'))
            content[0] = "    " + content[0]
            content.append("}\n")
            self.del_name_conventions(name_convention)
            return CodeNodeInfo(assign_id, pre_list=["    ".join(content)])
        sym_info = node.sym_dict[target_var[0]]
        if self.get_sym_type(target_var[0]).is_matrix():  # todo
            if sub == sym_info[0]:
                content.append("for(int {}=1; {}<={}.rows(); {}++){{\n".format(sub, sub, target_var[0], sub))
            else:
                content.append("for(int {}=1; {}<={}.cols(); {}++){{\n".format(sub, sub, target_var[0], sub))
        elif self.get_sym_type(target_var[0]).is_sequence():
            sym_list = node.sym_dict[target_var[0]]
            sub_index = sym_list.index(sub)
            if sub_index == 0:
                size_str = "{}.size()".format(self.convert_bound_symbol(target_var[0]))
            elif sub_index == 1:
                if self.get_sym_type(target_var[0]).element_type.is_dynamic_row():
                    size_str = "{}.at({}-1).rows()".format(self.convert_bound_symbol(target_var[0]), sym_list[0])
                else:
                    size_str = "{}".format(self.get_sym_type(target_var[0]).element_type.rows)
            else:
                if self.get_sym_type(target_var[0]).element_type.is_dynamic_col():
                    size_str = "{}.at({}-1).cols()".format(self.convert_bound_symbol(target_var[0]), sym_list[0])
                else:
                    size_str = "{}".format(self.get_sym_type(target_var[0]).element_type.cols)
            content.append("for(int {}=1; {}<={}; {}++){{\n".format(sub, sub, size_str, sub))
        else:
            content.append(
                "for(int {}=1; {}<={}.size(); {}++){{\n".format(sub, sub, self.convert_bound_symbol(target_var[0]),
                                                                sub))
        exp_pre_list = []
        if exp_info.pre_list:  # catch pre_list
            list_content = "".join(exp_info.pre_list)
            # content += exp_info.pre_list
            list_content = list_content.split('\n')
            for index in range(len(list_content)):
                if index != len(list_content) - 1:
                    exp_pre_list.append(list_content[index] + '\n')
        # only one sub for now
        if node.cond:
            content += ["    " + pre for pre in cond_info.pre_list]
            content.append("    " + cond_content)
            content += ["    " + pre for pre in exp_pre_list]
            content.append(str("        " + assign_id + " += " + exp_str + ';\n'))
            content.append("    }\n")
        else:
            content += exp_pre_list
            content.append(str("    " + assign_id + " += " + exp_str + ';\n'))
        content[0] = "    " + content[0]

        content.append("}\n")
        self.del_name_conventions(name_convention)
        return CodeNodeInfo(assign_id, pre_list=["    ".join(content)])

    def visit_local_func(self, node, **kwargs):
        self.local_func_parsing = True
        name_info = self.visit(node.name, **kwargs)
        self.local_func_name = name_info.content  # function name when visiting expressions
        param_list = []
        for parameter in node.params:
            param_info = self.visit(parameter, **kwargs)
            param_list.append(
                "        const {} & {}".format(self.get_ctype(self.get_cur_param_data().symtable[param_info.content]),
                                               param_info.content))
        if len(param_list) == 0:
            content = "    {} {}()\n"
        else:
            content = "    {} {}(\n".format(self.get_ctype(node.expr[0].la_type), name_info.content)
            content += ",\n".join(param_list) + ')\n'
        content += '    {\n'
        # get dimension content
        dim_defined_dict, test_content, dim_content = self.gen_dim_content(name_info.content)
        if dim_content != '':
            content += self.update_prelist_str([dim_content], '    ')
        #
        main_declaration = []
        # Handle sequences first
        test_generated_sym_set, seq_test_list = self.gen_same_seq_test()
        # get params content
        type_checks, doc, test_content, test_function, par_des_list, test_par_list = \
            self.get_param_content(main_declaration, test_generated_sym_set, dim_defined_dict)
        #
        type_checks += self.get_dim_check_str()
        type_checks += self.get_arith_dim_check_str()
        if len(type_checks) > 0:
            type_checks = self.update_prelist_str(type_checks, '    ')
            content += type_checks + '\n'
        expr_info = self.visit(node.expr[0], **kwargs)
        if node.expr[0].is_node(IRNodeType.MultiConds):
            content += '        {} {}_ret;\n'.format(self.get_ctype(node.expr[0].la_type), name_info.content)
            if len(expr_info.pre_list) > 0:
                content += self.update_prelist_str(expr_info.pre_list, "    ")
            content += '        return {}_ret;'.format(name_info.content)
        else:
            if len(expr_info.pre_list) > 0:
                content += self.update_prelist_str(expr_info.pre_list, "    ")
            content += '        return ' + expr_info.content + ';'
        content += '    \n    }\n'
        self.local_func_def += content
        self.local_func_parsing = False
        return CodeNodeInfo()

    def visit_norm(self, node, **kwargs):
        value_info = self.visit(node.value, **kwargs)
        value = value_info.content
        type_info = node.value
        content = ''
        pre_list = value_info.pre_list
        if type_info.la_type.is_scalar():
            content = "abs({})".format(value)
        elif type_info.la_type.is_vector():
            if node.norm_type == NormType.NormDet:
                content = "({}).determinant()".format(value)
            elif node.norm_type == NormType.NormInteger:
                if node.sub == 0:
                    content = "({}).array().count()".format(value)
                else:
                    if node.sub is None:
                        content = "({}).lpNorm<{}>()".format(value, 2)
                    else:
                        content = "({}).lpNorm<{}>()".format(value, node.sub)
            elif node.norm_type == NormType.NormMax:
                content = "({}).lpNorm<Eigen::Infinity>()".format(value)
            elif node.norm_type == NormType.NormIdentifier:
                sub_info = self.visit(node.sub, **kwargs)
                pre_list += sub_info.pre_list
                if node.sub.la_type.is_scalar():
                    content = "pow(({}).cwiseAbs().array().pow({}).sum(), 1.0/{});".format(value, sub_info.content,
                                                                                           sub_info.content)
                else:
                    content = "sqrt(({}).transpose()*{}*({}))".format(value, sub_info.content, value)
        elif type_info.la_type.is_matrix():
            if node.norm_type == NormType.NormDet:
                content = "({}).determinant()".format(value)
            elif node.norm_type == NormType.NormFrobenius:
                content = "({}).norm()".format(value)
            elif node.norm_type == NormType.NormNuclear:
                svd_name = self.generate_var_name("svd")
                content = "{}.singularValues().sum()".format(svd_name)
                pre_list.append(
                    "    Eigen::JacobiSVD<Eigen::MatrixXd> {}(T, Eigen::ComputeThinU | Eigen::ComputeThinV);\n".format(
                        svd_name))
        return CodeNodeInfo(content, pre_list=pre_list)

    def visit_transpose(self, node, **kwargs):
        f_info = self.visit(node.f, **kwargs)
        f_info.content = "{}.transpose()".format(f_info.content)
        return f_info

    def visit_pseudoinverse(self, node, **kwargs):
        f_info = self.visit(node.f, **kwargs)
        f_info.content = "{}.completeOrthogonalDecomposition().pseudoInverse()".format(f_info.content)
        return f_info
        
    def visit_squareroot(self, node, **kwargs):
        f_info = self.visit(node.value, **kwargs)
        f_info.content = "sqrt({})".format(f_info.content)
        return f_info

    def visit_power(self, node, **kwargs):
        pre_list = []
        base_info = self.visit(node.base, **kwargs)
        if node.t:
            base_info.content = "{}.transpose()".format(base_info.content)
        elif node.r:
            if node.la_type.is_scalar():
                base_info.content = "1 / ({})".format(base_info.content)
            else:
                if node.base.la_type.is_matrix() and node.base.la_type.sparse:
                    solver_name = self.generate_var_name("solver")
                    identity_name = self.generate_var_name("I")
                    pre_list.append("    Eigen::SparseQR <{}, Eigen::COLAMDOrdering<int> > {};\n".format(
                        self.get_ctype(node.base.la_type), solver_name))
                    pre_list.append("    {}.compute({});\n".format(solver_name, base_info.content))
                    pre_list.append("    {} {}({}, {});\n".format(self.get_ctype(node.base.la_type), identity_name,
                                                                  node.base.la_type.rows, node.base.la_type.cols))
                    pre_list.append("    {}.setIdentity();\n".format(identity_name))
                    base_info.content = "{}.solve({})".format(solver_name, identity_name)
                else:
                    base_info.content = "{}.inverse()".format(base_info.content)
        else:
            power_info = self.visit(node.power, **kwargs)
            if node.base.la_type.is_scalar():
                base_info.content = "pow({}, {})".format(base_info.content, power_info.content)
            else:
                name = self.generate_var_name('pow')
                base_info.pre_list.append(
                    "    Eigen::MatrixPower<{}> {}({});\n".format(self.get_ctype(node.la_type), name,
                                                                  base_info.content))
                base_info.content = "{}({})".format(name, power_info.content)
        base_info.pre_list += pre_list
        return base_info

    def visit_solver(self, node, **kwargs):
        pre_list = []
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.pre_list += right_info.pre_list
        if node.left.la_type.is_matrix() and node.left.la_type.sparse:
            solver_name = self.generate_var_name("solver")
            pre_list.append(
                "    Eigen::SparseQR <{}, Eigen::COLAMDOrdering<int> > {};\n".format(self.get_ctype(node.left.la_type),
                                                                                     solver_name))
            pre_list.append("    {}.compute({});\n".format(solver_name, left_info.content))
            left_info.content = "{}.solve({})".format(solver_name, right_info.content)
        else:
            if node.right.la_type.is_matrix() and node.right.la_type.sparse:
                left_info.content = "{}.colPivHouseholderQr().solve(({}).toDense())".format(left_info.content,
                                                                                            right_info.content)
            else:
                left_info.content = "{}.colPivHouseholderQr().solve({})".format(left_info.content, right_info.content)
        left_info.pre_list += pre_list
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
            pre_list.append('    else{\n')
            pre_list.append('        {}_ret = {};\n'.format(name, other_info.content))
            pre_list.append('    }\n')
        return CodeNodeInfo(cur_m_id, pre_list)

    def visit_sparse_matrix(self, node, **kwargs):
        assign_node = node.get_ancestor(IRNodeType.Assignment)
        type_info = node
        cur_m_id = type_info.symbol
        pre_list = []
        if_info = self.visit(node.ifs, **kwargs)
        pre_list += if_info.content
        pre_list.append(
            '    {}.setFromTriplets(tripletList_{}.begin(), tripletList_{}.end());\n'.format(
                assign_node.left[0].get_main_id(),
                assign_node.left[0].get_main_id(),
                assign_node.left[0].get_main_id()))
        return CodeNodeInfo(cur_m_id, pre_list)

    def visit_sparse_ifs(self, node, **kwargs):
        assign_node = node.get_ancestor(IRNodeType.Assignment)
        if assign_node is None:
            right_node = node.get_ancestor(IRNodeType.LocalFunc).expr[0]
        else:
            right_node = assign_node.right[0]
        if right_node.is_node(IRNodeType.SparseMatrix):
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
                assign_node = node.get_ancestor(IRNodeType.Assignment)
                sparse_node = node.get_ancestor(IRNodeType.SparseMatrix)
                subs = assign_node.left[0].subs
                ret = [
                    "    for( int {}=1; {}<={}; {}++){{\n".format(subs[0], subs[0], sparse_node.la_type.rows, subs[0]),
                    "        for( int {}=1; {}<={}; {}++){{\n".format(subs[1], subs[1], sparse_node.la_type.cols,
                                                                      subs[1])]
                for cond in node.cond_list:
                    cond_info = self.visit(cond, **kwargs)
                    for index in range(len(cond_info.content)):
                        cond_info.content[index] = '            ' + cond_info.content[index]
                    ret += cond_info.content
                    pre_list += cond_info.pre_list
                ret.append("        }\n")
                ret.append("    }\n")
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
            assign_node = node.get_ancestor(IRNodeType.Assignment)
            subs = assign_node.left[0].subs
            cond_info = self.visit(node.cond, **kwargs)
            stat_info = self.visit(node.stat, **kwargs)
            content = cond_info.pre_list
            stat_content = stat_info.content
            # replace '_ij' with '(i,j)'
            stat_content = stat_content.replace('_{}{}'.format(subs[0], subs[1]), '({}, {})'.format(subs[0], subs[1]))
            if node.loop:
                content += stat_info.pre_list
                content.append(cond_info.content)
                content.append('    tripletList_{}.push_back(Eigen::Triplet<double>({}-1, {}-1, {}));\n'.format(
                    assign_node.left[0].main.main_id, subs[0], subs[1], stat_content))
                content.append('}\n')
            else:
                content.append('{}({}){{\n'.format("if" if node.first_in_list else "else if", cond_info.content))
                content += stat_info.pre_list
                content.append('    tripletList_{}.push_back(Eigen::Triplet<double>({}-1, {}-1, {}));\n'.format(
                    assign_node.left[0].main.main_id, subs[0], subs[1], stat_content))
                content.append('}\n')
            self.convert_matrix = False
        else:
            cond_info = self.visit(node.cond, **kwargs)
            stat_info = self.visit(node.stat, **kwargs)
            content = cond_info.pre_list
            stat_content = stat_info.content
            content.append('{}({}){{\n'.format("if" if node.first_in_list else "else if", cond_info.content))
            content += stat_info.pre_list
            if assign_node is None:
                content.append("    {}_ret = {};\n".format(self.visit(left_node, **kwargs).content, stat_content))
            else:
                content.append("    {} = {};\n".format(self.visit(assign_node.left[0], **kwargs).content, stat_content))
            content.append('}\n')
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
        if self.get_sym_type(cur_m_id).is_dim_constant():
            content = '    Eigen::Matrix<double, {}, 1> {};\n'.format(self.get_sym_type(cur_m_id).rows, cur_m_id)
        else:
            content = '    Eigen::VectorXd {}({});\n'.format(cur_m_id, self.get_sym_type(cur_m_id).rows)
        content += '    {} << {};\n'.format(cur_m_id, ", ".join(ret))
        pre_list.append(content)
        return CodeNodeInfo(cur_m_id, pre_list=pre_list)

    def visit_matrix(self, node, **kwargs):
        content = "    "
        # lhs = kwargs[LHS]
        type_info = node
        cur_m_id = type_info.symbol
        kwargs["cur_id"] = cur_m_id
        ret_info = self.visit(node.value, **kwargs)
        ret = ret_info.content
        # preprocess
        if type_info.la_type.list_dim:
            for i in range(len(ret)):
                for j in range(len(ret[i])):
                    if (i, j) in type_info.la_type.list_dim:
                        dims = type_info.la_type.list_dim[(i, j)]
                        if dims[0] == 1 and dims[1] == 1:
                            # scalar value
                            continue
                        if ret[i][j] == '0':
                            func_name = 'Eigen::MatrixXd::Zero'
                        elif ret[i][j] == '1':
                            func_name = 'Eigen::MatrixXd::Ones'
                        elif 'I' in ret[i][j] and 'I' not in self.symtable:
                            # todo: assert in type checker
                            assert dims[0] == dims[1], "I must be square matrix"
                            ret[i][j] = ret[i][j].replace('I',
                                                          'Eigen::MatrixXd::Identity({}, {})'.format(dims[0], dims[0]))
                            continue
                        else:
                            func_name = ret[i][j] + ' * Eigen::MatrixXd::Ones'
                        if dims[1] == 1:
                            # vector
                            ret[i][j] = '{}({}, 1)'.format(func_name, dims[0])
                        else:
                            ret[i][j] = '{}({}, {})'.format(func_name, dims[0], dims[1])
        # matrix
        if self.get_sym_type(cur_m_id).sparse and self.get_sym_type(cur_m_id).block:
            row_index = 0  # start position for item
            # convert to sparse matrix
            sparse_id = "{}".format(cur_m_id)
            sparse_triplet = "tripletList{}".format(cur_m_id)
            tmp_sparse_name = self.generate_var_name("tmp")
            content += 'Eigen::SparseMatrix<double> {}({}, {});\n'.format(cur_m_id, self.get_sym_type(cur_m_id).rows,
                                                                          self.get_sym_type(cur_m_id).cols)
            content += '    std::vector<Eigen::Triplet<double> > {};\n'.format(sparse_triplet)
            first_item = True
            for i in range(len(ret)):
                col_index = 0
                cur_row_size = 1
                for j in range(len(ret[i])):
                    cur_scalar = False  # 1x1
                    # get size for current item
                    cur_col_size = 1
                    if type_info.la_type.list_dim and (i, j) in type_info.la_type.list_dim:
                        cur_col_size = type_info.la_type.list_dim[(i, j)][1]
                        cur_row_size = type_info.la_type.list_dim[(i, j)][0]
                    else:
                        if type_info.la_type.item_types[i][j].la_type.is_matrix() or type_info.la_type.item_types[i][
                            j].la_type.is_vector():
                            cur_col_size = type_info.la_type.item_types[i][j].la_type.cols
                            cur_row_size = type_info.la_type.item_types[i][j].la_type.rows
                    if 'Eigen::MatrixXd::Zero' in ret[i][j]:
                        # no need to handle zero
                        col_index += cur_col_size
                        continue
                    # get content for current item
                    if type_info.la_type.item_types[i][j].la_type.is_matrix() and type_info.la_type.item_types[i][
                        j].la_type.sparse:
                        item_content = ret[i][j]
                    else:
                        if type_info.la_type.item_types[i][j].la_type.is_matrix() or type_info.la_type.item_types[i][
                            j].la_type.is_vector() \
                                or (type_info.la_type.list_dim and (i, j) in type_info.la_type.list_dim):
                            if (type_info.la_type.list_dim and (i, j) in type_info.la_type.list_dim) and \
                                    type_info.la_type.list_dim[(i, j)][0] == 1 and type_info.la_type.list_dim[(i, j)][
                                1] == 1:
                                # scalar
                                item_content = ret[i][j]
                                cur_scalar = True
                            else:
                                item_content = '{}.sparseView()'.format(ret[i][j])
                        else:
                            # scalar
                            item_content = ret[i][j]
                            cur_scalar = True
                    # set matrix value
                    if first_item:
                        first_item = False
                        # declaration
                        content += '    Eigen::SparseMatrix<double> {} = {};\n'.format(tmp_sparse_name, item_content)
                        if cur_scalar:
                            content += '    {}.push_back(Eigen::Triplet<double>({}, {}, {}));\n'.format(
                                sparse_triplet, row_index, col_index, item_content)
                            col_index += cur_col_size
                            continue
                    else:
                        if cur_scalar:
                            content += '    {}.push_back(Eigen::Triplet<double>({}, {}, {}));\n'.format(
                                sparse_triplet, row_index, col_index, item_content)
                            col_index += cur_col_size
                            continue
                        content += '    {} = {};\n'.format(tmp_sparse_name, item_content)
                    content += '    for (int k=0; k < {}.outerSize(); ++k){{\n'.format(tmp_sparse_name)
                    content += '        for (Eigen::SparseMatrix<double>::InnerIterator it({}, k); it; ++it){{\n'.format(
                        tmp_sparse_name)
                    row_str = ''
                    col_str = ''
                    if not first_item:
                        row_str = "+{}".format(row_index)
                        col_str = "+{}".format(col_index)
                    content += '            {}.push_back(Eigen::Triplet<double>((int)it.row(){}, (int)it.col(){}, it.value()));\n'.format(
                        sparse_triplet, row_str, col_str)
                    content += '        }\n'
                    content += '    }\n'
                    # update col index
                    col_index += cur_col_size
                # update row index
                row_index += cur_row_size
            # set triplets
            content += '    {}.setFromTriplets({}.begin(), {}.end());\n'.format(sparse_id, sparse_triplet,
                                                                                sparse_triplet)
            cur_m_id = sparse_id
        else:
            # dense
            if self.get_sym_type(cur_m_id).is_dim_constant():
                content += 'Eigen::Matrix<double, {}, {}> {};\n'.format(self.get_sym_type(cur_m_id).rows,
                                                                        self.get_sym_type(cur_m_id).cols, cur_m_id)
            else:
                content += 'Eigen::MatrixXd {}({}, {});\n'.format(cur_m_id, self.get_sym_type(cur_m_id).rows,
                                                                  self.get_sym_type(cur_m_id).cols)
            if type_info.la_type:
                all_rows = []
                m_content = ""
                for i in range(len(ret)):
                    all_rows.append(', '.join(ret[i]))
                m_content += '{};'.format(',\n    '.join(all_rows))
                content += '    {} << {}\n'.format(cur_m_id, m_content)
            else:
                # dense
                m_list = []
                for i in range(len(ret)):
                    m_list.append(', '.join(ret[i]))
                content += '    {} << {};\n'.format(cur_m_id, ",\n    ".join(m_list))
        #####################
        pre_list = [content]
        if ret_info.pre_list:
            pre_list = ret_info.pre_list + pre_list
        return CodeNodeInfo(cur_m_id, pre_list)

    def visit_num_matrix(self, node, **kwargs):
        post_s = ''
        if node.id:
            func_name = "Eigen::MatrixXd::Identity"
        else:
            if node.left == '0':
                func_name = "Eigen::MatrixXd::Zero"
            elif node.left == '1' or node.left == '𝟙':
                func_name = "Eigen::MatrixXd::Ones"
            # else:
            #     func_name = "({} * Eigen::MatrixXd::Ones".format(left_info.content)
            #     post_s = ')'
        id1_info = self.visit(node.id1, **kwargs)
        if node.id2:
            id2_info = self.visit(node.id2, **kwargs)
            content = "{}({}, {})".format(func_name, id1_info.content, id2_info.content)
        else:
            content = "{}({}, {})".format(func_name, id1_info.content, id1_info.content)
        node_info = CodeNodeInfo(content + post_s)
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
                if self.get_sym_type(main_info.content).sparse:
                    content = "{}.coeff({}, {})".format(main_info.content, row_content, col_content)
                else:
                    content = "{}({}, {})".format(main_info.content, row_content, col_content)
            else:
                content = "{}.row({}).transpose()".format(main_info.content, row_content)
        else:
            col_info = self.visit(node.col_index, **kwargs)
            if node.col_index.la_type.index_type:
                content = "{}.col({})".format(main_info.content, col_info.content)
            else:
                content = "{}.col({}-1)".format(main_info.content, col_info.content)
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
                content = "{}.at({}).row({})".format(main_info.content, main_index_content, row_content)
            else:
                col_info = self.visit(node.col_index, **kwargs)
                if node.col_index.la_type.index_type:
                    col_content = col_info.content
                else:
                    col_content = "{}-1".format(col_info.content)
                content = "{}.at({}).col({})".format(main_info.content, main_index_content, col_content)
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
                    content = "{}.at({})({}, {})".format(main_info.content, main_index_content, row_content,
                                                         col_content)
                else:
                    # use [] instead of (): vector-like data structure
                    content = "{}.at({})[{}]".format(main_info.content, main_index_content, row_content)
            else:
                content = "{}.at({})".format(main_info.content, main_index_content)
        return CodeNodeInfo(content)

    def visit_seq_dim_index(self, node, **kwargs):
        main_index_info = self.visit(node.main_index, **kwargs)
        if node.main_index.la_type.index_type:
            main_index_content = main_index_info.content
        else:
            main_index_content = "{}-1".format(main_index_info.content)
        if node.is_row_index():
            content = "{}.at({}).rows()".format(node.real_symbol, main_index_content)
        else:
            content = "{}.at({}).cols()".format(node.real_symbol, main_index_content)
        return CodeNodeInfo(content)

    def visit_mul(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = left_info.content + ' * ' + right_info.content
        left_info.pre_list += right_info.pre_list
        return left_info

    def visit_div(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = "{} / double({})".format(left_info.content, right_info.content)
        left_info.pre_list += right_info.pre_list
        return left_info

    def visit_cast(self, node, **kwargs):
        value_info = self.visit(node.value, **kwargs)
        if node.la_type.is_scalar():
            if node.la_type.is_integer_element():
                value_info.content = "(int)({})".format(value_info.content)
            else:
                value_info.content = "(double)({})".format(value_info.content)
        return value_info

    def visit_assignment(self, node, **kwargs):
        type_info = node
        # visit matrix first
        placeholder = "{}_{}\n".format(self.comment_placeholder, node.parse_info.line)
        self.comment_dict[placeholder] = self.update_prelist_str([node.raw_text], '    // ')
        content = placeholder
        if node.optimize_param:
            pass
        else:
            for cur_index in range(len(node.left)):
                left_info = self.visit(node.left[cur_index], **kwargs)
                left_id = left_info.content
                kwargs[LHS] = left_id
                kwargs[ASSIGN_TYPE] = node.op
                # self left-hand-side symbol
                right_info = self.visit(node.right[cur_index], **kwargs)
                right_exp = ""
                # y_i = stat
                if node.left[cur_index].contain_subscript():
                    left_ids = node.left[cur_index].get_all_ids()
                    left_subs = left_ids[1]
                    if len(left_subs) == 2:  # matrix only
                        sequence = left_ids[0]  # y left_subs[0]
                        sub_strs = left_subs[0] + left_subs[1]
                        if self.get_sym_type(sequence).is_matrix() and self.get_sym_type(sequence).sparse:
                            if left_subs[0] == left_subs[1]:  # L_ii
                                if self.get_sym_type(sequence).diagonal:
                                    # add definition
                                    if sequence not in self.declared_symbols:
                                        content += "    {}.resize({}, {});\n".format(sequence,
                                                                                     self.get_sym_type(sequence).rows,
                                                                                     self.get_sym_type(sequence).cols)
                                        content += '    std::vector<Eigen::Triplet<double> > tripletList_{};\n'.format(sequence)
                                    else:
                                        content += '    tripletList_{}.clear();\n'.format(sequence)
                                content += "    for( int {}=1; {}<={}; {}++){{\n".format(left_subs[0], left_subs[0],
                                                                                         self.get_sym_type(sequence).rows,
                                                                                         left_subs[0])
                                if right_info.pre_list:
                                    content += self.update_prelist_str(right_info.pre_list, "    ")
                                content += '        tripletList_{}.push_back(Eigen::Triplet<double>({}-1, {}-1, {}));\n'.format(
                                    sequence, left_subs[0], left_subs[0], right_info.content)
                                content += "    }\n"
                                content += '    {}.setFromTriplets(tripletList_{}.begin(), tripletList_{}.end());\n'.format(
                                    sequence, sequence,
                                    sequence)
                            else:  # L_ij
                                if right_info.pre_list:
                                    content = "".join(right_info.pre_list) + content
                                # sparse mat assign
                                # right_exp += '    ' + sequence + ' = ' + right_info.content
                                # content += right_info.content
                                def_str = ""
                                if node.op != '+=':
                                    if node.left[cur_index].get_main_id() not in self.declared_symbols:
                                        def_str = "    {}.resize({}, {});\n".format(node.left[cur_index].get_main_id(),
                                                                                    self.get_sym_type(
                                                                                        node.left[cur_index].get_main_id()).rows,
                                                                                    self.get_sym_type(
                                                                                        node.left[cur_index].get_main_id()).cols)
                                        def_str += '    std::vector<Eigen::Triplet<double> > tripletList_{};\n'.format(
                                            node.left[cur_index].get_main_id())
                                    else:
                                        content += '    tripletList_{}.clear();\n'.format(node.left[cur_index].get_main_id())
                                content = def_str + content
                                pass
                        elif left_subs[0] == left_subs[1]:
                            # L_ii
                            content = ""
                            content += "    for( int {}=1; {}<={}; {}++){{\n".format(left_subs[0], left_subs[0],
                                                                                     self.get_sym_type(sequence).rows,
                                                                                     left_subs[0])
                            if right_info.pre_list:
                                content += self.update_prelist_str(right_info.pre_list, "    ")
                            content += "        {}({}-1, {}-1) = {};\n".format(sequence, left_subs[0], left_subs[0],
                                                                               right_info.content)
                            content += "    }"
                        else:
                            for right_var in type_info.symbols:
                                if sub_strs in right_var:
                                    var_ids = self.get_all_ids(right_var)
                                    right_info.content = right_info.content.replace(right_var, "{}({}, {})".format(var_ids[0],
                                                                                                                   var_ids[1][
                                                                                                                       0],
                                                                                                                   var_ids[1][
                                                                                                                       1]))
                            right_exp += "    {}({}-1, {}-1) = {}".format(node.left[cur_index].get_main_id(), left_subs[0], left_subs[1],
                                                                          right_info.content)
                            if self.get_sym_type(sequence).is_matrix():
                                if node.op == '=':
                                    # declare
                                    if sequence not in self.declared_symbols:
                                        content += "    {} = Eigen::MatrixXd::Zero({}, {});\n".format(sequence,
                                                                                                      self.get_sym_type(
                                                                                                          sequence).rows,
                                                                                                      self.get_sym_type(
                                                                                                          sequence).cols)
                            content += "    for( int {}=1; {}<={}; {}++){{\n".format(left_subs[0], left_subs[0],
                                                                                     self.get_sym_type(sequence).rows,
                                                                                     left_subs[0])
                            content += "        for( int {}=1; {}<={}; {}++){{\n".format(left_subs[1], left_subs[1],
                                                                                         self.get_sym_type(sequence).cols,
                                                                                         left_subs[1])
                            if right_info.pre_list:
                                content += self.update_prelist_str(right_info.pre_list, "        ")
                            content += "        " + right_exp + ";\n"
                            content += "        }\n"
                            content += "    }\n"
                            # content += '\n'
                    elif len(left_subs) == 1:  # sequence only
                        sequence = left_ids[0]  # y left_subs[0]
                        # replace sequence
                        for right_var in type_info.symbols:
                            if self.contain_subscript(right_var):
                                var_ids = self.get_all_ids(right_var)
                                right_info.content = right_info.content.replace(right_var,
                                                                                "{}.at({})".format(var_ids[0], var_ids[1][0]))

                        ele_type = self.get_sym_type(sequence).element_type
                        # definition
                        if self.get_sym_type(sequence).is_sequence():
                            right_exp += "    {} = {}".format(left_info.content, right_info.content)
                            content += "    {}.resize({});\n".format(sequence, self.get_sym_type(sequence).size)
                            content += "    for( int {}=1; {}<={}; {}++){{\n".format(left_subs[0], left_subs[0],
                                                                                     self.get_sym_type(sequence).size,
                                                                                     left_subs[0])
                        else:
                            # vector
                            right_exp += "    {} = {}".format(left_info.content, right_info.content)
                            content += "    {}.resize({});\n".format(sequence, self.get_sym_type(sequence).rows)
                            content += "    for( int {}=1; {}<={}; {}++){{\n".format(left_subs[0], left_subs[0],
                                                                                     self.get_sym_type(sequence).rows,
                                                                                     left_subs[0])
                        if right_info.pre_list:
                            content += self.update_prelist_str(right_info.pre_list, "    ")
                        if not node.right[cur_index].is_node(IRNodeType.MultiConds):
                            content += "    " + right_exp + ";\n"
                        content += '    }\n'
                #
                else:
                    if right_info.pre_list:
                        content = "".join(right_info.pre_list) + content
                    if type(node.right[cur_index]).__name__ == 'SparseMatrix':
                        content = right_info.content
                    elif node.right[cur_index].is_node(IRNodeType.MultiConds):
                        pass
                    else:
                        op = ' = '
                        if node.op == '+=':
                            op = ' += '
                        type_def = ""
                        if node.left[cur_index].get_main_id() in self.def_dict and not self.def_dict[node.left[0].get_main_id()]:
                            # type_def = self.get_ctype(self.get_sym_type(node.left.get_main_id())) + ' '
                            self.def_dict[node.left[cur_index].get_main_id()] = True
                        right_exp += '    ' + type_def + node.left[cur_index].get_main_id() + op + right_info.content + ';'
                        content += right_exp + '\n'
                la_remove_key(LHS, **kwargs)
                self.declared_symbols.add(node.left[cur_index].get_main_id())
        return CodeNodeInfo(content)

    def visit_if(self, node, **kwargs):
        ret_info = self.visit(node.cond)
        # ret_info.content = "if(" + ret_info.content + ")\n"
        return ret_info

    def visit_condition(self, node, **kwargs):
        if len(node.cond_list) > 1:
            pre_list = []
            content_list = []
            for condition in node.cond_list:
                info = self.visit(condition)
                pre_list += info.pre_list
                content_list.append("({})".format(info.content))
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
        pre_list += right_info.pre_list
        if node.loop:
            extra_list = []
            if node.set.la_type.index_type:
                for item in node.items:
                    item_info = self.visit(item, **kwargs)
                    item_content = item_info.content
                    extra_content = ''
                    if not item.la_type.index_type:
                        # item_content = "{}-1".format(item_info.content)
                        extra_content = '+1'
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
                    item_list.append(item_content)
                    extra_list.append(extra_content)
            if node.set.node_type != IRNodeType.Id:
                set_name = self.generate_var_name('set')
                pre_list.append('{} {} = {};\n'.format(self.get_ctype(node.set.la_type), set_name, right_info.content))
                content = 'for({} tuple : {}){{\n'.format(self.get_set_item_str(node.set.la_type), set_name)
            else:
                content = 'for({} tuple : {}){{\n'.format(self.get_set_item_str(node.set.la_type), right_info.content)
            content += '    int {} = std::get<0>(tuple){};\n'.format(item_list[0], extra_list[0])
            content += '    int {} = std::get<1>(tuple){};\n'.format(item_list[1], extra_list[1])
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
            if node.set.node_type != IRNodeType.Id:
                set_name = self.generate_var_name('set')
                pre_list.append('{} {} = {};\n'.format(self.get_ctype(node.set.la_type), set_name, right_info.content))
                content = '{}.find({}({})) != {}.end()'.format(set_name, self.get_set_item_str(node.set.la_type),
                                                               ', '.join(item_list), set_name)
            else:
                content = '{}.find({}({})) != {}.end()'.format(right_info.content,
                                                               self.get_set_item_str(node.set.la_type),
                                                               ', '.join(item_list), right_info.content)
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
        content = '{}.find({}({})) == {}.end()'.format(right_info.content,
                                                       self.get_set_item_str(self.get_sym_type(right_info.content)),
                                                       ', '.join(item_list), right_info.content)
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

    def visit_IdentifierAlone(self, node, **kwargs):
        if node.value:
            value = node.value
        else:
            value = '`' + node.id + '`'
        return CodeNodeInfo(value)

    def visit_derivative(self, node, **kwargs):
        return CodeNodeInfo("")

    def visit_optimize(self, node, **kwargs):
        self.enable_tmp_sym = True
        self.opt_key = node.key
        cur_len = 0
        param_name = self.generate_var_name('X')
        pre_list = []
        id_list = []
        init_list = []
        pack_list = []
        unpack_list = []
        param_list = []  # as function params
        decl_list = []   # declared params
        for cur_index in range(len(node.base_list)):
            cur_la_type = node.base_type_list[cur_index].la_type
            id_info = self.visit(node.base_list[cur_index], **kwargs)
            id_list.append(id_info.content)
            init_value = 0
            pack_str = ''
            unpack_str = ''
            if cur_la_type.is_scalar():
                init_value = 0
                pack_str = "{}".format(id_info.content)
                unpack_str = "        {} = {}.seqN({}, {})[0];\n".format(id_info.content, param_name, cur_len, 1)
                cur_len = add_syms(cur_len, 1)
            elif cur_la_type.is_vector():
                init_value = "np.zeros({})".format(cur_la_type.rows)
                pack_str = id_info.content
                unpack_str = "        {} = {}(Eigen::seqN({}, {}));\n".format(id_info.content, param_name, cur_len, cur_la_type.rows)
                cur_len = add_syms(cur_len, cur_la_type.rows)
            elif cur_la_type.is_matrix():
                pack_str = "Eigen::Map<Eigen::VectorXd>({}.data(), {}.cols()*{}.rows())".format(id_info.content, id_info.content, id_info.content)
                init_value = "np.zeros({}*{})".format(cur_la_type.rows, cur_la_type.cols)
                unpack_str = "        double* a = {}(Eigen::seqN({}, {})).data();\n".format(param_name, cur_len, mul_syms(cur_la_type.rows, cur_la_type.cols))
                unpack_str += "        {} = Eigen::Map<{} >(a);\n".format(id_info.content, self.get_ctype(cur_la_type))
                cur_len = add_syms(cur_len, mul_syms(cur_la_type.rows, cur_la_type.cols))
            init_list.append(init_value)
            pack_list.append(pack_str)
            unpack_list.append(unpack_str)
            param_list.append("{} & {}".format(self.get_ctype(cur_la_type), id_info.content))
            decl_list.append("{} {}".format(self.get_ctype(cur_la_type), id_info.content))
        init_var = self.generate_var_name("init")
        #
        exp_info = self.visit(node.exp, **kwargs)
        bfgs_param_name = self.generate_var_name('param')
        solver_name = self.generate_var_name('solver')
        # Handle target
        join_vec_name = self.generate_var_name('vec_joined')
        pre_list += ["    auto pack = [&]({})\n".format(', '.join(param_list)),
                     "    {\n",
                     "        Eigen::VectorXd {}({});\n".format(join_vec_name, cur_len),
                     "        {} << {};\n".format(join_vec_name, ', '.join(pack_list)),
                     "        return {};\n".format(join_vec_name),
                     "    };\n",
                     "    auto unpack = [&](Eigen::VectorXd & {}, {})\n".format(param_name, ', '.join(param_list)),
                     "    {\n",
                     "{}\n".format(''.join(unpack_list)),
                     "    };\n",
                     "    LBFGSpp::LBFGSParam<double> {};\n".format(bfgs_param_name),
                     "    {}.epsilon = 1e-6;\n".format(bfgs_param_name),
                     "    {}.max_iterations = 100;\n".format(bfgs_param_name),
                     "    LBFGSpp::LBFGSSolver<double> {}({}); \n".format(solver_name, bfgs_param_name),
                     ]
        target_func = self.generate_var_name('target')
        exp = exp_info.content
        # Handle optimization type
        if node.opt_type == OptimizeType.OptimizeMax or node.opt_type == OptimizeType.OptimizeArgmax:
            exp = "-({})".format(exp)
        # target function
        pre_list.append("    auto {} = [&](Eigen::VectorXd & {})\n".format(target_func, param_name))
        pre_list.append("    {\n")
        pre_list.append("        {};\n".format(';\n        '.join(decl_list)))
        pre_list.append("        unpack({}, {});\n".format(param_name, ', '.join(id_list)))
        if len(exp_info.pre_list) > 0:
            for pre in exp_info.pre_list:
                lines = pre.split('\n')
                for line in lines:
                    if line != "":
                        pre_list.append("    {}\n".format(line))
        pre_list.append("        return {};\n".format(exp))
        pre_list.append("    };\n")
        # gradient function for LBFGS
        helper_func = self.generate_var_name("helper")
        eps_name = self.generate_var_name("eps")
        pre_list.append("    double {} = 1e-6;\n".format(eps_name))
        pre_list.append("    auto {} = [&](Eigen::VectorXd & {}, Eigen::VectorXd & grad)\n".format(helper_func, param_name))
        pre_list.append("    {\n")
        pre_list.append("        double f_X = {}({});\n".format(target_func, param_name))
        pre_list.append("        for(int i = 0; i < grad.size(); ++i )\n")
        pre_list.append("        {\n")
        pre_list.append("            const double {}_i = {}[i];\n".format(param_name, param_name))
        pre_list.append("            {}[i] += {};\n".format(param_name, eps_name))
        pre_list.append("            grad[i] = ({}({}) - f_X)/{};\n".format(target_func, param_name, eps_name))
        pre_list.append("            {}[i] = {}_i;\n".format(param_name, param_name))
        pre_list.append("        }\n")
        pre_list.append("        return f_X;\n")
        pre_list.append("    };\n")
        #
        pre_list.append("    Eigen::VectorXd {} = Eigen::VectorXd::Zero({});\n".format(init_var, cur_len))
        pre_list.append("    double fx;\n")
        #
        content = ''
        if node.opt_type == OptimizeType.OptimizeMin:
            content = "{}.minimize({}, {}, fx)".format(solver_name, helper_func, init_var)
        elif node.opt_type == OptimizeType.OptimizeMax:
            content = "{}.minimize({}, {}, fx)".format(solver_name, helper_func, init_var)
        elif node.opt_type == OptimizeType.OptimizeArgmin or node.opt_type == OptimizeType.OptimizeArgmax:
            pre_list.append("    {};\n".format(';\n    '.join(decl_list)))
            pre_list.append("    {}.minimize({}, {}, fx);\n".format(solver_name, helper_func, init_var))
            pre_list.append("    unpack({}, {});\n".format(init_var, ', '.join(id_list)))
            content = ', '.join(id_list)
        self.enable_tmp_sym = False
        return CodeNodeInfo(content, pre_list=pre_list)

    def visit_domain(self, node, **kwargs):
        return CodeNodeInfo("")

    def visit_integral(self, node, **kwargs):
        return CodeNodeInfo("")

    def visit_inner_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        content = "({}).dot({})".format(left_info.content, right_info.content)
        if node.sub:
            sub_info = self.visit(node.sub, **kwargs)
            content = "({}).transpose() * ({}) * ({})".format(right_info.content, sub_info.content, left_info.content)
        return CodeNodeInfo(content, pre_list=left_info.pre_list + right_info.pre_list)

    def visit_fro_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("({}).cwiseProduct({}).sum()".format(left_info.content, right_info.content),
                            pre_list=left_info.pre_list + right_info.pre_list)

    def visit_hadamard_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("({}).cwiseProduct({})".format(left_info.content, right_info.content),
                            pre_list=left_info.pre_list + right_info.pre_list)

    def visit_cross_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("({}).cross({})".format(left_info.content, right_info.content),
                            pre_list=left_info.pre_list + right_info.pre_list)

    def visit_kronecker_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        index_i = self.generate_var_name('i')
        index_j = self.generate_var_name('j')
        kronecker = self.generate_var_name('kron')
        pre_list = left_info.pre_list + right_info.pre_list
        sparse = node.la_type.sparse
        node.la_type.sparse = False
        if node.la_type.is_dim_constant():
            pre_list.append("    {} {};\n".format(self.get_ctype(node.la_type), kronecker))
        else:
            pre_list.append("    {} {}({}, {});\n".format(self.get_ctype(node.la_type), kronecker, node.la_type.rows,
                                                          node.la_type.cols))
        node.la_type.sparse = sparse
        pre_list.append("    for( int {}=0; {}<{}; {}++){{\n".format(index_i, index_i, node.left.la_type.rows, index_i))
        pre_list.append(
            "        for( int {}=0; {}<{}; {}++){{\n".format(index_j, index_j, node.left.la_type.cols, index_j))
        if node.left.la_type.is_sparse_matrix():
            left_index_content = "({}).coeff({}, {})".format(left_info.content, index_i, index_j)
        else:
            left_index_content = "({})({}, {})".format(left_info.content, index_i, index_j)
        pre_list.append(
            "            {}.block({}*{},{}*{},{},{}) = {}*({});\n".format(kronecker, index_i, node.right.la_type.rows,
                                                                          index_j, node.right.la_type.cols,
                                                                          node.right.la_type.rows,
                                                                          node.right.la_type.cols,
                                                                          left_index_content, right_info.content))
        pre_list.append("        }\n")
        pre_list.append("    }\n")
        if node.la_type.is_sparse_matrix():
            kronecker += '.sparseView()'
        return CodeNodeInfo(content=kronecker, pre_list=pre_list)

    def visit_dot_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("({}).dot({})".format(left_info.content, right_info.content),
                            pre_list=left_info.pre_list + right_info.pre_list)

    def visit_math_func(self, node, **kwargs):
        content = ''
        param_info = self.visit(node.param, **kwargs)
        pre_list = param_info.pre_list
        params_content = param_info.content
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
            content = '1/tan'
        elif node.func_type == MathFuncType.MathFuncSec:
            content = '1/cos'
        elif node.func_type == MathFuncType.MathFuncCsc:
            content = '1/sin'
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
            return CodeNodeInfo('(log10({}) / log10(2))'.format(params_content), pre_list=pre_list)
        elif node.func_type == MathFuncType.MathFuncLog10:
            content = 'log10'
        elif node.func_type == MathFuncType.MathFuncLn:
            content = 'log'
        elif node.func_type == MathFuncType.MathFuncSqrt:
            content = 'sqrt'
        if node.func_type < MathFuncType.MathFuncTrace:
            if node.param.la_type.is_scalar():
                content = "{}({})".format(content, params_content)
            else:
                content = "{}.unaryExpr<double(*)(double)>(&std::{})".format(params_content, content)
                if node.func_type == MathFuncType.MathFuncCot:
                    content = "{}.unaryExpr<double(*)(double)>(&std::tan).cwiseInverse()".format(params_content)
                elif node.func_type == MathFuncType.MathFuncSec:
                    content = "{}.unaryExpr<double(*)(double)>(&std::cos).cwiseInverse()".format(params_content)
                elif node.func_type == MathFuncType.MathFuncCsc:
                    content = "{}.unaryExpr<double(*)(double)>(&std::sin).cwiseInverse()".format(params_content)
        else:
            # linear algebra
            if node.func_type == MathFuncType.MathFuncTrace:
                content = "({}).trace()".format(params_content)
            elif node.func_type == MathFuncType.MathFuncDiag:
                if node.param.la_type.is_vector():
                    content = "({}).asDiagonal()".format(params_content)
                else:
                    content = "({}).diagonal()".format(params_content)
            elif node.func_type == MathFuncType.MathFuncVec:
                vec_name = self.generate_var_name("vec")
                content = '{}'.format(vec_name)
                pre_list.append(
                    '    Eigen::VectorXd {}(Eigen::Map<Eigen::VectorXd>(((Eigen::MatrixXd)({})).data(), ({}).cols()*({}).rows()));;\n'.format(
                        vec_name, params_content, params_content, params_content))
            elif node.func_type == MathFuncType.MathFuncDet:
                content = "({}).determinant()".format(params_content)
            elif node.func_type == MathFuncType.MathFuncRank:
                rank_name = self.generate_var_name("rank")
                content = '{}.rank()'.format(rank_name)
                pre_list.append('    Eigen::FullPivLU<Eigen::MatrixXd> {}({});\n'.format(rank_name, params_content))
            elif node.func_type == MathFuncType.MathFuncNull:
                null_name = self.generate_var_name("null")
                content = '{}.kernel()'.format(null_name)
                pre_list.append('    Eigen::FullPivLU<Eigen::MatrixXd> {}({});\n'.format(null_name, params_content))
            elif node.func_type == MathFuncType.MathFuncOrth:
                content = 'orth'
            elif node.func_type == MathFuncType.MathFuncInv:
                content = "({}).inverse()".format(params_content)
        return CodeNodeInfo(content, pre_list=pre_list)

    def visit_fraction(self, node, **kwargs):
        return CodeNodeInfo("({}/double({}))".format(node.numerator, node.denominator))

    def visit_constant(self, node, **kwargs):
        content = ''
        if node.c_type == ConstantType.ConstantPi:
            content = 'M_PI'
        elif node.c_type == ConstantType.ConstantE:
            content = 'M_E'
        return CodeNodeInfo(content)

    ###################################################################
