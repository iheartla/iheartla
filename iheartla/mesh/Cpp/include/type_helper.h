// Support code for the C++ (Eigen) code that I❤️LA generates, from both the
// Python and the Rust compilers. Generated code turns on optional parts by
// defining their macros before it includes this header:
//
//     #define IHEARTLA_DERIVATIVES    // derivatives (https://github.com/autodiff/autodiff)
//     #include "type_helper.h"
//
// Each part has its own include guard (not #pragma once), so a later include
// with more parts turned on adds them: generated headers that need different
// parts can be included in any order. Only the derivatives part needs autodiff.

#ifndef IHEARTLA_TYPE_HELPER_H
#define IHEARTLA_TYPE_HELPER_H

#include <Eigen/Core>
#include <Eigen/QR>
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <iostream>
#include <vector>
#include <set>
#include <algorithm>
#include <type_traits>

// sets are sorted vectors without duplicates
template<typename T> std::vector<T> sorted_set(std::vector<T> v) {
    std::sort(v.begin(), v.end());
    v.erase(std::unique(v.begin(), v.end()), v.end());
    return v;
}
// (vectors in lexicographic order)
template<typename S, int R, int C, int O, int MR, int MC> std::vector<Eigen::Matrix<S, R, C, O, MR, MC>> sorted_set(std::vector<Eigen::Matrix<S, R, C, O, MR, MC>> v) {
    using M = Eigen::Matrix<S, R, C, O, MR, MC>;
    std::sort(v.begin(), v.end(), [](const M & a, const M & b){ return std::lexicographical_compare(a.data(), a.data() + a.size(), b.data(), b.data() + b.size()); });
    v.erase(std::unique(v.begin(), v.end(), [](const M & a, const M & b){ return a.size() == b.size() && (a.array() == b.array()).all(); }), v.end());
    return v;
}

namespace iheartmesh {

// x with double reals: a real (double, or autodiff::var's value), an Eigen
// matrix or vector of them, or a std::vector of those
inline double to_double(double x) {
    return x;
}

template<typename S> auto to_double(const S & x) -> decltype(double(x.expr->val)) {
    return x.expr->val;
}

template<typename Derived> Eigen::Matrix<double, Derived::RowsAtCompileTime, Derived::ColsAtCompileTime> to_double(const Eigen::MatrixBase<Derived> & x) {
    return x.unaryExpr([](const typename Derived::Scalar & s){ return to_double(s); });
}

template<typename T, typename A> auto to_double(const std::vector<T, A> & x) {
    std::vector<decltype(to_double(x[0]))> ret;
    ret.reserve(x.size());
    for (const auto & e : x) ret.push_back(to_double(e));
    return ret;
}

}

#endif

#if defined(IHEARTLA_DERIVATIVES) && !defined(IHEARTLA_TYPE_HELPER_DERIVATIVES_H)
#define IHEARTLA_TYPE_HELPER_DERIVATIVES_H

#include <autodiff/reverse/var.hpp>
#include <autodiff/reverse/var/eigen.hpp>

namespace iheartmesh {

using namespace autodiff;

// x with autodiff::var reals (the counterpart of to_double)
inline autodiff::var to_var(const autodiff::var & x) {
    return x;
}

inline autodiff::var to_var(double x) {
    return x;
}

template<typename Derived> Eigen::Matrix<autodiff::var, Derived::RowsAtCompileTime, Derived::ColsAtCompileTime> to_var(const Eigen::MatrixBase<Derived> & x) {
    return x.unaryExpr([](const typename Derived::Scalar & s){ return to_var(s); });
}

template<typename T, typename A> auto to_var(const std::vector<T, A> & x) {
    std::vector<decltype(to_var(x[0]))> ret;
    ret.reserve(x.size());
    for (const auto & e : x) ret.push_back(to_var(e));
    return ret;
}

// x with DT reals (double or autodiff::var)
template<class DT, typename T> auto to_dt(const T & x) {
    if constexpr (std::is_same<DT, autodiff::var>::value) return to_var(x);
    else return to_double(x);
}

}

// For derivatives (reverse mode): a value as one flat vector, the value from
// such a vector, and a value's reals converted to autodiff::var (anything else
// is kept).
namespace iheartla_diff {
template<typename T> struct is_vector : std::false_type {};
template<typename T, typename A> struct is_vector<std::vector<T, A>> : std::true_type {};
template<typename T> struct is_eigen : std::is_base_of<Eigen::EigenBase<T>, T> {};
// the length of the flat vector
template<typename T> long flat_size(const T & x) {
    if constexpr (is_vector<T>::value) { long n = 0; for (const auto & e : x) n += flat_size(e); return n; }
    else if constexpr (is_eigen<T>::value) return x.size();
    else return 1;
}
// x into v from offset k, row by row (as NumPy's ravel)
template<typename V, typename T> void flatten_into(const T & x, V & v, long & k) {
    if constexpr (is_vector<T>::value) { for (const auto & e : x) flatten_into(e, v, k); }
    else if constexpr (is_eigen<T>::value) { for (long i = 0; i < x.rows(); i++) for (long j = 0; j < x.cols(); j++) v(k++) = x(i, j); }
    else v(k++) = x;
}
template<typename S, typename T> Eigen::Matrix<S, Eigen::Dynamic, 1> flatten(const T & x) {
    Eigen::Matrix<S, Eigen::Dynamic, 1> v(flat_size(x)); long k = 0; flatten_into(x, v, k); return v;
}
// a value shaped as x, with S reals, from v (from offset k)
template<typename S, typename T, typename V> auto unflatten(const V & v, const T & x, long & k) {
    if constexpr (is_vector<T>::value) {
        std::vector<decltype(unflatten<S>(v, x[0], k))> r;
        for (const auto & e : x) r.push_back(unflatten<S>(v, e, k));
        return r;
    } else if constexpr (is_eigen<T>::value) {
        Eigen::Matrix<S, T::RowsAtCompileTime, T::ColsAtCompileTime> r(x.rows(), x.cols());
        for (long i = 0; i < x.rows(); i++) for (long j = 0; j < x.cols(); j++) r(i, j) = v(k++);
        return r;
    } else return S(v(k++));
}
template<typename S, typename T, typename V> auto unflatten(const V & v, const T & x) { long k = 0; return unflatten<S>(v, x, k); }
// x with its reals as S (integers, sets, meshes, functions, sparse matrices kept)
template<typename S, typename T> auto to(const T & x) {
    if constexpr (std::is_same<T, double>::value) return S(x);
    else if constexpr (is_vector<T>::value) {
        if constexpr (std::is_same<decltype(to<S>(x[0])), typename T::value_type>::value) return x;
        else { std::vector<decltype(to<S>(x[0]))> r; for (const auto & e : x) r.push_back(to<S>(e)); return r; }
    } else if constexpr (is_eigen<T>::value && !std::is_base_of<Eigen::SparseMatrixBase<T>, T>::value) {
        if constexpr (std::is_same<typename T::Scalar, double>::value) return Eigen::Matrix<S, T::RowsAtCompileTime, T::ColsAtCompileTime>(x.template cast<S>());
        else return x;
    } else return x;
}
}

#endif
