function output = siere(U_s, M, v, f, K, boldsymbolI, h, phi_1, u)
% output = siere(`$U_s$`, M, v, f, K, `$\boldsymbol{I}$`, h, `$φ_1$`, u)
%
%    `$G(u)$` = [`$v_G$`
%              M⁻¹`$f_G$`]
%    `$H(u)$` = [`$v_H$`
%              M⁻¹`$f_H$`]
%    `$v_G$` = `$U_s$``$U_s$`^T Mv
%    `$v_H$` =  v - `$v_G$`
%    `$f_G$` =  M`$U_s$``$U_s$`^T f
%    `$f_H$` =  f - `$f_G$`
%    
%    where 
%    `$U_s$` : ℝ^(n × s)
%    M : ℝ^(n × n)
%    v : ℝ^n
%    f : ℝ^n
%    K : ℝ^(n × n)
%    
%    `$J_G$` = [0    `$U_s$``$U_s$`^TM
%          -`$U_s$``$U_s$`^TK`$U_s$``$U_s$`^TM 0 ]
%    `$J_H$` =  [0     I_n
%                -M⁻¹K 0] - `$J_G$` 
%    
%    
%    `$u_+$` =  u + (`$\boldsymbol{I}$` -h`$J_H$`)⁻¹(h `$H(u)$` + h[`$U_s$` 0
%                                                   0   `$U_s$`] `$φ_1$`(h`$J_G^r$`) `$G^r(u)$`)
%    where 
%    `$\boldsymbol{I}$` : ℝ^(2n × 2n)
%    h : ℝ
%    `$φ_1$` : ℝ^(k×k) -> ℝ^(k×k)
%    u : ℝ^(2n × 1)
%    
%    `$J_G^r$` = [0     I_s
%                -`$U_s$`^TK`$U_s$` 0]
%    `$G^r(u)$` = [`$U_s$`^TMv
%                `$U_s$`^Tf]
%    
%    
    if nargin==0
        warning('generating random input data');
        [U_s, M, v, f, K, boldsymbolI, h, phi_1, u] = generateRandomData();
    end
    function [U_s, M, v, f, K, boldsymbolI, h, phi_1, u] = generateRandomData()
        h = randn();
        n = randi(10);
        s = randi(10);
        U_s = randn(n, s);
        M = randn(n, n);
        v = randn(n,1);
        f = randn(n,1);
        K = randn(n, n);
        boldsymbolI = randn(2*n, 2*n);
        phi_1 = @phi_1Func;
        rseed = randi(2^32);
        function [ret] =  phi_1Func(p0)
            rng(rseed);
            k = size(p0, 1);
            ret = randn(k,k);
        end

        u = randn(2*n, 1);
    end

    v = reshape(v,[],1);
    f = reshape(f,[],1);

    n = size(U_s, 1);
    s = size(U_s, 2);
    assert( isequal(size(U_s), [n, s]) );
    assert( isequal(size(M), [n, n]) );
    assert( numel(v) == n );
    assert( numel(f) == n );
    assert( isequal(size(K), [n, n]) );
    assert( isequal(size(boldsymbolI), [2*n, 2*n]) );
    assert(numel(h) == 1);
    assert( isequal(size(u), [2*n, 1]) );
    assert( mod(2*n, 1) == 0.0 );
    assert( mod(2*n, 1) == 0.0 );
    assert( mod(2*n, 1) == 0.0 );

    % `$v_G$` = `$U_s$``$U_s$`^T Mv
    v_G = U_s * U_s' * M * v;
    % `$v_H$` =  v - `$v_G$`
    v_H = v - v_G;
    % `$f_G$` =  M`$U_s$``$U_s$`^T f
    f_G = M * U_s * U_s' * f;
    % `$G(u)$` = [`$v_G$`
    %           M⁻¹`$f_G$`]
    Gu_0 = [[reshape(v_G, [n, 1])]; [reshape((M\f_G), [n, 1])]];
    Gu = Gu_0;
    % `$f_H$` =  f - `$f_G$`
    f_H = f - f_G;
    % `$H(u)$` = [`$v_H$`
    %           M⁻¹`$f_H$`]
    Hu_0 = [[reshape(v_H, [n, 1])]; [reshape((M\f_H), [n, 1])]];
    Hu = Hu_0;
    % `$J_G$` = [0    `$U_s$``$U_s$`^TM
    %       -`$U_s$``$U_s$`^TK`$U_s$``$U_s$`^TM 0 ]
    J_G_0 = [[zeros(n, n), U_s * U_s' * M]; [-U_s * U_s' * K * U_s * U_s' * M, zeros(n, n)]];
    J_G = J_G_0;
    % `$J_H$` =  [0     I_n
    %             -M⁻¹K 0] - `$J_G$`
    J_H_0 = [[zeros(n, n), speye(n)]; [-(M\K), zeros(n, n)]];
    J_H = J_H_0 - J_G;
    % `$J_G^r$` = [0     I_s
    %             -`$U_s$`^TK`$U_s$` 0]
    J_G_r_0 = [[zeros(s, s), speye(s)]; [-U_s' * K * U_s, zeros(s, s)]];
    J_G_r = J_G_r_0;
    % `$G^r(u)$` = [`$U_s$`^TMv
    %             `$U_s$`^Tf]
    G_ru_0 = [[reshape(U_s' * M * v, [s, 1])]; [reshape(U_s' * f, [s, 1])]];
    G_ru = G_ru_0;
    % `$u_+$` =  u + (`$\boldsymbol{I}$` -h`$J_H$`)⁻¹(h `$H(u)$` + h[`$U_s$` 0
    %                                                0   `$U_s$`] `$φ_1$`(h`$J_G^r$`) `$G^r(u)$`)
    u_plus_sign_2 = [[U_s, zeros(n, s)]; [zeros(n, s), U_s]];
    u_plus_sign = u + ((boldsymbolI - h * J_H)\(h * Hu + h * u_plus_sign_2 * phi_1(h * J_G_r) * G_ru));
    output.Gu = Gu;
    output.Hu = Hu;
    output.v_G = v_G;
    output.v_H = v_H;
    output.f_G = f_G;
    output.f_H = f_H;
    output.J_G = J_G;
    output.J_H = J_H;
    output.u_plus_sign = u_plus_sign;
    output.J_G_r = J_G_r;
    output.G_ru = G_ru;
end

function output = second(U_s, M, K)
% output = second(`$U_s$`, M, K)
%
%    `$J_G$` = `$Y_1$``$Z_1$`^T + `$Y_2$``$Z_2$`^T 
%    
%    `$Y_1$` =  [`$U_s$`
%                 0]
%    `$Z_1$` =  [ 0
%                 M`$U_s$`] 
%    `$Y_2$` =  [0
%                -`$U_s$``$U_s$`^TK`$U_s$`]
%    `$Z_2$` =  [ M`$U_s$`
%                 0] 
%    
%    where 
%    `$U_s$` : ℝ^(n × s)
%    M : ℝ^(n × n) 
%    K : ℝ^(n × n)
%    
    if nargin==0
        warning('generating random input data');
        [U_s, M, K] = generateRandomData();
    end
    function [U_s, M, K] = generateRandomData()
        n = randi(10);
        s = randi(10);
        U_s = randn(n, s);
        M = randn(n, n);
        K = randn(n, n);
    end

    n = size(U_s, 1);
    s = size(U_s, 2);
    assert( isequal(size(U_s), [n, s]) );
    assert( isequal(size(M), [n, n]) );
    assert( isequal(size(K), [n, n]) );

    % `$Y_1$` =  [`$U_s$`
    %              0]
    Y_1_0 = [[U_s]; [zeros(1, s)]];
    Y_1 = Y_1_0;
    % `$Z_1$` =  [ 0
    %              M`$U_s$`]
    Z_1_0 = [[zeros(1, s)]; [M * U_s]];
    Z_1 = Z_1_0;
    % `$Y_2$` =  [0
    %             -`$U_s$``$U_s$`^TK`$U_s$`]
    Y_2_0 = [[zeros(1, s)]; [-U_s * U_s' * K * U_s]];
    Y_2 = Y_2_0;
    % `$Z_2$` =  [ M`$U_s$`
    %              0]
    Z_2_0 = [[M * U_s]; [zeros(1, s)]];
    Z_2 = Z_2_0;
    % `$J_G$` = `$Y_1$``$Z_1$`^T + `$Y_2$``$Z_2$`^T
    J_G = Y_1 * Z_1' + Y_2 * Z_2';
    output.J_G = J_G;
    output.Y_1 = Y_1;
    output.Z_1 = Z_1;
    output.Y_2 = Y_2;
    output.Z_2 = Z_2;
end

