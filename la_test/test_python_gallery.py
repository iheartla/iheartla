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

    def test_gallery_1(self):
        # sequence
        la_str = """min_(x ∈ ℝ^n) ∑_i ||A_i x + b_i ||_2 +(1/2)||x-`x₀`||^2_2
        where
        A_i: ℝ^(m × n)  
        `x₀`: ℝ^n  
        b_i: ℝ^m  """
        func_info = self.gen_func_info(la_str)
        A = np.array([[[1, 2], [4, 3]], [[1, 2], [4, 3]]])
        x0 = [1, 2]
        b = np.array([[1, 2], [4, 3]])
        self.assertTrue(np.isclose(func_info.numpy_func(A, x0, b), 6.76227768454))

    def test_gallery_2(self):
        # sequence
        la_str = """y_i = (a_i)ᵀ x + w_i
        x̂ = (∑_i a_i(a_i)ᵀ)⁻¹ ∑_i y_i a_i
        where
        a_i: ℝ^(n×1): the measurement vectors  
        w_i: ℝ: measurement noise 
        x: ℝ^n: measurement noise """
        func_info = self.gen_func_info(la_str)
        A = np.array([[[1], [8], [3]], [[2], [9], [2]]])
        x = [4, 3, 9]
        w = [1, 4]
        b = np.array([[-16], [-4], [8]])
        self.assertDMatrixApproximateEqual(func_info.numpy_func(A, w, x), b)
        # eigen test
        # cppyy.include(func_info.eig_file_name)
        # func_list = ["bool {}(){{".format(func_info.eig_test_name),
        #              "    Eigen::Matrix<double, 3, 1> A1;",
        #              "    A1 << 1, 8, 3;",
        #              "    Eigen::Matrix<double, 3, 1> A2;",
        #              "    A2 << 2, 9, 2;",
        #              "    Eigen::Matrix<double, 3, 1> B;",
        #              "    B << -16, -4, 8;",
        #              "    Eigen::Matrix<double, 3, 1> x;",
        #              "    x << 4, 3, 9;",
        #              "    std::vector<Eigen::Matrix<double, 3, 1> > A;",
        #              "    A.push_back(A1);",
        #              "    A.push_back(A2);",
        #              "    std::vector<double> w;",
        #              "    w.push_back(1);",
        #              "    w.push_back(4);",
        #              "    Eigen::Matrix<double, 3, 1> C = {}(A, w, x);".format(func_info.eig_func_name),
        #              "    return ((C - B).norm() < {});".format(self.eps),
        #              "}"]
        # cppyy.cppdef('\n'.join(func_list))
        # self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_3(self):
        # sequence
        la_str = """[A⁻¹+A⁻¹BS⁻¹BᵀA⁻¹   -A⁻¹BS⁻¹
        -S⁻¹BᵀA⁻¹           S⁻¹]
        where
        A: ℝ^(2×2) 
        B: ℝ^(2×2) 
        S: ℝ^(2×2)"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[9, 12], [15, 16]])
        S = np.array([[0, 2], [5, 8]])
        b = np.array([[-9.2, -3.8, 1.6, 0.6], [2.4, 4.6, -0.2, -1.2], [3.6, 0.4, -0.8, 0.2], [-2.25, -0.75, 0.5, 0]])
        self.assertDMatrixApproximateEqual(func_info.numpy_func(A, B, S), b)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> A;",
                     "    A << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 9, 12, 15, 16;",
                     "    Eigen::Matrix<double, 2, 2> S;",
                     "    S << 0, 2, 5, 8;",
                     "    Eigen::Matrix<double, 4, 4> D;",
                     "    D << -9.2, -3.8, 1.6, 0.6,"
                     "    2.4, 4.6, -0.2, -1.2,"
                     "    3.6, 0.4, -0.8, 0.2,"
                     "    -2.25, -0.75, 0.5, 0;",
                     "    Eigen::Matrix<double, 4, 4> C = {}(A, B, S);".format(func_info.eig_func_name),
                     "    return ((C - D).norm() < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_4(self):
        # sequence
        la_str = """[P₁  0
         0   P₃][    L        0
                 P₃ᵀCP₂ᵀU⁻¹  -L̃][U  L⁻¹P₁ᵀB
                                 0     Ũ   ][P₂   0
                                             0   I_2]
        where
        P_i: ℝ^(2×2) 
        B: ℝ^(2×2) 
        C: ℝ^(2×2) 
        L: ℝ^(2×2) 
        L̃: ℝ^(2×2) 
        U: ℝ^(2×2) 
        Ũ: ℝ^(2×2)"""
        func_info = self.gen_func_info(la_str)
        P = np.array([[[1, 2], [3, 4]], [[1, 2], [3, 4]], [[1, 2], [3, 4]]])
        B = np.array([[1, 2], [3, 4]])
        C = np.array([[1, 2], [3, 4]])
        L = np.array([[1, 2], [3, 4]])
        L̃ = np.array([[1, 2], [3, 4]])
        U = np.array([[1, 2], [3, 4]])
        Ũ = np.array([[1, 2], [3, 4]])
        R = np.array([[199, 290, 38, 54], [435, 634, 86, 122], [1136, 1612, -1407, -1887], [2568, 3644, -3179, -4263]])
        self.assertDMatrixApproximateEqual(func_info.numpy_func(P, B, C, L, L̃, U, Ũ), R)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::vector<Eigen::Matrix<double, 2, 2> > P;",
                     "    Eigen::Matrix<double, 2, 2> B;",
                     "    B << 1, 2, 3, 4;",
                     "    P.push_back(B);",
                     "    P.push_back(B);",
                     "    P.push_back(B);",
                     "    Eigen::Matrix<double, 2, 2> C;",
                     "    C << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> L;",
                     "    L << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> L̃;",
                     "    L̃ << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> U;",
                     "    U << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 2, 2> Ũ;",
                     "    Ũ << 1, 2, 3, 4;",
                     "    Eigen::Matrix<double, 4, 4> R;",
                     "    R << 199, 290, 38, 54,"
                     "    435, 634, 86, 122,"
                     "    1136, 1612, -1407, -1887,"
                     "    2568, 3644, -3179, -4263;",
                     "    Eigen::Matrix<double, 4, 4> G = {}(P, B, C, L, L̃, U, Ũ);".format(func_info.eig_func_name),
                     "    return ((G - R).norm() < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_5(self):
        # sequence
        la_str = """`∂²I₅/∂f²` = 2[(A_1,1)I_3  (A_1,2)I_3  (A_1,3)I_3
               (A_2,1)I_3  (A_2,2)I_3  (A_2,3)I_3
               (A_3,1)I_3  (A_3,2)I_3  (A_3,3)I_3] 
        where
        A: ℝ^(3×3) """
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        B = 2*np.array([[1, 0, 0, 2, 0, 0, 3, 0, 0],
                      [0, 1, 0, 0, 2, 0, 0, 3, 0],
                      [0, 0, 1, 0, 0, 2, 0, 0, 3],
                      [4, 0, 0, 5, 0, 0, 6, 0, 0],
                      [0, 4, 0, 0, 5, 0, 0, 6, 0],
                      [0, 0, 4, 0, 0, 5, 0, 0, 6],
                      [7, 0, 0, 8, 0, 0, 9, 0, 0],
                      [0, 7, 0, 0, 8, 0, 0, 9, 0],
                      [0, 0, 7, 0, 0, 8, 0, 0, 9]])
        self.assertDMatrixApproximateEqual(func_info.numpy_func(A), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> A;",
                     "    A << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    Eigen::Matrix<double, 9, 9> B;",
                     "    B << 1, 0, 0, 2, 0, 0, 3, 0, 0,"
                     "    0, 1, 0, 0, 2, 0, 0, 3, 0,"
                     "    0, 0, 1, 0, 0, 2, 0, 0, 3,"
                     "    4, 0, 0, 5, 0, 0, 6, 0, 0,"
                     "    0, 4, 0, 0, 5, 0, 0, 6, 0,"
                     "    0, 0, 4, 0, 0, 5, 0, 0, 6,"
                     "    7, 0, 0, 8, 0, 0, 9, 0, 0,"
                     "    0, 7, 0, 0, 8, 0, 0, 9, 0,"
                     "    0, 0, 7, 0, 0, 8, 0, 0, 9;",
                     "    Eigen::Matrix<double, 9, 9> C = {}(A);".format(func_info.eig_func_name),
                     "    return ((2*B - C).norm() < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())
