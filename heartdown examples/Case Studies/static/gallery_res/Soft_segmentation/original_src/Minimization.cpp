#include "Minimization.h"

using InputParams = std::tuple<std::vector<cv::Vec3d>, std::vector<cv::Matx33d>, cv::Vec4d, cv::Vec3d, double,
	bool, std::vector<double>, std::vector<double>>; //mg added this last term to store gt alphas for refinement


/**
 * Print vector v in cout
 */
void print_v(std::vector<double> v){
	for(double d : v){
		std::cout << d << " ";
	}
	std::cout << std::endl;
}

/**
 * Energy function of vector v. See Eq. 4 in "Unmixing-Based Soft Color Segmentation for Image Manipulation"
 * v: Input vector
 * means: mean values of color model
 * covs: inverse covariances of color model
 * sparse: true if the sparsity part should be included
 */
double energy(std::vector<double> v, std::vector<cv::Vec3d> &means, std::vector<cv::Matx33d> &covs, bool sparse){
	int n = means.size();
	double energy = 0;
	double dist, c1, c2, c3, alpha, sparsity;
	cv::Vec3d color;
	std::vector<double> alphas;
	for(size_t i = 0; i < n; i++){
		alpha = v.at(i);
		alphas.push_back(alpha);
		c1 = v.at(3*i+n);
		c2 = v.at(3*i+n+1);
		c3 = v.at(3*i+n+2);
		color = cv::Vec3d(c1,c2,c3);
		dist = pow(cv::Mahalanobis(color, means.at(i), (covs.at(i)).inv()),2);
		energy += alpha * dist;
	}
	if(sparse){
		double sum_alpha = 0.0;
		double sum_squared = 0.0;
		for(auto& n : alphas){
			sum_alpha += n;
			sum_squared += pow(n,2);
		}
		if(sum_squared == 0)
		{
			sparsity = 500;
		}
		else{
			sparsity = constants::sigma * (((sum_alpha)/(sum_squared)) - 1);
		}
	} else {
		sparsity = 0;
	}
	return energy + sparsity;
}

/**
 * Constraint vector g in the unmixing step. See Eq. 4 in "Interactive High-Quality Green-Screen Keying via Color Unmixing"
 * v: Input vector
 * n: number of colors in color model
 * color: Color of pixel in the input image
 */
cv::Vec4d g(std::vector<double> &v, int n, cv::Vec3d color){
	double g1 = 0, g2 = 0, g3 = 0, g4 = 0;
	for(size_t i = 0; i < n; i++){
		g1 += v.at(i)*v.at(3*i+n);
		g2 += v.at(i)*v.at(3*i+n+1);
		g3 += v.at(i)*v.at(3*i+n+2);
		g4 += v.at(i);
	}
	return cv::Vec4d(pow(g1-color.val[0],2),pow(g2-color.val[1],2),pow(g3-color.val[2],2),pow(g4-1,2));
}

/**
 * Partial derivative of g in respect to alpha
 * v: minimization vector
 * n: number of layers
 * color: color of pixel
 * k: index of alpha value for this partial derivative
 */
cv::Vec4d dg_a(std::vector<double> &v, int n, cv::Vec3d color, int k){//mg checked - seems correct
	double g1 = 0, g2 = 0, g3 = 0, g4 = 0;
	for(size_t i = 0; i < n; i++){
		g1 += v.at(i)*v.at(3*i+n);//r
		g2 += v.at(i)*v.at(3*i+n+1);//g
		g3 += v.at(i)*v.at(3*i+n+2);//b
		g4 += v.at(i);//alpha
	}
	g1 = 2*(g1-color.val[0])*v.at(3*k+n);
	g2 = 2*(g2-color.val[1])*v.at(3*k+n+1);
	g3 = 2*(g3-color.val[2])*v.at(3*k+n+2);
	g4 = 2*(g4-1);
	return cv::Vec4d(g1,g2,g3,g4);
}

/**
 * Partial derivative of g in respect to u. Note that this function calculates the partial derivatives for all 3 RGB values
 * of u. In the gradient of the minimization function, only the partial derivative of one of those values at a time is needed.
 */
