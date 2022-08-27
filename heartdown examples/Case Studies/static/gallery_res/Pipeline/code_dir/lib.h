#pragma once
#include <Eigen/Core>
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <iostream>
#include <set>

struct pipeline {
    Eigen::MatrixXd textbfX;
    double ϕ;
    double D;
    double γ;
    Eigen::Matrix<double, 3, 3> K;
    Eigen::Matrix<double, 3, 1> textbft;
    double A;
    double B;
    double C;
    double α_1;
    double α_2;
    double α_i;
    double α_j;
    std::function<Eigen::Matrix<double, 2, 1>(Eigen::Matrix<double, 2, 1>)> φ_circumflex_accent_1_d;
    std::function<Eigen::Matrix<double, 2, 1>(Eigen::Matrix<double, 2, 1>)> φ_d;
    Eigen::Matrix<double, 2, 1> x_i;
    Eigen::Matrix<double, 2, 1> x_j;
    double x;
    double c_x;
    double f_x;
    double y;
    double c_y;
    Eigen::Matrix<double, 3, 3> R(
        const double & α)
    {
        Eigen::Matrix<double, 3, 3> R_0;
        R_0 << -sin(α), 0, -cos(α),
        0, 1, 0,
        cos(α), 0, -sin(α);
        return R_0;    
    }
    Eigen::MatrixXd P(
        const double & α)
    {
        Eigen::MatrixXd P_0(3, 4);
        P_0 << R(α), textbft;
        return K * P_0;    
    }
    double t(
        const double & α)
    {
        return (α - α_i) / double((α_j - α_i));    
    }
    Eigen::Matrix<double, 2, 1> textbfx(
        const double & α)
    {
        return φ_circumflex_accent_1_d((1 - t(α)) * φ_d(x_i) + t(α) * φ_d(x_j));    
    }
    double ω(
        const double & x)
    {
        return atan((x - c_x) / double(f_x));    
    }
    double s(
        const double & x)
    {
        return (y - c_y) * cos(ω(x));    
    }
    Eigen::VectorXd φ(
        const double & x)
    {
        Eigen::VectorXd φ_0(2);
        φ_0 << ω(x), s(x);
        return φ_0;    
    }
    pipeline(
        const double & f_x,
        const double & f_y,
        const double & c_x,
        const double & c_y,
        const double & r,
        const std::function<Eigen::Matrix<double, 2, 1>(Eigen::Matrix<double, 2, 1>)> & φ_circumflex_accent_1_d,
        const std::function<Eigen::Matrix<double, 2, 1>(Eigen::Matrix<double, 2, 1>)> & φ_d,
        const Eigen::Matrix<double, 2, 1> & x_i,
        const Eigen::Matrix<double, 2, 1> & x_j,
        const double & α_i,
        const double & α_j,
        const double & y,
        const double & X,
        const double & Y,
        const double & Z,
        const double & x)
    {
    
        this->α_i = α_i;
        this->α_j = α_j;
        this->φ_circumflex_accent_1_d = φ_circumflex_accent_1_d;
        this->φ_d = φ_d;
        this->x_i = x_i;
        this->x_j = x_j;
        this->x = x;
        this->c_x = c_x;
        this->f_x = f_x;
        this->y = y;
        this->c_y = c_y;
        Eigen::VectorXd textbfX_0(3);
        textbfX_0 << X, Y, Z;
        // `$\textbf{X}$` = (X,Y,Z)^T
        textbfX = textbfX_0.transpose();
        Eigen::Matrix<double, 3, 3> K_0;
        K_0 << f_x, 0, c_x,
        0, f_y, c_y,
        0, 0, 1;
        // K = [`$f_x$` 0 `$c_x$`
    //       0   `$f_y$` `$c_y$`
    //       0      0    1]
        K = K_0;
        Eigen::Matrix<double, 3, 1> textbft_0;
        textbft_0 << 0,
        0,
        -r;
        // `$\textbf{t}$` = [0;0;-r]
        textbft = textbft_0;
        // A = X ⋅ `$f_x$` - Z⋅(x - `$c_x$` )
        A = X * f_x - Z * (x - c_x);
        // B = Z⋅`$f_x$` + X⋅(x -`$c_x$` )
        B = Z * f_x + X * (x - c_x);
        // D = √(A^2 +B^2)
        D = sqrt((pow(A, 2) + pow(B, 2)));
        // γ = arctan(B/A)
        γ = atan(B / double(A));
        // C = -r⋅(x -`$c_x$` )
        C = -r * (x - c_x);
        // ϕ = arcsin(C/D)
        ϕ = asin(C / double(D));
        // `$α_1$` = ϕ - γ
        α_1 = ϕ - γ;
        // `$α_2$` = π - ϕ - γ
        α_2 = M_PI - ϕ - γ;
    }
};

