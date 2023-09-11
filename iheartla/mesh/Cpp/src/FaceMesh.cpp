#include <stdio.h>
#include <iostream>
#include <vector>
#include <algorithm> 
#include "dec_util.h"
#include "FaceMesh.h"

namespace iheartmesh {

FaceMesh::FaceMesh(){
    
} 
FaceMesh::FaceMesh(const Eigen::SparseMatrix<int>& bm1, const Eigen::SparseMatrix<int>& bm2){
    this->bm1 = bm1;
    this->pos_bm1 = this->bm1.cwiseAbs();
    this->bm2 = bm2;
    this->pos_bm2 = this->bm2.cwiseAbs();
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
} 

int FaceMesh::n_edges() const{
    return this->bm1.cols();
}
int FaceMesh::n_vertices() const{
    return this->bm1.rows();
} 
int FaceMesh::n_faces() const{
    return this->bm2.cols();
} 

SparseMatrix<int> FaceMesh::vertices_to_vector(const std::vector<int>& vset) const{
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
SparseMatrix<int> FaceMesh::edges_to_vector(const std::vector<int>& eset) const{
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
SparseMatrix<int> FaceMesh::faces_to_vector(const std::vector<int>& fset) const{
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

std::tuple<std::vector<int>, std::vector<int>, std::vector<int>> FaceMesh::ElementSets() const{
    return std::tuple<std::vector<int>, std::vector<int>, std::vector<int>>(this->Vi, this->Ei, this->Fi);
}

std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > FaceMesh::BoundaryMatrices() const{
    return std::tuple< Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> >(this->bm1, this->bm2);
}

std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > FaceMesh::UnsignedBoundaryMatrices() const{
    return std::tuple< Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> >(this->pos_bm1, this->pos_bm2);
}

}
