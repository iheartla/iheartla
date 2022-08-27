#pragma once
#include <Eigen/Core>
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <iostream>
#include <set>

struct Generic {
    Eigen::VectorXd x_p;
    Eigen::VectorXd v_p;
    Eigen::MatrixXd M;

    Generic(
        const Eigen::Matrix<double, 2, 2> & J,
        const double & x,
        const double & y,
        const double & u,
        const double & v)
    {
    
        Eigen::VectorXd x_p_0(2);
        x_p_0 << -y, x;
        // `$x_p$` = (-y, x)
        x_p = x_p_0;
        Eigen::VectorXd v_p_0(2);
        v_p_0 << -v, u;
        // `$v_p$` = (-v, u)
        v_p = v_p_0;
        Eigen::MatrixXd M_0(2, 6);
        M_0 << -J * x_p + v_p, J, x_p, Eigen::MatrixXd::Identity(2, 2);
        // M=[-J`$x_p$`+`$v_p$`  J  `$x_p$`  I_2]
        M = M_0;
    }
};

