import numpy as np
import scipy
import scipy.linalg
from scipy import sparse
from scipy.integrate import quad
from scipy.optimize import minimize


class elastic:
    def __init__(self, E_r, q_g, q_h, m_g, m_h, angle, λ_q_comma_1, λ_q_comma_2, t, λ_a_comma_1, λ_a_comma_2, q, q_a, m, m_a, δ_circumflex_accent_minus_sign, δ_circumflex_accent_plus_sign, β_q, β_circumflex_accent_minus_sign, β_circumflex_accent_plus_sign, μ, ε):
        q_g = np.asarray(q_g, dtype=np.float64)
        q_h = np.asarray(q_h, dtype=np.float64)
        m_g = np.asarray(m_g, dtype=np.float64)
        m_h = np.asarray(m_h, dtype=np.float64)
        q = np.asarray(q, dtype=np.float64)
        q_a = np.asarray(q_a, dtype=np.float64)
        m = np.asarray(m, dtype=np.float64)
        m_a = np.asarray(m_a, dtype=np.float64)
        n = q_g.shape[0]
        assert np.ndim(E_r) == 0
        assert q_g.shape == (n,)
        assert q_h.shape == (n,)
        assert m_g.shape == (n,)
        assert m_h.shape == (n,)
        assert np.ndim(λ_q_comma_1) == 0
        assert np.ndim(λ_q_comma_2) == 0
        assert np.ndim(t) == 0
        assert np.ndim(λ_a_comma_1) == 0
        assert np.ndim(λ_a_comma_2) == 0
        assert q.shape == (n,)
        assert q_a.shape == (n,)
        assert m.shape == (n,)
        assert m_a.shape == (n,)
        assert np.ndim(δ_circumflex_accent_minus_sign) == 0
        assert np.ndim(δ_circumflex_accent_plus_sign) == 0
        assert np.ndim(β_q) == 0
        assert np.ndim(β_circumflex_accent_minus_sign) == 0
        assert np.ndim(β_circumflex_accent_plus_sign) == 0
        assert np.ndim(μ) == 0
        assert np.ndim(ε) == 0
        _connection = self.connection(q_g, q_h, m_g, m_h, angle, λ_q_comma_1, λ_q_comma_2, t)
        _anchor = self.anchor(λ_a_comma_1, λ_a_comma_2, q, q_a, m, m_a, angle)
        _notchlimit = self.notchlimit(δ_circumflex_accent_minus_sign, δ_circumflex_accent_plus_sign, β_q, β_circumflex_accent_minus_sign, β_circumflex_accent_plus_sign)
        _penalty = self.penalty(μ, ε, β_q)
        self.E_q = _connection.E_q
        self.E_a = _anchor.E_a
        self.E_n = _notchlimit.E_n
        self.E_p = _penalty.E_p
        # E = `E_r` + `E_q` + `E_a` + `E_n` + `E_p`
        self.E = E_r + self.E_q + self.E_a + self.E_n + self.E_p

    class connection:
        def __init__(self, q_g, q_h, m_g, m_h, angle, λ_q_comma_1, λ_q_comma_2, t):
            q_g = np.asarray(q_g, dtype=np.float64)
            q_h = np.asarray(q_h, dtype=np.float64)
            m_g = np.asarray(m_g, dtype=np.float64)
            m_h = np.asarray(m_h, dtype=np.float64)
            n = q_g.shape[0]
            assert q_g.shape == (n,)
            assert q_h.shape == (n,)
            assert m_g.shape == (n,)
            assert m_h.shape == (n,)
            assert np.ndim(λ_q_comma_1) == 0
            assert np.ndim(λ_q_comma_2) == 0
            assert np.ndim(t) == 0
            # E_q = λ_q_comma_1||q_g-q_h+tm_g||^2 + λ_q_comma_1||q_h-q_g+tm_h||^2 + λ_q_comma_2||angle(m_g,m_h)||^2
            self.E_q = λ_q_comma_1 * np.power(float(np.linalg.norm(q_g - q_h + t * m_g, 2)), 2) + λ_q_comma_1 * np.power(float(np.linalg.norm(q_h - q_g + t * m_h, 2)), 2) + λ_q_comma_2 * np.power(float(np.linalg.norm(angle(m_g, m_h), 2)), 2)
    class anchor:
        def __init__(self, λ_a_comma_1, λ_a_comma_2, q, q_a, m, m_a, angle):
            q = np.asarray(q, dtype=np.float64)
            q_a = np.asarray(q_a, dtype=np.float64)
            m = np.asarray(m, dtype=np.float64)
            m_a = np.asarray(m_a, dtype=np.float64)
            n = q.shape[0]
            assert np.ndim(λ_a_comma_1) == 0
            assert np.ndim(λ_a_comma_2) == 0
            assert q.shape == (n,)
            assert q_a.shape == (n,)
            assert m.shape == (n,)
            assert m_a.shape == (n,)
            # E_a = λ_a_comma_1||q-q_a||^2 + λ_a_comma_2||angle(m,m_a)||^2
            self.E_a = λ_a_comma_1 * np.power(float(np.linalg.norm(q - q_a, 2)), 2) + λ_a_comma_2 * np.power(float(np.linalg.norm(angle(m, m_a), 2)), 2)
    class notchlimit:
        def __init__(self, δ_circumflex_accent_minus_sign, δ_circumflex_accent_plus_sign, β_q, β_circumflex_accent_minus_sign, β_circumflex_accent_plus_sign):
            assert np.ndim(δ_circumflex_accent_minus_sign) == 0
            assert np.ndim(δ_circumflex_accent_plus_sign) == 0
            assert np.ndim(β_q) == 0
            assert np.ndim(β_circumflex_accent_minus_sign) == 0
            assert np.ndim(β_circumflex_accent_plus_sign) == 0
            # E_n = δ_circumflex_accent_minus_sign(1/10 log((β_q-β_circumflex_accent_minus_sign)))^2 + δ_circumflex_accent_plus_sign(1/10 log((β_circumflex_accent_plus_sign-β_q)))^2
            self.E_n = δ_circumflex_accent_minus_sign * np.power(float((1 / 10 * np.log((β_q - β_circumflex_accent_minus_sign)))), 2) + δ_circumflex_accent_plus_sign * np.power(float((1 / 10 * np.log((β_circumflex_accent_plus_sign - β_q)))), 2)
    class penalty:
        def __init__(self, μ, ε, β_q):
            assert np.ndim(μ) == 0
            assert np.ndim(ε) == 0
            assert np.ndim(β_q) == 0
            # E_p = (μ log((ε + β_q)))^2 + (μ log((ε + 1 - β_q)))^2
            self.E_p = np.power(float((μ * np.log((ε + β_q)))), 2) + np.power(float((μ * np.log((ε + 1 - β_q)))), 2)

