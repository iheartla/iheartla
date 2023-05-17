function mesh = triangle_mesh(T)
    function output = permute_rvector(source)
        if ~isempty(source)
            min_index = 1;
            cur_val = source(1);
            for i =2:length(source)
                if source(i) < cur_val
                    cur_val = source(i);
                    min_index = i;
                end
            end
            if min_index ~= 1
                res = zeros(1, length(source));
                for i =1:length(source)
                    res(i) = source(mod(i + min_index - 2, length(source))+1);
                end
                output = res;
                return 
            end 
        end
        output = source;
    end

    function less = compare_vec(fir, sec)
        less = true;
        for i=1:length(fir)
            if fir(i) ~= sec(i)
                if fir(i) > sec(i)
                    less = false;
                end 
                break
            end
        end
    end

    function output = swap(source, i, j)
        for k=1:size(source, 2)
            tmp = source(i, k);
            source(i, k) = source(j, k);
            source(j, k) = tmp;
        end
        output = source;
    end

    function output = swap_vector(source, i, j)
        tmp = source(i);
        source(i) = source(j);
        source(j) = tmp;
        output = source;
    end

    function [p, output] = partition(source, start, endv)
        pivot = source(endv, :);
        i = start - 1;
        for j=start:endv-1
            cur = source(j, :);
            if compare_vec(cur, pivot)
                i = i + 1;
                source = swap(source, i, j);
            end
        end
        source = swap(source, i + 1, endv);
    	p = i + 1;
        output = source;
    end

    function [p, output] = partition_vector(source, start, endv)
        pivot = source(endv);
        i = start - 1;
        for j=start:endv-1
            if source(j) < pivot
                i = i + 1;
                source = swap_vector(source, i, j);
            end
        end
        source = swap_vector(source, i + 1, endv);
        p = i + 1;
        output = source;
    end

    function output = quick_sort(source, start, endv)
        if start >= endv
            output = source;
            return
        end
        [p, source] = partition(source, start, endv);
        source = quick_sort(source, start, p - 1);
        source = quick_sort(source, p + 1, endv);
        output = source;
    end
    
    function output = quick_sort_vector(source, start, endv)
        if start >= endv
            output = source;
            return
        end
        [p, source] = partition_vector(source, start, endv);
        source = quick_sort_vector(source, start, p - 1);
        source = quick_sort_vector(source, p + 1, endv);
        output = source;
    end

    function output = sort_matrix(source)
        source = quick_sort(source, 1, size(source, 1));
    	output = source;
    end

    function output = sort_vector(source)
        source = quick_sort_vector(source, 1, length(source));
        output = source;
    end
    
    function output = remove_duplicate_rows(source)
        if size(source, 1) == 0
            output = source;
            return
        end
        output = zeros(size(source));
        cur = source(1, :);
        output(1, :) = cur;
        cnt = 2;
        for j=1:size(source, 1)-1
            if isequal(cur, source(j + 1, :))
                continue
            else
                cur = source(j + 1, :);
                output(cnt, :) = cur;
                cnt = cnt + 1;
            end 
        end
        output = output(1:cnt-1, :);
    end 

    function output = preprocess_matrix(source)
        new_source = zeros(size(source));
        for i=1:size(source, 1)
            new_source(i, :) = permute_rvector(source(i, :));
        end
        output = remove_duplicate_rows(sort_matrix(new_source));
    end
    
    % mesh related
    function initialize(T)
        mesh.V = 1:max(T, [], 'all');
        mesh.T = preprocess_matrix(T);
        mesh.map_f = dictionary;
        mesh.map_e = dictionary;
        if size(T, 2) == 4
            % tets
            create_faces();
            create_edges();
            build_boundary_mat1();
            build_boundary_mat2();
            build_boundary_mat3();
        elseif size(T, 2) == 3
            % faces
            mesh.F = T;
            create_edges();
            build_boundary_mat1();
            build_boundary_mat2();
        end
        init_mesh_indices();
    end
    
    function output = face_key(i, j, k)
        output = keyHash("i" + int2str(i) + "j" + int2str(j) + "k" + int2str(k));
    end

    function output = edge_key(i, j)
        output = keyHash("i" + int2str(i) + "j" + int2str(j));
    end

    function [idx, sign] = get_edge_index(i, j)
        sign = -1;
        if i < j
            sign = 1;
            idx = mesh.map_e(edge_key(i, j));
            return
        end
        idx = mesh.map_e(edge_key(j, i));
    end

    function [idx, sign] = get_face_index(i, j, k)
        sign = -1;
        p = permute_rvector([i, j, k]);
        key = face_key(p(1), p(2), p(3));
        if isKey(mesh.map_f, key)
            sign = 1;
            idx = mesh.map_f(key);
            return
        end
        key = face_key(p(1), p(3), p(2));
        idx = mesh.map_f(key);
    end

    function create_faces
        F = zeros(4*size(mesh.T, 1), 3, 'uint32');
        for i=1:size(mesh.T, 1)
            F(4 * i - 3, :) = sort_vector([mesh.T(i, 1), mesh.T(i, 2), mesh.T(i, 3)]);
            F(4 * i - 2, :) = sort_vector([mesh.T(i, 1), mesh.T(i, 2), mesh.T(i, 4)]);
            F(4 * i - 1, :) = sort_vector([mesh.T(i, 1), mesh.T(i, 3), mesh.T(i, 4)]);
            F(4 * i, :) = sort_vector([mesh.T(i, 2), mesh.T(i, 3), mesh.T(i, 4)]);
        end
        mesh.F = remove_duplicate_rows(sort_matrix(F));
        for i=1:size(mesh.F, 1)
            key = face_key(mesh.F(i, 1), mesh.F(i, 2), mesh.F(i, 3));
            mesh.map_f(key) = i;
        end
    end

    function create_edges
        E = zeros(3*size(mesh.F, 1), 2, 'uint32'); 
        for i=1:size(mesh.F, 1)
            E(3 * i - 2, :) = sort_vector([mesh.F(i, 1), mesh.F(i, 2)]);
            E(3 * i - 1, :) = sort_vector([mesh.F(i, 1), mesh.F(i, 3)]);
            E(3 * i, :) = sort_vector([mesh.F(i, 2), mesh.F(i, 3)]);
        end
        mesh.E = remove_duplicate_rows(sort_matrix(E));
        for i=1:size(mesh.E, 1)
            key = edge_key(mesh.E(i, 1), mesh.E(i, 2));
            mesh.map_e(key) = i;
        end
    end

    function build_boundary_mat1
        index_list = zeros(2,0);
        value_list = zeros(1,0);
        for i=1:size(mesh.E, 1)
            index_list(1:2, end+1) = [mesh.E(i, 1); i];
            value_list(end+1) = -1;
            index_list(1:2, end+1) = [mesh.E(i, 2); i];
            value_list(end+1) = 1;
        end
        mesh.bm1 = sparse(index_list(1,:), index_list(2,:), value_list, length(mesh.V), size(mesh.E, 1));
        mesh.pos_bm1 = abs(mesh.bm1);
    end

    function build_boundary_mat2
        index_list = zeros(2,0);
        value_list = zeros(1,0);
        for i=1:size(mesh.F, 1)
            [idx, sign] = get_edge_index(mesh.F(i, 1), mesh.F(i, 2));
            index_list(1:2, end+1) = [idx; i];
            value_list(end+1) = sign;
            [idx, sign] = get_edge_index(mesh.F(i, 1), mesh.F(i, 3));
            index_list(1:2, end+1) = [idx; i];
            value_list(end+1) = -sign;
            [idx, sign] = get_edge_index(mesh.F(i, 2), mesh.F(i, 3));
            index_list(1:2, end+1) = [idx; i];
            value_list(end+1) = sign;
        end
        mesh.bm2 = sparse(index_list(1,:), index_list(2,:), value_list, size(mesh.E, 1), size(mesh.F, 1));
        mesh.pos_bm2 = abs(mesh.bm2);
    end

    function build_boundary_mat3
        index_list = zeros(2,0);
        value_list = zeros(1,0);
        for i=1:size(mesh.T, 1)
            [idx, sign] = get_face_index(mesh.T(i, 1), mesh.T(i, 2), mesh.T(i, 3));
            index_list(1:2, end+1) = [idx; i];
            value_list(end+1) = -sign;
            [idx, sign] = get_face_index(mesh.T(i, 1), mesh.T(i, 2), mesh.T(i, 4));
            index_list(1:2, end+1) = [idx; i];
            value_list(end+1) = sign;
            [idx, sign] = get_face_index(mesh.T(i, 1), mesh.T(i, 3), mesh.T(i, 4));
            index_list(1:2, end+1) = [idx; i];
            value_list(end+1) = -sign;
            [idx, sign] = get_face_index(mesh.T(i, 2), mesh.T(i, 3), mesh.T(i, 4));
            index_list(1:2, end+1) = [idx; i];
            value_list(end+1) = sign;
        end
        mesh.bm3 = sparse(index_list(1,:), index_list(2,:), value_list, size(mesh.F, 1), size(mesh.T, 1));
        mesh.pos_bm3 = abs(mesh.bm2);
    end

    function init_mesh_indices
        mesh.Vi = 1:length(mesh.V);
        mesh.Ei = 1:size(mesh.E, 1);
        mesh.Fi = 1:size(mesh.F, 1);
        mesh.Ti = 1:size(mesh.T, 1);
    end

    function output = vertices_to_vector(vset)
        index_list = zeros(2,0);
        value_list = zeros(1,0);
        for i=1:length(vset)
            index_list(1:2, end+1) = [vset(i); 1];
            value_list(end+1) = 1;
        end
        output = sparse(index_list(1,:), index_list(2,:), value_list, length(mesh.V), 1);
    end

    function output = edges_to_vector(eset)
        index_list = zeros(2,0);
        value_list = zeros(1,0);
        for i=1:length(eset)
            index_list(1:2, end+1) = [eset(i); 1];
            value_list(end+1) = 1;
        end
        output = sparse(index_list(1,:), index_list(2,:), value_list, size(mesh.E, 1), 1);
    end

    function output = faces_to_vector(fset)
        index_list = zeros(2,0);
        value_list = zeros(1,0);
        for i=1:length(fset)
            index_list(1:2, end+1) = [fset(i); 1];
            value_list(end+1) = 1;
        end
        output = sparse(index_list(1,:), index_list(2,:), value_list, size(mesh.F, 1), 1);
    end

    function output = tets_to_vector(tset)
        index_list = zeros(2,0);
        value_list = zeros(1,0);
        for i=1:length(tset)
            index_list(1:2, end+1) = [tset(i); 1];
            value_list(end+1) = 1;
        end
        output = sparse(index_list(1,:), index_list(2,:), value_list, size(mesh.T, 1), 1);
    end

    function output = n_vertices()
        output = length(mesh.V);
    end

    function output = n_edges()
        output = length(mesh.Ei);
    end

    function output = n_faces()
        output = length(mesh.Fi);
    end

    function output = n_tets()
        output = length(mesh.Ti);
    end

    function ret_set = NonZeros(target)
        output = nonzeros(target);
        [row, col] = find(output);
        ret_set = transpose(row);
    end

    function [v, e, f] = MeshSets
        v = mesh.Vi;
        e = mesh.Ei;
        f = mesh.Fi;
    end

    function [b1, b2] = BoundaryMatrices
        b1 = mesh.bm1;
        b2 = mesh.bm2;
    end

    function [b1, b2] = UnsignedBoundaryMatrices
        b1 = mesh.pos_bm1;
        b2 = mesh.pos_bm2;
    end

    % body
    initialize(T);
    mesh.vertices_to_vector = @vertices_to_vector;
    mesh.edges_to_vector = @edges_to_vector;
    mesh.faces_to_vector = @faces_to_vector;
    mesh.tets_to_vector = @tets_to_vector;
    mesh.n_vertices = @n_vertices;
    mesh.NonZeros = @NonZeros;
    mesh.n_edges = @n_edges;
    mesh.n_faces = @n_faces;
    mesh.n_tets = @n_tets;
    mesh.MeshSets = @MeshSets;
    mesh.BoundaryMatrices = @BoundaryMatrices;
    mesh.UnsignedBoundaryMatrices = @UnsignedBoundaryMatrices;
%     a= triangle_mesh([0 1 2 3; 1 2 3 4] + ones(2, 4))
%     mesh.permute_rvector = @permute_rvector;
%     mesh.preprocess_matrix = @preprocess_matrix;
%     mesh.c = mesh.preprocess_matrix([[1, 31, 4]; [1, 3, 1]; [1, 1, 1]; [31, 4, 1]]);
%     mesh.s = preprocess_matrix([[1, 31, 4]; [1, 3, 1]; [1, 1, 1]; [31, 4, 1]]);
% 	  mesh.faces_to_vector = sort_vector([3, 2, 1, 8,1, 3]);
end