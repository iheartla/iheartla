#pragma once

#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <map>
#include "Connectivity.h"

namespace iheartmesh {

class CellMesh {
public:
    CellMesh();
    CellMesh(const Eigen::SparseMatrix<int>& bm1, const Eigen::SparseMatrix<int>& bm2, const Eigen::SparseMatrix<int>& bm3);

    // API
    int n_edges() const;
    int n_vertices() const;
    int n_faces() const;
    int n_tets() const;

    std::tuple<std::vector<int>, std::vector<int>, std::vector<int>, std::vector<int>> ElementSets() const;
    std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > BoundaryMatrices() const;
    std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > UnsignedBoundaryMatrices() const;

    SparseMatrix<int> vertices_to_vector(const std::vector<int>& vset) const;
    SparseMatrix<int> edges_to_vector(const std::vector<int>& eset) const;
    SparseMatrix<int> faces_to_vector(const std::vector<int>& fset) const;
    SparseMatrix<int> tets_to_vector(const std::vector<int>& tset) const; 
    // 
// private:
    std::vector<int> Vi;
    std::vector<int> Ei; 
    std::vector<int> Fi; 
    std::vector<int> Ti;
    Eigen::SparseMatrix<int> bm1; // |V|x|E|
    Eigen::SparseMatrix<int> pos_bm1; // |V|x|E|
    Eigen::SparseMatrix<int> bm2; // |E|x|F|
    Eigen::SparseMatrix<int> pos_bm2; // |E|x|F| 
    Eigen::SparseMatrix<int> bm3; // |F|x|T|
    Eigen::SparseMatrix<int> pos_bm3; // |F|x|T|
};


}
