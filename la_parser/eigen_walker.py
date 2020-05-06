from la_parser.base_walker import *


class EigenWalker(BaseNodeWalker):
    def __init__(self):
        super().__init__(ParserTypeEnum.EIGEN)
        self.pre_str = '''#include <Eigen/Core>\n#include <string>\n#include <iostream>\n'''
        self.post_str = ''''''
        self.ret = 'ret'

    def walk_Start(self, node, **kwargs):
        return ""