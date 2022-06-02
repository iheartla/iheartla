import sys
sys.path.append('./')
from test.base_python_test import *
from iheartla.la_parser.parser import parse_la, ParserTypeEnum
import numpy as np
import scipy
from scipy import sparse
import cppyy
cppyy.add_include_path(eigen_path)


class TestConditions(BasePythonTest):
    def test_cond_gt(self):
        la_str = """Q = A
                Q_ii = sum_(j for j >2 ) Q_ij
                where
                A: ℝ ^ (3 × 3): a matrix"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        P = np.array([[3, 2, 3], [4, 6, 6], [7, 8, 9]])
        self.assertDMatrixEqual(func_info.numpy_func(Q).Q, P)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(Q.tolist()))['Q']), P)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> Q;",
                     "    Q << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    Eigen::Matrix<double, 3, 3> P;",
                     "    P << 3, 2, 3, 4, 6, 6, 7, 8, 9;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(Q).Q;".format(func_info.eig_func_name),
                     "    return ((C - P).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_cond_ge(self):
        la_str = """Q = A
                Q_ii = sum_(j for j >= 2 ) Q_ij
                where
                A: ℝ ^ (3 × 3): a matrix"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        P = np.array([[5, 2, 3], [4, 11, 6], [7, 8, 17]])
        self.assertDMatrixEqual(func_info.numpy_func(Q).Q, P)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(Q.tolist()))['Q']), P)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> Q;",
                     "    Q << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    Eigen::Matrix<double, 3, 3> P;",
                     "    P << 5, 2, 3, 4, 11, 6, 7, 8, 17;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(Q).Q;".format(func_info.eig_func_name),
                     "    return ((C - P).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_cond_le(self):
        la_str = """Q = A
                Q_ii = sum_(j for j <= 3 ) Q_ij
                where
                A: ℝ ^ (3 × 3): a matrix"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        P = np.array([[6, 2, 3], [4, 15, 6], [7, 8, 24]])
        self.assertDMatrixEqual(func_info.numpy_func(Q).Q, P)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(Q.tolist()))['Q']), P)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> Q;",
                     "    Q << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    Eigen::Matrix<double, 3, 3> P;",
                     "    P << 6, 2, 3, 4, 15, 6, 7, 8, 24;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(Q).Q;".format(func_info.eig_func_name),
                     "    return ((C - P).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_cond_lt(self):
        la_str = """Q = A
                Q_ii = sum_(j for j < 3 ) Q_ij
                where
                A: ℝ ^ (3 × 3): a matrix"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        P = np.array([[3, 2, 3], [4, 9, 6], [7, 8, 15]])
        self.assertDMatrixEqual(func_info.numpy_func(Q).Q, P)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(Q.tolist()))['Q']), P)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> Q;",
                     "    Q << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    Eigen::Matrix<double, 3, 3> P;",
                     "    P << 3, 2, 3, 4, 9, 6, 7, 8, 15;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(Q).Q;".format(func_info.eig_func_name),
                     "    return ((C - P).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_cond_eq(self):
        la_str = """Q = A
                Q_ii = sum_(j for j = 2 ) Q_ij
                where
                A: ℝ ^ (3 × 3): a matrix"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        P = np.array([[2, 2, 3], [4, 5, 6], [7, 8, 8]])
        self.assertDMatrixEqual(func_info.numpy_func(Q).Q, P)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(Q.tolist()))['Q']), P)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> Q;",
                     "    Q << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    Eigen::Matrix<double, 3, 3> P;",
                     "    P << 2, 2, 3, 4, 5, 6, 7, 8, 8;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(Q).Q;".format(func_info.eig_func_name),
                     "    return ((C - P).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_cond_ineq(self):
        la_str = """Q = A
                Q_ii = sum_(j for j != 2 ) Q_ij
                where
                A: ℝ ^ (3 × 3): a matrix"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        P = np.array([[4, 2, 3], [4, 10, 6], [7, 8, 16]])
        self.assertDMatrixEqual(func_info.numpy_func(Q).Q, P)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(Q.tolist()))['Q']), P)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> Q;",
                     "    Q << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    Eigen::Matrix<double, 3, 3> P;",
                     "    P << 4, 2, 3, 4, 10, 6, 7, 8, 16;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(Q).Q;".format(func_info.eig_func_name),
                     "    return ((C - P).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_and_cond(self):
        la_str = """A = sum_(j for j > 2 and j < 5 ) Q_j
                where
                Q: ℝ ^ 5"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([1, 2, 3, 4, 5])
        self.assertEqual(func_info.numpy_func(Q).A, 7)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(mat_func(matlab.double(Q.tolist()))['A'], 7)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 5, 1> Q;",
                     "    Q << 1, 2, 3, 4, 5;",
                     "    double C = {}(Q).A;".format(func_info.eig_func_name),
                     "    return ((C - 7) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_or_cond(self):
        la_str = """A = sum_(j for j < 2 or j > 3 ) Q_j
                where
                Q: ℝ ^ 5"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([1, 2, 3, 4, 5])
        self.assertEqual(func_info.numpy_func(Q).A, 10)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(mat_func(matlab.double(Q.tolist()))['A'], 10)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 5, 1> Q;",
                     "    Q << 1, 2, 3, 4, 5;",
                     "    double C = {}(Q).A;".format(func_info.eig_func_name),
                     "    return ((C - 10) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_combined_priority_cond(self):
        la_str = """A = sum_(j for j > 2 and j < 4 or j > 4 ) Q_j
                where
                Q: ℝ ^ 5"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([1, 2, 3, 4, 5])
        self.assertEqual(func_info.numpy_func(Q).A, 8)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(mat_func(matlab.double(Q.tolist()))['A'], 8)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 5, 1> Q;",
                     "    Q << 1, 2, 3, 4, 5;",
                     "    double C = {}(Q).A;".format(func_info.eig_func_name),
                     "    return ((C - 8) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_combined_priority_cond2(self):
        la_str = """A = sum_(j for j > 2 or j < 4 and j > 4 ) Q_j
                where
                Q: ℝ ^ 5"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([1, 2, 3, 4, 5])
        self.assertEqual(func_info.numpy_func(Q).A, 12)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(mat_func(matlab.double(Q.tolist()))['A'], 12)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 5, 1> Q;",
                     "    Q << 1, 2, 3, 4, 5;",
                     "    double C = {}(Q).A;".format(func_info.eig_func_name),
                     "    return ((C - 12) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_combined_priority_cond3(self):
        la_str = """A = sum_(j for (j > 2 or j > 3) and j > 4 ) Q_j
                where
                Q: ℝ ^ 5"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([1, 2, 3, 4, 5])
        self.assertEqual(func_info.numpy_func(Q).A, 5)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(mat_func(matlab.double(Q.tolist()))['A'], 5)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 5, 1> Q;",
                     "    Q << 1, 2, 3, 4, 5;",
                     "    double C = {}(Q).A;".format(func_info.eig_func_name),
                     "    return ((C - 5) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())