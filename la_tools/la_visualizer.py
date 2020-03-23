from tatsu.objectmodel import Node
from graphviz import Digraph, Source


class LaVisualizer(object):
    def __init__(self):
        self.node = []
        self.ps = []
        self.tags = {}
        self.index = 0
        self.queue = []

    def visualize(self, node):
        self.reset()
        self.node = node
        self.ps = Digraph(name='pet-shop', node_attr={'shape': 'plaintext', 'fontsize': '12', 'height': '.1'}, edge_attr={'arrowsize': '.5', 'minlen': '1'})
        self.queue.append(self.node)
        while self.queue:
            cur_node = self.queue.pop(0)
            cur_name = type(cur_node).__name__
            cur_index = self.index
            if cur_node in self.tags:
                cur_index = self.tags[cur_node]
            else:
                self.tags[cur_node] = self.index
                self.ps.node(name=str(self.index), label=cur_name)
                self.index += 1
            for k, v in cur_node.ast.items():
                if k != "parseinfo":
                    children = getattr(cur_node, k)
                    if isinstance(children, list):
                        for child in children:
                            self.handleChild(child, cur_index, k)
                    else:
                        self.handleChild(children, cur_index, k)
        src = Source(self.ps.source)
        src.render('AST', view=False)

    def handleChild(self, child, cur_index, k):
        if isinstance(child, Node):
            node_name = type(child).__name__
            self.queue.append(child)
            node_index = self.index
            if child in self.tags:
                node_index = self.tags[child]
            else:
                self.ps.node(name=str(self.index), label=k + ":" + node_name)
                self.tags[child] = self.index
                self.index += 1
            self.ps.edge(str(cur_index), str(node_index))
        else:
            self.ps.node(name=str(self.index), label=k + ":" + child)
            self.ps.edge(str(cur_index), str(self.index))
            self.index += 1

    def reset(self):
        self.tags = {}
        self.index = 0
        self.queue = []
