import sys
sys.path.append('./')
from la_test.base_python_test import BasePythonTest
from la_parser.parser import parse_la, ParserTypeEnum


class TestStat(BasePythonTest):
    def test_unary_scalar(self):
        la_str = """b = -2a
        where
        a: scalar"""
        fun_name = self.set_up(la_str, None)
        self.assertEqual(fun_name(3), -6)
        self.assertEqual(fun_name(-3), 6)

        la_str = """b = -a2
        where
        a: scalar"""
        fun_name = self.set_up(la_str, None)
        self.assertEqual(fun_name(3), -6)
        self.assertEqual(fun_name(-3), 6)

        la_str = """b = -2-a
        where
        a: scalar"""
        fun_name = self.set_up(la_str, None)
        self.assertEqual(fun_name(3), -5)
        self.assertEqual(fun_name(-3), 1)

        la_str = """b = -a -2
        where
        a: scalar"""
        self.set_up(la_str, None)
        self.assertEqual(fun_name(3), -5)
        self.assertEqual(fun_name(-3), 1)

    def test_unary_matrix(self):
        la_str = """B = -2A
        where
        A: scalar"""
        fun_name = self.set_up(la_str, None)