function [H] = I5_Hessian(U, Sigma, V, a)
  H = lib(a, zeros(3,3), zeros(3,3)).frac_partial_differential_2I5_partial_differential_f2;
end
