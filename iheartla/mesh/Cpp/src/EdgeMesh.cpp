#include <stdio.h>
#include <iostream>
#include <vector>
#include <algorithm> 
#include "dec_util.h"
#include "EdgeMesh.h"

namespace iheartmesh {

EdgeMesh::EdgeMesh(){
    
} 
EdgeMesh::EdgeMesh(Eigen::SparseMatrix<int>& bm1){
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

int EdgeMesh::n_edges() const{
    return this->bm1.cols();
}
int EdgeMesh::n_vertices() const{
    return this->bm1.rows();
} 

SparseMatrix<int> EdgeMesh::vertices_to_vector(const std::vector<int>& vset) const{
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
SparseMatrix<int> EdgeMesh::edges_to_vector(const std::vector<int>& eset) const{
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

std::tuple<std::vector<int>, std::vector<int>> EdgeMesh::ElementSets() const{
    return std::tuple<std::vector<int>, std::vector<int>>(this->Vi, this->Ei);
}

Eigen::SparseMatrix<int> EdgeMesh::BoundaryMatrices() const{
    return this->bm1;
}

Eigen::SparseMatrix<int> EdgeMesh::UnsignedBoundaryMatrices() const{
    return this->pos_bm1;
}

}
