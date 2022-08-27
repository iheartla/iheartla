function output = Anisotropic(a, C, F)
% output = Anisotropic(a, C, F)
%
%     A = a a^T 
%    `$\lambda_{0,1,2}$`=2||a||_2^2
%    tr from linearalgebra
%    `$I_5$` = tr(CA)
%    
%    where
%    
%    a ∈ ℝ^3
%    C ∈ ℝ^(3×3)
%    
%    `$\frac{∂I₅}{∂F}$` = 2FA
%    F ∈ ℝ^(3×3): scaling and rotation matrix
%    
%    
%    `$\frac{∂²I₅}{∂f²}$` = 2[A₁,₁I₃  A₁,₂I₃  A₁,₃I₃
%                   A₂,₁I₃  A₂,₂I₃  A₂,₃I₃
%                   A₃,₁I₃  A₃,₂I₃  A₃,₃I₃] 
%    
%    
%    
%    `$\mathbf{Q}_{0}$` = [a^T
%                   0
%                   0] 
%    `$\mathbf{Q}_{1}$` = [0
%                        a^T
%                   0] 
%    `$\mathbf{Q}_{2}$` = [ 0
%                   0
%                   a^T] 
%    
%    
%    
    if nargin==0
        warning('generating random input data');
        [a, C, F] = generateRandomData();
    end
    function [a, C, F] = generateRandomData()
        a = randn(3,1);
        C = randn(3, 3);
        F = randn(3, 3);
    end

    a = reshape(a,[],1);

    assert( numel(a) == 3 );
    assert( isequal(size(C), [3, 3]) );
    assert( isequal(size(F), [3, 3]) );

    % A = a a^T 
    A = reshape(a, [3, 1]) * a';
    % `$\lambda_{0,1,2}$`=2||a||_2^2
    lambda_0_1_2 = 2 * norm(a, 2).^2;
    % `$I_5$` = tr(CA)
    I_5 = trace(C * A);
    % `$\frac{∂I₅}{∂F}$` = 2FA
    frac_partial_differential_I5_partial_differential_F = 2 * F * A;
    % `$\frac{∂²I₅}{∂f²}$` = 2[A₁,₁I₃  A₁,₂I₃  A₁,₃I₃
    %                A₂,₁I₃  A₂,₂I₃  A₂,₃I₃
    %                A₃,₁I₃  A₃,₂I₃  A₃,₃I₃] 
    frac_partial_differential_2I5_partial_differential_f2_0 = [[A(1, 1) * speye(3), A(1, 2) * speye(3), A(1, 3) * speye(3)]; [A(2, 1) * speye(3), A(2, 2) * speye(3), A(2, 3) * speye(3)]; [A(3, 1) * speye(3), A(3, 2) * speye(3), A(3, 3) * speye(3)]];
    frac_partial_differential_2I5_partial_differential_f2 = 2 * frac_partial_differential_2I5_partial_differential_f2_0;
    % `$\mathbf{Q}_{0}$` = [a^T
    %                0
    %                0] 
    mathbfQ_0_0 = [[a']; [zeros(1, 3)]; [zeros(1, 3)]];
    mathbfQ_0 = mathbfQ_0_0;
    % `$\mathbf{Q}_{1}$` = [0
    %                     a^T
    %                0] 
    mathbfQ_1_0 = [[zeros(1, 3)]; [a']; [zeros(1, 3)]];
    mathbfQ_1 = mathbfQ_1_0;
    % `$\mathbf{Q}_{2}$` = [ 0
    %                0
    %                a^T] 
    mathbfQ_2_0 = [[zeros(1, 3)]; [zeros(1, 3)]; [a']];
    mathbfQ_2 = mathbfQ_2_0;
    output.A = A;
    output.lambda_0_1_2 = lambda_0_1_2;
    output.I_5 = I_5;
    output.frac_partial_differential_I5_partial_differential_F = frac_partial_differential_I5_partial_differential_F;
    output.frac_partial_differential_2I5_partial_differential_f2 = frac_partial_differential_2I5_partial_differential_f2;
    output.mathbfQ_0 = mathbfQ_0;
    output.mathbfQ_1 = mathbfQ_1;
    output.mathbfQ_2 = mathbfQ_2;
end

function output = Anisotropic2D(a, A)
% output = Anisotropic2D(a, A)
%
%    `$\lambda_{0,1}$`=2||a||_2^2
%    tr from linearalgebra
%    `$\frac{∂²I₅}{∂f²}$` = 2[A₁,₁I_2  A₁,₂I_2
%                   A₂,₁I_2  A₂,₂I_2] 
%    
%    where
%    
%    a ∈ ℝ^2
%    A ∈ ℝ^(2×2)
%    
%    `$\mathbf{Q}_{0}$` = [a^T
%                   0] 
%    `$\mathbf{Q}_{1}$` = [0
%                        a^T] 
%    
    if nargin==0
        warning('generating random input data');
        [a, A] = generateRandomData();
    end
    function [a, A] = generateRandomData()
        a = randn(2,1);
        A = randn(2, 2);
    end

    a = reshape(a,[],1);

    assert( numel(a) == 2 );
    assert( isequal(size(A), [2, 2]) );

    % `$\lambda_{0,1}$`=2||a||_2^2
    lambda_0_1 = 2 * norm(a, 2).^2;
    % `$\frac{∂²I₅}{∂f²}$` = 2[A₁,₁I_2  A₁,₂I_2
    %                A₂,₁I_2  A₂,₂I_2] 
    frac_partial_differential_2I5_partial_differential_f2_0 = [[A(1, 1) * speye(2), A(1, 2) * speye(2)]; [A(2, 1) * speye(2), A(2, 2) * speye(2)]];
    frac_partial_differential_2I5_partial_differential_f2 = 2 * frac_partial_differential_2I5_partial_differential_f2_0;
    % `$\mathbf{Q}_{0}$` = [a^T
    %                0] 
    mathbfQ_0_0 = [[a']; [zeros(1, 2)]];
    mathbfQ_0 = mathbfQ_0_0;
    % `$\mathbf{Q}_{1}$` = [0
    %                     a^T] 
    mathbfQ_1_0 = [[zeros(1, 2)]; [a']];
    mathbfQ_1 = mathbfQ_1_0;
    output.lambda_0_1 = lambda_0_1;
    output.frac_partial_differential_2I5_partial_differential_f2 = frac_partial_differential_2I5_partial_differential_f2;
    output.mathbfQ_0 = mathbfQ_0;
    output.mathbfQ_1 = mathbfQ_1;
end

