import sys
sys.path.append('./')
from test.base_python_test import BasePythonTest, eigen_path
import numpy as np
import scipy
from scipy import sparse
import cppyy
cppyy.add_include_path(eigen_path)


class TestFunction(BasePythonTest):
    def test_func_no_param(self):
        la_str = """A = Pf()P(P)
                    where 
                    P: ℝ ^ (2 × 2): a matrix 
                    f: {} -> ℝ^(2 × 2): a function"""
        func_info = self.gen_func_info(la_str)
        P = np.array([[1, 2], [4, 3]])
        f = lambda : np.array([[1, 2], [4, 3]])
        A = np.array([[209, 208], [416, 417]])
        self.assertDMatrixEqual(func_info.numpy_func(P, f).A, A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 209, 208, 416, 417;",
                     "    std::function<Eigen::Matrix<double, 2, 2>()> f = []()->Eigen::Matrix<double, 2, 2>{",
                     "        Eigen::Matrix<double, 2, 2> ret;",
                     "        ret << 1, 2, 4, 3;",
                     "    return ret;"
                     "    };",
                     "    Eigen::Matrix<double, 2, 2> B = {}(P, f).A;".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_func_param_types_matrix(self):
        la_str = """A = Pf(P)
                    where 
                    P: ℝ ^ (2 × 2): a matrix 
                    f: ℝ^(2 × 2) -> ℝ^(2 × 2): a function """
        func_info = self.gen_func_info(la_str)
        P = np.array([[1, 2], [4, 3]])
        f = lambda p : p+p
        A = np.array([[18, 16], [32, 34]])
        self.assertDMatrixEqual(func_info.numpy_func(P, f).A, A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 18, 16, 32, 34;",
                     "    std::function<Eigen::Matrix<double, 2, 2>(Eigen::Matrix<double, 2, 2>)> f;"
                     "    f = [](Eigen::Matrix<double, 2, 2> p)->Eigen::Matrix<double, 2, 2>{",
                     "    return p + p;"
                     "    };",
                     "    Eigen::Matrix<double, 2, 2> B = {}(P, f).A;".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_func_param_types_vector(self):
        la_str = """A = Q f(P)
                    where 
                    P: ℝ ^ 2: a matrix 
                    Q: ℝ ^(2×2): a matrix 
                    f: ℝ^(2) -> ℝ^(2 × 2): a function"""
        func_info = self.gen_func_info(la_str)
        P = np.array([1, 4])
        # P.reshape((2, 1))
        Q = np.array([[1, 2], [4, 3]])
        # f = lambda p : np.hstack((p, p))
        f = lambda p: [[1, 1], [4, 4]]
        A = np.array([[9, 9], [16, 16]])
        self.assertDMatrixEqual(func_info.numpy_func(P, Q, f).A, A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 1> P;",
                     "    P << 1, 4;",
                     "    Eigen::Matrix<double, 2, 2> Q;",
                     "    Q << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 9, 9, 16, 16;",
                     "    std::function<Eigen::Matrix<double, 2, 2>(Eigen::Matrix<double, 2, 1>)> f;"
                     "    f = [](Eigen::Matrix<double, 2, 1> p)->Eigen::Matrix<double, 2, 2>{"
                     "    Eigen::Matrix<double, 2, 2> ret;"
                     "    ret << p, p;",
                     "    return ret;"
                     "    };",
                     "    Eigen::Matrix<double, 2, 2> B = {}(P, Q, f).A;".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_func_param_types_scalar(self):
        la_str = """A = P f(2)
                    where 
                    P: ℝ ^(2×2): a matrix 
                    f: scalar -> ℝ^(2 × 2): a function"""
        func_info = self.gen_func_info(la_str)
        P = np.array([[1, 2], [4, 3]])
        def f(p):
            ret = np.zeros((2, 2))
            ret[0] = [p, p]
            ret[1] = [p, p]
            return ret
        A = np.array([[6, 6], [14, 14]])
        self.assertDMatrixEqual(func_info.numpy_func(P, f).A, A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 6, 6, 14, 14;",
                     "    std::function<Eigen::Matrix<double, 2, 2>(double)> f;"
                     "    f = [](double p)->Eigen::Matrix<double, 2, 2>{"
                     "    Eigen::Matrix<double, 2, 2> ret;"
                     "    ret << p, p, p, p;",
                     "    return ret;"
                     "    };",
                     "    Eigen::Matrix<double, 2, 2> B = {}(P, f).A;".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_func_multi_params(self):
        la_str = """A = P f(2, 3)
                    where 
                    P: ℝ ^(2×2): a matrix 
                    f: scalar, scalar -> ℝ^(2 × 2): a function"""
        func_info = self.gen_func_info(la_str)
        P = np.array([[1, 2], [4, 3]])
        def f(p, q):
            ret = np.zeros((2, 2))
            ret[0] = [p, p]
            ret[1] = [q, q]
            return ret
        A = np.array([[8, 8], [17, 17]])
        self.assertDMatrixEqual(func_info.numpy_func(P, f).A, A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 8, 8, 17, 17;",
                     "    std::function<Eigen::Matrix<double, 2, 2>(double, double)> f;"
                     "    f = [](double p, double q)->Eigen::Matrix<double, 2, 2>{"
                     "    Eigen::Matrix<double, 2, 2> ret;"
                     "    ret << p, p, q, q;",
                     "    return ret;"
                     "    };",
                     "    Eigen::Matrix<double, 2, 2> B = {}(P, f).A;".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_func_ret_types_vector(self):
        la_str = """A = P f(2)
                    where 
                    P: ℝ ^(2×2): a matrix 
                    f: scalar -> ℝ^(2 ): a function"""
        func_info = self.gen_func_info(la_str)
        P = np.array([[1, 2], [4, 3]])
        def f(p):
            ret = np.array([[p], [p]])
            ret.reshape((2, 1))
            return ret
        A = np.array([[6], [14]])
        self.assertDMatrixEqual(func_info.numpy_func(P, f).A, A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 1> A;",
                     "    A << 6, 14;",
                     "    std::function<Eigen::Matrix<double, 2, 1>(double)> f;",
                     "    f = [](double p)->Eigen::Matrix<double, 2, 1>{",
                     "    Eigen::Matrix<double, 2, 1> ret;",
                     "    ret << p, p;",
                     "    return ret;",
                     "    };",
                     "    Eigen::Matrix<double, 2, 1> B = {}(P, f).A;".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_func_ret_types_scalar(self):
        la_str = """A = P f(2)
                    where 
                    P: ℝ ^(2×2): a matrix 
                    f: scalar -> ℤ: a function"""
        func_info = self.gen_func_info(la_str)
        P = np.array([[1, 2], [4, 3]])
        f = lambda p : int(p)
        A = np.array([[2, 4], [8, 6]])
        self.assertDMatrixEqual(func_info.numpy_func(P, f).A, A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 2, 4, 8, 6;",
                     "    std::function<int(double)> f;",
                     "    f = [](double p)->int{",
                     "    return int(p);",
                     "    };",
                     "    Eigen::Matrix<double, 2, 2> B = {}(P, f).A;".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_nested_func(self):
        la_str = """A = Pf(g()P)P
                    where 
                    P: ℝ ^ (2 × 2): a matrix 
                    f: ℝ^(2 × 2) -> ℝ^(2 × 2): a function
                    g: {} -> ℝ^(2 × 2): a function """
        func_info = self.gen_func_info(la_str)
        P = np.array([[1, 2], [4, 3]])
        f = lambda p : p+p
        g = lambda : np.array([[1, 0], [0, 1]])
        A = np.array([[82, 84], [168, 166]])
        self.assertDMatrixEqual(func_info.numpy_func(P, f, g).A, A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 82, 84, 168, 166;",
                     "    std::function<Eigen::Matrix<double, 2, 2>(Eigen::Matrix<double, 2, 2>)> f;"
                     "    f = [](Eigen::Matrix<double, 2, 2> p)->Eigen::Matrix<double, 2, 2>{",
                     "    return p + p;"
                     "    };",
                     "    std::function<Eigen::Matrix<double, 2, 2>()> g = []()->Eigen::Matrix<double, 2, 2>{",
                     "        Eigen::Matrix<double, 2, 2> ret;",
                     "        ret << 1, 0, 0, 1;",
                     "    return ret;"
                     "    };",
                     "    Eigen::Matrix<double, 2, 2> B = {}(P, f, g).A;".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_recursive_func(self):
        la_str = """A = Pf(P+f(f(P⋅P))P)
                    where 
                    P: ℝ ^ (2 × 2): a matrix 
                    f: ℝ^(2 × 2) -> ℝ^(2 × 2): a function"""
        func_info = self.gen_func_info(la_str)
        P = np.array([[1, 2], [4, 3]])
        f = lambda p : p+p
        A = np.array([[1690, 1680], [3360, 3370]])
        self.assertDMatrixEqual(func_info.numpy_func(P, f).A, A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1690, 1680, 3360, 3370;",
                     "    std::function<Eigen::Matrix<double, 2, 2>(Eigen::Matrix<double, 2, 2>)> f;"
                     "    f = [](Eigen::Matrix<double, 2, 2> p)->Eigen::Matrix<double, 2, 2>{",
                     "    return p + p;"
                     "    };",
                     "    Eigen::Matrix<double, 2, 2> B = {}(P, f).A;".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())