import copy
from tatsu.model import NodeWalker
from tatsu.objectmodel import Node
from .la_types import *
from ..la_tools.la_logger import *
from ..la_tools.la_msg import *
from ..la_tools.la_helper import *
import regex as re


class DeWalker(NodeWalker):
    def __init__(self):
        super().__init__()

    def reset(self):
        pass

    def walk_Node(self, node):
        pass

    def walk_object(self, o):
        pass

    def walk_Start(self, node, **kwargs):
        content_list = []
        for vblock in node.vblock:
            content_list.append(self.walk(vblock, **kwargs))
        return '\n'.join(content_list)

    def walk_ParamsBlock(self, node, **kwargs):
        content = self.walk(node.conds, **kwargs)
        if node.annotation:
            content = "{}\n{}".format(node.annotation, content)
        return content

    def walk_WhereConditions(self, node, **kwargs):
        content_list = []
        for vblock in node.value:
            if type(vblock).__name__ == 'DeWhereCondition':
                print(vblock.text)
                continue
            content_list.append(self.walk(vblock, **kwargs))
        return '\n'.join(content_list)

    def walk_WhereCondition(self, node, **kwargs):
        if type(node.type).__name__ == 'MappingType':
            print(node.type.text)
            return ''
        return node.text

    def walk_Import(self, node, **kwargs):
        return node.text

    def walk_Statements(self, node, **kwargs):
        if type(node.stat).__name__ == 'DeSolver':
            return self.walk(node.stat, **kwargs)
        return node.text

    def walk_DeSolver(self, node, **kwargs):
        return node.text
