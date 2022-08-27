function output = computation(lambda_s, E_a, D, S_1, S_2, U_1, U_2, R)
% output = computation(`$λ_s$`, `$E_a$`, D, `$S_1$`, `$S_2$`, `$U_1$`, `$U_2$`, R)
%
%    E = `$λ_s$``$E_s$` + (1 - `$λ_s$`)`$E_f$` 
%    where
%    `$λ_s$` ∈ ℝ 
%    
%    `$E_s$` = `$E_c$` + `$E_a$` 
%    where
%    `$E_a$` ∈ ℝ
%    
%    `$E_c$` = D(`$S_1$`, `$U_1$`) + D(`$S_2$`, `$U_2$`)
%    where
%    D ∈ ℝ, ℝ -> ℝ
%    `$S_1$` ∈ ℝ
%    `$S_2$` ∈ ℝ
%    `$U_1$` ∈ ℝ
%    `$U_2$` ∈ ℝ
%    
%    `$E_f$` = sum_i ||R_i||
%    where
%    
%    R_i ∈ ℝ^3
%    
    if nargin==0
        warning('generating random input data');
        [lambda_s, E_a, D, S_1, S_2, U_1, U_2, R] = generateRandomData();
    end
    function [lambda_s, E_a, D, S_1, S_2, U_1, U_2, R] = generateRandomData()
        lambda_s = randn();
        E_a = randn();
        S_1 = randn();
        S_2 = randn();
        U_1 = randn();
        U_2 = randn();
        dim_0 = randi(10);
        D = @DFunc;
        rseed = randi(2^32);
        function [ret] =  DFunc(p0, p1)
            rng(rseed);
            ret = randn();
        end

        R = randn(dim_0,3);
    end

    dim_0 = size(R, 1);
    assert(numel(lambda_s) == 1);
    assert(numel(E_a) == 1);
    assert(numel(S_1) == 1);
    assert(numel(S_2) == 1);
    assert(numel(U_1) == 1);
    assert(numel(U_2) == 1);
    assert( isequal(size(R), [dim_0, 3]) );

    % `$E_c$` = D(`$S_1$`, `$U_1$`) + D(`$S_2$`, `$U_2$`)
    E_c = D(S_1, U_1) + D(S_2, U_2);
    % `$E_s$` = `$E_c$` + `$E_a$`
    E_s = E_c + E_a;
    % `$E_f$` = sum_i ||R_i||
    sum_0 = 0;
    for i = 1:size(R, 1)
        sum_0 = sum_0 + norm(R(i,:)', 2);
    end
    E_f = sum_0;
    % E = `$λ_s$``$E_s$` + (1 - `$λ_s$`)`$E_f$`
    E = lambda_s * E_s + (1 - lambda_s) * E_f;
    output.E = E;
    output.E_s = E_s;
    output.E_c = E_c;
    output.E_f = E_f;
end

