function output = elastic(E_r, q_g, q_h, m_g, m_h, angle, lambda_q_1, lambda_q_2, t, lambda_a_1, lambda_a_2, q, q_a, m, m_a, delta_minus_sign, delta_plus_sign, beta_q, beta_minus_sign, beta_plus_sign, mu, epsilon)
% output = elastic(`E_r`, `$q_g$`, `$q_h$`, `$m_g$`, `$m_h$`, `$\angle$`, `$λ_{q,1}$`, `$λ_{q,2}$`, t, `$λ_{a,1}$`, `$λ_{a,2}$`, q, `$q_a$`, m, `$m_a$`, `$δ^{(−)}$`, `$δ^{(+)}$`, `$β_q$`, `$β^{(−)}$`, `$β^{(+)}$`, μ, ε)
%
%    `E_q` from connection(`$q_g$`,`$q_h$`,`$m_g$`,`$m_h$`,`$\angle$`,`$λ_{q,1}$`,`$λ_{q,2}$`,t)
%    `E_a` from anchor(`$λ_{a,1}$`,`$λ_{a,2}$`,q,`$q_a$`,m,`$m_a$`, `$\angle$`)
%    `E_n` from notchlimit(`$δ^{(−)}$`,`$δ^{(+)}$`,`$β_q$`,`$β^{(−)}$`,`$β^{(+)}$`)
%    `E_p` from penalty(μ, ε, `$β_q$`)
%    E = `E_r` + `E_q` + `E_a` + `E_n` + `E_p`
%    where
%    `E_r` ∈ ℝ:the internal energy of the rods
%    where
%    `$q_g$` ∈ ℝ^n: point
%    `$q_h$` ∈ ℝ^n: point
%    `$m_g$` ∈ ℝ^n : the material vectors of $g$
%    `$m_h$` ∈ ℝ^n : the material vectors at $h$
%    `$\angle$` ∈ ℝ^n, ℝ^n -> ℝ^n
%    `$λ_{q,1}$` ∈ ℝ: the constraint weights for the position
%    `$λ_{q,2}$` ∈ ℝ: the constraint weights for the direction
%    t ∈ ℝ : offset
%    where
%    `$λ_{a,1}$` ∈ ℝ: weight
%    `$λ_{a,2}$` ∈ ℝ: weight
%    q ∈ ℝ^n 
%    `$q_a$` ∈ ℝ^n 
%    m ∈ ℝ^n 
%    `$m_a$` ∈ ℝ^n 
%    where
%    `$δ^{(−)}$` ∈ ℝ
%    `$δ^{(+)}$` ∈ ℝ
%    `$β_q$` ∈ ℝ :  barycentric coordinates 
%    `$β^{(−)}$` ∈ ℝ : the barycentric coordinates of the notch bounds on their corresponding edges
%    `$β^{(+)}$` ∈ ℝ : the barycentric coordinates of the notch bounds on their corresponding edges
%    where
%    μ ∈ ℝ: a weighting parameter
%    ε ∈ ℝ: denoting how far $q$ is allowed to move past the end of the edge
%    
    if nargin==0
        warning('generating random input data');
        [E_r, q_g, q_h, m_g, m_h, angle, lambda_q_1, lambda_q_2, t, lambda_a_1, lambda_a_2, q, q_a, m, m_a, delta_minus_sign, delta_plus_sign, beta_q, beta_minus_sign, beta_plus_sign, mu, epsilon] = generateRandomData();
    end
    function [E_r, q_g, q_h, m_g, m_h, angle, lambda_q_1, lambda_q_2, t, lambda_a_1, lambda_a_2, q, q_a, m, m_a, delta_minus_sign, delta_plus_sign, beta_q, beta_minus_sign, beta_plus_sign, mu, epsilon] = generateRandomData()
        E_r = randn();
        lambda_q_1 = randn();
        lambda_q_2 = randn();
        t = randn();
        lambda_a_1 = randn();
        lambda_a_2 = randn();
        delta_minus_sign = randn();
        delta_plus_sign = randn();
        beta_q = randn();
        beta_minus_sign = randn();
        beta_plus_sign = randn();
        mu = randn();
        epsilon = randn();
        n = randi(10);
        q_g = randn(n,1);
        q_h = randn(n,1);
        m_g = randn(n,1);
        m_h = randn(n,1);
        angle = @angleFunc;
        rseed = randi(2^32);
        function [ret] =  angleFunc(p0, p1)
            rng(rseed);
            ret = randn(n,1);
        end

        q = randn(n,1);
        q_a = randn(n,1);
        m = randn(n,1);
        m_a = randn(n,1);
    end

    q_g = reshape(q_g,[],1);
    q_h = reshape(q_h,[],1);
    m_g = reshape(m_g,[],1);
    m_h = reshape(m_h,[],1);
    q = reshape(q,[],1);
    q_a = reshape(q_a,[],1);
    m = reshape(m,[],1);
    m_a = reshape(m_a,[],1);

    n = size(q_g, 1);
    assert(numel(E_r) == 1);
    assert( numel(q_g) == n );
    assert( numel(q_h) == n );
    assert( numel(m_g) == n );
    assert( numel(m_h) == n );
    assert(numel(lambda_q_1) == 1);
    assert(numel(lambda_q_2) == 1);
    assert(numel(t) == 1);
    assert(numel(lambda_a_1) == 1);
    assert(numel(lambda_a_2) == 1);
    assert( numel(q) == n );
    assert( numel(q_a) == n );
    assert( numel(m) == n );
    assert( numel(m_a) == n );
    assert(numel(delta_minus_sign) == 1);
    assert(numel(delta_plus_sign) == 1);
    assert(numel(beta_q) == 1);
    assert(numel(beta_minus_sign) == 1);
    assert(numel(beta_plus_sign) == 1);
    assert(numel(mu) == 1);
    assert(numel(epsilon) == 1);

    function output = connection(q_g, q_h, m_g, m_h, angle, lambda_q_1, lambda_q_2, t)
    % output = connection(q_g, q_h, m_g, m_h, angle, lambda_q_1, lambda_q_2, t)
    %
    %    E_q = lambda_q_1||q_g-q_h+tm_g||^2 + lambda_q_1||q_h-q_g+tm_h||^2 + lambda_q_2||angle(m_g,m_h)||^2 
    %    where
    %    q_g ∈ ℝ^n : point
    %    q_h ∈ ℝ^n : point
    %    m_g ∈ ℝ^n : the material vectors of $g$
    %    m_h ∈ ℝ^n : the material vectors at $h$
    %    angle ∈ ℝ^n, ℝ^n -> ℝ^n
    %    lambda_q_1 ∈ ℝ : the constraint weights for the position
    %    lambda_q_2 ∈ ℝ : the constraint weights for the direction
    %    t ∈ ℝ
    %    
        if nargin==0
            warning('generating random input data');
            [q_g, q_h, m_g, m_h, angle, lambda_q_1, lambda_q_2, t] = generateRandomData();
        end
        function [q_g, q_h, m_g, m_h, angle, lambda_q_1, lambda_q_2, t] = generateRandomData()
            lambda_q_1 = randn();
            lambda_q_2 = randn();
            t = randn();
            n = randi(10);
            q_g = randn(n,1);
            q_h = randn(n,1);
            m_g = randn(n,1);
            m_h = randn(n,1);
            angle = @angleFunc;
            rseed = randi(2^32);
            function [ret] =  angleFunc(p0, p1)
                rng(rseed);
                ret = randn(n,1);
            end
        end
        q_g = reshape(q_g,[],1);
        q_h = reshape(q_h,[],1);
        m_g = reshape(m_g,[],1);
        m_h = reshape(m_h,[],1);
        n = size(q_g, 1);
        assert( numel(q_g) == n );
        assert( numel(q_h) == n );
        assert( numel(m_g) == n );
        assert( numel(m_h) == n );
        assert(numel(lambda_q_1) == 1);
        assert(numel(lambda_q_2) == 1);
        assert(numel(t) == 1);
        % E_q = lambda_q_1||q_g-q_h+tm_g||^2 + lambda_q_1||q_h-q_g+tm_h||^2 + lambda_q_2||angle(m_g,m_h)||^2
        E_q = lambda_q_1 * norm(q_g - q_h + t * m_g, 2).^2 + lambda_q_1 * norm(q_h - q_g + t * m_h, 2).^2 + lambda_q_2 * norm(angle(m_g, m_h), 2).^2;
        output.E_q = E_q;
    end
    function output = anchor(lambda_a_1, lambda_a_2, q, q_a, m, m_a, angle)
    % output = anchor(lambda_a_1, lambda_a_2, q, q_a, m, m_a, angle)
    %
    %    E_a = lambda_a_1||q-q_a||^2 + lambda_a_2||angle(m,m_a)||^2 
    %    where
    %    lambda_a_1 ∈ ℝ : weight
    %    lambda_a_2 ∈ ℝ : weight
    %    q ∈ ℝ^n 
    %    q_a ∈ ℝ^n 
    %    m ∈ ℝ^n 
    %    m_a ∈ ℝ^n 
    %    angle ∈ ℝ^n, ℝ^n -> ℝ^n
    %    
        if nargin==0
            warning('generating random input data');
            [lambda_a_1, lambda_a_2, q, q_a, m, m_a, angle] = generateRandomData();
        end
        function [lambda_a_1, lambda_a_2, q, q_a, m, m_a, angle] = generateRandomData()
            lambda_a_1 = randn();
            lambda_a_2 = randn();
            n = randi(10);
            q = randn(n,1);
            q_a = randn(n,1);
            m = randn(n,1);
            m_a = randn(n,1);
            angle = @angleFunc;
            rseed = randi(2^32);
            function [ret] =  angleFunc(p0, p1)
                rng(rseed);
                ret = randn(n,1);
            end
        end
        q = reshape(q,[],1);
        q_a = reshape(q_a,[],1);
        m = reshape(m,[],1);
        m_a = reshape(m_a,[],1);
        n = size(q, 1);
        assert(numel(lambda_a_1) == 1);
        assert(numel(lambda_a_2) == 1);
        assert( numel(q) == n );
        assert( numel(q_a) == n );
        assert( numel(m) == n );
        assert( numel(m_a) == n );
        % E_a = lambda_a_1||q-q_a||^2 + lambda_a_2||angle(m,m_a)||^2
        E_a = lambda_a_1 * norm(q - q_a, 2).^2 + lambda_a_2 * norm(angle(m, m_a), 2).^2;
        output.E_a = E_a;
    end
    function output = notchlimit(delta_minus_sign, delta_plus_sign, beta_q, beta_minus_sign, beta_plus_sign)
    % output = notchlimit(delta_minus_sign, delta_plus_sign, beta_q, beta_minus_sign, beta_plus_sign)
    %
    %    E_n = delta_minus_sign(1/10 log((beta_q-beta_minus_sign)))^2 + delta_plus_sign(1/10 log((beta_plus_sign-beta_q)))^2
    %    where
    %    delta_minus_sign ∈ ℝ 
    %    delta_plus_sign ∈ ℝ
    %    beta_q ∈ ℝ :  barycentric coordinates 
    %    beta_minus_sign ∈ ℝ : the barycentric coordinates of the notch bounds on their corresponding edges
    %    beta_plus_sign ∈ ℝ : the barycentric coordinates of the notch bounds on their corresponding edges
    %    
        if nargin==0
            warning('generating random input data');
            [delta_minus_sign, delta_plus_sign, beta_q, beta_minus_sign, beta_plus_sign] = generateRandomData();
        end
        function [delta_minus_sign, delta_plus_sign, beta_q, beta_minus_sign, beta_plus_sign] = generateRandomData()
            delta_minus_sign = randn();
            delta_plus_sign = randn();
            beta_q = randn();
            beta_minus_sign = randn();
            beta_plus_sign = randn();
        end
        assert(numel(delta_minus_sign) == 1);
        assert(numel(delta_plus_sign) == 1);
        assert(numel(beta_q) == 1);
        assert(numel(beta_minus_sign) == 1);
        assert(numel(beta_plus_sign) == 1);
        % E_n = delta_minus_sign(1/10 log((beta_q-beta_minus_sign)))^2 + delta_plus_sign(1/10 log((beta_plus_sign-beta_q)))^2
        E_n = delta_minus_sign * (1 / 10 * log((beta_q - beta_minus_sign))).^2 + delta_plus_sign * (1 / 10 * log((beta_plus_sign - beta_q))).^2;
        output.E_n = E_n;
    end
    function output = penalty(mu, epsilon, beta_q)
    % output = penalty(mu, epsilon, beta_q)
    %
    %    E_p = (mu log((epsilon + beta_q)))^2 + (mu log((epsilon + 1 - beta_q)))^2
    %    where
    %    mu ∈ ℝ : a weighting parameter
    %    epsilon ∈ ℝ : denoting how far $q$ is allowed to move past the end of the edge
    %    beta_q ∈ ℝ :  barycentric coordinates 
    %    
        if nargin==0
            warning('generating random input data');
            [mu, epsilon, beta_q] = generateRandomData();
        end
        function [mu, epsilon, beta_q] = generateRandomData()
            mu = randn();
            epsilon = randn();
            beta_q = randn();
        end
        assert(numel(mu) == 1);
        assert(numel(epsilon) == 1);
        assert(numel(beta_q) == 1);
        % E_p = (mu log((epsilon + beta_q)))^2 + (mu log((epsilon + 1 - beta_q)))^2
        E_p = (mu * log((epsilon + beta_q))).^2 + (mu * log((epsilon + 1 - beta_q))).^2;
        output.E_p = E_p;
    end
    connection_ = connection(q_g, q_h, m_g, m_h, angle, lambda_q_1, lambda_q_2, t);
    anchor_ = anchor(lambda_a_1, lambda_a_2, q, q_a, m, m_a, angle);
    notchlimit_ = notchlimit(delta_minus_sign, delta_plus_sign, beta_q, beta_minus_sign, beta_plus_sign);
    penalty_ = penalty(mu, epsilon, beta_q);
    E_q = connection_.E_q;
    E_a = anchor_.E_a;
    E_n = notchlimit_.E_n;
    E_p = penalty_.E_p;
    % E = `E_r` + `E_q` + `E_a` + `E_n` + `E_p`
    E = E_r + E_q + E_a + E_n + E_p;
    output.E = E;
