import numpy as np
import scipy
import scipy.linalg
from scipy import sparse
from scipy.integrate import quad
from scipy.optimize import minimize


class ICP:
    def __init__(self, R, a, θ, p, q, n_q, n_p, t, barq, barp, trans, rot):
        R = np.asarray(R, dtype=np.float64)
        a = np.asarray(a, dtype=np.float64)
        p = np.asarray(p, dtype=np.float64)
        q = np.asarray(q, dtype=np.float64)
        n_q = np.asarray(n_q, dtype=np.float64)
        n_p = np.asarray(n_p, dtype=np.float64)
        t = np.asarray(t, dtype=np.float64)
        barq = np.asarray(barq, dtype=np.float64)
        barp = np.asarray(barp, dtype=np.float64)
        dim_0 = p.shape[0]
        assert R.shape == (3, 3)
        assert a.shape == (3,)
        assert np.ndim(θ) == 0
        assert p.shape == (dim_0, 3, )
        assert q.shape == (dim_0, 3, )
        assert n_q.shape == (dim_0, 3, )
        assert n_p.shape == (dim_0, 3, )
        assert t.shape == (3,)
        assert barq.shape == (3,)
        assert barp.shape == (3,)
        # ã = a tan(θ)
        self.ã = a * np.tan(θ)
        # n_i = `$n_q$`_i + `$n_p$`_i
        self.n = np.zeros((dim_0, 3, ))
        for i in range(1, dim_0+1):
            self.n[i-1] = n_q[i-1] + n_p[i-1]
        # t̃ = t/cos(θ)
        self.t̃ = t / np.cos(θ)
        # p̃_i = p_i - `$\bar{p}$`
        self.p̃ = np.zeros((dim_0, 3, ))
        for i in range(1, dim_0+1):
            self.p̃[i-1] = p[i-1] - barp
        # q̃_i = q_i - `$\bar{q}$`
        self.q̃ = np.zeros((dim_0, 3, ))
        for i in range(1, dim_0+1):
            self.q̃[i-1] = q[i-1] - barq
        # `$\varepsilon_{point}$` = ∑_i ||R p_i + t - q_i||
        sum_0 = 0
        for i in range(1, len(p)+1):
            sum_0 += np.linalg.norm(R @ p[i-1] + t - q[i-1], 2)
        self.varepsilon_point = sum_0
        # `$\varepsilon_{plane}$` = ∑_i ((R p_i + t - q_i) ⋅ `$n_q$`_i)^2
        sum_1 = 0
        for i in range(1, len(p)+1):
            sum_1 += np.power(float((np.dot(((R @ p[i-1] + t - q[i-1])).ravel(), (n_q[i-1]).ravel()))), 2)
        self.varepsilon_plane = sum_1
        # `$\varepsilon_{symm-RN}$` = ∑_i ((R p_i + R⁻¹ q_i + t) ⋅ (R`$n_p$`_i + R⁻¹`$n_q$`_i))^2
        sum_2 = 0
        for i in range(1, len(p)+1):
            sum_2 += np.power(float((np.dot(((R @ p[i-1] + np.linalg.solve(R, q[i-1]) + t)).ravel(), ((R @ n_p[i-1] + np.linalg.solve(R, n_q[i-1]))).ravel()))), 2)
        self.varepsilon_symmRN = sum_2
        # `$\varepsilon_{symm}$` = ∑_i cos²(θ)((p_i - q_i)⋅n_i +((p_i+q_i)×n_i)⋅ã+n_i⋅t̃)²
        sum_3 = 0
        for i in range(1, len(p)+1):
            sum_3 += np.power(float(np.cos(θ)), 2) * np.power(float((np.dot(((p[i-1] - q[i-1])).ravel(), (self.n[i-1]).ravel()) + np.dot(((np.cross((p[i-1] + q[i-1]), self.n[i-1]))).ravel(), (self.ã).ravel()) + np.dot((self.n[i-1]).ravel(), (self.t̃).ravel()))), 2)
        self.varepsilon_symm = sum_3
        # S = trans(`$\bar{q}$`) ⋅ rot(θ, ã/||ã||) ⋅trans(t̃ cos(θ)) ⋅rot(θ, ã/||ã||)⋅ trans(-`$\bar{p}$`)
        self.S = trans(barq) @ rot(θ, self.ã / np.linalg.norm(self.ã, 2)) @ trans(self.t̃ * np.cos(θ)) @ rot(θ, self.ã / np.linalg.norm(self.ã, 2)) @ trans(-barp)
        # `$\varepsilon_{two-plane}$` = ∑_i(((R p_i + R⁻¹ q_i + t) ⋅ (R `$n_p$`_i))^2 + ((R p_i + R⁻¹ q_i + t) ⋅ (R⁻¹`$n_q$`_i))^2)
        sum_4 = 0
        for i in range(1, len(p)+1):
            sum_4 += (np.power(float((np.dot(((R @ p[i-1] + np.linalg.solve(R, q[i-1]) + t)).ravel(), ((R @ n_p[i-1])).ravel()))), 2) + np.power(float((np.dot(((R @ p[i-1] + np.linalg.solve(R, q[i-1]) + t)).ravel(), ((np.linalg.solve(R, n_q[i-1]))).ravel()))), 2))
        self.varepsilon_twoplane = sum_4

