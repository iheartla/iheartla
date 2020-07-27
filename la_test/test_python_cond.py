import sys
sys.path.append('./')
from la_test.base_python_test import BasePythonTest, eigen_path, TestFuncInfo
from la_parser.parser import parse_la, ParserTypeEnum
import numpy as np
import scipy
from scipy import sparse
import cppyy
cppyy.add_include_path(eigen_path)


class TestConditions(BasePythonTest):
    def test_cond_gt(self):
        la_str = """Q = A
                Q_ii = sum_(j for j >1 ) Q_ij
                where
                A: ℝ ^ (3 × 3): a matrix"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        P = np.array([[3, 2, 3], [4, 6, 6], [7, 8, 9]])
        self.assertDMatrixEqual(func_info.numpy_func(Q), P)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> Q;",
                     "    Q << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    Eigen::Matrix<double, 3, 3> P;",
                     "    P << 3, 2, 3, 4, 6, 6, 7, 8, 9;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(Q);".format(func_info.eig_func_name),
                     "    return ((C - P).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_cond_ge(self):
        la_str = """Q = A
                Q_ii = sum_(j for j >= 1 ) Q_ij
                where
                A: ℝ ^ (3 × 3): a matrix"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        P = np.array([[5, 2, 3], [4, 11, 6], [7, 8, 17]])
        self.assertDMatrixEqual(func_info.numpy_func(Q), P)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> Q;",
                     "    Q << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    Eigen::Matrix<double, 3, 3> P;",
                     "    P << 5, 2, 3, 4, 11, 6, 7, 8, 17;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(Q);".format(func_info.eig_func_name),
                     "    return ((C - P).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_cond_le(self):
        la_str = """Q = A
                Q_ii = sum_(j for j <= 2 ) Q_ij
                where
                A: ℝ ^ (3 × 3): a matrix"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        P = np.array([[6, 2, 3], [4, 15, 6], [7, 8, 24]])
        self.assertDMatrixEqual(func_info.numpy_func(Q), P)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> Q;",
                     "    Q << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    Eigen::Matrix<double, 3, 3> P;",
                     "    P << 6, 2, 3, 4, 15, 6, 7, 8, 24;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(Q);".format(func_info.eig_func_name),
                     "    return ((C - P).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_cond_lt(self):
        la_str = """Q = A
                Q_ii = sum_(j for j < 2 ) Q_ij
                where
                A: ℝ ^ (3 × 3): a matrix"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        P = np.array([[3, 2, 3], [4, 9, 6], [7, 8, 15]])
        self.assertDMatrixEqual(func_info.numpy_func(Q), P)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> Q;",
                     "    Q << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    Eigen::Matrix<double, 3, 3> P;",
                     "    P << 3, 2, 3, 4, 9, 6, 7, 8, 15;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(Q);".format(func_info.eig_func_name),
                     "    return ((C - P).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_cond_eq(self):
        la_str = """Q = A
                Q_ii = sum_(j for j = 1 ) Q_ij
                where
                A: ℝ ^ (3 × 3): a matrix"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        P = np.array([[2, 2, 3], [4, 5, 6], [7, 8, 8]])
        self.assertDMatrixEqual(func_info.numpy_func(Q), P)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> Q;",
                     "    Q << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    Eigen::Matrix<double, 3, 3> P;",
                     "    P << 2, 2, 3, 4, 5, 6, 7, 8, 8;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(Q);".format(func_info.eig_func_name),
                     "    return ((C - P).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_cond_ineq(self):
        la_str = """Q = A
                Q_ii = sum_(j for j != 1 ) Q_ij
                where
                A: ℝ ^ (3 × 3): a matrix"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        P = np.array([[4, 2, 3], [4, 10, 6], [7, 8, 16]])
        self.assertDMatrixEqual(func_info.numpy_func(Q), P)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> Q;",
                     "    Q << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    Eigen::Matrix<double, 3, 3> P;",
                     "    P << 4, 2, 3, 4, 10, 6, 7, 8, 16;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(Q);".format(func_info.eig_func_name),
                     "    return ((C - P).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())