import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)


class TestDims(BasePythonTest):
    def test_matrix_dims_0(self):
        la_str = """M+N
                    where
                    M: ℝ^( m×m )
                    N: ℝ^( m×m ) """
        func_info = self.gen_func_info(la_str)
        P = np.array([[1, 2], [4, 3]])
        Q = np.array([[5, 6], [8, 7]])
        R = np.array([[6, 8], [12, 10]])
        self.assertDMatrixEqual(func_info.numpy_func(P, Q).ret, R)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(matlab.double(P.tolist()), matlab.double(Q.tolist()))['ret']), R)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> Q;",
                     "    Q << 5, 6, 8, 7;",
                     "    Eigen::Matrix<double, 2, 2> R;",
                     "    R << 6, 8, 12, 10;",
                     "    Eigen::Matrix<double, 2, 2> B = {}(P, Q).ret;".format(func_info.eig_func_name),
                     "    return ((B - R).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_matrix_dims_1(self):
        la_str = """M+N
                    where
                    m: ℤ
                    M: ℝ^( m×m )
                    N: ℝ^( m×m ) 
                    """
        func_info = self.gen_func_info(la_str)
        P = np.array([[1, 2], [4, 3]])
        Q = np.array([[5, 6], [8, 7]])
        R = np.array([[6, 8], [12, 10]])
        self.assertDMatrixEqual(func_info.numpy_func(2, P, Q).ret, R)
        # MATLAB test
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertDMatrixEqual(np.array(mat_func(2, matlab.double(P.tolist()), matlab.double(Q.tolist()))['ret']), R)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> Q;",
                     "    Q << 5, 6, 8, 7;",
                     "    Eigen::Matrix<double, 2, 2> R;",
                     "    R << 6, 8, 12, 10;",
                     "    Eigen::Matrix<double, 2, 2> B = {}(2, P, Q).ret;".format(func_info.eig_func_name),
                     "    return ((B - R).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_template_func(self):
        la_str = """f( M ) 
                    where 
                    M: ℝ^( m×m )
                    f: ℝ^( k×k ) -> ℝ """
        func_info = self.gen_func_info(la_str)
        P = np.array([[1, 2], [4, 3]])
        f = lambda p : np.trace(p)
        self.assertEqual(func_info.numpy_func(P, f).ret, 4)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 1, 2, 4, 3;",
                     "    std::function<double(Eigen::MatrixXd)> f;"
                     "    f = [](Eigen::MatrixXd p)->double{",
                     "    return p.trace();"
                     "    };",
                     "    double B = {}(P, f).ret;".format(func_info.eig_func_name),
                     "    return ((B - 4) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_template_func_2(self):
        la_str = """f( M )
                    where
                    M: ℝ^( k×k )
                    f: ℝ^( k×k ) -> ℝ """
        func_info = self.gen_func_info(la_str)
        P = np.array([[1, 2], [4, 3]])
        f = lambda p : np.trace(p)
        self.assertEqual(func_info.numpy_func(P, f).ret, 4)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 1, 2, 4, 3;",
                     "    std::function<double(Eigen::MatrixXd)> f;"
                     "    f = [](Eigen::MatrixXd p)->double{",
                     "    return p.trace();"
                     "    };",
                     "    double B = {}(P, f).ret;".format(func_info.eig_func_name),
                     "    return ((B - 4) == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_template_func_3(self):
        la_str = """f( M ) + f(N)
                    where
                    M: ℝ^( m×m )
                    N: ℝ^( m×m )
                    f: ℝ^( k×k ) -> ℝ^( k×k )  """
        func_info = self.gen_func_info(la_str)
        P = np.array([[1, 2], [4, 3]])
        Q = np.array([[5, 6], [8, 7]])
        f = lambda p : 2*p
        R = np.array([[12, 16], [24, 20]])
        self.assertDMatrixEqual(func_info.numpy_func(P, Q, f).ret, R)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> Q;",
                     "    Q << 5, 6, 8, 7;",
                     "    Eigen::Matrix<double, 2, 2> R;",
                     "    R << 12, 16, 24, 20;",
                     "    std::function<Eigen::MatrixXd(Eigen::MatrixXd)> f;"
                     "    f = [](Eigen::MatrixXd p)->Eigen::MatrixXd{",
                     "    return 2*p;"
                     "    };",
                     "    Eigen::MatrixXd B = {}(P, Q, f).ret;".format(func_info.eig_func_name),
                     "    return ((B - R).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())