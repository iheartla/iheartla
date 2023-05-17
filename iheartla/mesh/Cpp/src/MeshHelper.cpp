#include "MeshHelper.h"

namespace iheartmesh {

// std::set<int> vector_to_vertices(const TriangleMesh& mesh, const Eigen::VectorXi& vi){
// 	return mesh.vector_to_vertices(vi);
// }

// std::set<int> vector_to_edges(const TriangleMesh& mesh, const Eigen::VectorXi& ei){
// 	return mesh.vector_to_vertices(ei);
// }

// std::set<int> vector_to_faces(const TriangleMesh& mesh, const Eigen::VectorXi& fi){
// 	return mesh.vector_to_vertices(fi);
// }

std::vector<int> nonzeros(Eigen::SparseMatrix<int> target, bool is_row){
    std::vector<int> result;
    result.reserve(target.rows());  // reserve
    for (int k=0; k<target.outerSize(); ++k){
      for (SparseMatrix<int>::InnerIterator it(target,k); it; ++it) {
        if (is_row)
        {
            result.push_back(it.row());
        }
        else{
            result.push_back(it.col());
        }
      }
    } 
    return result;
}

std::vector<int> nonzeros(Eigen::SparseMatrix<int> target){
    return nonzeros(target, true);
}

std::set<int> ValueSet(Eigen::SparseMatrix<int> target, int value){
    // return row indices for specific value
    return ValueSet(target, value, true);
}
std::set<int> ValueSet(Eigen::SparseMatrix<int> target, int value, bool is_row){
    std::set<int> result;
    for (int k=0; k<target.outerSize(); ++k){
      for (SparseMatrix<int>::InnerIterator it(target,k); it; ++it) {
        if (it.value() == value)
        {
            if (is_row)
            {
                result.insert(it.row());
            }
            else{
                result.insert(it.col());
            }
        }
      }
    } 
    return result;
}

}
