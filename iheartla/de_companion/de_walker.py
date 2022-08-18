import copy
from tatsu.model import NodeWalker
from tatsu.objectmodel import Node
from iheartla.la_parser.la_types import *
from iheartla.la_tools.la_logger import *
from iheartla.la_tools.la_msg import *
from iheartla.la_tools.la_helper import *
import regex as re
from .de_light_walker import DeLightWalker
from ..la_parser.ir import *
from ..la_parser.ir_visitor import *
from ..la_tools.config_manager import *


class DeWalker(DeLightWalker):
    def __init__(self):
        super().__init__()
        self.cfg_mgr = ConfMgr.getInstance()

    def reset(self):
        super(DeWalker, self).reset()

    def gen_extra_content(self):
        extra = ''
        # geometry info
        content_list = []
        for sym in self.cfg_mgr.walker.cfg_symtable:
            c_type = self.cfg_mgr.walker.cfg_symtable[sym]
            content_list.append("{} ∈ {}".format(sym, c_type.get_raw_text()))
        #
        for sym, c_type in self.cfg_mgr.walker.par_dict.items():
            if sym not in self.cfg_mgr.walker.solved_list:
                content_list.append("{} ∈ {}".format(sym, c_type.get_raw_text()))
        # laplacian
        for sym, node in self.cfg_mgr.walker.laplacian_dict.items():
            content_list.append(node.raw_text)
        if len(content_list) > 0:
            extra += '\n'.join(content_list) + '\n'
        return extra

    def walk_Start(self, node, **kwargs):
        # gen content from cfg
        extra = self.gen_extra_content()
        #
        content_list = []
        for vblock in node.vblock:
            content_list.append(self.walk(vblock, **kwargs))
        return extra + '\n'.join(content_list)

    def walk_ParamsBlock(self, node, **kwargs):
        content = self.walk(node.conds, **kwargs)
        if node.annotation:
            content = "{}\n{}".format(node.annotation, content)
        return content

    def walk_WhereConditions(self, node, **kwargs):
        content_list = []
        for vblock in node.value:
            content_list.append(self.walk(vblock, **kwargs))
        return '\n'.join(content_list)

    def walk_WhereCondition(self, node, **kwargs):
        if type(node.type).__name__ == 'MappingType':
            la_type = self.walk(node.type, **kwargs)
            print(node.type.text)
            for id_index in range(len(node.id)):
                cur_id = self.walk(node.id[id_index], **kwargs)
                self.mapping_dict[cur_id] = la_type
            return ''
        return node.text

    def walk_DeWhereCondition(self, node, **kwargs):
        # M in R^3
        assert type(node.type).__name__ == 'VectorType'
        la_type = self.walk(node.type, **kwargs)
        for id_index in range(len(node.id)):
            cur_id = self.walk(node.id[id_index], **kwargs)
            self.smooth_dict[cur_id] = la_type.rows
        return ""

    def walk_Import(self, node, **kwargs):
        return node.text

    def walk_Statements(self, node, **kwargs):
        if type(node.stat).__name__ == 'DeSolver':
            return self.walk(node.stat, **kwargs)
        return node.text

    def walk_DeSolver(self, node, **kwargs):
        unknown = self.walk(node.u, **kwargs)
        stat_list = []
        for cur_index in range(len(node.lexpr)):
            lhs = self.walk(node.lexpr[cur_index], **kwargs)
            rhs = self.walk(node.rexpr[cur_index], **kwargs)
            stat_list.append("{} = {}".format(lhs, rhs))
        return "solve_({} ∈ {}) {}".format(unknown, self.cfg_mgr.walker.par_dict[unknown].get_raw_text(), '\n'.join(stat_list))

    def walk_Laplace(self, node, **kwargs):
        if node.name in self.cfg_mgr.walker.laplacian_dict:
            import_node = self.cfg_mgr.walker.laplacian_dict[node.name]
            return "{}{}".format(import_node.get_imported_sym()[0], node.value.text)
        return node.text
