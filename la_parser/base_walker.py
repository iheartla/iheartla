from tatsu.model import NodeWalker
from tatsu.objectmodel import Node
from tatsu.symtables import *
from la_parser.la_types import *
from la_parser.la_symbol import *
from la_parser.type_walker import *
from la_tools.la_visualizer import LaVisualizer


class BaseNodeWalker(NodeWalker):
    def __init__(self):
        super().__init__()
        self.pre_str = ''
        self.post_str = ''
        self.symtable = {}
        self.parameters = set()
        self.subscripts = {}
        self.matrix_index = 0    # index of matrix in a single assignment statement
        self.m_dict = {}
        self.node_dict = {}
        self.dim_dict = {}
        self.sub_name_dict = {}
        self.visualizer = LaVisualizer()

    def print_symbols(self):
        print("symtable:")
        for (k, v) in self.symtable.items():
            print(k + ':' + str(v.var_type) + ', dimension:' + str(v.dimensions))
        print("subscripts:\n" + str(self.subscripts))
        print("parameters:\n" + str(self.parameters))
        print("m_dict:\n" + str(self.m_dict))
        print("dim_dict:\n" + str(self.dim_dict))
        print("sub_name_dict:\n" + str(self.sub_name_dict) + '\n')
        # print("node_dict:\n" + str(self.node_dict) + '\n')

    def walk_model(self, node):
        type_walker = TypeWalker()
        type_walker.walk(node)
        self.symtable = type_walker.symtable
        self.parameters = type_walker.parameters
        self.subscripts = type_walker.subscripts
        self.m_dict = type_walker.m_dict
        self.node_dict = type_walker.node_dict
        self.dim_dict = type_walker.dim_dict
        self.sub_name_dict = type_walker.sub_name_dict
        self.print_symbols()
        self.visualizer.visualize(node)
        content = self.pre_str + self.walk(node) + self.post_str
        return content

    def walk_Node(self, node):
        print('Reached Node: ', node)

    def walk_str(self, s):
        return s

    def walk_object(self, o):
        raise Exception('Unexpected type %s walked', type(o).__name__)
    ###################################################################

    def contain_subscript(self, identifier):
        return identifier.find("_") != -1

    def get_all_ids(self, identifier):
        res = identifier.split('_')
        return [res[0], res[1].split(',')]

    def get_main_id(self, identifier):
        if self.contain_subscript(identifier):
            ret = self.get_all_ids(identifier)
            return ret[0]
        return identifier