cv::Vec4d dg_u(std::vector<double> &v, int n, cv::Vec3d color, int k){
	double g1 = 0, g2 = 0, g3 = 0, g4 = 0;
	for(size_t i = 0; i < n; i++){
		g1 += v.at(i)*v.at(3*i+n);
		g2 += v.at(i)*v.at(3*i+n+1);
		g3 += v.at(i)*v.at(3*i+n+2);
	}
	g1 = 2*(g1-color.val[0])*v.at(k);
	g2 = 2*(g2-color.val[1])*v.at(k);
	g3 = 2*(g3-color.val[2])*v.at(k);
	return cv::Vec4d(g1,g2,g3,g4);
}

/**
 * Constraint vector g in the refinement step. See Eq. 6 in "Unmixing based soft color segmentation for image manipulation"
 * v: Input vector
 * n: number of colors in color model
 * color: Color of pixel in the input image
 * gt_alpha : the alpha values estimated using filtering step
 */
cv::Vec4d g_refine(std::vector<double> &v, int n, cv::Vec3d color, std::vector<double> gt_alphas){
	double g1 = 0, g2 = 0, g3 = 0, g4 = 0;
	for(size_t i = 0; i < n; i++){
		g1 += v.at(i)*v.at(3*i+n);
		g2 += v.at(i)*v.at(3*i+n+1);
		g3 += v.at(i)*v.at(3*i+n+2);
		g4 += (v.at(i) - gt_alphas.at(i))*(v.at(i) - gt_alphas.at(i));
	}
	return cv::Vec4d(pow(g1-color.val[0],2),pow(g2-color.val[1],2),pow(g3-color.val[2],2),pow(g4,2));
}

/**
 * Partial derivative of g_refine in respect to alpha
 * v: minimization vector
 * n: number of layers
 * color: color of pixel
 * k: index of alpha value for this partial derivative
 * gt_alpha : the alpha values estimated using filtering step
 */
cv::Vec4d dg_refine_a(std::vector<double> &v, int n, cv::Vec3d color, int k, std::vector<double> gt_alphas){
	double g1 = 0, g2 = 0, g3 = 0, g4 = 0;
	for(size_t i = 0; i < n; i++){
		g1 += v.at(i)*v.at(3*i+n);//r
		g2 += v.at(i)*v.at(3*i+n+1);//g
		g3 += v.at(i)*v.at(3*i+n+2);//b
		//g4 += v.at(i);//alpha
	}
	g1 = 2*(g1-color.val[0])*v.at(3*k+n);
	g2 = 2*(g2-color.val[1])*v.at(3*k+n+1);
	g3 = 2*(g3-color.val[2])*v.at(3*k+n+2);
	g4 = 2*( v.at(k) - gt_alphas.at(k)); 
	return cv::Vec4d(g1,g2,g3,g4);
}



/**
 * Partial derivative of the Mahalanobis distance in respect to u
 */
double d_maha(cv::Vec3d mean, cv::Matx33d cov, cv::Vec3d u, int i){ //the square has been removed from the mahalanobis distance so we don't need to deal with sqrt in derivative
    cv::Matx33d cov_inv = cov.inv();
	cv::Vec3d df_m;
	double df_i;
	df_m = cv::Vec3d(2*cov_inv*(cv::Mat(u - mean)));
	df_i = df_m.val[i];
    //return 2*(u.val[i]-mean.val[i])*(cov_inv.col(i).val[0]+cov_inv.col(i).val[1]+cov_inv.col(i).val[2]);//mg checked, 
	return df_i;
	}

/**
 * Minimization function for the unmixing step. See Line 1 in Algorithm 1 in
 * "Interactive High-Quality Green-Screen Keying via Color Unmixing"
 */
double min_f(std::vector<double> &v, void* params){
	InputParams* param = static_cast<InputParams*>(params);
	std::vector<cv::Vec3d> means = std::get<0>((*param));
	std::vector<cv::Matx33d> covs = std::get<1>((*param));
	cv::Vec4d lambda = std::get<2>((*param));
	cv::Vec3d color = std::get<3>((*param));
	double p = std::get<4>((*param));
	bool s =std:: get<5>((*param));
	cv::Vec4d g_vec = g(v, means.size(), color); //constraint vector 
	return energy(v, means, covs, s) + g_vec.dot(lambda) + 0.5*p*pow(cv::norm(g_vec, cv::NORM_L2),2);
}

