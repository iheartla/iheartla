#pragma once

#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <map>
#include "Connectivity.h"

namespace iheartmesh {

class TriangleMesh: public Connectivity {
public:
    TriangleMesh(const Eigen::MatrixXi &T);
    TriangleMesh();
    void initialize(Eigen::MatrixXi &T);
    void initialize(const MatrixXi &T);
    void create_edges();
    void create_faces();
    void build_boundary_mat3(); // T -> F, size: |F|x|T|, boundary of tets
    void build_boundary_mat2(); // F -> E, size: |E|x|F|, boundary of triangles
    void build_boundary_mat1(); // E -> V, size: |V|x|E|, boundary of edges
    void build_nonboundary_edges();
    int get_face_index(int i, int j, int k, int &sign);
    int get_face_index(int i, int j, int k); 
    // 
    bool numerical_order;       // whether the indices are stored as numerical order in edges/faces
};

}
