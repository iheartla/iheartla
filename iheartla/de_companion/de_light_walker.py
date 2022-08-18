from ..la_parser.ir import *
from ..la_parser.light_walker import LightWalker


class DeLightWalker(LightWalker):
    def __init__(self):
        super().__init__()
        self.smooth_dict = {}     # M in R^3
        self.mapping_dict = {}
        self.sym_list = []
        self.solved_list = []
        self.has_de = False

    def reset(self):
        self.smooth_dict.clear()
        self.mapping_dict.clear()
        self.has_de = False
        self.sym_list.clear()
        self.solved_list.clear()

    def walk_DeWhereCondition(self, node, **kwargs):
        self.has_de = True
        # M in R^3
        assert type(node.type).__name__ == 'VectorType'
        la_type = self.walk(node.type, **kwargs)
        for id_index in range(len(node.id)):
            cur_id = self.walk(node.id[id_index], **kwargs)
            self.smooth_dict[cur_id] = la_type.rows
            self.sym_list.append(cur_id)
        return ""

    def walk_WhereCondition(self, node, **kwargs):
        if type(node.type).__name__ == 'MappingType':
            la_type = self.walk(node.type, **kwargs)
            for id_index in range(len(node.id)):
                cur_id = self.walk(node.id[id_index], **kwargs)
                self.mapping_dict[cur_id] = la_type
                self.sym_list.append(cur_id)
            return ''
        else:
            for id_index in range(len(node.id)):
                cur_id = self.walk(node.id[id_index], **kwargs)
                self.sym_list.append(cur_id)
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
        la_type = VectorType(rows=id1_content, element_type=element_type)
        return la_type

    def walk_MappingType(self, node, **kwargs):
        params = []
        template_symbols = {}
        template_ret = []
        if node.params:
            for index in range(len(node.params)):
                param_node = self.walk(node.params[index], **kwargs)
                params.append(param_node)
        ret_list = []
        if node.ret:
            for cur_index in range(len(node.ret)):
                ret_node = self.walk(node.ret[cur_index], **kwargs)
                ret_list.append(ret_node)
        elif node.ret_type:
            for cur_index in range(len(node.ret_type)):
                ret_type = self.walk(node.ret_type[cur_index], **kwargs)
                ret_list.append(ret_type)
        la_type = MappingType(params=params, ret=ret_list, template_symbols=template_symbols, ret_symbols=template_ret)
        return la_type

    def walk_DeSolver(self, node, **kwargs):
        unknown = self.walk(node.u, **kwargs)
        self.sym_list.append(unknown)
        self.solved_list.append(unknown)
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