/**
 * Gradient of the minimization function for the unmixing step. Returns a vector where each element is the partial
 * derivative of input vector v in respect to that element (#Jo: rather of energy(v) in repect to that element)
 */
std::vector<double> min_df(std::vector<double> &v, void* params){
	InputParams* param = static_cast<InputParams*>(params);
	std::vector<cv::Vec3d> means = std::get<0>((*param));
	std::vector<cv::Matx33d> covs = std::get<1>((*param));
	cv::Vec4d lambda = std::get<2>((*param));
	cv::Vec3d color = std::get<3>((*param));
	double p = std::get<4>((*param));
	bool s = std::get<5>((*param));
	int n = means.size();
	std::vector<double> df(4*n);
	double dist, sparse, alpha, dot_prod, g_norm, u1, u2, u3, grad_a, grad_u1, grad_u2, grad_u3;
	double sum_alpha = 0.0, sum_squared = 0.0, sum_u1 = 0.0, sum_u2 = 0.0, sum_u3 = 0.0;
	cv::Vec3d u;
	for(size_t i = 0; i < n; i++){
		alpha = v.at(i);
		u1 = v.at(3*i+n);
		u2 = v.at(3*i+n+1);
		u3 = v.at(3*i+n+2);
		sum_alpha += alpha;
		sum_squared += pow(alpha,2);
		sum_u1 += alpha*u1; //B_i * alpha_i
		sum_u2 += alpha*u2; //G_i * alpha_i
		sum_u3 += alpha*u3; //R_i * alpha_i
	}
	for(size_t i = 0; i < n; i++){
		alpha = v.at(i);
		u1 = v.at(3*i+n);
		u2 = v.at(3*i+n+1);
		u3 = v.at(3*i+n+2);
		u = cv::Vec3d(u1,u2,u3);
		//Alphas
		dist = pow(cv::Mahalanobis(u, means.at(i), (covs.at(i)).inv()),2);
		if(s){
			if(sum_squared < 0.0000000001){
				sparse = 0;
			}else{
				sparse = (constants::sigma*sum_squared-(constants::sigma*sum_alpha*2*alpha))/(pow(sum_squared,2));
			}
		} else {
			sparse = 0;
		}
		dot_prod = lambda.dot(dg_a(v, means.size(), color, i));
		g_norm = 0.5*p* (4*pow(sum_u1-color.val[0],3)*u1
					+ 4*pow(sum_u2-color.val[1],3)*u2 
					+ 4*pow(sum_u3-color.val[2],3)*u3
					+ 4*pow(sum_alpha-1,3));
		grad_a = dist+sparse+dot_prod+g_norm;
		df.at(i) = grad_a;
		//Colors
		//u1
		dist = alpha*d_maha(means.at(i),covs.at(i),u,0);
		dot_prod = lambda.dot(cv::Vec4d(dg_u(v, means.size(), color, i).val[0],0,0,0));
		g_norm = 0.5*p*4*pow(sum_u1-color.val[0],3)*alpha;
		grad_u1 = dist+dot_prod+g_norm;
		df.at(3*i+n) = grad_u1;
		//u2
		dist = alpha*d_maha(means.at(i),covs.at(i),u,1);
		dot_prod = lambda.dot(cv::Vec4d(0,dg_u(v, means.size(), color, i).val[1],0,0));
		g_norm = 0.5*p*4*pow(sum_u2-color.val[1],3)*alpha;
		grad_u2 = dist+dot_prod+g_norm;
		df.at(3*i+n+1) = grad_u2;
		//u3
		dist = alpha*d_maha(means.at(i),covs.at(i),u,2);
		dot_prod = lambda.dot(cv::Vec4d(0,0,dg_u(v, means.size(), color, i).val[2],0));
		g_norm = 0.5*p*4*pow(sum_u3-color.val[2],3)*alpha;
		grad_u3 = dist+dot_prod+g_norm;
		df.at(3*i+n+2) = grad_u3;
	}
	// Apply box constraints
	for(size_t i = 0; i < 4*n; i++){
		if((df.at(i) < 0 && v.at(i) >= 1) || (df.at(i) > 0 && v.at(i) <= 0)){
			df.at(i) = 0;
		}
	}
	return df;
}



