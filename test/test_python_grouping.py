import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
from fractions import Fraction
import cppyy
cppyy.add_include_path(eigen_path)


class TestGrouping(BasePythonTest):
    # Floating-point + and * aren't associative: the generated code must keep the
    # parentheses the source wrote. Each value is checked bitwise against the same
    # expression grouped explicitly, on inputs where other groupings give other values.

    def assertBitwise(self, value, expected):
        value = np.asarray(value, dtype=np.float64)
        expected = np.asarray(expected, dtype=np.float64)
        self.assertEqual(value.shape, expected.shape)
        self.assertTrue(np.array_equal(value, expected), '{} != {}'.format(value, expected))

    def test_grouping_add_sub(self):
        la_str = """y = a + (b - c)
        w = a + (b + c)
        s = a - (b - c)
        z = (a - b) + (c - d)
        n = a + (b + (c + d))
        where
        a: scalar
        b: scalar
        c: scalar
        d: scalar"""
        func_info = self.gen_func_info(la_str)
        # 1 + 1e-16 rounds to 1, but 1 + 2e-16 doesn't
        a, b, c, d = 1.0, 1e-16, 1e-16, 1e-16
        r = func_info.numpy_func(a, b, c, d)
        self.assertBitwise(r.y, a + (b - c))
        self.assertNotEqual(a + (b - c), (a + b) - c)
        self.assertBitwise(r.w, a + (b + c))
        self.assertNotEqual(a + (b + c), (a + b) + c)
        self.assertBitwise(r.s, a - (b - c))
        self.assertBitwise(r.z, (a - b) + (c - d))
        self.assertBitwise(r.n, a + (b + (c + d)))
        self.assertNotEqual(a + (b + (c + d)), ((a + b) + c) + d)
        # 0.49999999999999994, not 0.5
        self.assertBitwise(func_info.numpy_func(1.0, 1e-16, 0.2, 0.7).z, (1.0 - 1e-16) + (0.2 - 0.7))
        self.assertNotEqual((1.0 - 1e-16) + (0.2 - 0.7), ((1.0 - 1e-16) + 0.2) - 0.7)
        # overflow depends on grouping
        big = 1e308
        with np.errstate(over='ignore'):
            r = func_info.numpy_func(big, big, -big, 0.0)
        self.assertBitwise(r.w, big)
        self.assertBitwise(r.y, np.inf)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            m = mat_func(a, b, c, d)
            self.assertBitwise(m['y'], a + (b - c))
            self.assertBitwise(m['w'], a + (b + c))
            self.assertBitwise(mat_func(1.0, 1e-16, 0.2, 0.7)['z'], (1.0 - 1e-16) + (0.2 - 0.7))
            self.assertBitwise(m['n'], a + (b + (c + d)))
            self.assertBitwise(mat_func(big, big, -big, 0.0)['w'], big)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    double a = 1.0, b = 1e-16, c = 1e-16, d = 1e-16;",
                     "    auto r = {}(a, b, c, d);".format(func_info.eig_func_name),
                     "    auto o = {}(1e308, 1e308, -1e308, 0.0);".format(func_info.eig_func_name),
                     "    return r.y == a + (b - c) && r.w == a + (b + c) && r.s == a - (b - c)",
                     "        && r.n == a + (b + (c + d)) && o.w == 1e308",
                     "        && {}(1.0, 1e-16, 0.2, 0.7).z == (1.0 - 1e-16) + (0.2 - 0.7);".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_grouping_neg(self):
        # -(a - b) is not -a - b
        la_str = """y = -(a - b)
        z = c - (-(a + b))
        where
        a: scalar
        b: scalar
        c: scalar"""
        func_info = self.gen_func_info(la_str)
        r = func_info.numpy_func(3.0, 2.0, 1.0)
        self.assertBitwise(r.y, -1.0)
        self.assertBitwise(r.z, 6.0)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertBitwise(mat_func(3.0, 2.0, 1.0)['y'], -1.0)
            self.assertBitwise(mat_func(3.0, 2.0, 1.0)['z'], 6.0)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    auto r = {}(3.0, 2.0, 1.0);".format(func_info.eig_func_name),
                     "    return r.y == -1.0 && r.z == 6.0;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_grouping_mul_div(self):
        la_str = """y = a (b c)
        z = (a b) c
        q = a/(b/c)
        p = (a/b)/c
        where
        a: scalar
        b: scalar
        c: scalar"""
        func_info = self.gen_func_info(la_str)
        a, b, c = 1e308, 10.0, 0.1
        r = func_info.numpy_func(a, b, c)
        self.assertBitwise(r.y, a * (b * c))
        self.assertBitwise(r.z, (a * b) * c)
        self.assertNotEqual(a * (b * c), (a * b) * c)
        self.assertBitwise(r.q, a / (b / c))
        self.assertBitwise(r.p, (a / b) / c)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            m = mat_func(a, b, c)
            self.assertBitwise(m['y'], a * (b * c))
            self.assertBitwise(m['z'], (a * b) * c)
            self.assertBitwise(m['q'], a / (b / c))
            self.assertBitwise(m['p'], (a / b) / c)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    double a = 1e308, b = 10.0, c = 0.1;",
                     "    auto r = {}(a, b, c);".format(func_info.eig_func_name),
                     "    return r.y == a * (b * c) && r.z == (a * b) * c && r.q == a / (b / c) && r.p == (a / b) / c;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_grouping_vector_matrix(self):
        la_str = """v = x + (y + z)
        M = A + (B + C)
        P = A ∘ (B ∘ C)
        where
        x: ℝ^2
        y: ℝ^2
        z: ℝ^2
        A: ℝ^(2×2)
        B: ℝ^(2×2)
        C: ℝ^(2×2)"""
        func_info = self.gen_func_info(la_str)
        x, y, z = np.array([1.0, 1e308]), np.array([1e-16, 1e308]), np.array([1e-16, -1e308])
        A = np.array([[1.0, 1e308], [0.1, 3.0]])
        B = np.array([[1e-16, 1e308], [0.2, 1e200]])
        C = np.array([[1e-16, -1e308], [0.3, 1e-200]])
        self.addCleanup(lambda old=np.seterr(over='ignore'): np.seterr(**old))
        r = func_info.numpy_func(x, y, z, A, B, C)
        self.assertBitwise(r.v, x + (y + z))
        self.assertFalse(np.array_equal(x + (y + z), (x + y) + z))
        self.assertBitwise(r.M, A + (B + C))
        self.assertFalse(np.array_equal(A + (B + C), (A + B) + C))
        self.assertBitwise(r.P, A * (B * C))
        self.assertFalse(np.array_equal(A * (B * C), (A * B) * C))
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            m = mat_func(matlab.double(x.reshape(-1, 1).tolist()), matlab.double(y.reshape(-1, 1).tolist()),
                         matlab.double(z.reshape(-1, 1).tolist()), matlab.double(A.tolist()),
                         matlab.double(B.tolist()), matlab.double(C.tolist()))
            self.assertBitwise(np.array(m['v']).ravel(), x + (y + z))
            self.assertBitwise(np.array(m['M']), A + (B + C))
            self.assertBitwise(np.array(m['P']), A * (B * C))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 1> x, y, z;",
                     "    x << 1.0, 1e308; y << 1e-16, 1e308; z << 1e-16, -1e308;",
                     "    Eigen::Matrix<double, 2, 2> A, B, C;",
                     "    A << 1.0, 1e308, 0.1, 3.0;",
                     "    B << 1e-16, 1e308, 0.2, 1e200;",
                     "    C << 1e-16, -1e308, 0.3, 1e-200;",
                     "    auto r = {}(x, y, z, A, B, C);".format(func_info.eig_func_name),
                     "    Eigen::Matrix<double, 2, 1> v = x + (y + z);",
                     "    Eigen::Matrix<double, 2, 2> M = A + (B + C);",
                     "    Eigen::Matrix<double, 2, 2> P = A.cwiseProduct(B.cwiseProduct(C));",
                     "    return (r.v.array() == v.array()).all() && (r.M.array() == M.array()).all() && (r.P.array() == P.array()).all();",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_grouping_kahan_triangle_area(self):
        # Kahan's stable triangle area (sides a ≥ b ≥ c), on a needle triangle;
        # Heron's formula and regrouped versions lose most of the digits here
        la_str = """A = sqrt((a+(b+c))(c-(a-b))(c+(a-b))(a+(b-c)))/4
        where
        a: scalar
        b: scalar
        c: scalar"""
        func_info = self.gen_func_info(la_str)
        # a needle triangle (Heron's formula, or this one regrouped, is off by 4e-5 here),
        # and an almost degenerate one
        triangles = [(1.0, 0.99999999999997, 1e-12), (1.0, 0.5 + 1e-12, 0.5 + 1e-12)]
        exact = []
        for a, b, c in triangles:
            kahan = np.sqrt((a + (b + c)) * (c - (a - b)) * (c + (a - b)) * (a + (b - c))) / 4
            # exact: 16 A² from the floating-point sides, in rationals
            fa, fb, fc = Fraction(a), Fraction(b), Fraction(c)
            e = float((fa + fb + fc) * (fc - fa + fb) * (fc + fa - fb) * (fa + fb - fc)) ** 0.5 / 4
            exact.append(e)
            self.assertLess(abs(kahan - e), 4e-16 * e)
            value = func_info.numpy_func(a, b, c).A
            self.assertBitwise(value, kahan)
            self.assertLess(abs(value - e), 4e-16 * e)
            # MATLAB test
            if TEST_MATLAB:
                mat_func = getattr(mat_engine, func_info.mat_func_name, None)
                self.assertLess(abs(float(mat_func(a, b, c)['A']) - e), 4e-16 * e)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    double a0 = 1.0, b0 = 0.99999999999997, c0 = 1e-12;",
                     "    double a1 = 1.0, b1 = 0.5 + 1e-12, c1 = 0.5 + 1e-12;",
                     "    double area0 = {}(a0, b0, c0).A;".format(func_info.eig_func_name),
                     "    double area1 = {}(a1, b1, c1).A;".format(func_info.eig_func_name),
                     "    return std::abs(area0 - {0!r}) < 4e-16 * {0!r} && std::abs(area1 - {1!r}) < 4e-16 * {1!r};".format(*exact),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_power_nan_inf(self):
        # a NumPy power: inf on overflow, nan for a negative base and a fractional
        # exponent (not Python's OverflowError, or a complex number)
        la_str = """y = a^b
        z = a²
        where
        a: scalar
        b: scalar"""
        func_info = self.gen_func_info(la_str)
        with np.errstate(all='ignore'):
            r = func_info.numpy_func(-8.0, 1/3)
            self.assertTrue(np.isnan(r.y))
            r = func_info.numpy_func(1e200, 2.0)
            self.assertBitwise(r.y, np.inf)
            self.assertBitwise(r.z, np.inf)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    auto r = {}(-8.0, 1.0/3);".format(func_info.eig_func_name),
                     "    auto o = {}(1e200, 2.0);".format(func_info.eig_func_name),
                     "    return std::isnan(r.y) && std::isinf(o.y) && std::isinf(o.z);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())
