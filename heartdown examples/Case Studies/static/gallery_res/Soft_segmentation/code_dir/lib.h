#pragma once
#include <Eigen/Core>
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <iostream>
#include <set>

struct soft {
    double F_S;

    soft(
        const std::vector<std::function<double(Eigen::Matrix<double, 3, 1>)>> & D,
        const std::vector<Eigen::Matrix<double, 3, 1>> & boldsymbolu,
        const double & σ,
        const std::vector<double> & α)
    {
        const long dim_0 = α.size();
        assert( D.size() == dim_0 );
        assert( boldsymbolu.size() == dim_0 );
        double sum_0 = 0;
        for(int i=1; i<=boldsymbolu.size(); i++){
            sum_0 += α.at(i-1) * D.at(i-1)(boldsymbolu.at(i-1));
        }
        double sum_1 = 0;
        for(int i=1; i<=α.size(); i++){
            sum_1 += α.at(i-1);
        }
        double sum_2 = 0;
        for(int i=1; i<=α.size(); i++){
            sum_2 += pow(α.at(i-1), 2);
        }
        // `$F_S$` = sum_i α_i D_i(`$\boldsymbol{u}$`_i) + σ((sum_i α_i)/(sum_i α_i^2) - 1)
        F_S = sum_0 + σ * ((sum_1) / double((sum_2)) - 1);
    }
};

