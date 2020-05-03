import sys
sys.path.append('./')
from la_test.base_python_test import BasePythonTest
from la_parser.parser import parse_la, ParserTypeEnum


class TestMatrix(BasePythonTest):
    def test_matrix(self):
        la_str = """A = [a b; b a]
        where
        a: scalar
        b: scalar"""
        fun_name = self.set_up(la_str, None)