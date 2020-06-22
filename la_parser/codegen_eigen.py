from la_parser.codegen import *
from la_parser.type_walker import *


class CodeGenEigen(CodeGen):
    def __init__(self):
        super().__init__()
        self.pre_str = '''#include <Eigen/Core>\n#include <Eigen/Dense>\n#include <Eigen/Sparse>\n#include <iostream>\n#include <set>\n\n'''
        self.post_str = ''''''
        self.ret = 'ret'

    def visit_id(self, node, **kwargs):
        return CodeNodeInfo(node.get_name())

    def visit_start(self, node, **kwargs):
        return self.visit(node.stat, **kwargs)

    def get_set_item_str(self, set_type):
        type_list = []
        for index in range(set_type.size):
            if set_type.int_list[index]:
                type_list.append('int')
            else:
                type_list.append('double')
        return "std::tuple< {} >".format(", ".join(type_list))

    def get_ctype(self, la_type):
        type_str = ""
        if la_type.var_type == VarTypeEnum.SEQUENCE:
            if la_type.element_type.var_type == VarTypeEnum.MATRIX:
                if la_type.element_type.sparse:
                    type_str = "std::vector<Eigen::SparseMatrix<double> >"
                else:
                    if la_type.element_type.is_dim_constant():
                        if la_type.element_type.element_type is not None and la_type.element_type.element_type.var_type == VarTypeEnum.INTEGER:
                            type_str = "std::vector<Eigen::Matrix<int, {}, {}> >".format(la_type.element_type.rows,
                                                                                         la_type.element_type.cols)
                        else:
                            type_str = "std::vector<Eigen::Matrix<double, {}, {}> >".format(la_type.element_type.rows,
                                                                                            la_type.element_type.cols)
                    else:
                        if la_type.element_type.element_type is not None and la_type.element_type.element_type.var_type == VarTypeEnum.INTEGER:
                            type_str = "std::vector<Eigen::MatrixXi>"
                        else:
                            type_str = "std::vector<Eigen::MatrixXd>"
            elif la_type.element_type.var_type == VarTypeEnum.VECTOR:
                if la_type.element_type.is_dim_constant():
                    if la_type.element_type.element_type is not None and la_type.element_type.element_type.var_type == VarTypeEnum.INTEGER:
                        type_str = "std::vector<Eigen::Matrix<int, {}, 1> >".format(la_type.element_type.rows)
                    else:
                        type_str = "std::vector<Eigen::Matrix<double, {}, 1> >".format(la_type.element_type.rows)
                else:
                    if la_type.element_type.element_type is not None and la_type.element_type.element_type.var_type == VarTypeEnum.INTEGER:
                        type_str = "std::vector<Eigen::VectorXi>"
                    else:
                        type_str = "std::vector<Eigen::VectorXd>"
            elif la_type.element_type.var_type == VarTypeEnum.SCALAR:
                type_str = "std::vector<double>"
        elif la_type.var_type == VarTypeEnum.MATRIX:
            if la_type.sparse:
                type_str = "Eigen::SparseMatrix<double>"
            else:
                if la_type.is_dim_constant():
                    if la_type.element_type is not None and la_type.element_type.var_type == VarTypeEnum.INTEGER:
                        type_str = "Eigen::Matrix<int, {}, {}>".format(la_type.rows, la_type.cols)
                    else:
                        type_str = "Eigen::Matrix<double, {}, {}>".format(la_type.rows, la_type.cols)
                else:
                    if la_type.element_type is not None and la_type.element_type.var_type == VarTypeEnum.INTEGER:
                        type_str = "Eigen::MatrixXi"
                    else:
                        type_str = "Eigen::MatrixXd"
        elif la_type.var_type == VarTypeEnum.VECTOR:
            if la_type.is_dim_constant():
                if la_type.element_type is not None and la_type.element_type.var_type == VarTypeEnum.INTEGER:
                    type_str = "Eigen::Matrix<int, {}, 1>".format(la_type.rows)
                else:
                    type_str = "Eigen::Matrix<double, {}, 1>".format(la_type.rows)
            else:
                if la_type.element_type is not None and la_type.element_type.var_type == VarTypeEnum.INTEGER:
                    type_str = "Eigen::VectorXi"
                else:
                    type_str = "Eigen::VectorXd"
        elif la_type.var_type == VarTypeEnum.SCALAR:
            type_str = "double"
        elif la_type.var_type == VarTypeEnum.SET:
            type_str = "std::set<{} >".format(self.get_set_item_str(la_type))
        elif la_type.var_type == VarTypeEnum.FUNCTION:
            param_list = []
            for param in la_type.params:
                param_list.append(self.get_ctype(param))
            type_str = "std::function<{}({})>".format(self.get_ctype(la_type.ret), ', '.join(param_list))
        return type_str

    def visit_block(self, node, **kwargs):
        type_checks = []
        doc = []
        show_doc = False
        func_name = "myExpression"
        rand_func_name = "generateRandomData"
        test_content = ['{']
        rand_int_max = 10
        # main
        main_declaration = []
        main_print = []
        main_content = ["int main(int argc, char *argv[])",
                        "{"]
        dim_content = ""
        if self.dim_dict:
            for key, value in self.dim_dict.items():
                test_content.append("    const int {} = rand()%{};".format(key, rand_int_max))
                if self.symtable[value[0]].var_type == VarTypeEnum.SEQUENCE:
                    dim_content += "    const long {} = {}.size();\n".format(key, value[0])
                elif self.symtable[value[0]].var_type == VarTypeEnum.MATRIX:
                    if value[1] == 0:
                        dim_content += "    const long {} = {}.rows();\n".format(key, value[0])
                    else:
                        dim_content += "    const long {} = {}.cols();\n".format(key, value[0])
                elif self.symtable[value[0]].var_type == VarTypeEnum.VECTOR:
                    dim_content += "    const long {} = {}.size();\n".format(key, value[0])
        par_des_list = []
        test_par_list = []
        for parameter in self.parameters:
            main_declaration.append("    {} {};".format(self.get_ctype(self.symtable[parameter]), parameter))
            par_des_list.append("const {} & {}".format(self.get_ctype(self.symtable[parameter]), parameter))
            test_par_list.append("{} & {}".format(self.get_ctype(self.symtable[parameter]), parameter))
            if self.symtable[parameter].desc:
                show_doc = True
                doc.append('@param {} {}'.format(parameter, self.symtable[parameter].desc))
            if self.symtable[parameter].var_type == VarTypeEnum.SEQUENCE:
                ele_type = self.symtable[parameter].element_type
                data_type = ele_type.element_type
                integer_type = False
                test_content.append('    {}.resize({});'.format(parameter, self.symtable[parameter].size))
                test_content.append('    for(int i=0; i<{}; i++){{'.format(self.symtable[parameter].size))
                if isinstance(data_type, LaVarType):
                    if data_type.var_type == VarTypeEnum.INTEGER:
                        integer_type = True
                if ele_type.var_type == VarTypeEnum.MATRIX:
                    type_checks.append(
                        '    assert( {}.size() == {} );'.format(parameter, self.symtable[parameter].size))
                    if not ele_type.is_dim_constant():
                        type_checks.append('    for( const auto& el : {} ) {{'.format(parameter))
                        type_checks.append('        assert( el.rows() == {} );'.format(ele_type.rows))
                        type_checks.append('        assert( el.cols() == {} );'.format(ele_type.cols))
                        type_checks.append('    }')
                    if integer_type:
                        test_content.append(
                            '        {}[i] = Eigen::MatrixXi::Random({}, {});'.format(parameter, ele_type.rows,
                                                                                      ele_type.cols))
                    else:
                        test_content.append(
                            '        {}[i] = Eigen::MatrixXd::Random({}, {});'.format(parameter, ele_type.rows,
                                                                                      ele_type.cols))
                elif ele_type.var_type == VarTypeEnum.VECTOR:
                    if not ele_type.is_dim_constant():
                        type_checks.append(
                            '    assert( {}.size() == {} );'.format(parameter, self.symtable[parameter].size))
                        type_checks.append('    for( const auto& el : {} ) {{'.format(parameter))
                        type_checks.append('        assert( el.size() == {} );'.format(ele_type.rows))
                        type_checks.append('    }')
                    if integer_type:
                        test_content.append(
                            '        {}[i] = Eigen::VectorXi::Random({});'.format(parameter, ele_type.rows))
                    else:
                        test_content.append(
                            '        {}[i] = Eigen::VectorXd::Random({});'.format(parameter, ele_type.rows))
                elif ele_type.var_type == VarTypeEnum.SCALAR:
                    type_checks.append(
                        '    assert( {}.size() == {} );'.format(parameter, self.symtable[parameter].size))
                test_content.append('    }')
            elif self.symtable[parameter].var_type == VarTypeEnum.MATRIX:
                element_type = self.symtable[parameter].element_type
                if isinstance(element_type, LaVarType):
                    if element_type.var_type == VarTypeEnum.INTEGER:
                        test_content.append(
                            '    {} = Eigen::MatrixXi::Random({}, {});'.format(parameter, self.symtable[parameter].rows,
                                                                               self.symtable[parameter].cols))
                    elif element_type.var_type == VarTypeEnum.REAL:
                        test_content.append(
                            '    {} = Eigen::MatrixXd::Random({}, {});'.format(parameter, self.symtable[parameter].rows,
                                                                               self.symtable[parameter].cols))
                else:
                    test_content.append(
                        '    {} = Eigen::MatrixXd::Random({}, {});'.format(parameter, self.symtable[parameter].rows,
                                                                           self.symtable[parameter].cols))
                if not self.symtable[parameter].is_dim_constant():
                    type_checks.append(
                        '    assert( {}.rows() == {} );'.format(parameter, self.symtable[parameter].rows))
                    type_checks.append(
                        '    assert( {}.cols() == {} );'.format(parameter, self.symtable[parameter].cols))
            elif self.symtable[parameter].var_type == VarTypeEnum.VECTOR:
                element_type = self.symtable[parameter].element_type
                if isinstance(element_type, LaVarType):
                    if element_type.var_type == VarTypeEnum.INTEGER:
                        test_content.append(
                            '    {} = Eigen::VectorXi::Random({});'.format(parameter, self.symtable[parameter].rows))
                    elif element_type.var_type == VarTypeEnum.REAL:
                        test_content.append(
                            '    {} = Eigen::VectorXd::Random({});'.format(parameter, self.symtable[parameter].rows))
                else:
                    test_content.append(
                        '    {} = Eigen::VectorXd::Random({});'.format(parameter, self.symtable[parameter].rows))
                if not self.symtable[parameter].is_dim_constant():
                    type_checks.append(
                        '    assert( {}.size() == {} );'.format(parameter, self.symtable[parameter].rows))
            elif self.symtable[parameter].var_type == VarTypeEnum.SCALAR:
                test_content.append('    {} = rand() % {};'.format(parameter, rand_int_max))
            elif self.symtable[parameter].var_type == VarTypeEnum.SET:
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

            # main_print.append('    std::cout<<"{}:\\n"<<{}<<std::endl;'.format(parameter, parameter))
        content = ""
        if show_doc:
            content += '/**\n * ' + func_name + '\n *\n * ' + '\n * '.join(doc) + '\n * @return {}\n */\n'.format(
                self.ret_symbol)
        ret_type = self.get_ctype(self.symtable[self.ret_symbol])
        if len(self.parameters) == 1:
            content += ret_type + ' ' + func_name + '(' + ', '.join(par_des_list) + ')\n{\n'  # func name
            test_content.insert(0, "void {}({})".format(rand_func_name, ', '.join(test_par_list)))
        else:
            content += ret_type + ' ' + func_name + '(\n    ' + ',\n    '.join(par_des_list) + ')\n{\n'  # func name
            test_content.insert(0, "void {}({})".format(rand_func_name, ',\n    '.join(test_par_list)))
        # merge content
        # content += '\n'.join(type_declare) + '\n\n'
        content += dim_content
        content += '\n'.join(type_checks) + '\n\n'
        # statements
        stats_content = ""
        for index in range(len(node.stmts)):
            ret_str = ''
            need_semicolon = False
            if index == len(node.stmts) - 1:
                if type(node.stmts[index]).__name__ != 'AssignNode':
                    kwargs[LHS] = self.ret_symbol
                    ret_str = "    " + ret_type + " " + self.ret_symbol + ' = '
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
        content += '    return ' + self.ret_symbol + ';'
        content += '\n}\n'
        # convert special string in identifiers
        content = self.trim_content(content)
        # test
        # test_content.append('    return {}'.format(', '.join(self.parameters)))
        test_content.append('}')
        # main
        main_content += main_declaration
        main_content.append("    {}({});".format(rand_func_name, ', '.join(self.parameters)))
        main_content += main_print
        main_content.append(
            "    {} func_value = {}({});".format(self.get_ctype(self.symtable[self.ret_symbol]), func_name,
                                                 ', '.join(self.parameters)))
        if self.symtable[self.ret_symbol].is_matrix():
            main_content.append('    std::cout<<"func_value:\\n"<<func_value<<std::endl;')
        main_content.append('    return 0;')
        main_content.append('}')
        content += '\n\n' + '\n'.join(test_content) + '\n\n\n' + '\n'.join(main_content)
        return content

    def visit_WhereConditions(self, node, **kwargs):
        pass

    def visit_expression(self, node, **kwargs):
        exp_info = self.visit(node.value, **kwargs)
        if node.sign:
            exp_info.content = '-' + exp_info.content
        return exp_info

    def visit_summation(self, node, **kwargs):
        type_info = node
        assign_id = type_info.symbol
        cond_content = ""
        if node.cond:
            if LHS in kwargs:
                lhs = kwargs[LHS]
                if self.contain_subscript(lhs):
                    lhs_ids = self.get_all_ids(lhs)
                    assert lhs_ids[1][0] == lhs_ids[1][1], "multiple subscripts for sum"
                    sub = type_info.content
                    cond_info = self.visit(node.cond, **kwargs)
                    cond_content = "if(" + cond_info.content + ")\n"
        else:
            sub_info = self.visit(node.sub)
            sub = sub_info.content
        vars = type_info.symbols
        kwargs[WALK_TYPE] = WalkTypeEnum.RETRIEVE_EXPRESSION
        content = []
        target_var = []
        exp_info = self.visit(node.exp)
        exp_str = exp_info.content
        for var in vars:
            if self.contain_subscript(var):
                var_ids = self.get_all_ids(var)
                var_subs = var_ids[1]
                for var_sub in var_subs:
                    if sub == var_sub:
                        target_var.append(var_ids[0])
        if self.symtable[assign_id].var_type == VarTypeEnum.MATRIX:
            content.append(
                "Eigen::MatrixXd {} = Eigen::MatrixXd::Zero({}, {});\n".format(assign_id, self.symtable[assign_id].rows,
                                                                               self.symtable[assign_id].cols))
        elif self.symtable[assign_id].var_type == VarTypeEnum.VECTOR:
            content.append(
                "Eigen::MatrixXd {} = Eigen::MatrixXd::Zero({}, 1);\n".format(assign_id, self.symtable[assign_id].rows))
        elif self.symtable[assign_id].var_type == VarTypeEnum.SEQUENCE:
            ele_type = self.symtable[assign_id].element_type
            content.append(
                "Eigen::MatrixXd {} = np.zeros(({}, {}, {}))\n".format(assign_id, self.symtable[assign_id].size,
                                                                       ele_type.rows, ele_type.cols))
        else:
            content.append("double {} = 0;\n".format(assign_id))
        if self.symtable[target_var[0]].var_type == VarTypeEnum.MATRIX:  # todo
            content.append("for(int {}=0; {}<{}.rows(); {}++){{\n".format(sub, sub, target_var[0], sub))
        else:
            content.append("for(int {}=0; {}<{}.size(); {}++){{\n".format(sub, sub, target_var[0], sub))
        if node.cond:
            for right_var in type_info.symbols:
                if self.contain_subscript(right_var):
                    var_ids = self.get_all_ids(right_var)
                    exp_str = exp_str.replace(right_var, "{}({}, {})".format(var_ids[0], var_ids[1][0], var_ids[1][1]))
                    if exp_info.pre_list:
                        for index in range(len(exp_info.pre_list)):
                            exp_info.pre_list[index] = exp_info.pre_list[index].replace(old, new)
        else:
            for var in target_var:
                old = "{}_{}".format(var, sub)
                new = "{}[{}]".format(var, sub)
                exp_str = exp_str.replace(old, new)
                if exp_info.pre_list:
                    for index in range(len(exp_info.pre_list)):
                        exp_info.pre_list[index] = exp_info.pre_list[index].replace(old, new)
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
        else:
            content.append(str("    " + assign_id + " += " + exp_str + ';\n'))
        content[0] = "    " + content[0]

        content.append("}\n")
        return CodeNodeInfo(assign_id, pre_list=["    ".join(content)])

    def visit_determinant(self, node, **kwargs):
        value_info = self.visit(node.value)
        value = value_info.content
        type_info = self.node_dict[node.value]
        if type_info.la_type.var_type == VarTypeEnum.VECTOR or type_info.la_type.var_type == VarTypeEnum.MATRIX or type_info.la_type.var_type == VarTypeEnum.SEQUENCE:
            if value in self.parameters:
                value_type = self.symtable[value]
                if type_info.la_type.var_type == VarTypeEnum.SEQUENCE:
                    dim = value_type.size
                else:
                    dim = value_type.rows
                return CodeNodeInfo(str(dim))
            elif value in self.symtable:
                return CodeNodeInfo(value + '.shape[0]')
            return CodeNodeInfo('(' + value + ').shape[0]')
        return CodeNodeInfo('np.absolute(' + value + ')')

    def visit_transpose(self, node, **kwargs):
        f_info = self.visit(node.f, **kwargs)
        f_info.content = "{}.transpose()".format(f_info.content)
        return f_info

    def visit_power(self, node, **kwargs):
        base_info = self.visit(node.base, **kwargs)
        if node.t:
            base_info.content = "{}.transpose()".format(base_info.content)
        elif node.r:
            base_info.content = "{}.inverse()".format(base_info.content)
        else:
            power_info = self.visit(node.power, **kwargs)
            base_info.content = base_info.content + '^' + power_info.content
        return base_info

    def visit_solver(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = "{}.colPivHouseholderQr().solve({});".format(left_info.content, right_info.content)
        return left_info

    def visit_sparse_matrix(self, node, **kwargs):
        lhs = kwargs[LHS]
        type_info = node
        cur_m_id = type_info.symbol
        pre_list = []
        if_info = self.visit(node.ifs, **kwargs)
        pre_list += if_info.content
        pre_list.append(
            '    {}.setFromTriplets(tripletList_{}.begin(), tripletList_{}.end());\n'.format(self.get_main_id(lhs),
                                                                                             self.get_main_id(lhs),
                                                                                             self.get_main_id(lhs)))
        return CodeNodeInfo(cur_m_id, pre_list)

    def visit_sparse_ifs(self, node, **kwargs):
        assign_node = node.get_ancestor(IRNodeType.Assignment)
        sparse_node = node.get_ancestor(IRNodeType.SparseMatrix)
        subs = assign_node.left.subs
        ret = ["    for( int {}=0; {}<{}; {}++){{\n".format(subs[0], subs[0], sparse_node.la_type.rows, subs[0]),
               "        for( int {}=0; {}<{}; {}++){{\n".format(subs[1], subs[1], sparse_node.la_type.cols, subs[1])]
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
        # replace '_ij' with '(i,j)'
        # stat_content = stat_content.replace('_{}{}'.format(id0, id1), '({}, {})'.format(id0, id1))
        # content = []
        # content.append('    for (auto& tuple : {}) {{\n'.format(id2))
        # content.append('        double {} = std::get<0>(tuple);\n'.format(id0))
        # content.append('        double {} = std::get<1>(tuple);\n'.format(id1))
        # content.append(
        #     '        tripletList_{}.push_back(Eigen::Triplet<double>({}, {}, {}));\n'.format(self.get_main_id(lhs), id0,
        #                                                                                      id1, stat_content))
        # content.append('    }\n')
        assign_node = node.get_ancestor(IRNodeType.Assignment)
        subs = assign_node.left.subs
        cond_info = self.visit(node.cond, **kwargs)
        stat_info = self.visit(node.stat, **kwargs)
        content = []
        stat_content = stat_info.content
        # replace '_ij' with '(i,j)'
        stat_content = stat_content.replace('_{}{}'.format(subs[0], subs[1]), '({}, {})'.format(subs[0], subs[1]))
        content.append('if({}){{\n'.format(cond_info.content))
        content.append('    tripletList_{}.push_back(Eigen::Triplet<double>({}, {}, {}));\n'.format(assign_node.left.get_main_id(), subs[0], subs[1], stat_content))
        content.append('}\n')
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
        # preprocess
        if type_info.la_type.list_dim:
            for i in range(len(ret)):
                for j in range(len(ret[i])):
                    if (i, j) in type_info.la_type.list_dim:
                        dims = type_info.la_type.list_dim[(i, j)]
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
            all_rows = []
            m_content = ""
            sparse_index = []
            sparse_exp = []
            row_index = 0

            # convert to sparse matrix
            sparse_id = "{}".format(cur_m_id)
            sparse_triplet = "tripletList{}".format(cur_m_id)
            for i in range(len(ret)):
                col_index = 0
                for j in range(len(ret[i])):
                    sparse_index.append((row_index, col_index))
                    if type_info.la_type.item_types[i][j].is_matrix() and type_info.la_type.item_types[i][j].sparse:
                        sparse_exp.append(ret[i][j])
                    else:
                        sparse_exp.append('{}.sparseView()'.format(ret[i][j]))
                    col_index += type_info.la_type.item_types[i][j].cols
                row_index += type_info.la_type.item_types[i][j].rows
                all_rows.append(', '.join(ret[i]))
            content += 'Eigen::SparseMatrix<double> {}({}, {});\n'.format(cur_m_id, self.symtable[cur_m_id].rows, self.symtable[cur_m_id].cols)
            content += '    std::vector<Eigen::Triplet<double> > {};\n'.format(sparse_triplet)
            # add all elements
            for index in range(len(sparse_index)):
                (i, j) = sparse_index[index]
                if index == 0:
                    content += '    Eigen::SparseMatrix<double> tmp = {};\n'.format(sparse_exp[index])
                else:
                    content += '    tmp = {};\n'.format(sparse_exp[index])
                content += '    for (int k=0; k < tmp.outerSize(); ++k){\n'
                content += '        for (Eigen::SparseMatrix<double>::InnerIterator it(tmp,k); it; ++it){\n'
                row_str = ''
                if i > 0:
                    row_str = "+{}".format(i)
                col_str = ''
                if j > 0:
                    col_str = "+{}".format(j)
                content += '            {}.push_back(Eigen::Triplet<double>((int)it.row(){}, (int)it.col(){}, it.value()));\n'.format(
                    sparse_triplet, row_str, col_str)
                content += '        }\n'
                content += '    }\n'
            # set triplets
            content += '    {}.setFromTriplets({}.begin(), {}.end());\n'.format(sparse_id, sparse_triplet,
                                                                                sparse_triplet)
            cur_m_id = sparse_id
        else:
            # dense
            content += 'Eigen::Matrix<double, {}, {}> {};\n'.format(self.symtable[cur_m_id].rows,
                                                                    self.symtable[cur_m_id].cols, cur_m_id)
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
            elif node.left == '1':
                func_name = "Eigen::MatrixXd::Ones"
            else:
                func_name = "({} * Eigen::MatrixXd::Ones".format(left_info.content)
                post_s = ')'
        id1_info = self.visit(node.id1, **kwargs)
        if node.id2:
            id2_info = self.visit(node.id2, **kwargs)
            content = "{}({}, {})".format(func_name, id1_info.content, id2_info.content)
        else:
            content = "{}({}, {})".format(func_name, id1_info.content, id1_info.content)
        node_info = CodeNodeInfo(content + post_s)
        return node_info

    def visit_add(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = left_info.content + ' + ' + right_info.content
        left_info.pre_list = self.merge_pre_list(left_info, right_info)
        return left_info

    def visit_sub(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = left_info.content + ' - ' + right_info.content
        left_info.pre_list = self.merge_pre_list(left_info, right_info)
        return left_info

    def visit_add_sub(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = left_info.content + ' +- ' + right_info.content
        left_info.pre_list = self.merge_pre_list(left_info, right_info)
        return left_info

    def visit_mul(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        l_info = node.left
        r_info = node.right
        mul = ' * '
        # if l_info.la_type.var_type == VarTypeEnum.MATRIX or l_info.la_type.var_type == VarTypeEnum.VECTOR:
        #     if r_info.la_type.var_type == VarTypeEnum.MATRIX or r_info.la_type.var_type == VarTypeEnum.VECTOR:
        #         mul = ' @ '
        left_info.content = left_info.content + mul + right_info.content
        left_info.pre_list = self.merge_pre_list(left_info, right_info)
        return left_info

    def visit_div(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = left_info.content + ' / ' + right_info.content
        left_info.pre_list = self.merge_pre_list(left_info, right_info)
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
            if len(left_subs) == 2:  # matrix only
                sequence = left_ids[0]  # y left_subs[0]
                sub_strs = left_subs[0] + left_subs[1]
                if self.symtable[sequence].var_type == VarTypeEnum.MATRIX and self.symtable[sequence].sparse:
                    # sparse mat assign
                    # right_exp += '    ' + sequence + ' = ' + right_info.content
                    # content += right_info.content
                    def_str = ""
                    if node.op != '+=':
                        def_str = "    Eigen::SparseMatrix<double> {}({}, {});\n".format(self.get_main_id(left_id),
                                                                                         self.symtable[self.get_main_id(
                                                                                             left_id)].rows,
                                                                                         self.symtable[self.get_main_id(
                                                                                             left_id)].cols)
                        def_str += '    std::vector<Eigen::Triplet<double> > tripletList_{};\n'.format(
                            self.get_main_id(left_id))
                    content = def_str + content
                    pass
                elif left_subs[0] == left_subs[1]:
                    # L_ii
                    content = ""
                    content += "    for( int {}=0; {}<{}; {}++){{\n".format(left_subs[0], left_subs[0],
                                                                            self.symtable[sequence].rows, left_subs[0])
                    if right_info.pre_list:
                        for list in right_info.pre_list:
                            lines = list.split('\n')
                            content += "    " + "\n    ".join(lines)
                    content += "    {}({}, {}) = {};\n".format(sequence, left_subs[0], left_subs[0], right_info.content)
                    content += "    }"
                else:
                    for right_var in type_info.symbols:
                        if sub_strs in right_var:
                            var_ids = self.get_all_ids(right_var)
                            right_info.content = right_info.content.replace(right_var, "{}({}, {})".format(var_ids[0], var_ids[1][0], var_ids[1][1]))
                    right_exp += "    {}({}, {}) = {};".format(self.get_main_id(left_id), left_subs[0], left_subs[1],
                                                               right_info.content)
                    if self.symtable[sequence].var_type == VarTypeEnum.MATRIX:
                        if node.op == '=':
                            # declare
                            content += "    Eigen::MatrixXd {} = Eigen::MatrixXd::Zero({}, {});\n".format(sequence,
                                                                                                          self.symtable[
                                                                                                              sequence].rows,
                                                                                                          self.symtable[
                                                                                                              sequence].cols)
                    content += "    for( int {}=0; {}<{}; {}++){{\n".format(left_subs[0], left_subs[0],
                                                                            self.symtable[sequence].rows, left_subs[0])
                    content += "        for( int {}=0; {}<{}; {}++){{\n".format(left_subs[1], left_subs[1],
                                                                                self.symtable[sequence].cols,
                                                                                left_subs[1])
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
                                                                        "{}[{}]".format(var_ids[0], var_ids[1][0]))

                right_exp += "    {}[{}] = {}".format(self.get_main_id(left_id), left_subs[0], right_info.content)
                ele_type = self.symtable[sequence].element_type
                if ele_type.var_type == VarTypeEnum.MATRIX:
                    content += "    {} {}({});\n".format(self.get_ctype(self.symtable[sequence]), sequence,
                                                         self.symtable[sequence].size)
                elif ele_type.var_type == VarTypeEnum.VECTOR:
                    content += "    Eigen::MatrixXd {} = Eigen::MatrixXd::Zero({}, {})\n".format(sequence,
                                                                                                 self.symtable[
                                                                                                     sequence].size,
                                                                                                 ele_type.rows)
                else:
                    content += "    {} = np.zeros({})\n".format(sequence, self.symtable[sequence].size)
                content += "    for( int {}=0; {}<{}; {}++){{\n".format(left_subs[0], left_subs[0],
                                                                        self.symtable[sequence].size, left_subs[0])
                content += "    " + right_exp + ";\n"
                content += '    }\n'
        #
        else:
            if type(node.right).__name__ == 'SparseMatrix':
                content = right_info.content
            else:
                op = ' = '
                if node.op == '+=':
                    op = ' += '
                type_def = ""
                if not self.def_dict[self.get_main_id(left_id)]:
                    type_def = self.get_ctype(self.symtable[self.get_main_id(left_id)]) + ' '
                    self.def_dict[self.get_main_id(left_id)] = True
                right_exp += '    ' + type_def + self.get_main_id(left_id) + op + right_info.content + ';'
                content += right_exp
        content += '\n'
        la_remove_key(LHS, **kwargs)
        return CodeNodeInfo(content)

    def visit_function(self, node, **kwargs):
        name_info = self.visit(node.name, **kwargs)
        params = []
        if node.params:
            for param in node.params:
                params.append(self.visit(param, **kwargs).content)
        content = "{}({})".format(name_info.content, ', '.join(params))
        return CodeNodeInfo(content)

    def visit_if(self, node, **kwargs):
        ret_info = self.visit(node.cond)
        # ret_info.content = "if(" + ret_info.content + ")\n"
        return ret_info

    def visit_in(self, node, **kwargs):
        item_list = []
        pre_list = []
        for item in node.items:
            item_info = self.visit(item, **kwargs)
            item_list.append(item_info.content)
            # pre_list = self.merge_pre_list(pre_list, item_info)
        right_info = self.visit(node.set, **kwargs)
        content = '{}.find({}({})) != {}.end()'.format(right_info.content, self.get_set_item_str(self.symtable[right_info.content]), ', '.join(item_list),right_info.content)
        # pre_list = self.merge_pre_list(pre_list, right_info)
        return CodeNodeInfo(content=content, pre_list=pre_list)

    def visit_not_in(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = left_info.content + 'not in' + right_info.content
        left_info.pre_list = self.merge_pre_list(left_info, right_info)
        return left_info

    def visit_bin_comp(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = left_info.content + ' {} '.format(self.get_bin_comp_str(node.comp_type)) + right_info.content
        left_info.pre_list = self.merge_pre_list(left_info, right_info)
        return left_info

    def visit_IdentifierAlone(self, node, **kwargs):
        if node.value:
            value = node.value
        else:
            value = '`' + node.id + '`'
        return CodeNodeInfo(value)

    def visit_derivative(self, node, **kwargs):
        return CodeNodeInfo("")

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

    def visit_number(self, node, **kwargs):
        return self.visit(node.value, **kwargs)

    def visit_integer(self, node, **kwargs):
        content = str(node.value)
        return CodeNodeInfo(content)

    ###################################################################
    def merge_pre_list(self, left_info, right_info):
        ret = left_info.pre_list
        if right_info.pre_list is not None:
            if ret is None:
                ret = right_info.pre_list
            else:
                ret = ret + right_info.pre_list
        return ret

    def is_keyword(self, name):
        kwlist = u"Asm auto bool break case catch char class const_cast	continue default delete	do double else " \
                 u"enum	dynamic_cast extern	false float for	union unsigned using friend goto if	" \
                 u"inline int long mutable virtual namespace new operator private protected	public " \
                 u"register	void reinterpret_cast return short signed sizeof static	static_cast	volatile " \
                 u"struct switch template this throw true try typedef typeid unsigned wchar_t while "
        keywords = kwlist.split(' ')
        return name in keywords
