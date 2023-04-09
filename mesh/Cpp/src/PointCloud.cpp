#include <stdio.h>
#include <iostream>
#include <vector>
#include <algorithm> 
#include "dec_util.h"
#include "PointCloud.h"

PointCloud::PointCloud(){

}

PointCloud::PointCloud(Eigen::MatrixXd &P, double distance){
    this->initialize(P, distance);
}

void PointCloud::initialize(Eigen::MatrixXd &P, double distance){
	this->num_v = P.rows();
	Eigen::MatrixXd dis = Eigen::MatrixXd::Zero(P.rows(), P.rows());
	this->E.resize(2*P.rows(), 2);
	int cnt = 0;
	for (int i = 0; i < P.rows()-1; ++i)
	{
		for (int j = i+1; j < P.rows(); ++j)
		{
			dis(i, j) = (P.row(i)-P.row(j)).norm();
			if (dis(i, j) < distance)
			{
				/* code */
				this->E(cnt, 0) = i;
				this->E(cnt, 1) = j;
				this->map_e.insert(std::pair<key_e, int>(std::make_tuple(i, j), cnt));
				cnt++;
			}
		}
	}
	std::cout<<"max distance:"<<dis.rowwise().maxCoeff().maxCoeff()<<", min distance:"<<dis.rowwise().minCoeff().minCoeff()<<std::endl;
	std::cout<<"cnt:"<<cnt<<std::endl;
	this->E.conservativeResize(cnt, 2); 
	//
	this->init_indices();
	this->build_boundary_mat1();
}

int PointCloud::get_edge_index(int i, int j){
    if (i < j)
    {
        return this->map_e[std::make_tuple(i, j)];
    }
    return this->map_e[std::make_tuple(j, i)];
} 

int PointCloud::get_edge_index(int i, int j, int &sign){
    if (i < j)
    {
        sign = 1;
        return this->map_e[std::make_tuple(i, j)];
    }
    sign = -1;
    return this->map_e[std::make_tuple(j, i)];
}

void PointCloud::init_indices(){
    this->Vi.resize(this->num_v);
    for (int i = 0; i < this->num_v; ++i){
        this->Vi[i] = i;
    }
    this->Ei.resize(this->E.rows());
    for (int i = 0; i < this->E.rows(); ++i){ 
        this->Ei[i] = i;
    }
    this->Fi.resize(this->F.rows());
    for (int i = 0; i < this->F.rows(); ++i){
        this->Fi[i] = i;
    }
}

void PointCloud::build_boundary_mat1(){
    this->bm1.resize(this->num_v, this->E.rows());
    std::vector<Eigen::Triplet<int> > tripletList;
    tripletList.reserve(2*this->E.rows());
    for(int i=0; i<this->E.rows(); i++){
        tripletList.push_back(Eigen::Triplet<int>(this->E(i,0), i, -1));
        tripletList.push_back(Eigen::Triplet<int>(this->E(i,1), i, 1));
    }
    this->bm1.setFromTriplets(tripletList.begin(), tripletList.end());
    this->pos_bm1 = this->bm1.cwiseAbs();
    std::cout<<"this->bm1:\n"<<this->bm1<<std::endl;
    // std::cout<<"this->pos_bm1:\n"<<this->pos_bm1<<std::endl;
}

std::tuple<std::vector<int>, std::vector<int>> PointCloud::MeshSets() const{
    return std::tuple<std::vector<int>, std::vector<int>>(this->Vi, this->Ei);
}

Eigen::SparseMatrix<int> PointCloud::BoundaryMatrices() const{
    return this->bm1;
}

Eigen::SparseMatrix<int> PointCloud::UnsignedBoundaryMatrices() const{
    return this->pos_bm1;
}