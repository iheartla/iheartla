import numpy as np
import scipy
import scipy.linalg
from scipy import sparse
from scipy.integrate import quad
from scipy.optimize import minimize


class Regularized:
    def __init__(self, r, boldsymbolf, s, boldsymbolF, r_ε, a, b, ε):
        boldsymbolf = np.asarray(boldsymbolf, dtype=np.float64)
        boldsymbolF = np.asarray(boldsymbolF, dtype=np.float64)
        assert np.ndim(r) == 0
        assert boldsymbolf.shape == (3,)
        assert np.ndim(s) == 0
        assert boldsymbolF.shape == (3, 3)
        assert np.ndim(r_ε) == 0
        assert np.ndim(a) == 0
        assert np.ndim(b) == 0
        assert np.ndim(ε) == 0

        self.a = a
        self.b = b
        self.r = r
        self.boldsymbolf = boldsymbolf
        self.r_ε = r_ε
        self.ε = ε
        self.boldsymbolF = boldsymbolF
        self.s = s
        pass

    def boldsymbolu(self, boldsymbolr):
        boldsymbolr = np.asarray(boldsymbolr, dtype=np.float64)
        assert boldsymbolr.shape == (3,)

        return ((self.a - self.b) / self.r * np.identity(3) + (self.b / np.power(float(self.r), 3) * boldsymbolr).reshape(3, 1) @ boldsymbolr.T.reshape(1, 3)) @ self.boldsymbolf

    def rho_ε(self, boldsymbolr):
        boldsymbolr = np.asarray(boldsymbolr, dtype=np.float64)
        assert boldsymbolr.shape == (3,)

        return (15 * np.power(float(self.r_ε), 4) / (8 * np.pi) + 1 / np.power(float(self.r_ε), 7))

    def boldsymbolu_ε(self, boldsymbolr):
        boldsymbolr = np.asarray(boldsymbolr, dtype=np.float64)
        assert boldsymbolr.shape == (3,)

        return ((self.a - self.b) / self.r_ε * np.identity(3) + (self.b / np.power(float(self.r_ε), 3) * boldsymbolr).reshape(3, 1) @ boldsymbolr.T.reshape(1, 3) + self.a * np.power(float(self.ε), 2) / (2 * np.power(float(self.r_ε), 3)) * np.identity(3)) @ self.boldsymbolf

    def tildeboldsymbolu_ε(self, boldsymbolr):
        boldsymbolr = np.asarray(boldsymbolr, dtype=np.float64)
        assert boldsymbolr.shape == (3,)

        return -self.a * (1 / np.power(float(self.r_ε), 3) + 3 * np.power(float(self.ε), 2) / (2 * np.power(float(self.r_ε), 5))) * self.boldsymbolF @ boldsymbolr + self.b * (1 / np.power(float(self.r_ε), 3) * (self.boldsymbolF + self.boldsymbolF.T + np.trace(self.boldsymbolF) * np.identity(3)) - 3 / np.power(float(self.r_ε), 5) * ((boldsymbolr.T.reshape(1, 3) @ self.boldsymbolF @ boldsymbolr).item()) * np.identity(3)) @ boldsymbolr

    def boldsymbolt_ε(self, boldsymbolr):
        boldsymbolr = np.asarray(boldsymbolr, dtype=np.float64)
        assert boldsymbolr.shape == (3,)

        return -self.a * (1 / np.power(float(self.r_ε), 3) + 3 * np.power(float(self.ε), 2) / (2 * np.power(float(self.r_ε), 5))) * self.boldsymbolF @ boldsymbolr

    def boldsymbols_ε(self, boldsymbolr):
        boldsymbolr = np.asarray(boldsymbolr, dtype=np.float64)
        assert boldsymbolr.shape == (3,)

        return (2 * self.b - self.a) * (1 / np.power(float(self.r_ε), 3) + 3 * np.power(float(self.ε), 2) / (2 * np.power(float(self.r_ε), 5))) * (self.s * boldsymbolr)

    def boldsymbolp_ε(self, boldsymbolr):
        boldsymbolr = np.asarray(boldsymbolr, dtype=np.float64)
        assert boldsymbolr.shape == (3,)

        return (2 * self.b - self.a) / np.power(float(self.r_ε), 3) * self.boldsymbolF @ boldsymbolr - 3 / (2 * np.power(float(self.r_ε), 5)) * (2 * self.b * ((boldsymbolr.T.reshape(1, 3) @ self.boldsymbolF @ boldsymbolr).item()) * np.identity(3) + self.a * np.power(float(self.ε), 2) * self.boldsymbolF) @ boldsymbolr

