#include <stdio.h>
#include <iostream>
#include <algorithm> 
#include <vector>
#include <algorithm> 
#include "dec_util.h"
#include "PolygonMesh.h"

PolygonMesh::PolygonMesh(){

}

PolygonMesh::PolygonMesh(std::vector<std::vector<int> > &T){
    this->initialize(T);
}

void PolygonMesh::initialize(std::vector<std::vector<int> > &T){
	// T is a list of faces
	this->Face.resize(T.size());
	int max_vertices = 0;
	this->max_degree = 0;
	for (int i = 0; i < T.size(); ++i)
	{
		std::vector<int> cur_f(T[i].begin(), T[i].end());
		std::sort(cur_f.begin(), cur_f.end());
		this->map_face[cur_f] = i;                // mapping, sorted indices
		this->Face[i] = permute_vector(T[i]);     // saved faces, permutated indices
		if (this->max_degree < T[i].size())
		{
			this->max_degree = T[i].size();
		}
		for (int j = 0; j < T[i].size(); ++j)
		{
			if (T[i][j] > max_vertices)
			{
				max_vertices = T[i][j];
			}
		}
	}
	this->num_v = max_vertices + 1;
	this->create_edges();
    this->init_indices();
    // boundary mat
    this->build_boundary_mat1();
    this->build_boundary_mat2();
}

void PolygonMesh::init_indices(){
    this->Vi.resize(this->num_v);
    for (int i = 0; i < this->num_v; ++i){
        this->Vi[i] = i;
    }
    this->Ei.resize(this->E.rows());
    for (int i = 0; i < this->E.rows(); ++i){ 
        this->Ei[i] = i;
    }
    this->Fi.resize(this->Face.size());
    for (int i = 0; i < this->Face.size(); ++i){
        this->Fi[i] = i;
    }
    std::cout<<"Total vertices:"<<this->num_v<<", edges:"<<this->E.rows()<<", faces:"<<this->Fi.size()<<", max degree:"<<this->max_degree<<std::endl;
}

void PolygonMesh::create_edges(){
    Matrix E((this->max_degree+1)*this->Face.size(), 2); // max edges
    int cnt = 0;
    for (int i=0; i<this->Face.size(); i++) {
    	for (int j = 0; j < this->Face[i].size(); ++j)
    	{
    		Vector v0(2); v0 << this->Face[i][j], this->Face[i][(j+1)%this->Face[i].size()];
        	E.row(cnt) = sort_vector(v0);
        	cnt++;
    	}
    }
    E.conservativeResize(cnt, 2); 
    // std::cout<<"before this->E:\n"<<E<<std::endl;
    this->E = remove_duplicate_rows(sort_matrix(E));    
    // std::cout<<"this->E:\n"<<this->E<<std::endl;
    // create the mapping
    for (int i=0; i<this->E.rows(); i++) {
        this->map_e.insert(std::pair<key_e, int>(std::make_tuple(this->E(i,0), this->E(i,1)), i));
    }
}

void PolygonMesh::build_boundary_mat2(){
    this->bm2.resize(this->E.rows(), this->Face.size());
    std::vector<Eigen::Triplet<int> > tripletList;
    tripletList.reserve(this->max_degree * this->Face.size());
    int sign = 1;
    // The faces of a triangle +(f0,f1,f2)
    for(int i=0; i<this->Face.size(); i++){
    	for (int j = 0; j < this->Face[i].size(); ++j)
    	{
    		// +(f0,f1)
    		int idx = get_edge_index(this->Face[i][j], this->Face[i][(j+1)%this->Face[i].size()], sign);
        	tripletList.push_back(Eigen::Triplet<int>(idx, i, sign));
    	}
    }
    this->bm2.setFromTriplets(tripletList.begin(), tripletList.end());
    this->pos_bm2 = this->bm2.cwiseAbs();
    // std::cout<<"this->bm2:\n"<<this->bm2<<std::endl;
    // std::cout<<"this->pos_bm2:\n"<<this->pos_bm2<<std::endl;
}
SparseMatrix<int> PolygonMesh::faces_to_vector(const std::vector<int>& fset) const{
    SparseMatrix<int> f(this->Face.size(), 1);
    std::vector<Eigen::Triplet<int> > tripletList; 
    tripletList.reserve(this->Face.size());
    for (int idx : fset)
    {
        tripletList.push_back(Eigen::Triplet<int>(idx, 0, 1));
    }
    f.setFromTriplets(tripletList.begin(), tripletList.end());
    return f;
}
void PolygonMesh::build_boundary_mat1(){
    this->bm1.resize(this->num_v, this->E.rows());
    std::vector<Eigen::Triplet<int> > tripletList;
    tripletList.reserve(2*this->E.rows());
    for(int i=0; i<this->E.rows(); i++){
        tripletList.push_back(Eigen::Triplet<int>(this->E(i,0), i, -1));
        tripletList.push_back(Eigen::Triplet<int>(this->E(i,1), i, 1));
    }
    this->bm1.setFromTriplets(tripletList.begin(), tripletList.end());
    this->pos_bm1 = this->bm1.cwiseAbs();
    // std::cout<<"this->bm1:\n"<<this->bm1<<std::endl;
    // std::cout<<"this->pos_bm1:\n"<<this->pos_bm1<<std::endl;
}
  
std::tuple<std::vector<int>, std::vector<int>, std::vector<int>> PolygonMesh::ElementSets() const{
    return std::tuple<std::vector<int>, std::vector<int>, std::vector<int>>(this->Vi, this->Ei, this->Fi);
}

std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > PolygonMesh::BoundaryMatrices() const{
    return std::tuple< Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> >(this->bm1, this->bm2);
}

std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > PolygonMesh::UnsignedBoundaryMatrices() const{
    return std::tuple< Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> >(this->pos_bm1, this->pos_bm2);
}