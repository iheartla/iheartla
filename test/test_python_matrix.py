import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import scipy
from scipy import sparse
import cppyy
cppyy.add_include_path(eigen_path)


class TestMatrix(BasePythonTest):
    def test_square_matrix(self):
        la_str = """A = [a 2; b 3]
        where
        a: scalar
        b: scalar"""
        func_info = self.gen_func_info(la_str)
        a = 1
        b = 4
        B = np.array([[1, 2], [4, 3]])
        self.assertDMatrixEqual(func_info.numpy_func(a, b).A, B)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(a, b)['A']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(1, 4).A;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_transpose_0(self):
        # T
        la_str = """B = A^T
        where
        A: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [4, 3]])
        B = np.array([[1, 4], [2, 3]])
        self.assertDMatrixEqual(func_info.numpy_func(A).B, B)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()))['B']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 1, 4, 2, 3;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A).B;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_transpose_1(self):
        # unicode t
        la_str = """B = Aᵀ
        where
        A: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [4, 3]])
        B = np.array([[1, 4], [2, 3]])
        self.assertDMatrixEqual(func_info.numpy_func(A).B, B)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()))['B']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 1, 4, 2, 3;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A).B;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_inverse(self):
        # -1
        la_str = """B = A^(-1)
        where
        A: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[4, 0], [0, 0.5]])
        B = np.array([[0.25, 0], [0, 2]])
        self.assertDMatrixEqual(func_info.numpy_func(A).B, B)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()))['B']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 4, 0, 0, 0.5;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 0.25, 0, 0, 2;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A).B;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_block_matrix_0(self):
        # normal block
        la_str = """C = [A ; B]
        where
        A: ℝ ^ (2 × 2): a matrix
        B: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[5, 6], [7, 8]])
        C = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        self.assertDMatrixEqual(func_info.numpy_func(A, B).C, C)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()), matlab.double(B.tolist()))['C']), C)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 5, 6, 7, 8;",
                     "    Eigen::Matrix<double, 4, 2> C;",
                     "    C << 1, 2, 3, 4, 5, 6, 7, 8;",
                     "    Eigen::Matrix<double, 4, 2> D = {}(A, B).C;".format(func_info.eig_func_name),
                     "    return ((D - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_block_matrix_1(self):
        la_str = """C = [A B]
        where
        A: ℝ ^ (2 × 2): a matrix
        B: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[5, 6], [7, 8]])
        C = np.array([[1, 2, 5, 6], [3, 4, 7, 8]])
        self.assertDMatrixEqual(func_info.numpy_func(A, B).C, C)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()), matlab.double(B.tolist()))['C']), C)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 5, 6, 7, 8;",
                     "    Eigen::Matrix<double, 2, 4> C;",
                     "    C << 1, 2, 5, 6, 3, 4, 7, 8;",
                     "    Eigen::Matrix<double, 2, 4> D = {}(A, B).C;".format(func_info.eig_func_name),
                     "    return ((D - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_block_matrix_2(self):
        # expression as item
        la_str = """C = [A+B A-B]
        where
        A: ℝ ^ (2 × 2): a matrix
        B: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[5, 6], [7, 8]])
        C = np.array([[6, 8, -4, -4], [10, 12, -4, -4]])
        self.assertDMatrixEqual(func_info.numpy_func(A, B).C, C)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()), matlab.double(B.tolist()))['C']), C)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 5, 6, 7, 8;",
                     "    Eigen::Matrix<double, 2, 4> C;",
                     "    C << 6, 8, -4, -4, 10, 12, -4, -4;",
                     "    Eigen::Matrix<double, 2, 4> D = {}(A, B).C;".format(func_info.eig_func_name),
                     "    return ((D - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_block_matrix_3(self):
        # number matrix
        la_str = """C = [A 1_2,2; 0 0_2,2]
        where
        A: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [3, 4]])
        C = np.array([[1, 2, 1, 1], [3, 4, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]])
        self.assertDMatrixEqual(func_info.numpy_func(A).C, C)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()))['C']), C)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 4, 4> B;",
                     "    B << 1, 2, 1, 1, 3, 4, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0;",
                     "    Eigen::Matrix<double, 4, 4> C = {}(A).C;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_block_matrix_4(self):
        # I identity matrix
        la_str = """C = [A 1; 0 I_2]
        where
        A: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [3, 4]])
        C = np.array([[1, 2, 1, 1], [3, 4, 1, 1], [0, 0, 1, 0], [0, 0, 0, 1]])
        self.assertDMatrixEqual(func_info.numpy_func(A).C, C)
        # MATLAB testA
        # if TEST_MATLAB:
        #     mat_func = getattr(mat_engine, func_info.mat_func_name, None)
        #     print(np.array(mat_func((A.tolist()))['C']))
        #     self.assertDMatrixEqual(np.array(mat_func((A.tolist()))['C']), C)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 4, 4> B;",
                     "    B << 1, 2, 1, 1, 3, 4, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1;",
                     "    Eigen::Matrix<double, 4, 4> C = {}(A).C;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_block_matrix_5(self):
        # I identity matrix
        la_str = """B = [ A C I ]
        where
        A: ℝ ^ (2 × 2): a matrix
        C: ℝ ^ (2 × 2): a matrix """
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[1, 2, 1, 2, 1, 0], [3, 4, 3, 4, 0, 1]])
        self.assertDMatrixEqual(func_info.numpy_func(A, A).B, B)
        # MATLAB test
        # if TEST_MATLAB:
        #     mat_func = getattr(mat_engine, func_info.mat_func_name, None)
        #     self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()), matlab.double(A.tolist()))['B']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 6> B;",
                     "    B << 1, 2, 1, 2, 1, 0, 3, 4, 3, 4, 0, 1;",
                     "    Eigen::Matrix<double, 2, 6> C = {}(A, A).B;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_block_matrix_6(self):
        # scalar value
        la_str = """B = [ A 1 ]
        where
        A: ℝ ^ 2: a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([3, 4])
        B = np.array([[3, 1], [4, 1]])
        self.assertDMatrixEqual(func_info.numpy_func(A).B, B)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()))['B']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 1> A;",
                     "    A << 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 3, 1, 4, 1;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A).B;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_block_matrix_7(self):
        # scalar value
        la_str = """B = [ A ; 1 ]
        where
        A: ℝ ^ 2: a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([3, 4])
        B = np.array([[3], [4], [1]])
        self.assertDMatrixEqual(func_info.numpy_func(A).B, B)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()))['B']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 1> A;",
                     "    A << 3, 4;",
                     "    Eigen::Matrix<double, 3, 1> B;",
                     "    B << 3, 4, 1;",
                     "    Eigen::Matrix<double, 3, 1> C = {}(A).B;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_elementwise_matrix(self):
        # scalar value
        la_str = """B_i,j = A_j,i
        where
        A: ℝ^(2 × 3) """
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 3, 4], [2, 0, 1]])
        B = np.array([[1, 2], [3, 0], [4, 1]])
        self.assertDMatrixEqual(func_info.numpy_func(A).B, B)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()))['B']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 3> A;",
                     "    A << 1, 3, 4, 2, 0, 1;",
                     "    Eigen::Matrix<double, 3, 2> B;",
                     "    B << 1, 2, 3, 0, 4, 1;",
                     "    Eigen::Matrix<double, 3, 2> C = {}(A).B;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_identity_matrix_0(self):
        # outside matrix
        la_str = """C = I_2 + A
        where
        A: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[2, 2], [3, 5]])
        self.assertDMatrixEqual(func_info.numpy_func(A).C, B)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()))['C']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 2, 2, 3, 5;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A).C;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_identity_matrix_1(self):
        # I used as symbol rather than identity matrix
        la_str = """I = A
        B = I + A
        where
        A: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[2, 4], [6, 8]])
        self.assertDMatrixEqual(func_info.numpy_func(A).B, B)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()))['B']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 2, 4, 6, 8;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A).B;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_shadow_identity_matrix(self):
        la_str = """given
        I ∈ ℝ²
        I_1+I_2"""
        func_info = self.gen_func_info(la_str)
        A = np.array([1, 2])
        self.assertEqual(func_info.numpy_func(A).ret, 3)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()))['ret']), 3)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 1> A;",
                     "    A << 1, 2;",
                     "    double C = {}(A).ret;".format(func_info.eig_func_name),
                     "    return C == 3;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_sparse_matrix_0(self):
        # sparse matrix: =
        la_str = """G_ij = { P_ij + J_ij  if  ( i , j ) ∈ E
        0 otherwise

        where
        P: ℝ ^ (4 × 4): a matrix
        J: ℝ ^ (4 × 4): a matrix
        G: ℝ ^ (10 × 10): a matrix
        E: { ℤ × ℤ } index
        """
        func_info = self.gen_func_info(la_str)
        P = np.array([[-6, 9, -1, -11], [17, 14, 0, 0], [6, -2, 11, 0], [2, -9, -2, -9]])
        J = np.array([[-9, -6, 0, -3], [1, 10, 0, 14], [-14, -2, 10, 13], [5, 9, 0, -10]])
        E = [(0, 1), (0, 2), (1, 2), (2, 0), (3, 0), (3, 1), (3, 2)]
        value = np.array([3, -1, 0, -8, 7, 0, -2])
        B = scipy.sparse.coo_matrix((value, np.asarray(E).T), shape=(10, 10), dtype=np.float64)
        self.assertSMatrixEqual(func_info.numpy_func(P, J, E).G, B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 4, 4> P;",
                     "    P << -6, 9, -1, -11, 17, 14, 0, 0, 6, -2, 11, 0, 2, -9, -2, -9;",
                     "    Eigen::Matrix<double, 4, 4> J;",
                     "    J << -9, -6, 0, -3, 1, 10, 0, 14, -14, -2, 10, 13, 5, 9, 0, -10;",
                     "    std::set< std::tuple< int, int > > E;",
                     "    E.insert(std::make_tuple(3, 0));",
                     "    E.insert(std::make_tuple(1, 2));",
                     "    E.insert(std::make_tuple(3, 2));",
                     "    E.insert(std::make_tuple(0, 1));",
                     "    E.insert(std::make_tuple(3, 1));",
                     "    E.insert(std::make_tuple(0, 2));",
                     "    E.insert(std::make_tuple(2, 0));",
                     "    std::vector<Eigen::Triplet<double> > t1;",
                     "    t1.push_back(Eigen::Triplet<double>(3, 0, 7));",
                     "    t1.push_back(Eigen::Triplet<double>(1, 2, 0));",
                     "    t1.push_back(Eigen::Triplet<double>(3, 2, -2));",
                     "    t1.push_back(Eigen::Triplet<double>(0, 1, 3));",
                     "    t1.push_back(Eigen::Triplet<double>(3, 1, 0));",
                     "    t1.push_back(Eigen::Triplet<double>(0, 2, -1));",
                     "    t1.push_back(Eigen::Triplet<double>(2, 0, -8));",
                     "    Eigen::SparseMatrix<double> A(10, 10);",
                     "    A.setFromTriplets(t1.begin(), t1.end());"
                     "    Eigen::SparseMatrix<double> B = {}(P, J, E).G;".format(func_info.eig_func_name),
                     "    return A.isApprox(B);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_sparse_matrix_1(self):
        # sparse matrix: +=
        la_str = """G_ij = { P_ij + J_ij  if  ( i , j ) ∈ E
        0 otherwise

        G_jk += { ( j , k ) ∈ F : P_jk + J_jk
        0 otherwise

        where
        P: ℝ ^ (4 × 4): a matrix
        J: ℝ ^ (4 × 4): a matrix
        G: ℝ ^ (10 × 10): a matrix
        E: { ℤ × ℤ } index
        F: { ℤ × ℤ } index"""
        func_info = self.gen_func_info(la_str)
        P = np.array([[-6, 9, -1, -11], [17, 14, 0, 0], [6, -2, 11, 0], [2, -9, -2, -9]])
        J = np.array([[-9, -6, 0, -3], [1, 10, 0, 14], [-14, -2, 10, 13], [5, 9, 0, -10]])
        E = [(3, 0), (1, 2), (3, 2), (0, 1), (3, 1), (0, 2), (2, 0)]
        F = [(1, 1), (2, 2), (3, 3)]
        G = [(1, 1), (2, 2), (3, 3), (0, 1), (0, 2), (1, 2), (2, 0), (3, 0), (3, 1), (3, 2)]
        value = np.array([24, 21, -19, 3, -1, 0, -8, 7, 0, -2])
        B = scipy.sparse.coo_matrix((value, np.asarray(G).T), shape=(10, 10))
        self.assertSMatrixEqual(func_info.numpy_func(P, J, E, F).G, B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 4, 4> P;",
                     "    P << -6, 9, -1, -11, 17, 14, 0, 0, 6, -2, 11, 0, 2, -9, -2, -9;",
                     "    Eigen::Matrix<double, 4, 4> J;",
                     "    J << -9, -6, 0, -3, 1, 10, 0, 14, -14, -2, 10, 13, 5, 9, 0, -10;",
                     "    std::set< std::tuple< int, int > > E;",
                     "    E.insert(std::make_tuple(3, 0));",
                     "    E.insert(std::make_tuple(1, 2));",
                     "    E.insert(std::make_tuple(3, 2));",
                     "    E.insert(std::make_tuple(0, 1));",
                     "    E.insert(std::make_tuple(3, 1));",
                     "    E.insert(std::make_tuple(0, 2));",
                     "    E.insert(std::make_tuple(2, 0));",
                     "    std::set< std::tuple< int, int > > F;",
                     "    F.insert(std::make_tuple(1, 1));",
                     "    F.insert(std::make_tuple(2, 2));",
                     "    F.insert(std::make_tuple(3, 3));",
                     "    std::vector<Eigen::Triplet<double> > t1;",
                     "    t1.push_back(Eigen::Triplet<double>(3, 0, 7));",
                     "    t1.push_back(Eigen::Triplet<double>(1, 2, 0));",
                     "    t1.push_back(Eigen::Triplet<double>(3, 2, -2));",
                     "    t1.push_back(Eigen::Triplet<double>(0, 1, 3));",
                     "    t1.push_back(Eigen::Triplet<double>(3, 1, 0));",
                     "    t1.push_back(Eigen::Triplet<double>(0, 2, -1));",
                     "    t1.push_back(Eigen::Triplet<double>(2, 0, -8));",
                     "    t1.push_back(Eigen::Triplet<double>(1, 1, 24));",
                     "    t1.push_back(Eigen::Triplet<double>(2, 2, 21));",
                     "    t1.push_back(Eigen::Triplet<double>(3, 3, -19));",
                     "    Eigen::SparseMatrix<double> A(10, 10);",
                     "    A.setFromTriplets(t1.begin(), t1.end());"
                     "    Eigen::SparseMatrix<double> B = {}(P, J, E, F).G;".format(func_info.eig_func_name),
                     "    return A.isApprox(B);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_sparse_diagonal_matrix(self):
        # sparse matrix: =
        la_str = """D_ii = sum_j A_ij
        where
        A: ℝ^(n × n)
        """
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        E = [(0, 0), (1, 1), (2, 2)]
        value = np.array([6, 15, 24])
        B = scipy.sparse.coo_matrix((value, np.asarray(E).T), shape=(3, 3), dtype=np.float64)
        self.assertSMatrixEqual(func_info.numpy_func(A).D, B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> A;",
                     "    A << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    std::vector<Eigen::Triplet<double> > t1;",
                     "    t1.push_back(Eigen::Triplet<double>(0, 0, 6));",
                     "    t1.push_back(Eigen::Triplet<double>(1, 1, 15));",
                     "    t1.push_back(Eigen::Triplet<double>(2, 2, 24));",
                     "    Eigen::SparseMatrix<double> C(3, 3);",
                     "    C.setFromTriplets(t1.begin(), t1.end());"
                     "    Eigen::SparseMatrix<double> B = {}(A).D;".format(func_info.eig_func_name),
                     "    return C.isApprox(B);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_sparse_block_matrix_1(self):
        # sparse matrix in block matrix
        la_str = """[ A   0₂,₂
        0_2,2   I]
        where
        A: ℝ ^ (2 × 2) sparse """
        func_info = self.gen_func_info(la_str)
        t = [(0, 0), (1, 1)]
        t2 = [(0, 0), (1, 1), (2, 2), (3, 3)]
        value = np.array([3, 4])
        value2 = np.array([3, 4, 1, 1])
        A = scipy.sparse.coo_matrix((value, np.asarray(t).T), shape=(2, 2))
        B = scipy.sparse.coo_matrix((value2, np.asarray(t2).T), shape=(4, 4))
        self.assertSMatrixEqual(func_info.numpy_func(A).ret, B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::vector<Eigen::Triplet<double> > t1;",
                     "    t1.push_back(Eigen::Triplet<double>(0, 0, 3));",
                     "    t1.push_back(Eigen::Triplet<double>(1, 1, 4));",
                     "    Eigen::SparseMatrix<double> A(2, 2);",
                     "    A.setFromTriplets(t1.begin(), t1.end());"
                     "    std::vector<Eigen::Triplet<double> > t2;",
                     "    t2.push_back(Eigen::Triplet<double>(0, 0, 3));",
                     "    t2.push_back(Eigen::Triplet<double>(1, 1, 4));",
                     "    t2.push_back(Eigen::Triplet<double>(2, 2, 1));",
                     "    t2.push_back(Eigen::Triplet<double>(3, 3, 1));",
                     "    Eigen::SparseMatrix<double> C(4, 4);",
                     "    C.setFromTriplets(t2.begin(), t2.end());"
                     "    Eigen::SparseMatrix<double> B = {}(A).ret;".format(func_info.eig_func_name),
                     "    return C.isApprox(B);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_sparse_block_matrix_2(self):
        # sparse matrix in block matrix
        la_str = """C = [ A   1   2  0  B]
        where
        A: ℝ ^ (1 × 2) sparse
        B: ℝ ^ (1 × 2) sparse  """
        func_info = self.gen_func_info(la_str)
        t = [(0, 0)]
        t2 = [(0, 0), (0, 2), (0, 3), (0, 5)]
        value = np.array([3])
        value2 = np.array([3, 1, 2, 3])
        A = scipy.sparse.coo_matrix((value, np.asarray(t).T), shape=(1, 2))
        B = scipy.sparse.coo_matrix((value2, np.asarray(t2).T), shape=(1, 7))
        self.assertSMatrixEqual(func_info.numpy_func(A, A).C, B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::vector<Eigen::Triplet<double> > t1;",
                     "    t1.push_back(Eigen::Triplet<double>(0, 0, 3));",
                     "    Eigen::SparseMatrix<double> A(1, 2);",
                     "    A.setFromTriplets(t1.begin(), t1.end());"
                     "    std::vector<Eigen::Triplet<double> > t2;",
                     "    t2.push_back(Eigen::Triplet<double>(0, 0, 3));",
                     "    t2.push_back(Eigen::Triplet<double>(0, 1, 0));",
                     "    t2.push_back(Eigen::Triplet<double>(0, 2, 1));",
                     "    t2.push_back(Eigen::Triplet<double>(0, 3, 2));",
                     "    t2.push_back(Eigen::Triplet<double>(0, 4, 0));",
                     "    t2.push_back(Eigen::Triplet<double>(0, 5, 3));",
                     "    t2.push_back(Eigen::Triplet<double>(0, 6, 0));",
                     "    Eigen::SparseMatrix<double> C(1, 7);",
                     "    C.setFromTriplets(t2.begin(), t2.end());"
                     "    Eigen::SparseMatrix<double> B = {}(A, A).C;".format(func_info.eig_func_name),
                     "    return C.isApprox(B);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_sparse_block_matrix_3(self):
        # sparse matrix in block matrix
        la_str = """C = [ A   1   2  0  B]
        where
        A: ℝ ^ (1 × 2)
        B: ℝ ^ (1 × 2) sparse  """
        func_info = self.gen_func_info(la_str)
        t = [(0, 0)]
        t2 = [(0, 0), (0, 2), (0, 3), (0, 5)]
        value = np.array([3])
        value2 = np.array([3, 1, 2, 3])
        D = np.array([[3, 0]])
        A = scipy.sparse.coo_matrix((value, np.asarray(t).T), shape=(1, 2))
        B = scipy.sparse.coo_matrix((value2, np.asarray(t2).T), shape=(1, 7))
        self.assertSMatrixEqual(func_info.numpy_func(D, A).C, B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::vector<Eigen::Triplet<double> > t1;",
                     "    t1.push_back(Eigen::Triplet<double>(0, 0, 3));",
                     "    Eigen::Matrix<double, 1, 2> D;",
                     "    D<< 3, 0;"
                     "    Eigen::SparseMatrix<double> A(1, 2);",
                     "    A.setFromTriplets(t1.begin(), t1.end());"
                     "    std::vector<Eigen::Triplet<double> > t2;",
                     "    t2.push_back(Eigen::Triplet<double>(0, 0, 3));",
                     "    t2.push_back(Eigen::Triplet<double>(0, 1, 0));",
                     "    t2.push_back(Eigen::Triplet<double>(0, 2, 1));",
                     "    t2.push_back(Eigen::Triplet<double>(0, 3, 2));",
                     "    t2.push_back(Eigen::Triplet<double>(0, 4, 0));",
                     "    t2.push_back(Eigen::Triplet<double>(0, 5, 3));",
                     "    t2.push_back(Eigen::Triplet<double>(0, 6, 0));",
                     "    Eigen::SparseMatrix<double> C(1, 7);",
                     "    C.setFromTriplets(t2.begin(), t2.end());"
                     "    Eigen::SparseMatrix<double> B = {}(D, A).C;".format(func_info.eig_func_name),
                     "    return C.isApprox(B);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_vector_1(self):
        # vector
        la_str = """B = (1, A, 4) + (1, 1, 1, 1)
        where
        A: ℝ ^ 2: a vector"""
        func_info = self.gen_func_info(la_str)
        A = np.array([1, 2])
        B = np.array([2, 2, 3, 5])
        self.assertDMatrixEqual(func_info.numpy_func(A).B, B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 1> A;",
                     "    A << 1, 2;",
                     "    Eigen::Matrix<double, 4, 1> B;",
                     "    B << 2, 2, 3, 5;",
                     "    Eigen::Matrix<double, 4, 1> C = {}(A).B;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())