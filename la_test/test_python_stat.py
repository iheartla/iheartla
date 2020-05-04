import sys
sys.path.append('./')
from la_test.base_python_test import BasePythonTest
from la_parser.parser import parse_la, ParserTypeEnum
import numpy as np


class TestStat(BasePythonTest):
    def test_return_value(self):
        # no return symbol
        la_str = """a b
        where
        a: scalar
        b: scalar"""
        fun_name = self.set_up(la_str, None)
        self.assertEqual(fun_name(3, 2), 6)
