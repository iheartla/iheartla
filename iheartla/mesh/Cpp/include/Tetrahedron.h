#pragma once

#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <map>
#include "Connectivity.h"
#include "TriangleMesh.h"

namespace iheartmesh {

class Tetrahedron: public TriangleMesh {
public:
    Tetrahedron(const Eigen::MatrixXi &T);
    Tetrahedron();
    void initialize(Eigen::MatrixXi &T);
    void initialize(const MatrixXi &T);

    void create_faces();
    void build_boundary_mat3(); // T -> F, size: |F|x|T|, boundary of tets
    int get_face_index(int i, int j, int k, int &sign);
    int get_face_index(int i, int j, int k); 
    void init_mesh_indices();
    std::tuple<std::vector<int>, std::vector<int>, std::vector<int>, std::vector<int>> ElementSets() const;
    std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > BoundaryMatrices() const;
    std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > UnsignedBoundaryMatrices() const;
};

}
