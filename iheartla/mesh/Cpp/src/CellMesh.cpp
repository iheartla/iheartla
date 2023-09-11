#include <stdio.h>
#include <iostream>
#include <vector>
#include <algorithm> 
#include "dec_util.h"
#include "CellMesh.h"

namespace iheartmesh {

CellMesh::CellMesh(){
    
} 
CellMesh::CellMesh(const Eigen::SparseMatrix<int>& bm1, const Eigen::SparseMatrix<int>& bm2, const Eigen::SparseMatrix<int>& bm3){
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

int CellMesh::n_edges() const{
    return this->bm1.cols();
}
int CellMesh::n_vertices() const{
    return this->bm1.rows();
}  
int CellMesh::n_faces() const{
    return this->bm2.cols();
}
int CellMesh::n_tets() const{
    return this->bm3.cols();
}

SparseMatrix<int> CellMesh::vertices_to_vector(const std::vector<int>& vset) const{
    SparseMatrix<int> v(this->bm1.rows(), 1);
    std::vector<Eigen::Triplet<int> > tripletList; 
    tripletList.reserve(this->bm1.rows());
    for (int idx : vset)
    {
        tripletList.push_back(Eigen::Triplet<int>(idx, 0, 1));
    }
    v.setFromTriplets(tripletList.begin(), tripletList.end());
    return v;
}
SparseMatrix<int> CellMesh::edges_to_vector(const std::vector<int>& eset) const{
    SparseMatrix<int> e(this->bm1.cols(), 1);
    std::vector<Eigen::Triplet<int> > tripletList; 
    tripletList.reserve(this->bm1.cols());
    for (int idx : eset)
    {
        tripletList.push_back(Eigen::Triplet<int>(idx, 0, 1));
    }
    e.setFromTriplets(tripletList.begin(), tripletList.end());
    return e;
} 
SparseMatrix<int> CellMesh::faces_to_vector(const std::vector<int>& fset) const{
    SparseMatrix<int> f(this->bm2.cols(), 1);
    std::vector<Eigen::Triplet<int> > tripletList; 
    tripletList.reserve(this->bm2.cols());
    for (int idx : fset)
    {
        tripletList.push_back(Eigen::Triplet<int>(idx, 0, 1));
    }
    f.setFromTriplets(tripletList.begin(), tripletList.end());
    return f;
}
SparseMatrix<int> CellMesh::tets_to_vector(const std::vector<int>& tset) const{
    SparseMatrix<int> t(this->bm3.cols(), 1);
    std::vector<Eigen::Triplet<int> > tripletList; 
    tripletList.reserve(this->bm3.cols());
    for (int idx : tset)
    {
        tripletList.push_back(Eigen::Triplet<int>(idx, 0, 1));
    }
    t.setFromTriplets(tripletList.begin(), tripletList.end());
    return t;
}

std::tuple<std::vector<int>, std::vector<int>, std::vector<int>, std::vector<int>> CellMesh::ElementSets() const{
    return std::tuple<std::vector<int>, std::vector<int>, std::vector<int>, std::vector<int>>(this->Vi, this->Ei, this->Fi, this->Ti);
}

std::tuple< Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > CellMesh::BoundaryMatrices() const{
    return std::tuple< Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> >(this->bm1, this->bm2, this->bm3);
}

std::tuple< Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > CellMesh::UnsignedBoundaryMatrices() const{
    return std::tuple< Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> >(this->pos_bm1, this->pos_bm2, this->pos_bm3);
}

}
