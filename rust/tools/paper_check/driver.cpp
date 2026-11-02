// Drive one I❤MESH example and print its values (to compare two generated heartlib.h).
#include <iostream>
#include <iomanip>
#include <cmath>
#include "TriangleMesh.h"
#include "Tetrahedron.h"
#include "FaceMesh.h"
#include "CellMesh.h"
#include "EdgeMesh.h"
#include "MeshHelper.h"
#include "heartlib.h"

static Eigen::Vector3d pos(int i) { return Eigen::Vector3d(std::sin(1.3 * i + 0.2), std::cos(0.7 * i + 1.1), std::sin(2.1 * i + 0.5)); }
static void show(const std::vector<int> &s) { std::cout << "{"; for (int v : s) std::cout << v << " "; std::cout << "}"; }
static void showm(const Eigen::MatrixXd &m) { for (int i = 0; i < m.size(); i++) std::cout << " " << std::setprecision(9) << m(i); std::cout << "\n"; }
static Eigen::MatrixXi octahedron() {
    Eigen::MatrixXi T(8, 3);
    T << 0, 1, 2, 0, 2, 3, 0, 3, 4, 0, 4, 1, 5, 2, 1, 5, 3, 2, 5, 4, 3, 5, 1, 4;
    return T;
}

int main() {
    std::cout << std::setprecision(9);
#if defined(EX_geodesic_distance)
    TriangleMesh tm(octahedron());
    FaceMesh M(tm.bm1, tm.bm2);
    std::vector<Eigen::Matrix<double, 3, 1>> x;
    for (int i = 0; i < 6; i++) x.push_back(pos(i));
    heartlib h(M, x);
    std::vector<double> d = {0, 0.4, 0.7, 1.1, 0.5, 2.0};
    for (int i = 0; i < 6; i++) for (int j = 0; j < 6; j++) for (int k = 0; k < 6; k++)
        if (i != j && j != k && i != k) std::cout << "UpdateStep " << i << j << k << " " << h.UpdateStep(i, j, k, d) << "\n";
    std::vector<std::vector<int>> U = {{0}, {1, 2}, {5}};
    std::cout << "GetNextLevel "; show(h.GetNextLevel(U)); std::cout << "\n";
    std::cout << "GetRangeLevel01 "; show(h.GetRangeLevel(U, 0, 1)); std::cout << "\n";
    std::cout << "GetRangeLevel12 "; show(h.GetRangeLevel(U, 1, 2)); std::cout << "\n";
    std::cout << "GetLevelSequence ";
    for (auto &s : h.GetLevelSequence({{0}})) show(s);
    std::cout << "\n";
#elif defined(EX_point_cloud)
    TriangleMesh tm(octahedron());
    EdgeMesh M(tm.bm1);
    std::vector<Eigen::Matrix<double, 3, 1>> x;
    for (int i = 0; i < 6; i++) x.push_back(pos(i));
    heartlib h(M, x);
    for (int i = 0; i < 6; i++) { std::cout << "Normal " << i; showm(h.Normal(i)); }
#elif defined(EX_mesh_parameterization)
    TriangleMesh tm(octahedron());
    FaceMesh M(tm.bm1, tm.bm2);
    std::vector<Eigen::Matrix<double, 3, 1>> xb;
    std::vector<Eigen::Matrix<double, 2, 1>> x;
    for (int i = 0; i < 6; i++) { xb.push_back(pos(i)); x.push_back(Eigen::Vector2d(pos(i)(0) + 0.05 * i, pos(i)(1) - 0.03 * i)); }
    auto psd = [](Eigen::MatrixXd m) -> Eigen::SparseMatrix<double> { return m.sparseView(); };
    heartlib h(M, xb, x, 1e-3, psd);
    std::cout << "e " << autodiff::val(h.e) << "\n";
    std::cout << "G"; showm(h.G);
    std::cout << "H"; showm(Eigen::MatrixXd(h.H));
#elif defined(EX_mesh_deformation)
    Eigen::MatrixXi T(2, 4);
    T << 0, 1, 2, 3, 1, 2, 3, 4;
    Tetrahedron tet(T);
    CellMesh M(tet.bm1, tet.bm2, tet.bm3);
    std::vector<Eigen::Matrix<double, 3, 1>> xb = {{0, 0, 0}, {1, 0, 0}, {0, 1, 0}, {0, 0, 1}, {1, 1, 1}}, x;
    for (int i = 0; i < 5; i++) x.push_back(xb[i] + 0.05 * pos(i));
    std::vector<int> bx = {0};
    std::vector<Eigen::Matrix<double, 3, 1>> bp = {{0.1, 0, 0}};
    auto psd = [](Eigen::MatrixXd m) -> Eigen::SparseMatrix<double> { return m.sparseView(); };
    heartlib h(M, xb, x, bx, bp, 2.0, 1e-3, psd);
    std::cout << "e " << autodiff::val(h.e) << "\n";
    std::cout << "G"; showm(h.G);
    std::cout << "H"; showm(Eigen::MatrixXd(h.H));
#endif
}
