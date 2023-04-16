from tatsu.objectmodel import Node
from graphviz import Digraph, Source


class LaVisualizer(object):
    def __init__(self):
        self.node = []
        self.ps = []
        self.tags = {}
        self.index = 0
        self.queue = []
        self.cnt = 0

    def visualize(self, node, pre_walk=True):
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
            if isinstance(cur_node.ast, str):  # no annotation
                self.ps.node(name=str(self.index), label=cur_node.ast)
                self.ps.edge(str(cur_index), str(self.index))
                self.index += 1
                continue
            for k, v in cur_node.ast.items():
                if k != "parseinfo":
                    children = getattr(cur_node, k)
                    if isinstance(children, list):
                        for child in children:
                            if child is not None:
                                self.handleChild(child, cur_index, k)
                    else:
                        if children is not None:
                            self.handleChild(children, cur_index, k)
        src = Source(self.ps.source)
        self.cnt += 1
        pre = "_PRE" if pre_walk else ""
        src.render("AST{}_{}".format(pre, self.cnt), view=False)

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
            if isinstance(child, list):
                # e.g.: partial derivative
                content = "".join(['' if isinstance(c, Node) else str(c) for c in child])
            else:
                if isinstance(child, tuple):
                    # identifier in simplified grammar: due to tatsu regex update
                    content = child[0].text
                elif isinstance(child, dict):
                    for k, v in child.items():
                        if k != "parseinfo":
                            children = getattr(child, k)
                            content = str(children)
                            break
                else:
                    content = str(child)
            self.ps.node(name=str(self.index), label=str(k) + ":" + content)
            self.ps.edge(str(cur_index), str(self.index))
            self.index += 1

    def reset(self):
        self.tags = {}
        self.index = 0
        self.queue = []
