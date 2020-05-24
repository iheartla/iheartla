import sys
sys.path.append('./')
from la_test.base_python_test import BasePythonTest, eigen_path, TestFuncInfo
from la_parser.parser import parse_la, ParserTypeEnum
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)


class TestExpr(BasePythonTest):
    def test_multiplication_0(self):
        # space
        la_str = """c = a b
        where
        a: scalar
        b: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3, 2), 6)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    if({}(3, 4) == 12){{".format(func_info.eig_func_name),
                     "        return true;",
                     "    }",
                     "    return false;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_multiplication_1(self):
        # star
        la_str = """c = a * b
        where
        a: scalar
        b: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3, 2), 6)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    if({}(3, 4) == 12){{".format(func_info.eig_func_name),
                     "        return true;",
                     "    }",
                     "    return false;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_multiplication_2(self):
        # matrix
        la_str = """c = a * A
                where
                a: scalar
                A: ℝ ^ (2 × 2): a matrix"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[2, 4], [6, 8]])
        self.assertDMatrixEqual(func_info.numpy_func(2, A), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 2, 4, 6, 8;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(2, A);".format(func_info.eig_func_name),
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
        B = np.asarray(B, dtype=np.floating)
        self.assertDMatrixEqual(func_info.numpy_func(A, C), np.linalg.solve(A, C))

    def test_unary_scalar_0(self):
        la_str = """b = -2a
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3), -6)
        self.assertEqual(func_info.numpy_func(-3), 6)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    if({}(3) == -6 && {}(-3) == 6){{".format(func_info.eig_func_name, func_info.eig_func_name),
                     "        return true;",
                     "    }",
                     "    return false;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_unary_scalar_1(self):
        la_str = """b = -a2
        where
        a: scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(3), -6)
        self.assertEqual(func_info.numpy_func(-3), 6)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    if({}(3) == -6 && {}(-3) == 6){{".format(func_info.eig_func_name, func_info.eig_func_name),
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
        self.assertEqual(func_info.numpy_func(3), -5)
        self.assertEqual(func_info.numpy_func(-3), 1)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    if({}(3) == -5 && {}(-3) == 1){{".format(func_info.eig_func_name, func_info.eig_func_name),
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
        self.assertEqual(func_info.numpy_func(3), -5)
        self.assertEqual(func_info.numpy_func(-3), 1)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    if({}(3) == -5 && {}(-3) == 1){{".format(func_info.eig_func_name, func_info.eig_func_name),
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
        self.assertDMatrixEqual(func_info.numpy_func(A), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << -2, -4, -6, -8;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A);".format(func_info.eig_func_name),
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
        self.assertDMatrixEqual(func_info.numpy_func(A), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << -2, -4, -6, -8;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A);".format(func_info.eig_func_name),
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
        self.assertDMatrixEqual(func_info.numpy_func(A), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << -3, -4, -5, -6;",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A);".format(func_info.eig_func_name),
                     "    return ((B - C).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())