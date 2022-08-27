function output = ICP(R, a, theta, p, q, n_q, n_p, t, barq, barp, trans, rot)
% output = ICP(R, a, θ, p, q, `$n_q$`, `$n_p$`, t, `$\bar{q}$`, `$\bar{p}$`, trans, rot)
%
%    ã = a tan(θ)
%    n_i = `$n_q$`_i + `$n_p$`_i
%    t̃ = t/cos(θ)
%     p̃_i = p_i - `$\bar{p}$` 
%     q̃_i = q_i - `$\bar{q}$` 
%    `$\varepsilon_{point}$` = ∑_i ||R p_i + t - q_i||
%    R ∈ ℝ^(3 × 3): the rigid-body rotation matrix
%    
%    `$\varepsilon_{plane}$` = ∑_i ((R p_i + t - q_i) ⋅ `$n_q$`_i)^2
%    
%    `$\varepsilon_{symm-RN}$` = ∑_i ((R p_i + R⁻¹ q_i + t) ⋅ (R`$n_p$`_i + R⁻¹`$n_q$`_i))^2
%    
%    tan, cos from trigonometry
%    
%    `$\varepsilon_{symm}$` = ∑_i cos²(θ)((p_i - q_i)⋅n_i +((p_i+q_i)×n_i)⋅ã+n_i⋅t̃)² 
%    
%    where
%    a ∈ ℝ³ : axis of rotation
%    θ ∈ ℝ  : angle of rotation
%    p_i ∈ ℝ³: a sequence of points
%    q_i ∈ ℝ³: a sequence of points
%    `$n_q$`_i ∈ ℝ³: the surface normals
%    `$n_p$`_i ∈ ℝ³: the surface normals
%    t ∈ ℝ³: the translation vector
%    
%    S = trans(`$\bar{q}$`) ⋅ rot(θ, ã/||ã||) ⋅trans(t̃ cos(θ)) ⋅rot(θ, ã/||ã||)⋅ trans(-`$\bar{p}$`)
%    
%    where 
%    `$\bar{q}$` ∈ ℝ³: the averaged coordinate of points
%    `$\bar{p}$` ∈ ℝ³: the averaged coordinate of points
%    trans ∈ ℝ³ -> ℝ^(4 × 4) : the translation function
%    rot ∈ ℝ, ℝ³ -> ℝ^(4 × 4): the rotation function
%    
%    `$\varepsilon_{two-plane}$` = ∑_i(((R p_i + R⁻¹ q_i + t) ⋅ (R `$n_p$`_i))^2 + ((R p_i + R⁻¹ q_i + t) ⋅ (R⁻¹`$n_q$`_i))^2)
%    
    if nargin==0
        warning('generating random input data');
        [R, a, theta, p, q, n_q, n_p, t, barq, barp, trans, rot] = generateRandomData();
    end
    function [R, a, theta, p, q, n_q, n_p, t, barq, barp, trans, rot] = generateRandomData()
        theta = randn();
        dim_0 = randi(10);
        R = randn(3, 3);
        a = randn(3,1);
        p = randn(dim_0,3);
        q = randn(dim_0,3);
        n_q = randn(dim_0,3);
        n_p = randn(dim_0,3);
        t = randn(3,1);
        barq = randn(3,1);
        barp = randn(3,1);
        trans = @transFunc;
        rseed = randi(2^32);
        function [ret] =  transFunc(p0)
            rng(rseed);
            ret = randn(4,4);
        end

        rot = @rotFunc;
        rseed = randi(2^32);
        function [ret_1] =  rotFunc(p0, p1)
            rng(rseed);
            ret_1 = randn(4,4);
        end

    end

    a = reshape(a,[],1);
    t = reshape(t,[],1);
    barq = reshape(barq,[],1);
    barp = reshape(barp,[],1);

    dim_0 = size(p, 1);
    assert( isequal(size(R), [3, 3]) );
    assert( numel(a) == 3 );
    assert(numel(theta) == 1);
    assert( isequal(size(p), [dim_0, 3]) );
    assert( isequal(size(q), [dim_0, 3]) );
    assert( isequal(size(n_q), [dim_0, 3]) );
    assert( isequal(size(n_p), [dim_0, 3]) );
    assert( numel(t) == 3 );
    assert( numel(barq) == 3 );
    assert( numel(barp) == 3 );

    % ã = a tan(θ)
    a_tilde = a * tan(theta);
    % n_i = `$n_q$`_i + `$n_p$`_i
    n = zeros(dim_0, 3);
    for i = 1:dim_0
        n(i,:) = (n_q(i,:)' + n_p(i,:)')';
    end
    % t̃ = t/cos(θ)
    t_tilde = t / cos(theta);
    % p̃_i = p_i - `$\bar{p}$`
    p_tilde = zeros(dim_0, 3);
    for i = 1:dim_0
        p_tilde(i,:) = (p(i,:)' - barp)';
    end
    % q̃_i = q_i - `$\bar{q}$`
    q_tilde = zeros(dim_0, 3);
    for i = 1:dim_0
        q_tilde(i,:) = (q(i,:)' - barq)';
    end
    % `$\varepsilon_{point}$` = ∑_i ||R p_i + t - q_i||
    sum_0 = 0;
    for i = 1:size(q, 1)
        sum_0 = sum_0 + norm(R * p(i,:)' + t - q(i,:)', 2);
    end
    varepsilon_point = sum_0;
    % `$\varepsilon_{plane}$` = ∑_i ((R p_i + t - q_i) ⋅ `$n_q$`_i)^2
    sum_1 = 0;
    for i = 1:size(p, 1)
        sum_1 = sum_1 + (dot((R * p(i,:)' + t - q(i,:)'),n_q(i,:)')).^2;
    end
    varepsilon_plane = sum_1;
    % `$\varepsilon_{symm-RN}$` = ∑_i ((R p_i + R⁻¹ q_i + t) ⋅ (R`$n_p$`_i + R⁻¹`$n_q$`_i))^2
    sum_2 = 0;
    for i = 1:size(p, 1)
        sum_2 = sum_2 + (dot((R * p(i,:)' + (R\q(i,:)') + t),(R * n_p(i,:)' + (R\n_q(i,:)')))).^2;
    end
    varepsilon_symmRN = sum_2;
    % `$\varepsilon_{symm}$` = ∑_i cos²(θ)((p_i - q_i)⋅n_i +((p_i+q_i)×n_i)⋅ã+n_i⋅t̃)²
    sum_3 = 0;
    for i = 1:size(p, 1)
        sum_3 = sum_3 + cos(theta).^2 * (dot((p(i,:)' - q(i,:)'),n(i,:)') + dot((cross((p(i,:)' + q(i,:)'), n(i,:)')),a_tilde) + dot(n(i,:)',t_tilde)).^2;
    end
    varepsilon_symm = sum_3;
    % S = trans(`$\bar{q}$`) ⋅ rot(θ, ã/||ã||) ⋅trans(t̃ cos(θ)) ⋅rot(θ, ã/||ã||)⋅ trans(-`$\bar{p}$`)
    S = trans(barq) * rot(theta, a_tilde / norm(a_tilde, 2)) * trans(t_tilde * cos(theta)) * rot(theta, a_tilde / norm(a_tilde, 2)) * trans(-barp);
    % `$\varepsilon_{two-plane}$` = ∑_i(((R p_i + R⁻¹ q_i + t) ⋅ (R `$n_p$`_i))^2 + ((R p_i + R⁻¹ q_i + t) ⋅ (R⁻¹`$n_q$`_i))^2)
    sum_4 = 0;
    for i = 1:size(p, 1)
        sum_4 = sum_4 + ((dot((R * p(i,:)' + (R\q(i,:)') + t),(R * n_p(i,:)'))).^2 + (dot((R * p(i,:)' + (R\q(i,:)') + t),((R\n_q(i,:)')))).^2);
    end
    varepsilon_twoplane = sum_4;
    output.a_tilde = a_tilde;
    output.n = n;
    output.t_tilde = t_tilde;
    output.p_tilde = p_tilde;
    output.q_tilde = q_tilde;
    output.varepsilon_point = varepsilon_point;
    output.varepsilon_plane = varepsilon_plane;
    output.varepsilon_symmRN = varepsilon_symmRN;
    output.varepsilon_symm = varepsilon_symm;
    output.S = S;
    output.varepsilon_twoplane = varepsilon_twoplane;
end

