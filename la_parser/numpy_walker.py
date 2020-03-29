from la_parser.base_walker import *


class NumpyWalker(BaseNodeWalker):
    def __init__(self):
        super().__init__()
        self.pre_str = '''import numpy as np\n\n\n'''
        self.post_str = ''''''
        self.ret = 'ret'

    def walk_Start(self, node, **kwargs):
        pars = []
        type_checks = []
        show_doc = False
        doc = []
        for parameter in self.parameters:
            par = parameter
            if self.symtable[parameter].desc:
                show_doc = True
                doc.append('    :param :{} :{}'.format(parameter, self.symtable[parameter].desc))
            if self.symtable[parameter].var_type == VarTypeEnum.SEQUENCE:
                ele_type = self.symtable[parameter].element_type
                type_checks.append('    assert isinstance({}, np.ndarray)'.format(parameter))
                type_checks.append('    dim = {}.shape'.format(parameter))
                if ele_type.var_type == VarTypeEnum.MATRIX:
                    type_checks.append('    assert len(dim) == 3')
                    type_checks.append('    assert dim[1] == {}'.format(ele_type.dimensions[0]))
                    type_checks.append('    assert dim[2] == {}'.format(ele_type.dimensions[1]))
                elif ele_type.var_type == VarTypeEnum.VECTOR:
                    type_checks.append('    assert len(dim) == 2')
                    type_checks.append('    assert dim[1] == {}'.format(ele_type.dimensions[0]))
                elif ele_type.var_type == VarTypeEnum.SCALAR:
                    type_checks.append('    assert len(dim) == 1')
            elif self.symtable[parameter].var_type == VarTypeEnum.MATRIX:
                type_checks.append('    assert isinstance({}, np.ndarray)'.format(parameter))
                type_checks.append('    dim = {}.shape'.format(parameter))
                type_checks.append('    assert len(dim) == 2')
                type_checks.append('    assert dim[0] == {}'.format(self.symtable[parameter].dimensions[0]))
                type_checks.append('    assert dim[1] == {}'.format(self.symtable[parameter].dimensions[1]))
            elif self.symtable[parameter].var_type == VarTypeEnum.VECTOR:
                type_checks.append('    assert isinstance({}, np.ndarray)'.format(parameter))
                type_checks.append('    dim = {}.shape'.format(parameter))
                type_checks.append('    assert len(dim) == 1')
                type_checks.append('    assert dim[0] == {}'.format(self.symtable[parameter].dimensions[0]))
            elif self.symtable[parameter].var_type == VarTypeEnum.SCALAR:
                pass
            pars.append(par)
        content = 'def myExpression(' + ', '.join(pars) + '):\n'
        if show_doc:
            content += '    \"\"\"\n' + '\n'.join(doc) + '\n    \"\"\"\n'
        content += '\n'.join(type_checks) + '\n\n'
        content += self.walk(node.stat)
        content += '    return ' + self.ret
        content += '\n'
        return content

    def walk_WhereConditions(self, node, **kwargs):
        pass

    def walk_Statements(self, node, **kwargs):
        index = 0
        content = ''
        for stat in node.value:
            if type(stat).__name__ == 'Statements':
                content += self.walk(stat, **kwargs)
            else:
                content += '    '
                if index == len(node.value) - 1:
                    if type(stat).__name__ != 'Assignment':
                        self.ret = 'ret'
                        content += self.ret + ' = '
                content += self.walk(stat, **kwargs) + '\n'
            index += 1
        return content

    def walk_Summation(self, node, **kwargs):
        if la_need_ret_vars(**kwargs):
            return {self.walk(node.exp, **kwargs)}
        subs = []
        for sub in node.sub:
            subs.append(self.walk(sub))
        kwargs[WALK_TYPE] = WalkTypeEnum.RETRIEVE_VAR
        vars = self.walk(node.exp, **kwargs)
        kwargs[WALK_TYPE] = WalkTypeEnum.RETRIEVE_EXPRESSION
        content = ""
        target_var = ''
        for sub in subs:
            for var in vars:
                same_sub = False
                if self.contain_subscript(var):
                    var_ids = self.get_all_ids(var)
                    var_subs = var_ids[1]
                    for var_sub in var_subs:
                        if sub == var_sub:
                            same_sub = True
                            target_var = var_ids[0]
                            break
                    if same_sub:
                        break
            #only one sub for now
            # content += "    for {} in range(len({})):\n".format(sub, target_var)
            content = self.walk(node.exp)
        return content

    def walk_Determinant(self, node, **kwargs):
        if la_need_ret_vars(**kwargs):
            return self.walk(node.value, **kwargs)
        value = self.walk(node.value)
        return '|' + value + '|'

    def walk_Matrix(self, node, **kwargs):
        content = ""
        lhs = kwargs[LHS]
        cur_m_id = "{}_{}".format(lhs, self.matrix_index)
        if la_need_ret_vars(**kwargs):
            return {}
        elif la_need_ret_matrix(**kwargs):
            content += '{} = np.zeros(({},{}))\n'.format(cur_m_id, self.symtable[cur_m_id].dimensions[0],
                                                      self.symtable[cur_m_id].dimensions[1])
            ret = self.walk(node.value, **kwargs)
            for i in range(len(ret)):
                content += "    {}[{}] = [{}]\n".format(cur_m_id, i, ret[i])
            self.matrix_index += 1
            return content
        self.matrix_index += 1
        return cur_m_id

    def walk_MatrixRows(self, node, **kwargs):
        content = ""
        lhs = kwargs[LHS]
        cur_m_id = "{}_{}".format(lhs, self.matrix_index)
        rows = self.symtable[cur_m_id].dimensions[0]
        cols = self.symtable[cur_m_id].dimensions[1]
        ret = []
        if node.rs:
            for r in node.rs:
                ret = ret + self.walk(r, **kwargs)
        if node.r:
            for r in node.r:
                ret.append(self.walk(r, **kwargs))
        return ret

    def walk_MatrixRow(self, node, **kwargs):
        ret = []
        if node.rc:
            for rc in node.rc:
                ret.append(self.walk(rc, **kwargs))
        if node.exp:
            for exp in node.exp:
                ret.append(self.walk(exp, **kwargs))
        return ','.join(ret)

    def walk_MatrixRowCommas(self, node, **kwargs):
        ret = []
        if node.value:
            for value in node.value:
                ret.append(self.walk(value, **kwargs))
        if node.exp:
            for exp in node.exp:
                ret.append(self.walk(exp, **kwargs))
        return ','.join(ret)

    def walk_ExpInMatrix(self, node, **kwargs):
        return self.walk(node.value, **kwargs)

    def walk_Add(self, node, **kwargs):
        if la_need_ret_vars(**kwargs):
            left_set = self.walk(node.left, **kwargs)
            right_set = self.walk(node.right, **kwargs)
            return left_set.union(right_set)
        elif la_need_ret_matrix(**kwargs):
            return self.walk(node.left, **kwargs) + self.walk(node.right, **kwargs)
        return self.walk(node.left, **kwargs) + '+' + self.walk(node.right, **kwargs)

    def walk_Subtract(self, node, **kwargs):
        if la_need_ret_vars(**kwargs):
            left_set = self.walk(node.left, **kwargs)
            right_set = self.walk(node.right, **kwargs)
            return left_set.union(right_set)
        elif la_need_ret_matrix(**kwargs):
            return self.walk(node.left, **kwargs) + self.walk(node.right, **kwargs)
        return self.walk(node.left, **kwargs) + '-' + self.walk(node.right, **kwargs)

    def walk_Multiply(self, node, **kwargs):
        if la_need_ret_vars(**kwargs):
            left_set = self.walk(node.left, **kwargs)
            right_set = self.walk(node.right, **kwargs)
            return left_set.union(right_set)
        elif la_need_ret_matrix(**kwargs):
            return self.walk(node.left, **kwargs) + self.walk(node.right, **kwargs)
        return self.walk(node.left, **kwargs) + '*' + self.walk(node.right, **kwargs)

    def walk_Divide(self, node, **kwargs):
        if la_need_ret_vars(**kwargs):
            left_set = self.walk(node.left, **kwargs)
            right_set = self.walk(node.right, **kwargs)
            return left_set.union(right_set)
        elif la_need_ret_matrix(**kwargs):
            return self.walk(node.left, **kwargs) + self.walk(node.right, **kwargs)
        return self.walk(node.left, **kwargs) + '/' + self.walk(node.right, **kwargs)

    def walk_Assignment(self, node, **kwargs):
        if la_need_ret_vars(**kwargs):
            left_set = self.walk(node.left, **kwargs)
            right_set = self.walk(node.right, **kwargs)
            return left_set.union(right_set)
        # walk matrix first
        content = ""
        left_id = self.walk(node.left, **kwargs)
        kwargs[LHS] = left_id
        self.matrix_index = 0
        if left_id in self.m_dict:
            kwargs[WALK_TYPE] = WalkTypeEnum.RETRIEVE_MATRIX_STAT
            content += self.walk(node.right, **kwargs)
            kwargs[WALK_TYPE] = WalkTypeEnum.RETRIEVE_EXPRESSION
        self.ret = left_id
        self.matrix_index = 0
        # self left-hand-side symbol
        if self.symtable[left_id].var_type == VarTypeEnum.MATRIX:
            content += '    {} = np.zeros(({},{}))\n'.format(left_id, self.symtable[left_id].dimensions[0], self.symtable[left_id].dimensions[1])
        elif self.symtable[left_id].var_type == VarTypeEnum.VECTOR:
            content += '{} = np.zeros(({}))\n'.format(left_id, self.symtable[left_id].dimensions[0])
        content += "    " + left_id + ' = ' + str(self.walk(node.right, **kwargs))
        la_remove_key(LHS, **kwargs)
        return content

    def walk_IdentifierSubscript(self, node, **kwargs):
        right = []
        for value in node.right:
            right.append(self.walk(value))
        if la_need_ret_vars(**kwargs):
            return {self.walk(node.left) + '_' + ','.join(right)}
        return self.walk(node.left, **kwargs) + '_' + ','.join(right)

    def walk_IdentifierAlone(self, node, **kwargs):
        if la_need_ret_vars(**kwargs):
            return {node.value}
        return node.value

    def walk_Derivative(self, node, **kwargs):
        if la_need_ret_vars(**kwargs):
            return {}
        return ""

    def walk_Factor(self, node, **kwargs):
        if node.id:
            return self.walk(node.id, **kwargs)
        elif node.num:
            return self.walk(node.num, **kwargs)
        elif node.sub:
            return self.walk(node.sub, **kwargs)
        elif node.m:
            return self.walk(node.m, **kwargs)
        elif node.f:
            return self.walk(node.f, **kwargs)
        elif node.op:
            return self.walk(node.op, **kwargs)

    def walk_Number(self, node, **kwargs):
        if la_need_ret_vars(**kwargs):
            return {}
        return self.walk(node.value, **kwargs)

    def walk_Integer(self, node, **kwargs):
        if la_need_ret_vars(**kwargs):
            return {}
        return ''.join(node.value)