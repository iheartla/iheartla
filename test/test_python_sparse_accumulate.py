import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import scipy.sparse
import cppyy
cppyy.add_include_path(eigen_path)
if TEST_MATLAB:
    import matlab


# A weighted graph on 3 vertices whose edge set E includes the self-loop (0, 0): E is the nonzeros of w.
W = np.array([[5., 1., 2.], [1., 0., 3.], [2., 3., 0.]])
E_LOOP = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)]
F = [(0, 1), (2, 2)]


def dense_of(edges, values, n=3):
    M = np.zeros((n, n))
    for (i, j), v in zip(edges, values):
        M[i, j] += v
    return M


class TestSparseAccumulate(BasePythonTest):
    # L_i,i = e on a sparse matrix defined before replaces its diagonal (it used to add e to the old
    # diagonal entries, because COO and setFromTriplets sum duplicates); L_i,i += e adds to it.
    # x += e with no earlier definition of x defines it (iheartla#131, #144); a `where` line may hold
    # its first condition (`where a ∈ ℝ`).
    def check_sparse(self, la_str, args, eig_args, mat_args, expected):
        func_info = self.gen_func_info(la_str)
        L = func_info.numpy_func(*args).L
        self.assertTrue(scipy.sparse.issparse(L))
        np.testing.assert_array_equal(L.toarray(), expected)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            L = mat_func(*mat_args)['L']
            np.testing.assert_array_equal(L.toarray() if hasattr(L, 'toarray') else np.array(L), expected)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name)] + eig_args + [
                     "    Eigen::MatrixXd A = {}({}).L;".format(func_info.eig_func_name, ', '.join(eig_arg_names(eig_args))),
                     "    Eigen::MatrixXd B(3, 3);",
                     "    B << {};".format(', '.join(repr(float(x)) for x in np.asarray(expected).ravel())),
                     "    return A == B;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def graph_args(self, edges):
        # (NumPy args, Eigen declarations, MATLAB args) for w and an edge set
        eig = ["    Eigen::Matrix<double, 3, 3> w;",
               "    w << {};".format(', '.join(repr(float(x)) for x in W.ravel())),
               "    std::vector< std::tuple< int, int > > E;"] + \
              ["    E.push_back(std::make_tuple({}, {}));".format(i, j) for i, j in edges]
        mat = [matlab.double(W.tolist()), matlab.int32([[i + 1, j + 1] for i, j in edges])] if TEST_MATLAB else []
        return [W, edges], eig, mat

    def laplacian_expected(self, edges, include_diagonal):
        first = dense_of(edges, [W[i, j] for i, j in edges])
        L = first.copy()
        for i in range(3):
            L[i, i] = -(first[i].sum() if include_diagonal else first[i].sum() - first[i, i])
        return L

    def test_diagonal_replaces(self):
        args, eig, mat = self.graph_args(E_LOOP)
        self.check_sparse("""L_i,j = { w_i,j if (i,j) ∈ E
        L_i,i = -sum_(l for l != i) L_i,l
        where
        L: ℝ^(3×3)
        w: ℝ^(3×3)
        E: {ℤ²} index""", args, eig, mat, self.laplacian_expected(E_LOOP, include_diagonal=False))

    def test_diagonal_replaces_sum_includes_old_diagonal(self):
        # the right-hand side reads L as the first line left it, its diagonal included: L₀₀ = −(5+1+2)
        args, eig, mat = self.graph_args(E_LOOP)
        expected = self.laplacian_expected(E_LOOP, include_diagonal=True)
        self.assertEqual(expected[0, 0], -8)
        self.check_sparse("""L_i,j = { w_i,j if (i,j) ∈ E
        L_i,i = -sum_l L_i,l
        where
        L: ℝ^(3×3)
        w: ℝ^(3×3)
        E: {ℤ²} index""", args, eig, mat, expected)

    def test_diagonal_without_self_loops_unchanged(self):
        edges = [e for e in E_LOOP if e[0] != e[1]]
        args, eig, mat = self.graph_args(edges)
        self.check_sparse("""L_i,j = { w_i,j if (i,j) ∈ E
        L_i,i = -sum_(l for l != i) L_i,l
        where
        L: ℝ^(3×3)
        w: ℝ^(3×3)
        E: {ℤ²} index""", args, eig, mat, self.laplacian_expected(edges, include_diagonal=False))

    def test_diagonal_accumulates(self):
        # L_i,i += 10 adds to the diagonal the first line set (5 at (0, 0), 0 elsewhere)
        args, eig, mat = self.graph_args(E_LOOP)
        expected = dense_of(E_LOOP, [W[i, j] for i, j in E_LOOP]) + 10 * np.eye(3)
        self.check_sparse("""L_i,j = { w_i,j if (i,j) ∈ E
        L_i,i += 10
        where
        L: ℝ^(3×3)
        w: ℝ^(3×3)
        E: {ℤ²} index""", args, eig, mat, expected)

    def test_accumulate_two_edge_sets(self):
        # L = w on E, plus 1 on F: (0, 1) is in both, (2, 2) only in F
        args, eig, mat = self.graph_args(E_LOOP)
        eig = eig + ["    std::vector< std::tuple< int, int > > F;"] + \
            ["    F.push_back(std::make_tuple({}, {}));".format(i, j) for i, j in F]
        if TEST_MATLAB:
            mat = mat + [matlab.int32([[i + 1, j + 1] for i, j in F])]
        expected = dense_of(E_LOOP, [W[i, j] for i, j in E_LOOP]) + dense_of(F, [1, 1])
        self.check_sparse("""L_i,j = { w_i,j if (i,j) ∈ E
        L_i,j += { 1 if (i,j) ∈ F
        where
        L: ℝ^(3×3)
        w: ℝ^(3×3)
        E: {ℤ²} index
        F: {ℤ²} index""", args + [F], eig, mat, expected)

    def test_accumulate_without_definition(self):
        # iheartla#131: no `L_i,j = { 0 if (i,j) ∈ E` first
        args, eig, mat = self.graph_args(E_LOOP)
        self.check_sparse("""L_i,j += { w_i,j if (i,j) ∈ E
        where
        L: ℝ^(3×3)
        w: ℝ^(3×3)
        E: {ℤ²} index""", args, eig, mat, dense_of(E_LOOP, [W[i, j] for i, j in E_LOOP]))

    def check_scalar(self, la_str, args, expected):
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(*args).a, expected)
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func(*[matlab.double([x]) for x in args])['a']), expected)
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}({}).a == {};".format(func_info.eig_func_name, ', '.join(repr(float(x)) for x in args), repr(float(expected))),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_scalar_accumulate_without_definition(self):
        # iheartla#144: parses (where with its condition on the same line), and a is not a parameter
        self.check_scalar("""a += 2
        where a ∈ ℝ""", [], 2)

    def test_scalar_accumulate_onto_definition(self):
        self.check_scalar("""a = b
        a += 2
        where b ∈ ℝ""", [1], 3)

    def test_latex_shows_accumulation(self):
        tex = compile_la_content("""L_i,j += { w_i,j if (i,j) ∈ E
        where
        L: ℝ^(3×3)
        w: ℝ^(3×3)
        E: {ℤ²} index""", ParserTypeEnum.LATEX)[ParserTypeEnum.LATEX]
        self.assertIn('\\mathrel{+}=', tex)


def eig_arg_names(eig_args):
    # the variables the Eigen declarations define, in order
    names = []
    for line in eig_args:
        line = line.strip()
        if line.endswith(';') and ' << ' not in line and '.push_back' not in line:
            names.append(line[:-1].split()[-1])
    return names
