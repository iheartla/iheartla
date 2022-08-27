#pragma once
#include <Eigen/Core>
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <iostream>
#include <set>

struct siere {
    Eigen::MatrixXd Gu;
    Eigen::MatrixXd Hu;
    Eigen::VectorXd v_G;
    Eigen::VectorXd v_H;
    Eigen::VectorXd f_G;
    Eigen::VectorXd f_H;
    Eigen::MatrixXd J_G;
    Eigen::MatrixXd J_H;
    Eigen::MatrixXd u_plus_sign;
    Eigen::MatrixXd J_G_circumflex_accent_r;
    Eigen::MatrixXd G_circumflex_accent_ru;

    siere(
        const Eigen::MatrixXd & U_s,
        const Eigen::MatrixXd & M,
        const Eigen::VectorXd & v,
        const Eigen::VectorXd & f,
        const Eigen::MatrixXd & K,
        const Eigen::MatrixXd & boldsymbolI,
        const double & h,
        const std::function<Eigen::MatrixXd(Eigen::MatrixXd)> & φ_1,
        const Eigen::MatrixXd & u)
    {
        const long n = U_s.rows();
        const long s = U_s.cols();
        assert( U_s.rows() == n );
        assert( M.rows() == n );
        assert( M.cols() == n );
        assert( v.size() == n );
        assert( f.size() == n );
        assert( K.rows() == n );
        assert( K.cols() == n );
        assert( boldsymbolI.rows() == 2*n );
        assert( boldsymbolI.cols() == 2*n );
        assert( u.rows() == 2*n );
        assert( u.cols() == 1 );
        assert( fmod(2*n, 1) == 0.0 );
        assert( fmod(2*n, 1) == 0.0 );
        assert( fmod(2*n, 1) == 0.0 );
        // `$v_G$` = `$U_s$``$U_s$`^T Mv
        v_G = U_s * U_s.transpose() * M * v;
        // `$v_H$` =  v - `$v_G$`
        v_H = v - v_G;
        // `$f_G$` =  M`$U_s$``$U_s$`^T f
        f_G = M * U_s * U_s.transpose() * f;
        Eigen::MatrixXd Gu_0(2*n, 1);
        Gu_0 << v_G,
        M.colPivHouseholderQr().solve(f_G);
        // `$G(u)$` = [`$v_G$`
    //           M⁻¹`$f_G$`]
        Gu = Gu_0;
        // `$f_H$` =  f - `$f_G$`
        f_H = f - f_G;
        Eigen::MatrixXd Hu_0(2*n, 1);
        Hu_0 << v_H,
        M.colPivHouseholderQr().solve(f_H);
        // `$H(u)$` = [`$v_H$`
    //           M⁻¹`$f_H$`]
        Hu = Hu_0;
        Eigen::MatrixXd J_G_0(2*n, 2*n);
        J_G_0 << Eigen::MatrixXd::Zero(n, n), U_s * U_s.transpose() * M,
        -U_s * U_s.transpose() * K * U_s * U_s.transpose() * M, Eigen::MatrixXd::Zero(n, n);
        // `$J_G$` = [0    `$U_s$``$U_s$`^TM
    //       -`$U_s$``$U_s$`^TK`$U_s$``$U_s$`^TM 0 ]
        J_G = J_G_0;
        Eigen::MatrixXd J_H_0(2*n, 2*n);
        J_H_0 << Eigen::MatrixXd::Zero(n, n), Eigen::MatrixXd::Identity(n, n),
        -M.colPivHouseholderQr().solve(K), Eigen::MatrixXd::Zero(n, n);
        // `$J_H$` =  [0     I_n
    //             -M⁻¹K 0] - `$J_G$`
        J_H = J_H_0 - J_G;
        Eigen::MatrixXd J_G_circumflex_accent_r_0(2*s, 2*s);
        J_G_circumflex_accent_r_0 << Eigen::MatrixXd::Zero(s, s), Eigen::MatrixXd::Identity(s, s),
        -U_s.transpose() * K * U_s, Eigen::MatrixXd::Zero(s, s);
        // `$J_G^r$` = [0     I_s
    //             -`$U_s$`^TK`$U_s$` 0]
        J_G_circumflex_accent_r = J_G_circumflex_accent_r_0;
        Eigen::MatrixXd G_circumflex_accent_ru_0(2*s, 1);
        G_circumflex_accent_ru_0 << U_s.transpose() * M * v,
        U_s.transpose() * f;
        // `$G^r(u)$` = [`$U_s$`^TMv
    //             `$U_s$`^Tf]
        G_circumflex_accent_ru = G_circumflex_accent_ru_0;
        Eigen::MatrixXd u_plus_sign_2(2*n, 2*s);
        u_plus_sign_2 << U_s, Eigen::MatrixXd::Zero(n, s),
        Eigen::MatrixXd::Zero(n, s), U_s;
        // `$u_+$` =  u + (`$\boldsymbol{I}$` -h`$J_H$`)⁻¹(h `$H(u)$` + h[`$U_s$` 0
    //                                                0   `$U_s$`] `$φ_1$`(h`$J_G^r$`) `$G^r(u)$`)
        u_plus_sign = u + (boldsymbolI - h * J_H).colPivHouseholderQr().solve((h * Hu + h * u_plus_sign_2 * φ_1(h * J_G_circumflex_accent_r) * G_circumflex_accent_ru));
    }
};

struct second {
    Eigen::MatrixXd J_G;
    Eigen::MatrixXd Y_1;
    Eigen::MatrixXd Z_1;
    Eigen::MatrixXd Y_2;
    Eigen::MatrixXd Z_2;

    second(
        const Eigen::MatrixXd & U_s,
        const Eigen::MatrixXd & M,
        const Eigen::MatrixXd & K)
    {
        const long n = U_s.rows();
        const long s = U_s.cols();
        assert( U_s.rows() == n );
        assert( M.rows() == n );
        assert( M.cols() == n );
        assert( K.rows() == n );
        assert( K.cols() == n );
        Eigen::MatrixXd Y_1_0(n + 1, s);
        Y_1_0 << U_s,
        Eigen::MatrixXd::Zero(1, s);
        // `$Y_1$` =  [`$U_s$`
    //              0]
        Y_1 = Y_1_0;
        Eigen::MatrixXd Z_1_0(n + 1, s);
        Z_1_0 << Eigen::MatrixXd::Zero(1, s),
        M * U_s;
        // `$Z_1$` =  [ 0
    //              M`$U_s$`]
        Z_1 = Z_1_0;
        Eigen::MatrixXd Y_2_0(n + 1, s);
        Y_2_0 << Eigen::MatrixXd::Zero(1, s),
        -U_s * U_s.transpose() * K * U_s;
        // `$Y_2$` =  [0
    //             -`$U_s$``$U_s$`^TK`$U_s$`]
        Y_2 = Y_2_0;
        Eigen::MatrixXd Z_2_0(n + 1, s);
        Z_2_0 << M * U_s,
        Eigen::MatrixXd::Zero(1, s);
        // `$Z_2$` =  [ M`$U_s$`
    //              0]
        Z_2 = Z_2_0;
        // `$J_G$` = `$Y_1$``$Z_1$`^T + `$Y_2$``$Z_2$`^T
        J_G = Y_1 * Z_1.transpose() + Y_2 * Z_2.transpose();
    }
};

