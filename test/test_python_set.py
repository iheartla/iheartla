import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)


class TestSet(BasePythonTest):
    def test_set_init(self):
        # no return symbol
        la_str = """a =  {1, 2, 3}"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(list(func_info.numpy_func().a), [1,2,3])
        # MATLAB testv
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            # (an array: compare its items, assertEqual can't compare an array with a list)
            self.assertEqual(np.ravel(np.array(mat_func()['a'])).tolist(), [1, 2, 3])
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::vector<int > a = {}().a;".format(func_info.eig_func_name),
                     "    if(std::binary_search(a.begin(), a.end(), 1) && std::binary_search(a.begin(), a.end(), 2) && std::binary_search(a.begin(), a.end(), 3)){",
                     "        return true;",
                     "    }",
                     "    return false;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_set_not_in(self):
        # ∉ must negate the membership test, for both a set parameter and a set-valued call
        la_str = """L_i,j = { α_ij if j ∉ N(i)
        M_i,j = { α_ij if j ∉ S
        where
        L: ℝ^(n×n)
        M: ℝ^(n×n)
        α: ℝ^(n×n)
        N: ℤ -> {ℤ}
        S: {ℤ}
        """
        func_info = self.gen_func_info(la_str)
        α = np.array([[1., 2, 3], [4, 7, 6], [5, 3, 2]])
        def N(p0):
            if p0 == 1:
                return [2]
            elif p0 == 2:
                return [1]
            return [1, 2]
        S = [2]
        L = α.copy()
        L[0, 1] = L[1, 0] = L[2, 0] = L[2, 1] = 0
        M = α.copy()
        M[:, 1] = 0
        res = func_info.numpy_func(α, N, S)
        self.assertDMatrixEqual(res.L.toarray(), L)
        self.assertDMatrixEqual(res.M.toarray(), M)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> α;",
                     "    α << 1, 2, 3, 4, 7, 6, 5, 3, 2;",
                     "    std::function<std::vector<int >(int)> N = [](int p)->std::vector<int >{",
                     "        if(p == 1) return {2};",
                     "        if(p == 2) return {1};",
                     "        return {1, 2};",
                     "    };",
                     "    std::vector<int > S = {2};",
                     "    Eigen::Matrix<double, 3, 3> L = α;",
                     "    L(0, 1) = 0; L(1, 0) = 0; L(2, 0) = 0; L(2, 1) = 0;",
                     "    Eigen::Matrix<double, 3, 3> M = α;",
                     "    M.col(1).setZero();",
                     "    auto r = {}(α, N, S);".format(func_info.eig_func_name),
                     "    return Eigen::MatrixXd(r.L).isApprox(L) && Eigen::MatrixXd(r.M).isApprox(M);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_union_sequence_call(self):
        # union over a set of the sets returned by a function
        la_str = """A = ∪_(i ∈ T) N(i)
        where
        N: ℤ -> {ℤ}
        T: {ℤ}
        """
        func_info = self.gen_func_info(la_str)
        def N(p0):
            return [p0, p0 + 10]
        T = [1, 3]
        self.assertEqual(sorted(func_info.numpy_func(N, T).A), [1, 3, 11, 13])
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::function<std::vector<int >(int)> N = [](int p)->std::vector<int >{",
                     "        return {p, p + 10};",
                     "    };",
                     "    std::vector<int > T = {1, 3};",
                     "    std::vector<int > A = {}(N, T).A;".format(func_info.eig_func_name),
                     "    return A == std::vector<int >({1, 3, 11, 13});",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_union_index_set(self):
        # union over an index set: its elements are stored 0-based, and the name i is 1-based
        la_str = """A = ∪_(i ∈ T) N(i)
        where
        N: ℤ -> {ℤ}
        T: {ℤ} index
        """
        func_info = self.gen_func_info(la_str)
        def N(p0):
            return [p0, p0 + 10]
        T = [0, 2]  # i = 1 and i = 3
        self.assertEqual(sorted(func_info.numpy_func(N, T).A), [1, 3, 11, 13])
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::function<std::vector<int >(int)> N = [](int p)->std::vector<int >{",
                     "        return {p, p + 10};",
                     "    };",
                     "    std::vector<int > T = {0, 2};",
                     "    std::vector<int > A = {}(N, T).A;".format(func_info.eig_func_name),
                     "    return A == std::vector<int >({1, 3, 11, 13});",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_sequence_of_sets(self):
        # a sequence of sets as a parameter (not an integer array), sequence() appending to it, ∪_i
        la_str = """f(U) = sequence(U, {5}) where U_i ⊂ V
                    g(U) = ∪_i U_i where U_i ⊂ V
                    z = 1
                    where
                    V ∈ {ℤ}"""
        func_info = self.gen_func_info(la_str)
        h = func_info.numpy_func({1, 2, 5})
        self.assertEqual([sorted(s) for s in h.f([{1}, {2}])], [[1], [2], [5]])
        self.assertEqual(sorted(h.g([{1}, {2, 5}])), [1, 2, 5])
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::vector<int> V = {1, 2, 5};",
                     "    auto h = {}(V);".format(func_info.eig_func_name),
                     "    std::vector<std::vector<int>> s = h.f({{1}, {2}});",
                     "    return s.size() == 3 && s[2] == std::vector<int>({5}) && h.g({{1}, {2, 5}}) == std::vector<int>({1, 2, 5});",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_set_of_vectors_rows_svd(self):
        # rows from a set of vectors (m_i,* = d_i) in a local function, and svd (U, singular values, V)
        la_str = """svd from linearalgebra
                    f(S) = s where S ⊂ V,
                    d = {x_i for i ∈ S},
                    m_i,* = d_i,
                    u, s, vv = svd(m)
                    z = 1
                    where
                    V ∈ {ℤ}
                    x_i ∈ ℝ^3"""
        func_info = self.gen_func_info(la_str)
        h = func_info.numpy_func({1, 2, 3}, np.array([[1., 0, 0], [0, 2, 0], [0, 0, 3]]))
        self.assertDMatrixApproximateEqual(h.f({1, 2, 3}), np.array([3., 2., 1.]))

    def test_min_max_of_set(self):
        # the minimum of a set of values (np.amin of a Python set was the set itself)
        la_str = """f(S) = min({x_i for i ∈ S}) where S ⊂ V
                    g(S) = max({x_i for i ∈ S}) where S ⊂ V
                    z = 1
                    where
                    V ∈ {ℤ}
                    x_i ∈ ℝ"""
        func_info = self.gen_func_info(la_str)
        h = func_info.numpy_func({1, 2, 3}, np.array([2.5, -1., 4.]))
        self.assertEqual(h.f({1, 2, 3}), -1)
        self.assertEqual(h.g({1, 3}), 4)
