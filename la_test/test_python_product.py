import sys
sys.path.append('./')
from la_test.base_python_test import BasePythonTest, eigen_path, TestFuncInfo
from la_parser.parser import parse_la, ParserTypeEnum
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)


class TestProduct(BasePythonTest):
    def test_inner_product(self):
        la_str = """A = <T , P>
                    where 
                    T: ℝ ^ 3: a sequence
                    P: ℝ ^ 3: a sequence """
        func_info = self.gen_func_info(la_str)
        T = np.array([1, 2, 3])
        P = np.array([4, 5, 6])
        self.assertEqual(func_info.numpy_func(T, P), 32)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> T;",
                     "    T << 1, 2, 3;",
                     "    Eigen::Matrix<double, 3, 1> P;",
                     "    P << 4, 5, 6;",
                     "    double B = {}(T, P);".format(func_info.eig_func_name),
                     "    return (B == 32);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_inner_product_subscript(self):
        la_str = """A = <T , P>_M
                    where 
                    T: ℝ ^ 2: a sequence
                    P: ℝ ^ 2: a sequence 
                    M: ℝ ^ (2×2): a sequence"""
        func_info = self.gen_func_info(la_str)
        T = np.array([1, 2])
        P = np.array([3, 4])
        M = np.array([[5, 6], [7, 8]])
        self.assertEqual(func_info.numpy_func(T, P, M), 143)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 1> T;",
                     "    T << 1, 2;",
                     "    Eigen::Matrix<double, 2, 1> P;",
                     "    P << 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> M;",
                     "    M << 5, 6, 7, 8;",
                     "    double B = {}(T, P, M);".format(func_info.eig_func_name),
                     "    return (B == 143);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_frobenius_product(self):
        la_str = """A = T : P
                    where 
                    T: ℝ ^ (2×2): a sequence
                    P: ℝ ^ (2×2): a sequence"""
        func_info = self.gen_func_info(la_str)
        T = np.array([[1, 2], [3, 4]])
        P = np.array([[5, 6], [7, 8]])
        self.assertEqual(func_info.numpy_func(T, P), 70)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> T;",
                     "    T << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 5, 6, 7, 8;",
                     "    double B = {}(T, P);".format(func_info.eig_func_name),
                     "    return (B == 70);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_hadamard_product(self):
        la_str = """A = T ○ P
                    where 
                    T: ℝ ^ (2×2): a sequence
                    P: ℝ ^ (2×2): a sequence"""
        func_info = self.gen_func_info(la_str)
        T = np.array([[1, 2], [3, 4]])
        P = np.array([[5, 6], [7, 8]])
        A = np.array([[5, 12], [21, 32]])
        self.assertDMatrixEqual(func_info.numpy_func(T, P), A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> T;",
                     "    T << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 5, 6, 7, 8;",
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 5, 12, 21, 32;",
                     "   Eigen::Matrix<double, 2, 2> B = {}(T, P);".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_cross_product(self):
        la_str = """A = T × P
                    where 
                    T: ℝ ^ 3: a sequence
                    P: ℝ ^ 3: a sequence """
        func_info = self.gen_func_info(la_str)
        T = np.array([1, 2, 3])
        P = np.array([4, 5, 6])
        A = np.array([-3, 6, -3])
        self.assertDMatrixEqual(func_info.numpy_func(T, P), A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> T;",
                     "    T << 1, 2, 3;",
                     "    Eigen::Matrix<double, 3, 1> P;",
                     "    P << 4, 5, 6;",
                     "    Eigen::Matrix<double, 3, 1> A;",
                     "    A << -3, 6, -3;",
                     "   Eigen::Matrix<double, 3, 1> B = {}(T, P);".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_kronecker_product(self):
        la_str = """A = T ⨂ P
                    where 
                    T: ℝ ^ (2×2): a sequence
                    P: ℝ ^ (2×2): a sequence"""
        func_info = self.gen_func_info(la_str)
        T = np.array([[1, 2], [3, 4]])
        P = np.array([[5, 6], [7, 8]])
        A = np.array([[5, 6, 10, 12], [7, 8, 14, 16], [15, 18, 20, 24], [21, 24, 28, 32]])
        self.assertDMatrixEqual(func_info.numpy_func(T, P), A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> T;",
                     "    T << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 5, 6, 7, 8;",
                     "    Eigen::Matrix<double, 4, 4> A;",
                     "    A << 5, 6, 10, 12, 7, 8, 14, 16, 15, 18, 20, 24, 21, 24, 28, 32;",
                     "   Eigen::Matrix<double, 4, 4> B = {}(T, P);".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_dot_product(self):
        la_str = """A = T ⋅ P
                    where 
                    T: ℝ ^ 3: a sequence
                    P: ℝ ^ 3: a sequence """
        func_info = self.gen_func_info(la_str)
        T = np.array([1, 2, 3])
        P = np.array([4, 5, 6])
        self.assertEqual(func_info.numpy_func(T, P), 32)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> T;",
                     "    T << 1, 2, 3;",
                     "    Eigen::Matrix<double, 3, 1> P;",
                     "    P << 4, 5, 6;",
                     "    double B = {}(T, P);".format(func_info.eig_func_name),
                     "    return (B == 32);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())