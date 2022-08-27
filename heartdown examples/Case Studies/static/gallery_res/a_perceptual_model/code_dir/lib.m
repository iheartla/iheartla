function output = perceptual(CSF, omega, m_tilde_t_b, beta_b, sigma_P_A, sigma_P_B, sigma_O_A, sigma_O_B)
% output = perceptual(CSF, ω, `$m̃_{t,b}$`, `$β_b$`, `$σ_P^A$`, `$σ_P^B$`, `$σ_O^A$`, `$σ_O^B$`)
%
%    m(ω;σ) = exp(-2π^2 ω^2 σ^2) where ω ∈ ℝ, σ∈ ℝ
%    
%    m̃(ω;σ) = CSF(ω) m(ω;σ) where ω ∈ ℝ, σ∈ ℝ
%    where
%    CSF ∈ ℝ->ℝ
%    
%    
%    `$E_b$`(σ) = sum_i ( (m̃(ω_i ; σ))/`$m̃_{t,b}$`)^`$β_b$`  where σ ∈ ℝ
%    where
%    ω_i ∈ ℝ
%    `$m̃_{t,b}$` ∈ ℝ
%    `$β_b$` ∈ ℝ
%    
%    `$∆Q_P$` = `$E_b$`(`$σ_P^A$`) - `$E_b$`(`$σ_P^B$`)
%    `$∆Q_O$` = `$E_b$`(`$σ_O^A$`) - `$E_b$`(`$σ_O^B$`)
%    where
%    `$σ_P^A$` ∈ ℝ
%    `$σ_P^B$` ∈ ℝ
%    `$σ_O^A$` ∈ ℝ
%    `$σ_O^B$` ∈ ℝ
%    
    if nargin==0
        warning('generating random input data');
        [CSF, omega, m_tilde_t_b, beta_b, sigma_P_A, sigma_P_B, sigma_O_A, sigma_O_B] = generateRandomData();
    end
    function [CSF, omega, m_tilde_t_b, beta_b, sigma_P_A, sigma_P_B, sigma_O_A, sigma_O_B] = generateRandomData()
        m_tilde_t_b = randn();
        beta_b = randn();
        sigma_P_A = randn();
        sigma_P_B = randn();
        sigma_O_A = randn();
        sigma_O_B = randn();
        dim_0 = randi(10);
        CSF = @CSFFunc;
        rseed = randi(2^32);
        function [ret] =  CSFFunc(p0)
            rng(rseed);
            ret = randn();
        end

        omega = randn(dim_0,1);
    end

    omega = reshape(omega,[],1);

    dim_0 = size(omega, 1);
    assert( size(omega,1) == dim_0 );
    assert(numel(m_tilde_t_b) == 1);
    assert(numel(beta_b) == 1);
    assert(numel(sigma_P_A) == 1);
    assert(numel(sigma_P_B) == 1);
    assert(numel(sigma_O_A) == 1);
    assert(numel(sigma_O_B) == 1);

    % `$∆Q_P$` = `$E_b$`(`$σ_P^A$`) - `$E_b$`(`$σ_P^B$`)
    increment_Q_P = E_b(sigma_P_A) - E_b(sigma_P_B);
    % `$∆Q_O$` = `$E_b$`(`$σ_O^A$`) - `$E_b$`(`$σ_O^B$`)
    increment_Q_O = E_b(sigma_O_A) - E_b(sigma_O_B);
    function [ret_1] = m(omega, sigma)
        assert(numel(omega) == 1);
        assert(numel(sigma) == 1);

        ret_1 = exp(-2 * pi.^2 * omega.^2 * sigma.^2);
    end

    function [ret_2] = m_tilde(omega, sigma)
        assert(numel(omega) == 1);
        assert(numel(sigma) == 1);

        ret_2 = CSF(omega) * m(omega, sigma);
    end

    function [ret_3] = E_b(sigma)
        assert(numel(sigma) == 1);

        sum_0 = 0;
        for i = 1:size(omega, 1)
            sum_0 = sum_0 + ((m_tilde(omega(i), sigma)) / m_tilde_t_b).^beta_b;
        end
        ret_3 = sum_0;
    end

    output.increment_Q_P = increment_Q_P;
    output.increment_Q_O = increment_Q_O;
    output.m = @m;
    output.m_tilde = @m_tilde;
    output.E_b = @E_b;
    output.omega = omega;    
    output.CSF = CSF;    
    output.m_tilde_t_b = m_tilde_t_b;    
    output.beta_b = beta_b;
end

