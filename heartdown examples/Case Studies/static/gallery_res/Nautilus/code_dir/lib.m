function output = nautilus(x, lambda_, v)
% output = nautilus(x, λ, v)
%
%    H = PSP⁻¹
%    
%    P = [1 x₁ 0
%         0 x₂ 0
%         x₃ x₄ 1]
%    S = [x₅ x₆ x₇
%         x₈ x₉ x₁₀
%         0 0 1]
%    where
%    x ∈ ℝ^n
%    
%    E(x) = λ||(x₅, x₈) - (x₉, x₆)||^2 + sum_i ||H v_i - PSP⁻¹ v_i||^2 where x ∈ ℝ^n
%    
%    where
%    λ ∈ ℝ
%    v_i ∈ ℝ^(3 × 3)
%    
    if nargin==0
        warning('generating random input data');
        [x, lambda_, v] = generateRandomData();
    end
    function [x, lambda_, v] = generateRandomData()
        lambda_ = randn();
        n = randi(10);
        dim_0 = randi(10);
        x = randn(n,1);
        v = randn(dim_0,3,3);
    end

    x = reshape(x,[],1);

    n = size(x, 1);
    dim_0 = size(v, 1);
    assert( numel(x) == n );
    assert(numel(lambda_) == 1);
    assert( isequal(size(v), [dim_0, 3, 3]) );

    % P = [1 x₁ 0
    %      0 x₂ 0
    %      x₃ x₄ 1]
    P_0 = zeros(3, 3);
    P_0(1,:) = [1, x(1), 0];
    P_0(2,:) = [0, x(2), 0];
    P_0(3,:) = [x(3), x(4), 1];
    P = P_0;
    % S = [x₅ x₆ x₇
    %      x₈ x₉ x₁₀
    %      0 0 1]
    S_0 = zeros(3, 3);
    S_0(1,:) = [x(5), x(6), x(7)];
    S_0(2,:) = [x(8), x(9), x(10)];
    S_0(3,:) = [0, 0, 1];
    S = S_0;
    % H = PSP⁻¹
    H = P * S * inv(P);
    function [ret] = E(x)
        x = reshape(x,[],1);
        n = size(x, 1);
        assert( numel(x) == n );

        sum_0 = 0;
        for i = 1:size(v, 1)
            sum_0 = sum_0 + norm(H * squeeze(v(i,:,:)) - P * S * (P\squeeze(v(i,:,:))), 'fro').^2;
        end
        ret = lambda_ * norm([x(5); x(8)] - [x(9); x(6)], 2).^2 + sum_0;
    end

    output.H = H;
    output.P = P;
    output.S = S;
    output.E = @E;
    output.x = x;    
    output.lambda_ = lambda_;    
    output.v = v;
end

