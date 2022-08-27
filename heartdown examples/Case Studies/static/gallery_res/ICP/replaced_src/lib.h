#pragma once
#include <Eigen/Core>
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <iostream>
#include <set>

struct icp {
    Eigen::Matrix<double, 3, 1> ã;
    std::vector<Eigen::Matrix<double, 3, 1>> n;
    Eigen::Matrix<double, 3, 1> t̃;
    std::vector<Eigen::Matrix<double, 3, 1>> p̃;
    std::vector<Eigen::Matrix<double, 3, 1>> q̃;
    double varepsilon_point;
    double varepsilon_plane;
    double varepsilon_symmRN;
    double varepsilon_symm;
    Eigen::Matrix<double, 4, 4> S;
    double varepsilon_twoplane;

    icp(
        const Eigen::Matrix<double, 3, 3> & R,
        const Eigen::Matrix<double, 3, 1> & a,
        const double & θ,
        const std::vector<Eigen::Matrix<double, 3, 1>> & p,
        const std::vector<Eigen::Matrix<double, 3, 1>> & q,
        const std::vector<Eigen::Matrix<double, 3, 1>> & n_q,
        const std::vector<Eigen::Matrix<double, 3, 1>> & n_p,
        const Eigen::Matrix<double, 3, 1> & t,
        const Eigen::Matrix<double, 3, 1> & barq,
        const Eigen::Matrix<double, 3, 1> & barp,
        const std::function<Eigen::Matrix<double, 4, 4>(Eigen::Matrix<double, 3, 1>)> & trans,
        const std::function<Eigen::Matrix<double, 4, 4>(double, Eigen::Matrix<double, 3, 1>)> & rot)
    {
        const long dim_0 = p.size();
        assert( q.size() == dim_0 );
        assert( n_q.size() == dim_0 );
        assert( n_p.size() == dim_0 );
        // ã = a tan(θ)
        ã = a * tan(θ);
        // n_i = `$n_q$`_i + `$n_p$`_i
        n.resize(dim_0);
        for( int i=1; i<=dim_0; i++){
            n.at(i-1) = n_q.at(i-1) + n_p.at(i-1);
        }
        // t̃ = t/cos(θ)
        t̃ = t / double(cos(θ));
        // p̃_i = p_i - `$\bar{p}$` 
        p̃.resize(dim_0);
        for( int i=1; i<=dim_0; i++){
            p̃.at(i-1) = p.at(i-1) - barp;
        }
        // q̃_i = q_i - `$\bar{q}$` 
        q̃.resize(dim_0);
        for( int i=1; i<=dim_0; i++){
            q̃.at(i-1) = q.at(i-1) - barq;
        }
        double sum_0 = 0;
        for(int i=1; i<=q.size(); i++){
            sum_0 += (R * p.at(i-1) + t - q.at(i-1)).lpNorm<2>();
        }
        // `$\varepsilon_{point}$` = ∑_i ||R p_i + t - q_i||
        varepsilon_point = sum_0;
        double sum_1 = 0;
        for(int i=1; i<=q.size(); i++){
            sum_1 += pow((((R * p.at(i-1) + t - q.at(i-1))).dot(n_q.at(i-1))), 2);
        }
        // `$\varepsilon_{plane}$` = ∑_i ((R p_i + t - q_i) ⋅ `$n_q$`_i)^2
        varepsilon_plane = sum_1;
        double sum_2 = 0;
        for(int i=1; i<=q.size(); i++){
            sum_2 += pow((((R * p.at(i-1) + R.colPivHouseholderQr().solve(q.at(i-1)) + t)).dot((R * n_p.at(i-1) + R.colPivHouseholderQr().solve(n_q.at(i-1))))), 2);
        }
        // `$\varepsilon_{symm-RN}$` = ∑_i ((R p_i + R⁻¹ q_i + t) ⋅ (R`$n_p$`_i + R⁻¹`$n_q$`_i))^2
        varepsilon_symmRN = sum_2;
        double sum_3 = 0;
        for(int i=1; i<=q.size(); i++){
            sum_3 += pow(cos(θ), 2) * pow((((p.at(i-1) - q.at(i-1))).dot(n.at(i-1)) + ((((p.at(i-1) + q.at(i-1))).cross(n.at(i-1)))).dot(ã) + (n.at(i-1)).dot(t̃)), 2);
        }
        // `$\varepsilon_{symm}$` = ∑_i cos²(θ)((p_i - q_i)⋅n_i +((p_i+q_i)×n_i)⋅ã+n_i⋅t̃)² 
        varepsilon_symm = sum_3;
        // S = trans(`$\bar{q}$`) ⋅ rot(θ, ã/||ã||) ⋅trans(t̃ cos(θ)) ⋅rot(θ, ã/||ã||)⋅ trans(-`$\bar{p}$`)
        S = trans(barq) * rot(θ, ã / double((ã).lpNorm<2>())) * trans(t̃ * cos(θ)) * rot(θ, ã / double((ã).lpNorm<2>())) * trans(-barp);
        double sum_4 = 0;
        for(int i=1; i<=p.size(); i++){
            sum_4 += (pow((((R * p.at(i-1) + R.colPivHouseholderQr().solve(q.at(i-1)) + t)).dot((R * n_p.at(i-1)))), 2) + pow((((R * p.at(i-1) + R.colPivHouseholderQr().solve(q.at(i-1)) + t)).dot((R.colPivHouseholderQr().solve(n_q.at(i-1))))), 2));
        }
        // `$\varepsilon_{two-plane}$` = ∑_i(((R p_i + R⁻¹ q_i + t) ⋅ (R `$n_p$`_i))^2 + ((R p_i + R⁻¹ q_i + t) ⋅ (R⁻¹`$n_q$`_i))^2)
        varepsilon_twoplane = sum_4;
    }
};

