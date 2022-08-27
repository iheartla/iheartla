#pragma once
#include <Eigen/Core>
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <iostream>
#include <set>

struct elastic {
    double E;
    double E_q;
    double E_a;
    double E_n;
    double E_p;

    struct connection {
        double E_q;
        connection(
            const Eigen::VectorXd & q_g,
            const Eigen::VectorXd & q_h,
            const Eigen::VectorXd & m_g,
            const Eigen::VectorXd & m_h,
            const std::function<Eigen::VectorXd(Eigen::VectorXd, Eigen::VectorXd)> & angle,
            const double & λ_q_comma_1,
            const double & λ_q_comma_2,
            const double & t)
        {
            const long n = q_g.size();
            assert( q_h.size() == n );
            assert( m_g.size() == n );
            assert( m_h.size() == n );
            // E_q = λ_q_comma_1||q_g-q_h+tm_g||^2 + λ_q_comma_1||q_h-q_g+tm_h||^2 + λ_q_comma_2||angle(m_g,m_h)||^2
            E_q = λ_q_comma_1 * pow((q_g - q_h + t * m_g).lpNorm<2>(), 2) + λ_q_comma_1 * pow((q_h - q_g + t * m_h).lpNorm<2>(), 2) + λ_q_comma_2 * pow((angle(m_g, m_h)).lpNorm<2>(), 2);
        }
    };
    struct anchor {
        double E_a;
        anchor(
            const double & λ_a_comma_1,
            const double & λ_a_comma_2,
            const Eigen::VectorXd & q,
            const Eigen::VectorXd & q_a,
            const Eigen::VectorXd & m,
            const Eigen::VectorXd & m_a,
            const std::function<Eigen::VectorXd(Eigen::VectorXd, Eigen::VectorXd)> & angle)
        {
            const long n = q.size();
            assert( q_a.size() == n );
            assert( m.size() == n );
            assert( m_a.size() == n );
            // E_a = λ_a_comma_1||q-q_a||^2 + λ_a_comma_2||angle(m,m_a)||^2
            E_a = λ_a_comma_1 * pow((q - q_a).lpNorm<2>(), 2) + λ_a_comma_2 * pow((angle(m, m_a)).lpNorm<2>(), 2);
        }
    };
    struct notchlimit {
        double E_n;
        notchlimit(
            const double & δ_circumflex_accent_minus_sign,
            const double & δ_circumflex_accent_plus_sign,
            const double & β_q,
            const double & β_circumflex_accent_minus_sign,
            const double & β_circumflex_accent_plus_sign)
        {
        
            // E_n = δ_circumflex_accent_minus_sign(1/10 log((β_q-β_circumflex_accent_minus_sign)))^2 + δ_circumflex_accent_plus_sign(1/10 log((β_circumflex_accent_plus_sign-β_q)))^2
            E_n = δ_circumflex_accent_minus_sign * pow((1 / double(10) * log((β_q - β_circumflex_accent_minus_sign))), 2) + δ_circumflex_accent_plus_sign * pow((1 / double(10) * log((β_circumflex_accent_plus_sign - β_q))), 2);
        }
    };
    struct penalty {
        double E_p;
        penalty(
            const double & μ,
            const double & ε,
            const double & β_q)
        {
        
            // E_p = (μ log((ε + β_q)))^2 + (μ log((ε + 1 - β_q)))^2
            E_p = pow((μ * log((ε + β_q))), 2) + pow((μ * log((ε + 1 - β_q))), 2);
        }
    };
    connection _connection;
    anchor _anchor;
    notchlimit _notchlimit;
    penalty _penalty;
    elastic(
        const double & E_r,
        const Eigen::VectorXd & q_g,
        const Eigen::VectorXd & q_h,
        const Eigen::VectorXd & m_g,
        const Eigen::VectorXd & m_h,
        const std::function<Eigen::VectorXd(Eigen::VectorXd, Eigen::VectorXd)> & angle,
        const double & λ_q_comma_1,
        const double & λ_q_comma_2,
        const double & t,
        const double & λ_a_comma_1,
        const double & λ_a_comma_2,
        const Eigen::VectorXd & q,
        const Eigen::VectorXd & q_a,
        const Eigen::VectorXd & m,
        const Eigen::VectorXd & m_a,
        const double & δ_circumflex_accent_minus_sign,
        const double & δ_circumflex_accent_plus_sign,
        const double & β_q,
        const double & β_circumflex_accent_minus_sign,
        const double & β_circumflex_accent_plus_sign,
        const double & μ,
        const double & ε)
    :
    _connection(q_g, q_h, m_g, m_h, angle, λ_q_comma_1, λ_q_comma_2, t),
    _anchor(λ_a_comma_1, λ_a_comma_2, q, q_a, m, m_a, angle),
    _notchlimit(δ_circumflex_accent_minus_sign, δ_circumflex_accent_plus_sign, β_q, β_circumflex_accent_minus_sign, β_circumflex_accent_plus_sign),
    _penalty(μ, ε, β_q)
    {
        const long n = q_g.size();
        assert( q_h.size() == n );
        assert( m_g.size() == n );
        assert( m_h.size() == n );
        assert( q.size() == n );
        assert( q_a.size() == n );
        assert( m.size() == n );
        assert( m_a.size() == n );
        E_q = _connection.E_q;
        E_a = _anchor.E_a;
        E_n = _notchlimit.E_n;
        E_p = _penalty.E_p;
        // E = `E_r` + `E_q` + `E_a` + `E_n` + `E_p`
        E = E_r + E_q + E_a + E_n + E_p;
    }
};

