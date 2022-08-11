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
from .geometry import *

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
        # print(node)

    def walk_Triangle(self, node, **kwargs):
        return Triangle(self.walk(node.v, **kwargs), self.walk(node.e, **kwargs), self.walk(node.f, **kwargs))

    def walk_Point(self, node, **kwargs):
        return PointCloud(self.walk(node.v, **kwargs))

    def walk_Operators(self, node, **kwargs):
        # print(node)
        return node.text

    def walk_Mapping(self, node, **kwargs):
        # print(node)
        lhs = self.walk(node.lhs, **kwargs)
        rhs = self.walk(node.rhs, **kwargs)
        # print("lhs: {}".format(lhs))
        if type(node.lhs).__name__ == 'Operators':
            if node.lhs.l:
                if node.rhs.im:
                    self.laplacian_dict[lhs] = rhs
                # self.laplacian_dict[lhs] = self.walk(node.rhs, **kwargs)
        else:
            # identifier
            # print(rhs)
            pass
        # if node.ref:
        #     ref = self.walk(node.ref, **kwargs)
        #     print("ref: {}, {}".format(ref, node.ref))

    def walk_Rhs(self, node, **kwargs):
        if node.im:
            # import
            return self.walk(node.im, **kwargs)
        else:
            # normal mapping
            if len(node.params) == 1:
                par_ir = self.walk(node.params[0], **kwargs)
                ret_ir = self.walk(node.ret[0], **kwargs)
                if par_ir.is_node(IRNodeType.Id):
                    pass
                # print(par)
            else:
                # function
                pass

        return node.text

    def walk_Geometry(self, node, **kwargs):
        id = self.walk(node.id)
        geometry = self.walk(node.g)
        return GeometryNode(id, geometry)

    def walk_ImportVar(self, node, **kwargs):
        rname = None
        if node.r:
            rname = self.walk(node.r, **kwargs)
        return ImportVarNode(self.walk(node.name, **kwargs), rname)

    def walk_Import(self, node, **kwargs):
        params = []
        params_list = []
        module = None
        package = None
        for par in node.params:
            par_ir = self.walk(par, **kwargs)
            params.append(par_ir)
            # params_list.append(par_ir.get_name())
        package_info = self.walk(node.package, **kwargs)
        name_list = []
        name_ir_list = []
        r_dict = {}
        for cur_name in node.names:
            import_var = self.walk(cur_name, **kwargs)
            name_ir = import_var.name
            if import_var.rname:
                r_dict[name_ir.get_name()] = import_var.rname.get_name()
            else:
                r_dict[name_ir.get_name()] = name_ir.get_name()
            name_ir_list.append(name_ir)
            name_list.append(name_ir.get_name())
        module = package_info
        import_node = ImportNode(package=package, module=module, names=name_ir_list, separators=node.separators,
                                 params=params, r_dict=r_dict, parse_info=node.parseinfo, raw_text=node.text)
        return import_node

    def walk_SizeOp(self, node, **kwargs):
        param = self.walk(node.i, **kwargs)
        return SizeNode(param, parse_info=node.parseinfo, raw_text=node.text)

    def walk_Module(self, node, **kwargs):
        return ModuleNode(node.text, parse_info=node.parseinfo, raw_text=node.text)

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
        return ir_node

