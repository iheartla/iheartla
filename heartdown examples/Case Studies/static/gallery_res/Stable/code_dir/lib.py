import numpy as np
import scipy
import scipy.linalg
from scipy import sparse
from scipy.integrate import quad
from scipy.optimize import minimize


class Stable:
    def __init__(self, F, μ, I_C, λ, f_0, f_1, f_2):
        F = np.asarray(F, dtype=np.float64)
        f_0 = np.asarray(f_0, dtype=np.float64)
        f_1 = np.asarray(f_1, dtype=np.float64)
        f_2 = np.asarray(f_2, dtype=np.float64)
        assert F.shape == (3, 3)
        assert np.ndim(μ) == 0
        assert np.ndim(I_C) == 0
        assert np.ndim(λ) == 0
        assert f_0.shape == (3,)
        assert f_1.shape == (3,)
        assert f_2.shape == (3,)
        # α = 1 + μ/λ - μ/(4λ)
        self.α = 1 + μ / λ - μ / (4 * λ)
        # J =`$f_0$`⋅(`$f_1$`×`$f_2$`)
        self.J = np.dot((f_0).ravel(), ((np.cross(f_1, f_2))).ravel())
        # `$\frac{\partial J}{\partial F}$` = [`$f_1$`×`$f_2$` `$f_2$`×`$f_0$` `$f_0$`×`$f_1$`]
        fracpartialJpartialF_0 = np.hstack(((np.cross(f_1, f_2)).reshape(3, 1), (np.cross(f_2, f_0)).reshape(3, 1), (np.cross(f_0, f_1)).reshape(3, 1)))
        self.fracpartialJpartialF = fracpartialJpartialF_0
        # `$P(F)$` = μ(1-1/(`$I_C$`+1))F + λ(J- α)`$\frac{\partial J}{\partial F}$`
        self.PF = μ * (1 - 1 / (I_C + 1)) * F + λ * (self.J - self.α) * self.fracpartialJpartialF

