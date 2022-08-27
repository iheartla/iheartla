#pragma once
#include <Eigen/Core>
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <iostream>
#include <set>

struct Stable {
    double α;
    double J;
    Eigen::Matrix<double, 3, 3> PF;
    Eigen::MatrixXd fracpartialJpartialF;

    Stable(
        const Eigen::Matrix<double, 3, 3> & F,
        const double & μ,
        const double & I_C,
        const double & λ,
        const Eigen::Matrix<double, 3, 1> & f_0,
        const Eigen::Matrix<double, 3, 1> & f_1,
        const Eigen::Matrix<double, 3, 1> & f_2)
    {
    
        // α = 1 + μ/λ - μ/(4λ)
        α = 1 + μ / double(λ) - μ / double((4 * λ));
        // J =`$f_0$`⋅(`$f_1$`×`$f_2$`)
        J = (f_0).dot(((f_1).cross(f_2)));
        Eigen::MatrixXd fracpartialJpartialF_0(3, 3);
        fracpartialJpartialF_0 << (f_1).cross(f_2), (f_2).cross(f_0), (f_0).cross(f_1);
        // `$\frac{\partial J}{\partial F}$` = [`$f_1$`×`$f_2$` `$f_2$`×`$f_0$` `$f_0$`×`$f_1$`]
        fracpartialJpartialF = fracpartialJpartialF_0;
        // `$P(F)$` = μ(1-1/(`$I_C$`+1))F + λ(J- α)`$\frac{\partial J}{\partial F}$`
        PF = μ * (1 - 1 / double((I_C + 1))) * F + λ * (J - α) * fracpartialJpartialF;
    }
};

