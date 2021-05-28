import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import scipy
from scipy import sparse
import cppyy
cppyy.add_include_path(eigen_path)


class TestBuiltinFunctions(BasePythonTest):
    def test_builtin_sin(self):
        # space
        la_str = self.import_trig+"""b = sin(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, np.sin(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3).b == sin(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_cos(self):
        # space
        la_str = self.import_trig+"""b = cos(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, np.cos(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3).b == cos(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_asin_0(self):
        # space
        la_str = self.import_trig+"""b = asin(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(0.4).b, np.arcsin(0.4))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(0.4).b == asin(0.4);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_asin_1(self):
        # space
        la_str = self.import_trig+"""b = arcsin(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(0.4).b, np.arcsin(0.4))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(0.4).b == asin(0.4);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_acos_0(self):
        # space
        la_str = self.import_trig+"""b = acos(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(0.4).b, np.arccos(0.4))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(0.4).b == acos(0.4);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_acos_1(self):
        # space
        la_str = self.import_trig+"""b = arccos(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(0.4).b, np.arccos(0.4))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(0.4).b == acos(0.4);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_tan(self):
        # space
        la_str = self.import_trig+"""b = tan(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, np.tan(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3).b == tan(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_arctan_0(self):
        # space
        la_str = self.import_trig+"""b = atan(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, np.arctan(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3).b == atan(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_arctan_1(self):
        # space
        la_str = self.import_trig+"""b = arctan(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, np.arctan(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3).b == atan(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_arctan2(self):
        # space
        la_str = self.import_trig+"""c = atan2(a, b)
        where
        a: scalar
        b: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3, 2).c, np.arctan2(3, 2))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3, 2).c == atan2(3, 2);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_sinh(self):
        # space
        la_str = self.import_trig+"""b = sinh(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, np.sinh(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3).b == sinh(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_asinh(self):
        # space
        la_str = self.import_trig+"""b = asinh(a) + arsinh(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, 2*np.arcsinh(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3).b == 2*asinh(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_cosh(self):
        # space
        la_str = self.import_trig+"""b = cosh(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, np.cosh(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3).b == cosh(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_acosh(self):
        # space
        la_str = self.import_trig+"""b = acosh(a) + arcosh(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, 2*np.arccosh(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3).b == 2*acosh(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_tanh(self):
        # space
        la_str = self.import_trig+"""b = tanh(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, np.tanh(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3).b == tanh(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_atanh(self):
        # space
        la_str = self.import_trig+"""b = atanh(a) + artanh(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(0.3).b, 2*np.arctanh(0.3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(0.3).b == 2*atanh(0.3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_cot(self):
        # space
        la_str = self.import_trig+"""b = cot(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, 1/np.tan(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3).b == 1/tan(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_sec(self):
        # space
        la_str = self.import_trig+"""b = sec(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, 1/np.cos(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3).b == 1/cos(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_csc(self):
        # space
        la_str = self.import_trig+"""b = csc(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, 1/np.sin(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3).b == 1/sin(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_trig_matrix_sin(self):
        # space
        la_str = self.import_trig+"""A = sin(T)
        where
        T: ℝ ^ (2×2): a sequence"""
        func_info = self.gen_func_info(la_str)
        T = np.array([[1, 2], [3, 4]])
        self.assertDMatrixEqual(func_info.numpy_func(T).A, np.sin(T))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> T;",
                     "    T << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> B = {}(T).A;".format(func_info.eig_func_name),
                     "    return ((B - T.unaryExpr<double(*)(double)>(&std::sin)).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_trig_matrix_cot(self):
        # space
        la_str = self.import_trig+"""A = cot(T)
        where
        T: ℝ ^ (2×2): a sequence"""
        func_info = self.gen_func_info(la_str)
        T = np.array([[1, 2], [3, 4]])
        self.assertDMatrixEqual(func_info.numpy_func(T).A, 1/np.tan(T))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> T;",
                     "    T << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> B = {}(T).A;".format(func_info.eig_func_name),
                     "    return ((B - T.unaryExpr<double(*)(double)>(&std::tan).cwiseInverse()).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_trig_power(self):
        # space
        la_str = self.import_trig+"""b = asin^2(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(0.4).b, np.power(np.arcsin(0.4), 2))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(0.4).b == pow(asin(0.4), 2);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_exp(self):
        # space
        la_str = self.import_trig+"""b = exp(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, np.exp(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3).b == exp(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_log(self):
        # space
        la_str = """b = log(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, np.log(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3).b == log(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_ln(self):
        # space
        la_str = """b = ln(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, np.log(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3).b == log(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))

    def test_builtin_sqrt(self):
        # space
        la_str = """b = sqrt(a)
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, np.sqrt(3))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(3).b == sqrt(3);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))