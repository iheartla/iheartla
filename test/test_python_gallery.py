import sys
sys.path.append('./')
from test.base_python_test import *
import scipy
from scipy import sparse
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)


class TestGallery(BasePythonTest):
    def test_gallery_0(self):
        # sequence
        la_str = """sin, cos from trigonometry
        `x(θ, ϕ)` = [Rcos(θ)cos(ϕ)
                     Rsin(θ)cos(ϕ)
                     Rsin(ϕ)]
        where
        ϕ: ℝ : angle between 0 and 2π
        θ: ℝ : angle between -π/2 and π/2
        R: ℝ : the radius of the sphere"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[0], [0], [3]])
        self.assertDMatrixApproximateEqual(func_info.numpy_func(np.pi/2, np.pi/2, 3).xθ_comma_ϕ, A)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> A;",
                     "    A << 0, 0, 3;",
                     "    Eigen::Matrix<double, 3, 1> B = {}(M_PI/2, M_PI/2, 3).xθ_comma_ϕ;".format(func_info.eig_func_name),
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
        self.assertTrue(np.isclose(func_info.numpy_func(A, x0, b).ret, 6.76227768454))

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
        self.assertTrue(np.isclose(func_info.numpy_func(x, n̂ , p).ret, 0))

    def test_gallery_1_2(self):
        # sequence
        la_str = """min_(C ∈ ℝ^3) ∑_i ||x_i + (R_i - I_3)C ||²
        where
        x_i: ℝ^3
        R_i: ℝ^(3×3)"""
        func_info = self.gen_func_info(la_str)
        x = np.array([[1, 2, 3], [3, 6, 5]])
        R = np.array([[[1, 2, 3], [3, 6, 5], [6, 3, 2]], [[2, 2, 1], [2, 3, 5], [9, 3, 1]]])
        self.assertTrue(np.isclose(func_info.numpy_func(x, R).ret, 11.123203285420))

    def test_gallery_2(self):
        # sequence
        la_str = """y_i = (a_i)ᵀ x + w_i
        x̂ = (∑_i a_i(a_i)ᵀ)⁻¹ ∑_i y_i a_i
        where
        a_i: ℝ^n: the measurement vectors
        w_i: ℝ: measurement noise
        x: ℝ^n: measurement noise """
        func_info = self.gen_func_info(la_str)
        a = np.array([[10, 4], [8, 6]])
        w = np.array([3, 2])
        x = np.array([2, 3])
        b = np.array([2.35714286, 2.85714286])
        self.assertDMatrixApproximateEqual(func_info.numpy_func(a, w, x).x̂ , b)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::vector<Eigen::VectorXd > a;",
                     "    Eigen::VectorXd a1(2);",
                     "    a1 << 10, 4;",
                     "    Eigen::VectorXd a2(2);",
                     "    a2 << 8, 6;",
                     "    a.push_back(a1);",
                     "    a.push_back(a2);",
                     "    std::vector<double> w = {3, 2};",
                     "    Eigen::VectorXd x(2);",
                     "    x << 2, 3;",
                     "    Eigen::VectorXd B(2);",
                     "    B << 2.35714286, 2.85714286;",
                     "    Eigen::Matrix<double, 2, 1> C = {}(a, w, x).x̂ ;".format(func_info.eig_func_name),
                     "    return ((C - B).norm() < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

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
        self.assertDMatrixApproximateEqual(func_info.numpy_func(A, B, S).ret, b)
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
                     "    Eigen::Matrix<double, 4, 4> C = {}(A, B, S).ret;".format(func_info.eig_func_name),
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
        self.assertDMatrixApproximateEqual(func_info.numpy_func(P, B, C, L, L̃, U, Ũ).ret, R)
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
                     "    Eigen::Matrix<double, 4, 4> G = {}(P, B, C, L, L̃, U, Ũ).ret;".format(func_info.eig_func_name),
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
        self.assertDMatrixApproximateEqual(func_info.numpy_func(A).partial_differential_2I5_solidus_partial_differential_f2, B)
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
                     "    Eigen::Matrix<double, 9, 9> C = {}(A).partial_differential_²I₅_solidus_partial_differential_f²;".format(func_info.eig_func_name),
                     "    return ((2*B - C).norm() < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_6(self):
        # sequence
        la_str = """tr from linearalgebra
        `J₃` = [1_3,3]
        `k_angle(Dₘ)` = 3(sqrt(2)v)^(2/3)(7/4||`Dₘ`||_F^2-1/4tr(`J₃``Dₘ`ᵀ`Dₘ`))⁻¹
        where
        `Dₘ`: ℝ^(3×3)
        v: ℝ"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        v = 10
        self.assertTrue(np.isclose(func_info.numpy_func(A, v).k_angleDₘ, 0.06060140390))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> A;",
                     "    A << 1, 2, 3, 4, 5, 6, 7, 8, 9;",
                     "    double C = {}(A, 10).k_angleDₘ;".format(func_info.eig_func_name),
                     "    return (abs(0.06060140390 - C) < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_7(self):
        # sequence
        la_str = """`xᵢ` = T_*,1
        `xⱼ` = T_*,2
        `xₖ` = T_*,3
        `n(T)` = (`xⱼ`-`xᵢ`)×(`xₖ`-`xᵢ`)/||(`xⱼ`-`xᵢ`)×(`xₖ`-`xᵢ`)||
        where
        T: ℝ^(3×3)"""
        func_info = self.gen_func_info(la_str)
        A = np.array([[1, 2, 3], [3, 8, 6], [7, 8, 7]])
        B = np.array([-0.38100038, 0.25400025, -0.88900089])
        self.assertDMatrixApproximateEqual(func_info.numpy_func(A).nT, B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> A;",
                     "    A << 1, 2, 3, 3, 8, 6, 7, 8, 7;",
                     "    Eigen::Matrix<double, 3, 1> B;",
                     "    B << -0.38100038, 0.25400025, -0.88900089;",
                     "    Eigen::Matrix<double, 3, 1> C = {}(A).nT;".format(func_info.eig_func_name),
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
        self.assertDMatrixApproximateEqual(func_info.numpy_func(T, α, N1, n).nv, B)
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
                     "    std::set<int > N1;",
                     "    N1.insert(1);",
                     "    N1.insert(2);",
                     "    std::function<Eigen::Matrix<double, 3, 1>(Eigen::Matrix<double, 3, 3>)> n;",
                     "    n = [](Eigen::Matrix<double, 3, 3> t)->Eigen::Matrix<double, 3, 1>{",
                     "        return t.row(0);",
                     "    };",
                     "    Eigen::Matrix<double, 3, 1> B;",
                     "    B << 0.38601376, 0.79776177, 0.46321651;",
                     "    Eigen::Matrix<double, 3, 1> C = {}(T, α, N1, n).nv;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_9(self):
        # sequence
        la_str = """cos from trigonometry
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
        self.assertEqual(func_info.numpy_func(θ, p, q, n, ã, t̃).b, 5252)
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
                     "    double C = {}(0, p, q, n, a, t).b;".format(func_info.eig_func_name),
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
        self.assertDMatrixApproximateEqual(func_info.numpy_func(U, V).T1, B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> U;",
                     "    U << 1, 2, 3, 2, 3, 5, 8, 10, 6;",
                     "    Eigen::Matrix<double, 3, 3> V;",
                     "    V << 10, 2, 2, 1, 3, 1, 7, 4, 8;",
                     "    Eigen::Matrix<double, 3, 3> B;",
                     "    B << 1.41421356, 4.94974747, -2.82842712, 2.82842712, 8.48528137, -2.82842712, -5.65685425, 5.65685425, -39.59797975;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(U, V).T₁;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_11(self):
        # sequence
        la_str = """r̄ = v̄×ō
        s̄ = ō×ū
        n̄ = ū×v̄
        `kᵣ` = r̄⋅(`C̄ₐ`-V̄)
        `kₛ` = s̄⋅(`C̄ₐ`-V̄)
        `kₙ` = n̄⋅(`C̄ₐ`-V̄)
        `x(θ,v)` =  (r̄⋅`D_A`(θ, v)+`kᵣ`delta(θ, v))/(n̄⋅`D_A`(θ, v)+`kₙ`delta(θ, v))
        `y(θ,v)` =  (s̄⋅`D_A`(θ, v)+`kₛ`delta(θ, v))/(n̄⋅`D_A`(θ, v)+`kₙ`delta(θ, v))
        where
        v̄: ℝ^3
        ō: ℝ^3
        ū: ℝ^3
        V̄: ℝ^3
        `C̄ₐ`: ℝ^3
        θ: ℝ
        v: ℝ
        `D_A`: ℝ,ℝ->ℝ^3
        `delta`: ℝ,ℝ->ℝ """
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
        self.assertTrue(np.isclose(func_info.numpy_func(v̄, ō, ū, V̄, C_combining_macron_ₐ, θ, v, D_A, δ).yθ_comma_v, -1.2989690721))
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
                     "    double B = {}(v, o, u, V, C, 2, 3, f1, f2).yθ_comma_v;".format(func_info.eig_func_name),
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
        self.assertTrue(np.isclose(func_info.numpy_func(σ_N, E_I, α, β, σ_S, σ_T, ρ, ρ̄, σ_ρ, ā).E, 9.146235827664398))
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
                     "    double C = {}(3, 4, α, β, σ_S, σ_T, ρ, ρ̄, σ_ρ, ā).E;".format(func_info.eig_func_name),
                     "    return (abs(9.146235827664398 - C) < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_13(self):
        # sequence
        la_str = """`C(x,y)` = (∑_n ∑_i c_n,i w_n,i R̂_n) / (∑_n ∑_i w_n,i R̂_n)
        where
        c ∈ ℝ^(f×s): the value of the Bayer pixel
        w ∈ ℝ^(f×s): the local sample weight
        R̂ ∈ ℝ^f: the local robustness"""
        func_info = self.gen_func_info(la_str)
        c = np.array([[1, 2], [3, 6]])
        w = np.array([[2, 2], [2, 4]])
        R̂ = np.array([2, 4])
        self.assertTrue(np.isclose(func_info.numpy_func(c, w, R̂).Cx_comma_y, 4.125))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 2, 2> c;",
                     "    c << 1, 2, 3, 6;",
                     "    Eigen::Matrix<double, 2, 2> w;",
                     "    w << 2, 2, 2, 4;",
                     "    Eigen::Matrix<double, 2, 1> R;",
                     "    R << 2, 4;",
                     "    double C = {}(c, w, R).Cx_comma_y;".format(func_info.eig_func_name),
                     "    return (abs(4.125 - C) < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_14(self):
        # sequence
        la_str = """Ω = [`e₁` `e₂`][`k₁`   0
                 0    `k₂`] [`e₁`ᵀ
			                 `e₂`ᵀ]
        where
        `k₁`: ℝ  : control the desired kernel variance in either edge or orthogonal direction
        `k₂`: ℝ  : control the desired kernel variance in either edge or orthogonal direction
        `e₁`: ℝ ^ 3: orthogonal direction vectors
        `e₂`: ℝ ^ 3: orthogonal direction vectors"""
        func_info = self.gen_func_info(la_str)
        k1 = 2
        k2 = 3
        e1 = np.array([4, 2, 3])
        e2 = np.array([1, 5, 2])
        B = np.array([[35, 31, 30], [31, 83, 42], [30, 42, 30]])
        self.assertDMatrixApproximateEqual(func_info.numpy_func(k1, k2, e1, e2).Ω, B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 1> e1;",
                     "    e1 << 4, 2, 3;",
                     "    Eigen::Matrix<double, 3, 1> e2;",
                     "    e2 << 1, 5, 2;",
                     "    Eigen::Matrix<double, 3, 3> B;",
                     "    B << 35, 31, 30, 31, 83, 42, 30, 42, 30;",
                     "    Eigen::Matrix<double, 3, 3> C = {}(2, 3, e1, e2).Ω;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_15(self):
        # sequence
        la_str = """`G_σ(s_i^k)` = ∑_j l_j exp(-dist(`bᵢ`, b_j)/(2σ²))(s_j)^k
        where
        l_j: ℝ : the length of bj
        dist: ℝ^n, ℝ^n -> ℝ : measures the geodesic distance between the centers of bi and bj along the boundary
        σ: ℝ
        `bᵢ`: ℝ^n
        b_j: ℝ^n
        s_j: ℝ : unit direction vector of bi
        k: ℝ : iteration number"""
        func_info = self.gen_func_info(la_str)
        l = np.array([1, 4, 6])
        def dist(p0, p1):
            return p0[0] + p1[0]
        σ = 2
        b_i = np.array([3, 2, 1])
        b = np.array([[10, 5, 2], [2, 4, 2], [3, 8, 5]])
        s = np.array([9, 9, 8])
        k = 4
        self.assertTrue(np.isclose(func_info.numpy_func(l, dist, σ, b_i, b, s, k).G_σs_i_circumflex_accent_k, 26948.21883123))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::vector<double> l = {1, 4, 6};",
                     "    double σ = 2;",
                     "    std::vector<double> s = {9, 9, 8};",
                     "    std::function<double(Eigen::VectorXd, Eigen::VectorXd)> dist;"
                     "    dist = [](Eigen::VectorXd p1, Eigen::VectorXd p2)->double{",
                     "        return p1(0) + p2(0);"
                     "    };",
                     "    Eigen::VectorXd b_i(3);",
                     "    b_i << 3, 2, 1;",
                     "    std::vector<Eigen::VectorXd> b;",
                     "    Eigen::VectorXd n1(3);",
                     "    n1 << 10, 5, 2;",
                     "    Eigen::VectorXd n2(3);",
                     "    n2 << 2, 4, 2;",
                     "    Eigen::VectorXd n3(3);",
                     "    n3 << 3, 8, 5;",
                     "    b.push_back(n1);",
                     "    b.push_back(n2);",
                     "    b.push_back(n3);",
                     "    double k = 4;",
                     "    double C = {}(l, dist, σ, b_i, b, s, k).G_σs_i_circumflex_accent_k;".format(func_info.eig_func_name),
                     "    return (abs(26948.21883123 - C) < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_16(self):
        # sequence
        la_str = """∑_i α_i + 1/M ∑_i ∑_j (f(X_i,j)/`p_c`(X_i,j) - (∑_k α_k p_k X_i,j)/`p_c`(X_i,j))
        where
        α: ℝ^m
        p: ℝ^m
        X: ℝ^(m×n)
        M: ℝ
        f: ℝ -> ℝ
        `p_c`: ℝ -> ℝ """
        func_info = self.gen_func_info(la_str)
        α = np.array([1, 2])
        p = np.array([4, 3])
        X = np.array([[2, 2], [2, 4]])
        M = 4
        def f(p0):
            return 2 * p0 - 1
        def p_c(p0):
            return p0 + 1
        self.assertTrue(np.isclose(func_info.numpy_func(α, p, X, M, f, p_c).ret, -2.9))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::vector<double> l = {1, 4, 6};",
                     "    double σ = 2;",
                     "    std::vector<double> s = {9, 9, 8};",
                     "    std::function<double(Eigen::VectorXd, Eigen::VectorXd)> dist;"
                     "    dist = [](Eigen::VectorXd p1, Eigen::VectorXd p2)->double{",
                     "        return p1(0) + p2(0);"
                     "    };",
                     "    Eigen::VectorXd α(2);",
                     "    α << 1, 2;",
                     "    Eigen::VectorXd p(2);",
                     "    p << 4, 3;",
                     "    Eigen::MatrixXd X(2,2);",
                     "    X << 2, 2, 2, 4;",
                     "    double M = 4;",
                     "    std::function<double(double)> f;",
                     "    f = [](double p1)->double{",
                     "        return p1*2-1;",
                     "    };",
                     "    std::function<double(double)> p_c;",
                     "    p_c = [](double p1)->double{",
                     "        return p1+1;",
                     "    };",
                     "    double C = {}(α, p, X, M, f, p_c).ret;".format(func_info.eig_func_name),
                     "    return (abs(-2.9 - C) < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_17(self):
        # sequence
        la_str = """v_i = ∑_j w_i,j M_j u_i
        where
        w: ℝ^(4×4)
        M_j: ℝ^(4×4)
        u_i: ℝ^4"""
        w = np.array([[1, 2, 3, 4], [3, 4, 5, 6], [5, 3, 5, 6], [9, 1, 3, 2]])
        M = np.array([[[2, 2, 1, 4], [2, 1, 1, 2], [4, 3, 5, 1], [1, 1, 2, 2]],
                      [[4, 2, 3, 4], [3, 1, 2, 1], [2, 3, 2, 2], [3, 4, 3, 4]],
                      [[1, 2, 2, 4], [2, 1, 5, 1], [1, 3, 2, 2], [3, 4, 9, 4]],
                      [[2, 2, 2, 4], [5, 1, 2, 1], [2, 3, 2, 1], [2, 4, 1, 4]]])
        u = np.array([[2, 1, 4, 3], [3, 1, 2, 6], [0, 0, 0, 0], [0, 0, 0, 0]])
        B = np.array([[266, 223, 205, 355], [659, 414, 417, 723], [0, 0, 0, 0], [0, 0, 0, 0]])
        func_info = self.gen_func_info(la_str)
        self.assertDMatrixApproximateEqual(func_info.numpy_func(w, M, u).v, B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 4, 4> w;",
                     "    w << 1, 2, 3, 4, 3, 4, 5, 6, 5, 3, 5, 6, 9, 1, 3, 2;",
                     "    std::vector<Eigen::Matrix<double, 4, 4>> M;",
                     "    Eigen::Matrix<double, 4, 4> M1;"
                     "    M1 << 2, 2, 1, 4, 2, 1, 1, 2, 4, 3, 5, 1, 1, 1, 2, 2;",
                     "    Eigen::Matrix<double, 4, 4> M2;"
                     "    M2 << 4, 2, 3, 4, 3, 1, 2, 1, 2, 3, 2, 2, 3, 4, 3, 4;",
                     "    Eigen::Matrix<double, 4, 4> M3;"
                     "    M3 << 1, 2, 2, 4, 2, 1, 5, 1, 1, 3, 2, 2, 3, 4, 9, 4;",
                     "    Eigen::Matrix<double, 4, 4> M4;"
                     "    M4 << 2, 2, 2, 4, 5, 1, 2, 1, 2, 3, 2, 1, 2, 4, 1, 4;",
                     "    M.push_back(M1);",
                     "    M.push_back(M2);",
                     "    M.push_back(M3);",
                     "    M.push_back(M4);",
                     "    std::vector<Eigen::Matrix<double, 4, 1>> u;"
                     "    Eigen::Matrix<double, 4, 1> u1;"
                     "    u1 << 2, 1, 4, 3;",
                     "    Eigen::Matrix<double, 4, 1> u2;"
                     "    u2 << 3, 1, 2, 6;",
                     "    Eigen::Matrix<double, 4, 1> u3;"
                     "    u3 << 0, 0, 0, 0;",
                     "    u.push_back(u1);",
                     "    u.push_back(u2);",
                     "    u.push_back(u3);",
                     "    u.push_back(u3);",
                     "    Eigen::Matrix<double, 4, 1> B1;"
                     "    B1 << 266, 223, 205, 355;",
                     "    Eigen::Matrix<double, 4, 1> B2;"
                     "    B2 << 659, 414, 417, 723;",
                     "    std::vector<Eigen::Matrix<double, 4, 1> > A = {}(w, M, u).v;".format(func_info.eig_func_name),
                     "    if((A[0] - B1).norm() < {} && (A[1] - B2).norm() < {}){{".format(self.eps, self.eps),
                     "        return true;",
                     "    }",
                     "    return false;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_18(self):
        # sequence
        la_str = """n = ∑_T A_T||M_T v_T - [0 -1
                        1  0] M_T u_T||²
        where
        v_i: ℝ^3
        u_i: ℝ^3
        M_i: ℝ^(2×3)
        A_i: ℝ"""
        v = np.array([[1, 2, 3], [3, 4, 5]])
        u = np.array([[2, 1, 3], [5, 8, 1]])
        M = np.array([[[2, 2, 1], [2, 1, 1]],
                      [[4, 2, 3], [3, 1, 2]]])
        A = np.array([2, 6])
        func_info = self.gen_func_info(la_str)
        self.assertTrue(np.isclose(func_info.numpy_func(v, u, M, A).n, 23722))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::vector<Eigen::Matrix<double, 3, 1> > v;",
                     "    Eigen::Matrix<double, 3, 1> v1;"
                     "    v1 << 1, 2, 3;",
                     "    Eigen::Matrix<double, 3, 1> v2;"
                     "    v2 << 3, 4, 5;",
                     "    v.push_back(v1);",
                     "    v.push_back(v2);",
                     "    std::vector<Eigen::Matrix<double, 3, 1> > u;",
                     "    Eigen::Matrix<double, 3, 1> u1;"
                     "    u1 << 2, 1, 3;",
                     "    Eigen::Matrix<double, 3, 1> u2;"
                     "    u2 << 5, 8, 1;",
                     "    u.push_back(u1);",
                     "    u.push_back(u2);",
                     "    std::vector<Eigen::Matrix<double, 2, 3> > M;",
                     "    Eigen::Matrix<double, 2, 3> M1;"
                     "    M1 << 2, 2, 1, 2, 1, 1;",
                     "    Eigen::Matrix<double, 2, 3> M2;"
                     "    M2 << 4, 2, 3, 3, 1, 2;",
                     "    M.push_back(M1);",
                     "    M.push_back(M2);",
                     "    std::vector<double> A = {2, 6};",
                     "    double C = {}(v, u, M, A).n;".format(func_info.eig_func_name),
                     "    return (abs(23722 - C) < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_19(self):
        # sequence
        la_str = """∑_i f_i²p_i - (∑_i f_i p_i)²
        where
        f_i: ℝ
        p_i: ℝ  """
        func_info = self.gen_func_info(la_str)
        f = np.array([1, 2, 3, 3, 4, 5])
        p = np.array([4, 2, 3, 3, 1, 2])
        self.assertTrue(np.isclose(func_info.numpy_func(f, p).ret, -1468))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::vector<double> f = {1, 2, 3, 3, 4, 5};",
                     "    std::vector<double> g = {4, 2, 3, 3, 1, 2};",
                     "    double C = {}(f, g).ret;".format(func_info.eig_func_name),
                     "    return (abs(-1468 - C) < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_20(self):
        # sequence
        la_str = """`I(X;Y)` = ∑_i ∑_j x_j p_i,j log_2(p_i,j/∑_k x_k p_i,k)
        where
        x: ℝ^n
        p: ℝ^(m×n)"""
        func_info = self.gen_func_info(la_str)
        x = np.array([1, 2, 3, 4])
        p = np.array([[1, 2, 3, 4], [3, 4, 5, 6], [5, 3, 5, 6], [9, 1, 3, 2]])
        self.assertTrue(np.isclose(func_info.numpy_func(x, p).IX_semicolon_Y, -509.52927877))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::VectorXd x(4);"
                     "    x << 1, 2, 3, 4;",
                     "    Eigen::MatrixXd p(4,4);",
                     "    p << 1, 2, 3, 4, 3, 4, 5, 6, 5, 3, 5, 6, 9, 1, 3, 2;",
                     "    double C = {}(x, p).IX_semicolon_Y;".format(func_info.eig_func_name),
                     "    return (abs(-509.52927877 - C) < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_21(self):
        # sequence
        la_str = """`L(x,v)` = xᵀWx + ∑_i v_i(x_i²-1)
        where
        x: ℝ^n
        W: ℝ^(n×n)
        v: ℝ^n"""
        func_info = self.gen_func_info(la_str)
        x = np.array([3, 1, 4, 2])
        W = np.array([[1, 2, 3, 4], [3, 4, 5, 6], [5, 3, 5, 6], [9, 1, 3, 2]])
        v = np.array([2, 1, 5, 7])
        self.assertTrue(np.isclose(func_info.numpy_func(x, W, v).Lx_comma_v, 520))
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::VectorXd x(4);"
                     "    x << 3, 1, 4, 2;",
                     "    Eigen::MatrixXd W(4,4);",
                     "    W << 1, 2, 3, 4, 3, 4, 5, 6, 5, 3, 5, 6, 9, 1, 3, 2;",
                     "    Eigen::VectorXd v(4);"
                     "    v << 2, 1, 5, 7;",
                     "    double C = {}(x, W, v).Lx_comma_v;".format(func_info.eig_func_name),
                     "    return (abs(520 - C) < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_gallery_22(self):
        # sequence
        # la_str = """given
        # p_i: ℝ^3: points on lines
        # d_i: ℝ^3: unit directions along lines
        # k_i = (p_i - (p_i⋅d_i)d_i)
        # a_i = (1,0,0) - d_i,1 d_i
        # b_i = (0,1,0) - d_i,2 d_i
        # c_i = (0,0,1) - d_i,3 d_i
        # M = [ ∑_i( a_i,1 - d_i,1 (d_i⋅a_i) )    ∑_i( a_i,2 - d_i,2 (d_i⋅a_i) )    ∑_i( a_i,3 - d_i,3 (d_i⋅a_i) )
        #       ∑_i( b_i,1 - d_i,1 (d_i⋅b_i) )    ∑_i( b_i,2 - d_i,2 (d_i⋅b_i) )    ∑_i( b_i,3 - d_i,3 (d_i⋅b_i) )
        #       ∑_i( c_i,1 - d_i,1 (d_i⋅c_i) )    ∑_i( c_i,2 - d_i,2 (d_i⋅c_i) )    ∑_i( c_i,3 - d_i,3 (d_i⋅c_i) ) ]
        # r = [ ∑_i( k_i⋅a_i )
        #       ∑_i( k_i⋅b_i )
        #       ∑_i( k_i⋅c_i ) ]
        # q = M^(-1) r"""
        la_str = """given
        p_i: ℝ^3: points on lines
        d_i: ℝ^3: unit directions along lines
        P_i = ( I_3 - d_i d_iᵀ )
        q = ( ∑_i P_iᵀP_i )⁻¹ ( ∑_i P_iᵀP_i p_i )"""
        func_info = self.gen_func_info(la_str)
        p = np.array([[1, 2, 3], [4, 7, 6], [5, 3, 2]])
        d = np.array([[2, 5, 4], [3, 5, 6], [9, 3, 2]])
        B = np.array([6.74855046, -17.5092147, 24.91003206])
        self.assertDMatrixApproximateEqual(func_info.numpy_func(p, d).q, B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::vector<Eigen::Matrix<double, 3, 1>> p;",
                     "    Eigen::Matrix<double, 3, 1> p1;",
                     "    p1 << 1, 2, 3;",
                     "    Eigen::Matrix<double, 3, 1> p2;",
                     "    p2 << 4, 7, 6;",
                     "    Eigen::Matrix<double, 3, 1> p3;",
                     "    p3 << 5, 3, 2;",
                     "    p.push_back(p1);",
                     "    p.push_back(p2);",
                     "    p.push_back(p3);",
                     "    std::vector<Eigen::Matrix<double, 3, 1>> d;",
                     "    Eigen::Matrix<double, 3, 1> d1;",
                     "    d1 << 2, 5, 4;",
                     "    Eigen::Matrix<double, 3, 1> d2;",
                     "    d2 << 3, 5, 6;",
                     "    Eigen::Matrix<double, 3, 1> d3;",
                     "    d3 << 9, 3, 2;",
                     "    d.push_back(d1);",
                     "    d.push_back(d2);",
                     "    d.push_back(d3);",
                     "    Eigen::Matrix<double, 3, 1> B;",
                     "    B << 6.74855046, -17.5092147, 24.91003206;",
                     "    Eigen::Matrix<double, 3, 1> C = {}(p, d).q;".format(func_info.eig_func_name),
                     "    return ((B - C).norm() < {});".format(self.eps),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_laplacian(self):
        # sparse matrix
        la_str = """cot from trigonometry
        L_i,j = { cot(α_ij) + cot(β_ij) if j ∈ N(i)
        L_i,i = -sum_(k for k != i) L_i,k
        where
        L: ℝ^(n×n)
        α: ℝ^(n×n)
        β: ℝ^(n×n)
        N: ℤ -> {ℤ}
        """
        func_info = self.gen_func_info(la_str)
        α = np.array([[1, 2, 3], [4, 7, 6], [5, 3, 2]])
        β = np.array([[2, 5, 4], [3, 5, 6], [9, 3, 2]])
        def N(p0):
            if p0 == 1:
                return [2]
            elif p0 == 2:
                return [1]
            return [1, 2]
        G = [(0, 1), (1, 0), (2, 0), (2, 1), (0, 0), (1, 1), (2, 2)]
        value = np.array([-0.75347046989, -6.151561396983, -2.506658326531, -14.0305051028690, 0.7534704698930, 6.15156139698, 16.5371634294])
        B = scipy.sparse.coo_matrix((value, np.asarray(G).T), shape=(3, 3))
        self.assertSMatrixEqual(func_info.numpy_func(α, β, N).L, B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 3, 3> α;",
                     "    α << 1, 2, 3, 4, 7, 6, 5, 3, 2;",
                     "    Eigen::Matrix<double, 3, 3> β;",
                     "    β << 2, 5, 4, 3, 5, 6, 9, 3, 2;",
                     "    std::function<std::set<int >(int)> N = [](int p)->std::set<int >{",
                     "        std::set<int > tmp;",
                     "        if(p == 1){",
                     "            tmp.insert(2);",
                     "        }",
                     "        else if(p == 2){",
                     "            tmp.insert(1);",
                     "        }",
                     "        else{",
                     "            tmp.insert(1);",
                     "            tmp.insert(2);",
                     "        }",
                     "        return tmp;",
                     "    };",
                     "    std::vector<Eigen::Triplet<double> > t1;",
                     "    t1.push_back(Eigen::Triplet<double>(0, 1, -0.75347046989));",
                     "    t1.push_back(Eigen::Triplet<double>(1, 0, -6.151561396983));",
                     "    t1.push_back(Eigen::Triplet<double>(2, 0, -2.506658326531));",
                     "    t1.push_back(Eigen::Triplet<double>(2, 1, -14.0305051028690));",
                     "    t1.push_back(Eigen::Triplet<double>(0, 0, 0.7534704698930));",
                     "    t1.push_back(Eigen::Triplet<double>(1, 1, 6.15156139698));",
                     "    t1.push_back(Eigen::Triplet<double>(2, 2, 16.5371634294));",
                     "    Eigen::SparseMatrix<double> A(3, 3);",
                     "    A.setFromTriplets(t1.begin(), t1.end());"
                     "    Eigen::SparseMatrix<double> B = {}(α, β, N).L;".format(func_info.eig_func_name),
                     "    return A.isApprox(B);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_laplacian_1(self):
        # sparse matrix
        la_str = """L_i,j = { w_i,j if (i,j) ∈ E
        L_i,i = -sum_(l for l != i) L_i,l
        where
        L: ℝ^(n×n)
        w: ℝ^(n×n): edge weight matrix
        E: {ℤ²} index: edges
        """
        func_info = self.gen_func_info(la_str)
        w = np.array([[-6, 9, -1, -11], [17, 14, 0, 0], [6, -2, 11, 0], [2, -9, -2, -9]])
        E = [(0, 1), (0, 2), (1, 2), (2, 0), (3, 0), (3, 1), (3, 2)]
        F = [(0, 1), (0, 2), (1, 2), (2, 0), (3, 0), (3, 1), (3, 2), (0, 0), (1, 1), (2, 2), (3, 3)]
        value = np.array([9, -1, 0, 6, 2, -9, -2, -8, 0, -6, 9])
        B = scipy.sparse.coo_matrix((value, np.asarray(F).T), shape=(4, 4), dtype=np.float64)
        self.assertSMatrixEqual(func_info.numpy_func(w, E).L, B)
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    Eigen::Matrix<double, 4, 4> w;",
                     "    w << -6, 9, -1, -11, 17, 14, 0, 0, 6, -2, 11, 0, 2, -9, -2, -9;",
                     "    std::set< std::tuple< int, int > > E;",
                     "    E.insert(std::make_tuple(0, 1));",
                     "    E.insert(std::make_tuple(0, 2));",
                     "    E.insert(std::make_tuple(1, 2));",
                     "    E.insert(std::make_tuple(2, 0));",
                     "    E.insert(std::make_tuple(3, 0));",
                     "    E.insert(std::make_tuple(3, 1));",
                     "    E.insert(std::make_tuple(3, 2));",
                     "    std::set< std::tuple< int, int > > F;",
                     "    F.insert(std::make_tuple(0, 1));",
                     "    F.insert(std::make_tuple(0, 2));",
                     "    F.insert(std::make_tuple(1, 2));",
                     "    F.insert(std::make_tuple(2, 0));",
                     "    F.insert(std::make_tuple(3, 0));",
                     "    F.insert(std::make_tuple(3, 1));",
                     "    F.insert(std::make_tuple(3, 2));",
                     "    F.insert(std::make_tuple(0, 0));",
                     "    F.insert(std::make_tuple(1, 1));",
                     "    F.insert(std::make_tuple(2, 2));",
                     "    F.insert(std::make_tuple(3, 3));",
                     "    std::vector<Eigen::Triplet<double> > t1;",
                     "    t1.push_back(Eigen::Triplet<double>(0, 1, 9));",
                     "    t1.push_back(Eigen::Triplet<double>(0, 2, -1));",
                     "    t1.push_back(Eigen::Triplet<double>(1, 2, 0));",
                     "    t1.push_back(Eigen::Triplet<double>(2, 0, 6));",
                     "    t1.push_back(Eigen::Triplet<double>(3, 0, 2));",
                     "    t1.push_back(Eigen::Triplet<double>(3, 1, -9));",
                     "    t1.push_back(Eigen::Triplet<double>(3, 2, -2));",
                     "    t1.push_back(Eigen::Triplet<double>(0, 0, -8));",
                     "    t1.push_back(Eigen::Triplet<double>(1, 1, 0));",
                     "    t1.push_back(Eigen::Triplet<double>(2, 2, -6));",
                     "    t1.push_back(Eigen::Triplet<double>(3, 3, 9));",
                     "    Eigen::SparseMatrix<double> A(4, 4);",
                     "    A.setFromTriplets(t1.begin(), t1.end());"
                     "    Eigen::SparseMatrix<double> B = {}(w, E).L;".format(func_info.eig_func_name),
                     "    return A.isApprox(B);",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_integral(self):
        la_str = """`H(p)` = 1/(2π)int_[0, 2π] `kₙ`(φ, p) ∂φ
        where 
        p: ℝ^3 : point on the surface
        `kₙ`: ℝ,ℝ^3->ℝ : normal curvature
        """
        func_info = self.gen_func_info(la_str)
        def kₙ(p0, p1):
            return p0 * p1[1]
        p = np.array([1, 2, 3])
        self.assertTrue(np.isclose(func_info.numpy_func(p, kₙ).Hp, 6.28318530))
