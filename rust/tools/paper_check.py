"""Check the Rust compiler's output for four I❤️MESH paper examples against the
C++ that the paper's own compiler generated (the supplement's heartlib.h).

usage: python rust/tools/paper_check.py SUPPLEMENT_DIR [example ...]
  SUPPLEMENT_DIR: the unzipped supplemental_material/ of
  https://iheartla.github.io/iheartmesh/supplemental_material.zip

The examples (in rust/corpus/iheartmesh) use features checked nowhere else:
geodesic_distance (sequence(), unions over a subscript), point_cloud (a set of
vectors, rows from it, svd), mesh_parameterization and mesh_deformation
(gradients and Hessians). paper_check/driver.cpp runs each on a small mesh and
prints its values. It is built twice: with the paper's heartlib.h and runtime
(resource/), and with the Rust compiler's Eigen output and this repository's
runtime (iheartla/mesh/Cpp); the outputs must agree. The Rust compiler's NumPy
output runs on the same values and is compared with them too (normals up to
sign: SVD leaves it free). C++ derivatives need autodiff (Homebrew: autodiff)
and Eigen 3.4 (test/fetch_deps.sh); NumPy derivatives need autograd.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import warnings

import numpy as np
import scipy.sparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BINARY = os.path.join(ROOT, 'rust', 'target', 'release', 'iheartla')
CORPUS = os.path.join(ROOT, 'rust', 'corpus', 'iheartmesh')
EIGEN = os.environ.get('EIGEN_PATH', os.path.join(ROOT, 'test', 'third_party', 'eigen'))
AUTODIFF = os.environ.get('AUTODIFF_PATH', '/opt/homebrew/include')
EXAMPLES = ['geodesic_distance', 'point_cloud', 'mesh_parameterization', 'mesh_deformation']
TMP = tempfile.mkdtemp()
sys.path.insert(0, os.path.join(HERE, 'mesh_runtime'))
warnings.filterwarnings('ignore')


def build_and_run(example, header, runtime, tag):
    """The driver's output with a heartlib.h and a runtime (include/, src/), as lines."""
    d = os.path.join(TMP, tag)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'heartlib.h'), 'w') as f:
        f.write(header)
    exe = os.path.join(d, example)
    srcs = [os.path.join(runtime, 'src', s) for s in ['MeshHelper.cpp', 'TriangleMesh.cpp', 'Tetrahedron.cpp', 'Connectivity.cpp', 'dec_util.cpp']]
    r = subprocess.run(['clang++', '-std=c++17', '-O1', '-w', '-DEX_' + example, '-I' + d, '-I' + EIGEN, '-I' + AUTODIFF,
                        '-I' + os.path.join(runtime, 'include'), '-o', exe, os.path.join(HERE, 'paper_check', 'driver.cpp')] + srcs,
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError('{} C++ compile error: {}'.format(tag, ' | '.join(l for l in r.stderr.splitlines() if 'error' in l)[:400]))
    r = subprocess.run([exe], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError('{} C++ run error: {}'.format(tag, r.stderr[-300:]))
    return [l for l in r.stdout.splitlines() if not l.startswith('Total ')]


def values(lines):
    """{label: numbers} from the driver's lines ("label n1 n2 ..." or "label {1 2 }{3 }")."""
    out = {}
    for l in lines:
        parts = l.replace('{', ' { ').replace('}', ' } ').split()
        label, rest = parts[0], parts[1:]
        if label in ('Normal', 'UpdateStep'):
            label, rest = label + ' ' + rest[0], rest[1:]
        out[label] = [x if x in '{}' else float(x) for x in rest]
    return out


def same(a, b, up_to_sign=False):
    if len(a) != len(b) or any((x in '{}') != (y in '{}') for x, y in zip(a, b) if isinstance(x, str) or isinstance(y, str)):
        return False
    x = np.array([v for v in a if not isinstance(v, str)], dtype=float)
    y = np.array([v for v in b if not isinstance(v, str)], dtype=float)
    ok = lambda u, v: np.allclose(u, v, rtol=1e-6, atol=1e-8, equal_nan=True)
    return ok(x, y) or (up_to_sign and ok(x, -y))


def numpy_lines(example, code):
    """The driver's values from the Rust compiler's NumPy output (the same meshes and arguments)."""
    path = os.path.join(TMP, 'np_' + example + '.py')
    with open(path, 'w') as f:
        f.write(code)
    spec = importlib.util.spec_from_file_location('np_' + example, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    import triangle_mesh
    pos = lambda i: np.array([np.sin(1.3 * i + 0.2), np.cos(0.7 * i + 1.1), np.sin(2.1 * i + 0.5)])
    show = lambda v: ' '.join(repr(float(x)) for x in np.ravel(v))
    sets = lambda s: '{' + ''.join('{} '.format(v) for v in sorted(s)) + '}'
    octahedron = np.array([[0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1], [5, 2, 1], [5, 3, 2], [5, 4, 3], [5, 1, 4]])
    out = []
    if example == 'geodesic_distance':
        h = m.heartlib(triangle_mesh.TriangleMesh(octahedron), np.array([pos(i) for i in range(6)]))
        d = [0, 0.4, 0.7, 1.1, 0.5, 2.0]
        for i in range(6):
            for j in range(6):
                for k in range(6):
                    if len({i, j, k}) == 3:
                        with np.errstate(all='ignore'):
                            out.append('UpdateStep {}{}{} {}'.format(i, j, k, float(h.UpdateStep(i, j, k, d))))
        U = [frozenset({0}), frozenset({1, 2}), frozenset({5})]
        out.append('GetNextLevel ' + sets(h.GetNextLevel(U)))
        out.append('GetRangeLevel01 ' + sets(h.GetRangeLevel(U, 0, 1)))
        out.append('GetRangeLevel12 ' + sets(h.GetRangeLevel(U, 1, 2)))
        out.append('GetLevelSequence ' + ''.join(sets(s) for s in h.GetLevelSequence([frozenset({0})])))
    elif example == 'point_cloud':
        class EdgeMesh:  # the octahedron's vertices and edges
            def __init__(self, tm):
                self.tm = tm

            def ElementSets(self):
                return self.tm.ElementSets()[:2]

            def BoundaryMatrices(self):
                return self.tm.BoundaryMatrices()[0]

            def UnsignedBoundaryMatrices(self):
                return self.tm.UnsignedBoundaryMatrices()[0]

            def __getattr__(self, k):
                return getattr(self.tm, k)
        h = m.heartlib(EdgeMesh(triangle_mesh.TriangleMesh(octahedron)), np.array([pos(i) for i in range(6)]))
        out += ['Normal {} {}'.format(i, show(h.Normal(i))) for i in range(6)]
    else:
        psd = lambda A: scipy.sparse.csr_matrix(A)
        if example == 'mesh_parameterization':
            xb = np.array([pos(i) for i in range(6)])
            x = np.array([[pos(i)[0] + 0.05 * i, pos(i)[1] - 0.03 * i] for i in range(6)])
            h = m.heartlib(triangle_mesh.TriangleMesh(octahedron), xb, x, 1e-3, psd)
        else:
            T = np.array([[0, 1, 2, 3], [1, 2, 3, 4]])
            xb = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 1]], dtype=float)
            h = m.heartlib(triangle_mesh.TriangleMesh(T), xb, xb + 0.05 * np.array([pos(i) for i in range(5)]), [0], [[0.1, 0, 0]], 2.0, 1e-3, psd)
        H = h.H.toarray() if hasattr(h.H, 'toarray') else h.H
        out += ['e {}'.format(float(h.e)), 'G ' + show(h.G), 'H ' + show(H)]
    return out


