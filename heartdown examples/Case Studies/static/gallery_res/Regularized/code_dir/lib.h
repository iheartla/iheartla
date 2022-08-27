#pragma once
#include <Eigen/Core>
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <iostream>
#include <set>

struct Regularized {

    double a;
    double b;
    double r;
    Eigen::Matrix<double, 3, 1> boldsymbolf;
    double r_ε;
    double ε;
    Eigen::Matrix<double, 3, 3> boldsymbolF;
    double s;
    Eigen::Matrix<double, 3, 1> boldsymbolu(
        const Eigen::Matrix<double, 3, 1> & boldsymbolr)
    {
        return ((a - b) / double(r) * Eigen::MatrixXd::Identity(3, 3) + b / double(pow(r, 3)) * boldsymbolr * boldsymbolr.transpose()) * boldsymbolf;    
    }
    double rho_ε(
        const Eigen::Matrix<double, 3, 1> & boldsymbolr)
    {
        return (15 * pow(r_ε, 4) / double((8 * M_PI)) + 1 / double(pow(r_ε, 7)));    
    }
    Eigen::Matrix<double, 3, 1> boldsymbolu_ε(
        const Eigen::Matrix<double, 3, 1> & boldsymbolr)
    {
        return ((a - b) / double(r_ε) * Eigen::MatrixXd::Identity(3, 3) + b / double(pow(r_ε, 3)) * boldsymbolr * boldsymbolr.transpose() + a * pow(ε, 2) / double((2 * pow(r_ε, 3))) * Eigen::MatrixXd::Identity(3, 3)) * boldsymbolf;    
    }
    Eigen::Matrix<double, 3, 1> tildeboldsymbolu_ε(
        const Eigen::Matrix<double, 3, 1> & boldsymbolr)
    {
        return -a * (1 / double(pow(r_ε, 3)) + 3 * pow(ε, 2) / double((2 * pow(r_ε, 5)))) * boldsymbolF * boldsymbolr + b * (1 / double(pow(r_ε, 3)) * (boldsymbolF + boldsymbolF.transpose() + (boldsymbolF).trace() * Eigen::MatrixXd::Identity(3, 3)) - 3 / double(pow(r_ε, 5)) * ((double)(boldsymbolr.transpose() * boldsymbolF * boldsymbolr)) * Eigen::MatrixXd::Identity(3, 3)) * boldsymbolr;    
    }
    Eigen::Matrix<double, 3, 1> boldsymbolt_ε(
        const Eigen::Matrix<double, 3, 1> & boldsymbolr)
    {
        return -a * (1 / double(pow(r_ε, 3)) + 3 * pow(ε, 2) / double((2 * pow(r_ε, 5)))) * boldsymbolF * boldsymbolr;    
    }
    Eigen::Matrix<double, 3, 1> boldsymbols_ε(
        const Eigen::Matrix<double, 3, 1> & boldsymbolr)
    {
        return (2 * b - a) * (1 / double(pow(r_ε, 3)) + 3 * pow(ε, 2) / double((2 * pow(r_ε, 5)))) * (s * boldsymbolr);    
    }
    Eigen::Matrix<double, 3, 1> boldsymbolp_ε(
        const Eigen::Matrix<double, 3, 1> & boldsymbolr)
    {
        return (2 * b - a) / double(pow(r_ε, 3)) * boldsymbolF * boldsymbolr - 3 / double((2 * pow(r_ε, 5))) * (2 * b * ((double)(boldsymbolr.transpose() * boldsymbolF * boldsymbolr)) * Eigen::MatrixXd::Identity(3, 3) + a * pow(ε, 2) * boldsymbolF) * boldsymbolr;    
    }
    Regularized(
        const double & r,
        const Eigen::Matrix<double, 3, 1> & boldsymbolf,
        const double & s,
        const Eigen::Matrix<double, 3, 3> & boldsymbolF,
        const double & r_ε,
        const double & a,
        const double & b,
        const double & ε)
    {
    
        this->a = a;
        this->b = b;
        this->r = r;
        this->boldsymbolf = boldsymbolf;
        this->r_ε = r_ε;
        this->ε = ε;
        this->boldsymbolF = boldsymbolF;
        this->s = s;
    
    }
};

