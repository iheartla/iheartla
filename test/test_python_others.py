import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)


class TestOthers(BasePythonTest):
    def test_integral_1(self):
        # no return symbol
        la_str = """c = int_[1, 2] ia 𝕕i
        where 
        a: scalar """
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(2).c, 3)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double([2]))['c']), 3)

    def test_integral_2(self):
        # no return symbol
        la_str = """c = int_1^2 ia 𝕕i
        where 
        a: scalar """
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(2).c, 3)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double([2]))['c']), 3)

    def test_nested_integral(self):
        # no return symbol
        la_str = """c = int_0^3  int_[1, 2] ia 𝕕i 𝕕j
        where 
        a: scalar """
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(2).c, 9)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(matlab.double([2]))['c']), 9)

    def test_optimization_argmin(self):
        # no return symbol
        la_str = """b = argmin_(i ∈ ℝ) 3i+a
        s.t.
        i > 4
        i < 9 
        where 
        a: scalar """
        func_info = self.gen_func_info(la_str)
        self.assertTrue(abs(func_info.numpy_func(2).b - 4) < 0.00001)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertTrue(abs(np.array(mat_func(matlab.double([2]))['b']) - 4) < 0.00001)

    def test_optimization_min(self):
        # no return symbol
        la_str = """b = min_(i ∈ ℝ) 3i+a
        s.t.
        i > 4
        i < 9 
        where 
        a: scalar """
        func_info = self.gen_func_info(la_str)
        self.assertTrue(abs(func_info.numpy_func(2).b - 14) < 0.00001)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertTrue(abs(np.array(mat_func(matlab.double([2]))['b']) - 14) < 0.00001)

    def test_optimization_argmax(self):
        # no return symbol
        la_str = """b = argmax_(i ∈ ℝ) 3i+a
        s.t.
        i > 4
        i < 9 
        where 
        a: scalar """
        func_info = self.gen_func_info(la_str)
        self.assertTrue(abs(func_info.numpy_func(2).b - 9) < 0.00001)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertTrue(abs(np.array(mat_func(matlab.double([2]))['b']) - 9) < 0.00001)

    def test_optimization_argmax_vec(self):
        # vector variable
        la_str = """b = argmax_(i ∈ ℝ^3) i⋅a
        s.t.
        i_1 > 4
        i_1 < 9
        i_2 > 4
        i_2 < 9
        i_3 > 4
        i_3 < 9
        where 
        a: ℝ^3 """
        func_info = self.gen_func_info(la_str)
        b = func_info.numpy_func([1, -1, 1]).b
        self.assertTrue(abs(b[0] - 9) < 0.00001)
        self.assertTrue(abs(b[1] - 4) < 0.00001)
        self.assertTrue(abs(b[2] - 9) < 0.00001)

    def test_optimization_argmax_matrix(self):
        # vector variable
        la_str = """b = argmax_(i ∈ ℝ^(2×2)) ||i||
        s.t.
        i_1,1 > 2
        i_1,1 < 3
        i_1,2 > 2
        i_1,2 < 3
        i_2,1 > 2
        i_2,1 < 3
        i_2,2 > 2
        i_2,2 < 3
        where 
        a: ℝ^3
        """
        func_info = self.gen_func_info(la_str)
        b = func_info.numpy_func([1, -1, 1]).b
        a = np.array([[3, 3], [3, 3]])
        self.assertDMatrixEqual(b, a)

    def test_optimization_max(self):
        # no return symbol
        la_str = """b = max_(i ∈ ℝ) 3i+a
        s.t.
        i > 4
        i < 9 
        where 
        a: scalar """
        func_info = self.gen_func_info(la_str)
        self.assertTrue(abs(func_info.numpy_func(2).b - 29) < 0.00001)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertTrue(abs(np.array(mat_func(matlab.double([2]))['b']) - 29) < 0.00001)

    def test_optimization_argmin_no_st(self):
        # no return symbol
        la_str = """b = argmin_(i ∈ ℝ) i^2 
        where 
        a: scalar """
        func_info = self.gen_func_info(la_str)
        self.assertTrue(abs(func_info.numpy_func(2).b == 0))
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertTrue(abs(np.array(mat_func(matlab.double([2]))['b'])) == 0)

    def test_optimization_argmin_in_cond(self):
        # no return symbol
        la_str = """b = argmin_(i ∈ ℝ) i^2 
        s.t.
        i ∈ s
        where 
        s: {ℝ} """
        func_info = self.gen_func_info(la_str)
        self.assertTrue(abs(func_info.numpy_func([2, 1, 4]).b - 1) < 0.00001)
        # MATLAB test
        # if TEST_MATLAB:
        #     mat_func = getattr(mat_engine, func_info.mat_func_name, None)
        #     self.assertTrue(abs(np.array(mat_func(matlab.double([2]))['b'])) == 0)