/**
 * mg - Minimization function for the color refinement step. See equation (4) and(6) of unmixing paper
 * 
 */
double min_refine_f(std::vector<double> &v, void* params){
	InputParams* param = static_cast<InputParams*>(params);
	std::vector<cv::Vec3d> means = std::get<0>((*param));
	std::vector<cv::Matx33d> covs = std::get<1>((*param));
	cv::Vec4d lambda = std::get<2>((*param));
	cv::Vec3d color = std::get<3>((*param));
	double p = std::get<4>((*param));
	bool s = 0;
	std::vector<double> gt_alpha = std::get<7>((*param));
	cv::Vec4d g_vec = g_refine(v, means.size(), color, gt_alpha); //constraint vector
	return energy(v, means, covs, s) + g_vec.dot(lambda) + 0.5*p*pow(cv::norm(g_vec, cv::NORM_L2),2);
}

/**
 * Gradient of the minimization function for the color refinement step. Returns a vector where each element is the partial
 * derivative of input vector v in respect to that element.
 */
std::vector<double> min_refine_df(std::vector<double> &v, void* params){
	InputParams* param = static_cast<InputParams*>(params);
	std::vector<cv::Vec3d> means = std::get<0>((*param));
	std::vector<cv::Matx33d> covs = std::get<1>((*param));
	cv::Vec4d lambda = std::get<2>((*param));
	cv::Vec3d color = std::get<3>((*param));
	double p = std::get<4>((*param));
	bool s = std::get<5>((*param));
	std::vector<double> gt_alpha = std::get<7>((*param));
	int n = means.size();
	std::vector<double> df(4*n);
	double dist, sparse, alpha, alphai_gt, dot_prod, g_norm, u1, u2, u3, grad_a, grad_u1, grad_u2, grad_u3;
	double diff_gt_alpha = 0.0, sum_squared = 0.0, sum_u1 = 0.0, sum_u2 = 0.0, sum_u3 = 0.0;
	cv::Vec3d u;
	for(size_t i = 0; i < n; i++){
		alpha = v.at(i);
		alphai_gt = gt_alpha.at(i);
		u1 = v.at(3*i+n);
		u2 = v.at(3*i+n+1);
		u3 = v.at(3*i+n+2);
		diff_gt_alpha += pow((alpha - alphai_gt),2);
		sum_squared += pow(alpha,2);
		sum_u1 += alpha*u1; //B_i * alpha_i
		sum_u2 += alpha*u2; //G_i * alpha_i
		sum_u3 += alpha*u3; //R_i * alpha_i
	}
	for(size_t i = 0; i < n; i++){
		alpha = v.at(i);
		alphai_gt = gt_alpha.at(i);
		u1 = v.at(3*i+n);
		u2 = v.at(3*i+n+1);
		u3 = v.at(3*i+n+2);
		u = cv::Vec3d(u1,u2,u3);
		//Alphas - mg changed this so that the alpha values are not estimated in the final step - the filtered alphas are used instead - if they change, they may not add to 1 after optimisation.
		//these are the rows that were removed:
		/*************************
		//dist = pow(cv::Mahalanobis(u, means.at(i), (covs.at(i)).inv()),2);
		//sparse = 0;
		//dot_prod = lambda.dot(dg_refine_a(v, means.size(), color, i, gt_alpha));
		//g_norm = 0.5*p* (4*pow(sum_u1-color.val[0],3)*u1
		//			+ 4*pow(sum_u2-color.val[1],3)*u2 
		//			+ 4*pow(sum_u3-color.val[2],3)*u3
		//			+ 4*(diff_gt_alpha)*(alpha - alphai_gt)); //mg checked
		//grad_a = dist+sparse+dot_prod+g_norm;
		//df.at(i) = grad_a;
		/****************************/
		df.at(i) = 0;
		//Colors
		//u1
		dist = alpha*d_maha(means.at(i),covs.at(i),u,0);
		dot_prod = lambda.dot(cv::Vec4d(dg_u(v, means.size(), color, i).val[0],0,0,0));
		g_norm = 0.5*p*4*pow(sum_u1-color.val[0],3)*alpha;
		grad_u1 = dist+dot_prod+g_norm;
		df.at(3*i+n) = grad_u1;
		//u2
		dist = alpha*d_maha(means.at(i),covs.at(i),u,1);
		dot_prod = lambda.dot(cv::Vec4d(0,dg_u(v, means.size(), color, i).val[1],0,0));
		g_norm = 0.5*p*4*pow(sum_u2-color.val[1],3)*alpha;
		grad_u2 = dist+dot_prod+g_norm;
		df.at(3*i+n+1) = grad_u2;
		//u3
		dist = alpha*d_maha(means.at(i),covs.at(i),u,2);
		dot_prod = lambda.dot(cv::Vec4d(0,0,dg_u(v, means.size(), color, i).val[2],0));
		g_norm = 0.5*p*4*pow(sum_u3-color.val[2],3)*alpha;
		grad_u3 = dist+dot_prod+g_norm;
		df.at(3*i+n+2) = grad_u3;
	}
	// Apply box constraints
	for(size_t i = 0; i < 4*n; i++){
		if((df.at(i) < 0 && v.at(i) >= 1) || (df.at(i) > 0 && v.at(i) <= 0)){
			df.at(i) = 0;
		}
	}
	//mg added this to make sure that the alpha values don't change in the final refinement step - can rejig this code in future to make better
	//for(size_t i = 0; i < n; i++){
	//	df.at(i) = 0;
	//}
	return df;
}




