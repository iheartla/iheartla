#pragma once
#include <Eigen/Core>
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <iostream>
#include <set>

struct nautilus {
    Eigen::Matrix<double, 3, 3> H;
    Eigen::Matrix<double, 3, 3> P;
    Eigen::Matrix<double, 3, 3> S;
    Eigen::VectorXd x;
    double λ;
    std::vector<Eigen::Matrix<double, 3, 3>> v;
    double E(
        const Eigen::VectorXd & x)
    {
        const long n = x.size();
        Eigen::VectorXd E_0(2);
        E_0 << x[5-1], x[8-1];
        Eigen::VectorXd E_1(2);
        E_1 << x[9-1], x[6-1];
        double sum_0 = 0;
        for(int i=1; i<=v.size(); i++){
            sum_0 += pow((H * v.at(i-1) - P * S * P.colPivHouseholderQr().solve(v.at(i-1))).norm(), 2);
        }
        return λ * pow((E_0 - E_1).lpNorm<2>(), 2) + sum_0;    
    }
    nautilus(
        const Eigen::VectorXd & x,
        const double & λ,
        const std::vector<Eigen::Matrix<double, 3, 3>> & v)
    {
        const long n = x.size();
        const long dim_0 = v.size();
        this->x = x;
        this->λ = λ;
        this->v = v;
        Eigen::Matrix<double, 3, 3> P_0;
        P_0 << 1, x[1-1], 0,
        0, x[2-1], 0,
        x[3-1], x[4-1], 1;
        // P = [1 x₁ 0
    //      0 x₂ 0
    //      x₃ x₄ 1]
        P = P_0;
        Eigen::Matrix<double, 3, 3> S_0;
        S_0 << x[5-1], x[6-1], x[7-1],
        x[8-1], x[9-1], x[10-1],
        0, 0, 1;
        // S = [x₅ x₆ x₇
    //      x₈ x₉ x₁₀
    //      0 0 1]
        S = S_0;
        // H = PSP⁻¹
        H = P * S * P.inverse();
    }
};

