import copy
from tatsu.model import NodeWalker
from tatsu.objectmodel import Node
from iheartla.la_parser.la_types import *
from iheartla.la_tools.la_logger import *
from iheartla.la_tools.la_msg import *
from iheartla.la_tools.la_helper import *
import regex as re
from ..la_parser.light_walker import LightWalker
from ..la_parser.ir import *


class DeWalker(LightWalker):
    def __init__(self):
        super().__init__()
        self.smooth_dict = {}     # M in R^3
        self.mapping_dict = {}

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
                self.walk(vblock, **kwargs)
                continue
            content_list.append(self.walk(vblock, **kwargs))
        return '\n'.join(content_list)

    def walk_WhereCondition(self, node, **kwargs):
        if type(node.type).__name__ == 'MappingType':
            print(node.type.text)
            return ''
        return node.text

    def walk_DeWhereCondition(self, node, **kwargs):
        # M in R^3
        assert type(node.type).__name__ == 'VectorType'
        la_type = self.walk(node.type, **kwargs)
        for id_index in range(len(node.id)):
            cur_id = self.walk(node.id[id_index], **kwargs)
            self.smooth_dict[cur_id] = la_type.rows
        return node.text

    def walk_VectorType(self, node, **kwargs):
        ir_node = VectorTypeNode(parse_info=node.parseinfo, raw_text=node.text)
        self.dyn_dim = False
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
        la_type = VectorType(rows=id1_content, element_type=element_type)
        return la_type

    def walk_Import(self, node, **kwargs):
        return node.text

    def walk_Statements(self, node, **kwargs):
        if type(node.stat).__name__ == 'DeSolver':
            return ''
            return self.walk(node.stat, **kwargs)
        return node.text

    def walk_DeSolver(self, node, **kwargs):
        return node.text

    def walk_SubInteger(self, node, **kwargs):
        value = 0
        for index in range(len(node.value)):
            value += get_unicode_sub_number(node.value[len(node.value) - 1 - index]) * 10 ** index
        return int(value)

    def walk_SupInteger(self, node, **kwargs):
        value = 0
        for index in range(len(node.value)):
            value += get_unicode_number(node.value[len(node.value) - 1 - index]) * 10 ** index
        return int(value)
