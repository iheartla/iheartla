import sys
sys.path.append('./')
from la_test.base_python_test import BasePythonTest
from la_parser.parser import parse_la, ParserTypeEnum
import numpy as np


class TestExpr(BasePythonTest):
    def test_multiplication(self):
        # space
        la_str = """c = a b
        where
        a: scalar
        b: scalar"""
        fun_name = self.set_up(la_str, None)
        self.assertEqual(fun_name(3, 2), 6)
        # star
        la_str = """c = a * b
        where
        a: scalar
        b: scalar"""
        fun_name = self.set_up(la_str, None)
        self.assertEqual(fun_name(3, 2), 6)
        self.assertEqual(fun_name(3, 2), 6)
        # matrix
        la_str = """c = a * A
        where
        a: scalar
        A: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[2, 4], [6, 8]])
        self.assertDMatrixEqual(fun_name(2, A), B)

    def test_solver(self):
        # matrix
        la_str = """y = A \ C 
        where
        A: ℝ ^ (2 × 2): a matrix
        C: ℝ ^ (2 × 2): a matrix """
        fun_name = self.set_up(la_str, None)
        A = np.array([[1, 2], [3, 4]])
        C = np.array([[19, 22], [43, 50]])
        B = np.array([[5., 6.], [7., 8.]])
        B = np.asarray(B, dtype=np.floating)
        self.assertDMatrixEqual(fun_name(A, C), np.linalg.solve(A, C))

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