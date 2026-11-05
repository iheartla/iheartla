import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)
if TEST_MATLAB:
    import matlab


class TestSize(BasePythonTest):
    # The size operator #x (iheartla#142): a vector's length, a sequence's length, a set's size, a
    # matrix's (rows, cols). In a dimension, #a names a's size (x ∈ ℝ^(#a)). It used to crash the
    # compiler in NumPy and MATLAB, and in any dimension.
    def check_int(self, la_str, np_args, eig_decls, eig_args, mat_args, name, expected):
        func_info = self.gen_func_info(la_str)
        self.assertEqual(getattr(func_info.numpy_func(*np_args), name), expected)
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(*mat_args)[name]), expected)
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name)] + eig_decls + [
                     "    return {}({}).{} == {};".format(func_info.eig_func_name, ', '.join(eig_args), name, expected),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_vector(self):
        self.check_int("""y = #a
        where
        a ∈ ℝ^n""", [np.array([1., 2., 3.])],
                       ["    Eigen::VectorXd a(3);", "    a << 1, 2, 3;"], ["a"],
                       [matlab.double([[1], [2], [3]])] if TEST_MATLAB else [], "y", 3)

    def test_sequence(self):
        self.check_int("""y = #a
        where
        a_i ∈ ℝ""", [np.array([1., 2., 3., 4.])],
                       ["    std::vector<double> a = {1, 2, 3, 4};"], ["a"],
                       [matlab.double([[1], [2], [3], [4]])] if TEST_MATLAB else [], "y", 4)

    def test_set(self):
        self.check_int("""y = #S
        where
        S ∈ {ℤ}""", [{1, 5, 7}],
                       ["    std::vector<int> S = {1, 5, 7};"], ["S"],
                       [matlab.int32([[1], [5], [7]])] if TEST_MATLAB else [], "y", 3)

    def test_matrix_rows_cols(self):
        la_str = """m, n = #A
        where
        A ∈ ℝ^(2×3)"""
        A = np.arange(6.).reshape(2, 3)
        decls = ["    Eigen::Matrix<double, 2, 3> A;", "    A << 0, 1, 2, 3, 4, 5;"]
        mat = [matlab.double(A.tolist())] if TEST_MATLAB else []
        self.check_int(la_str, [A], decls, ["A"], mat, "m", 2)
        self.check_int(la_str, [A], decls, ["A"], mat, "n", 3)

    def test_size_in_expression(self):
        self.check_int("""y = 2#a + 1
        where
        a ∈ ℝ^n""", [np.array([1., 2., 3.])],
                       ["    Eigen::VectorXd a(3);", "    a << 1, 2, 3;"], ["a"],
                       [matlab.double([[1], [2], [3]])] if TEST_MATLAB else [], "y", 7)

    def test_dimension_of_sequence(self):
        # x has as many entries as the sequence a, which names no size of its own
        la_str = """y = x + x
        where
        a_i ∈ ℝ
        x ∈ ℝ^(#a)"""
        func_info = self.gen_func_info(la_str)
        a = np.array([1., 2., 3.])
        np.testing.assert_array_equal(func_info.numpy_func(a, np.array([1., 2., 3.])).y, [2., 4., 6.])
        with self.assertRaises(AssertionError):
            func_info.numpy_func(a, np.array([1., 2.]))

    def test_dimension_arithmetic(self):
        la_str = """y = x + x
        where
        a ∈ ℝ^n
        x ∈ ℝ^(#a+1)"""
        func_info = self.gen_func_info(la_str)
        np.testing.assert_array_equal(func_info.numpy_func(np.ones(2), np.ones(3)).y, [2., 2., 2.])
        with self.assertRaises(AssertionError):
            func_info.numpy_func(np.ones(2), np.ones(2))

    def test_dimension_of_matrix_is_an_error(self):
        # #A is a pair, which can't be one dimension
        with self.assertRaises(AssertionError):
            compile_la_content("""y = x + x
            where
            A ∈ ℝ^(2×3)
            x ∈ ℝ^(#A)""", ParserTypeEnum.NUMPY)

    def test_latex(self):
        tex = compile_la_content("""y = #a
        where
        a_i ∈ ℝ
        x ∈ ℝ^(#a)""", ParserTypeEnum.LATEX)[ParserTypeEnum.LATEX]
        self.assertIn('\\#a', tex)
        self.assertNotIn('dim_0', tex)
