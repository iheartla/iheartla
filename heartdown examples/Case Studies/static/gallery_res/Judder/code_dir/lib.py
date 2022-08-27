import numpy as np
import scipy
import scipy.linalg
from scipy import sparse
from scipy.integrate import quad
from scipy.optimize import minimize


class judder:
    def __init__(self, F, L, S, P, a, b, M, L_a, L_b):
        assert np.ndim(F) == 0
        assert np.ndim(L) == 0
        assert np.ndim(S) == 0
        assert np.ndim(a) == 0
        assert np.ndim(b) == 0
        assert np.ndim(M) == 0
        assert np.ndim(L_a) == 0
        assert np.ndim(L_b) == 0

        self.L = L
        self.a = a
        self.b = b
        self.F = F
        # `$F_a$` = M⋅ CFF(`$L_a$`)
        self.F_a = M * self.CFF(L_a)
        # `$F_b$` = M⋅ CFF(`$L_b$`)
        self.F_b = M * self.CFF(L_b)
        # J = P(α(F), β(L), S)
        self.J = P(self.α(F), self.β(L), S)

    def CFF(self, L):
        assert np.ndim(L) == 0

        return self.a * np.log(L) + self.b

    def α(self, F):
        assert np.ndim(F) == 0

        return 1 / F

    def β(self, L):
        assert np.ndim(L) == 0

        return np.log10(L)

class error:
    def __init__(self, O, M):
        O = np.asarray(O, dtype=np.float64)
        M = np.asarray(M, dtype=np.float64)
        N = O.shape[0]
        assert O.shape == (N,)
        assert M.shape == (N,)
        # E = sum_i |log(O_i) - log(M_i)|/log(O_i)
        sum_0 = 0
        for i in range(1, len(M)+1):
            sum_0 += np.absolute(np.log(O[i-1]) - np.log(M[i-1])) / np.log(O[i-1])
        self.E = sum_0

class third:
    def __init__(self, a, b, F_b, F_a, L_a):
        assert np.ndim(a) == 0
        assert np.ndim(b) == 0
        assert np.ndim(F_b) == 0
        assert np.ndim(F_a) == 0
        assert np.ndim(L_a) == 0
        # `$L_b$` = 10^((a `$F_b$`log((`$L_a$`))+b(`$F_b$`-`$F_a$`))/(a`$F_a$`))
        self.L_b = np.power(float(10), ((a * F_b * np.log((L_a)) + b * (F_b - F_a)) / (a * F_a)))

