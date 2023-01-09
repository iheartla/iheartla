//
//  TriangleMesh.cpp
//  DEC
//
//  Created by pressure on 10/31/22.
//

#include <stdio.h>
#include <iostream>
#include <vector>
#include <algorithm> 
#include "dec_util.h"
#include "TriangleMesh.h"
using Eigen::VectorXi;
using Eigen::MatrixXi;
// typedef Eigen::Matrix< int, Eigen::Dynamic, 1> Vector;
// typedef Eigen::Matrix< int, 1, Eigen::Dynamic> RowVector;
// typedef Eigen::Matrix< int, Eigen::Dynamic, Eigen::Dynamic> Matrix;
TriangleMesh::TriangleMesh(){

}
TriangleMesh::TriangleMesh(const Eigen::MatrixXd &V, const Matrix &T){
    this->initialize(V, T);
}

void TriangleMesh::initialize(const Eigen::MatrixXd &V, const Matrix &T){
    this->V = V;
    Matrix new_T = preprocess_matrix(T);
    this->initialize(V, new_T);
}
void TriangleMesh::initialize(const Eigen::MatrixXd &V, Matrix &T){
    std::cout<<"T cols:"<<T.cols()<<std::endl;
    this->numerical_order = true;
    this->T = T;
    // std::cout<<"T:\n"<<this->T<<std::endl;
    if (T.cols() == 4) {
        // tets, assume each row (tet) already has the positive orientation
        this->T = T;
        Vector maxVal = T.rowwise().maxCoeff();
        this->num_v = maxVal.maxCoeff()+1;
        this->create_faces();
        this->create_edges();
        //
        this->build_boundary_mat1();
        this->build_boundary_mat2();
        this->build_boundary_mat3();
        }
    else if(T.cols() == 3){
        // faces, assume each row (face) already has the positive orientation
        this->F = T;
        // std::cout<<"this->F:\n"<<this->F<<std::endl;
        Vector maxVal = this->F.rowwise().maxCoeff();
        this->num_v = maxVal.maxCoeff()+1;
        this->create_edges();
        // boundary mat
        this->build_boundary_mat1();
        this->build_boundary_mat2();
    }
    this->init_mesh_indices();
    std::cout<<"Total vertices:"<<this->num_v<<", edges:"<<this->E.rows()<<", faces:"<<this->F.rows()<<", tets:"<<this->T.rows()<<std::endl;
}


void TriangleMesh::init_mesh_indices(){
    this->Vi.resize(this->num_v);
    for (int i = 0; i < this->num_v; ++i){
        this->Vi[i] = i;
    }
    this->Ei.resize(this->E.rows());
    for (int i = 0; i < this->E.rows(); ++i){ 
        this->Ei[i] = i;
    }
    this->Fi.resize(this->F.rows());
    for (int i = 0; i < this->F.rows(); ++i){
        this->Fi[i] = i;
    }
}


std::vector<int> TriangleMesh::nonzeros(Eigen::SparseMatrix<int> & target)const{
    return nonzeros(target, true);
}

