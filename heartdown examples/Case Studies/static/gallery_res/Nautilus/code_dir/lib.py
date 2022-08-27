import numpy as np
import scipy
import scipy.linalg
from scipy import sparse
from scipy.integrate import quad
from scipy.optimize import minimize


class nautilus:
    def __init__(self, x, λ, v):
        x = np.asarray(x, dtype=np.float64)
        v = np.asarray(v, dtype=np.float64)
        n = x.shape[0]
        dim_0 = v.shape[0]
        assert x.shape == (n,)
        assert np.ndim(λ) == 0
        assert v.shape == (dim_0, 3, 3)

        self.x = x
        self.λ = λ
        self.v = v
        # P = [1 x₁ 0
    #      0 x₂ 0
    #      x₃ x₄ 1]
        P_0 = np.zeros((3, 3))
        P_0[0] = [1, x[1-1], 0]
        P_0[1] = [0, x[2-1], 0]
        P_0[2] = [x[3-1], x[4-1], 1]
        self.P = P_0
        # S = [x₅ x₆ x₇
    #      x₈ x₉ x₁₀
    #      0 0 1]
        S_0 = np.zeros((3, 3))
        S_0[0] = [x[5-1], x[6-1], x[7-1]]
        S_0[1] = [x[8-1], x[9-1], x[10-1]]
        S_0[2] = [0, 0, 1]
        self.S = S_0
        # H = PSP⁻¹
        self.H = self.P @ self.S @ np.linalg.inv(self.P)

    def E(self, x):
        x = np.asarray(x, dtype=np.float64)
        n = x.shape[0]
        assert x.shape == (n,)

        sum_0 = 0
        for i in range(1, len(self.v)+1):
            sum_0 += np.power(float(np.linalg.norm(self.H @ self.v[i-1] - self.P @ self.S @ np.linalg.solve(self.P, self.v[i-1]), 'fro')), 2)
        return self.λ * np.power(float(np.linalg.norm(np.hstack((x[5-1], x[8-1])) - np.hstack((x[9-1], x[6-1])), 2)), 2) + sum_0

