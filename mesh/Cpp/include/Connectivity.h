#ifndef Connectivity_h
#define Connectivity_h
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <map>
#include "simplicial_set.h"
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

    int n_edges() const;
    int n_vertices() const;
    int n_faces() const;
    int n_tets() const;
    
    std::vector<int> ValueSet(Eigen::SparseMatrix<int> &target, int value)const;
    std::vector<int> ValueSet(Eigen::SparseMatrix<int> &target, int value, bool is_row)const;
    // API
    SparseMatrix<int> vertices_to_vector(const std::vector<int>& vset) const;
    SparseMatrix<int> edges_to_vector(const std::vector<int>& eset) const;
    SparseMatrix<int> faces_to_vector(const std::vector<int>& fset) const;
    SparseMatrix<int> tets_to_vector(const std::vector<int>& tset) const;  
    std::vector<int> nonzeros(Eigen::SparseMatrix<int> &target)const;
    std::vector<int> nonzeros(Eigen::SparseMatrix<int> &target, bool is_row)const;
    //
    int get_edge_index(int i, int j); 
    int get_edge_index(int i, int j, int &sign);
    // 
// private:
    int num_v; 
    MatrixXi T;
    MatrixXi E;
    MatrixXi F;
    std::vector<int> Vi;
    std::vector<int> Ei; 
    std::vector<int> Fi;
    std::vector<int> Ti;
    std::map<key_f, int> map_f; // tuple -> face index
    std::map<key_e, int> map_e; // tuple -> edge index
    Eigen::SparseMatrix<int> bm1; // |V|x|E|
    Eigen::SparseMatrix<int> pos_bm1; // |V|x|E|
    Eigen::SparseMatrix<int> bm2; // |E|x|F|
    Eigen::SparseMatrix<int> pos_bm2; // |E|x|F|
    Eigen::SparseMatrix<int> bm3; // |F|x|T|
    Eigen::SparseMatrix<int> pos_bm3; // |F|x|T|
};

#endif