/**
 * Returns -v for input vector v
 */
std::vector<double> negate_v(std::vector<double> v){
	std::vector<double> r(v.size());
	for(unsigned int i = 0; i < v.size(); i++){
		r.at(i) = -v.at(i);
	}
	return r;
}

/**
 * The beta value for the polak-ribiere conjugate gradient descent
 */
double b_pr(std::vector<double> &a, std::vector<double> &b){
	double r1 = 0.0, r2 = 0.0;
	for(unsigned int i = 0; i < a.size(); i++){
		r1 += a.at(i)*(a.at(i)-b.at(i));
		r2 += b.at(i)*b.at(i);
	}
	if(r2 != 0){
		return r1/r2;
	} else {
		return 0;
	}
}

/**
 * Make Input vector v a unit vector
 */
std::vector<double> make_unit(std::vector<double> v){
	double l = 0.0;
	std::vector<double> r(v.size());
	for(double d : v){
		l += pow(d,2);
	}
	double k = sqrt(l);
	for(unsigned int i = 0; i < v.size(); i++){
		if(k != 0){
			r.at(i) = v.at(i)/k;
		}
	}
	return r;
}

/**
 * Clip a double value into range [0,1]
 */
double clip(double x){
	if(x > 1){
		return 1;
	} else if(x < 0){
		return 0;
	} else {
		return x;
	}
}

/**
 * Clip a vector into range [0,1]
 */
std::vector<double> clip(std::vector<double> &v){
	for(unsigned int i = 0; i < v.size(); i++){
		v.at(i) = (v.at(i)>1.0)?1.0:v.at(i);
		v.at(i) = (v.at(i)<0.0)?0.0:v.at(i);
	}
	return v;
}

/**
 * Linear transformation of two vectors and a scalar: a+c*b
 */
std::vector<double> lin_transform(std::vector<double> &a, std::vector<double> &b, double c){
	std::vector<double> r(a.size());
	for(unsigned int i = 0; i < a.size(); i++){
		r.at(i) = a.at(i)+c*b.at(i);
	}
	return r;
}

/**
 * Backtracking line-search
 * Start direction x, search direction d
 */
