#pragma once

#include <iostream>
#include <set>
#include <vector>
#include <Eigen/Dense>
#include <Eigen/Sparse>
// using Eigen::Matrix;
// using Eigen::Vector;
#include "TriangleMesh.h"

namespace iheartmesh {

// std::tuple<std::set<int>, std::set<int>, std::set<int>> MeshSets(const TriangleMesh& mesh);
// std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > BoundaryMatrices(const TriangleMesh& mesh);
// std::set<int> vector_to_vertices(const TriangleMesh& mesh, const Eigen::VectorXi& vi);
// std::set<int> vector_to_edges(const TriangleMesh& mesh, const Eigen::VectorXi& ei);
// std::set<int> vector_to_faces(const TriangleMesh& mesh, const Eigen::VectorXi& fi);

std::vector<int> nonzeros(Eigen::SparseMatrix<int> target);
std::vector<int> nonzeros(Eigen::SparseMatrix<int> target, bool is_row);
std::set<int> ValueSet(Eigen::SparseMatrix<int> target, int value);
std::set<int> ValueSet(Eigen::SparseMatrix<int> target, int value, bool is_row);
Eigen::SparseMatrix<int> indicator(const std::vector<int>& ele_set, int size);
}
