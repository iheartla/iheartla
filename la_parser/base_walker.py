from tatsu.model import NodeWalker
from tatsu.objectmodel import Node


class BaseNodeWalker(NodeWalker):
    def __init__(self):
        super().__init__()
        self.pre_str = ''
        self.post_str = ''

    def walk_model(self, node):
        print(node)
        content = self.pre_str + self.walk(node) + self.post_str
        return content

    def walk_Node(self, node):
        print('Reached Node', node)

    def walk_str(self, s):
        return s

    def walk_object(self, o):
        raise Exception('Unexpected type %s walked', type(o).__name__)
