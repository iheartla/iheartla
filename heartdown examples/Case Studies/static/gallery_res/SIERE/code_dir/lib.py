import numpy as np
import scipy
import scipy.linalg
from scipy import sparse
from scipy.integrate import quad
from scipy.optimize import minimize


class siere:
    def __init__(self, U_s, M, v, f, K, boldsymbolI, h, φ_1, u):
        U_s = np.asarray(U_s, dtype=np.float64)
        M = np.asarray(M, dtype=np.float64)
        v = np.asarray(v, dtype=np.float64)
        f = np.asarray(f, dtype=np.float64)
        K = np.asarray(K, dtype=np.float64)
        boldsymbolI = np.asarray(boldsymbolI, dtype=np.float64)
        u = np.asarray(u, dtype=np.float64)
        n = U_s.shape[0]
        s = U_s.shape[1]
        assert U_s.shape == (n, s)
        assert M.shape == (n, n)
        assert v.shape == (n,)
        assert f.shape == (n,)
        assert K.shape == (n, n)
        assert boldsymbolI.shape == (2*n, 2*n)
        assert np.ndim(h) == 0
        assert u.shape == (2*n, 1)
        assert 2*n == int(2*n)
        assert 2*n == int(2*n)
        assert 2*n == int(2*n)
        # `$v_G$` = `$U_s$``$U_s$`^T Mv
        self.v_G = U_s @ U_s.T @ M @ v
        # `$v_H$` =  v - `$v_G$`
        self.v_H = v - self.v_G
        # `$f_G$` =  M`$U_s$``$U_s$`^T f
        self.f_G = M @ U_s @ U_s.T @ f
        # `$G(u)$` = [`$v_G$`
    #           M⁻¹`$f_G$`]
        Gu_0 = np.vstack(((self.v_G).reshape(n, 1), (np.linalg.solve(M, self.f_G)).reshape(n, 1)))
        self.Gu = Gu_0
        # `$f_H$` =  f - `$f_G$`
        self.f_H = f - self.f_G
        # `$H(u)$` = [`$v_H$`
    #           M⁻¹`$f_H$`]
        Hu_0 = np.vstack(((self.v_H).reshape(n, 1), (np.linalg.solve(M, self.f_H)).reshape(n, 1)))
        self.Hu = Hu_0
        # `$J_G$` = [0    `$U_s$``$U_s$`^TM
    #       -`$U_s$``$U_s$`^TK`$U_s$``$U_s$`^TM 0 ]
        J_G_0 = np.block([[np.zeros((n, n)), U_s @ U_s.T @ M], [-U_s @ U_s.T @ K @ U_s @ U_s.T @ M, np.zeros((n, n))]])
        self.J_G = J_G_0
        # `$J_H$` =  [0     I_n
    #             -M⁻¹K 0] - `$J_G$`
        J_H_0 = np.block([[np.zeros((n, n)), np.identity(n)], [-np.linalg.solve(M, K), np.zeros((n, n))]])
        self.J_H = J_H_0 - self.J_G
        # `$J_G^r$` = [0     I_s
    #             -`$U_s$`^TK`$U_s$` 0]
        J_G_circumflex_accent_r_0 = np.block([[np.zeros((s, s)), np.identity(s)], [-U_s.T @ K @ U_s, np.zeros((s, s))]])
        self.J_G_circumflex_accent_r = J_G_circumflex_accent_r_0
        # `$G^r(u)$` = [`$U_s$`^TMv
    #             `$U_s$`^Tf]
        G_circumflex_accent_ru_0 = np.vstack(((U_s.T @ M @ v).reshape(s, 1), (U_s.T @ f).reshape(s, 1)))
        self.G_circumflex_accent_ru = G_circumflex_accent_ru_0
        # `$u_+$` =  u + (`$\boldsymbol{I}$` -h`$J_H$`)⁻¹(h `$H(u)$` + h[`$U_s$` 0
    #                                                0   `$U_s$`] `$φ_1$`(h`$J_G^r$`) `$G^r(u)$`)
        u_plus_sign_2 = np.block([[U_s, np.zeros((n, s))], [np.zeros((n, s)), U_s]])
        self.u_plus_sign = u + np.linalg.solve((boldsymbolI - h * self.J_H), (h * self.Hu + h * u_plus_sign_2 @ φ_1(h * self.J_G_circumflex_accent_r) @ self.G_circumflex_accent_ru))

class second:
    def __init__(self, U_s, M, K):
        U_s = np.asarray(U_s, dtype=np.float64)
        M = np.asarray(M, dtype=np.float64)
        K = np.asarray(K, dtype=np.float64)
        n = U_s.shape[0]
        s = U_s.shape[1]
        assert U_s.shape == (n, s)
        assert M.shape == (n, n)
        assert K.shape == (n, n)
        # `$Y_1$` =  [`$U_s$`
    #              0]
        Y_1_0 = np.vstack((U_s, np.zeros((1, s))))
        self.Y_1 = Y_1_0
        # `$Z_1$` =  [ 0
    #              M`$U_s$`]
        Z_1_0 = np.vstack((np.zeros((1, s)), M @ U_s))
        self.Z_1 = Z_1_0
        # `$Y_2$` =  [0
    #             -`$U_s$``$U_s$`^TK`$U_s$`]
        Y_2_0 = np.vstack((np.zeros((1, s)), -U_s @ U_s.T @ K @ U_s))
        self.Y_2 = Y_2_0
        # `$Z_2$` =  [ M`$U_s$`
    #              0]
        Z_2_0 = np.vstack((M @ U_s, np.zeros((1, s))))
        self.Z_2 = Z_2_0
        # `$J_G$` = `$Y_1$``$Z_1$`^T + `$Y_2$``$Z_2$`^T
        self.J_G = self.Y_1 @ self.Z_1.T + self.Y_2 @ self.Z_2.T

