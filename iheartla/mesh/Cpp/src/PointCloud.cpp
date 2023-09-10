#include <stdio.h>
#include <iostream>
#include <vector>
#include <algorithm> 
#include "dec_util.h"
#include "PointCloud.h"

namespace iheartmesh {

std::vector<std::vector<size_t>> GetPointNeighbors(std::vector<Eigen::VectorXd>& P, int k){
    std::unique_ptr<PointCloudWrapper> impl;
    impl.reset(new PointCloudWrapper(P));
    std::vector<std::vector<size_t>> neighbors(P.size());
    for (int i = 0; i < P.size(); ++i)
    {
        neighbors[i] = impl->kNearestNeighbors(i, k);
        // std::cout<<"i: "<<i<<", neighbors: "<<neighbors[i].size()<<std::endl;
        // if (i == 0)
        // {
        //     for (int m = 0; m < neighbors[i].size(); ++m)
        //     {
        //         std::cout<<"v: "<<m<<", k neighbors: "<<neighbors[i][m]<<std::endl;
        //     }
        //     //
        //     std::cout<<"radius neighbors"<<std::endl;
        //     std::vector<size_t> nn = impl->radiusSearch(P[i]);
        //     for (int m = 0; m < nn.size(); ++m)
        //     {
        //         std::cout<<"v: "<<m<<", radius neighbors:"<<nn[m]<<std::endl;
        //     }
        // }
    }

    return neighbors;
}


std::vector<std::vector<size_t>> GetPointNeighbors(std::vector<Eigen::VectorXd>& P, double rad){
    std::unique_ptr<PointCloudWrapper> impl;
    impl.reset(new PointCloudWrapper(P));
    std::vector<std::vector<size_t>> neighbors(P.size());
    for (int i = 0; i < P.size(); ++i)
    {
        neighbors[i] = impl->radiusSearch(P[i], rad);
    }

    return neighbors;
}

PointCloud::PointCloud(){}

PointCloud::PointCloud(std::vector<Eigen::VectorXd>& P, std::vector<std::vector<size_t>> neighbors){
    this->num_v = P.size();
    int max_e = 0;
    for (int i = 0; i < neighbors.size(); ++i)
    {
        max_e += neighbors[i].size();
    }
    // std::cout<<"this->num_v num_v is:"<<this->num_v<<std::endl;
    this->E.resize(max_e, 2);
    int cnt = 0;
    for (int i = 0; i < P.size(); ++i)
    {
        for (int j = 0; j < neighbors[i].size(); ++j)
        { 
            this->E(cnt, 0) = i;
            this->E(cnt, 1) = neighbors[i][j]; 
            cnt++;
        }
        /* code */
    }
    // std::cout<<"this->E is:"<<this->E.rows()<<std::endl;
    this->E = preprocess_matrix(this->E);
    // std::cout<<"processed this->E:"<<this->E.rows()<<std::endl;
    for (int i = 0; i < this->E.rows(); ++i)
    {
        this->map_e.insert(std::pair<key_e, int>(std::make_tuple(this->E(i, 0), this->E(i, 1)), i));
        // std::cout<<"cur: "<<i<<", i: "<<E(i,0)<<", j:"<<E(i,1)<<std::endl;
    }
    // this->E.conservativeResize(cnt, 2); 
    //  
    // this->init_indices();
    this->build_boundary_mat1();
}

// void PointCloud::initialize(Eigen::MatrixXd &P, double distance){
// 	this->num_v = P.rows();
// 	Eigen::MatrixXd dis = Eigen::MatrixXd::Zero(P.rows(), P.rows());
// 	this->E.resize(2*P.rows(), 2);
// 	int cnt = 0;
// 	for (int i = 0; i < P.rows()-1; ++i)
// 	{
// 		for (int j = i+1; j < P.rows(); ++j)
// 		{
// 			dis(i, j) = (P.row(i)-P.row(j)).norm();
// 			if (dis(i, j) < distance)
// 			{
// 				/* code */
// 				this->E(cnt, 0) = i;
// 				this->E(cnt, 1) = j;
// 				this->map_e.insert(std::pair<key_e, int>(std::make_tuple(i, j), cnt));
// 				cnt++;
// 			}
// 		}
// 	}
// 	std::cout<<"max distance:"<<dis.rowwise().maxCoeff().maxCoeff()<<", min distance:"<<dis.rowwise().minCoeff().minCoeff()<<std::endl;
// 	std::cout<<"cnt:"<<cnt<<std::endl;
// 	this->E.conservativeResize(cnt, 2); 
// 	//
// 	this->init_indices();
// 	this->build_boundary_mat1();
// }

PointCloudWrapper::PointCloudWrapper(std::vector<Eigen::VectorXd>& P)
: data{P}, 
tree(3, data){
    tree.buildIndex();
}
PointCloudWrapper::~PointCloudWrapper(){}

std::vector<size_t> PointCloudWrapper::kNearest(Eigen::VectorXd query, size_t k) {
    if (k > data.points.size()) throw std::runtime_error("k is greater than number of points");
    std::vector<size_t> outInds(k);
    std::vector<double> outDistSq(k);
    tree.knnSearch(&query(0), k, &outInds[0], &outDistSq[0]);
    return outInds;
}

std::vector<size_t> PointCloudWrapper::kNearestNeighbors(size_t sourceInd, size_t k) {
    if ((k + 1) > data.points.size()) throw std::runtime_error("k+1 is greater than number of points");

    std::vector<size_t> outInds(k + 1);
    std::vector<double> outDistSq(k + 1);
    tree.knnSearch(&data.points[sourceInd](0), k + 1, &outInds[0], &outDistSq[0]);

    // remove source from list
    bool found = false;
    for (size_t i = 0; i < outInds.size(); i++) {
      if (outInds[i] == sourceInd) {
        outInds.erase(outInds.begin() + i);
        // outDistSq.erase(outDistSq.begin() + i);
        found = true;
        break;
      }
    }

    // if the source didn't appear, just remove the last point
    if (!found) {
      outInds.pop_back();
      outDistSq.pop_back();
    }

    return outInds;
}

std::vector<size_t> PointCloudWrapper::radiusSearch(Eigen::VectorXd query, double rad) {
    // nanoflann wants a SQUARED raidus
    double radSq = rad * rad;

    std::vector<std::pair<size_t, double>> outPairs;
    tree.radiusSearch(&query(0), radSq, outPairs, nanoflann::SearchParams());

    // copy in to an array off indices
    std::vector<size_t> outInds(outPairs.size());
    for (size_t i = 0; i < outInds.size(); i++) {
      outInds[i] = outPairs[i].first;
    }

    return outInds;
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
    // this->pos_bm1 = this->bm1.cwiseAbs();
    // std::cout<<"this->bm1:\n"<<this->bm1<<std::endl;
    // std::cout<<"this->pos_bm1:\n"<<this->pos_bm1<<std::endl;
}

}
