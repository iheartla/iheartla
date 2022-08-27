import numpy as np
import scipy
import scipy.linalg
from scipy import sparse
from scipy.integrate import quad
from scipy.optimize import minimize


class Generic:
    def __init__(self, J, x, y, u, v):
        J = np.asarray(J, dtype=np.float64)
        assert J.shape == (2, 2)
        assert np.ndim(x) == 0
        assert np.ndim(y) == 0
        assert np.ndim(u) == 0
        assert np.ndim(v) == 0
        # `$x_p$` = (-y, x)
        self.x_p = np.hstack((-y, x))
        # `$v_p$` = (-v, u)
        self.v_p = np.hstack((-v, u))
        # M=[-J`$x_p$`+`$v_p$`  J  `$x_p$`  I_2]
        M_0 = np.hstack(((-J @ self.x_p + self.v_p).reshape(2, 1), J, (self.x_p).reshape(2, 1), np.identity(2)))
        self.M = M_0

