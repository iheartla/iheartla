from la_parser.base_walker import *


class NumpyWalker(BaseNodeWalker):
    def __init__(self):
        super().__init__()
        self.pre_str = '''import numpy as np\n'''
        self.post_str = ''''''

    def walk_Statements(self, node):
        content = ''
        for stat in node.value:
            content += self.walk(stat)
        content += '\n'
        return content

    def walk_Assignment(self, node):
        return node.left + '=' + node.right

    def walk_Derivative(self, node):
        return ""