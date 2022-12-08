import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import scipy
from scipy import sparse
import cppyy
cppyy.add_include_path(eigen_path)


class TestExtraFunction(BasePythonTest):
    def test_func_sub_params(self):
        la_str = """a_m(f) = m+f where f,m ∈ ℤ 
                    c = a(1, 2)
                    """
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func().c, 3)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    int B = {}().c;".format(func_info.eig_func_name),
                     "    return ((B - 3) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_func_sub_params1(self):
        la_str = """a_m(f) = m+f where f,m ∈ ℤ 
                    c = a_1(2)
                    """
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func().c, 3)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    int B = {}().c;".format(func_info.eig_func_name),
                     "    return ((B - 3) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_func_unicode_sub_params(self):
        la_str = """aₘ(f) = m+f where f,m ∈ ℤ 
                    c = a(1, 2)
                    """
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func().c, 3)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    int B = {}().c;".format(func_info.eig_func_name),
                     "    return ((B - 3) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_func_unicode_sub_params1(self):
        la_str = """aₘ(f) = m+f where f,m ∈ ℤ 
                    c = a_1,2
                    """
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func().c, 3)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    int B = {}().c;".format(func_info.eig_func_name),
                     "    return ((B - 3) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_func_overloading(self):
        la_str = """aₘ(f) = f + m  where f,m ∈ ℤ 
                    aₘ(f) = f + m  where f,m ∈ ℝ 
                    c = a(2, 3)
                    """
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func().c, 5)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    int B = {}().c;".format(func_info.eig_func_name),
                     "    return ((B - 5) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_func_overloading_as_param(self):
        la_str = """a  ∈  ℝ ->  ℝ
                    a  ∈  ℤ -> ℤ 
                    b = a(2)
                    """
        func_info = self.gen_func_info(la_str)
        a1 = lambda p: p
        a2 = lambda p: p
        self.assertEqual(func_info.numpy_func(a1, a2).b, 2)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::function<double(double)> a1;"
                     "    a1 = [](double p)->double{"
                     "    return p;"
                     "    };",
                     "    std::function<int(int)> a2;"
                     "    a2 = [](int p)->int{"
                     "    return p;"
                     "    };",
                     "    int B = {}(a1, a2).b;".format(func_info.eig_func_name),
                     "    return ((B - 2) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_func_overloading_in_cpp(self):
        la_str = """aₘ(f) = f where f,m ∈ ℤ^3
                    aₘ(f) = f where f,m ∈ ℤ^(3×1)
                    d = a((1,2,3), (2,3,4))
                    """
        func_info = self.gen_func_info(la_str)
        A = np.array([2, 3, 4])
        self.assertDMatrixEqual(func_info.numpy_func().d, A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<int, 3, 1> P;",
                     "    P << 2, 3, 4;",
                     "    Eigen::Matrix<int, 3, 1> B = {}().d;".format(func_info.eig_func_name),
                     "    return ((B - P).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_func_overloading_mix(self):
        la_str = """aₘ(f) = f + m where f,m ∈ ℤ 
                    a(g,h) = g+h where g,h ∈ ℝ 
                    b = a(2, 3)
                    a ∈  ℝ -> ℝ
                    """
        func_info = self.gen_func_info(la_str)
        a1 = lambda p: p
        self.assertEqual(func_info.numpy_func(a1).b, 5)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::function<double(double)> a1;"
                     "    a1 = [](double p)->double{"
                     "    return p;"
                     "    };",
                     "    int B = {}(a1).b;".format(func_info.eig_func_name),
                     "    return ((B - 5) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_func_overloading_mix1(self):
        la_str = """aₘ(f) = f + m where f,m ∈ ℤ 
                    a(g,h) = g+h where g,h ∈ ℝ 
                    b = a(2, 3)
                    a ∈  ℝ -> ℝ
                    a ∈  ℤ -> ℤ
                    """
        func_info = self.gen_func_info(la_str)
        a1 = lambda p: p
        a2 = lambda p: p
        self.assertEqual(func_info.numpy_func(a1, a2).b, 5)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::function<double(double)> a1;"
                     "    a1 = [](double p)->double{"
                     "    return p;"
                     "    };",
                     "    std::function<int(int)> a2;"
                     "    a2 = [](int p)->int{"
                     "    return p;"
                     "    };",
                     "    int B = {}(a1, a2).b;".format(func_info.eig_func_name),
                     "    return ((B - 5) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_func_set_param(self):
        la_str = """S ∈ {ℤ}
                    f(x) = x where x ∈ S
                    a = f(2)
                    """
        func_info = self.gen_func_info(la_str)
        a1 = [1 , 2, 3]
        self.assertEqual(func_info.numpy_func(a1).a, 2)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::set<int > a1;"
                     "    a1.insert(1);"
                     "    a1.insert(2);"
                     "    a1.insert(3);"
                     "    int B = {}(a1).a;".format(func_info.eig_func_name),
                     "    return ((B - 2) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())