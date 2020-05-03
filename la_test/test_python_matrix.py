import sys
sys.path.append('./')
from la_test.base_python_test import BasePythonTest
from la_parser.parser import parse_la, ParserTypeEnum
import numpy as np


class TestMatrix(BasePythonTest):
    def test_matrix(self):
        la_str = """A = [a 2; b 3]
        where
        a: scalar
        b: scalar"""
        fun_name = self.set_up(la_str, None)
        a = 1
        b = 4
        B = np.array([[1, 2], [4, 3]])
        self.assertDMatrixEqual(fun_name(a, b), B)