function output = lib(F, L, S, P, a, b, M, L_a, L_b)
% output = judder(F, L, S, P, a, b, M, `$L_a$`, `$L_b$`)
%
%    J = P(α(F), β(L), S)
%    F ∈ ℝ
%    L ∈ ℝ
%    S ∈ ℝ
%    P ∈ ℝ, ℝ, ℝ -> ℝ
%    
%    
%    CFF(L) = a ⋅ log(L) + b where L ∈ ℝ
%    
%    a ∈ ℝ
%    b ∈ ℝ
%    
%    
%    `$F_a$` = M⋅ CFF(`$L_a$`)
%    
%    M ∈ ℝ
%    `$L_a$` ∈ ℝ
%    
%    `$F_b$` = M⋅ CFF(`$L_b$`)
%    
%    `$L_b$` ∈ ℝ
%    
%    α(F) = 1/F where F ∈ ℝ
%    
%    β(L) = log_10(L) where L ∈ ℝ
%    
    if nargin==0
        warning('generating random input data');
        [F, L, S, P, a, b, M, L_a, L_b] = generateRandomData();
    end
    function [F, L, S, P, a, b, M, L_a, L_b] = generateRandomData()
        F = randn();
        L = randn();
        S = randn();
        a = randn();
        b = randn();
        M = randn();
        L_a = randn();
        L_b = randn();
        P = @PFunc;
        rseed = randi(2^32);
        function tmp =  PFunc(p0, p1, p2)
            rng(rseed);
            tmp = randn();
        end

    end

    assert(numel(F) == 1);
    assert(numel(L) == 1);
    assert(numel(S) == 1);
    assert(numel(a) == 1);
    assert(numel(b) == 1);
    assert(numel(M) == 1);
    assert(numel(L_a) == 1);
    assert(numel(L_b) == 1);

    % `$F_a$` = M⋅ CFF(`$L_a$`)
    F_a = M * CFF(L_a);
    % `$F_b$` = M⋅ CFF(`$L_b$`)
    F_b = M * CFF(L_b);
    % J = P(α(F), β(L), S)
    J = P(alpha(F), beta(L), S);
    function ret = CFF(L)
        assert(numel(L) == 1);

        ret = a * log(L) + b;
    end

    function ret = alpha(F)
        assert(numel(F) == 1);

        ret = 1 / F;
    end

    function ret = beta(L)
        assert(numel(L) == 1);

        ret = log10(L);
    end

    output.J = J;
    output.F_a = F_a;
    output.F_b = F_b;
    output.CFF = @CFF;
    output.alpha = @alpha;
    output.beta = @beta;
output.L = L;    
output.a = a;    
output.b = b;    
output.F = F;
end

function output = error(O, M)
% output = error(O, M)
%
%    E = sum_i |log(O_i) - log(M_i)|/log(O_i) 
%    
%    O ∈ ℝ^N
%    M ∈ ℝ^N
%    
%    
    if nargin==0
        warning('generating random input data');
        [O, M] = generateRandomData();
    end
    function [O, M] = generateRandomData()
        N = randi(10);
        O = randn(N,1);
        M = randn(N,1);
    end

    O = reshape(O,[],1);
    M = reshape(M,[],1);

    N = size(O, 1);
    assert( numel(O) == N );
    assert( numel(M) == N );

    % E = sum_i |log(O_i) - log(M_i)|/log(O_i) 
    sum_0 = 0;
    for i = 1:size(O,1)
        sum_0 = sum_0 + abs(log(O(i)) - log(M(i))) / log(O(i));
    end
    E = sum_0;
    output.E = E;
end

function output = third(a, b, F_b, F_a, L_a)
% output = third(a, b, `$F_b$`, `$F_a$`, `$L_a$`)
%
%    
%    `$L_b$` = 10^((a `$F_b$`log((`$L_a$`))+b(`$F_b$`-`$F_a$`))/(a`$F_a$`))
%    a ∈ ℝ
%    b ∈ ℝ
%    `$F_b$` ∈ ℝ
%    `$F_a$` ∈ ℝ
%    `$L_a$` ∈ ℝ
%    
%    
    if nargin==0
        warning('generating random input data');
        [a, b, F_b, F_a, L_a] = generateRandomData();
    end
    function [a, b, F_b, F_a, L_a] = generateRandomData()
        a = randn();
        b = randn();
        F_b = randn();
        F_a = randn();
        L_a = randn();
    end

    assert(numel(a) == 1);
    assert(numel(b) == 1);
    assert(numel(F_b) == 1);
    assert(numel(F_a) == 1);
    assert(numel(L_a) == 1);

    % `$L_b$` = 10^((a `$F_b$`log((`$L_a$`))+b(`$F_b$`-`$F_a$`))/(a`$F_a$`))
    L_b = 10.^((a * F_b * log((L_a)) + b * (F_b - F_a)) / (a * F_a));
    output.L_b = L_b;
end

