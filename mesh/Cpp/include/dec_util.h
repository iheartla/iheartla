//
//  util.h
//  DEC
//
//  Created by pressure on 10/31/22.
//
#pragma once

#include <iostream>
#include <set>
#include <vector>
#include <Eigen/Dense>
#include <Eigen/Sparse>
// using Eigen::Matrix;
// using Eigen::Vector;

typedef Eigen::Matrix< int, Eigen::Dynamic, 1> Vector;
typedef Eigen::Matrix< int, 1, Eigen::Dynamic> RowVector;
typedef Eigen::Matrix< int, Eigen::Dynamic, Eigen::Dynamic> Matrix;

bool compare_vec(const Matrix &fir, const Matrix &sec);

void swap(Matrix &source, int i, int j);

void swap(Vector &source, int i, int j);

int partition(Matrix &source, int start, int end);

int partition(Vector &source, int start, int end);

void quickSort(Matrix &source, int start, int end);

void quickSort(Vector &source, int start, int end);

Matrix sort_matrix(Matrix &source);

Vector sort_vector(Vector &source);

RowVector sort_rvector(RowVector &source);

RowVector permute_rvector(const RowVector &source);

Matrix remove_duplicate_rows(Matrix source);

Matrix preprocess_matrix(const Matrix &source);

void print_set(const std::set<int>& source);

void print_vec(const std::vector<int>& source);