std::vector<int> TriangleMesh::nonzeros(Eigen::SparseMatrix<int> & target, bool is_row)const{
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
std::vector<int> TriangleMesh::ValueSet(Eigen::SparseMatrix<int> &target, int value)const{
    // return row indices for specific value
    return ValueSet(target, value, true);
}
std::vector<int> TriangleMesh::ValueSet(Eigen::SparseMatrix<int> &target, int value, bool is_row)const{
    std::vector<int> result;
    for (int k=0; k<target.outerSize(); ++k){
      for (SparseMatrix<int>::InnerIterator it(target,k); it; ++it) {
        if (it.value() == value)
        {
            if (is_row)
            {
                result.push_back(it.row());
            }
            else{
                result.push_back(it.col());
            }
        }
      }
    } 
    return result;
} 

int TriangleMesh::get_edge_index(int i, int j, int &sign){
    if (i < j)
    {
        sign = 1;
        return this->map_e[std::make_tuple(i, j)];
    }
    sign = -1;
    return this->map_e[std::make_tuple(j, i)];
}
int TriangleMesh::get_edge_index(int i, int j){
    if (i < j)
    {
        return this->map_e[std::make_tuple(i, j)];
    }
    return this->map_e[std::make_tuple(j, i)];
} 

int TriangleMesh::get_face_index(int i, int j, int k, int &sign){
    RowVector r(3); r << i, j, k;
    RowVector p = permute_rvector(r); // get sorted face
    // find orientation
    key_f key = std::make_tuple(p(0), p(1), p(2));
    auto search = this->map_f.find(key);
    if (search != this->map_f.end()){
        // the input face has the same orientation as the one stored
        sign = 1;
        return this->map_f[key];
    }
    sign = -1;
    return this->map_f[std::make_tuple(p(0), p(2), p(1))];
}
int TriangleMesh::get_face_index(int i, int j, int k){
    RowVector r(3); r << i, j, k;
    RowVector p = permute_rvector(r); // get sorted face
    // find orientation
    key_f key = std::make_tuple(p(0), p(1), p(2));
    auto search = this->map_f.find(key);
    if (search != this->map_f.end()){
        // the input face has the same orientation as the one stored
        return this->map_f[key];
    }
    return this->map_f[std::make_tuple(p(0), p(2), p(1))];
} 

void TriangleMesh::create_edges(){
    Matrix E(3*this->F.rows(), 2);
    for (int i=0; i<this->F.rows(); i++) {
        if (this->numerical_order)
        {
            Vector v0(2); v0 << this->F(i,0), this->F(i,1);
            E.row(3*i) = sort_vector(v0);
            Vector v1(2); v1 << this->F(i,0), this->F(i,2);
            E.row(3*i+1) = sort_vector(v1);
            Vector v2(2); v2 << this->F(i,1), this->F(i,2);
            E.row(3*i+2) = sort_vector(v2); 
        }
        else{
            RowVector v0(2); v0 << this->F(i,0), this->F(i,1);
            E.row(3*i) = v0;
            RowVector v1(2); v1 << this->F(i,2), this->F(i,0);
            E.row(3*i+1) = v1;
            RowVector v2(2); v2 << this->F(i,1), this->F(i,2);
            E.row(3*i+2) = v2; 
        }
    }
    // std::cout<<"before this->E:\n"<<E<<std::endl;
    this->E = remove_duplicate_rows(sort_matrix(E));    
    // std::cout<<"this->E:\n"<<this->E<<std::endl;
    // create the mapping
    for (int i=0; i<this->E.rows(); i++) {
        this->map_e.insert(std::pair<key_e, int>(std::make_tuple(this->E(i,0), this->E(i,1)), i));
    }
}


void TriangleMesh::create_faces(){
    // create face from tetrahedra, assume the tetrahedra orientation is positive
    Matrix F(4*T.rows(), 3);
    for (int i=0; i<this->T.rows(); i++) {
        if (this->numerical_order)
        {
            Vector v0(3); v0 << this->T(i,0), this->T(i,1), this->T(i,2);
            F.row(4*i) = sort_vector(v0);
            Vector v1(3); v1 << this->T(i,0), this->T(i,1), this->T(i,3);
            F.row(4*i+1) = sort_vector(v1);
            Vector v2(3); v2 << this->T(i,0), this->T(i,2), this->T(i,3);
            F.row(4*i+2) = sort_vector(v2);
            Vector v3(3); v3 << this->T(i,1), this->T(i,2), this->T(i,3);
            F.row(4*i+3) = sort_vector(v3);
        }
        else{
            // positive
            RowVector v0(3); v0 << this->T(i,0), this->T(i,2), this->T(i,1);
            F.row(4*i) = permute_rvector(v0);
            RowVector v1(3); v1 << this->T(i,0), this->T(i,1), this->T(i,3);
            F.row(4*i+1) = permute_rvector(v1);
            RowVector v2(3); v2 << this->T(i,0), this->T(i,3), this->T(i,2);
            F.row(4*i+2) = permute_rvector(v2);
            RowVector v3(3); v3 << this->T(i,1), this->T(i,2), this->T(i,3);
            F.row(4*i+3) = permute_rvector(v3);
        }
    }
    this->F = remove_duplicate_rows(sort_matrix(F));
    std::cout<<"this->F:\n"<<this->F<<std::endl;
    // create the mapping
    for (int i=0; i<this->F.rows(); i++) {
        this->map_f.insert(std::pair<key_f, int>(std::make_tuple(this->F(i,0), this->F(i,1), this->F(i,2)), i));
    }
}

void TriangleMesh::build_boundary_mat3(){
    this->bm3.resize(this->F.rows(), this->T.rows());
    std::vector<Eigen::Triplet<int> > tripletList;
    tripletList.reserve(3*this->T.rows());
    int sign = 1;
    // The faces of a tet +(t0,t1,t2,t3) 
    for(int i=0; i<this->T.rows(); i++){
        // −(t0,t1,t2)
        int idx = get_face_index(this->T(i,0), this->T(i,1), this->T(i,2), sign);
        tripletList.push_back(Eigen::Triplet<int>(idx, i, -sign));
        // +(t0,t1,t3)
        idx = get_face_index(this->T(i,0), this->T(i,1), this->T(i,3), sign);
        tripletList.push_back(Eigen::Triplet<int>(idx, i, sign));
        // −(t0,t2,t3)
        idx = get_face_index(this->T(i,0), this->T(i,2), this->T(i,3), sign);
        tripletList.push_back(Eigen::Triplet<int>(idx, i, -sign));
        // +(t1,t2,t3)
        idx = get_face_index(this->T(i,1), this->T(i,2), this->T(i,3), sign);
        tripletList.push_back(Eigen::Triplet<int>(idx, i, sign));
        // tripletList.push_back(Eigen::Triplet<int>(this->map_f[std::make_tuple(this->T(i,0), this->T(i,1), this->T(i,2))], i, -1));
        // tripletList.push_back(Eigen::Triplet<int>(this->map_f[std::make_tuple(this->T(i,0), this->T(i,1), this->T(i,3))], i, 1));
        // tripletList.push_back(Eigen::Triplet<int>(this->map_f[std::make_tuple(this->T(i,0), this->T(i,2), this->T(i,3))], i, -1));
        // tripletList.push_back(Eigen::Triplet<int>(this->map_f[std::make_tuple(this->T(i,1), this->T(i,2), this->T(i,3))], i, 1));
    }
    this->bm3.setFromTriplets(tripletList.begin(), tripletList.end());
    this->pos_bm3 = this->bm3.cwiseAbs();
    // std::cout<<"this->bm3:\n"<<this->bm3<<std::endl;
    // std::cout<<"this->pos_bm3:\n"<<this->pos_bm3<<std::endl;
}

void TriangleMesh::build_boundary_mat2(){
    this->bm2.resize(this->E.rows(), this->F.rows());
    std::vector<Eigen::Triplet<int> > tripletList;
    tripletList.reserve(3*this->F.rows());
    int sign = 1;
    // The faces of a triangle +(f0,f1,f2)
    for(int i=0; i<this->F.rows(); i++){
        // +(f0,f1)
        int idx = get_edge_index(this->F(i,0), this->F(i,1), sign);
        tripletList.push_back(Eigen::Triplet<int>(idx, i, sign));
        // −(f0,f2)
        idx = get_edge_index(this->F(i,0), this->F(i,2), sign);
        tripletList.push_back(Eigen::Triplet<int>(idx, i, -sign));
        // +(f1, f2)
        idx = get_edge_index(this->F(i,1), this->F(i,2), sign);
        tripletList.push_back(Eigen::Triplet<int>(idx, i, sign));
        // tripletList.push_back(Eigen::Triplet<int>(this->map_e[std::make_tuple(this->F(i,0), this->F(i,1))], i, 1));
        // tripletList.push_back(Eigen::Triplet<int>(this->map_e[std::make_tuple(this->F(i,0), this->F(i,2))], i, -1));
        // tripletList.push_back(Eigen::Triplet<int>(this->map_e[std::make_tuple(this->F(i,1), this->F(i,2))], i, 1));
    }
    this->bm2.setFromTriplets(tripletList.begin(), tripletList.end());
    this->pos_bm2 = this->bm2.cwiseAbs();
    // std::cout<<"this->bm2:\n"<<this->bm2<<std::endl;
    // std::cout<<"this->pos_bm2:\n"<<this->pos_bm2<<std::endl;
}

void TriangleMesh::build_boundary_mat1(){
    this->bm1.resize(this->num_v, this->E.rows());
    std::vector<Eigen::Triplet<int> > tripletList;
    tripletList.reserve(2*this->E.rows());
    for(int i=0; i<this->E.rows(); i++){
        tripletList.push_back(Eigen::Triplet<int>(this->E(i,0), i, -1));
        tripletList.push_back(Eigen::Triplet<int>(this->E(i,1), i, 1));
    }
    this->bm1.setFromTriplets(tripletList.begin(), tripletList.end());
    this->pos_bm1 = this->bm1.cwiseAbs();
    // std::cout<<"this->bm1:\n"<<this->bm1<<std::endl;
    // std::cout<<"this->pos_bm1:\n"<<this->pos_bm1<<std::endl;
}

int TriangleMesh::n_edges() const{
    return this->E.rows();
}
int TriangleMesh::n_vertices() const{
    return this->num_v;
}
int TriangleMesh::n_faces() const{
    return this->F.rows();
}
int TriangleMesh::n_tets() const{
    return this->T.rows();
}
SparseMatrix<int> TriangleMesh::vertices_to_vector(const std::vector<int>& vset) const{
    SparseMatrix<int> v(this->num_v, 1);
    std::vector<Eigen::Triplet<int> > tripletList; 
    tripletList.reserve(this->num_v);
    for (int idx : vset)
    {
        tripletList.push_back(Eigen::Triplet<int>(idx, 0, 1));
    }
    // std::cout<<"this->num_v:"<<this->num_v<<std::endl;
    // std::cout<<"vset size:"<<vset.size()<<std::endl;
    // std::cout<<"tripletList size:"<<tripletList.size()<<std::endl;
    v.setFromTriplets(tripletList.begin(), tripletList.end());
    return v;
}
SparseMatrix<int> TriangleMesh::edges_to_vector(const std::vector<int>& eset) const{
    SparseMatrix<int> e(this->E.rows(), 1);
    std::vector<Eigen::Triplet<int> > tripletList; 
    tripletList.reserve(this->E.rows());
    for (int idx : eset)
    {
        tripletList.push_back(Eigen::Triplet<int>(idx, 0, 1));
    }
    e.setFromTriplets(tripletList.begin(), tripletList.end());
    return e;
}
SparseMatrix<int> TriangleMesh::faces_to_vector(const std::vector<int>& fset) const{
    SparseMatrix<int> f(this->F.rows(), 1);
    std::vector<Eigen::Triplet<int> > tripletList; 
    tripletList.reserve(this->F.rows());
    for (int idx : fset)
    {
        tripletList.push_back(Eigen::Triplet<int>(idx, 0, 1));
    }
    f.setFromTriplets(tripletList.begin(), tripletList.end());
    return f;
}
SparseMatrix<int> TriangleMesh::tets_to_vector(const std::vector<int>& tset) const{
    SparseMatrix<int> t(this->T.rows(), 1);
    std::vector<Eigen::Triplet<int> > tripletList; 
    tripletList.reserve(this->T.rows());
    for (int idx : tset)
    {
        tripletList.push_back(Eigen::Triplet<int>(idx, 0, 1));
    }
    t.setFromTriplets(tripletList.begin(), tripletList.end());
    return t;
}
  
std::tuple<std::vector<int>, std::vector<int>, std::vector<int>> TriangleMesh::MeshSets() const{
    return std::tuple<std::vector<int>, std::vector<int>, std::vector<int>>(this->Vi, this->Ei, this->Fi);
}

std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > TriangleMesh::BoundaryMatrices() const{
    return std::tuple< Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> >(this->bm1, this->bm2);
}

std::tuple<Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> > TriangleMesh::UnsignedBoundaryMatrices() const{
    return std::tuple< Eigen::SparseMatrix<int>, Eigen::SparseMatrix<int> >(this->pos_bm1, this->pos_bm2);
}
