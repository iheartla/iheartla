import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import cppyy
import scipy
from scipy import sparse
cppyy.add_include_path(eigen_path)


class TestProduct(BasePythonTest):
    def test_inner_product(self):
        la_str = """A = <T , P>
                    where 
                    T: ℝ ^ 3: a sequence
                    P: ℝ ^ 3: a sequence """
        func_info = self.gen_func_info(la_str)
        T = np.array([1, 2, 3])
        P = np.array([4, 5, 6])
        self.assertEqual(func_info.numpy_func(T, P).A, 32)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(T.tolist()), matlab.double(P.tolist()))['A']), 32)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> T;",
                     "    T << 1, 2, 3;",
                     "    Eigen::Matrix<double, 3, 1> P;",
                     "    P << 4, 5, 6;",
                     "    double B = {}(T, P).A;".format(func_info.eig_func_name),
                     "    return (B == 32);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_inner_product_subscript(self):
        la_str = """A = <T , P>_M
                    where 
                    T: ℝ ^ 2: a sequence
                    P: ℝ ^ 2: a sequence 
                    M: ℝ ^ (2×2): a sequence"""
        func_info = self.gen_func_info(la_str)
        T = np.array([1, 2])
        P = np.array([3, 4])
        M = np.array([[5, 6], [7, 8]])
        self.assertEqual(func_info.numpy_func(T, P, M).A, 143)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(T.tolist()), matlab.double(P.tolist()), matlab.double(M.tolist()))['A']), 143)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 1> T;",
                     "    T << 1, 2;",
                     "    Eigen::Matrix<double, 2, 1> P;",
                     "    P << 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> M;",
                     "    M << 5, 6, 7, 8;",
                     "    double B = {}(T, P, M).A;".format(func_info.eig_func_name),
                     "    return (B == 143);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_frobenius_product(self):
        la_str = """A = T : P
                    where 
                    T: ℝ ^ (2×2): a sequence
                    P: ℝ ^ (2×2): a sequence"""
        func_info = self.gen_func_info(la_str)
        T = np.array([[1, 2], [3, 4]])
        P = np.array([[5, 6], [7, 8]])
        self.assertEqual(func_info.numpy_func(T, P).A, 70)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(T.tolist()), matlab.double(P.tolist()))['A']), 70)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> T;",
                     "    T << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 5, 6, 7, 8;",
                     "    double B = {}(T, P).A;".format(func_info.eig_func_name),
                     "    return (B == 70);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_hadamard_product(self):
        la_str = """A = T ∘ P
                    where 
                    T: ℝ ^ (2×2): a sequence
                    P: ℝ ^ (2×2): a sequence"""
        func_info = self.gen_func_info(la_str)
        T = np.array([[1, 2], [3, 4]])
        P = np.array([[5, 6], [7, 8]])
        A = np.array([[5, 12], [21, 32]])
        self.assertDMatrixEqual(func_info.numpy_func(T, P).A, A)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(T.tolist()), matlab.double(P.tolist()))['A']), A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> T;",
                     "    T << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 5, 6, 7, 8;",
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 5, 12, 21, 32;",
                     "   Eigen::Matrix<double, 2, 2> B = {}(T, P).A;".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_cross_product(self):
        la_str = """A = T × P
                    where 
                    T: ℝ ^ 3: a sequence
                    P: ℝ ^ 3: a sequence """
        func_info = self.gen_func_info(la_str)
        T = np.array([1, 2, 3])
        P = np.array([4, 5, 6])
        A = np.array([-3, 6, -3])
        self.assertDMatrixEqual(func_info.numpy_func(T, P).A, A)
        # MATLAB test
        # if TEST_MATLAB:
        #     mat_func = getattr(mat_engine, func_info.mat_func_name, None)
        #     self.assertDMatrixEqual(np.array(mat_func(matlab.double(T.tolist()), matlab.double(P.tolist()))['A']), A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> T;",
                     "    T << 1, 2, 3;",
                     "    Eigen::Matrix<double, 3, 1> P;",
                     "    P << 4, 5, 6;",
                     "    Eigen::Matrix<double, 3, 1> A;",
                     "    A << -3, 6, -3;",
                     "   Eigen::Matrix<double, 3, 1> B = {}(T, P).A;".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_kronecker_product(self):
        la_str = """A = T ⊗ P
                    where 
                    T: ℝ ^ (2×3): a sequence
                    P: ℝ ^ (2×3): a sequence"""
        func_info = self.gen_func_info(la_str)
        T = np.array([[1, 2, 3], [3, 4, 5]])
        P = np.array([[5, 6, 7], [7, 8, 9]])
        A = np.array([[5, 6, 7, 10, 12, 14, 15, 18, 21],
                      [7, 8, 9, 14, 16, 18, 21, 24, 27],
                      [15, 18, 21, 20, 24, 28, 25, 30, 35],
                      [21, 24, 27, 28, 32, 36, 35, 40, 45]])
        self.assertDMatrixEqual(func_info.numpy_func(T, P).A, A)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(T.tolist()), matlab.double(P.tolist()))['A']), A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 3> T;",
                     "    T << 1, 2, 3, 3, 4, 5;",
                     "    Eigen::Matrix<double, 2, 3> P;",
                     "    P << 5, 6, 7, 7, 8, 9;",
                     "    Eigen::Matrix<double, 4, 9> A;",
                     "    A << 5, 6, 7, 10, 12, 14, 15, 18, 21,"
                     "    7, 8, 9, 14, 16, 18, 21, 24, 27,"
                     "    15, 18, 21, 20, 24, 28, 25, 30, 35,"
                     "    21, 24, 27, 28, 32, 36, 35, 40, 45;",
                     "   Eigen::Matrix<double, 4, 9> B = {}(T, P).A;".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_kronecker_product1(self):
        la_str = """A = T ⊗ P
                    where 
                    T: ℝ ^ (a×b): a sequence
                    P: ℝ ^ (c×d): a sequence"""
        func_info = self.gen_func_info(la_str)
        T = np.array([[1, 2, 3], [3, 4, 5]])
        P = np.array([[5, 6, 7], [7, 8, 9]])
        A = np.array([[5, 6, 7, 10, 12, 14, 15, 18, 21],
                      [7, 8, 9, 14, 16, 18, 21, 24, 27],
                      [15, 18, 21, 20, 24, 28, 25, 30, 35],
                      [21, 24, 27, 28, 32, 36, 35, 40, 45]])
        self.assertDMatrixEqual(func_info.numpy_func(T, P).A, A)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(T.tolist()), matlab.double(P.tolist()))['A']), A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 3> T;",
                     "    T << 1, 2, 3, 3, 4, 5;",
                     "    Eigen::Matrix<double, 2, 3> P;",
                     "    P << 5, 6, 7, 7, 8, 9;",
                     "    Eigen::Matrix<double, 4, 9> A;",
                     "    A << 5, 6, 7, 10, 12, 14, 15, 18, 21,"
                     "    7, 8, 9, 14, 16, 18, 21, 24, 27,"
                     "    15, 18, 21, 20, 24, 28, 25, 30, 35,"
                     "    21, 24, 27, 28, 32, 36, 35, 40, 45;",
                     "   Eigen::Matrix<double, 4, 9> B = {}(T, P).A;".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_kronecker_product_sparse_lhs(self):
        la_str = """A = T ⊗ P
                    where 
                    T: ℝ ^ (2×3) sparse
                    P: ℝ ^ (2×3): a sequence"""
        func_info = self.gen_func_info(la_str)
        t = [(0, 1), (1, 2)]
        value = np.array([2, 5])
        T = scipy.sparse.coo_matrix((value, np.asarray(t).T), shape=(2, 3))
        P = np.array([[5, 6, 7], [7, 8, 9]])
        t1 = [(0, 3), (0, 4), (0, 5), (1, 3), (1, 4), (1, 5), (2, 6), (2, 7), (2, 8), (3, 6), (3, 7), (3, 8)]
        value1 = np.array([10, 12, 14, 14, 16, 18, 25, 30, 35, 35, 40, 45])
        A = scipy.sparse.coo_matrix((value1, np.asarray(t1).T), shape=(4, 9))
        self.assertSMatrixEqual(func_info.numpy_func(T, P).A, A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::vector<Eigen::Triplet<double> > t2;",
                     "    t2.push_back(Eigen::Triplet<double>(0, 1, 2));",
                     "    t2.push_back(Eigen::Triplet<double>(1, 2, 5));",
                     "    Eigen::SparseMatrix<double> T(2, 3);",
                     "    T.setFromTriplets(t2.begin(), t2.end());"
                     "    Eigen::Matrix<double, 2, 3> P;",
                     "    P << 5, 6, 7, 7, 8, 9;",
                     "    std::vector<Eigen::Triplet<double> > t1;",
                     "    t1.push_back(Eigen::Triplet<double>(0, 3, 10));",
                     "    t1.push_back(Eigen::Triplet<double>(0, 4, 12));",
                     "    t1.push_back(Eigen::Triplet<double>(0, 5, 14));",
                     "    t1.push_back(Eigen::Triplet<double>(1, 3, 14));",
                     "    t1.push_back(Eigen::Triplet<double>(1, 4, 16));",
                     "    t1.push_back(Eigen::Triplet<double>(1, 5, 18));",
                     "    t1.push_back(Eigen::Triplet<double>(2, 6, 25));",
                     "    t1.push_back(Eigen::Triplet<double>(2, 7, 30));",
                     "    t1.push_back(Eigen::Triplet<double>(2, 8, 35));",
                     "    t1.push_back(Eigen::Triplet<double>(3, 6, 35));",
                     "    t1.push_back(Eigen::Triplet<double>(3, 7, 40));",
                     "    t1.push_back(Eigen::Triplet<double>(3, 8, 45));",
                     "    Eigen::SparseMatrix<double> A(4, 9);",
                     "    A.setFromTriplets(t1.begin(), t1.end());"
                     "   Eigen::SparseMatrix<double> B = {}(T, P).A;".format(func_info.eig_func_name),
                     "    return A.isApprox(B);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_dot_product(self):
        la_str = """A = T ⋅ P
                    where 
                    T: ℝ ^ 3: a sequence
                    P: ℝ ^ 3: a sequence """
        func_info = self.gen_func_info(la_str)
        T = np.array([1, 2, 3])
        P = np.array([4, 5, 6])
        self.assertEqual(func_info.numpy_func(T, P).A, 32)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(T.tolist()), matlab.double(P.tolist()))['A']), 32)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> T;",
                     "    T << 1, 2, 3;",
                     "    Eigen::Matrix<double, 3, 1> P;",
                     "    P << 4, 5, 6;",
                     "    double B = {}(T, P).A;".format(func_info.eig_func_name),
                     "    return (B == 32);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())