#pragma once

#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <map>
#include "Connectivity.h"

namespace iheartmesh {

class EdgeMesh {
public:
    EdgeMesh();
    EdgeMesh(const Eigen::SparseMatrix<int>& bm1);

    int n_edges() const;
    int n_vertices() const;

    // API
    std::tuple<std::vector<int>, std::vector<int>> ElementSets() const;
    Eigen::SparseMatrix<int> BoundaryMatrices() const;
    Eigen::SparseMatrix<int> UnsignedBoundaryMatrices() const;

    SparseMatrix<int> vertices_to_vector(const std::vector<int>& vset) const;
    SparseMatrix<int> edges_to_vector(const std::vector<int>& eset) const;
    // 
// private:
    std::vector<int> Vi;
    std::vector<int> Ei; 
    Eigen::SparseMatrix<int> bm1; // |V|x|E|
    Eigen::SparseMatrix<int> pos_bm1; // |V|x|E|
};


}
