import numpy as np
import scipy
import scipy.linalg
from scipy import sparse
from scipy.integrate import quad
from scipy.optimize import minimize


class Anisotropic:
    def __init__(self, a, C, F):
        a = np.asarray(a, dtype=np.float64)
        C = np.asarray(C, dtype=np.float64)
        F = np.asarray(F, dtype=np.float64)
        assert a.shape == (3,)
        assert C.shape == (3, 3)
        assert F.shape == (3, 3)
        # A = a a^T
        self.A = (a).reshape(3, 1) @ a.T.reshape(1, 3)
        # `$\lambda_{0,1,2}$`=2||a||_2^2
        self.lambda_0_comma_1_comma_2 = 2 * np.power(float(np.linalg.norm(a, 2)), 2)
        # `$I_5$` = tr(CA)
        self.I_5 = np.trace(C @ self.A)
        # `$\frac{∂I₅}{∂F}$` = 2FA
        self.frac_partial_differential_I5_partial_differential_F = 2 * F @ self.A
        # `$\frac{∂²I₅}{∂f²}$` = 2[A₁,₁I₃  A₁,₂I₃  A₁,₃I₃
    #                A₂,₁I₃  A₂,₂I₃  A₂,₃I₃
    #                A₃,₁I₃  A₃,₂I₃  A₃,₃I₃]
        frac_partial_differential_2I5_partial_differential_f2_0 = np.block([[self.A[1-1, 1-1] * np.identity(3), self.A[1-1, 2-1] * np.identity(3), self.A[1-1, 3-1] * np.identity(3)], [self.A[2-1, 1-1] * np.identity(3), self.A[2-1, 2-1] * np.identity(3), self.A[2-1, 3-1] * np.identity(3)], [self.A[3-1, 1-1] * np.identity(3), self.A[3-1, 2-1] * np.identity(3), self.A[3-1, 3-1] * np.identity(3)]])
        self.frac_partial_differential_2I5_partial_differential_f2 = 2 * frac_partial_differential_2I5_partial_differential_f2_0
        # `$\mathbf{Q}_{0}$` = [a^T
    #                0
    #                0]
        mathbfQ_0_0 = np.vstack((a.T.reshape(1, 3), np.zeros((1, 3)), np.zeros((1, 3))))
        self.mathbfQ_0 = mathbfQ_0_0
        # `$\mathbf{Q}_{1}$` = [0
    #                     a^T
    #                0]
        mathbfQ_1_0 = np.vstack((np.zeros((1, 3)), a.T.reshape(1, 3), np.zeros((1, 3))))
        self.mathbfQ_1 = mathbfQ_1_0
        # `$\mathbf{Q}_{2}$` = [ 0
    #                0
    #                a^T]
        mathbfQ_2_0 = np.vstack((np.zeros((1, 3)), np.zeros((1, 3)), a.T.reshape(1, 3)))
        self.mathbfQ_2 = mathbfQ_2_0

class Anisotropic2D:
    def __init__(self, a, A):
        a = np.asarray(a, dtype=np.float64)
        A = np.asarray(A, dtype=np.float64)
        assert a.shape == (2,)
        assert A.shape == (2, 2)
        # `$\lambda_{0,1}$`=2||a||_2^2
        self.lambda_0_comma_1 = 2 * np.power(float(np.linalg.norm(a, 2)), 2)
        # `$\frac{∂²I₅}{∂f²}$` = 2[A₁,₁I_2  A₁,₂I_2
    #                A₂,₁I_2  A₂,₂I_2]
        frac_partial_differential_2I5_partial_differential_f2_0 = np.block([[A[1-1, 1-1] * np.identity(2), A[1-1, 2-1] * np.identity(2)], [A[2-1, 1-1] * np.identity(2), A[2-1, 2-1] * np.identity(2)]])
        self.frac_partial_differential_2I5_partial_differential_f2 = 2 * frac_partial_differential_2I5_partial_differential_f2_0
        # `$\mathbf{Q}_{0}$` = [a^T
    #                0]
        mathbfQ_0_0 = np.vstack((a.T.reshape(1, 2), np.zeros((1, 2))))
        self.mathbfQ_0 = mathbfQ_0_0
        # `$\mathbf{Q}_{1}$` = [0
    #                     a^T]
        mathbfQ_1_0 = np.vstack((np.zeros((1, 2)), a.T.reshape(1, 2)))
        self.mathbfQ_1 = mathbfQ_1_0

