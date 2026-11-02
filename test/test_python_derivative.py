import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import unittest

try:
    import autograd  # noqa: F401  (NumPy output with derivatives uses autograd)
    HAS_AUTOGRAD = True
except ImportError:
    HAS_AUTOGRAD = False


@unittest.skipUnless(HAS_AUTOGRAD, "needs autograd")
class TestDerivative(BasePythonTest):
    def test_gradient_hessian(self):
        # of a definition (the program recomputed) and of a local function, with respect to a vector
        la_str = """sin from trigonometry
                    A = x ⋅ x + sin(x_1)
                    G = ∂A/∂x
                    H = ∂²A/∂x²
                    f(y) = y ⋅ y where y ∈ ℝ^3
                    K = ∂²f(x)/∂x²
                    where
                    x ∈ ℝ^3"""
        func_info = self.gen_func_info(la_str)
        x = np.array([0.3, -1., 2.])
        h = func_info.numpy_func(x)
        self.assertDMatrixApproximateEqual(h.G, 2 * x + np.array([np.cos(x[0]), 0, 0]))
        self.assertDMatrixApproximateEqual(h.H, np.diag([2 - np.sin(x[0]), 2, 2]))
        self.assertDMatrixApproximateEqual(h.K, 2 * np.eye(3))

    def test_derivative_piecewise_sequence(self):
        # through a piecewise local function, with respect to a sequence (flattened, as in C++)
        la_str = """S(x) = { ∞ if x_1 ⋅ x_2 ≤ 0
                             (x_1 ⋅ x_2)² otherwise where x_i ∈ ℝ^2
                    E = S(x)
                    G = ∂E/∂x
                    where
                    x_i ∈ ℝ^2"""
        func_info = self.gen_func_info(la_str)
        x = np.array([[1., 2.], [3., 4.]])
        h = func_info.numpy_func(x)
        d = x[0] @ x[1]
        self.assertAlmostEqual(h.E, d ** 2)
        self.assertDMatrixApproximateEqual(h.G, np.concatenate([2 * d * x[1], 2 * d * x[0]]))
