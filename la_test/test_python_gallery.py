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

    def test_gallery_1_1(self):
        # sequence
        la_str = """min_(u ∈ ℝ^6) uᵀ(∑_i [x_i×n̂_i; n̂_i][(x_i×n̂_i)ᵀ n̂_iᵀ])u - 2uᵀ(∑_i [x_i×n̂_i; n̂_i]n̂_iᵀ(p_i-x_i)) + ∑_i(p_i-x_i)ᵀn̂_i n̂_iᵀ(p_i-x_i)
        where
        x_i: ℝ^3 
        n̂_i: ℝ^3  
        p_i: ℝ^3  """
        func_info = self.gen_func_info(la_str)
        x = np.array([[-11, 2, 3], [4, 5, 6], [17, 8, 9]])
        n̂ = np.array([[4, 15, 6], [7, -18, 9], [1, 22, 3]])
        p = np.array([[7, -8, 9], [1, 12, 3], [4, -5, 6]])
        self.assertTrue(np.isclose(func_info.numpy_func(x, n̂ , p), 0))

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

    def test_gallery_6(self):
        # sequence
        la_str = """from linearalgebra: tr
        `J₃` = [1_3,3]
        `k_angle(Dₘ)` = 3(sqrt(2)v)^(2/3)(7/4||Dₘ||_F^2-1/4tr(`J₃` (Dₘ)ᵀDₘ))⁻¹
        where
        Dₘ: ℝ^(3×3)
        v: ℝ"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        v = 10
        self.assertTrue(np.isclose(func_info.numpy_func(A, v), 0.06060140390))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> A;",
                     "    A << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    double C = {}(A, 10);".format(func_info.eig_func_name),
                     "    return (abs(0.06060140390 - C) < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_7(self):
        # sequence
        la_str = """xᵢ = T_*,1
        xⱼ = T_*,2
        xₖ = T_*,3
        `n(T)` = (xⱼ-xᵢ)×(xₖ-xᵢ)/||(xⱼ-xᵢ)×(xₖ-xᵢ)||
        where
        T: ℝ^(3×3)"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2, 3], [3, 8, 6], [7, 8, 7]])
        B = np.array([-0.38100038, 0.25400025, -0.88900089])
        self.assertDMatrixApproximateEqual(func_info.numpy_func(A), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> A;",
                     "    A << 1, 2, 3, 3, 8, 6, 7, 8, 7;",
                     "    Eigen::Matrix<double, 3, 1> B;",
                     "    B << -0.38100038, 0.25400025, -0.88900089;",
                     "    Eigen::Matrix<double, 3, 1> C = {}(A);".format(func_info.eig_func_name),
                     "    return ((B - C).norm() < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_8(self):
        # sequence
        la_str = """`n(v)` = (∑_(i for i ∈ `N₁(v)`) α_i n(T_i))/||∑_(i for i ∈ `N₁(v)`) α_i n(T_i)||
        where
        T_i: ℝ^(3×3)
        α_i: ℝ
        `N₁(v)`: {ℤ}
        n: ℝ^(3×3) -> ℝ^3"""
        func_info = self.gen_func_info(la_str)
        T = np.array([[[1, 2, 3], [4, 5, 6], [7, 8, 9]], [[10, 21, 3], [4, 5, 6], [7, 8, 9]]])
        α = np.array([10, 2])
        N1 = [1, 2]
        n = lambda p: p[0]
        B = np.array([0.38601376, 0.79776177, 0.46321651])
        self.assertDMatrixApproximateEqual(func_info.numpy_func(T, α, N1, n), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::vector<Eigen::Matrix<double, 3, 3>> T;",
                     "    Eigen::Matrix<double, 3, 3> A1;",
                     "    A1 << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    Eigen::Matrix<double, 3, 3> A2;",
                     "    A2 << 10, 21, 3, 4, 5, 6, 7, 8, 9;",
                     "    T.push_back(A1);",
                     "    T.push_back(A2);",
                     "    std::vector<double> α;",
                     "    α.push_back(10);",
                     "    α.push_back(2);",
                     "    std::set<std::tuple< int > > N1;",
                     "    N1.insert(1);",
                     "    N1.insert(2);",
                     "    std::function<Eigen::Matrix<double, 3, 1>(Eigen::Matrix<double, 3, 3>)> n;",
                     "    n = [](Eigen::Matrix<double, 3, 3> t)->Eigen::Matrix<double, 3, 1>{",
                     "        return t.row(0);",
                     "    };",
                     "    Eigen::Matrix<double, 3, 1> B;",
                     "    B << 0.38601376, 0.79776177, 0.46321651;",
                     "    Eigen::Matrix<double, 3, 1> C = {}(T, α, N1, n);".format(func_info.eig_func_name),
                     "    return ((B - C).norm() < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_9(self):
        # sequence
        la_str = """from trigonometry: cos
        b = ∑_i cos(θ)²((p_i - q_i)⋅n_i +((p_i+q_i)×n_i)⋅ã+n_i⋅t̃)²
        where
        θ: ℝ: angle of rotation
        p_i: ℝ^3
        q_i: ℝ^3
        n_i: ℝ^3
        ã: ℝ^3
        t̃: ℝ^3"""
        func_info = self.gen_func_info(la_str)
        θ = 0
        p = np.array([[1, 2, 3], [8, 3, 6]])
        q = np.array([[2, 2, 5], [8, 3, 6]])
        n = np.array([[7, 2, 4], [8, 3, 6]])
        ã = np.array([4, 2, 3])
        t̃ = np.array([1, 10, 3])
        self.assertEqual(func_info.numpy_func(θ, p, q, n, ã, t̃), 5252)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::vector<Eigen::Matrix<double, 3, 1>> p;",
                     "    Eigen::Matrix<double, 3, 1> p1;",
                     "    p1 << 1, 2, 3;",
                     "    Eigen::Matrix<double, 3, 1> p2;",
                     "    p2 << 8, 3, 6;",
                     "    p.push_back(p1);",
                     "    p.push_back(p2);",
                     "    std::vector<Eigen::Matrix<double, 3, 1>> q;",
                     "    Eigen::Matrix<double, 3, 1> q1;",
                     "    q1 << 2, 2, 5;",
                     "    Eigen::Matrix<double, 3, 1> q2;",
                     "    q2 << 8, 3, 6;",
                     "    q.push_back(q1);",
                     "    q.push_back(q2);",
                     "    std::vector<Eigen::Matrix<double, 3, 1>> n;",
                     "    Eigen::Matrix<double, 3, 1> n1;",
                     "    n1 << 7, 2, 4;",
                     "    Eigen::Matrix<double, 3, 1> n2;",
                     "    n2 << 8, 3, 6;",
                     "    n.push_back(n1);",
                     "    n.push_back(n2);",
                     "    Eigen::Matrix<double, 3, 1> a;",
                     "    a << 4, 2, 3;",
                     "    Eigen::Matrix<double, 3, 1> t;",
                     "    t << 1, 10, 3;",
                     "    double C = {}(0, p, q, n, a, t);".format(func_info.eig_func_name),
                     "    return ((5252 - C) < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_10(self):
        # sequence
        la_str = """`T₁` = 1/sqrt(2)U[0 0 0
                  0 0 -1
                  0 1 0]Vᵀ
        where
        U: ℝ^(3×3)
        V: ℝ^(3×3)"""
        func_info = self.gen_func_info(la_str)
        U = np.array([[1, 2, 3], [2, 3, 5], [8, 10, 6]])
        V = np.array([[10, 2, 2], [1, 3, 1], [7, 4, 8]])
        B = np.array([[1.41421356, 4.94974747, -2.82842712], [2.82842712, 8.48528137, -2.82842712], [-5.65685425, 5.65685425, -39.59797975]])
        self.assertDMatrixApproximateEqual(func_info.numpy_func(U, V), B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> U;",
                     "    U << 1, 2, 3, 2, 3, 5, 8, 10, 6;",
                     "    Eigen::Matrix<double, 3, 3> V;",
                     "    V << 10, 2, 2, 1, 3, 1, 7, 4, 8;",
                     "    Eigen::Matrix<double, 3, 3> B;",
                     "    B << 1.41421356, 4.94974747, -2.82842712, 2.82842712, 8.48528137, -2.82842712, -5.65685425, 5.65685425, -39.59797975;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(U, V);".format(func_info.eig_func_name),
                     "    return ((B - C).norm() < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_11(self):
        # sequence
        la_str = """r̄ = v̄×ō
        s̄ = ō×ū
        n̄ = ū×v̄
        `k_r` = r̄⋅(`C̄ₐ`-V̄)
        `k_s` = s̄⋅(`C̄ₐ`-V̄)
        `k_n` = n̄⋅(`C̄ₐ`-V̄)
        `x(θ,v)` =  (r̄⋅`D_A`(θ, v)+`k_r`δ(θ, v))/(n̄⋅`D_A`(θ, v)+`k_n`δ(θ, v))
        `y(θ,v)` =  (s̄⋅`D_A`(θ, v)+`k_s`δ(θ, v))/(n̄⋅`D_A`(θ, v)+`k_n`δ(θ, v))
        where
        v̄: ℝ^3
        ō: ℝ^3
        ū: ℝ^3
        V̄: ℝ^3
        `C̄ₐ`: ℝ^3
        θ: ℝ
        v: ℝ
        `D_A`: ℝ,ℝ->ℝ^3
        δ: ℝ,ℝ->ℝ """
        func_info = self.gen_func_info(la_str)
        v̄ = np.array([1, 2, 3])
        ō = np.array([2, 2, 4])
        ū = np.array([4, 1, 2])
        V̄ = np.array([5, 2, 4])
        C_combining_macron_ₐ = np.array([1, 3, 2])
        θ = 2
        v = 3
        def D_A(p0, p1):
            return np.array([p0, p1, p0 + p1])
        def δ(p0, p1):
            return p0 + p1
        self.assertTrue(np.isclose(func_info.numpy_func(v̄, ō, ū, V̄, C_combining_macron_ₐ, θ, v, D_A, δ), -1.2989690721))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> v;",
                     "    v << 1, 2, 3;",
                     "    Eigen::Matrix<double, 3, 1> o;",
                     "    o << 2, 2, 4;",
                     "    Eigen::Matrix<double, 3, 1> u;",
                     "    u << 4, 1, 2;",
                     "    Eigen::Matrix<double, 3, 1> V;",
                     "    V << 5, 2, 4;",
                     "    Eigen::Matrix<double, 3, 1> C;",
                     "    C << 1, 3, 2;",
                     "    std::function<Eigen::Matrix<double, 3, 1>(double, double)> f1;"
                     "    f1 = [](double p1, double p2)->Eigen::Matrix<double, 3, 1>{",
                     "        Eigen::Matrix<double, 3, 1> tmp;",
                     "        tmp << p1, p2, p2+p1;",
                     "        return tmp;"
                     "    };",
                     "    std::function<double(double, double)> f2;"
                     "    f2 = [](double p1, double p2)->double{",
                     "        return p1 + p2;"
                     "    };",
                     "    double B = {}(v, o, u, V, C, 2, 3, f1, f2);".format(func_info.eig_func_name),
                     "    return (abs(-1.2989690721 - B) < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_12(self):
        # sequence
        la_str = """E = 1/`σ_N`²`E_I` + ∑_(j for j>1) α_j²/`σ_S`_j² + ∑_(j for j>1) β_j²/`σ_T`_j²  + ∑_j (ρ_j-ρ̄_j)²/`σ_ρ`_j²
        where
        `σ_N`: ℝ
        `E_I`: ℝ
        α_i : ℝ
        β_i : ℝ
        `σ_S`_i: ℝ
        `σ_T`_i: ℝ
        ρ_i: ℝ
        ρ̄_i: ℝ
        `σ_ρ`_i: ℝ
        ā_i: ℝ """
        func_info = self.gen_func_info(la_str)
        σ_N = 3
        E_I = 4
        α = np.array([1, 2, 3])
        β = np.array([1, 3, 2])
        σ_S = np.array([2, 2, 7])
        σ_T = np.array([5, 7, 3])
        ρ = np.array([10, 2, 3])
        ρ̄ = np.array([5, 2, 7])
        σ_ρ = np.array([2, 3, 5])
        ā = np.array([3, 1, 8])
        self.assertTrue(np.isclose(func_info.numpy_func(σ_N, E_I, α, β, σ_S, σ_T, ρ, ρ̄, σ_ρ, ā), 9.146235827664398))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::vector<double> α = {1, 2, 3};",
                     "    std::vector<double> β = {1, 3, 2};",
                     "    std::vector<double> σ_S = {2, 2, 7};",
                     "    std::vector<double> σ_T = {5, 7, 3};",
                     "    std::vector<double> ρ = {10, 2, 3};",
                     "    std::vector<double> ρ̄ = {5, 2, 7};",
                     "    std::vector<double> σ_ρ = {2, 3, 5};",
                     "    std::vector<double> ā = {3, 1, 8};",
                     "    double C = {}(3, 4, α, β, σ_S, σ_T, ρ, ρ̄, σ_ρ, ā);".format(func_info.eig_func_name),
                     "    return (abs(9.146235827664398 - C) < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())
