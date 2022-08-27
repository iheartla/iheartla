import numpy as np
import scipy
import scipy.linalg
from scipy import sparse
from scipy.integrate import quad
from scipy.optimize import minimize


class soft:
    def __init__(self, D, boldsymbolu, σ, α):
        boldsymbolu = np.asarray(boldsymbolu, dtype=np.float64)
        α = np.asarray(α, dtype=np.float64)
        dim_0 = α.shape[0]
        assert boldsymbolu.shape == (dim_0, 3, )
        assert np.ndim(σ) == 0
        assert α.shape == (dim_0,)
        # `$F_S$` = sum_i α_i D_i(`$\boldsymbol{u}$`_i) + σ((sum_i α_i)/(sum_i α_i^2) - 1)
        sum_0 = 0
        for i in range(1, len(α)+1):
            sum_0 += α[i-1] * D[i-1](boldsymbolu[i-1])
        sum_1 = 0
        for i in range(1, len(α)+1):
            sum_1 += α[i-1]
        sum_2 = 0
        for i in range(1, len(α)+1):
            sum_2 += np.power(float(α[i-1]), 2)
        self.F_S = sum_0 + σ * ((sum_1) / (sum_2) - 1)