end

function output = connection(q_g, q_h, m_g, m_h, angle, lambda_q_1, lambda_q_2, t)
% output = connection(`$q_g$`, `$q_h$`, `$m_g$`, `$m_h$`, `$\angle$`, `$λ_{q,1}$`, `$λ_{q,2}$`, t)
%
%    `E_q` = `$λ_{q,1}$`||`$q_g$`-`$q_h$`+t`$m_g$`||^2 + `$λ_{q,1}$`||`$q_h$`-`$q_g$`+t`$m_h$`||^2 + `$λ_{q,2}$`||`$\angle$`(`$m_g$`,`$m_h$`)||^2 
%    where
%    `$q_g$` ∈ ℝ^n : point
%    `$q_h$` ∈ ℝ^n : point
%    `$m_g$` ∈ ℝ^n : the material vectors of $g$
%    `$m_h$` ∈ ℝ^n : the material vectors at $h$
%    `$\angle$` ∈ ℝ^n, ℝ^n -> ℝ^n
%    `$λ_{q,1}$` ∈ ℝ : the constraint weights for the position
%    `$λ_{q,2}$` ∈ ℝ : the constraint weights for the direction
%    t ∈ ℝ
%    
    if nargin==0
        warning('generating random input data');
        [q_g, q_h, m_g, m_h, angle, lambda_q_1, lambda_q_2, t] = generateRandomData();
    end
    function [q_g, q_h, m_g, m_h, angle, lambda_q_1, lambda_q_2, t] = generateRandomData()
        lambda_q_1 = randn();
        lambda_q_2 = randn();
        t = randn();
        n = randi(10);
        q_g = randn(n,1);
        q_h = randn(n,1);
        m_g = randn(n,1);
        m_h = randn(n,1);
        angle = @angleFunc;
        rseed = randi(2^32);
        function [ret] =  angleFunc(p0, p1)
            rng(rseed);
            ret = randn(n,1);
        end

    end

    q_g = reshape(q_g,[],1);
    q_h = reshape(q_h,[],1);
    m_g = reshape(m_g,[],1);
    m_h = reshape(m_h,[],1);

    n = size(q_g, 1);
    assert( numel(q_g) == n );
    assert( numel(q_h) == n );
    assert( numel(m_g) == n );
    assert( numel(m_h) == n );
    assert(numel(lambda_q_1) == 1);
    assert(numel(lambda_q_2) == 1);
    assert(numel(t) == 1);

    % `E_q` = `$λ_{q,1}$`||`$q_g$`-`$q_h$`+t`$m_g$`||^2 + `$λ_{q,1}$`||`$q_h$`-`$q_g$`+t`$m_h$`||^2 + `$λ_{q,2}$`||`$\angle$`(`$m_g$`,`$m_h$`)||^2
    E_q = lambda_q_1 * norm(q_g - q_h + t * m_g, 2).^2 + lambda_q_1 * norm(q_h - q_g + t * m_h, 2).^2 + lambda_q_2 * norm(angle(m_g, m_h), 2).^2;
    output.E_q = E_q;
