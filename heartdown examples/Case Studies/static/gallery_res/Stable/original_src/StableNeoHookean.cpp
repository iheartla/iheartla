///////////////////////////////////////////////////////////////////////////////////////////////////
// I. LICENSE CONDITIONS
//
// Copyright (c) 2018 by Disney-Pixar
//
// Permission is hereby granted to use this software solely for non-commercial applications
// and purposes including academic or industrial research, evaluation and not-for-profit media
// production. All other rights are retained by Pixar. For use for or in connection with
// commercial applications and purposes, including without limitation in or in connection with
// software products offered for sale or for-profit media production, please contact Pixar at
// tech-licensing@pixar.com.
//
// THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
// NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY, NONINFRINGEMENT, AND FITNESS
// FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL PIXAR OR ITS AFFILIATES BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
// (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
// DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
// WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
// IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
///////////////////////////////////////////////////////////////////////////////////////////////////

#include "StableNeoHookean.h"

namespace CubeSim
{

StableNeoHookean::StableNeoHookean(const Scalar& mu, const Scalar& lambda)
: _mu(mu)
, _lambda(lambda)
, _ratio(_mu / _lambda)
{
    assert(_mu > 0.0);
    assert(_lambda > 0.0);
    assert(_ratio > 0.0);
}

Scalar StableNeoHookean::Psi(const Matrix3& F, const Matrix3& /*U*/, const Matrix3& /*V*/, const Vector3& /*S*/) const
{
    const Scalar Ic = F.squaredNorm();
    const Scalar Jminus1 = F.determinant() - 1.0 - _ratio;
    return 0.5 * (_mu * (Ic - 3.0) + _lambda * Jminus1 * Jminus1);
}

static Matrix3 PartialJpartialF(const Matrix3& F)
{
    Matrix3 pJpF;

    pJpF.col(0) = F.col(1).cross(F.col(2));
    pJpF.col(1) = F.col(2).cross(F.col(0));
    pJpF.col(2) = F.col(0).cross(F.col(1));

    return pJpF;
}

Matrix3 StableNeoHookean::PK1(const Matrix3& F, const Matrix3& /*U*/, const Matrix3& /*V*/, const Vector3& /*S*/) const
{
    const Matrix3 pJpF = PartialJpartialF(F);
    const Scalar Jminus1 = F.determinant() - 1.0 - _ratio;
    return _mu * F + _lambda * Jminus1 * pJpF;
}

static void BuildTwistAndFlipEigenvectors(const Matrix3& U, const Matrix3& V, Matrix9& Q)
{
    static const Scalar scale = 1.0 / std::sqrt(2.0);
    const Matrix3 sV = scale * V;

    using M3 = Eigen::Matrix<Scalar, 3, 3, Eigen::ColMajor>;

    M3 A;
    A << sV(0,2) * U(0,1), sV(1,2) * U(0,1), sV(2,2) * U(0,1),
         sV(0,2) * U(1,1), sV(1,2) * U(1,1), sV(2,2) * U(1,1),
         sV(0,2) * U(2,1), sV(1,2) * U(2,1), sV(2,2) * U(2,1);

    M3 B;
    B << sV(0,1) * U(0,2), sV(1,1) * U(0,2), sV(2,1) * U(0,2),
         sV(0,1) * U(1,2), sV(1,1) * U(1,2), sV(2,1) * U(1,2),
         sV(0,1) * U(2,2), sV(1,1) * U(2,2), sV(2,1) * U(2,2);

    M3 C;
    C << sV(0,2) * U(0,0), sV(1,2) * U(0,0), sV(2,2) * U(0,0),
         sV(0,2) * U(1,0), sV(1,2) * U(1,0), sV(2,2) * U(1,0),
         sV(0,2) * U(2,0), sV(1,2) * U(2,0), sV(2,2) * U(2,0);

    M3 D;
    D << sV(0,0) * U(0,2), sV(1,0) * U(0,2), sV(2,0) * U(0,2),
         sV(0,0) * U(1,2), sV(1,0) * U(1,2), sV(2,0) * U(1,2),
         sV(0,0) * U(2,2), sV(1,0) * U(2,2), sV(2,0) * U(2,2);

    M3 E;
    E << sV(0,1) * U(0,0), sV(1,1) * U(0,0), sV(2,1) * U(0,0),
         sV(0,1) * U(1,0), sV(1,1) * U(1,0), sV(2,1) * U(1,0),
         sV(0,1) * U(2,0), sV(1,1) * U(2,0), sV(2,1) * U(2,0);

    M3 F;
    F << sV(0,0) * U(0,1), sV(1,0) * U(0,1), sV(2,0) * U(0,1),
         sV(0,0) * U(1,1), sV(1,0) * U(1,1), sV(2,0) * U(1,1),
         sV(0,0) * U(2,1), sV(1,0) * U(2,1), sV(2,0) * U(2,1);

    // Twist eigenvectors
    Eigen::Map<M3>(Q.data())      = B - A;
    Eigen::Map<M3>(Q.data() + 9)  = D - C;
    Eigen::Map<M3>(Q.data() + 18) = F - E;

    // Flip eigenvectors
    Eigen::Map<M3>(Q.data() + 27) = A + B;
    Eigen::Map<M3>(Q.data() + 36) = C + D;
    Eigen::Map<M3>(Q.data() + 45) = E + F;
}

static Matrix9 ProjectHessianWithAnalyticalFormulasNew(const Scalar& mu, const Scalar& lambda, const Matrix3& F, const Matrix3& U, const Matrix3& V, const Vector3& S)
{

    Vector9 eigenvalues;
    Matrix9 eigenvectors;

    const Scalar J = F.determinant();

    // Compute the twist and flip eigenvalues
    {
        // Twist eigenvalues
        eigenvalues.segment<3>(0) = S;
        // Flip eigenvalues
        eigenvalues.segment<3>(3) = -S;
        const Scalar evScale = lambda * (J - 1.0) - mu;
        eigenvalues.segment<6>(0) *= evScale;
        eigenvalues.segment<6>(0).array() += mu;
    }

    // Compute the twist and flip eigenvectors
    BuildTwistAndFlipEigenvectors(U, V, eigenvectors);

    // Compute the remaining three eigenvalues and eigenvectors
    {
        Matrix3 A;
        const Scalar s0s0 = S(0) * S(0);
        const Scalar s1s1 = S(1) * S(1);
        const Scalar s2s2 = S(2) * S(2);
        A(0, 0) = mu + lambda * s1s1 * s2s2;
        A(1, 1) = mu + lambda * s0s0 * s2s2;
        A(2, 2) = mu + lambda * s0s0 * s1s1;
        const Scalar evScale = lambda * (2.0 * J - 1.0) - mu;
        A(0, 1) = evScale * S(2);
        A(1, 0) = A(0, 1);
        A(0, 2) = evScale * S(1);
        A(2, 0) = A(0, 2);
        A(1, 2) = evScale * S(0);
        A(2, 1) = A(1, 2);

        const Eigen::SelfAdjointEigenSolver<Matrix3> Aeigs(A);
        eigenvalues.segment<3>(6) = Aeigs.eigenvalues();

        Eigen::Map<Matrix3>(eigenvectors.data() + 54) = U * Aeigs.eigenvectors().col(0).asDiagonal() * V.transpose();
        Eigen::Map<Matrix3>(eigenvectors.data() + 63) = U * Aeigs.eigenvectors().col(1).asDiagonal() * V.transpose();
        Eigen::Map<Matrix3>(eigenvectors.data() + 72) = U * Aeigs.eigenvectors().col(2).asDiagonal() * V.transpose();
    }

    // Clamp the eigenvalues
    for (int i = 0; i < 9; i++)
    {
        if (eigenvalues(i) < 0.0)
        {
            eigenvalues(i) = 0.0;
        }
    }

    return eigenvectors * eigenvalues.asDiagonal() * eigenvectors.transpose();
}

static Vector9 PartialJpartialFVec(const Matrix3& F)
{
    Vector9 pJpF;
    pJpF.segment<3>(0) = F.col(1).cross(F.col(2));
    pJpF.segment<3>(3) = F.col(2).cross(F.col(0));
    pJpF.segment<3>(6) = F.col(0).cross(F.col(1));
    return pJpF;
}

static Matrix3 CrossProductMatrix(const Matrix3& F, const int col, const Scalar& scale)
{
    Matrix3 cpm;
    cpm <<  0, -scale * F(2, col), scale * F(1, col),
            scale * F(2, col), 0, -scale * F(0, col),
           -scale * F(1, col), scale * F(0, col), 0;
    return cpm;
}

static Matrix9 ComputeFJSecondDerivContribs(const Scalar& lambda, const Scalar& ratio, const Matrix3& F)
{
    const Scalar scale = lambda * (F.determinant() - 1.0 - ratio);

    const Matrix3 ahat = CrossProductMatrix(F, 0, scale);
    const Matrix3 bhat = CrossProductMatrix(F, 1, scale);
    const Matrix3 chat = CrossProductMatrix(F, 2, scale);

    Matrix9 FJ;
    FJ.block<3,3>(0, 0).setZero();
    FJ.block<3,3>(0, 3) = -chat;
    FJ.block<3,3>(0, 6) = bhat;

    FJ.block<3,3>(3, 0) = chat;
    FJ.block<3,3>(3, 3).setZero();
    FJ.block<3,3>(3, 6) = -ahat;

    FJ.block<3,3>(6, 0) = -bhat;
    FJ.block<3,3>(6, 3) = ahat;
    FJ.block<3,3>(6, 6).setZero();

    return FJ;
}

Matrix9 StableNeoHookean::PartialPpartialF(const Matrix3& F, const Matrix3& /*U*/, const Matrix3& /*V*/, const Vector3& /*S*/) const
{
    const Vector9 pjpf = PartialJpartialFVec(F);
    return _mu * Matrix9::Identity() + _lambda * pjpf * pjpf.transpose() + ComputeFJSecondDerivContribs(_lambda, _ratio, F);
}

Matrix9 StableNeoHookean::ClampedPartialPpartialF(const Matrix3& F, const Matrix3& U, const Matrix3& V, const Vector3& S) const
{
    return ProjectHessianWithAnalyticalFormulasNew(_mu, _lambda, F, U, V, S);
}

std::string StableNeoHookean::Name() const
{
    return "stable_neo_hookean";
}

bool StableNeoHookean::EnergyNeedsSVD() const
{
    return false;
}

bool StableNeoHookean::PK1NeedsSVD() const
{
    return false;
}

}
