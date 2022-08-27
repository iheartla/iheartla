function output = Generic(J, x, y, u, v)
% output = Generic(J, x, y, u, v)
%
%     `$x_p$` = (-y, x)
%     `$v_p$` = (-v, u)
%    M=[-J`$x_p$`+`$v_p$`  J  `$x_p$`  I_2] 
%    
%    where
%    J: ℝ^(2×2): The Jacobian matrix
%    x: ℝ : point coordinate
%    y: ℝ : point coordinate
%    u: ℝ : vector field coordinate
%    v: ℝ : vector field coordinate
%    
%    
    if nargin==0
        warning('generating random input data');
        [J, x, y, u, v] = generateRandomData();
    end
    function [J, x, y, u, v] = generateRandomData()
        x = randn();
        y = randn();
        u = randn();
        v = randn();
        J = randn(2, 2);
    end

    assert( isequal(size(J), [2, 2]) );
    assert(numel(x) == 1);
    assert(numel(y) == 1);
    assert(numel(u) == 1);
    assert(numel(v) == 1);

    % `$x_p$` = (-y, x)
    x_p = [-y; x];
    % `$v_p$` = (-v, u)
    v_p = [-v; u];
    % M=[-J`$x_p$`+`$v_p$`  J  `$x_p$`  I_2]
    M_0 = [[reshape(-J * x_p + v_p, [2, 1]), J, reshape(x_p, [2, 1]), speye(2)]];
    M = M_0;
    output.x_p = x_p;
    output.v_p = v_p;
    output.M = M;
end

