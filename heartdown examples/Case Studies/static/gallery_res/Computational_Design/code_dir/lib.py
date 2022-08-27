import numpy as np
import scipy
import scipy.linalg
from scipy import sparse
from scipy.integrate import quad
from scipy.optimize import minimize


class computation:
    def __init__(self, λ_s, E_a, D, S_1, S_2, U_1, U_2, R):
        R = np.asarray(R, dtype=np.float64)
        dim_0 = R.shape[0]
        assert np.ndim(λ_s) == 0
        assert np.ndim(E_a) == 0
        assert np.ndim(S_1) == 0
        assert np.ndim(S_2) == 0
        assert np.ndim(U_1) == 0
        assert np.ndim(U_2) == 0
        assert R.shape == (dim_0, 3, )
        # `$E_c$` = D(`$S_1$`, `$U_1$`) + D(`$S_2$`, `$U_2$`)
        self.E_c = D(S_1, U_1) + D(S_2, U_2)
        # `$E_s$` = `$E_c$` + `$E_a$`
        self.E_s = self.E_c + E_a
        # `$E_f$` = sum_i ||R_i||
        sum_0 = 0
        for i in range(1, len(R)+1):
            sum_0 += np.linalg.norm(R[i-1], 2)
        self.E_f = sum_0
        # E = `$λ_s$``$E_s$` + (1 - `$λ_s$`)`$E_f$`
        self.E = λ_s * self.E_s + (1 - λ_s) * self.E_f

