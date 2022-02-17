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