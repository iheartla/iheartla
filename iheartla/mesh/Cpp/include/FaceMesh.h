#pragma once

#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <map>
#include "Connectivity.h"

namespace iheartmesh {

class FaceMesh {
public:
    FaceMesh();
    FaceMesh(Eigen::SparseMatrix<int>& bm1, Eigen::SparseMatrix<int>& bm2);

    int n_edges() const;
    int n_vertices() const;
    int n_faces() const;

    // API
    std::tuple<std::vector<int>, std::vector<int>, std::vector<int>> ElementSets() const;
    std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > BoundaryMatrices() const;
    std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > UnsignedBoundaryMatrices() const;

    SparseMatrix<int> vertices_to_vector(const std::vector<int>& vset) const;
    SparseMatrix<int> edges_to_vector(const std::vector<int>& eset) const;
    SparseMatrix<int> faces_to_vector(const std::vector<int>& fset) const;
    // 
// private:
    std::vector<int> Vi;
    std::vector<int> Ei; 
    std::vector<int> Fi; 
    Eigen::SparseMatrix<int> bm1; // |V|x|E|
    Eigen::SparseMatrix<int> pos_bm1; // |V|x|E|
    Eigen::SparseMatrix<int> bm2; // |E|x|F|
    Eigen::SparseMatrix<int> pos_bm2; // |E|x|F| 
};


}
