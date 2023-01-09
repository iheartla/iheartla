//
//  TriangleMesh.h
//  DEC
//
//  Created by pressure on 10/31/22.
//

#ifndef TriangleMesh_h
#define TriangleMesh_h
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <map>
#include "simplicial_set.h"
// using Eigen::Matrix;
// using Eigen::VectorXi;
using Eigen::SparseMatrix;
typedef std::tuple<std::vector<int>, std::vector<int>, std::vector<int>, std::vector<int> > SetTuple;
typedef std::tuple<int, int, int> key_f;
typedef std::tuple<int, int> key_e;
typedef Eigen::Matrix< int, Eigen::Dynamic, 1> Vector;
typedef Eigen::Matrix< int, 1, Eigen::Dynamic> RowVector;
typedef Eigen::Matrix< int, Eigen::Dynamic, Eigen::Dynamic> Matrix;
class TriangleMesh {
public:
    TriangleMesh(const Eigen::MatrixXd &V, const Eigen::MatrixXi &T);
    TriangleMesh();
    void initialize(const Eigen::MatrixXd &V, Eigen::MatrixXi &T);
    void initialize(const Eigen::MatrixXd &V, const Matrix &T);
    void create_edges();
    void create_faces();
    void build_boundary_mat3(); // T -> F, size: |F|x|T|, boundary of tets
    void build_boundary_mat2(); // F -> E, size: |E|x|F|, boundary of triangles
    void build_boundary_mat1(); // E -> V, size: |V|x|E|, boundary of edges
    void build_nonboundary_edges();
    int get_edge_index(int i, int j); 
    int get_edge_index(int i, int j, int &sign);
    int get_face_index(int i, int j, int k, int &sign);
    int get_face_index(int i, int j, int k); 
    void init_mesh_indices();
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
    std::tuple<std::vector<int>, std::vector<int>, std::vector<int>> MeshSets() const;
    std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > BoundaryMatrices() const;
    std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > UnsignedBoundaryMatrices() const;
    std::vector<int> nonzeros(Eigen::SparseMatrix<int> &target)const;
    std::vector<int> nonzeros(Eigen::SparseMatrix<int> &target, bool is_row)const;
    // 
// private:
    int num_v;
    bool numerical_order;       // whether the indices are stored as numerical order in edges/faces
    Eigen::MatrixXd V;
    Matrix T;
    Matrix E;
    Matrix F;
    std::vector<int> Vi;
    std::vector<int> Ei;
    std::vector<int> nEi;   // non-boundary edges
    std::vector<int> Fi;
    std::map<key_f, int> map_f; // tuple -> face index
    std::map<key_e, int> map_e; // tuple -> edge index
    Eigen::SparseMatrix<int> bm1; // |V|x|E|
    Eigen::SparseMatrix<int> pos_bm1; // |V|x|E|
    Eigen::SparseMatrix<int> bm2; // |E|x|F|
    Eigen::SparseMatrix<int> pos_bm2; // |E|x|F|
    Eigen::SparseMatrix<int> bm3; // |F|x|T|
    Eigen::SparseMatrix<int> pos_bm3; // |F|x|T|
};

#endif /* TriangleMesh_h */