double line_search(vFunctionCall f, std::vector<double> &x, std::vector<double> d, void* params)
{

	double in = f(x,params);
	double a_k = .5;
	int iter = 0;
	double rhok  = 1e-8;
	std::vector<double> x1;
	x1 = lin_transform(x,d,a_k);
	x1 = clip(x1); // Clip to box constraints
	while(!(f(x1,params) <= f(x,params) - (a_k*a_k)*(1e-4)*cv::norm(d,cv::NORM_L2)*cv::norm(d,cv::NORM_L2)) && (iter < 7)){ //mg was 5
		iter++;
		if(a_k*cv::norm(d,cv::NORM_L2) < rhok){   
            a_k = 0;
			x1 = lin_transform(x,d,a_k);
			x1 = clip(x1);  
		}else{
			a_k = a_k*0.5;
			x1 = lin_transform(x,d,a_k);
			x1 = clip(x1);
		}
	};
	double out = f(x1,params);
	if(in < out){
		a_k = 0;
	}
	return a_k;
}

//mg_changed line_search for testing
// double mg_line_search(vFunctionCall f, std::vector<double> &x, std::vector<double> d, void* params)
// {
// 	//std::cout << f(x,params) << "just inside line search " << std::endl;
// 	double in = f(x,params);
// 	int iter = 0;
// 	std::vector<double> x1;
// 	double min_cost = 1000000;
// 	double cost_ai;
// 	double a_k = 0.0;
// 	double a_ik = 0.0;
// 	std::vector<double> x_k;
// 	for(int a_i = 0; a_i < 501 ; a_i++){
// 		a_ik = double(a_i)/1000;
// 		x1 = lin_transform(x,d,a_ik);
// 		x1 = clip(x1);
// 		cost_ai = f(x1,params);
// 		if(cost_ai < min_cost){
// 			min_cost = cost_ai;
// 			a_k = a_ik;
// 			x_k = x1;
// 		}
// 	}

// 	double out = f(x_k,params);
// 	if(in < out){
// 		a_k = 0;
// 		//std::cout << "line search wrong" << std::endl;
// 	}
// 	return a_k;
// }

/**
 * L2-Normed difference between vectors x1 and x2: ||x1-x2||
 */
double normed_diff(std::vector<double> &x1, std::vector<double> &x2){
	double ret = 0;
	for(unsigned int i = 0; i < x1.size(); i++){
		ret += pow(x1.at(i) - x2.at(i),2);
	}
	return sqrt(ret);
}

/**
 * Given a in_vect vector of values with alphas and B G R of each layer
 * return the corresponding pixel value when summed together
 */
cv::Vec4i getPixelBGRA(std::vector<double> in_vect)
{
	int n = in_vect.size() / 4;
	double alpha_unit;
	double sum_u1 = 0.0, sum_u2 = 0.0, sum_u3 = 0.0, sum_alpha = 0.0;
	cv::Vec4i out_pix;
	// for each layer
	for(size_t l = 0; l < n; l++){
		alpha_unit = in_vect.at(l);
		sum_u1 += alpha_unit*in_vect.at(3*l+n) * 255; //B_i * alpha_i
		sum_u2 += alpha_unit*in_vect.at(3*l+n+1) * 255; //G_i * alpha_i
		sum_u3 += alpha_unit*in_vect.at(3*l+n+2) * 255; //R_i * alpha_i
		sum_alpha += in_vect.at(l) * 255;
	}
	out_pix[0] = sum_u1;
	out_pix[1] = sum_u2;
	out_pix[2] = sum_u3;
	out_pix[3] = sum_alpha;
	return out_pix;
}

/**
 * This is the conjugate gradient minimisation step - used to minimise the cost function F
 */

