/*
Szymon Rusinkiewicz
Princeton University

ICP_align.inc
A variety of methods for error metric minimization in the context of ICP.
This needs to be combined with ICP_iter.inc and a driver routine to get
a full ICP.

The functions in this file use doubles for all internal computations, just
to eliminate numerical roundoff from consideration for testing purposes.
Real ICP implementations will, realistically, probably just use floats instead.

All functions take a vector of PtPairs as input.  The point pairs must
already be transformed to world coordinates.  They also take as input the
centroids of the two point sets, and a scale representing the *reciprocal*
of the size of the point pairs (e.g., RMS distance distance of points from
their centroids).  They return a bool indicating whether ICP succeeded
(i.e., the points were brought closer by the iteration), and set alignxf
to be the rigid-body transformation to be applied to the *second* point set
to bring it into alignment with the first point set.
*/

#include "TriMesh.h"
#include "XForm.h"
#include "lineqn.h"


namespace trimesh {


// Supported ICP variants
enum ICP_Variant { VARIANT_PT2PT, VARIANT_PT2PL_ONEWAY, VARIANT_SYMM,
                   VARIANT_PT2PL_TWOPLANE, VARIANT_SYMM_ROTNORM, VARIANT_MITRA,
		   VARIANT_PT2PL_ONEWAY_LM, VARIANT_SYMM_LM };


// A pair of points, with associated normals and principal curvatures / dirs
struct PtPair {
	vec p1, n1, p2, n2;
	vec pdir1, pdir2;
	float curv1, curv2;
	PtPair(const point &p1_, const vec &n1_,
	       const point &p2_, const vec &n2_) :
			p1(p1_), n1(n1_), p2(p2_), n2(n2_)
		{}
};


// Determinant of a 3x3 matrix - used by align_pt2pt
static double det(const double (&A)[3][3])
{
	return A[0][0] * (A[1][1] * A[2][2] - A[1][2] * A[2][1]) +
	       A[0][1] * (A[1][2] * A[2][0] - A[1][0] * A[2][2]) +
	       A[0][2] * (A[1][0] * A[2][1] - A[1][1] * A[2][0]);
}


// Rigid-body point-to-point alignment
static bool align_pt2pt(const ::std::vector<PtPair> &pairs,
	const point &centroid1, const point &centroid2, xform &alignxf)
{
	size_t n = pairs.size();
	double U[3][3] = { { 0 } };

	for (size_t i = 0; i < n; i++) {
		dvec3 v1 = dvec3(pairs[i].p1 - centroid1);
		dvec3 v2 = dvec3(pairs[i].p2 - centroid2);
		for (int j = 0; j < 3; j++)
			for (int k = 0; k < 3; k++)
				U[j][k] += v1[j] * v2[k];
	}
	double s[3], V[3][3];
	svd<double,3,3>(U, s, V);
	for (int i = 0; i < 3; i++) {
		if (s[i] < 1e-6)
			return false;
	}

	if ((det(U) < 0.0) ^ (det(V) < 0.0)) {
		V[2][0] = -V[2][0];
		V[2][1] = -V[2][1];
		V[2][2] = -V[2][2];
	}
	alignxf = xform::trans(centroid1) *
	          xform::fromarray(U) * transp(xform::fromarray(V)) *
	          xform::trans(-centroid2);

	return true;
}


// Non-symmetric point-to-plane alignment
static bool align_pt2pl_oneway(const ::std::vector<PtPair> &pairs,
	float scale, point &centroid1, point &centroid2, xform &alignxf)
{
	size_t npairs = pairs.size();
	double A[6][6] = { { 0 } }, b[6] = { 0 };

	for (size_t i = 0; i < npairs; i++) {
		dvec3 p1 = dvec3(scale * (pairs[i].p1 - centroid1));
		dvec3 p2 = dvec3(scale * (pairs[i].p2 - centroid2));
		dvec3 n = dvec3(pairs[i].n1);
		dvec3 c = p2 CROSS n;
		dvec3 d = p1 - p2;

		double x[6] = { c[0], c[1], c[2], n[0], n[1], n[2] };
		double dn = d DOT n;

		for (int j = 0; j < 6; j++) {
			b[j] += dn * x[j];
			for (int k = j; k < 6; k++)
				A[j][k] += x[j] * x[k];
		}
	}

	// Make matrix symmetric
	for (int j = 0; j < 6; j++)
		for (int k = 0; k < j; k++)
			A[j][k] = A[k][j];

	// Eigen-decomposition and inverse
	double eval[6], einv[6];
	eigdc<double,6>(A, eval);
	for (int i = 0; i < 6; i++) {
		if (eval[i] < 1e-6)
			return false;
		else
			einv[i] = 1.0 / eval[i];
	}

	// Solve system
	eigmult<double,6>(A, einv, b);

	// Extract rotation and translation
	dvec3 rot(b[0], b[1], b[2]), trans(b[3], b[4], b[5]);
	double rotangle = len(rot);
	trans *= 1.0 / scale;

	xform R = xform::rot(rotangle, rot);
	alignxf = xform::trans(centroid1) *
	          xform::trans(trans) * R *
	          xform::trans(-centroid2);

	return true;
}


// Mitra's on-demand variant of non-symmetric quadratic alignment.
// Unlike the other functions here, this requires that curv1,2 and pdir1,2
// be filled-in in pairs.
static bool align_mitra(const ::std::vector<PtPair> &pairs,
	float scale, point &centroid1, point &centroid2, xform &alignxf)
{
	size_t npairs = pairs.size();
	double A[6][6] = { { 0 } }, b[6] = { 0 };

	// Component along normal
	for (size_t i = 0; i < npairs; i++) {
		dvec3 p1 = dvec3(scale * (pairs[i].p1 - centroid1));
		dvec3 p2 = dvec3(scale * (pairs[i].p2 - centroid2));
		dvec3 n = dvec3(pairs[i].n1);
		dvec3 c = p2 CROSS n;
		dvec3 d = p1 - p2;

		double x[6] = { c[0], c[1], c[2], n[0], n[1], n[2] };
		double dn = d DOT n;

		for (int j = 0; j < 6; j++) {
			b[j] += dn * x[j];
			for (int k = j; k < 6; k++)
				A[j][k] += x[j] * x[k];
		}
	}

	// Component along first principal direction
	for (size_t i = 0; i < npairs; i++) {
		dvec3 p1 = dvec3(pairs[i].p1 - centroid1);
		dvec3 p2 = dvec3(pairs[i].p2 - centroid2);
		dvec3 n = dvec3(pairs[i].n1);

		double dd = (p2 - p1) DOT n;
		double k1d = double(pairs[i].curv1) * dd;
		if (k1d <= 0.0)
			continue;
		double wt1 = k1d / (1.0 + k1d);
		// Reset "n" to be along the 1st principal dir
		n = wt1 * dvec3(pairs[i].pdir1);

		dvec3 c = dvec3(scale * p2) CROSS n;
		dvec3 d = scale * (p1 - p2);

		double x[6] = { c[0], c[1], c[2], n[0], n[1], n[2] };
		double dn = d DOT n;

		for (int j = 0; j < 6; j++) {
			b[j] += dn * x[j];
			for (int k = j; k < 6; k++)
				A[j][k] += x[j] * x[k];
		}
	}

	// Component along second principal direction
	for (size_t i = 0; i < npairs; i++) {
		dvec3 p1 = dvec3(pairs[i].p1 - centroid1);
		dvec3 p2 = dvec3(pairs[i].p2 - centroid2);
		dvec3 n = dvec3(pairs[i].n1);

		double dd = (p2 - p1) DOT n;
		double k2d = double(pairs[i].curv2) * dd;
		if (k2d <= 0.0)
			continue;
		double wt2 = k2d / (1.0 + k2d);
		// Reset "n" to be along the 2nd principal dir
		n = wt2 * dvec3(pairs[i].pdir2);

		dvec3 c = dvec3(scale * p2) CROSS n;
		dvec3 d = scale * (p1 - p2);

		double x[6] = { c[0], c[1], c[2], n[0], n[1], n[2] };
		double dn = d DOT n;

		for (int j = 0; j < 6; j++) {
			b[j] += dn * x[j];
			for (int k = j; k < 6; k++)
				A[j][k] += x[j] * x[k];
		}
	}

	// Make matrix symmetric
	for (int j = 0; j < 6; j++)
		for (int k = 0; k < j; k++)
			A[j][k] = A[k][j];

	// Eigen-decomposition and inverse
	double eval[6], einv[6];
	eigdc<double,6>(A, eval);
	for (int i = 0; i < 6; i++) {
		if (eval[i] < 1e-6)
			return false;
		else
			einv[i] = 1.0 / eval[i];
	}

	// Solve system
	eigmult<double,6>(A, einv, b);

	// Extract rotation and translation
	dvec3 rot(b[0], b[1], b[2]), trans(b[3], b[4], b[5]);
	double rotangle = len(rot);
	trans *= 1.0 / scale;

	xform R = xform::rot(rotangle, rot);
	alignxf = xform::trans(centroid1) *
	          xform::trans(trans) * R *
	          xform::trans(-centroid2);

	return true;
}


// Non-symmetric Levenberg-Marquardt point-to-plane alignment.
static bool align_pt2pl_oneway_lm(const ::std::vector<PtPair> &pairs,
	float scale, point &centroid1, point &centroid2, xform &alignxf,
	float lambda)
{
	size_t npairs = pairs.size();
	double A[6][6] = { { 0 } }, b[6] = { 0 };

	for (size_t i = 0; i < npairs; i++) {
		dvec3 p1 = dvec3(scale * (pairs[i].p1 - centroid1));
		dvec3 p2 = dvec3(scale * (pairs[i].p2 - centroid2));
		dvec3 n = dvec3(pairs[i].n1);
		dvec3 c = p2 CROSS n;
		dvec3 d = p1 - p2;

		double x[6] = { c[0], c[1], c[2], n[0], n[1], n[2] };
		double dn = d DOT n;

		for (int j = 0; j < 6; j++) {
			b[j] += dn * x[j];
			for (int k = j; k < 6; k++)
				A[j][k] += x[j] * x[k];
		}
	}

	// Make matrix symmetric
	for (int j = 0; j < 6; j++)
		for (int k = 0; k < j; k++)
			A[j][k] = A[k][j];

	// L-M regularization.  This is the "scale the diagonal" variant,
	// as opposed to the "add a multiple of the identity" variant.
	for (int j = 0; j < 6; j++)
		A[j][j] *= (1.0 + lambda);

	// Eigen-decomposition and inverse
	double eval[6], einv[6];
	eigdc<double,6>(A, eval);
	for (int i = 0; i < 6; i++) {
		if (eval[i] < 1e-6)
			return false;
		else
			einv[i] = 1.0 / eval[i];
	}

	// Solve system
	eigmult<double,6>(A, einv, b);

	// Extract rotation and translation
	dvec3 rot(b[0], b[1], b[2]), trans(b[3], b[4], b[5]);
	double rotangle = len(rot);
	trans *= 1.0 / scale;

	xform R = xform::rot(rotangle, rot);
	alignxf = xform::trans(centroid1) *
	          xform::trans(trans) * R *
	          xform::trans(-centroid2);

	double delta = 0.0;
	for (size_t i = 0; i < npairs; i++) {
		dvec3 v1 = dvec3(pairs[i].p1);
		dvec3 v2 = dvec3(pairs[i].p2);
		dvec3 n = dvec3(pairs[i].n1);
		delta += sqr((v1 - v2) DOT n);
		v2 = alignxf * v2;
		delta -= sqr((v1 - v2) DOT n);
	}
	return (delta >= 0.0);
}


// Two-plane symmetric point-to-plane alignment.
static bool align_pt2pl_twoplane(const ::std::vector<PtPair> &pairs,
	float scale, point &centroid1, point &centroid2, xform &alignxf)
{
	size_t npairs = pairs.size();
	double A[6][6] = { { 0 } }, b[6] = { 0 };

	// Using n1
	for (size_t i = 0; i < npairs; i++) {
		dvec3 p1 = dvec3(scale * (pairs[i].p1 - centroid1));
		dvec3 p2 = dvec3(scale * (pairs[i].p2 - centroid2));
		dvec3 n = dvec3(pairs[i].n1);
		dvec3 c = p2 CROSS n;
		dvec3 d = p1 - p2;

		double x[6] = { c[0], c[1], c[2], n[0], n[1], n[2] };
		double dn = d DOT n;

		for (int j = 0; j < 6; j++) {
			b[j] += dn * x[j];
			for (int k = j; k < 6; k++)
				A[j][k] += x[j] * x[k];
		}
	}

	// Using n2
	for (size_t i = 0; i < npairs; i++) {
		dvec3 p1 = dvec3(scale * (pairs[i].p1 - centroid1));
		dvec3 p2 = dvec3(scale * (pairs[i].p2 - centroid2));
		dvec3 n = dvec3(pairs[i].n2);
		dvec3 c = p1 CROSS n;
		dvec3 d = p1 - p2;

		double x[6] = { c[0], c[1], c[2], n[0], n[1], n[2] };
		double dn = d DOT n;

		for (int j = 0; j < 6; j++) {
			b[j] += dn * x[j];
			for (int k = j; k < 6; k++)
				A[j][k] += x[j] * x[k];
		}
	}

	// Make matrix symmetric
	for (int j = 1; j < 6; j++)
		for (int k = 0; k < j; k++)
			A[j][k] = A[k][j];

	// Eigen-decomposition and inverse
	double eval[6], einv[6];
	eigdc<double,6>(A, eval);
	for (int i = 0; i < 6; i++) {
		if (eval[i] < 1e-6)
			return false;
		else
			einv[i] = 1.0 / eval[i];
	}

	// Solve system
	eigmult<double,6>(A, einv, b);

	// Extract rotation and translation
	dvec3 rot(b[0], b[1], b[2]), trans(b[3], b[4], b[5]);
	double rotangle = 0.5 * atan(len(rot));
	trans *= 1.0 / scale;
	trans *= cos(rotangle);

	xform R = xform::rot(rotangle, rot);
	alignxf = xform::trans(centroid1) *
	          R * xform::trans(trans) * R *
	          xform::trans(-centroid2);

	return true;
}


// Symmetric point-to-plane alignment.
static bool align_symm(const ::std::vector<PtPair> &pairs,
	float scale, point &centroid1, point &centroid2, xform &alignxf)
{
	size_t npairs = pairs.size();
	double A[6][6] = { { 0 } }, b[6] = { 0 };

	for (size_t i = 0; i < npairs; i++) {
		dvec3 p1 = dvec3(scale * (pairs[i].p1 - centroid1));
		dvec3 p2 = dvec3(scale * (pairs[i].p2 - centroid2));
		dvec3 n = dvec3(pairs[i].n1 + pairs[i].n2);
		dvec3 p = p1 + p2;
		dvec3 c = p CROSS n;
		dvec3 d = p1 - p2;

		double x[6] = { c[0], c[1], c[2], n[0], n[1], n[2] };
		double dn = d DOT n;

		for (int j = 0; j < 6; j++) {
			b[j] += dn * x[j];
			for (int k = j; k < 6; k++)
				A[j][k] += x[j] * x[k];
		}
	}

	// Make matrix symmetric
	for (int j = 1; j < 6; j++)
		for (int k = 0; k < j; k++)
			A[j][k] = A[k][j];

	// Eigen-decomposition and inverse
	double eval[6], einv[6];
	eigdc<double,6>(A, eval);
	for (int i = 0; i < 6; i++) {
		if (eval[i] < 1e-6)
			return false;
		else
			einv[i] = 1.0 / eval[i];
	}

	// Solve system
	eigmult<double,6>(A, einv, b);

	// Extract rotation and translation
	dvec3 rot(b[0], b[1], b[2]), trans(b[3], b[4], b[5]);
	double rotangle = atan(len(rot));
	trans *= 1.0 / scale;
	trans *= cos(rotangle);

	xform R = xform::rot(rotangle, rot);
	alignxf = xform::trans(centroid1) *
	          R * xform::trans(trans) * R *
	          xform::trans(-centroid2);

	return true;
}


// Symmetric point-to-plane Levenberg-Marquardt alignment
static bool align_symm_lm(const ::std::vector<PtPair> &pairs,
	float scale, point &centroid1, point &centroid2, xform &alignxf,
	float lambda)
{
	size_t npairs = pairs.size();
	double A[6][6] = { { 0 } }, b[6] = { 0 };

	for (size_t i = 0; i < npairs; i++) {
		dvec3 p1 = dvec3(scale * (pairs[i].p1 - centroid1));
		dvec3 p2 = dvec3(scale * (pairs[i].p2 - centroid2));
		dvec3 n = dvec3(pairs[i].n1 + pairs[i].n2);
		dvec3 p = p1 + p2;
		dvec3 c = p CROSS n;
		dvec3 d = p1 - p2;

		double x[6] = { c[0], c[1], c[2], n[0], n[1], n[2] };
		double dn = d DOT n;

		for (int j = 0; j < 6; j++) {
			b[j] += dn * x[j];
			for (int k = j; k < 6; k++)
				A[j][k] += x[j] * x[k];
		}
	}

	// Make matrix symmetric
	for (int j = 1; j < 6; j++)
		for (int k = 0; k < j; k++)
			A[j][k] = A[k][j];

	// L-M regularization.  This is the "scale the diagonal" variant,
	// as opposed to the "add a multiple of the identity" variant.
	for (int j = 0; j < 6; j++)
		A[j][j] *= (1.0 + lambda);

	// Eigen-decomposition and inverse
	double eval[6], einv[6];
	eigdc<double,6>(A, eval);
	for (int i = 0; i < 6; i++) {
		if (eval[i] < 1e-6)
			return false;
		else
			einv[i] = 1.0 / eval[i];
	}

	// Solve system
	eigmult<double,6>(A, einv, b);

	// Extract rotation and translation
	dvec3 rot(b[0], b[1], b[2]), trans(b[3], b[4], b[5]);
	double rotangle = atan(len(rot));
	trans *= 1.0 / scale;
	trans *= cos(rotangle);

	xform R = xform::rot(rotangle, rot);
	alignxf = xform::trans(centroid1) *
	          R * xform::trans(trans) * R *
	          xform::trans(-centroid2);

	double delta = 0.0;
	for (size_t i = 0; i < npairs; i++) {
		dvec3 v1 = dvec3(pairs[i].p1);
		dvec3 v2 = dvec3(pairs[i].p2);
		dvec3 n = dvec3(pairs[i].n1 + pairs[i].n2);
		delta += sqr((v1 - v2) DOT n);
		v2 = alignxf * v2;
		n = R * n;
		delta -= sqr((v1 - v2) DOT n);
	}
	return (delta >= 0.0);
}


// Symmetric rotated-normals point-to-plane alignment
static bool align_symm_rotnorm(const ::std::vector<PtPair> &pairs,
	float scale, point &centroid1, point &centroid2, xform &alignxf)
{
	size_t npairs = pairs.size();
	double A[6][6] = { { 0 } }, b[6] = { 0 };

	for (size_t i = 0; i < npairs; i++) {
		dvec3 p1 = dvec3(scale * (pairs[i].p1 - centroid1));
		dvec3 p2 = dvec3(scale * (pairs[i].p2 - centroid2));
		const dvec3 n1 = dvec3(pairs[i].n1);
		const dvec3 n2 = dvec3(pairs[i].n2);
		dvec3 n = n1 + n2;
		dvec3 c = p1 CROSS n2 + p2 CROSS n1;
		dvec3 d = p1 - p2;

		double x[6] = { c[0], c[1], c[2], n[0], n[1], n[2] };
		double dn = d DOT n;

		for (int j = 0; j < 6; j++) {
			b[j] += dn * x[j];
			for (int k = j; k < 6; k++)
				A[j][k] += x[j] * x[k];
		}
	}

	// Make matrix symmetric
	for (int j = 1; j < 6; j++)
		for (int k = 0; k < j; k++)
			A[j][k] = A[k][j];

	// Eigen-decomposition and inverse
	double eval[6], einv[6];
	eigdc<double,6>(A, eval);
	for (int i = 0; i < 6; i++) {
		if (eval[i] < 1e-6)
			return false;
		else
			einv[i] = 1.0 / eval[i];
	}

	// Solve system
	eigmult<double,6>(A, einv, b);

	// Extract rotation and translation
	dvec3 rot(b[0], b[1], b[2]), trans(b[3], b[4], b[5]);
	double rotangle = 0.5 * atan(len(rot));
	trans *= 1.0 / scale;
	trans *= cos(rotangle);

	xform R = xform::rot(rotangle, rot);
	alignxf = xform::trans(centroid1) *
	          R * xform::trans(trans) * R *
	          xform::trans(-centroid2);

	return true;
}


} // namespace trimesh
