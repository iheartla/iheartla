#pragma once

#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <map>
#include "Connectivity.h"

namespace iheartmesh {

typedef std::tuple<const std::vector<int>&,const std::vector<int>&,const std::vector<int>&,const std::vector<int>&> CellSetTuple;
typedef std::tuple<const Eigen::SparseMatrix<int>&, const Eigen::SparseMatrix<int>&, const Eigen::SparseMatrix<int>&> CellMatTuple;
class CellMesh {
public:
    CellMesh(){};
    CellMesh(const Eigen::SparseMatrix<int>& bm1, const Eigen::SparseMatrix<int>& bm2, const Eigen::SparseMatrix<int>& bm3){
        this->bm1 = bm1;
        this->pos_bm1 = this->bm1.cwiseAbs();
        this->bm2 = bm2;
        this->pos_bm2 = this->bm2.cwiseAbs();
        this->bm3 = bm3;
        this->pos_bm3 = this->bm3.cwiseAbs();
        this->Vi.resize(this->bm1.rows());
        for (int i = 0; i < this->bm1.rows(); ++i){
            this->Vi[i] = i;
        }
        this->Ei.resize(this->bm1.cols());
        for (int i = 0; i < this->bm1.cols(); ++i){ 
            this->Ei[i] = i;
        }
        this->Fi.resize(this->bm2.cols());
        for (int i = 0; i < this->bm2.cols(); ++i){ 
            this->Fi[i] = i;
        }
        this->Ti.resize(this->bm3.cols());
        for (int i = 0; i < this->bm3.cols(); ++i){ 
            this->Ti[i] = i;
        }
    }

    // API
    int n_vertices() const{
        return this->bm1.rows();
    }  
    int n_edges() const{
        return this->bm1.cols();
    }
    int n_faces() const{
        return this->bm2.cols();
    }
    int n_tets() const{
        return this->bm3.cols();
    }

    CellSetTuple ElementSets() const{
        return std::tie(this->Vi, this->Ei, this->Fi, this->Ti);
    }
    CellMatTuple BoundaryMatrices() const{
        return std::tie(this->bm1, this->bm2, this->bm3);
    }
    CellMatTuple UnsignedBoundaryMatrices() const{
        return std::tie(this->pos_bm1, this->pos_bm2, this->pos_bm3);
    }

    // 
private:
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