std::vector<double> minimizeFCG(std::vector<double> x_0, vFunctionCall f, vFunctionCall2 df, std::vector<cv::Vec3d> &means,
	std::vector<cv::Matx33d> &covs, cv::Vec3d color, double p, cv::Vec4d lambda, std::vector<double> gt_alpha){
	// Initialize variables
	int n = means.size();
	InputParams par[1] = {std::make_tuple(means, covs, lambda, color, p, true, std::vector<double> {0}, gt_alpha)};
	void* params = (void *)par;

	// First search direction is gradient of f. Direction is always made a unit vector
	std::vector<double> dx0 = negate_v(df(x_0,params)); 
	dx0 = make_unit(dx0);
	double a0 = line_search(f, x_0, dx0, params);// arg min alpha

	std::vector<double> x_n1, x_n, s_n, s_n1, dx_n, dx_n1;
	// Add direction*step_size to x_0 to get x_1, always clip to box constraints
	x_n = lin_transform(x_0, dx0, a0);
	x_n = clip(x_n); 
	s_n = dx0;
	dx_n = dx0;
	double b, a_n, tol;
	int iter = 0, isMin = 0;

	do{ // Iterate until no progress is made
		iter++;		
		dx_n1 = negate_v(df(x_n,params)); //go in direction of gradient of the minimisation function
		dx_n1 = make_unit(dx_n1);
		b = b_pr(dx_n1, dx_n);
		s_n = lin_transform(dx_n1, s_n, b);
		s_n = make_unit(s_n); // New search direction

		a_n = line_search(f, x_n, s_n, params);
		x_n1 = lin_transform(x_n, s_n, a_n);
		x_n1 = clip(x_n1);


		tol = normed_diff(x_n1, x_n);
		x_n = x_n1;
		dx_n = dx_n1;
		if(tol < constants::tol){
			isMin++;
			s_n = negate_v(df(x_n,params));
			s_n = make_unit(s_n);
		}
		if(iter % (4*n) == 0){ //Periodical reset of direction
			s_n = negate_v(df(x_n,params));
			s_n = make_unit(s_n);
		}

	}while((isMin < constants::isMin_max_iter) && (iter < constants::cg_max_iter));

	//  std::cout << "end: " << std::endl; 
	//  for(int i = 0; i < x_n.size(); i++){
	//  	std::cout << "i " << i << " " << x_n.at(i) << std::endl;
	//  }
	//  std::cout << "f x_n: " << f(x_n,params) << std::endl;

	return x_n;
}


/* 
*
*This is the method of multipliers - mg
*
*/

std::vector<double> minimizeMofM(std::vector<double> x_0, vFunctionCall f, vFunctionCall2 df, std::vector<cv::Vec3d> &means,
	std::vector<cv::Matx33d> &covs, cv::Vec3d color, std::vector<double>gt_alpha){
	// Initialize variables
	double p = .1; //initial value 0.1 
	cv::Vec4d lambda = cv::Vec4d(.1,.1,.1,.1); //initial value (0.1,0.1,0.1,0.1) 
	int n = means.size();
	InputParams par[1] = {std::make_tuple(means, covs, lambda, color, p, true, std::vector<double> {0}, gt_alpha)};
	void* params = (void *)par;
	std::vector<double> x_n, x_n1;
	double diff;
	x_n = x_0;
	int count = 0;
	int iter = 0;
	do{
		//std::cout << "lambda: " << lambda.val[0] << std::endl;
		//std::cout << "p: " << p << std::endl;
		if(count== 0){
			x_n1 = minimizeFCG( x_n, f, df,  means,covs, color, p, lambda, gt_alpha);
			count++;
		}else{

			lambda += p*g(x_n1,n,color); 
			if(cv::norm(g(x_n1,n,color), cv::NORM_L2) > constants::gamma*cv::norm(g(x_n,n,color), cv::NORM_L2)){
				p = constants::beta * p;
			}
			par[0] = std::make_tuple(means, covs, lambda, color, p, true, std::vector<double> {0}, gt_alpha);
			params = (void *)par;
			x_n1 = minimizeFCG( x_n, f, df,  means,covs, color, p, lambda, gt_alpha);
		}
		iter ++;
		diff = cv::norm(x_n,x_n1,cv::NORM_L2);
		x_n = x_n1;
		
	}while((diff < 0.0001 && iter < 11) ||(diff > 0.0001));	//mg found 11 was a good number for the minimum number of iterations needed to make sure constraints were imposed
	std::cout << "MoM iter: " << iter << std::endl;
	return x_n;
}



