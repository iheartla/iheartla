import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)


class TestOthers(BasePythonTest):
    def test_integral_1(self):
        # no return symbol
        la_str = """c = int_[1, 2] ia ∂i
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
        la_str = """c = int_1^2 ia ∂i
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
        la_str = """c = int_0^3  int_[1, 2] ia ∂i ∂j
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

    def test_optimization_argmin_no_st(self):
        # no return symbol
        la_str = """b = argmin_(i ∈ ℝ) i^2 
        where 
        a: scalar """
        func_info = self.gen_func_info(la_str)
        self.assertTrue(abs(func_info.numpy_func(2).b == 0))

    def test_optimization_argmin_in_cond(self):
        # no return symbol
        la_str = """b = argmin_(i ∈ ℝ) i^2 
        s.t.
        i ∈ s
        where 
        s: {ℝ} """
        func_info = self.gen_func_info(la_str)
        self.assertTrue(abs(func_info.numpy_func([2, 1, 4]).b - 1) < 0.00001)
