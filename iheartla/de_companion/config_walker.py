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
        self.par_dict = {}   # parameters
        self.ode_dict = {}

    def walk_Start(self, node, **kwargs):
        for block in node.vblock:
            self.walk(block, **kwargs)
        print("end parsing config")

    def walk_Triangle(self, node, **kwargs):
        return Triangle(self.walk(node.v, **kwargs), self.walk(node.e, **kwargs), self.walk(node.f, **kwargs))

    def walk_Point(self, node, **kwargs):
        return PointCloud(self.walk(node.v, **kwargs))

    def walk_Operators(self, node, **kwargs):
        # print(node)
        return node.text

    def walk_WhereCondition(self, node, **kwargs):
        if type(node.type).__name__ == 'MappingType':
            la_type = self.walk(node.type, **kwargs)
            print(node.type.text)
            for id_index in range(len(node.id)):
                cur_id = self.walk(node.id[id_index], **kwargs)
                self.par_dict[cur_id.get_name()] = la_type
            return ''
        else:
            #
            la_type = self.walk(node.type, **kwargs)
            print(node.type.text)
            for id_index in range(len(node.id)):
                cur_id = self.walk(node.id[id_index], **kwargs)
                self.par_dict[cur_id.get_name()] = la_type
        return node.text

    def walk_VectorType(self, node, **kwargs):
        element_type = ''
        if node.type:
            if node.type == 'ℝ':
                element_type = ScalarType()
            elif node.type == 'ℤ':
                element_type = ScalarType(is_int=True)
        else:
            element_type = ScalarType()
        id1_content = self.walk(node.id1, **kwargs)
        la_type = VectorType(rows=id1_content.raw_text, element_type=element_type)
        return la_type

    def walk_MatrixType(self, node, **kwargs):
        ir_node = MatrixTypeNode(parse_info=node.parseinfo, raw_text=node.text)
        element_type = ''
        if node.type:
            ir_node.type = node.type
            if node.type == 'ℝ':
                element_type = ScalarType()
            elif node.type == 'ℤ':
                element_type = ScalarType(is_int=True)
        else:
            element_type = ScalarType()
        id1_content = self.walk(node.id1, **kwargs)
        id2_content = self.walk(node.id2, **kwargs)
        la_type = MatrixType(rows=id1_content, cols=id2_content, element_type=element_type)
        if node.attr and 'sparse' in node.attr:
            la_type.sparse = True
        return la_type

    def walk_MappingType(self, node, **kwargs):
        params = []
        if node.params:
            for index in range(len(node.params)):
                param_node = self.walk(node.params[index], **kwargs)
                params.append(param_node)
        ret_list = []
        if node.ret:
            for cur_index in range(len(node.ret)):
                ret_node = self.walk(node.ret[cur_index], **kwargs).ir
                ret_list.append(ret_node)
        elif node.ret_type:
            for cur_index in range(len(node.ret_type)):
                ret_node = self.walk(node.ret_type[cur_index], **kwargs)
                ret_list.append(ret_node)
            if len(ret_list) == 1 and len(params) == 1:
                t_type = ret_list[0]
                if params[0].is_node(IRNodeType.Id):
                    if t_type.is_vector():
                        # V → ℝ^n
                        la_type = MatrixType(rows=SizeNode(params[0]), cols=t_type.rows, element_type=t_type.element_type)
                        return la_type
        la_type = MappingType(params=params, ret=ret_list)
        return la_type

    def walk_Geometry(self, node, **kwargs):
        id = self.walk(node.id)
        geometry = self.walk(node.g)
        return GeometryNode(id, geometry)

    def walk_ImportVar(self, node, **kwargs):
        rname = None
        if node.r:
            rname = self.walk(node.r, **kwargs)
        return ImportVarNode(self.walk(node.name, **kwargs), rname)

    def walk_ImportDef(self, node, **kwargs):
        lhs = self.walk(node.lhs)
        rhs = self.walk(node.rhs)
        if type(node.lhs).__name__ == 'Operators':
            if node.lhs.l:
                self.laplacian_dict[lhs] = rhs
        return node.text

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

#### Arith
    def walk_ArithExpression(self, node, **kwargs):
        value_ir = self.walk(node.value, **kwargs)
        ir_node = ExpressionNode(parse_info=node.parseinfo, raw_text=node.text)
        ir_node.value = value_ir
        ir_node.sign = node.sign
        return ir_node

    def walk_ArithSubexpression(self, node, **kwargs):
        value_ir = self.walk(node.value, **kwargs)
        ir_node = SubexpressionNode(parse_info=node.parseinfo, raw_text=node.text)
        ir_node.value = value_ir
        return ir_node

    def walk_ArithAdd(self, node, **kwargs):
        left_ir = self.walk(node.left, **kwargs)
        right_ir = self.walk(node.right, **kwargs)
        ir_node = AddNode(left_ir, right_ir, parse_info=node.parseinfo, raw_text=node.text)
        return ir_node

    def walk_ArithSubtract(self, node, **kwargs):
        left_ir = self.walk(node.left, **kwargs)
        right_ir = self.walk(node.right, **kwargs)
        ir_node = SubNode(left_ir, right_ir, parse_info=node.parseinfo, raw_text=node.text)
        return ir_node

    def walk_ArithMultiply(self, node, **kwargs):
        left_ir = self.walk(node.left, **kwargs)
        right_ir = self.walk(node.right, **kwargs)
        ir_node = MulNode(left_ir, right_ir, parse_info=node.parseinfo, raw_text=node.text)
        return ir_node

    def walk_ArithDivide(self, node, **kwargs):
        left_ir = self.walk(node.left, **kwargs)
        right_ir = self.walk(node.right, **kwargs)
        ir_node = DivNode(left_ir, right_ir, parse_info=node.parseinfo, raw_text=node.text)
        return ir_node

    def walk_ArithFactor(self, node, **kwargs):
        ir_node = FactorNode(parse_info=node.parseinfo, raw_text=node.text)
        if node.id0:
            id_ir = self.walk(node.id0, **kwargs)
            ir_node.id = id_ir
        elif node.num:
            ir_node.num = self.walk(node.num, **kwargs)
        elif node.sub:
            ir_node.sub = self.walk(node.sub, **kwargs)
        elif node.size:
            ir_node.size = self.walk(node.size, **kwargs)
        return ir_node
####