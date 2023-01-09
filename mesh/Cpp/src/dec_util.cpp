//
//  util.h
//  DEC
//
//  Created by pressure on 10/31/22.
//
#pragma once

#include <Eigen/Dense>
#include <Eigen/Sparse>
#include "dec_util.h"
// using Eigen::Matrix;
// using Eigen::Vector;

typedef Eigen::Matrix< int, Eigen::Dynamic, 1> Vector;
typedef Eigen::Matrix< int, 1, Eigen::Dynamic> RowVector;
typedef Eigen::Matrix< int, Eigen::Dynamic, Eigen::Dynamic> Matrix;

bool compare_vec(const Matrix &fir, const Matrix &sec){
    assert(fir.rows() == sec.rows() && fir.rows() == 1);
    assert(fir.cols() == sec.cols());
    bool less = true;
    for (int i=0; i<fir.cols(); i++){
        if (fir(0, i) != sec(0, i)) {
            if (fir(0, i) > sec(0, i)) {
                less = false;
            }
            break;
        }
    }
//    std::cout<<"fir:"<<fir<<", sec:"<<sec<<", less:"<<less<<std::endl;
    return less;
}

void swap(Matrix &source, int i, int j){
//    std::cout<<"before:"<<source<<", i:"<<i<<", j:"<<j<<std::endl;
    for (int k=0; k<source.cols(); k++){
        int tmp = source(i, k);
        source(i, k) = source(j, k);
        source(j, k) = tmp;
    }
//    std::cout<<"after:"<<source;
}

void swap(Vector &source, int i, int j){
    int tmp = source(i);
    source(i) = source(j);
    source(j) = tmp;
}

int partition(Matrix &source, int start, int end)
{
    Matrix pivot = source.row(end);
    int i = start - 1;
    for (int j = start; j <= end-1; j++){
        Matrix cur = source.row(j);
        if (compare_vec(cur, pivot)) {
            i = i + 1;
            swap(source, i, j);
        }
    }
    swap(source, i+1, end);
    return i+1;
}

int partition(Vector &source, int start, int end)
{
    int pivot = source(end);
    int i = start - 1;
    for (int j = start; j <= end-1; j++){
        if (source(j) < pivot) {
            i = i + 1;
            swap(source, i, j);
        }
    }
    swap(source, i+1, end);
    return i+1;
}
void quickSort(Matrix &source, int start, int end)
{
    if (start >= end)
        return;
    int p = partition(source, start, end);
    quickSort(source, start, p - 1);
    quickSort(source, p + 1, end);
}

void quickSort(Vector &source, int start, int end)
{
    if (start >= end)
        return;
    int p = partition(source, start, end);
    quickSort(source, start, p - 1);
    quickSort(source, p + 1, end);
}
 

Matrix sort_matrix(Matrix &source){
    quickSort(source, 0, (int)source.rows()-1);
    return source;
}

Vector sort_vector(Vector &source){
    quickSort(source, 0, (int)source.rows()-1);
    return source;
}

RowVector sort_rvector(RowVector &source){
    Vector t = source.transpose();
    quickSort(t, 0, (int)t.rows()-1);
    return t.transpose();
}

RowVector permute_rvector(const RowVector &source){
    if (source.cols() > 0)
    {
        int min_index = 0;
        int cur_val = source(0);
        for (int i = 1; i < source.cols(); ++i)
        {
            if (source(i)<cur_val)
            {
                cur_val = source(i);
                min_index = i;
            }
        }
        if (min_index != 0)
        {
            RowVector res(source.cols());
            for (int i = 0; i < source.cols(); ++i)
            {
                res(i) = source((i+min_index)%source.cols());
            }
            return res;
        }
    }
    return source;
}

Matrix remove_duplicate_rows(Matrix source){
    if (source.rows() == 0) {
        return source;
    }
    Matrix output(source.rows(), source.cols());
    Matrix cur = source.row(0);
    output.row(0) = cur;
    int cnt = 1;
    for (int j = 1; j < source.rows(); j++){
        if (cur == source.row(j)) {
            continue;
        }
        else{
            cur = source.row(j);
            output.row(cnt) = cur;
            cnt++;
        }
    }
    output.conservativeResize(cnt, source.cols());
    return output;
}


Matrix preprocess_matrix(const Matrix &source){
    Matrix new_source(source.rows(), source.cols());
    for (int i=0; i< source.rows(); i++) {
        RowVector r = source.row(i);
        new_source.row(i) = permute_rvector(r);
    }
    return remove_duplicate_rows(sort_matrix(new_source));
}


void print_set(const std::set<int>& source){
    for (std::set<int>::iterator it = source.begin(); it != source.end(); ++it) {
        std::cout << *it << ", ";
    }
    std::cout << std::endl;
} 

void print_vec(const std::vector<int>& source){
    for (int i=0; i<source.size(); ++i) {
        std::cout << source[i] << ", ";
    }
    std::cout << std::endl;
}
