#pragma once
#include <Eigen/Core>
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <iostream>
#include <set>

struct Anisotropic {
    Eigen::Matrix<double, 3, 3> A;
    double lambda_0_comma_1_comma_2;
    double I_5;
    Eigen::Matrix<double, 3, 3> frac_partial_differential_I₅_partial_differential_F;
    Eigen::MatrixXd frac_partial_differential_²I₅_partial_differential_f²;
    Eigen::MatrixXd mathbfQ_0;
    Eigen::MatrixXd mathbfQ_1;
    Eigen::MatrixXd mathbfQ_2;

    Anisotropic(
        const Eigen::Matrix<double, 3, 1> & a,
        const Eigen::Matrix<double, 3, 3> & C,
        const Eigen::Matrix<double, 3, 3> & F)
    {
    
        // A = a a^T
        A = a * a.transpose();
        // `$\lambda_{0,1,2}$`=2||a||_2^2
        lambda_0_comma_1_comma_2 = 2 * pow((a).lpNorm<2>(), 2);
        // `$I_5$` = tr(CA)
        I_5 = (C * A).trace();
        // `$\frac{∂I₅}{∂F}$` = 2FA
        frac_partial_differential_I₅_partial_differential_F = 2 * F * A;
        Eigen::MatrixXd frac_partial_differential_²I₅_partial_differential_f²_0(9, 9);
        frac_partial_differential_²I₅_partial_differential_f²_0 << A(1-1, 1-1) * Eigen::MatrixXd::Identity(3, 3), A(1-1, 2-1) * Eigen::MatrixXd::Identity(3, 3), A(1-1, 3-1) * Eigen::MatrixXd::Identity(3, 3),
        A(2-1, 1-1) * Eigen::MatrixXd::Identity(3, 3), A(2-1, 2-1) * Eigen::MatrixXd::Identity(3, 3), A(2-1, 3-1) * Eigen::MatrixXd::Identity(3, 3),
        A(3-1, 1-1) * Eigen::MatrixXd::Identity(3, 3), A(3-1, 2-1) * Eigen::MatrixXd::Identity(3, 3), A(3-1, 3-1) * Eigen::MatrixXd::Identity(3, 3);
        // `$\frac{∂²I₅}{∂f²}$` = 2[A₁,₁I₃  A₁,₂I₃  A₁,₃I₃
    //                A₂,₁I₃  A₂,₂I₃  A₂,₃I₃
    //                A₃,₁I₃  A₃,₂I₃  A₃,₃I₃]
        frac_partial_differential_²I₅_partial_differential_f² = 2 * frac_partial_differential_²I₅_partial_differential_f²_0;
        Eigen::MatrixXd mathbfQ_0_0(3, 3);
        mathbfQ_0_0 << a.transpose(),
        Eigen::MatrixXd::Zero(1, 3),
        Eigen::MatrixXd::Zero(1, 3);
        // `$\mathbf{Q}_{0}$` = [a^T
    //                0
    //                0]
        mathbfQ_0 = mathbfQ_0_0;
        Eigen::MatrixXd mathbfQ_1_0(3, 3);
        mathbfQ_1_0 << Eigen::MatrixXd::Zero(1, 3),
        a.transpose(),
        Eigen::MatrixXd::Zero(1, 3);
        // `$\mathbf{Q}_{1}$` = [0
    //                     a^T
    //                0]
        mathbfQ_1 = mathbfQ_1_0;
        Eigen::MatrixXd mathbfQ_2_0(3, 3);
        mathbfQ_2_0 << Eigen::MatrixXd::Zero(1, 3),
        Eigen::MatrixXd::Zero(1, 3),
        a.transpose();
        // `$\mathbf{Q}_{2}$` = [ 0
    //                0
    //                a^T]
        mathbfQ_2 = mathbfQ_2_0;
    }
};

struct Anisotropic2D {
    double lambda_0_comma_1;
    Eigen::MatrixXd frac_partial_differential_²I₅_partial_differential_f²;
    Eigen::MatrixXd mathbfQ_0;
    Eigen::MatrixXd mathbfQ_1;

    Anisotropic2D(
        const Eigen::Matrix<double, 2, 1> & a,
        const Eigen::Matrix<double, 2, 2> & A)
    {
    
        // `$\lambda_{0,1}$`=2||a||_2^2
        lambda_0_comma_1 = 2 * pow((a).lpNorm<2>(), 2);
        Eigen::MatrixXd frac_partial_differential_²I₅_partial_differential_f²_0(4, 4);
        frac_partial_differential_²I₅_partial_differential_f²_0 << A(1-1, 1-1) * Eigen::MatrixXd::Identity(2, 2), A(1-1, 2-1) * Eigen::MatrixXd::Identity(2, 2),
        A(2-1, 1-1) * Eigen::MatrixXd::Identity(2, 2), A(2-1, 2-1) * Eigen::MatrixXd::Identity(2, 2);
        // `$\frac{∂²I₅}{∂f²}$` = 2[A₁,₁I_2  A₁,₂I_2
    //                A₂,₁I_2  A₂,₂I_2]
        frac_partial_differential_²I₅_partial_differential_f² = 2 * frac_partial_differential_²I₅_partial_differential_f²_0;
        Eigen::MatrixXd mathbfQ_0_0(2, 2);
        mathbfQ_0_0 << a.transpose(),
        Eigen::MatrixXd::Zero(1, 2);
        // `$\mathbf{Q}_{0}$` = [a^T
    //                0]
        mathbfQ_0 = mathbfQ_0_0;
        Eigen::MatrixXd mathbfQ_1_0(2, 2);
        mathbfQ_1_0 << Eigen::MatrixXd::Zero(1, 2),
        a.transpose();
        // `$\mathbf{Q}_{1}$` = [0
    //                     a^T]
        mathbfQ_1 = mathbfQ_1_0;
    }
};

