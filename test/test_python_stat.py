import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)


class TestStat(BasePythonTest):
    def test_return_value(self):
        # no return symbol
        la_str = """a b
        where
        a: scalar
        b: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3, 2).ret, 6)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(3, 2)['ret']), 6)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    if({}(3, 2).ret == 6){{".format(func_info.eig_func_name),
                     "        return true;",
                     "    }",
                     "    return false;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_no_where_block(self):
        la_str = """A = 2 + 3"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func().A, 5)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func()['A']), 5)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    double B = {}().A;".format(func_info.eig_func_name),
                     "    return (B == 5);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_interleaved_stat(self):
        la_str = """A: ℝ^(n×n)
        a = A_1,1
        n: ℤ"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[2, 5], [0, 12]])
        self.assertEqual(func_info.numpy_func(A, 2).a, 2)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()), 2)['a']), 2)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 2, 5, 0, 12;",
                     "    double B = {}(A, 2).a;".format(func_info.eig_func_name),
                     "    return (B == 2);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())
