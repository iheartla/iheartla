function output = pipeline(f_x, f_y, c_x, c_y, r, phi_1_d, phi_d, x_i, x_j, alpha_i, alpha_j, y, X, Y, Z, x)
% output = pipeline(`$f_x$`, `$f_y$`, `$c_x$`, `$c_y$`, r, `$φ^{-1}_d$`, `$φ_d$`, `$x_i$`, `$x_j$`, `$α_i$`, `$α_j$`, y, X, Y, Z, x)
%
%    `$\textbf{X}$` = (X,Y,Z)^T
%    ϕ = arcsin(C/D) 
%    D = √(A^2 +B^2)
%    γ = arctan(B/A)
%    K = [`$f_x$` 0 `$c_x$`
%          0   `$f_y$` `$c_y$`
%          0      0    1]
%    
%    where
%    
%    `$f_x$`: ℝ: focal length
%    `$f_y$`: ℝ: focal length
%    `$c_x$`: ℝ: principal point
%    `$c_y$`: ℝ: principal point
%    
%    sin, cos, atan from trigonometry
%    
%    R(α) = [-sin(α) 0 -cos(α)
%          0   1  0
%          cos(α)     0    -sin(α)] where α: ℝ
%    `$\textbf{t}$` = [0;0;-r]
%    where
%    
%    r: ℝ: the camera circle radius
%    
%    P(α) = K [R(α) `$\textbf{t}$`] where α: ℝ
%    
%    
%    `$\textbf{x}$`(α) = `$φ^{-1}_d$`((1-t(α)) ⋅ `$φ_d$`(`$x_i$`) + t(α)⋅ `$φ_d$`(`$x_j$`))  where α: ℝ 
%    
%    where
%    
%    `$φ^{-1}_d$`: ℝ^2 -> ℝ^2: inverse function of $φ_d$
%    `$φ_d$`: ℝ^2 -> ℝ^2 : the backprojection onto a cylinder with radius $d$ followed by a conversion to cylindrical coordinates
%    `$x_i$`: ℝ^2 : image point
%    `$x_j$`: ℝ^2 : image point
%    
%    t(α) = (α- `$α_i$`)/(`$α_j$`-`$α_i$`) where α: ℝ 
%    
%    where
%    
%    `$α_i$`: ℝ : angle
%    `$α_j$`: ℝ : angle
%    
%    φ(x) = (ω(x), s(x))  where x: ℝ 
%    y: ℝ
%    
%    
%    ω(x) = atan((x-`$c_x$`)/`$f_x$`) where x: ℝ   
%    s(x) = (y-`$c_y$`)⋅cos(ω(x)) where x: ℝ  
%    
%    A = X ⋅ `$f_x$` - Z⋅(x - `$c_x$` )
%    B = Z⋅`$f_x$` + X⋅(x -`$c_x$` ) 
%    C = -r⋅(x -`$c_x$` )
%    
%    where 
%    X: ℝ : coordinate value
%    Y: ℝ : coordinate value
%    Z: ℝ : coordinate value
%    x: ℝ 
%    
%    arcsin, arctan from trigonometry
%    `$α_1$` = ϕ - γ
%    `$α_2$` = π - ϕ - γ  
%    
%    
    if nargin==0
        warning('generating random input data');
        [f_x, f_y, c_x, c_y, r, phi_1_d, phi_d, x_i, x_j, alpha_i, alpha_j, y, X, Y, Z, x] = generateRandomData();
    end
    function [f_x, f_y, c_x, c_y, r, phi_1_d, phi_d, x_i, x_j, alpha_i, alpha_j, y, X, Y, Z, x] = generateRandomData()
        f_x = randn();
        f_y = randn();
        c_x = randn();
        c_y = randn();
        r = randn();
        alpha_i = randn();
        alpha_j = randn();
        y = randn();
        X = randn();
        Y = randn();
        Z = randn();
        x = randn();
        phi_1_d = @phi_1_dFunc;
        rseed = randi(2^32);
        function [ret] =  phi_1_dFunc(p0)
            rng(rseed);
            ret = randn(2,1);
        end

        phi_d = @phi_dFunc;
        rseed = randi(2^32);
        function [ret_1] =  phi_dFunc(p0)
            rng(rseed);
            ret_1 = randn(2,1);
        end

        x_i = randn(2,1);
        x_j = randn(2,1);
    end

    x_i = reshape(x_i,[],1);
    x_j = reshape(x_j,[],1);

    assert(numel(f_x) == 1);
    assert(numel(f_y) == 1);
    assert(numel(c_x) == 1);
    assert(numel(c_y) == 1);
    assert(numel(r) == 1);
    assert( numel(x_i) == 2 );
    assert( numel(x_j) == 2 );
    assert(numel(alpha_i) == 1);
    assert(numel(alpha_j) == 1);
    assert(numel(y) == 1);
    assert(numel(X) == 1);
    assert(numel(Y) == 1);
    assert(numel(Z) == 1);
    assert(numel(x) == 1);

    % `$\textbf{X}$` = (X,Y,Z)^T
    textbfX = [X; Y; Z]';
    % K = [`$f_x$` 0 `$c_x$`
    %       0   `$f_y$` `$c_y$`
    %       0      0    1]
    K_0 = zeros(3, 3);
    K_0(1,:) = [f_x, 0, c_x];
    K_0(2,:) = [0, f_y, c_y];
    K_0(3,:) = [0, 0, 1];
    K = K_0;
    % `$\textbf{t}$` = [0;0;-r]
    textbft_0 = zeros(3, 1);
    textbft_0(1,:) = [0];
    textbft_0(2,:) = [0];
    textbft_0(3,:) = [-r];
    textbft = textbft_0;
    % A = X ⋅ `$f_x$` - Z⋅(x - `$c_x$` )
    A = X * f_x - Z * (x - c_x);
    % B = Z⋅`$f_x$` + X⋅(x -`$c_x$` )
    B = Z * f_x + X * (x - c_x);
    % D = √(A^2 +B^2)
    D = sqrt((A.^2 + B.^2));
    % γ = arctan(B/A)
    gamma = atan(B / A);
    % C = -r⋅(x -`$c_x$` )
    C = -r * (x - c_x);
    % ϕ = arcsin(C/D)
    phi_ = asin(C / D);
    % `$α_1$` = ϕ - γ
    alpha_1 = phi_ - gamma;
    % `$α_2$` = π - ϕ - γ
    alpha_2 = pi - phi_ - gamma;
    function [ret_2] = R(alpha)
        assert(numel(alpha) == 1);

        R_0 = zeros(3, 3);
        R_0(1,:) = [-sin(alpha), 0, -cos(alpha)];
        R_0(2,:) = [0, 1, 0];
        R_0(3,:) = [cos(alpha), 0, -sin(alpha)];
        ret_2 = R_0;
    end

    function [ret_3] = P(alpha)
        assert(numel(alpha) == 1);

        P_0 = [[R(alpha), textbft]];
        ret_3 = K * P_0;
    end

    function [ret_4] = t(alpha)
        assert(numel(alpha) == 1);

        ret_4 = (alpha - alpha_i) / (alpha_j - alpha_i);
    end

    function [ret_5] = textbfx(alpha)
        assert(numel(alpha) == 1);

        ret_5 = phi_1_d((1 - t(alpha)) * phi_d(x_i) + t(alpha) * phi_d(x_j));
    end

    function [ret_6] = omega(x)
        assert(numel(x) == 1);

        ret_6 = atan((x - c_x) / f_x);
    end

    function [ret_7] = s(x)
        assert(numel(x) == 1);

        ret_7 = (y - c_y) * cos(omega(x));
    end

    function [ret_8] = phi(x)
        assert(numel(x) == 1);

        ret_8 = [omega(x); s(x)];
    end

    output.textbfX = textbfX;
    output.phi_ = phi_;
    output.D = D;
    output.gamma = gamma;
    output.K = K;
    output.textbft = textbft;
    output.A = A;
    output.B = B;
    output.C = C;
    output.alpha_1 = alpha_1;
    output.alpha_2 = alpha_2;
    output.R = @R;
    output.P = @P;
    output.textbfx = @textbfx;
    output.t = @t;
    output.phi = @phi;
    output.omega = @omega;
    output.s = @s;
    output.alpha_i = alpha_i;    
    output.alpha_j = alpha_j;    
    output.phi_1_d = phi_1_d;    
    output.phi_d = phi_d;    
    output.x_i = x_i;    
    output.x_j = x_j;    
    output.x = x;    
    output.c_x = c_x;    
    output.f_x = f_x;    
    output.y = y;    
    output.c_y = c_y;
end

