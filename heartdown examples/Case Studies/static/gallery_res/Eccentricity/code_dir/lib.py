import numpy as np
import scipy
import scipy.linalg
from scipy import sparse
from scipy.integrate import quad
from scipy.optimize import minimize


class eccentricity:
    def __init__(self, m, 𝑝, 𝑓_𝑠0, a):
        𝑝 = np.asarray(𝑝, dtype=np.float64)
        assert 𝑝.shape == (10,)
        assert np.ndim(𝑓_𝑠0) == 0
        assert np.ndim(a) == 0

        self.m = m
        self.𝑓_𝑠0 = 𝑓_𝑠0
        self.𝑝 = 𝑝
        self.a = a
        # `$𝑙_0$` = 1488
        self.𝑙_0 = 1488
        # q = (5.71 ⋅ 10^(-6), -1.78 ⋅ 10^(-4), 0.204)
        self.q = np.hstack((5.71 * np.power(float(10), (-6)), -1.78 * np.power(float(10), (-4)), 0.204))

    def 𝑔(self, x, x_0, 𝜃, 𝜎, 𝑓_𝑠):
        x = np.asarray(x, dtype=np.float64)
        x_0 = np.asarray(x_0, dtype=np.float64)
        assert x.shape == (2,)
        assert x_0.shape == (2,)
        assert np.ndim(𝜃) == 0
        assert np.ndim(𝜎) == 0
        assert np.ndim(𝑓_𝑠) == 0

        return np.exp(-np.power(float(np.linalg.norm(x - x_0, 2)), 2) / (2 * np.power(float(𝜎), 2))) * np.cos(np.dot((2 * np.pi * 𝑓_𝑠 * x).ravel(), (np.hstack((np.cos(𝜃), np.sin(𝜃)))).ravel()))

    def 𝜏(self, 𝑓_𝑠):
        assert np.ndim(𝑓_𝑠) == 0

        return self.m(np.log10(𝑓_𝑠) - np.log10(self.𝑓_𝑠0), 0)

    def 𝜁(self, 𝑓_𝑠):
        assert np.ndim(𝑓_𝑠) == 0

        return np.exp(self.𝑝[10-1] * self.𝜏(𝑓_𝑠)) - 1

    def Ψ(self, 𝑒, 𝑓_𝑠):
        assert np.ndim(𝑒) == 0
        assert np.ndim(𝑓_𝑠) == 0

        return self.m(0, self.𝑝[1-1] * np.power(float(self.𝜏(𝑓_𝑠)), 2) + self.𝑝[2-1] * self.𝜏(𝑓_𝑠) + self.𝑝[3-1] + (self.𝑝[4-1] * np.power(float(self.𝜏(𝑓_𝑠)), 2) + self.𝑝[5-1] * self.𝜏(𝑓_𝑠) + self.𝑝[6-1]) * self.𝜁(𝑓_𝑠) * 𝑒 + (self.𝑝[7-1] * np.power(float(self.𝜏(𝑓_𝑠)), 2) + self.𝑝[8-1] * self.𝜏(𝑓_𝑠) + self.𝑝[9-1]) * self.𝜁(𝑓_𝑠) * np.power(float(𝑒), 2))

    def 𝐴(self, 𝑒):
        assert np.ndim(𝑒) == 0

        return np.log(64) * 2.3 / (0.106 * (𝑒 + 2.3))

    def 𝑑(self, 𝐿):
        assert np.ndim(𝐿) == 0

        return 7.75 - 5.75 * (np.power(float((𝐿 * self.a / 846)), 0.41) / (np.power(float((𝐿 * self.a / 846)), 0.41) + 2))

    def 𝑙(self, 𝐿):
        assert np.ndim(𝐿) == 0

        return np.pi * np.power(float(self.𝑑(𝐿)), 2) / 4 * 𝐿

    def 𝑠(self, 𝑒, 𝑓_𝑠):
        assert np.ndim(𝑒) == 0
        assert np.ndim(𝑓_𝑠) == 0

        return self.𝜁(𝑓_𝑠) * (self.q[1-1] * np.power(float(𝑒), 2) + self.q[2-1] * 𝑒) + self.q[3-1]

    def hatΨ(self, 𝑒, 𝑓_𝑠, 𝐿):
        assert np.ndim(𝑒) == 0
        assert np.ndim(𝑓_𝑠) == 0
        assert np.ndim(𝐿) == 0

        return (self.𝑠(𝑒, 𝑓_𝑠) * (np.log10(self.𝑙(𝐿) / self.𝑙_0)) + 1) * self.Ψ(𝑒, 𝑓_𝑠)

