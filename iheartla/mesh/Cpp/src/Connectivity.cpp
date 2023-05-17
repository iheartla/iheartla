#include <stdio.h>
#include <iostream>
#include <vector>
#include <algorithm> 
#include "dec_util.h"
#include "Connectivity.h"

Connectivity::Connectivity(){

} 

std::vector<int> Connectivity::nonzeros(Eigen::SparseMatrix<int> & target)const{
    return nonzeros(target, true);
}

std::vector<int> Connectivity::nonzeros(Eigen::SparseMatrix<int> & target, bool is_row)const{
    std::vector<int> result;
    result.reserve(target.rows());  // reserve
    for (int k=0; k<target.outerSize(); ++k){
      for (SparseMatrix<int>::InnerIterator it(target,k); it; ++it) {
        if (is_row)
        {
            result.push_back(it.row());
        }
        else{
            result.push_back(it.col());
        }
      }
    } 
    return result;
}
std::vector<int> Connectivity::ValueSet(Eigen::SparseMatrix<int> &target, int value)const{
    // return row indices for specific value
    return ValueSet(target, value, true);
}
std::vector<int> Connectivity::ValueSet(Eigen::SparseMatrix<int> &target, int value, bool is_row)const{
    std::vector<int> result;
    for (int k=0; k<target.outerSize(); ++k){
      for (SparseMatrix<int>::InnerIterator it(target,k); it; ++it) {
        if (it.value() == value)
        {
            if (is_row)
            {
                result.push_back(it.row());
            }
            else{
                result.push_back(it.col());
            }
        }
      }
    } 
    return result;
} 


int Connectivity::n_edges() const{
    return this->E.rows();
}
int Connectivity::n_vertices() const{
    return this->num_v;
}
int Connectivity::n_faces() const{
    return this->Fi.size();
}
int Connectivity::n_tets() const{
    return this->T.rows();
}

SparseMatrix<int> Connectivity::vertices_to_vector(const std::vector<int>& vset) const{
    SparseMatrix<int> v(this->num_v, 1);
    // std::cout<<"this->num_v is:"<<this->num_v<<std::endl;
    std::vector<Eigen::Triplet<int> > tripletList; 
    tripletList.reserve(this->num_v);
    for (int idx : vset)
    {
        tripletList.push_back(Eigen::Triplet<int>(idx, 0, 1));
    }
    // std::cout<<"this->num_v:"<<this->num_v<<std::endl;
    // std::cout<<"vset size:"<<vset.size()<<std::endl;
    // std::cout<<"tripletList size:"<<tripletList.size()<<std::endl;
    v.setFromTriplets(tripletList.begin(), tripletList.end());
    return v;
}
SparseMatrix<int> Connectivity::edges_to_vector(const std::vector<int>& eset) const{
    SparseMatrix<int> e(this->E.rows(), 1);
    std::vector<Eigen::Triplet<int> > tripletList; 
    tripletList.reserve(this->E.rows());
    for (int idx : eset)
    {
        tripletList.push_back(Eigen::Triplet<int>(idx, 0, 1));
    }
    e.setFromTriplets(tripletList.begin(), tripletList.end());
    return e;
}
SparseMatrix<int> Connectivity::faces_to_vector(const std::vector<int>& fset) const{
    SparseMatrix<int> f(this->F.rows(), 1);
    std::vector<Eigen::Triplet<int> > tripletList; 
    tripletList.reserve(this->F.rows());
    for (int idx : fset)
    {
        tripletList.push_back(Eigen::Triplet<int>(idx, 0, 1));
    }
    f.setFromTriplets(tripletList.begin(), tripletList.end());
    return f;
}
SparseMatrix<int> Connectivity::tets_to_vector(const std::vector<int>& tset) const{
    SparseMatrix<int> t(this->T.rows(), 1);
    std::vector<Eigen::Triplet<int> > tripletList; 
    tripletList.reserve(this->T.rows());
    for (int idx : tset)
    {
        tripletList.push_back(Eigen::Triplet<int>(idx, 0, 1));
    }
    t.setFromTriplets(tripletList.begin(), tripletList.end());
    return t;
}

int Connectivity::get_edge_index(int i, int j, int &sign){
    if (i < j)
    {
        sign = 1;
        return this->map_e[std::make_tuple(i, j)];
    }
    sign = -1;
    return this->map_e[std::make_tuple(j, i)];
}
int Connectivity::get_edge_index(int i, int j){
    if (i < j)
    {
        return this->map_e[std::make_tuple(i, j)];
    }
    return this->map_e[std::make_tuple(j, i)];
} 
 