#ifndef PolygonMesh_h
#define PolygonMesh_h
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <map>
#include "simplicial_set.h"
#include "Connectivity.h"

class PolygonMesh: public Connectivity {
public:
    PolygonMesh();
    PolygonMesh(std::vector<std::vector<int> > &T);
    void initialize(std::vector<std::vector<int> > &T);
    // void initialize(const std::vector<std::vector<int> > &T);
    void create_edges();


    void create_faces();
    void build_boundary_mat3(); // T -> F, size: |F|x|T|, boundary of tets
    void build_boundary_mat2(); // F -> E, size: |E|x|F|, boundary of triangles
    void build_boundary_mat1(); // E -> V, size: |V|x|E|, boundary of edges
    void build_nonboundary_edges();
    int get_face_index(int i, int j, int k, int &sign);
    int get_face_index(int i, int j, int k); 
    void init_indices();
    //
    SparseMatrix<int> faces_to_vector(const std::vector<int>& fset) const;
    std::tuple<std::vector<int>, std::vector<int>, std::vector<int>> ElementSets() const;
    std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > BoundaryMatrices() const;
    std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > UnsignedBoundaryMatrices() const;
    // 
    bool numerical_order;       // whether the indices are stored as numerical order in edges/faces

    std::vector<std::vector<int> > Face;
    std::map<std::vector<int>, int> map_face;
    int max_degree;   // max vertices in a face
};

#endif