% This Matlab code snippet calculates judder as described in "A Luminance-Aware
% Model of Judder Perception", publish in ACM TOG 2019 by Alexandre
% Chapiro, Robin Atkins and Scott Daly.

% sample query of the model
function judder()
    % loading the model coefficients as described in the supplementary
    % material
    p = loadModelTerms();
    
    % let's use the model to predict the judder of a 24 FPS, 2.5 nit scene
    % with a pan of 7 seconds!
    F = 24; % FPS
    L = 2.5; % nits
    S = 7; % second pan
    % remember to convert the variables as described in Appendix A3
    F_ = 1/F;
    L_ = log10(L);
    S_ = 1920/S;
    % applying the model
    Jval = useModel(p,F_,L_,S_);
    
    sprintf('F = %f FPS, L = %f nits, S = %f s/pic | Judder = %f', ...
        F, L, S, Jval)
    
end

% queries the model at points F_,L_,S_ using the polynomial model p
function Jval = useModel(p,F_,L_,S_)
  
    Jval = zeros(size(L_));
    for i = 1:size(p.ModelTerms,1)
        Jval = Jval + p.Coefficients(i)*...
            ((F_.^p.ModelTerms(i,1)).*...
             (L_.^p.ModelTerms(i,2)).*...
             (S_.^p.ModelTerms(i,3)));
    end

end

% model as coefficients presented in our paper and supplementary material
function p = loadModelTerms()
    % represents the powers to which each variable is taken
    p.ModelTerms = [2     0     0
                    1     1     0
                    1     0     1
                    1     0     0
                    0     2     0
                    0     1     1
                    0     1     0
                    0     0     2
                    0     0     1
                    0     0     0];
    % proper coefficients 
    p.Coefficients = [1620.37267080746,86.8082906256909, ...
         0.320448868447774,-95.5544193256484,-0.318628091166034, ...
         0.000763570204858091,-0.476231268832550,-1.00998175043235e-05, ...
         -0.000937624477501956,2.34848262897281];
end
