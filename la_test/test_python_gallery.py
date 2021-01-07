import sys
sys.path.append('./')
from la_test.base_python_test import BasePythonTest, eigen_path, TestFuncInfo
from la_parser.parser import parse_la, ParserTypeEnum
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)


class TestGallery(BasePythonTest):
    def test_gallery_0(self):
        # sequence
        la_str = """from trigonometry: sin, cos
        `x(θ, ϕ)` = [Rcos(θ)cos(ϕ)
                     Rsin(θ)cos(ϕ)
                     Rsin(ϕ)]
        where
        ϕ: ℝ : angle between 0 and 2π
        θ: ℝ : angle between -π/2 and π/2
        R: ℝ : the radius of the sphere"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[0], [0], [3]])
        self.assertDMatrixApproximateEqual(func_info.numpy_func(np.pi/2, np.pi/2, 3), A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> A;",
                     "    A << 0, 0, 3;",
                     "    Eigen::Matrix<double, 3, 1> B = {}(M_PI/2, M_PI/2, 3);".format(func_info.eig_func_name),
                     "    return ((A - B).norm() < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())
