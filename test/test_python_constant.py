import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)


class TestConstant(BasePythonTest):
    def test_constant_pi(self):
        # space
        la_str = self.import_trig+"""A = sin(π/a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(2).A, 1)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double([2]))['A']), 1)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(2).A == 1;".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))