class connection:
    def __init__(self, q_g, q_h, m_g, m_h, angle, λ_q_comma_1, λ_q_comma_2, t):
        q_g = np.asarray(q_g, dtype=np.float64)
        q_h = np.asarray(q_h, dtype=np.float64)
        m_g = np.asarray(m_g, dtype=np.float64)
        m_h = np.asarray(m_h, dtype=np.float64)
        n = q_g.shape[0]
        assert q_g.shape == (n,)
        assert q_h.shape == (n,)
        assert m_g.shape == (n,)
        assert m_h.shape == (n,)
        assert np.ndim(λ_q_comma_1) == 0
        assert np.ndim(λ_q_comma_2) == 0
        assert np.ndim(t) == 0
        # `E_q` = `$λ_{q,1}$`||`$q_g$`-`$q_h$`+t`$m_g$`||^2 + `$λ_{q,1}$`||`$q_h$`-`$q_g$`+t`$m_h$`||^2 + `$λ_{q,2}$`||`$\angle$`(`$m_g$`,`$m_h$`)||^2
        self.E_q = λ_q_comma_1 * np.power(float(np.linalg.norm(q_g - q_h + t * m_g, 2)), 2) + λ_q_comma_1 * np.power(float(np.linalg.norm(q_h - q_g + t * m_h, 2)), 2) + λ_q_comma_2 * np.power(float(np.linalg.norm(angle(m_g, m_h), 2)), 2)

class anchor:
    def __init__(self, λ_a_comma_1, λ_a_comma_2, q, q_a, m, m_a, angle):
        q = np.asarray(q, dtype=np.float64)
        q_a = np.asarray(q_a, dtype=np.float64)
        m = np.asarray(m, dtype=np.float64)
        m_a = np.asarray(m_a, dtype=np.float64)
        n = q.shape[0]
        assert np.ndim(λ_a_comma_1) == 0
        assert np.ndim(λ_a_comma_2) == 0
        assert q.shape == (n,)
        assert q_a.shape == (n,)
        assert m.shape == (n,)
        assert m_a.shape == (n,)
        # `E_a` = `$λ_{a,1}$`||q-`$q_a$`||^2 + `$λ_{a,2}$`||`$\angle$`(m,`$m_a$`)||^2
        self.E_a = λ_a_comma_1 * np.power(float(np.linalg.norm(q - q_a, 2)), 2) + λ_a_comma_2 * np.power(float(np.linalg.norm(angle(m, m_a), 2)), 2)

class notchlimit:
    def __init__(self, δ_circumflex_accent_minus_sign, δ_circumflex_accent_plus_sign, β_q, β_circumflex_accent_minus_sign, β_circumflex_accent_plus_sign):
        assert np.ndim(δ_circumflex_accent_minus_sign) == 0
        assert np.ndim(δ_circumflex_accent_plus_sign) == 0
        assert np.ndim(β_q) == 0
        assert np.ndim(β_circumflex_accent_minus_sign) == 0
        assert np.ndim(β_circumflex_accent_plus_sign) == 0
        # `E_n` = `$δ^{(−)}$`(1/10 log((`$β_q$`-`$β^{(−)}$`)))^2 + `$δ^{(+)}$`(1/10 log((`$β^{(+)}$`-`$β_q$`)))^2
        self.E_n = δ_circumflex_accent_minus_sign * np.power(float((1 / 10 * np.log((β_q - β_circumflex_accent_minus_sign)))), 2) + δ_circumflex_accent_plus_sign * np.power(float((1 / 10 * np.log((β_circumflex_accent_plus_sign - β_q)))), 2)

class penalty:
    def __init__(self, μ, ε, β_q):
        assert np.ndim(μ) == 0
        assert np.ndim(ε) == 0
        assert np.ndim(β_q) == 0
        # `E_p` = (μ log((ε + `$β_q$`)))^2 + (μ log((ε + 1 - `$β_q$`)))^2
        self.E_p = np.power(float((μ * np.log((ε + β_q)))), 2) + np.power(float((μ * np.log((ε + 1 - β_q)))), 2)

