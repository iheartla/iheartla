import copy
from tatsu.model import NodeWalker
from tatsu.objectmodel import Node
from ..la_parser.la_types import *
from ..la_tools.la_logger import *
from ..la_tools.la_msg import *
from ..la_tools.la_helper import *
import regex as re
from ..la_tools.la_helper import filter_subscript


class ConfigWalker(NodeWalker):
    def __init__(self):
        super().__init__()

    def walk_Start(self, node, **kwargs):
        for block in node.vblock:
            self.walk(block, **kwargs)
        print(node)

    def walk_Triangle(self, node, **kwargs):
        print(node)

    def walk_Point(self, node, **kwargs):
        print(node)

    def walk_Mapping(self, node, **kwargs):
        print(node)

    def walk_MapType(self, node, **kwargs):
        print(node)

