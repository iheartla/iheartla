import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import scipy
from scipy import sparse
import cppyy
cppyy.add_include_path(eigen_path)


class TestNorm(BasePythonTest):
    def test_scalar_norm(self):
        la_str = """A = |a|
                    where 
                    a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(-2).A, 2)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(-2)['A']), 2)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    double B = {}(-2).A;".format(func_info.eig_func_name),
                     "    return (B == 2);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_vector_norm_0(self):
        la_str = """A = ||T||_0
                    where 
                    T: ℝ ^ 2: vector"""
        func_info = self.gen_func_info(la_str)
        A = np.array([1, 3])
        B = np.array([1, 0])
        self.assertEqual(func_info.numpy_func(A).A, 2)
        self.assertEqual(func_info.numpy_func(B).A, 1)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            # self.assertEqual(np.array(mat_func(matlab.double(A.tolist()))['A']), 2)
            # self.assertEqual(np.array(mat_func(matlab.double(B.tolist()))['A']), 1)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 1> A;",
                     "    A << 1, 3;",
                     "    Eigen::Matrix<double, 2, 1> B;",
                     "    B << 1, 0;",
                     "    double C = {}(A).A;".format(func_info.eig_func_name),
                     "    double D = {}(B).A;".format(func_info.eig_func_name),
                     "    return (C == 2 && D == 1);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_vector_norm_1(self):
        la_str = """A = ||T||_1
                    where 
                    T: ℝ ^ 2: vector"""
        func_info = self.gen_func_info(la_str)
        A = np.array([1, 2])
        self.assertEqual(func_info.numpy_func(A).A, 3)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()))['A']), 3)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 1> A;",
                     "    A << 1, 2;",
                     "    double B = {}(A).A;".format(func_info.eig_func_name),
                     "    return (B == 3);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_vector_norm_default(self):
        la_str = """A = ||T||
                    where 
                    T: ℝ ^ 3: vector"""
        func_info = self.gen_func_info(la_str)
        A = np.array([3, 4, 12])
        self.assertEqual(func_info.numpy_func(A).A, 13)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()))['A']), 13)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> A;",
                     "    A << 3, 4, 12;",
                     "    double B = {}(A).A;".format(func_info.eig_func_name),
                     "    return (B == 13);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_vector_norm_2(self):
        la_str = """A = ||T||_2
                    where 
                    T: ℝ ^ 3: vector"""
        func_info = self.gen_func_info(la_str)
        A = np.array([3, 4, 12])
        self.assertEqual(func_info.numpy_func(A).A, 13)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()))['A']), 13)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> A;",
                     "    A << 3, 4, 12;",
                     "    double B = {}(A).A;".format(func_info.eig_func_name),
                     "    return (B == 13);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_vector_norm_3(self):
        la_str = """A = ||T||_3
                    where 
                    T: ℝ ^ 4: vector"""
        func_info = self.gen_func_info(la_str)
        A = np.array([3, 0, 0, 0])
        self.assertEqual(func_info.numpy_func(A).A, 3)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()))['A']), 3)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 4, 1> A;",
                     "    A << 3, 0, 0, 0;",
                     "    double B = {}(A).A;".format(func_info.eig_func_name),
                     "    return (B == 3);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_vector_norm_id(self):
        la_str = """A = ||T||_a
                    where 
                    a: scalar
                    T: ℝ ^ 4: vector"""
        func_info = self.gen_func_info(la_str)
        A = np.array([5, 0, 12, 0])
        self.assertEqual(func_info.numpy_func(2, A).A, 13)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(2, matlab.double(A.tolist()))['A']), 13)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 4, 1> A;",
                     "    A << 5, 0, 12, 0;",
                     "    double B = {}(2, A).A;".format(func_info.eig_func_name),
                     "    return (B == 13);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_vector_norm_max(self):
        la_str = """A = ||T||_∞
                    where 
                    T: ℝ ^ 4: vector"""
        func_info = self.gen_func_info(la_str)
        A = np.array([-3, 10, 120, 0])
        self.assertEqual(func_info.numpy_func(A).A, 120)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()))['A']), 120)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 4, 1> A;",
                     "    A << -3, 10, 120, 0;",
                     "    double B = {}(A).A;".format(func_info.eig_func_name),
                     "    return (B == 120);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_vector_norm_matrix(self):
        la_str = """A = ||T||_P
                    where 
                    T: ℝ ^ 2: a sequence
                    P: ℝ ^ (2×2): a sequence"""
        func_info = self.gen_func_info(la_str)
        A = np.array([-5, 12])
        P = np.array([[1, 0], [0, 1]])
        self.assertEqual(func_info.numpy_func(A, P).A, 13)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()), matlab.double(P.tolist()))['A']), 13)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 1> A;",
                     "    A << -5, 12;",
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 1, 0, 0, 1;",
                     "    double B = {}(A, P).A;".format(func_info.eig_func_name),
                     "    return (B == 13);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_matrix_default(self):
        la_str = """A = ||T||
                    where 
                    T: ℝ ^ (2×2): matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[0, 5], [0, 12]])
        self.assertEqual(func_info.numpy_func(A).A, 13)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()))['A']), 13)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 0, 5, 0, 12;",
                     "    double B = {}(A).A;".format(func_info.eig_func_name),
                     "    return (B == 13);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_matrix_frobenius(self):
        la_str = """A = ||T||_F
                    where 
                    T: ℝ ^ (2×2): matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[0, 5], [0, 12]])
        self.assertEqual(func_info.numpy_func(A).A, 13)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()))['A']), 13)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 0, 5, 0, 12;",
                     "    double B = {}(A).A;".format(func_info.eig_func_name),
                     "    return (B == 13);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_matrix_frobenius1(self):
        la_str = """A = ||T||_F²
                    where 
                    T: ℝ ^ (2×2): matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[0, 5], [0, 12]])
        self.assertEqual(func_info.numpy_func(A).A, 169)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()))['A']), 169)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 0, 5, 0, 12;",
                     "    double B = {}(A).A;".format(func_info.eig_func_name),
                     "    return (B == 169);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_matrix_frobenius2(self):
        la_str = """A = ||T||_F^2
                    where 
                    T: ℝ ^ (2×2): matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[0, 5], [0, 12]])
        self.assertEqual(func_info.numpy_func(A).A, 169)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()))['A']), 169)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 0, 5, 0, 12;",
                     "    double B = {}(A).A;".format(func_info.eig_func_name),
                     "    return (B == 169);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_matrix_frobenius3(self):
        la_str = """A = ||T||^2_F
                    where 
                    T: ℝ ^ (2×2): matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[0, 5], [0, 12]])
        self.assertEqual(func_info.numpy_func(A).A, 169)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()))['A']), 169)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 0, 5, 0, 12;",
                     "    double B = {}(A).A;".format(func_info.eig_func_name),
                     "    return (B == 169);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_matrix_frobenius4(self):
        la_str = """A = ||T||²_F
                    where 
                    T: ℝ ^ (2×2): matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[0, 5], [0, 12]])
        self.assertEqual(func_info.numpy_func(A).A, 169)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()))['A']), 169)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 0, 5, 0, 12;",
                     "    double B = {}(A).A;".format(func_info.eig_func_name),
                     "    return (B == 169);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_matrix_nuclear(self):
        la_str = """A = ||T||_*
                    where 
                    T: ℝ ^ (2×2): matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[12, 5], [5, 12]])
        self.assertEqual(func_info.numpy_func(A).A, 24)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()))['A']), 24)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 12, 5, 5, 12;",
                     "    double B = {}(A).A;".format(func_info.eig_func_name),
                     "    Eigen::JacobiSVD<Eigen::MatrixXd> svd(A, Eigen::ComputeThinU | Eigen::ComputeThinV);",
                     "    return (B == svd.singularValues().sum());",     # precision
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_vector_superscript_only(self):
        la_str = """A = ||T||^2
                    where 
                    T: ℝ ^ 3: vector"""
        func_info = self.gen_func_info(la_str)
        A = np.array([3, 4, 12])
        self.assertEqual(func_info.numpy_func(A).A, 169)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()))['A']), 169)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> A;",
                     "    A << 3, 4, 12;",
                     "    double B = {}(A).A;".format(func_info.eig_func_name),
                     "    return (B == 169);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_vector_superscript_subscript_0(self):
        la_str = """A = ||T||^2_2
                    where 
                    T: ℝ ^ 3: vector"""
        func_info = self.gen_func_info(la_str)
        A = np.array([3, 4, 12])
        self.assertEqual(func_info.numpy_func(A).A, 169)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()))['A']), 169)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> A;",
                     "    A << 3, 4, 12;",
                     "    double B = {}(A).A;".format(func_info.eig_func_name),
                     "    return (B == 169);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_vector_superscript_subscript_1(self):
        la_str = """A = ||T||_2^2
                    where 
                    T: ℝ ^ 3: vector"""
        func_info = self.gen_func_info(la_str)
        A = np.array([3, 4, 12])
        self.assertEqual(func_info.numpy_func(A).A, 169)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()))['A']), 169)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> A;",
                     "    A << 3, 4, 12;",
                     "    double B = {}(A).A;".format(func_info.eig_func_name),
                     "    return (B == 169);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_vector_superscript_subscript_2(self):
        la_str = """A = ||T||_P^2
                    where 
                    T: ℝ ^ 2: a sequence
                    P: ℝ ^ (2×2): a sequence"""
        func_info = self.gen_func_info(la_str)
        A = np.array([-5, 12])
        P = np.array([[1, 0], [0, 1]])
        self.assertEqual(func_info.numpy_func(A, P).A, 169)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()), matlab.double(P.tolist()))['A']), 169)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 1> A;",
                     "    A << -5, 12;",
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 1, 0, 0, 1;",
                     "    double B = {}(A, P).A;".format(func_info.eig_func_name),
                     "    return (B == 169);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_vector_superscript_subscript_3(self):
        la_str = """A = ||T||^2_P
                    where 
                    T: ℝ ^ 2: a sequence
                    P: ℝ ^ (2×2): a sequence"""
        func_info = self.gen_func_info(la_str)
        A = np.array([-5, 12])
        P = np.array([[1, 0], [0, 1]])
        self.assertEqual(func_info.numpy_func(A, P).A, 169)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()), matlab.double(P.tolist()))['A']), 169)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 1> A;",
                     "    A << -5, 12;",
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 1, 0, 0, 1;",
                     "    double B = {}(A, P).A;".format(func_info.eig_func_name),
                     "    return (B == 169);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())