function output = soft(D, boldsymbolu, sigma, alpha)
% output = soft(D, `$\boldsymbol{u}$`, σ, α)
%
%    `$F_S$` = sum_i α_i D_i(`$\boldsymbol{u}$`_i) + σ((sum_i α_i)/(sum_i α_i^2) - 1)
%    
%    where
%    
%    D_i: ℝ^3 -> ℝ
%    `$\boldsymbol{u}$`_i: ℝ^3
%    σ: ℝ
%    α_i: ℝ 
%    
    if nargin==0
        warning('generating random input data');
        [D, boldsymbolu, sigma, alpha] = generateRandomData();
    end
    function [D, boldsymbolu, sigma, alpha] = generateRandomData()
        sigma = randn();
        dim_0 = randi(10);
        D = {};
        D_f = @D_fFunc;
        rseed = randi(2^32);
        function [ret] =  D_fFunc(p0)
            rng(rseed);
            ret = randn();
        end
        for i = 1:dim_0
            D{end+1,1} = D_f;
        end
        boldsymbolu = randn(dim_0,3);
        alpha = randn(dim_0,1);
    end

    alpha = reshape(alpha,[],1);

    dim_0 = size(alpha, 1);
    assert( isequal(size(boldsymbolu), [dim_0, 3]) );
    assert(numel(sigma) == 1);
    assert( size(alpha,1) == dim_0 );

    % `$F_S$` = sum_i α_i D_i(`$\boldsymbol{u}$`_i) + σ((sum_i α_i)/(sum_i α_i^2) - 1)
    sum_0 = 0;
    for i = 1:size(boldsymbolu, 1)
        sum_0 = sum_0 + alpha(i) * D{i}(boldsymbolu(i,:)');
    end
    sum_1 = 0;
    for i = 1:size(alpha, 1)
        sum_1 = sum_1 + alpha(i);
    end
    sum_2 = 0;
    for i = 1:size(alpha, 1)
        sum_2 = sum_2 + alpha(i).^2;
    end
    F_S = sum_0 + sigma * ((sum_1) / (sum_2) - 1);
    output.F_S = F_S;
end

