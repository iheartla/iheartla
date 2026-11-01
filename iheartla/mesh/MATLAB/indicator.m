function ret = indicator(ele_set, n)
% An n × 1 sparse column with a 1 at each index in ele_set (as indicator() in the C++ and Python runtimes).
    k = numel(ele_set);
    ret = sparse(reshape(ele_set, k, 1), ones(k, 1), ones(k, 1), n, 1);
end
