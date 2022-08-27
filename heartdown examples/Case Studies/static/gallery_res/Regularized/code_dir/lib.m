function output = Regularized(r, boldsymbolf, s, boldsymbolF, r_epsilon, a, b, epsilon)
% output = Regularized(r, `$\boldsymbol{f}$`, s, `$\boldsymbol{F}$`, `$r_ε$`, a, b, ε)
%
%    `$\boldsymbol{u}$`(`$\boldsymbol{r}$`) = ((a-b)/rI_3 + b/r³ `$\boldsymbol{r}$` `$\boldsymbol{r}$`^T) `$\boldsymbol{f}$` where `$\boldsymbol{r}$` ∈ ℝ^3
%    
%    where
%    r ∈ ℝ: the norm of $\boldsymbol{r}$
%    
%    `${\rho}_ε$`(`$\boldsymbol{r}$`) = (15`$r_ε$`^4/(8π) + 1/`$r_ε$`^7 )  where `$\boldsymbol{r}$` ∈ ℝ^3
%    
%    
%    `$\boldsymbol{u}_ε$`(`$\boldsymbol{r}$`) = ((a-b)/`$r_ε$`I_3 + b/`$r_ε$`³ `$\boldsymbol{r}$` `$\boldsymbol{r}$`^T + aε²/(2`$r_ε$`³) I_3 ) `$\boldsymbol{f}$` where `$\boldsymbol{r}$` ∈ ℝ^3
%    
%    where
%    
%    `$\boldsymbol{f}$` ∈ ℝ^3: force vector
%    
%    tr from linearalgebra
%    `$\tilde{\boldsymbol{u}}_ε$`(`$\boldsymbol{r}$`) = -a(1/`$r_ε$`³ + 3ε²/(2`$r_ε$`⁵) ) `$\boldsymbol{F}$``$\boldsymbol{r}$` + b(1/`$r_ε$`³(`$\boldsymbol{F}$`+`$\boldsymbol{F}$`^T+tr(`$\boldsymbol{F}$`)I_3) - 3/`$r_ε$`⁵(`$\boldsymbol{r}$`^T`$\boldsymbol{F}$``$\boldsymbol{r}$`)I_3)`$\boldsymbol{r}$` where `$\boldsymbol{r}$` ∈ ℝ^3
%    
%    `$\boldsymbol{t}_ε$`(`$\boldsymbol{r}$`) = -a(1/`$r_ε$`³ + 3ε²/(2`$r_ε$`⁵) ) `$\boldsymbol{F}$``$\boldsymbol{r}$` where `$\boldsymbol{r}$` ∈ ℝ^3
%    
%    `$\boldsymbol{s}_ε$`(`$\boldsymbol{r}$`) = (2b-a)(1/`$r_ε$`³ + 3ε²/(2`$r_ε$`⁵))(s`$\boldsymbol{r}$`) where `$\boldsymbol{r}$` ∈ ℝ^3
%    
%    where
%    
%    s ∈ ℝ
%    
%    `$\boldsymbol{p}_ε$`(`$\boldsymbol{r}$`) = (2b-a)/`$r_ε$`³ `$\boldsymbol{F}$``$\boldsymbol{r}$` - 3/(2`$r_ε$`⁵)(2b(`$\boldsymbol{r}$`ᵀ`$\boldsymbol{F}$``$\boldsymbol{r}$`)I_3+aε²`$\boldsymbol{F}$`)`$\boldsymbol{r}$` where `$\boldsymbol{r}$` ∈ ℝ^3
%    
%    where
%    
%    `$\boldsymbol{F}$` ∈ ℝ^(3×3): force matrix 
%    `$r_ε$` ∈ ℝ
%    a ∈ ℝ : coefficient
%    b ∈ ℝ : coefficient
%    ε ∈ ℝ : the radial scale
%    
    if nargin==0
        warning('generating random input data');
        [r, boldsymbolf, s, boldsymbolF, r_epsilon, a, b, epsilon] = generateRandomData();
    end
    function [r, boldsymbolf, s, boldsymbolF, r_epsilon, a, b, epsilon] = generateRandomData()
        r = randn();
        s = randn();
        r_epsilon = randn();
        a = randn();
        b = randn();
        epsilon = randn();
        boldsymbolf = randn(3,1);
        boldsymbolF = randn(3, 3);
    end

    boldsymbolf = reshape(boldsymbolf,[],1);

    assert(numel(r) == 1);
    assert( numel(boldsymbolf) == 3 );
    assert(numel(s) == 1);
    assert( isequal(size(boldsymbolF), [3, 3]) );
    assert(numel(r_epsilon) == 1);
    assert(numel(a) == 1);
    assert(numel(b) == 1);
    assert(numel(epsilon) == 1);

    function [ret] = boldsymbolu(boldsymbolr)
        boldsymbolr = reshape(boldsymbolr,[],1);
        assert( numel(boldsymbolr) == 3 );

        ret = ((a - b) / r * speye(3) + reshape(b / r.^3 * boldsymbolr, [3, 1]) * boldsymbolr') * boldsymbolf;
    end

    function [ret_1] = rho_epsilon(boldsymbolr)
        boldsymbolr = reshape(boldsymbolr,[],1);
        assert( numel(boldsymbolr) == 3 );

        ret_1 = (15 * r_epsilon.^4 / (8 * pi) + 1 / r_epsilon.^7);
    end

    function [ret_2] = boldsymbolu_epsilon(boldsymbolr)
        boldsymbolr = reshape(boldsymbolr,[],1);
        assert( numel(boldsymbolr) == 3 );

        ret_2 = ((a - b) / r_epsilon * speye(3) + reshape(b / r_epsilon.^3 * boldsymbolr, [3, 1]) * boldsymbolr' + a * epsilon.^2 / (2 * r_epsilon.^3) * speye(3)) * boldsymbolf;
    end

    function [ret_3] = tildeboldsymbolu_epsilon(boldsymbolr)
        boldsymbolr = reshape(boldsymbolr,[],1);
        assert( numel(boldsymbolr) == 3 );

        ret_3 = -a * (1 / r_epsilon.^3 + 3 * epsilon.^2 / (2 * r_epsilon.^5)) * boldsymbolF * boldsymbolr + b * (1 / r_epsilon.^3 * (boldsymbolF + boldsymbolF' + trace(boldsymbolF) * speye(3)) - 3 / r_epsilon.^5 * (boldsymbolr' * boldsymbolF * boldsymbolr) * speye(3)) * boldsymbolr;
    end

    function [ret_4] = boldsymbolt_epsilon(boldsymbolr)
        boldsymbolr = reshape(boldsymbolr,[],1);
        assert( numel(boldsymbolr) == 3 );

        ret_4 = -a * (1 / r_epsilon.^3 + 3 * epsilon.^2 / (2 * r_epsilon.^5)) * boldsymbolF * boldsymbolr;
    end

    function [ret_5] = boldsymbols_epsilon(boldsymbolr)
        boldsymbolr = reshape(boldsymbolr,[],1);
        assert( numel(boldsymbolr) == 3 );

        ret_5 = (2 * b - a) * (1 / r_epsilon.^3 + 3 * epsilon.^2 / (2 * r_epsilon.^5)) * (s * boldsymbolr);
    end

    function [ret_6] = boldsymbolp_epsilon(boldsymbolr)
        boldsymbolr = reshape(boldsymbolr,[],1);
        assert( numel(boldsymbolr) == 3 );

        ret_6 = (2 * b - a) / r_epsilon.^3 * boldsymbolF * boldsymbolr - 3 / (2 * r_epsilon.^5) * (2 * b * (boldsymbolr' * boldsymbolF * boldsymbolr) * speye(3) + a * epsilon.^2 * boldsymbolF) * boldsymbolr;
    end

    output.boldsymbolu = @boldsymbolu;
    output.rho_epsilon = @rho_epsilon;
    output.boldsymbolu_epsilon = @boldsymbolu_epsilon;
    output.tildeboldsymbolu_epsilon = @tildeboldsymbolu_epsilon;
    output.boldsymbolt_epsilon = @boldsymbolt_epsilon;
    output.boldsymbols_epsilon = @boldsymbols_epsilon;
    output.boldsymbolp_epsilon = @boldsymbolp_epsilon;
    output.a = a;    
    output.b = b;    
    output.r = r;    
    output.boldsymbolf = boldsymbolf;    
    output.r_epsilon = r_epsilon;    
    output.epsilon = epsilon;    
    output.boldsymbolF = boldsymbolF;    
    output.s = s;
end

