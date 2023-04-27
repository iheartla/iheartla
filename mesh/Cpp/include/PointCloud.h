#ifndef PointCloud_h
#define PointCloud_h
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <map>
#include "simplicial_set.h"
#include "Connectivity.h"
#include "nanoflann.hpp"

struct MPoint {
  std::vector<Eigen::VectorXd> points;
  inline size_t kdtree_get_point_count() const { return points.size(); }
  inline double kdtree_get_pt(const size_t idx, int dim) const { return points[idx](dim); }
  template <class BBOX>
  bool kdtree_get_bbox(BBOX& bb) const {
    return false;
  }
};

typedef nanoflann::KDTreeSingleIndexAdaptor<nanoflann::L2_Simple_Adaptor<double, MPoint>, MPoint, 3>
      MESH_KD_Tree_T;

class PointCloudWrapper {
public:
  PointCloudWrapper(std::vector<Eigen::VectorXd>& P, int k=10);
  ~PointCloudWrapper();
  MPoint data;
  MESH_KD_Tree_T tree;
  std::vector<size_t> kNearest(Eigen::VectorXd query, size_t k);
  std::vector<size_t> kNearestNeighbors(size_t sourceInd, size_t k);
};


class PointCloud: public Connectivity {
public:
    PointCloud(std::vector<Eigen::VectorXd>& P, int k=10);
    PointCloud(const PointCloud& a){
      this->num_v = a.num_v;
      this->bm1 = a.bm1;
      this->Vi = a.Vi;
      this->Ei = a.Ei;
    } 
    void build_boundary_mat1(); // E -> V, size: |V|x|E|, boundary of edges 
    void init_indices();
    //

    std::tuple<std::vector<int>, std::vector<int>> ElementSets() const;
    Eigen::SparseMatrix<int> BoundaryMatrices() const;
    Eigen::SparseMatrix<int> UnsignedBoundaryMatrices() const;
    // 
    bool numerical_order;       // whether the indices are stored as numerical order in edges/faces
    std::unique_ptr<PointCloudWrapper> impl;
};


#endif