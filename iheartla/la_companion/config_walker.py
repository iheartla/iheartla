import copy
from tatsu.model import NodeWalker
from tatsu.objectmodel import Node
from ..la_parser.la_types import *
from ..la_tools.la_logger import *
from ..la_tools.la_msg import *
from ..la_tools.la_helper import *
import regex as re
from ..la_tools.la_helper import filter_subscript
from ..la_parser.type_walker import *


class ConfigWalker(NodeWalker):
    def __init__(self):
        super().__init__()
        self.type_walker = TypeWalker()
        self.path = None
        self.gradient_dict = {}
        self.divergence_dict = {}
        self.laplacian_dict = {}
        self.par_dict = {}
        self.ode_dict = {}

    def walk_Start(self, node, **kwargs):
        for block in node.vblock:
            self.walk(block, **kwargs)
        print(node)

    def walk_Triangle(self, node, **kwargs):
        # print(node)
        pass

    def walk_Point(self, node, **kwargs):
        # print(node)
        pass

    def walk_Operators(self, node, **kwargs):
        # print(node)
        return node.text

    def walk_Mapping(self, node, **kwargs):
        # print(node)
        lhs = self.walk(node.lhs, **kwargs)
        print("lhs: {}".format(lhs))
        if type(node.lhs).__name__ == 'Operators':
            if node.lhs.l:
                self.laplacian_dict[lhs] = self.walk(node.rhs, **kwargs)
        # if node.ref:
        #     ref = self.walk(node.ref, **kwargs)
        #     print("ref: {}, {}".format(ref, node.ref))

    def walk_Rhs(self, node, **kwargs):
        return node.text

    def walk_MapType(self, node, **kwargs):
        # print(node)
        pass

    def walk_SizeOp(self, node, **kwargs):
        param = self.walk(node.i, **kwargs)

    def walk_IdentifierAlone(self, node, **kwargs):
        node_type = LaVarType(VarTypeEnum.INVALID)
        if node.value:
            value = node.value
        elif node.id:
            value = '`' + node.id + '`'
        else:
            value = node.const
        return value