struct connection {
    double E_q;

    connection(
        const Eigen::VectorXd & q_g,
        const Eigen::VectorXd & q_h,
        const Eigen::VectorXd & m_g,
        const Eigen::VectorXd & m_h,
        const std::function<Eigen::VectorXd(Eigen::VectorXd, Eigen::VectorXd)> & angle,
        const double & λ_q_comma_1,
        const double & λ_q_comma_2,
        const double & t)
    {
        const long n = q_g.size();
        assert( q_h.size() == n );
        assert( m_g.size() == n );
        assert( m_h.size() == n );
        // `E_q` = `$λ_{q,1}$`||`$q_g$`-`$q_h$`+t`$m_g$`||^2 + `$λ_{q,1}$`||`$q_h$`-`$q_g$`+t`$m_h$`||^2 + `$λ_{q,2}$`||`$\angle$`(`$m_g$`,`$m_h$`)||^2
        E_q = λ_q_comma_1 * pow((q_g - q_h + t * m_g).lpNorm<2>(), 2) + λ_q_comma_1 * pow((q_h - q_g + t * m_h).lpNorm<2>(), 2) + λ_q_comma_2 * pow((angle(m_g, m_h)).lpNorm<2>(), 2);
    }
};

struct anchor {
    double E_a;

    anchor(
        const double & λ_a_comma_1,
        const double & λ_a_comma_2,
        const Eigen::VectorXd & q,
        const Eigen::VectorXd & q_a,
        const Eigen::VectorXd & m,
        const Eigen::VectorXd & m_a,
        const std::function<Eigen::VectorXd(Eigen::VectorXd, Eigen::VectorXd)> & angle)
    {
        const long n = q.size();
        assert( q_a.size() == n );
        assert( m.size() == n );
        assert( m_a.size() == n );
        // `E_a` = `$λ_{a,1}$`||q-`$q_a$`||^2 + `$λ_{a,2}$`||`$\angle$`(m,`$m_a$`)||^2
        E_a = λ_a_comma_1 * pow((q - q_a).lpNorm<2>(), 2) + λ_a_comma_2 * pow((angle(m, m_a)).lpNorm<2>(), 2);
    }
};

struct notchlimit {
    double E_n;

    notchlimit(
        const double & δ_circumflex_accent_minus_sign,
        const double & δ_circumflex_accent_plus_sign,
        const double & β_q,
        const double & β_circumflex_accent_minus_sign,
        const double & β_circumflex_accent_plus_sign)
    {
    
        // `E_n` = `$δ^{(−)}$`(1/10 log((`$β_q$`-`$β^{(−)}$`)))^2 + `$δ^{(+)}$`(1/10 log((`$β^{(+)}$`-`$β_q$`)))^2
        E_n = δ_circumflex_accent_minus_sign * pow((1 / double(10) * log((β_q - β_circumflex_accent_minus_sign))), 2) + δ_circumflex_accent_plus_sign * pow((1 / double(10) * log((β_circumflex_accent_plus_sign - β_q))), 2);
    }
};

struct penalty {
    double E_p;

    penalty(
        const double & μ,
        const double & ε,
        const double & β_q)
    {
    
        // `E_p` = (μ log((ε + `$β_q$`)))^2 + (μ log((ε + 1 - `$β_q$`)))^2
        E_p = pow((μ * log((ε + β_q))), 2) + pow((μ * log((ε + 1 - β_q))), 2);
    }
};

