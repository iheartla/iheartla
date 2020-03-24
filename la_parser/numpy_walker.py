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
                content += self.walk(stat,**kwargs) + '\n'
            index += 1
        return content

    def walk_Summation(self, node, **kwargs):
        subs = []
        for sub in node.sub:
            subs.append(self.walk(sub))

        return self.walk(node.exp)

    def walk_Add(self, node, **kwargs):
        return self.walk(node.left) + '+' + self.walk(node.right)

    def walk_Subtract(self, node, **kwargs):
        return self.walk(node.left) + '-' + self.walk(node.right)

    def walk_Multiply(self, node, **kwargs):
        return self.walk(node.left) + '*' + self.walk(node.right)

    def walk_Assignment(self, node, **kwargs):
        self.ret = self.walk(node.left)
        return self.walk(node.left) + ' = ' + str(self.walk(node.right))

    def walk_IdentifierSubscript(self, node, **kwargs):
        right = []
        for value in node.right:
            right.append(self.walk(value))
        return self.walk(node.left) + '_' + ','.join(right)

    def walk_IdentifierAlone(self, node, **kwargs):
        return node.value

    def walk_Derivative(self, node, **kwargs):
        return ""

    def walk_Factor(self, node, **kwargs):
        if node.id:
            return self.walk(node.id)
        elif node.num:
            return self.walk(node.num)
        elif node.sub:
            return self.walk(node.sub)
        elif node.m:
            return self.walk(node.m)
        elif node.f:
            return self.walk(node.f)

    def walk_Number(self, node, **kwargs):
        return self.walk(node.value)

    def walk_Integer(self, node, **kwargs):
        return ''.join(node.value)