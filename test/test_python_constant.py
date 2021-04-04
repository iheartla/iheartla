import sys
sys.path.append('./')
from test.base_python_test import BasePythonTest, eigen_path
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
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(2).A == 1;".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))