from .codegen import *
from .type_walker import *


class CodeGenEigen(CodeGen):
    def __init__(self):
        super().__init__(ParserTypeEnum.EIGEN)

    def init_type(self, type_walker, func_name):
        super().init_type(type_walker, func_name)
        self.pre_str = '''/*\n{}\n*/\n#include <Eigen/Core>\n#include <Eigen/Dense>\n#include <Eigen/Sparse>\n#include <iostream>\n#include <set>\n'''.format(self.la_content)
        self.post_str = ''''''
        self.ret = 'ret'
        if self.unofficial_method:
            self.pre_str += '#include <unsupported/Eigen/MatrixFunctions>\n'
        self.pre_str += '\n'

    def get_dim_check_str(self):
        check_list = []
        if len(self.same_dim_list) > 0:
            check_list = super().get_dim_check_str()
            check_list = ['    assert( {} );'.format(stat) for stat in check_list]
        return check_list

    def get_set_item_str(self, set_type):
        type_list = []
        for index in range(set_type.size):
            if set_type.int_list[index]:
                type_list.append('int')
            else:
                type_list.append('double')
        return "std::tuple< {} >".format(", ".join(type_list))

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
            type_str = "std::function<{}({})>".format(self.get_ctype(la_type.ret), self.get_func_params_str(la_type))
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

    def get_set_test_list(self, parameter, la_type, rand_int_max, pre='    '):
        test_content = []
        test_content.append('const int {}_0 = rand()%10;'.format(parameter, rand_int_max))
        test_content.append('for(int i=0; i<{}_0; i++){{'.format(parameter))
        gen_list = []
        for i in range(la_type.size):
            if la_type.int_list[i]:
                gen_list.append('rand()%{}'.format(rand_int_max))
            else:
                gen_list.append('rand()%10')
        test_content.append(
            '    {}.insert(std::make_tuple('.format(parameter) + ', '.join(gen_list) + '));')
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
                if self.symtable[node.main_id].is_matrix():
                    if self.symtable[node.main_id].sparse:
                        content = "{}.coeff({}, {})".format(node.main_id, node.subs[0], node.subs[1])
                    else:
                        content = "{}({}, {})".format(node.main_id, node.subs[0], node.subs[1])
        return CodeNodeInfo(content)

    def visit_start(self, node, **kwargs):
        return self.visit(node.stat, **kwargs)

    def get_struct_definition(self):
        item_list = []
        def_list = []
        assign_list = []
        for parameter in self.lhs_list:
            item_list.append("    {} {};".format(self.get_ctype(self.symtable[parameter]), parameter))
            def_list.append("const {} & {}".format(self.get_ctype(self.symtable[parameter]), parameter))
            assign_list.append("{}({})".format(parameter, parameter))
        content = ["struct {} {{".format(self.get_result_type()),
                   "{}".format('\n'.join(item_list)),
                   "    {}({})".format(self.get_result_type(), ',\n               '.join(def_list)),
                   "    : {}".format(',\n    '.join(assign_list)),
                   "    {}",
                   "};\n"]
        return "\n".join(content)

    def get_ret_struct(self):
        return "{}({})".format(self.get_result_type(), ', '.join(self.lhs_list))

    def visit_block(self, node, **kwargs):
        type_checks = []
        doc = []
        show_doc = False
        rand_func_name = "generateRandomData"
        test_content = []
        test_function = ['{']
        rand_int_max = 10
        # main
        main_declaration = []
        main_print = []
        main_content = ["int main(int argc, char *argv[])",
                        "{",
                        "    srand((int)time(NULL));"]
        dim_content = ""
        dim_defined_dict = {}
        dim_defined_list = []
        if self.dim_dict:
            for key, target_dict in self.dim_dict.items():
                if key in self.parameters:
                    continue
                target = list(target_dict.keys())[0]
                dim_defined_dict[target] = target_dict[target]
                #
                has_defined = False
                if len(self.same_dim_list) > 0:
                    if key not in dim_defined_list:
                        for cur_set in self.same_dim_list:
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
                if not has_defined:
                    test_content.append("    const int {} = rand()%{};".format(key, rand_int_max))
                if self.symtable[target].is_sequence():
                    if target_dict[target] == 0:
                        dim_content += "    const long {} = {}.size();\n".format(key, target)
                    elif target_dict[target] == 1:
                        dim_content += "    const long {} = {}[0].rows();\n".format(key, target)
                    elif target_dict[target] == 2:
                        dim_content += "    const long {} = {}[0].cols();\n".format(key, target)
                elif self.symtable[target].is_matrix():
                    if target_dict[target] == 0:
                        dim_content += "    const long {} = {}.rows();\n".format(key, target)
                    else:
                        dim_content += "    const long {} = {}.cols();\n".format(key, target)
                elif self.symtable[target].is_vector():
                    dim_content += "    const long {} = {}.size();\n".format(key, target)
        par_des_list = []
        test_par_list = []
        for parameter in self.parameters:
            main_declaration.append("    {} {};".format(self.get_ctype(self.symtable[parameter]), parameter))
            par_des_list.append("const {} & {}".format(self.get_ctype(self.symtable[parameter]), parameter))
            test_par_list.append("{} & {}".format(self.get_ctype(self.symtable[parameter]), parameter))
            if self.symtable[parameter].desc:
                show_doc = True
                doc.append('@param {} {}'.format(parameter, self.symtable[parameter].desc))
            if self.symtable[parameter].is_sequence():
                ele_type = self.symtable[parameter].element_type
                data_type = ele_type.element_type
                integer_type = False
                test_content.append('    {}.resize({});'.format(parameter, self.symtable[parameter].size))
                test_content.append('    for(int i=0; i<{}; i++){{'.format(self.symtable[parameter].size))
                if isinstance(data_type, LaVarType):
                    if data_type.is_scalar() and data_type.is_int:
                        integer_type = True
                if not (parameter in dim_defined_dict and dim_defined_dict[parameter] == 0):
                    type_checks.append(
                        '    assert( {}.size() == {} );'.format(parameter, self.symtable[parameter].size))
                if ele_type.is_matrix():
                    if not ele_type.is_dim_constant():
                        type_checks.append('    for( const auto& el : {} ) {{'.format(parameter))
                        type_checks.append('        assert( el.rows() == {} );'.format(ele_type.rows))
                        type_checks.append('        assert( el.cols() == {} );'.format(ele_type.cols))
                        type_checks.append('    }')
                    sparse_view = ''
                    if ele_type.sparse:
                        sparse_view = '.sparseView()'
                    if integer_type:
                        test_content.append(
                            '        {}[i] = Eigen::MatrixXi::Random({}, {}){};'.format(parameter, ele_type.rows,
                                                                                      ele_type.cols, sparse_view))
                    else:
                        test_content.append(
                            '        {}[i] = Eigen::MatrixXd::Random({}, {}){};'.format(parameter, ele_type.rows,
                                                                                      ele_type.cols, sparse_view))
                elif ele_type.is_vector():
                    if not ele_type.is_dim_constant():
                        type_checks.append('    for( const auto& el : {} ) {{'.format(parameter))
                        type_checks.append('        assert( el.size() == {} );'.format(ele_type.rows))
                        type_checks.append('    }')
                    if integer_type:
                        test_content.append(
                            '        {}[i] = Eigen::VectorXi::Random({});'.format(parameter, ele_type.rows))
                    else:
                        test_content.append(
                            '        {}[i] = Eigen::VectorXd::Random({});'.format(parameter, ele_type.rows))
                elif ele_type.is_scalar():
                    test_content.append(
                        '        {}[i] = rand() % {};'.format(parameter, rand_int_max))
                test_content.append('    }')
            elif self.symtable[parameter].is_matrix():
                element_type = self.symtable[parameter].element_type
                sparse_view = ''
                if self.symtable[parameter].sparse:
                    sparse_view = '.sparseView()'
                if isinstance(element_type, LaVarType):
                    if element_type.is_scalar() and element_type.is_int:
                        test_content.append(
                            '    {} = Eigen::MatrixXi::Random({}, {}){};'.format(parameter, self.symtable[parameter].rows,
                                                                               self.symtable[parameter].cols, sparse_view))
                    else:
                        test_content.append(
                            '    {} = Eigen::MatrixXd::Random({}, {}){};'.format(parameter, self.symtable[parameter].rows,
                                                                               self.symtable[parameter].cols, sparse_view))
                else:
                    test_content.append(
                        '    {} = Eigen::MatrixXd::Random({}, {}){};'.format(parameter, self.symtable[parameter].rows,
                                                                           self.symtable[parameter].cols,sparse_view))
                if not self.symtable[parameter].is_dim_constant() or self.symtable[parameter].sparse:
                    if not (parameter in dim_defined_dict and dim_defined_dict[parameter] == 0):
                        type_checks.append(
                            '    assert( {}.rows() == {} );'.format(parameter, self.symtable[parameter].rows))
                    if not (parameter in dim_defined_dict and dim_defined_dict[parameter] == 1):
                        type_checks.append(
                            '    assert( {}.cols() == {} );'.format(parameter, self.symtable[parameter].cols))
            elif self.symtable[parameter].is_vector():
                element_type = self.symtable[parameter].element_type
                if isinstance(element_type, LaVarType):
                    if element_type.is_scalar() and element_type.is_int:
                        test_content.append(
                            '    {} = Eigen::VectorXi::Random({});'.format(parameter, self.symtable[parameter].rows))
                    else:
                        test_content.append(
                            '    {} = Eigen::VectorXd::Random({});'.format(parameter, self.symtable[parameter].rows))
                else:
                    test_content.append(
                        '    {} = Eigen::VectorXd::Random({});'.format(parameter, self.symtable[parameter].rows))
                if not self.symtable[parameter].is_dim_constant():
                    if not (parameter in dim_defined_dict and dim_defined_dict[parameter] == 0):
                        type_checks.append(
                            '    assert( {}.size() == {} );'.format(parameter, self.symtable[parameter].rows))
            elif self.symtable[parameter].is_scalar():
                test_function.append('    {} = rand() % {};'.format(parameter, rand_int_max))
            elif self.symtable[parameter].is_set():
                test_content.append('    const int {}_0 = rand()%10;'.format(parameter, rand_int_max))
                test_content.append('    for(int i=0; i<{}_0; i++){{'.format(parameter))
                gen_list = []
                for i in range(self.symtable[parameter].size):
                    if self.symtable[parameter].int_list[i]:
                        gen_list.append('rand()%{}'.format(rand_int_max))
                    else:
                        gen_list.append('rand()%10')
                test_content.append(
                    '        {}.insert(std::make_tuple('.format(parameter) + ', '.join(gen_list) + '));')
                test_content.append('    }')
            elif self.symtable[parameter].is_function():
                name_required = False
                dim_definition = []
                if self.symtable[parameter].ret_template():
                    name_required = True
                    for ret_dim in self.symtable[parameter].ret_symbols:
                        param_i = self.symtable[parameter].template_symbols[ret_dim]
                        if self.symtable[parameter].params[param_i].is_vector():
                            dim_definition.append('        long {} = {}{}.size();'.format(ret_dim, self.param_name_test, param_i))
                        elif self.symtable[parameter].params[param_i].is_matrix():
                            if ret_dim == self.symtable[parameter].params[param_i].rows:
                                dim_definition.append('        long {} = {}{}.rows();'.format(ret_dim, self.param_name_test, param_i))
                            else:
                                dim_definition.append('        long {} = {}{}.cols();'.format(ret_dim, self.param_name_test, param_i))
                test_content.append('    {} = []({})->{}{{'.format(parameter, self.get_func_params_str(self.symtable[parameter], name_required), self.get_ctype(self.symtable[parameter].ret)))
                test_content += dim_definition
                if self.symtable[parameter].ret.is_set():
                    test_content.append('        {} tmp;'.format(self.get_ctype(self.symtable[parameter].ret)))
                    test_content += self.get_set_test_list('tmp', self.symtable[parameter].ret, rand_int_max, '        ')
                    test_content.append('        return tmp;')
                else:
                    test_content.append('        return {}'.format(self.get_rand_test_str(self.symtable[parameter].ret, rand_int_max)))
                test_content.append('    };')
            # main_print.append('    std::cout<<"{}:\\n"<<{}<<std::endl;'.format(parameter, parameter))
        content = ""
        content += self.get_struct_definition() + '\n'
        if show_doc:
            content += '/**\n * ' + self.func_name + '\n *\n * ' + '\n * '.join(doc) + '\n * @return {}\n */\n'.format(
                self.ret_symbol)
        # ret_type = self.get_ctype(self.symtable[self.ret_symbol])
        ret_type = self.get_result_type()
        if len(self.parameters) == 0:
            content += ret_type + ' ' + self.func_name + '(' + ')\n{\n'  # func name
            test_function.insert(0, "void {}({})".format(rand_func_name, ', '.join(test_par_list)))
        elif len(self.parameters) == 1:
            content += ret_type + ' ' + self.func_name + '(' + ', '.join(par_des_list) + ')\n{\n'  # func name
            test_function.insert(0, "void {}({})".format(rand_func_name, ', '.join(test_par_list)))
        else:
            content += ret_type + ' ' + self.func_name + '(\n    ' + ',\n    '.join(par_des_list) + ')\n{\n'  # func name
            test_function.insert(0, "void {}({})".format(rand_func_name, ',\n    '.join(test_par_list)))
        # merge content
        # content += '\n'.join(type_declare) + '\n\n'
        content += dim_content
        type_checks += self.get_dim_check_str()
        if len(type_checks) > 0:
            content += '\n'.join(type_checks) + '\n\n'
        # statements
        stats_content = ""
        for index in range(len(node.stmts)):
            ret_str = ''
            need_semicolon = False
            if index == len(node.stmts) - 1:
                if type(node.stmts[index]).__name__ != 'AssignNode':
                    kwargs[LHS] = self.ret_symbol
                    ret_str = "    " + self.get_ctype(self.symtable[self.ret_symbol]) + " " + self.ret_symbol + ' = '
                    need_semicolon = True
            else:
                if type(node.stmts[index]).__name__ != 'AssignNode':
                    # meaningless
                    continue
            stat_info = self.visit(node.stmts[index], **kwargs)
            if stat_info.pre_list:
                stats_content += "".join(stat_info.pre_list)
            if need_semicolon:
                stats_content += ret_str + stat_info.content + ';\n'
            else:
                stats_content += ret_str + stat_info.content + '\n'

        content += stats_content
        # return value
        # ret_value = self.ret_symbol
        ret_value = self.get_ret_struct()
        content += '    return ' + ret_value + ';'
        content += '\n}\n'
        # test
        # test_content.append('    return {}'.format(', '.join(self.parameters)))
        test_function += test_content
        test_function.append('}')
        # main
        main_content += main_declaration
        main_content.append("    {}({});".format(rand_func_name, ', '.join(self.parameters)))
        main_content += main_print
        main_content.append(
            "    {} func_value = {}({});".format(self.get_result_type(), self.func_name,
                                                 ', '.join(self.parameters)))
        if self.symtable[self.ret_symbol].is_matrix() or self.symtable[self.ret_symbol].is_vector() or self.symtable[self.ret_symbol].is_scalar():
            main_content.append('    std::cout<<"return value:\\n"<<func_value.{}<<std::endl;'.format(self.ret_symbol))
        else:
            # sequence
            main_content.append('    std::cout<<"vector return value:"<<std::endl;')
            main_content.append('    for(int i=0; i<func_value.{}.size(); i++){{'.format(self.ret_symbol))
            main_content.append('        std::cout<<"i:"<<i<<", value:\\n"<<func_value.{}.at(i)<<std::endl;'.format(self.ret_symbol))
            main_content.append('    }')
        main_content.append('    return 0;')
        main_content.append('}')
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
                    name_convention[var] = "{}({}, {})".format(var_ids[0], var_ids[1][0], var_ids[1][1])
                else:
                    name_convention[var] = "{}.at({})".format(var_ids[0], var_ids[1][0])
        for sym, subs in node.sym_dict.items():
            target_var.append(sym)
        self.add_name_conventions(name_convention)
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
        if self.symtable[assign_id].is_matrix():
            if self.symtable[assign_id].sparse:
                content.append("{} {}({}, {});\n".format(self.get_ctype(self.symtable[assign_id]), assign_id, self.symtable[
                    assign_id].rows, self.symtable[assign_id].cols))
            else:
                content.append("Eigen::MatrixXd {} = Eigen::MatrixXd::Zero({}, {});\n".    format(assign_id, self.symtable[assign_id].rows,
                                                                               self.symtable[assign_id].cols))
        elif self.symtable[assign_id].is_vector():
            content.append(
                "Eigen::MatrixXd {} = Eigen::MatrixXd::Zero({}, 1);\n".format(assign_id, self.symtable[assign_id].rows))
        elif self.symtable[assign_id].is_sequence():
            ele_type = self.symtable[assign_id].element_type
            content.append(
                "Eigen::MatrixXd {} = np.zeros(({}, {}, {}))\n".format(assign_id, self.symtable[assign_id].size,
                                                                       ele_type.rows, ele_type.cols))
        else:
            content.append("double {} = 0;\n".format(assign_id))
        sym_info = node.sym_dict[target_var[0]]
        if self.symtable[target_var[0]].is_matrix():  # todo
            if sub == sym_info[0]:
                content.append("for(int {}=1; {}<={}.rows(); {}++){{\n".format(sub, sub, target_var[0], sub))
            else:
                content.append("for(int {}=1; {}<={}.cols(); {}++){{\n".format(sub, sub, target_var[0], sub))
        else:
            content.append("for(int {}=1; {}<={}.size(); {}++){{\n".format(sub, sub, target_var[0], sub))
        if exp_info.pre_list:  # catch pre_list
            list_content = "".join(exp_info.pre_list)
            # content += exp_info.pre_list
            list_content = list_content.split('\n')
            for index in range(len(list_content)):
                if index != len(list_content) - 1:
                    content.append(list_content[index] + '\n')
        # only one sub for now
        if node.cond:
            content.append("    " + cond_content)
            content.append(str("        " + assign_id + " += " + exp_str + ';\n'))
            content.append("    }\n")
        else:
            content.append(str("    " + assign_id + " += " + exp_str + ';\n'))
        content[0] = "    " + content[0]

        content.append("}\n")
        self.del_name_conventions(name_convention)
        return CodeNodeInfo(assign_id, pre_list=["    ".join(content)])

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
                    content = "({}).lpNorm<{}>()".format(value, node.sub)
            elif node.norm_type == NormType.NormMax:
                content = "({}).lpNorm<Eigen::Infinity>()".format(value)
            elif node.norm_type == NormType.NormIdentifier:
                sub_info = self.visit(node.sub, **kwargs)
                pre_list += sub_info.pre_list
                if node.sub.la_type.is_scalar():
                    content = "pow(({}).cwiseAbs().array().pow({}).sum(), 1.0/{});".format(value, sub_info.content, sub_info.content)
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
                pre_list.append("    Eigen::JacobiSVD<Eigen::MatrixXd> {}(T, Eigen::ComputeThinU | Eigen::ComputeThinV);\n".format(svd_name))
        return CodeNodeInfo(content, pre_list=pre_list)

    def visit_transpose(self, node, **kwargs):
        f_info = self.visit(node.f, **kwargs)
        f_info.content = "{}.transpose()".format(f_info.content)
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
                    pre_list.append("    Eigen::SparseQR <{}, Eigen::COLAMDOrdering<int> > {};\n".format(self.get_ctype(node.base.la_type), solver_name))
                    pre_list.append("    {}.compute({});\n".format(solver_name, base_info.content))
                    pre_list.append("    {} {}({}, {});\n".format(self.get_ctype(node.base.la_type), identity_name, node.base.la_type.rows, node.base.la_type.cols))
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
                base_info.pre_list.append("    Eigen::MatrixPower<{}> {}({});\n".format(self.get_ctype(node.la_type), name, base_info.content))
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
                left_info.content = "{}.colPivHouseholderQr().solve(({}).toDense())".format(left_info.content, right_info.content)
            else:
                left_info.content = "{}.colPivHouseholderQr().solve({})".format(left_info.content, right_info.content)
        left_info.pre_list += pre_list
        return left_info

    def visit_sparse_matrix(self, node, **kwargs):
        assign_node = node.get_ancestor(IRNodeType.Assignment)
        type_info = node
        cur_m_id = type_info.symbol
        pre_list = []
        if_info = self.visit(node.ifs, **kwargs)
        pre_list += if_info.content
        pre_list.append(
            '    {}.setFromTriplets(tripletList_{}.begin(), tripletList_{}.end());\n'.format(assign_node.left.get_main_id(),
                                                                                             assign_node.left.get_main_id(),
                                                                                             assign_node.left.get_main_id()))
        return CodeNodeInfo(cur_m_id, pre_list)

    def visit_sparse_ifs(self, node, **kwargs):
        assign_node = node.get_ancestor(IRNodeType.Assignment)
        sparse_node = node.get_ancestor(IRNodeType.SparseMatrix)
        subs = assign_node.left.subs
        ret = ["    for( int {}=1; {}<={}; {}++){{\n".format(subs[0], subs[0], sparse_node.la_type.rows, subs[0]),
               "        for( int {}=1; {}<={}; {}++){{\n".format(subs[1], subs[1], sparse_node.la_type.cols, subs[1])]
        pre_list = []
        for cond in node.cond_list:
            cond_info = self.visit(cond, **kwargs)
            for index in range(len(cond_info.content)):
                cond_info.content[index] = '            ' + cond_info.content[index]
            ret += cond_info.content
            pre_list += cond_info.pre_list
        ret.append("        }\n")
        ret.append("    }\n")
        return CodeNodeInfo(ret, pre_list)


    def visit_sparse_if(self, node, **kwargs):
        self.convert_matrix = True
        assign_node = node.get_ancestor(IRNodeType.Assignment)
        subs = assign_node.left.subs
        cond_info = self.visit(node.cond, **kwargs)
        stat_info = self.visit(node.stat, **kwargs)
        content = cond_info.pre_list
        stat_content = stat_info.content
        # replace '_ij' with '(i,j)'
        stat_content = stat_content.replace('_{}{}'.format(subs[0], subs[1]), '({}, {})'.format(subs[0], subs[1]))
        content.append('if({}){{\n'.format(cond_info.content))
        content += stat_info.pre_list
        content.append('    tripletList_{}.push_back(Eigen::Triplet<double>({}-1, {}-1, {}));\n'.format(assign_node.left.main.main_id, subs[0], subs[1], stat_content))
        content.append('}\n')
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
        if self.symtable[cur_m_id].is_dim_constant():
            content = '    Eigen::Matrix<double, {}, 1> {};\n'.format(self.symtable[cur_m_id].rows, cur_m_id)
        else:
            content = '    Eigen::VectorXd {}({});\n'.format(cur_m_id, self.symtable[cur_m_id].rows)
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
        if self.symtable[cur_m_id].sparse and self.symtable[cur_m_id].block:
            row_index = 0       # start position for item
            # convert to sparse matrix
            sparse_id = "{}".format(cur_m_id)
            sparse_triplet = "tripletList{}".format(cur_m_id)
            tmp_sparse_name = self.generate_var_name("tmp")
            content += 'Eigen::SparseMatrix<double> {}({}, {});\n'.format(cur_m_id, self.symtable[cur_m_id].rows, self.symtable[cur_m_id].cols)
            content += '    std::vector<Eigen::Triplet<double> > {};\n'.format(sparse_triplet)
            first_item = True
            for i in range(len(ret)):
                col_index = 0
                cur_row_size = 1
                for j in range(len(ret[i])):
                    cur_scalar = False   # 1x1
                    # get size for current item
                    cur_col_size = 1
                    if type_info.la_type.list_dim and (i, j) in type_info.la_type.list_dim:
                        cur_col_size = type_info.la_type.list_dim[(i, j)][1]
                        cur_row_size = type_info.la_type.list_dim[(i, j)][0]
                    else:
                        if type_info.la_type.item_types[i][j].la_type.is_matrix() or type_info.la_type.item_types[i][j].la_type.is_vector():
                            cur_col_size = type_info.la_type.item_types[i][j].la_type.cols
                            cur_row_size = type_info.la_type.item_types[i][j].la_type.rows
                    if 'Eigen::MatrixXd::Zero' in ret[i][j]:
                        # no need to handle zero
                        col_index += cur_col_size
                        continue
                    # get content for current item
                    if type_info.la_type.item_types[i][j].la_type.is_matrix() and type_info.la_type.item_types[i][j].la_type.sparse:
                        item_content = ret[i][j]
                    else:
                        if type_info.la_type.item_types[i][j].la_type.is_matrix() or type_info.la_type.item_types[i][j].la_type.is_vector()\
                                or (type_info.la_type.list_dim and (i, j) in type_info.la_type.list_dim):
                            if type_info.la_type.list_dim[(i, j)][0] == 1 and type_info.la_type.list_dim[(i, j)][1] == 1:
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
            if self.symtable[cur_m_id].is_dim_constant():
                content += 'Eigen::Matrix<double, {}, {}> {};\n'.format(self.symtable[cur_m_id].rows,
                                                                        self.symtable[cur_m_id].cols, cur_m_id)
            else:
                content += 'Eigen::MatrixXd {}({}, {});\n'.format(cur_m_id, self.symtable[cur_m_id].rows,
                                                                    self.symtable[cur_m_id].cols)
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
                if self.symtable[main_info.content].sparse:
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
                    content = "{}.at({})({}, {})".format(main_info.content, main_index_content, row_content, col_content)
                else:
                    # use [] instead of (): vector-like data structure
                    content = "{}.at({})[{}]".format(main_info.content, main_index_content, row_content)
            else:
                content = "{}.at({})".format(main_info.content, main_index_content)
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
        left_info.content = left_info.content + ' * ' + right_info.content
        left_info.pre_list += right_info.pre_list
        return left_info

    def visit_div(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = "{} / double({})".format(left_info.content, right_info.content)
        left_info.pre_list += right_info.pre_list
        return left_info

    def visit_sub_expr(self, node, **kwargs):
        value_info = self.visit(node.value, **kwargs)
        value_info.content = '(' + value_info.content + ')'
        return value_info

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
        content = ""
        left_info = self.visit(node.left, **kwargs)
        left_id = left_info.content
        kwargs[LHS] = left_id
        kwargs[ASSIGN_TYPE] = node.op
        # self left-hand-side symbol
        right_info = self.visit(node.right, **kwargs)
        right_exp = ""
        # y_i = stat
        if node.left.contain_subscript():
            left_ids = node.left.get_all_ids()
            left_subs = left_ids[1]
            if len(left_subs) == 2:  # matrix only
                sequence = left_ids[0]  # y left_subs[0]
                sub_strs = left_subs[0] + left_subs[1]
                if self.symtable[sequence].is_matrix() and self.symtable[sequence].sparse:
                    if left_subs[0] == left_subs[1]:  # L_ii
                        if self.symtable[sequence].diagonal:
                            # add definition
                            content += "    Eigen::SparseMatrix<double> {}({}, {});\n".format(sequence,
                                                                                             self.symtable[sequence].rows,
                                                                                             self.symtable[sequence].cols)
                            content += '    std::vector<Eigen::Triplet<double> > tripletList_{};\n'.format(sequence)
                        content += "    for( int {}=1; {}<={}; {}++){{\n".format(left_subs[0], left_subs[0],
                                                                                 self.symtable[sequence].rows,
                                                                                 left_subs[0])
                        if right_info.pre_list:
                            content += self.update_prelist_str(right_info.pre_list, "    ")
                        content += '        tripletList_{}.push_back(Eigen::Triplet<double>({}-1, {}-1, {}));\n'.format(
                            sequence, left_subs[0], left_subs[0], right_info.content)
                        content += "    }\n"
                        content += '    {}.setFromTriplets(tripletList_{}.begin(), tripletList_{}.end());\n'.format(sequence, sequence,
                                                                                            sequence)
                    else:  # L_ij
                        if right_info.pre_list:
                            content = "".join(right_info.pre_list) + content
                        # sparse mat assign
                        # right_exp += '    ' + sequence + ' = ' + right_info.content
                        # content += right_info.content
                        def_str = ""
                        if node.op != '+=':
                            def_str = "    Eigen::SparseMatrix<double> {}({}, {});\n".format(node.left.get_main_id(),
                                                                                             self.symtable[node.left.get_main_id()].rows,
                                                                                             self.symtable[node.left.get_main_id()].cols)
                            def_str += '    std::vector<Eigen::Triplet<double> > tripletList_{};\n'.format(
                                node.left.get_main_id())
                        content = def_str + content
                        pass
                elif left_subs[0] == left_subs[1]:
                    # L_ii
                    content = ""
                    content += "    for( int {}=1; {}<={}; {}++){{\n".format(left_subs[0], left_subs[0],
                                                                            self.symtable[sequence].rows, left_subs[0])
                    if right_info.pre_list:
                        content += self.update_prelist_str(right_info.pre_list, "    ")
                    content += "        {}({}-1, {}-1) = {};\n".format(sequence, left_subs[0], left_subs[0], right_info.content)
                    content += "    }"
                else:
                    for right_var in type_info.symbols:
                        if sub_strs in right_var:
                            var_ids = self.get_all_ids(right_var)
                            right_info.content = right_info.content.replace(right_var, "{}({}, {})".format(var_ids[0], var_ids[1][0], var_ids[1][1]))
                    right_exp += "    {}({}-1, {}-1) = {};".format(node.left.get_main_id(), left_subs[0], left_subs[1],
                                                               right_info.content)
                    if self.symtable[sequence].is_matrix():
                        if node.op == '=':
                            # declare
                            content += "    Eigen::MatrixXd {} = Eigen::MatrixXd::Zero({}, {});\n".format(sequence,
                                                                                                          self.symtable[
                                                                                                              sequence].rows,
                                                                                                          self.symtable[
                                                                                                              sequence].cols)
                    content += "    for( int {}=1; {}<={}; {}++){{\n".format(left_subs[0], left_subs[0],
                                                                            self.symtable[sequence].rows, left_subs[0])
                    content += "        for( int {}=1; {}<={}; {}++){{\n".format(left_subs[1], left_subs[1],
                                                                                self.symtable[sequence].cols,
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

                ele_type = self.symtable[sequence].element_type
                # definition
                if self.symtable[sequence].is_sequence():
                    right_exp += "    {} = {}".format(left_info.content, right_info.content)
                    content += "    {} {}({});\n".format(self.get_ctype(self.symtable[sequence]), sequence,
                                                         self.symtable[sequence].size)
                    content += "    for( int {}=1; {}<={}; {}++){{\n".format(left_subs[0], left_subs[0],
                                                                            self.symtable[sequence].size, left_subs[0])
                else:
                    right_exp += "    {} = {}".format(left_info.content, right_info.content)
                    content += "    {} {}({});\n".format(self.get_ctype(self.symtable[sequence]), sequence,
                                                         self.symtable[sequence].rows)
                    content += "    for( int {}=1; {}<={}; {}++){{\n".format(left_subs[0], left_subs[0],
                                                                            self.symtable[sequence].rows, left_subs[0])
                if right_info.pre_list:
                    content += self.update_prelist_str(right_info.pre_list, "    ")
                content += "    " + right_exp + ";\n"
                content += '    }\n'
        #
        else:
            if right_info.pre_list:
                content = "".join(right_info.pre_list) + content
            if type(node.right).__name__ == 'SparseMatrix':
                content = right_info.content
            else:
                op = ' = '
                if node.op == '+=':
                    op = ' += '
                type_def = ""
                if not self.def_dict[node.left.get_main_id()]:
                    type_def = self.get_ctype(self.symtable[node.left.get_main_id()]) + ' '
                    self.def_dict[node.left.get_main_id()] = True
                right_exp += '    ' + type_def + node.left.get_main_id() + op + right_info.content + ';'
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
        # ret_info.content = "if(" + ret_info.content + ")\n"
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
        if node.set.node_type != IRNodeType.Id:
            set_name = self.generate_var_name('set')
            pre_list.append('{} {} = {};\n'.format(self.get_ctype(node.set.la_type), set_name, right_info.content))
            content = '{}.find({}({})) != {}.end()'.format(set_name, self.get_set_item_str(node.set.la_type), ', '.join(item_list), set_name)
        else:
            content = '{}.find({}({})) != {}.end()'.format(right_info.content, self.get_set_item_str(node.set.la_type), ', '.join(item_list),right_info.content)
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
        content = '{}.find({}({})) == {}.end()'.format(right_info.content, self.get_set_item_str(self.symtable[right_info.content]), ', '.join(item_list),right_info.content)
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
        return CodeNodeInfo("")

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
        return CodeNodeInfo(content, pre_list=left_info.pre_list+right_info.pre_list)

    def visit_fro_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("({}).cwiseProduct({}).sum();".format(left_info.content, right_info.content), pre_list=left_info.pre_list+right_info.pre_list)

    def visit_hadamard_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("({}).cwiseProduct({})".format(left_info.content, right_info.content), pre_list=left_info.pre_list+right_info.pre_list)

    def visit_cross_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("({}).cross({})".format(left_info.content, right_info.content), pre_list=left_info.pre_list+right_info.pre_list)

    def visit_kronecker_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        index_i = self.generate_var_name('i')
        index_j = self.generate_var_name('j')
        kronecker = self.generate_var_name('kron')
        pre_list = left_info.pre_list + right_info.pre_list
        pre_list.append("    {} {};\n".format(self.get_ctype(node.la_type), kronecker))
        pre_list.append("    for( int {}=0; {}<{}; {}++){{\n".format(index_i, index_i, node.left.la_type.rows, index_i))
        pre_list.append("        for( int {}=0; {}<{}; {}++){{\n".format(index_j, index_j, node.left.la_type.cols, index_j))
        pre_list.append("            {}.block({}*{},{}*{},{},{}) = ({})({}, {})*({});\n".format(kronecker, index_i, node.left.la_type.rows, index_j, node.left.la_type.cols,
                                                                                           node.right.la_type.rows, node.right.la_type.cols,
                                                                                         left_info.content, index_i, index_j, right_info.content))
        pre_list.append("        }\n")
        pre_list.append("    }\n")
        return CodeNodeInfo(content=kronecker,pre_list=pre_list)

    def visit_dot_product(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return CodeNodeInfo("({}).dot({})".format(left_info.content, right_info.content), pre_list=left_info.pre_list+right_info.pre_list)

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
                pre_list.append('    Eigen::VectorXd {}(Eigen::Map<Eigen::VectorXd>(((Eigen::MatrixXd)({})).data(), ({}).cols()*({}).rows()));;\n'.format(vec_name,params_content,params_content,params_content))
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

    def visit_factor(self, node, **kwargs):
        if node.id:
            return self.visit(node.id, **kwargs)
        elif node.num:
            return self.visit(node.num, **kwargs)
        elif node.sub:
            return self.visit(node.sub, **kwargs)
        elif node.v:
            return self.visit(node.v, **kwargs)
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
            content = 'M_PI'
        elif node.c_type == ConstantType.ConstantE:
            content = 'M_E'
        return CodeNodeInfo(content)

    def visit_double(self, node, **kwargs):
        content = str(node.value)
        return CodeNodeInfo(content)

    def visit_integer(self, node, **kwargs):
        content = str(node.value)
        return CodeNodeInfo(content)

    ###################################################################
