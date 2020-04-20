from la_parser.ir import *


class IRVisitor(object):
    def __init__(self):
        super().__init__()

    def visit(self, node):
        type_func = {
            IRNodeType.Id: "visit_id",
            IRNodeType.Add: "visit_add",
        }
        func = getattr(self, type_func[node.node_type], None)
        if func:
            func(node)
        else:
            print("invalid node type")

    def visit_id(self, node):
        print("visit_id")

    def visit_add(self, node):
        print("visit_add")