end

function output = anchor(lambda_a_1, lambda_a_2, q, q_a, m, m_a, angle)
% output = anchor(`$λ_{a,1}$`, `$λ_{a,2}$`, q, `$q_a$`, m, `$m_a$`, `$\angle$`)
%
%    `E_a` = `$λ_{a,1}$`||q-`$q_a$`||^2 + `$λ_{a,2}$`||`$\angle$`(m,`$m_a$`)||^2 
%    where
%    `$λ_{a,1}$` ∈ ℝ : weight
%    `$λ_{a,2}$` ∈ ℝ : weight
%    q ∈ ℝ^n 
%    `$q_a$` ∈ ℝ^n 
%    m ∈ ℝ^n 
%    `$m_a$` ∈ ℝ^n 
%    `$\angle$` ∈ ℝ^n, ℝ^n -> ℝ^n
%    
    if nargin==0
        warning('generating random input data');
        [lambda_a_1, lambda_a_2, q, q_a, m, m_a, angle] = generateRandomData();
    end
    function [lambda_a_1, lambda_a_2, q, q_a, m, m_a, angle] = generateRandomData()
        lambda_a_1 = randn();
        lambda_a_2 = randn();
        n = randi(10);
        q = randn(n,1);
        q_a = randn(n,1);
        m = randn(n,1);
        m_a = randn(n,1);
        angle = @angleFunc;
        rseed = randi(2^32);
        function [ret] =  angleFunc(p0, p1)
            rng(rseed);
            ret = randn(n,1);
        end

    end

    q = reshape(q,[],1);
    q_a = reshape(q_a,[],1);
    m = reshape(m,[],1);
    m_a = reshape(m_a,[],1);

    n = size(q, 1);
    assert(numel(lambda_a_1) == 1);
    assert(numel(lambda_a_2) == 1);
    assert( numel(q) == n );
    assert( numel(q_a) == n );
    assert( numel(m) == n );
    assert( numel(m_a) == n );

    % `E_a` = `$λ_{a,1}$`||q-`$q_a$`||^2 + `$λ_{a,2}$`||`$\angle$`(m,`$m_a$`)||^2
    E_a = lambda_a_1 * norm(q - q_a, 2).^2 + lambda_a_2 * norm(angle(m, m_a), 2).^2;
    output.E_a = E_a;
