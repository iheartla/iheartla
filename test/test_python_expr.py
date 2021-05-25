import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)


class TestExpr(BasePythonTest):
    # def test_addition_vector_matrix(self):
    #     # space
    #     la_str = """C = P+Q
    #     where
    #     P: ℝ^2
    #     Q: ℝ^(2×1)"""
    #     func_info = self.gen_func_info(la_str)
    #     P = np.array([[1], [4]])
    #     P.reshape((2, 1))
    #     Q = np.array([[1], [2]])
    #     C = np.array([[2], [6]])
    #     self.assertDMatrixEqual(func_info.numpy_func(P, Q), C)
    #     # eigen test
    #     cppyy.include(func_info.eig_file_name)
    #     func_list = ["bool {}(){{".format(func_info.eig_test_name),
    #                  "    Eigen::Matrix<double, 2, 1> P;",
    #                  "    P << 1, 4;",
    #                  "    Eigen::Matrix<double, 2, 1> Q;",
    #                  "    Q << 1, 2;",
    #                  "    Eigen::Matrix<double, 2, 1> C;",
    #                  "    C << 2, 6;",
    #                  "    Eigen::Matrix<double, 2, 1> B = {}(P, Q);".format(func_info.eig_func_name),
    #                  "    return ((B - C).norm() == 0);",
    #                  "}"]
    #     cppyy.cppdef('\n'.join(func_list))
    #     self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_multiplication_0(self):
        # space
        la_str = """c = a b
        where
        a: scalar
        b: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3, 2).c, 6)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(mat_func(3, 2)['c'], 6)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    if({}(3, 4).c == 12){{".format(func_info.eig_func_name),
                     "        return true;",
                     "    }",
                     "    return false;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_multiplication_1(self):
        # star
        la_str = """c = a ⋅ b
        where
        a: scalar
        b: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3, 2).c, 6)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(mat_func(3, 2)['c'], 6)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    if({}(3, 4).c == 12){{".format(func_info.eig_func_name),
                     "        return true;",
                     "    }",
                     "    return false;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_multiplication_2(self):
        # matrix
        la_str = """c = a ⋅ A
                where
                a: scalar
                A: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[2, 4], [6, 8]])
        self.assertDMatrixEqual(func_info.numpy_func(2, A).c, B)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(2, matlab.int64(A.tolist()))['c']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 2, 4, 6, 8;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(2, A).c;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_solver(self):
        # matrix
        la_str = """y = A \ C
        where
        A: ℝ ^ (2 × 2): a matrix
        C: ℝ ^ (2 × 2): a matrix """
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [3, 4]])
        C = np.array([[19, 22], [43, 50]])
        B = np.array([[5., 6.], [7., 8.]])
        B = np.asarray(B, dtype=np.float64)
        self.assertDMatrixEqual(func_info.numpy_func(A, C).y, np.linalg.solve(A, C))
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()), matlab.double(C.tolist()))['y']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 5, 6, 7, 8;",
                     "    Eigen::Matrix<double, 2, 2> C;",
                     "    C << 19, 22, 43, 50;",
                     "    Eigen::Matrix<double, 2, 2> D = {}(A, C).y;".format(func_info.eig_func_name),
                     "    return ((A.colPivHouseholderQr().solve(C) - D).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_unary_scalar_0(self):
        la_str = """b = -2a
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, -6)
        self.assertEqual(func_info.numpy_func(-3).b, 6)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(3)['b']), -6)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    if({}(3).b == -6 && {}(-3).b == 6){{".format(func_info.eig_func_name, func_info.eig_func_name),
                     "        return true;",
                     "    }",
                     "    return false;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())
    #
    def test_unary_scalar_1(self):
        la_str = """b = -a2
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, -6)
        self.assertEqual(func_info.numpy_func(-3).b, 6)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(3)['b']), -6)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    if({}(3).b == -6 && {}(-3).b == 6){{".format(func_info.eig_func_name, func_info.eig_func_name),
                     "        return true;",
                     "    }",
                     "    return false;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_unary_scalar_2(self):
        la_str = """b = -2-a
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, -5)
        self.assertEqual(func_info.numpy_func(-3).b, 1)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(3)['b']), -5)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    if({}(3).b == -5 && {}(-3).b == 1){{".format(func_info.eig_func_name, func_info.eig_func_name),
                     "        return true;",
                     "    }",
                     "    return false;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_unary_scalar_3(self):
        la_str = """b = -a -2
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3).b, -5)
        self.assertEqual(func_info.numpy_func(-3).b, 1)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(3)['b']), -5)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    if({}(3).b == -5 && {}(-3).b == 1){{".format(func_info.eig_func_name, func_info.eig_func_name),
                     "        return true;",
                     "    }",
                     "    return false;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_unary_matrix_0(self):
        la_str = """B = -2A
        where
        A: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[-2, -4], [-6, -8]])
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
                     "    B << -2, -4, -6, -8;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A).B;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_unary_matrix_1(self):
        la_str = """B = -A2
        where
        A: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[-2, -4], [-6, -8]])
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
                     "    B << -2, -4, -6, -8;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A).B;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_unary_matrix_2(self):
        la_str = """B = -[2 2; 2 2]-A
        where
        A: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[-3, -4], [-5, -6]])
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
                     "    B << -3, -4, -5, -6;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A).B;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_scalar_pow(self):
        la_str = """C = A^2
        where
        A: ℝ: a scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(2).C, 4)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(2)['C']), 4)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    double C = {}(2).C;".format(func_info.eig_func_name),
                     "    return (C == 4);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_matrix_pow(self):
        la_str = """C = A^2
        where
        A: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [3, 4]])
        C = np.array([[7, 10], [15, 22]])
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
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 7, 10, 15, 22;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A).C;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())