import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)


class TestSubscript(BasePythonTest):
    def test_subscript_0(self):
        # sequence
        la_str = """B_i = A_i
        where
        A_i: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[[1, 2], [4, 3]], [[1, 2], [4, 3]]])
        self.assertDMatrixEqual(func_info.numpy_func(A).B, A)
        # MATLAB test
        # if TEST_MATLAB:
        #     mat_func = getattr(mat_engine, func_info.mat_func_name, None)
        #     self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()))['B']), A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A1;",
                     "    A1 << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A2;",
                     "    A2 << 1, 2, 4, 3;",
                     "    std::vector<Eigen::Matrix<double, 2, 2> > A;",
                     "    A.push_back(A1);",
                     "    A.push_back(A2);",
                     "    std::vector<Eigen::Matrix<double, 2, 2> > B = {}(A).B;".format(func_info.eig_func_name),
                     "    if((A[0] - B[0]).norm() == 0 && (A[1] - B[1]).norm() == 0){",
                     "        return true;",
                     "    }",
                     "    return false;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_subscript_1(self):
        # matrix
        la_str = """B_ij = A_ij A_ij
        where
        A: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [4, 3]])
        B = np.array([[1, 4], [16, 9]])
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
                     "    B << 1, 4, 16, 9;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A).B;".format(func_info.eig_func_name),
                     "    return ((C - B).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_vector_assignment(self):
        # matrix
        la_str = """q_i = p_i
        where
        p ∈ ℝ^3"""
        func_info = self.gen_func_info(la_str)
        A = np.array([1, 2, 3])
        self.assertDMatrixEqual(func_info.numpy_func(A).q, A)
        # MATLAB test
        # if TEST_MATLAB:
        #     mat_func = getattr(mat_engine, func_info.mat_func_name, None)
        #     self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()))['q']), A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> A;",
                     "    A << 1, 2, 3;",
                     "    Eigen::Matrix<double, 3, 1> C = {}(A).q;".format(func_info.eig_func_name),
                     "    return ((C - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_subscript_I(self):
        # sequence
        la_str = """B_i = I_i
        where
        I_i: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[[1, 2], [4, 3]], [[1, 2], [4, 3]]])
        self.assertDMatrixEqual(func_info.numpy_func(A).B, A)
        # MATLAB test
        # if TEST_MATLAB:
        #     mat_func = getattr(mat_engine, func_info.mat_func_name, None)
        #     self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()))['B']), A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A1;",
                     "    A1 << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A2;",
                     "    A2 << 1, 2, 4, 3;",
                     "    std::vector<Eigen::Matrix<double, 2, 2> > A;",
                     "    A.push_back(A1);",
                     "    A.push_back(A2);",
                     "    std::vector<Eigen::Matrix<double, 2, 2> > B = {}(A).B;".format(func_info.eig_func_name),
                     "    if((A[0] - B[0]).norm() == 0 && (A[1] - B[1]).norm() == 0){",
                     "        return true;",
                     "    }",
                     "    return false;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_summation_0(self):
        # simple version
        la_str = """B = sum_i A_i
        where
        A_i: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[[1, 2], [4, 3]], [[1, 2], [4, 3]]])
        B = np.array([[2, 4], [8, 6]])
        self.assertDMatrixEqual(func_info.numpy_func(A).B, B)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()))['B']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A1;",
                     "    A1 << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A2;",
                     "    A2 << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 2, 4, 8, 6;",
                     "    std::vector<Eigen::Matrix<double, 2, 2> > A;",
                     "    A.push_back(A1);",
                     "    A.push_back(A2);",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A).B;".format(func_info.eig_func_name),
                     "    return ((C - B).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_summation_1(self):
        # simple version: different subscript
        la_str = """B = sum_j A_j
        where
        A_i: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[[1, 2], [4, 3]], [[1, 2], [4, 3]]])
        B = np.array([[2, 4], [8, 6]])
        self.assertDMatrixEqual(func_info.numpy_func(A).B, B)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()))['B']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A1;",
                     "    A1 << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A2;",
                     "    A2 << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 2, 4, 8, 6;",
                     "    std::vector<Eigen::Matrix<double, 2, 2> > A;",
                     "    A.push_back(A1);",
                     "    A.push_back(A2);",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A).B;".format(func_info.eig_func_name),
                     "    return ((C - B).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_summation_2(self):
        # multiple operands: Add
        la_str = """C = sum_i (A_i + B_i)
        where
        A_i: ℝ ^ (2 × 2): a matrix
        B_i: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[[1, 2], [4, 3]], [[1, 2], [4, 3]]])
        B = np.array([[4, 8], [16, 12]])
        self.assertDMatrixEqual(func_info.numpy_func(A, A).C, B)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()), matlab.double(A.tolist()))['C']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A1;",
                     "    A1 << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A2;",
                     "    A2 << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 4, 8, 16, 12;",
                     "    std::vector<Eigen::Matrix<double, 2, 2> > A;",
                     "    A.push_back(A1);",
                     "    A.push_back(A2);",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A, A).C;".format(func_info.eig_func_name),
                     "    return ((C - B).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_summation_3(self):
        # multiple operands: Mul
        la_str = """C = sum_i A_i B_i
        where
        A_i: ℝ ^ (2 × 2): a matrix
        B_i: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[[1, 2], [4, 3]], [[1, 2], [4, 3]]])
        B = np.array([[[1, 0], [0, 1]], [[1, 0], [0, 1]]])
        C = np.array([[2, 4], [8, 6]])
        self.assertDMatrixEqual(func_info.numpy_func(A, B).C, C)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()), matlab.double(B.tolist()))['C']), C)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A1;",
                     "    A1 << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A2;",
                     "    A2 << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> B1;",
                     "    B1 << 1, 0, 0, 1;",
                     "    Eigen::Matrix<double, 2, 2> B2;",
                     "    B2 << 1, 0, 0, 1;",
                     "    Eigen::Matrix<double, 2, 2> C;",
                     "    C << 2, 4, 8, 6;",
                     "    std::vector<Eigen::Matrix<double, 2, 2> > A;",
                     "    A.push_back(A1);",
                     "    A.push_back(A2);",
                     "    std::vector<Eigen::Matrix<double, 2, 2> > B;",
                     "    B.push_back(B1);",
                     "    B.push_back(B2);",
                     "    Eigen::Matrix<double, 2, 2> D = {}(A, B).C;".format(func_info.eig_func_name),
                     "    return ((C - D).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_nested_summation_0(self):
        # nested
        la_str = """C = sum_i A_i sum_j w_j
        where
        w_j: scalar: a scalar
        A_i: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        w = np.array([1, 1, 2, 2])
        A = np.array([[[1, 2], [4, 3]], [[1, 2], [4, 3]]])
        B = np.array([[12, 24], [48, 36]])
        self.assertDMatrixEqual(func_info.numpy_func(w, A).C, B)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(w.tolist()), matlab.double(A.tolist()))['C']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A1;",
                     "    A1 << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A2;",
                     "    A2 << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 12, 24, 48, 36;",
                     "    std::vector<Eigen::Matrix<double, 2, 2> > A;",
                     "    A.push_back(A1);",
                     "    A.push_back(A2);",
                     "    std::vector<double> w = {1, 1, 2, 2};",
                     "    Eigen::Matrix<double, 2, 2> C = {}(w, A).C;".format(func_info.eig_func_name),
                     "    return ((C - B).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_nested_summation_1(self):
        # special
        la_str = """C = sum_i A_i sum_j w_j A_i
        where
        w_j: scalar: a scalar
        A_i: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        w = np.array([1, 1, 2, 2])
        A = np.array([[[1, 2], [4, 3]], [[1, 2], [4, 3]]])
        B = np.array([[108, 96], [192, 204]])
        self.assertDMatrixEqual(func_info.numpy_func(w, A).C, B)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(w.tolist()), matlab.double(A.tolist()))['C']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A1;",
                     "    A1 << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A2;",
                     "    A2 << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 108, 96, 192, 204;",
                     "    std::vector<Eigen::Matrix<double, 2, 2> > A;",
                     "    A.push_back(A1);",
                     "    A.push_back(A2);",
                     "    std::vector<double> w = {1, 1, 2, 2};",
                     "    Eigen::Matrix<double, 2, 2> C = {}(w, A).C;".format(func_info.eig_func_name),
                     "    return ((C - B).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_conditional_summation(self):
        # if condition
        la_str = """Q = A
        Q_ii = sum_(j for j ≠ i ) Q_ij
        where
        A: ℝ ^ (3 × 3): a matrix"""
        func_info = self.gen_func_info(la_str)
        Q = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        P = np.array([[5, 2, 3], [4, 10, 6], [7, 8, 15]])
        self.assertDMatrixEqual(func_info.numpy_func(Q).Q, P)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(Q.tolist()))['Q']), P)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> Q;",
                     "    Q << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    Eigen::Matrix<double, 3, 3> P;",
                     "    P << 5, 2, 3, 4, 10, 6, 7, 8, 15;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(Q).Q;".format(func_info.eig_func_name),
                     "    return ((C - P).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_lhs_and_sum(self):
        # matrix
        la_str = """v_ij = sum_k u_k w_i,j
        where
        w ∈ ℝ^(2×2)
        u ∈ ℝ^2"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [4, 3]])
        u = np.array([1, 2])
        B = np.array([[3, 6], [12, 9]])
        self.assertDMatrixEqual(func_info.numpy_func(A, u).v, B)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(A.tolist()), matlab.double(u.tolist()))['v']), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 1> u;",
                     "    u << 1, 2;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 3, 6, 12, 9;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A, u).v;".format(func_info.eig_func_name),
                     "    return ((C - B).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_indexing_type(self):
        la_str = """d = a_b + a_c
                where
                a  ∈ ℝ^3
                b  ∈ ℤ
                c  ∈ ℤ index"""
        func_info = self.gen_func_info(la_str)
        A = np.array([4, 5, 6])
        self.assertEqual(func_info.numpy_func(A, 1, 1).d, 9)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()), 1, 1)['d']), 8)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> A;",
                     "    A << 4, 5, 6;",
                     "    double C = {}(A, 1, 1).d;".format(func_info.eig_func_name),
                     "    return (C == 9);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_indexing_type_addition(self):
        la_str = """ c = b + 1
                d = a_c 
                where
                a  ∈ ℝ^3
                b  ∈ ℤ index"""
        func_info = self.gen_func_info(la_str)
        A = np.array([4, 5, 6])
        self.assertEqual(func_info.numpy_func(A, 1).d, 6)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()), 1)['d']), 5)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> A;",
                     "    A << 4, 5, 6;",
                     "    double C = {}(A, 1).d;".format(func_info.eig_func_name),
                     "    return (C == 6);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_indexing_type_subtraction(self):
        la_str = """ d = b - c
                e = a_d 
                where
                a  ∈ ℝ^3
                b  ∈ ℤ index
                c  ∈ ℤ index"""
        func_info = self.gen_func_info(la_str)
        A = np.array([4, 5, 6])
        self.assertEqual(func_info.numpy_func(A, 3, 2).e, 4)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double(A.tolist()), 3, 2)['e']), 4)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> A;",
                     "    A << 4, 5, 6;",
                     "    double C = {}(A, 3, 2).e;".format(func_info.eig_func_name),
                     "    return (C == 4);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_ragged_array(self):
        # matrix
        la_str = """a = ∑_i ∑_j A_i,j  
        where
        A_i ∈ ℝ^(n_i)"""
        func_info = self.gen_func_info(la_str)
        A = [np.array([1, 1]), np.array([2, 2, 2]), np.array([3, 3, 3, 3])]
        self.assertEqual(func_info.numpy_func(A).a, 20)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 1> A1;",
                     "    A1 << 1, 1;",
                     "    Eigen::Matrix<double, 3, 1> A2;",
                     "    A2 << 2, 2, 2;",
                     "    Eigen::Matrix<double, 4, 1> A3;",
                     "    A3 << 3, 3, 3, 3;",
                     "    std::vector<Eigen::VectorXd> A;",
                     "    A.push_back(A1);",
                     "    A.push_back(A2);",
                     "    A.push_back(A3);",
                     "    double C = {}(A).a;".format(func_info.eig_func_name),
                     "    return C == 20;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    # def test_ragged_array1(self):
    #     # matrix
    #     la_str = """a = ∑_i n_i m_i
    #     where
    #     A_i ∈ ℝ^(n_i×m_i) """
    #     func_info = self.gen_func_info(la_str)
    #     A = [np.array([[1, 0], [0, 1]]), np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])]
    #     self.assertEqual(func_info.numpy_func(A).a, 13)
    #     # eigen test
    #     cppyy.include(func_info.eig_file_name)
    #     func_list = ["bool {}(){{".format(func_info.eig_test_name),
    #                  "    Eigen::Matrix<double, 2, 2> A1;",
    #                  "    A1 << 1, 0, 0, 1;",
    #                  "    Eigen::Matrix<double, 3, 3> A2;",
    #                  "    A2 << 1, 0, 0, 0, 1, 0, 0, 0, 1;",
    #                  "    std::vector<Eigen::MatrixXd> A;",
    #                  "    A.push_back(A1);",
    #                  "    A.push_back(A2);",
    #                  "    double C = {}(A).a;".format(func_info.eig_func_name),
    #                  "    return C == 13;",
    #                  "}"]
    #     cppyy.cppdef('\n'.join(func_list))
    #     self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_ragged_array2(self):
        # matrix
        la_str = """a = ∑_i ∑_j (A_i,j,* B_i)
        where
        A_i ∈ ℝ^(n_i×m_i)
        B_i ∈ ℝ^m_i"""
        func_info = self.gen_func_info(la_str)
        A = [np.array([[1, 0], [0, 1]]), np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])]
        B = [np.array([1, 1]), np.array([2, 2, 2])]
        self.assertEqual(func_info.numpy_func(A, B).a, 8)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A1;",
                     "    A1 << 1, 0, 0, 1;",
                     "    Eigen::Matrix<double, 3, 3> A2;",
                     "    A2 << 1, 0, 0, 0, 1, 0, 0, 0, 1;",
                     "    std::vector<Eigen::MatrixXd> A;",
                     "    A.push_back(A1);",
                     "    A.push_back(A2);",
                     "    Eigen::Matrix<double, 2, 1> B1;",
                     "    B1 << 1, 1;",
                     "    Eigen::Matrix<double, 3, 1> B2;",
                     "    B2 << 2, 2, 2;",
                     "    std::vector<Eigen::VectorXd> B;",
                     "    B.push_back(B1);",
                     "    B.push_back(B2);",
                     "    double C = {}(A, B).a;".format(func_info.eig_func_name),
                     "    return C == 8;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_arith_dims(self):
        # matrix
        la_str = """w ∈ ℝ^(p×k)
        x = [ w
              0_1,k ]
        a = x + y
        where
        y ∈ ℝ^((p+1)×k)"""
        func_info = self.gen_func_info(la_str)
        w = np.array([[1, 1, 1], [2, 2, 2]])
        y = np.array([[1, 1, 1], [2, 2, 2], [3, 3, 3]])
        a = np.array([[2, 2, 2], [4, 4, 4], [3, 3, 3]])
        self.assertDMatrixEqual(func_info.numpy_func(w, y).a, a)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(w.tolist()), matlab.double(y.tolist()))['a']), a)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 3> w;",
                     "    w << 1, 1, 1, 2, 2, 2;",
                     "    Eigen::Matrix<double, 3, 3> y;",
                     "    y << 1, 1, 1, 2, 2, 2, 3, 3, 3;",
                     "    Eigen::Matrix<double, 3, 3> a;",
                     "    a << 2, 2, 2, 4, 4, 4, 3, 3, 3;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(w, y).a;".format(func_info.eig_func_name),
                     "    return ((C - a).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_arith_dims_1(self):
        # matrix
        la_str = """w ∈ ℝ^(p×k) 
        y ∈ ℝ^(p(2k-k)/k×k)
        a = w + y"""
        func_info = self.gen_func_info(la_str)
        w = np.array([[1, 1, 1], [2, 2, 2], [3, 2, 3]])
        y = np.array([[1, 1, 1], [2, 2, 2], [3, 3, 3]])
        a = np.array([[2, 2, 2], [4, 4, 4], [6, 5, 6]])
        self.assertDMatrixEqual(func_info.numpy_func(w, y).a, a)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(w.tolist()), matlab.double(y.tolist()))['a']), a)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> w;",
                     "    w << 1, 1, 1, 2, 2, 2, 3, 2, 3;",
                     "    Eigen::Matrix<double, 3, 3> y;",
                     "    y << 1, 1, 1, 2, 2, 2, 3, 3, 3;",
                     "    Eigen::Matrix<double, 3, 3> a;",
                     "    a << 2, 2, 2, 4, 4, 4, 6, 5, 6;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(w, y).a;".format(func_info.eig_func_name),
                     "    return ((C - a).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())