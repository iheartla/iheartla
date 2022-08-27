#pragma once
#include <Eigen/Core>
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <iostream>
#include <set>

struct eccentricity {
    int 𝑙_0;
    Eigen::VectorXd q;
    std::function<double(double, double)> m;
    double 𝑓_𝑠₀;
    Eigen::Matrix<double, 10, 1> 𝑝;
    double a;
    double 𝑔(
        const Eigen::Matrix<double, 2, 1> & x,
        const Eigen::Matrix<double, 2, 1> & x_0,
        const double & 𝜃,
        const double & 𝜎,
        const double & 𝑓_𝑠)
    {
        Eigen::VectorXd 𝑔_1(2);
        𝑔_1 << cos(𝜃), sin(𝜃);
        return exp(-pow((x - x_0).lpNorm<2>(), 2) / double((2 * pow(𝜎, 2)))) * cos((2 * M_PI * 𝑓_𝑠 * x).dot(𝑔_1));    
    }
    double 𝜏(
        const double & 𝑓_𝑠)
    {
        return m(log10(𝑓_𝑠) - log10(𝑓_𝑠₀), 0);    
    }
    double 𝜁(
        const double & 𝑓_𝑠)
    {
        return exp(𝑝[10-1] * 𝜏(𝑓_𝑠)) - 1;    
    }
    double Ψ(
        const double & 𝑒,
        const double & 𝑓_𝑠)
    {
        return m(0, 𝑝[1-1] * pow(𝜏(𝑓_𝑠), 2) + 𝑝[2-1] * 𝜏(𝑓_𝑠) + 𝑝[3-1] + (𝑝[4-1] * pow(𝜏(𝑓_𝑠), 2) + 𝑝[5-1] * 𝜏(𝑓_𝑠) + 𝑝[6-1]) * 𝜁(𝑓_𝑠) * 𝑒 + (𝑝[7-1] * pow(𝜏(𝑓_𝑠), 2) + 𝑝[8-1] * 𝜏(𝑓_𝑠) + 𝑝[9-1]) * 𝜁(𝑓_𝑠) * pow(𝑒, 2));    
    }
    double 𝐴(
        const double & 𝑒)
    {
        return log(64) * 2.3 / double((0.106 * (𝑒 + 2.3)));    
    }
    double 𝑑(
        const double & 𝐿)
    {
        return 7.75 - 5.75 * (pow((𝐿 * a / double(846)), 0.41) / double((pow((𝐿 * a / double(846)), 0.41) + 2)));    
    }
    double 𝑙(
        const double & 𝐿)
    {
        return M_PI * pow(𝑑(𝐿), 2) / double(4) * 𝐿;    
    }
    double 𝑠(
        const double & 𝑒,
        const double & 𝑓_𝑠)
    {
        return 𝜁(𝑓_𝑠) * (q[1-1] * pow(𝑒, 2) + q[2-1] * 𝑒) + q[3-1];    
    }
    double hatΨ(
        const double & 𝑒,
        const double & 𝑓_𝑠,
        const double & 𝐿)
    {
        return (𝑠(𝑒, 𝑓_𝑠) * (log10(𝑙(𝐿) / double(𝑙_0))) + 1) * Ψ(𝑒, 𝑓_𝑠);    
    }
    eccentricity(
        const std::function<double(double, double)> & m,
        const Eigen::Matrix<double, 10, 1> & 𝑝,
        const double & 𝑓_𝑠₀,
        const double & a)
    {
    
        this->m = m;
        this->𝑓_𝑠₀ = 𝑓_𝑠₀;
        this->𝑝 = 𝑝;
        this->a = a;
        // `$𝑙_0$` = 1488
        𝑙_0 = 1488;
        Eigen::VectorXd q_0(3);
        q_0 << 5.71 * pow(10, (-6)), -1.78 * pow(10, (-4)), 0.204;
        // q = (5.71 ⋅ 10^(-6), -1.78 ⋅ 10^(-4), 0.204)
        q = q_0;
    }
};

