#pragma once
#include <Eigen/Core>
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <iostream>
#include <set>

struct judder {
    double J;
    double F_a;
    double F_b;
    double L;
    double a;
    double b;
    double F;
    double CFF(
        const double & L)
    {
        return a * log(L) + b;    
    }
    double α(
        const double & F)
    {
        return 1 / double(F);    
    }
    double β(
        const double & L)
    {
        return log10(L);    
    }
    judder(
        const double & F,
        const double & L,
        const double & S,
        const std::function<double(double, double, double)> & P,
        const double & a,
        const double & b,
        const double & M,
        const double & L_a,
        const double & L_b)
    {
    
        this->L = L;
        this->a = a;
        this->b = b;
        this->F = F;
        // `$F_a$` = M⋅ CFF(`$L_a$`)
        F_a = M * CFF(L_a);
        // `$F_b$` = M⋅ CFF(`$L_b$`)
        F_b = M * CFF(L_b);
        // J = P(α(F), β(L), S)
        J = P(α(F), β(L), S);
    }
};

struct error {
    double E;

    error(
        const Eigen::VectorXd & O,
        const Eigen::VectorXd & M)
    {
        const long N = O.size();
        assert( M.size() == N );
        double sum_0 = 0;
        for(int i=1; i<=O.size(); i++){
            sum_0 += abs(log(O[i-1]) - log(M[i-1])) / double(log(O[i-1]));
        }
        // E = sum_i |log(O_i) - log(M_i)|/log(O_i)
        E = sum_0;
    }
};

struct third {
    double L_b;

    third(
        const double & a,
        const double & b,
        const double & F_b,
        const double & F_a,
        const double & L_a)
    {
    
        // `$L_b$` = 10^((a `$F_b$`log((`$L_a$`))+b(`$F_b$`-`$F_a$`))/(a`$F_a$`))
        L_b = pow(10, ((a * F_b * log((L_a)) + b * (F_b - F_a)) / double((a * F_a))));
    }
};

