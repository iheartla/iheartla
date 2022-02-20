import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import scipy
from scipy import sparse
import cppyy
cppyy.add_include_path(eigen_path)


class TestDefuse(BasePythonTest):
    def test_def1(self):
        la_str = """a = b
                    b = 1"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func().a, 1)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    double B = {}().a;".format(func_info.eig_func_name),
                     "    return ((B - 1) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_def2(self):
        la_str = """D = B + f(A) 
        B = A+C 
        f(x) = x  where x ∈ ℝ 
        where 
        A ∈ ℝ
        C ∈ ℝ"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(1, 2).D, 4)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    double B = {}(1, 2).D;".format(func_info.eig_func_name),
                     "    return ((B - 4) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())