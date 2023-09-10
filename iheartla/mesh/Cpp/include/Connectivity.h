#pragma once

#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <map>

namespace iheartmesh {

using Eigen::MatrixXi;
using Eigen::VectorXi;
using Eigen::SparseMatrix;
typedef std::tuple<std::vector<int>, std::vector<int>, std::vector<int>, std::vector<int> > SetTuple;
typedef std::tuple<int, int, int> key_f;
typedef std::tuple<int, int> key_e;
typedef Eigen::Matrix< int, Eigen::Dynamic, 1> Vector;
typedef Eigen::Matrix< int, 1, Eigen::Dynamic> RowVector;
// typedef Eigen::Matrix< int, Eigen::Dynamic, Eigen::Dynamic> Matrix;
class Connectivity {
public:
    Connectivity();

    int get_edge_index(int i, int j); 
    int get_edge_index(int i, int j, int &sign);
    // 
// private:
    int num_v; 
    MatrixXi T;
    MatrixXi E;
    MatrixXi F;
    std::map<key_f, int> map_f; // tuple -> face index
    std::map<key_e, int> map_e; // tuple -> edge index
    Eigen::SparseMatrix<int> bm1; // |V|x|E|
    Eigen::SparseMatrix<int> bm2; // |E|x|F|
    Eigen::SparseMatrix<int> bm3; // |F|x|T|
};

}
