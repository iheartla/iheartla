import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import scipy
from scipy import sparse
import cppyy
cppyy.add_include_path(eigen_path)


class TestLocalFunction(BasePythonTest):
    def test_local_func_no_param(self):
        la_str = """f(x) = x where x: ℝ ^ (2 × 2)"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[209, 208], [416, 417]])
        self.assertDMatrixEqual(func_info.numpy_func().f(A), A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 209, 208, 416, 417;",
                     "    Eigen::Matrix<double, 2, 2> B = {}().f(A);".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_local_func_where_position(self):
        la_str = """f(x) = x 
                    where x: ℝ ^ (2 × 2)"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[209, 208], [416, 417]])
        self.assertDMatrixEqual(func_info.numpy_func().f(A), A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 209, 208, 416, 417;",
                     "    Eigen::Matrix<double, 2, 2> B = {}().f(A);".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_local_func_same_param(self):
        la_str = """f(x) = x where x: ℝ ^ (2 × 2)
                    where
                    x: ℝ : a scalar"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[209, 208], [416, 417]])
        self.assertDMatrixEqual(func_info.numpy_func(0).f(A), A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 209, 208, 416, 417;",
                     "    Eigen::Matrix<double, 2, 2> B = {}(0).f(A);".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_local_func_conditional(self):
        la_str = """f(x) = {x if x > 0
                           -x otherwise where x: ℝ """
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func().f(-2), 2)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    double B = {}().f(2);".format(func_info.eig_func_name),
                     "    return ((B - 2) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_local_func_seq_param(self):
        la_str = """f(x) = x_1 where x_i: ℝ"""
        func_info = self.gen_func_info(la_str)
        A = np.array([1, 2])
        self.assertEqual(func_info.numpy_func().f(A), 1)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::vector<double> A(2);"
                     "    A[0] = 1;"
                     "    A[1] = 2;"
                     "    double B = {}().f(A);".format(func_info.eig_func_name),
                     "    return ((B - 1) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_local_func_use_global_param(self):
        la_str = """f(x) = x + y where x: ℝ
                    where
                    y: ℝ : a scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(2).f(3), 5)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    double B = {}(2).f(3);".format(func_info.eig_func_name),
                     "    return ((B - 5) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_local_func_use_defined_sym(self):
        la_str = """z = y
                    f(x) = x + z where x: ℝ
                    where
                    y: ℝ : a scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(2).f(3), 5)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    double B = {}(2).f(3);".format(func_info.eig_func_name),
                     "    return ((B - 5) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_local_func_use_defined_sym_unorder(self):
        la_str = """f(x) = x + z where x: ℝ
                    z = y
                    where
                    y: ℝ : a scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(2).f(3), 5)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    double B = {}(2).f(3);".format(func_info.eig_func_name),
                     "    return ((B - 5) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_local_func_real_param_int_arg(self):
        # an integer argument to a real parameter is converted (not integer division, not an int vector)
        la_str = """f(s) = s / 2 where s: ℝ
                    g(v) = 2 v where v: ℝ ^ 3
                    a = f(k)
                    b = g(x)
                    where
                    k: ℤ
                    x: ℤ ^ 3"""
        func_info = self.gen_func_info(la_str)
        res = func_info.numpy_func(3, np.array([1, 2, 3]))
        self.assertEqual(res.a, 1.5)
        self.assertDMatrixEqual(res.b, np.array([2, 4, 6]))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<int, 3, 1> x;",
                     "    x << 1, 2, 3;",
                     "    auto r = {}(3, x);".format(func_info.eig_func_name),
                     "    Eigen::Matrix<double, 3, 1> b;",
                     "    b << 2, 4, 6;",
                     "    return r.a == 1.5 && r.b.isApprox(b);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_local_func_vector_param_expression_arg(self):
        # expression arguments (a lazy Eigen expression, not a Matrix) for a vector parameter
        la_str = """f(x) = x + x where x: ℝ ^ 3
                    a = f(y + y)
                    b = f(2 y)
                    c = f(A y)
                    where
                    y: ℝ ^ 3
                    A: ℝ ^ (3 × 3)"""
        func_info = self.gen_func_info(la_str)
        y = np.array([1, 2, 3])
        A = np.array([[1, 0, 0], [0, 2, 0], [0, 0, 3]])
        res = func_info.numpy_func(y, A)
        self.assertDMatrixEqual(res.a, np.array([4, 8, 12]))
        self.assertDMatrixEqual(res.b, np.array([4, 8, 12]))
        self.assertDMatrixEqual(res.c, np.array([2, 8, 18]))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> y;",
                     "    y << 1, 2, 3;",
                     "    Eigen::Matrix<double, 3, 3> A;",
                     "    A << 1, 0, 0, 0, 2, 0, 0, 0, 3;",
                     "    auto r = {}(y, A);".format(func_info.eig_func_name),
                     "    Eigen::Matrix<double, 3, 1> ab, c;",
                     "    ab << 4, 8, 12;",
                     "    c << 2, 8, 18;",
                     "    return r.a.isApprox(ab) && r.b.isApprox(ab) && r.c.isApprox(c);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())
