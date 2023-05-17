#pragma once

#include <Eigen/Core>
#include <Eigen/QR>
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <iostream>
#include <vector>
#include <set>
#include <algorithm>
#include <autodiff/reverse/var.hpp>
#include <autodiff/reverse/var/eigen.hpp>
#include <type_traits>

namespace iheartmesh {

using namespace autodiff;

// double/var to var
var to_var(double &param){
	return param;
}

var to_var(var &param){
	return param;
}

Eigen::Matrix<autodiff::var, Eigen::Dynamic, 1> to_var(Eigen::Matrix<double, Eigen::Dynamic, 1> &param){
	Eigen::Matrix<autodiff::var, Eigen::Dynamic, 1> ret(param.rows());
	for (int i = 0; i < param.rows(); ++i)
	{
		ret(i) = param(i);
	}
	return ret;
}

Eigen::Matrix<autodiff::var, Eigen::Dynamic, 1> to_var(Eigen::Matrix<autodiff::var, Eigen::Dynamic, 1> &param){
	return param;
}

Eigen::Matrix<autodiff::var, Eigen::Dynamic, Eigen::Dynamic> to_var(Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic> &param){
	Eigen::Matrix<autodiff::var, Eigen::Dynamic, Eigen::Dynamic> ret(param.rows(), param.cols());
	for (int i = 0; i < param.rows(); ++i)
	{
		for (int j = 0; j < param.cols(); ++j)
		{
			ret(i, j) = param(i, j);
		}
	}
	return ret;
}

Eigen::Matrix<autodiff::var, Eigen::Dynamic, Eigen::Dynamic> to_var(Eigen::Matrix<autodiff::var, Eigen::Dynamic, Eigen::Dynamic> &param){
	return param;
}

std::vector<autodiff::var> to_var(std::vector<double> &param){
	std::vector<autodiff::var> ret(param.size());
	for (int i = 0; i < param.size(); ++i)
	{
		ret[i] = param[i];
	}
	return ret;
}

std::vector<autodiff::var> to_var(std::vector<autodiff::var> &param){
	return param;
}

std::vector<Eigen::Matrix<autodiff::var, Eigen::Dynamic, Eigen::Dynamic>> to_var(std::vector<Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic>> &param){
	std::vector<Eigen::Matrix<autodiff::var, Eigen::Dynamic, Eigen::Dynamic>> ret(param.size());
	for (int i = 0; i < param.size(); ++i)
	{
		ret[i] = to_var(param[i]);
	}
	return ret;
}

std::vector<Eigen::Matrix<autodiff::var, Eigen::Dynamic, Eigen::Dynamic>> to_var(std::vector<Eigen::Matrix<autodiff::var, Eigen::Dynamic, Eigen::Dynamic>> &param){
	return param;
}

std::vector<Eigen::Matrix<autodiff::var, Eigen::Dynamic, 1>> to_var(std::vector<Eigen::Matrix<double, Eigen::Dynamic, 1>> &param){
	std::vector<Eigen::Matrix<autodiff::var, Eigen::Dynamic, 1>> ret(param.size());
	for (int i = 0; i < param.size(); ++i)
	{
		ret[i] = to_var(param[i]);
	}
	return ret;
}

std::vector<Eigen::Matrix<autodiff::var, Eigen::Dynamic, 1>> to_var(std::vector<Eigen::Matrix<autodiff::var, Eigen::Dynamic, 1>> &param){
	return param;
}

// var/double to double
double to_double(autodiff::var &param){
	return param.expr->val;
}

double to_double(double &param){
	return param;
}

Eigen::Matrix<double, Eigen::Dynamic, 1> to_double(Eigen::Matrix<autodiff::var, Eigen::Dynamic, 1> &param){
	Eigen::Matrix<double, Eigen::Dynamic, 1> ret(param.rows());
	for (int i = 0; i < param.rows(); ++i)
	{
		ret(i) = param(i).expr->val;
	}
	return ret;
}

Eigen::Matrix<double, Eigen::Dynamic, 1> to_double(Eigen::Matrix<double, Eigen::Dynamic, 1> &param){
	return param;
}

Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic> to_double(const Eigen::Matrix<autodiff::var, Eigen::Dynamic, Eigen::Dynamic> &param){
	Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic> ret(param.rows(), param.cols());
	for (int i = 0; i < param.rows(); ++i)
	{
		for (int j = 0; j < param.cols(); ++j)
		{
			ret(i, j) = param(i, j).expr->val;
		}
	}
	return ret;
}

Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic> to_double(Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic> &param){
	return param;
}

std::vector<double> to_double(std::vector<autodiff::var> &param){
	std::vector<double> ret(param.size());
	for (int i = 0; i < param.size(); ++i)
	{
		ret[i] = param[i].expr->val;;
	}
	return ret;
}

std::vector<double> to_double(std::vector<double> &param){
	return param;
}

std::vector<Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic>> to_double(std::vector<Eigen::Matrix<autodiff::var, Eigen::Dynamic, Eigen::Dynamic>> &param){
	std::vector<Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic>> ret(param.size());
	for (int i = 0; i < param.size(); ++i)
	{
		ret[i] = to_double(param[i]);
	}
	return ret;
}

std::vector<Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic>> to_double(std::vector<Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic>> &param){
	return param;
}

std::vector<Eigen::Matrix<double, Eigen::Dynamic, 1>> to_double(std::vector<Eigen::Matrix<autodiff::var, Eigen::Dynamic, 1>> &param){
	std::vector<Eigen::Matrix<double, Eigen::Dynamic, 1>> ret(param.size());
	for (int i = 0; i < param.size(); ++i)
	{
		ret[i] = to_double(param[i]);
	}
	return ret;
}

std::vector<Eigen::Matrix<double, Eigen::Dynamic, 1>> to_double(std::vector<Eigen::Matrix<double, Eigen::Dynamic, 1>> &param){
	return param;
}

// template 
template<class DT>
DT to_dt(double &param){
	if constexpr (std::is_same_v<DT, autodiff::var>)
	{
		std::cout<<"var is"<<std::endl;
		return to_var(param);
	}
	return to_double(param);
}

template<class DT>
DT to_dt(autodiff::var &param){
	if constexpr (std::is_same_v<DT, autodiff::var>)
	{
		std::cout<<"var is"<<std::endl;
		return to_var(param);
	}
	return to_double(param);
}

}
