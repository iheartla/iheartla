#ifndef PointCloud_h
#define PointCloud_h
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <map>
#include "simplicial_set.h"
#include "Connectivity.h"

class PointCloud: public Connectivity {
public:
    PointCloud(Eigen::MatrixXd &P, double distance=1.4);
    PointCloud();
    void initialize(Eigen::MatrixXd &P, double distance=1.4); 
    void build_boundary_mat1(); // E -> V, size: |V|x|E|, boundary of edges 
    int get_edge_index(int i, int j); 
    int get_edge_index(int i, int j, int &sign); 
    void init_indices();
    //
    std::tuple<std::vector<int>, std::vector<int>> MeshSets() const;
    Eigen::SparseMatrix<int> BoundaryMatrices() const;
    Eigen::SparseMatrix<int> UnsignedBoundaryMatrices() const;
    // 
    bool numerical_order;       // whether the indices are stored as numerical order in edges/faces
};

#endif