from .de_ir_printer import *
import copy


class DCodeGen(DIRPrinter):
    def __init__(self, parse_type=None):
        super().__init__(parse_type=parse_type)

    def init_type(self, type_walker):
        super().init_type(type_walker)

    def visit_start(self, node, **kwargs):
        content = ''
        for vblock in node.vblock:
            content += self.visit(vblock, **kwargs).content
        # self.visit(node.stat, **kwargs)
        return CodeNodeInfo(content)

    def visit_block(self, node, **kwargs):
        ret = []
        pre_list = []
        for stmt in node.stmts:
            stmt_info = self.visit(stmt, **kwargs)
            ret.append(stmt_info.content)
            pre_list += stmt_info.pre_list
        return CodeNodeInfo('\n'.join(ret), pre_list)

    def visit_where_conditions(self, node, **kwargs):
        ret = []
        for val in node.value:
            ret.append(self.visit(val, **kwargs).content + " \\n")
        return CodeNodeInfo(''.join(ret))

    def visit_where_condition(self, node, **kwargs):
        id_list = [self.visit(id0, **kwargs) for id0 in node.id]
        type_content = self.visit(node.type, **kwargs)
        if node.belong:
            belong = node.belong
        else:
            belong = "\\in"
        if node.type.is_node(IRNodeType.MappingType):
            if node.type.subset:
                belong = "\\subset"
        content = "{} & {} {}".format(','.join(id_list), belong, type_content)
        if node.attrib:
            content += " ,\\text{{ {}}}".format(node.attrib)
        if node.desc:
            content += " \\text{{ {}}}".format(node.desc)
        return CodeNodeInfo(content)

    def visit_assignment(self, node, **kwargs):
        content = ''
        lhs_list = []
        for cur_index in range(len(node.left)):
            lhs_list.append(self.visit(node.left[cur_index], **kwargs).content)
        if node.right[0].node_type == IRNodeType.Optimize:
            content = self.visit(node.right[0], **kwargs).content
        else:
            rhs_list = []
            for cur_index in range(len(node.right)):
                rhs_list.append(self.visit(node.right[cur_index], **kwargs).content)
            content = ','.join(lhs_list) + " = " + ','.join(rhs_list)
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

    def visit_sub_expr(self, node, **kwargs):
        value_info = self.visit(node.value, **kwargs)
        value_info.content = '(' + value_info.content + ')'
        return value_info

    def visit_expression(self, node, **kwargs):
        exp_info = self.visit(node.value, **kwargs)
        if node.sign:
            exp_info.content = '-' + exp_info.content
        return exp_info

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

    def visit_matrix(self, node, **kwargs):
        res = self.visit(node.value, **kwargs)
        res.content = "[{}]".format(res.content)
        return res

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
        return CodeNodeInfo('\n'.join(ret), pre_list)

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
        return CodeNodeInfo(', '.join(ret), pre_list)

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

    def get_func_prefix(self):
        return ''
    def get_builtin_func_name(self, name):
        res = name
        for key, module_data in self.builtin_module_dict.items():
            if key in CLASS_PACKAGES:
                if key == MESH_HELPER:
                    if name in module_data.inverse_dict:
                        res = module_data.inverse_dict[name]
        return res

    def convert_overloaded_name(self, name):
        # mapp builtin func names to the different backends
        cur_dict = BACKEND_OVERLOADING_DICT[self.parse_type]
        if name in cur_dict:
            return cur_dict[name]
        return name
    
    def get_mesh_str(self, mesh):
        # prepend self. if necessary
        return mesh

    def visit_gp_func(self, node, **kwargs):
        params_content_list = []
        pre_list = []
        for param in node.params:
            param_info = self.visit(param, **kwargs)
            pre_list += param_info.pre_list
            params_content_list.append(param_info.content)
        content = node.identity_name
        content = self.convert_overloaded_name(content)
        # content = "{}.{}({})".format(self.get_func_prefix(), self.get_builtin_func_name(content), ', '.join(params_content_list))
        if node.params[0].la_type.is_mesh():
            # if the first param is a mesh
            content = "{}.{}({})".format(self.get_mesh_str(params_content_list[0]), self.get_builtin_func_name(content), ', '.join(params_content_list[1:]))
        else:
            if node.func_type == GPType.NonZeros:
                content = "{}({})".format(self.get_builtin_func_name(content), ', '.join(params_content_list))
            elif node.func_type == GPType.IndicatorVector:
                indicator_dim_dict = {
                    VERTICES_TO_VECTOR: 'n_vertices()',
                    EDGES_TO_VECTOR: 'n_edges()',
                    FACES_TO_VECTOR: 'n_faces()',
                    TETS_TO_VECTOR: 'n_tets()'
                }
                content = "indicator({}, {}.{})".format(', '.join(params_content_list), self.get_mesh_str(node.params[0].la_type.owner), indicator_dim_dict[self.get_builtin_func_name(content)])
            else:
                # mesh is still necessary
                content = "{}.{}({})".format(self.get_mesh_str(node.params[0].la_type.owner), self.get_builtin_func_name(content), ', '.join(params_content_list))
        return CodeNodeInfo(content, pre_list=pre_list)

    def visit_IdentifierAlone(self, node, **kwargs):
        if node.value:
            value = node.value
        else:
            value = '`' + node.id + '`'
        return CodeNodeInfo(value)

    def visit_id(self, node, **kwargs):
        content = node.raw_text
        return CodeNodeInfo(content)