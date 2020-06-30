import sys
sys.path.append('./')
from la_test.base_python_test import BasePythonTest, eigen_path, TestFuncInfo
from la_parser.parser import parse_la, ParserTypeEnum
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)


class TestBuiltinFunctions(BasePythonTest):
    def test_builtin_sin(self):
        # space
        la_str = """b = sin(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3), np.sin(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3) == sin(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_cos(self):
        # space
        la_str = """b = cos(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3), np.cos(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3) == cos(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_asin_0(self):
        # space
        la_str = """b = asin(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(0.4), np.arcsin(0.4))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(0.4) == asin(0.4);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_asin_1(self):
        # space
        la_str = """b = arcsin(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(0.4), np.arcsin(0.4))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(0.4) == asin(0.4);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_acos_0(self):
        # space
        la_str = """b = acos(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(0.4), np.arccos(0.4))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(0.4) == acos(0.4);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_acos_1(self):
        # space
        la_str = """b = arccos(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(0.4), np.arccos(0.4))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(0.4) == acos(0.4);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_tan(self):
        # space
        la_str = """b = tan(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3), np.tan(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3) == tan(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_arctan_0(self):
        # space
        la_str = """b = atan(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3), np.arctan(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3) == atan(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_arctan_1(self):
        # space
        la_str = """b = arctan(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3), np.arctan(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3) == atan(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_arctan2(self):
        # space
        la_str = """c = atan2(a, b)
        where
        a: scalar
        b: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3, 2), np.arctan2(3, 2))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3, 2) == atan2(3, 2);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_exp(self):
        # space
        la_str = """b = exp(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3), np.exp(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3) == exp(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_log(self):
        # space
        la_str = """b = log(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3), np.log10(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3) == log10(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_ln(self):
        # space
        la_str = """b = ln(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3), np.log(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3) == log(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_sqrt(self):
        # space
        la_str = """b = sqrt(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3), np.sqrt(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3) == sqrt(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))