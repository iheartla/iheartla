import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)
if TEST_MATLAB:
    import matlab


class TestIntDivision(BasePythonTest):
    # Division of integers is real division, and its type is ℝ, in every backend (7/2 is 3.5,
    # 1/2 is 0.5); so are negative powers of integers (i^(-1), 2^(-1)). The C++ backend used to
    # declare `int y` for `y = 1/2` (giving 0) and to divide integers with C++'s truncating `/`.
    def check_scalar(self, la_str, args, expected):
        # y is a real (double in C++) equal to `expected` in NumPy, C++ and MATLAB
        func_info = self.gen_func_info(la_str)
        y = func_info.numpy_func(*args).y
        self.assertEqual(y, expected)
        self.assertNotIsInstance(y, (int, np.integer))
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(*[matlab.double([a]) for a in args])['y']), expected)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    static_assert(std::is_same<decltype({}::y), double>::value, \"y must be double\");".format(func_info.eig_func_name),
                     "    return {}({}).y == {};".format(func_info.eig_func_name, ', '.join(str(a) for a in args), repr(float(expected))),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_literal_half(self):
        self.check_scalar("""y = 1/2
        where
        a ∈ ℝ""", [1.0], 0.5)

    def test_literal_thirds(self):
        self.check_scalar("""y = 1/3 + 1/3
        where
        a ∈ ℝ""", [1.0], 1/3 + 1/3)

    def test_literal_negative_power(self):
        self.check_scalar("""y = 2^(-1)
        where
        a ∈ ℝ""", [1.0], 0.5)

    def test_int_div(self):
        self.check_scalar("""y = i/j
        where
        i, j ∈ ℤ""", [7, 2], 3.5)

    def test_int_div_unicode(self):
        self.check_scalar("""y = i÷j
        where
        i, j ∈ ℤ""", [7, 2], 3.5)

    def test_int_div_sum(self):
        self.check_scalar("""y = (i + j)/k
        where
        i, j, k ∈ ℤ""", [7, 2, 4], 2.25)

    def test_int_div_chain(self):
        self.check_scalar("""y = i/j/k
        where
        i, j, k ∈ ℤ""", [7, 2, 4], 0.875)

    def test_int_div_nested(self):
        self.check_scalar("""y = i/(j/k)
        where
        i, j, k ∈ ℤ""", [7, 3, 2], 7 / (3 / 2))

    def test_int_negative_power(self):
        self.check_scalar("""y = i^(-1)
        where
        i ∈ ℤ""", [2], 0.5)

    def test_int_div_used_downstream(self):
        # the quotient is real where it is used: z = (i/j)·2 is 7, not 6
        la_str = """y = i/j
        z = y + y
        where
        i, j ∈ ℤ"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(7, 2).z, 7.0)
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double([7]), matlab.double([2]))['z']), 7.0)
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    static_assert(std::is_same<decltype({}::z), double>::value, \"z must be double\");".format(func_info.eig_func_name),
                     "    return {}(7, 2).z == 7.0;".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_int_vector_div(self):
        # an integer vector divided by an integer is a real vector
        la_str = """y = v/2
        where
        v ∈ ℤ^3"""
        func_info = self.gen_func_info(la_str)
        v = np.array([1, 2, 3])
        y = func_info.numpy_func(v).y
        self.assertDMatrixEqual(y, np.array([0.5, 1.0, 1.5]))
        self.assertTrue(np.issubdtype(y.dtype, np.floating))
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(v.tolist()))['y']).reshape(-1), np.array([0.5, 1.0, 1.5]))
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    static_assert(std::is_same<decltype({}::y)::Scalar, double>::value, \"y must be real\");".format(func_info.eig_func_name),
                     "    Eigen::Matrix<int, 3, 1> v;",
                     "    v << 1, 2, 3;",
                     "    Eigen::Matrix<double, 3, 1> B;",
                     "    B << 0.5, 1.0, 1.5;",
                     "    return {}(v).y == B;".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_division_in_dimension(self):
        # A dimension must be an integer: n/2 in a dimension is exact division, and every
        # backend asserts that it divides evenly. The block matrix needs the size n/2 as an int.
        la_str = """y = [x; 1]
        where
        x ∈ ℝ^(n/2)
        n ∈ ℤ"""
        func_info = self.gen_func_info(la_str)
        x = np.array([1.0, 2.0, 3.0])
        self.assertDMatrixEqual(func_info.numpy_func(x, 6).y, np.array([[1.0], [2.0], [3.0], [1.0]]))
        with self.assertRaises(AssertionError):
            func_info.numpy_func(x, 7)
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(x.tolist()), matlab.double([6]))['y']).reshape(-1),
                                    np.array([1.0, 2.0, 3.0, 1.0]))
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::VectorXd x(3);",
                     "    x << 1, 2, 3;",
                     "    Eigen::VectorXd B(4);",
                     "    B << 1, 2, 3, 1;",
                     "    return {}(x, 6).y == B;".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())
        # (C++ checks divisibility with real division: `fmod(n/2, 1)` with int n was always 0)
        content = compile_la_content(la_str, ParserTypeEnum.EIGEN)[ParserTypeEnum.EIGEN]
        self.assertNotIn('fmod(n/2, 1)', content)

    def test_division_in_dimension_loop(self):
        # a vector defined element by element over a dimension n/2: its size and loop bound are int
        la_str = """y_i = x_i + 1
        where
        x ∈ ℝ^(n/2)
        n ∈ ℤ"""
        func_info = self.gen_func_info(la_str)
        x = np.array([1.0, 2.0, 3.0])
        self.assertDMatrixEqual(func_info.numpy_func(x, 6).y, np.array([2.0, 3.0, 4.0]))
        with self.assertRaises(AssertionError):
            func_info.numpy_func(x, 7)
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(x.tolist()), matlab.double([6]))['y']).reshape(-1),
                                    np.array([2.0, 3.0, 4.0]))
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::VectorXd x(3);",
                     "    x << 1, 2, 3;",
                     "    Eigen::VectorXd B(3);",
                     "    B << 2, 3, 4;",
                     "    return {}(x, 6).y == B;".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_division_in_subscript(self):
        # A subscript must be an integer, and i/2 is real: a compile error (C++ used to truncate
        # 3.5 to 3 silently, NumPy raised an IndexError at run time)
        la_str = """y = v_(i/2)
        where
        v ∈ ℝ^3
        i ∈ ℤ"""
        with self.assertRaises(AssertionError) as cm:
            compile_la_content(la_str, ParserTypeEnum.NUMPY)
        self.assertIn('integer', str(cm.exception))
