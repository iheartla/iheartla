from la_parser.base_walker import *


class NumpyWalker(BaseNodeWalker):
    def __init__(self):
        super().__init__()
        self.pre_str = '''import numpy as np\n\n'''
        self.post_str = ''''''
        self.ret = 'ret'

    def walk_Start(self, node):
        content = 'def myExpression(' + ', '.join(self.parameters) + ')\n'
        content += self.walk(node.stat)
        content += '    return ' + self.ret
        content += '\n'
        return content

    def walk_WhereConditions(self, node):
        pass

    def walk_Statements(self, node):
        index = 0
        content = ''
        for stat in node.value:
            if type(stat).__name__ == 'Statements':
                content += self.walk(stat)
            else:
                content += '    '
                if index == len(node.value) - 1:
                    if type(stat).__name__ != 'Assignment':
                        self.ret = 'ret'
                        content += self.ret + ' = '
                content += self.walk(stat) + '\n'
            index += 1
        return content

    def walk_Summation(self, node):
        return self.walk(node.exp)

    def walk_Multiply(self, node):
        return self.walk(node.left) + '*' + self.walk(node.right)

    def walk_Assignment(self, node):
        self.ret = self.walk(node.left)
        return self.walk(node.left) + ' = ' + str(self.walk(node.right))

    def walk_IdentifierSubscript(self, node):
        right = []
        for value in node.right:
            right.append(self.walk(value))
        print(self.walk(node.left) + '_' + ','.join(right))
        return self.walk(node.left) + '_' + ','.join(right)

    def walk_IdentifierAlone(self, node):
        return node.value

    def walk_Derivative(self, node):
        return ""

    def walk_Factor(self, node):
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

    def walk_Number(self, node):
        return self.walk(node.value)

    def walk_Integer(self, node):
        return ''.join(node.value)