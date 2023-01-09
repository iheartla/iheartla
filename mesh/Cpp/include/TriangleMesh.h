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
typedef std::tuple<std::set<int>, std::set<int>, std::set<int>, std::set<int> > SetTuple;
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
    void create_edges_from_faces();
    void create_faces();
    void build_boundary_mat3(); // T -> F, size: |F|x|T|, boundary of tets
    void build_boundary_mat2(); // F -> E, size: |E|x|F|, boundary of triangles
    void build_boundary_mat1(); // E -> V, size: |V|x|E|, boundary of edges
    void build_nonboundary_edges();
    // mesh API
    // v as input
    std::set<int> get_adjacent_vertices_v(int vindex); 
    std::set<int> get_incident_edges_v(int vindex); 
    std::set<int> get_incident_faces_v(int vindex); 
    // e as input
    std::set<int> get_incident_vertices_e(int eindex); 
    std::set<int> get_incident_faces_e(int eindex); 
    std::set<int> get_diamond_vertices_e(int eindex);
    std::tuple< int, int > get_diamond_vertices_e(int start, int end);
    std::tuple< int, int > get_diamond_faces_e(int eindex);
    std::tuple< int, int> get_vertices_e(int eindex);
    // f as input
    std::set<int> get_incident_vertices_f(int findex); 
    std::set<int> get_incident_edges_f(int findex); 
    std::set<int> get_adjacent_faces_f(int findex); 
    std::set<int> get_adjacent_faces_f2(int findex);
    std::tuple< int, int, int > get_edges_f(int findex);
    std::tuple< int, int, int > get_vertices_f(int findex);
    //
    int get_opposite_vertex(const RowVector& f, int start, int end);
    // simplicial complex
    SparseMatrix<int> vertices_to_vector(const SimplicialSet& subset) const;
    SparseMatrix<int> edges_to_vector(const SimplicialSet& subset) const;
    SparseMatrix<int> faces_to_vector(const SimplicialSet& subset) const;
    SparseMatrix<int> vertices_to_vector(const std::set<int>& vset) const;
    SparseMatrix<int> edges_to_vector(const std::set<int>& eset) const;
    SparseMatrix<int> faces_to_vector(const std::set<int>& fset) const;
    SparseMatrix<int> tets_to_vector(const std::set<int>& tset) const;
    std::set<int> vector_to_vertices(SparseMatrix<int>& vi);
    std::set<int> vector_to_edges(SparseMatrix<int>& ei);
    std::set<int> vector_to_faces(SparseMatrix<int>& fi);
    std::set<int> vector_to_tets(SparseMatrix<int>& ti);
    SimplicialSet star(const SimplicialSet& subset) const;
    SetTuple star(SetTuple& subset) const;
    SimplicialSet closure(const SimplicialSet& subset) const;
    SimplicialSet link(const SimplicialSet& subset) const;
    SetTuple diamond(int eindex);
    bool is_complex(const SimplicialSet& subset) const;
    int is_pure_complex(const SimplicialSet& subset) const;
    SimplicialSet boundary(const SimplicialSet& subset) const;

    std::set<int> vertices(const SetTuple& sset);
    std::set<int> edges(const SetTuple& sset);
    std::set<int> faces(const SetTuple& sset);
    std::set<int> tets(const SetTuple& sset);
    std::tuple<std::set<int>, std::set<int>, std::set<int>> MeshSets() const;
    std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > BoundaryMatrices() const;
    std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > UnsignedBoundaryMatrices() const;
    // std::tuple<Eigen::VectorXi, Eigen::Matrix<int, Eigen::Dynamic, 2>, Eigen::Matrix<int, Eigen::Dynamic, 3> > CanonicalVertexOrderings() const;

    //
    int n_edges() const;
    int n_vertices() const;
    int n_faces() const;
    int n_tets() const;
    int get_edge_index(int i, int j); 
    int get_edge_index(int i, int j, int &sign);
    int get_face_index(int i, int j, int k, int &sign);
    int get_face_index(int i, int j, int k); 
    void init_mesh_indices();
    std::set<int> nonzeros(Eigen::SparseMatrix<int> &target)const;
    std::set<int> nonzeros(Eigen::SparseMatrix<int> &target, bool is_row)const;
    std::set<int> ValueSet(Eigen::SparseMatrix<int> &target, int value)const;
    std::set<int> ValueSet(Eigen::SparseMatrix<int> &target, int value, bool is_row)const;
// private:
    int num_v;
    bool numerical_order;       // whether the indices are stored as numerical order in edges/faces
    Eigen::MatrixXd V;
    Matrix T;
    Matrix E;
    Matrix nonboundary_edges;  // non-boundary edges
    Matrix F;
    std::set<int> Vi;
    std::set<int> Ei;
    std::set<int> nEi;   // non-boundary edges
    std::set<int> Fi;
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
