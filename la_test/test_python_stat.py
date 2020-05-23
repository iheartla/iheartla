import sys
sys.path.append('./')
from la_test.base_python_test import BasePythonTest, eigen_path, TestFuncInfo
from la_parser.parser import parse_la, ParserTypeEnum
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)


class TestStat(BasePythonTest):
    def test_return_value(self):
        # no return symbol
        la_str = """a b
        where
        a: scalar
        b: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3, 2), 6)
