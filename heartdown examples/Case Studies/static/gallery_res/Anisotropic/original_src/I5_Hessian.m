function [H] = I5_Hessian(U, Sigma, V, a)
  A = a * a';
  H = zeros(9,9);
  for i = 1:3
    for j = 1:3
      block = 2 * A(i,j) * eye(3,3);
      iStart = (i - 1) * 3 + 1;
      iEnd = i * 3;
      jStart = (j - 1) * 3 + 1;
      jEnd = j * 3;
      H(iStart:iEnd, jStart:jEnd) = block;
    end
  end
end
