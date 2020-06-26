import sys
sys.path.append('./')
from la_test.base_python_test import BasePythonTest, eigen_path, TestFuncInfo
from la_parser.parser import parse_la, ParserTypeEnum
import numpy as np
import scipy
from scipy import sparse
import cppyy
cppyy.add_include_path(eigen_path)


class TestBacktick(BasePythonTest):
    def test_backtick_input_set(self):
        la_str = """A = `!@#$%^&*()_+-=<>?,./;':"` `बलवान किया उपलब्ध संस्थान केन्द्रित`  `ΦΧΨΩΥΣΠΞΘΔΓ`
                    where 
                    `!@#$%^&*()_+-=<>?,./;':"`:scalar
                    `बलवान किया उपलब्ध संस्थान केन्द्रित`:scalar
                    `ΦΧΨΩΥΣΠΞΘΔΓ`:scalar"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(1, 2, 3), 6)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    double B = {}(1, 2, 3);".format(func_info.eig_func_name),
                     "    return (B == 6);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_backtick_sub(self):
        la_str = """A = sum_`j_i` `Energy`_`j_i`
                    where 
                    `Energy`_`index`: ℝ ^ (2 × 2): a sequence"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[[1, 2], [4, 3]], [[1, 2], [4, 3]]])
        B = np.array([[2, 4], [8, 6]])
        self.assertDMatrixEqual(func_info.numpy_func(A), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A1;",
                     "    A1 << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A2;",
                     "    A2 << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 2, 4, 8, 6;",
                     "    std::vector<Eigen::Matrix<double, 2, 2> > A;",
                     "    A.push_back(A1);",
                     "    A.push_back(A2);",
                     "    Eigen::Matrix<double, 2, 2> C = {}(A);".format(func_info.eig_func_name),
                     "    return ((C - B).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_backtick_function(self):
        la_str = """`Output` = `Parameters` `Minimize`(`Parameters`)
                    where 
                    `Parameters`: ℝ ^ (2 × 2): a matrix 
                    `Minimize`: ℝ^(2 × 2) -> ℝ^(2 × 2): a function """
        func_info = self.gen_func_info(la_str)
        P = np.array([[1, 2], [4, 3]])
        f = lambda p : p+p
        A = np.array([[18, 16], [32, 34]])
        self.assertDMatrixEqual(func_info.numpy_func(P, f), A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> P;",
                     "    P << 1, 2, 4, 3;",
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 18, 16, 32, 34;",
                     "    std::function<Eigen::Matrix<double, 2, 2>(Eigen::Matrix<double, 2, 2>)> f;"
                     "    f = [](Eigen::Matrix<double, 2, 2> p)->Eigen::Matrix<double, 2, 2>{",
                     "    return p + p;"
                     "    };",
                     "    Eigen::Matrix<double, 2, 2> B = {}(P, f);".format(func_info.eig_func_name),
                     "    return ((B - A).norm() == 0);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())