def check(supplement, example):
    src = open(os.path.join(CORPUS, example + '.hlang')).read()
    outs = {}
    for b in ['eigen', 'numpy']:
        r = subprocess.run([BINARY, 'compile', '--backend', b], input=src.encode(), capture_output=True, cwd=CORPUS)
        if r.returncode:
            return 'rust compile error: ' + r.stderr.decode().strip().splitlines()[0]
        outs[b] = r.stdout.decode()
    paper = build_and_run(example, open(os.path.join(supplement, 'examples', example, 'heartlib.h')).read(),
                          os.path.join(supplement, 'resource'), 'paper')
    rust = build_and_run(example, outs['eigen'], os.path.join(ROOT, 'iheartla', 'mesh', 'Cpp'), 'rust')
    expected, report = values(paper), []
    for tag, got in [('C++', values(rust)), ('NumPy', values(numpy_lines(example, outs['numpy'])))]:
        if set(got) != set(expected):
            report.append('  {}: values {} vs the paper\'s {}'.format(tag, sorted(got), sorted(expected)))
            continue
        for k, v in expected.items():
            if not same(got[k], v, up_to_sign=k.startswith('Normal')):
                report.append('  {} {}: {} vs the paper\'s {}'.format(tag, k, got[k][:6], v[:6]))
    n = sum(len([x for x in v if not isinstance(x, str)]) for v in expected.values())
    return ('OK' if not report else 'MISMATCH') + ' ({} values, C++ and NumPy)'.format(n) + ''.join('\n' + l for l in report[:20])


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for ex in sys.argv[2:] or EXAMPLES:
        try:
            res = check(sys.argv[1], ex)
        except Exception as e:  # noqa: BLE001
            res = 'error: {}'.format(e)
        print('{}: {}'.format(ex, res), flush=True)
