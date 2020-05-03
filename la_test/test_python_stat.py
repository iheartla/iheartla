import sys
sys.path.append('./')
from la_test.base_python_test import BasePythonTest
from la_parser.parser import parse_la, ParserTypeEnum
import numpy as np


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
        fun_name = self.set_up(la_str, None)
        self.assertEqual(fun_name(3), -5)
        self.assertEqual(fun_name(-3), 1)

    def test_unary_matrix(self):
        la_str = """B = -2A
        where
        A: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[-2, -4], [-6, -8]])
        self.assertDMatrixEqual(fun_name(A), B)

        la_str = """B = -A2
        where
        A: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[-2, -4], [-6, -8]])
        self.assertDMatrixEqual(fun_name(A), B)

        la_str = """B = -[2 2; 2 2]-A
        where
        A: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[-3, -4], [-5, -6]])
        self.assertDMatrixEqual(fun_name(A), B)