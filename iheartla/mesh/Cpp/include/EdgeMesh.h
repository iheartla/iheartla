#pragma once

#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <map>
#include "Connectivity.h"

namespace iheartmesh {

class EdgeMesh {
public:
    EdgeMesh(){};
    EdgeMesh(const Eigen::SparseMatrix<int>& bm1){
        this->bm1 = bm1;
        this->pos_bm1 = this->bm1.cwiseAbs();
        this->Vi.resize(this->bm1.rows());
        for (int i = 0; i < this->bm1.rows(); ++i){
            this->Vi[i] = i;
        }
        this->Ei.resize(this->bm1.cols());
        for (int i = 0; i < this->bm1.cols(); ++i){ 
            this->Ei[i] = i;
        }
    } 

    int n_edges() const{
        return this->bm1.cols();
    }
    int n_vertices() const{
        return this->bm1.rows();
    } 
    // API
    std::tuple<std::vector<int>, std::vector<int>> ElementSets() const{
        return std::tuple<std::vector<int>, std::vector<int>>(this->Vi, this->Ei);
    }
    Eigen::SparseMatrix<int> BoundaryMatrices() const{
        return this->bm1;
    }
    Eigen::SparseMatrix<int> UnsignedBoundaryMatrices() const{
        return this->pos_bm1;
    }

    // SparseMatrix<int> vertices_to_vector(const std::vector<int>& vset) const;
    // SparseMatrix<int> edges_to_vector(const std::vector<int>& eset) const;
    // 
private:
    std::vector<int> Vi;
    std::vector<int> Ei; 
    Eigen::SparseMatrix<int> bm1; // |V|x|E|
    Eigen::SparseMatrix<int> pos_bm1; // |V|x|E|
};


}