end

function output = notchlimit(delta_minus_sign, delta_plus_sign, beta_q, beta_minus_sign, beta_plus_sign)
% output = notchlimit(`$δ^{(−)}$`, `$δ^{(+)}$`, `$β_q$`, `$β^{(−)}$`, `$β^{(+)}$`)
%
%    `E_n` = `$δ^{(−)}$`(1/10 log((`$β_q$`-`$β^{(−)}$`)))^2 + `$δ^{(+)}$`(1/10 log((`$β^{(+)}$`-`$β_q$`)))^2
%    where
%    `$δ^{(−)}$` ∈ ℝ 
%    `$δ^{(+)}$` ∈ ℝ
%    `$β_q$` ∈ ℝ :  barycentric coordinates 
%    `$β^{(−)}$` ∈ ℝ : the barycentric coordinates of the notch bounds on their corresponding edges
%    `$β^{(+)}$` ∈ ℝ : the barycentric coordinates of the notch bounds on their corresponding edges
%    
    if nargin==0
        warning('generating random input data');
        [delta_minus_sign, delta_plus_sign, beta_q, beta_minus_sign, beta_plus_sign] = generateRandomData();
    end
    function [delta_minus_sign, delta_plus_sign, beta_q, beta_minus_sign, beta_plus_sign] = generateRandomData()
        delta_minus_sign = randn();
        delta_plus_sign = randn();
        beta_q = randn();
        beta_minus_sign = randn();
        beta_plus_sign = randn();
    end

    assert(numel(delta_minus_sign) == 1);
    assert(numel(delta_plus_sign) == 1);
    assert(numel(beta_q) == 1);
    assert(numel(beta_minus_sign) == 1);
    assert(numel(beta_plus_sign) == 1);

    % `E_n` = `$δ^{(−)}$`(1/10 log((`$β_q$`-`$β^{(−)}$`)))^2 + `$δ^{(+)}$`(1/10 log((`$β^{(+)}$`-`$β_q$`)))^2
    E_n = delta_minus_sign * (1 / 10 * log((beta_q - beta_minus_sign))).^2 + delta_plus_sign * (1 / 10 * log((beta_plus_sign - beta_q))).^2;
    output.E_n = E_n;
end

function output = penalty(mu, epsilon, beta_q)
% output = penalty(μ, ε, `$β_q$`)
%
%    `E_p` = (μ log((ε + `$β_q$`)))^2 + (μ log((ε + 1 - `$β_q$`)))^2
%    where
%    μ ∈ ℝ : a weighting parameter
%    ε ∈ ℝ : denoting how far $q$ is allowed to move past the end of the edge
%    `$β_q$` ∈ ℝ :  barycentric coordinates 
%    
    if nargin==0
        warning('generating random input data');
        [mu, epsilon, beta_q] = generateRandomData();
    end
    function [mu, epsilon, beta_q] = generateRandomData()
        mu = randn();
        epsilon = randn();
        beta_q = randn();
    end

    assert(numel(mu) == 1);
    assert(numel(epsilon) == 1);
    assert(numel(beta_q) == 1);

    % `E_p` = (μ log((ε + `$β_q$`)))^2 + (μ log((ε + 1 - `$β_q$`)))^2
    E_p = (mu * log((epsilon + beta_q))).^2 + (mu * log((epsilon + 1 - beta_q))).^2;
    output.E_p = E_p;
end

