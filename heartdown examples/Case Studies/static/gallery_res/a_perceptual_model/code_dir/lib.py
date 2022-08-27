import numpy as np
import scipy
import scipy.linalg
from scipy import sparse
from scipy.integrate import quad
from scipy.optimize import minimize


class perceptual:
    def __init__(self, CSF, ω, m_combining_tilde_t_comma_b, β_b, σ_P_circumflex_accent_A, σ_P_circumflex_accent_B, σ_O_circumflex_accent_A, σ_O_circumflex_accent_B):
        ω = np.asarray(ω, dtype=np.float64)
        dim_0 = ω.shape[0]
        assert ω.shape == (dim_0,)
        assert np.ndim(m_combining_tilde_t_comma_b) == 0
        assert np.ndim(β_b) == 0
        assert np.ndim(σ_P_circumflex_accent_A) == 0
        assert np.ndim(σ_P_circumflex_accent_B) == 0
        assert np.ndim(σ_O_circumflex_accent_A) == 0
        assert np.ndim(σ_O_circumflex_accent_B) == 0

        self.ω = ω
        self.CSF = CSF
        self.m_combining_tilde_t_comma_b = m_combining_tilde_t_comma_b
        self.β_b = β_b
        # `$∆Q_P$` = `$E_b$`(`$σ_P^A$`) - `$E_b$`(`$σ_P^B$`)
        self.increment_Q_P = self.E_b(σ_P_circumflex_accent_A) - self.E_b(σ_P_circumflex_accent_B)
        # `$∆Q_O$` = `$E_b$`(`$σ_O^A$`) - `$E_b$`(`$σ_O^B$`)
        self.increment_Q_O = self.E_b(σ_O_circumflex_accent_A) - self.E_b(σ_O_circumflex_accent_B)

    def m(self, ω, σ):
        assert np.ndim(ω) == 0
        assert np.ndim(σ) == 0

        return np.exp(-2 * np.power(float(np.pi), 2) * np.power(float(ω), 2) * np.power(float(σ), 2))

    def m̃(self, ω, σ):
        assert np.ndim(ω) == 0
        assert np.ndim(σ) == 0

        return self.CSF(ω) * self.m(ω, σ)

    def E_b(self, σ):
        assert np.ndim(σ) == 0

        sum_0 = 0
        for i in range(1, len(self.ω)+1):
            sum_0 += np.power(float(((self.m̃(ω[i-1], σ)) / self.m_combining_tilde_t_comma_b)), self.β_b)
        return sum_0

