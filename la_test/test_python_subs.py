import sys
sys.path.append('./')
from la_test.base_python_test import BasePythonTest
from la_parser.parser import parse_la, ParserTypeEnum
import numpy as np


class TestSubscript(BasePythonTest):
    def test_subscript(self):
        # sequence
        la_str = """B_i = A_i
        where
        A_i: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[[1, 2], [4, 3]], [[1, 2], [4, 3]]])
        self.assertDMatrixEqual(fun_name(A), A)

        # matrix
        la_str = """B_ij = A_ij A_ij
        where
        A: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[1, 2], [4, 3]])
        B = np.array([[1, 4], [16, 9]])
        self.assertDMatrixEqual(fun_name(A), B)

    def test_summation(self):
        # simple version
        la_str = """B = sum_i A_i
        where
        A_i: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[[1, 2], [4, 3]], [[1, 2], [4, 3]]])
        B = np.array([[2, 4], [8, 6]])
        self.assertDMatrixEqual(fun_name(A), B)

        # simple version: different subscript
        la_str = """B = sum_j A_j
        where
        A_i: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[[1, 2], [4, 3]], [[1, 2], [4, 3]]])
        B = np.array([[2, 4], [8, 6]])
        self.assertDMatrixEqual(fun_name(A), B)

        # multiple operands: Add
        la_str = """C = sum_i A_i + B_i
        where
        A_i: ℝ ^ (2 × 2): a matrix
        B_i: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[[1, 2], [4, 3]], [[1, 2], [4, 3]]])
        B = np.array([[4, 8], [16, 12]])
        self.assertDMatrixEqual(fun_name(A, A), B)

        # multiple operands: Mul
        la_str = """C = sum_i A_i B_i
        where
        A_i: ℝ ^ (2 × 2): a matrix
        B_i: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[[1, 2], [4, 3]], [[1, 2], [4, 3]]])
        B = np.array([[[1, 0], [0, 1]], [[1, 0], [0, 1]]])
        C = np.array([[2, 4], [8, 6]])
        self.assertDMatrixEqual(fun_name(A, B), C)

    def test_nested_summation(self):
        # nested
        la_str = """C = sum_i A_i sum_j w_j
        where
        w_j: scalar: a scalar
        A_i: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        w = np.array([1, 1, 2, 2])
        A = np.array([[[1, 2], [4, 3]], [[1, 2], [4, 3]]])
        B = np.array([[12, 24], [48, 36]])
        self.assertDMatrixEqual(fun_name(w, A), B)

        # special
        la_str = """C = sum_i A_i sum_j w_j A_i
        where
        w_j: scalar: a scalar
        A_i: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        w = np.array([1, 1, 2, 2])
        A = np.array([[[1, 2], [4, 3]], [[1, 2], [4, 3]]])
        B = np.array([[108, 96], [192, 204]])
        self.assertDMatrixEqual(fun_name(w, A), B)

    def test_conditional_summation(self):
        # if condition
        la_str = """Q_ii = sum_(j for j ≠ i ) Q_ij
        where
        Q: ℝ ^ (3 × 3): a matrix"""
        fun_name = self.set_up(la_str, None)
        Q = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        P = np.array([[5, 2, 3], [4, 10, 6], [7, 8, 15]])
        self.assertDMatrixEqual(fun_name(Q), P)