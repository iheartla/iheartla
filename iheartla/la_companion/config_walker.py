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
                if node.rhs.im:
                    self.laplacian_dict[lhs] = self.walk(node.rhs, **kwargs)
                # self.laplacian_dict[lhs] = self.walk(node.rhs, **kwargs)
        # if node.ref:
        #     ref = self.walk(node.ref, **kwargs)
        #     print("ref: {}, {}".format(ref, node.ref))

    def walk_Rhs(self, node, **kwargs):
        if node.im:
            return self.walk(node.im, **kwargs)
        return node.text

    def walk_MapType(self, node, **kwargs):
        # print(node)
        pass

    def walk_Import(self, node, **kwargs):
        params = []
        params_list = []
        module = None
        package = None
        for par in node.params:
            par_info = self.walk(par, **kwargs)
            params.append(par_info.ir)
            params_list.append(par_info.ir.get_name())
        package_info = self.walk(node.package, **kwargs)
        name_list = []
        name_ir_list = []
        for cur_name in node.names:
            name_info = self.walk(cur_name, **kwargs)
            name_ir_list.append(name_info.ir)
            name_list.append(name_info.ir.get_name())
        module = package_info.ir
        import_node = ImportNode(package=package, module=module, names=name_ir_list, separators=node.separators,
                                     params=params, parse_info=node.parseinfo, raw_text=node.text)
        return import_node

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
        #
        ir_node = IdNode(value, parse_info=node.parseinfo, raw_text=node.text)
        node_info = NodeInfo(node_type, value, {value}, ir_node)
        return node_info

