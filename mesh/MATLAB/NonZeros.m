function ret_set = NonZeros(target)
    output = nonzeros(target);
    [row, col] = find(output);
    ret_set = transpose(row);
end