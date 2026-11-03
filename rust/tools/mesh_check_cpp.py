"""Check the Rust compiler's Eigen (C++) output for I❤️MESH programs against
its NumPy output (which tools/mesh_check.py checks against the Python
compiler's).

usage: python rust/tools/mesh_check_cpp.py [program.ila|Module.hlang ...]

The NumPy class runs on an octahedron (with the I❤️MESH runtime); a generated
C++ main builds the same mesh (a FaceMesh from the NumPy mesh's boundary
matrices, so elements are numbered alike), evaluates every attribute and
every function on the argument combinations that succeed in NumPy, and
prints the values in the same normalized form. The runtime
(iheartla/mesh/Cpp) is compiled with clang++.
"""
import glob
import importlib.util
import inspect
import itertools
import json
import re
import os
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'iheartla', 'mesh', 'Python'))
import triangle_mesh  # noqa: E402  (the I❤️MESH runtime)

BINARY = os.path.join(ROOT, 'rust', 'target', 'release', 'iheartla')
CPP = os.path.join(ROOT, 'iheartla', 'mesh', 'Cpp')
EIGEN = os.environ.get('EIGEN_PATH', '/opt/homebrew/include/eigen3')
T = np.array([[0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1], [5, 2, 1], [5, 3, 2], [5, 4, 3], [5, 1, 4]])
TMP = tempfile.mkdtemp()

SHOW = r'''
#include <sstream>
#include <tuple>
std::string show(int v) { return "[\"num\"," + std::to_string(v) + "]"; }
std::string show(long v) { return "[\"num\"," + std::to_string(v) + "]"; }
std::string show(double v) { std::ostringstream s; s.precision(9); s << std::fixed << v; return "[\"num\"," + s.str() + "]"; }
std::string show(const std::vector<int>& v) { std::string s = "[\"set\",["; for (size_t i = 0; i < v.size(); i++) s += (i ? "," : "") + std::to_string(v[i]); return s + "]]"; }
template<typename T> std::string show(const std::vector<T>& v) { std::string s = "[\"seq\",["; for (size_t i = 0; i < v.size(); i++) s += (i ? "," : "") + show(v[i]); return s + "]]"; }
template<typename Derived> std::string show_dense(const Eigen::MatrixBase<Derived>& m, const char* tag) {
    std::ostringstream s; s.precision(9); s << std::fixed << "[\"" << tag << "\",[";
    for (int i = 0; i < m.rows(); i++) { if (i) s << ","; if (m.cols() > 1 || std::string(tag) == "mat") s << "["; for (int j = 0; j < m.cols(); j++) { if (j) s << ","; s << double(m(i, j)); } if (m.cols() > 1 || std::string(tag) == "mat") s << "]"; }
    s << "]]"; return s.str(); }
template<typename S, int R, int C> std::string show(const Eigen::Matrix<S, R, C>& m) { return show_dense(m, "arr"); }
template<typename S> std::string show(const Eigen::SparseMatrix<S>& m) { return show_dense(Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic>(Eigen::MatrixXd(m.template cast<double>())), "mat"); }
template<typename... Ts, size_t... I> std::string show_tuple(const std::tuple<Ts...>& t, std::index_sequence<I...>) { std::string s = "[\"seq\",["; ((s += (I ? "," : "") + show(std::get<I>(t))), ...); return s + "]]"; }
template<typename... Ts> std::string show(const std::tuple<Ts...>& t) { return show_tuple(t, std::index_sequence_for<Ts...>{}); }
'''


def norm(v):
    """Values as JSON-able lists, as the C++ show() prints them."""
    if isinstance(v, (set, frozenset)):
        return ['set', sorted(int(x) for x in v)]
    if isinstance(v, (list, tuple)):
        if len(v) == 0:
            return ['set', []]
        return ['seq', [norm(x) for x in v]]
    if hasattr(v, 'toarray'):
        return ['mat', np.asarray(v.toarray(), dtype=float).round(6).tolist()]
    if isinstance(v, np.ndarray):
        return ['arr', np.asarray(v, dtype=float).ravel().round(6).tolist()] if v.ndim <= 1 or 1 in v.shape else ['arr', np.asarray(v, dtype=float).round(6).tolist()]
    if isinstance(v, (int, np.integer)):
        return ['num', float(v)]
    if isinstance(v, (float, np.floating)):
        return ['num', 'nan' if np.isnan(v) else round(float(v), 6)]
    return ['other', repr(type(v))]


def renorm(x):
    """Round C++ values like norm() does."""
    if isinstance(x, list) and len(x) == 2 and x[0] in ('num',):
        return ['num', 'nan' if np.isnan(float(x[1])) else round(float(x[1]), 6)]
    if isinstance(x, list) and len(x) == 2 and x[0] in ('arr', 'mat'):
        return [x[0], np.round(np.asarray(x[1], dtype=float), 6).tolist()]
    if isinstance(x, list) and len(x) == 2 and x[0] == 'seq':
        return ['seq', [renorm(y) for y in x[1]]]
    return x


def cpp_matrix(name, m):
    m = m.tocoo()
    lines = ['std::vector<Eigen::Triplet<int>> t_{};'.format(name)]
    for i, j, v in zip(m.row, m.col, m.data):
        lines.append('t_{}.emplace_back({}, {}, {});'.format(name, i, j, int(v)))
    lines.append('Eigen::SparseMatrix<int> {}({}, {}); {}.setFromTriplets(t_{}.begin(), t_{}.end());'.format(name, m.shape[0], m.shape[1], name, name, name))
    return '\n    '.join(lines)


def check(path):
    src = open(path).read()
    outs = {}
    for b in ['numpy', 'eigen']:
        r = subprocess.run([BINARY, 'compile', '--backend', b], input=src.encode(), capture_output=True)
        if r.returncode:
            return 'rust compile error: ' + r.stderr.decode().strip().splitlines()[0]
        outs[b] = r.stdout.decode()
    py_path = os.path.join(TMP, 'gen_np.py')
    open(py_path, 'w').write(outs['numpy'])
    spec = importlib.util.spec_from_file_location('gen_np', py_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cls = mod.heartlib
    mesh = triangle_mesh.TriangleMesh(T)
    nv = mesh.n_vertices()
    pnames = list(inspect.signature(cls.__init__).parameters)[1:]
    x = np.random.default_rng(1).standard_normal((nv, 3))
    obj = cls(*[mesh if p == 'M' else x for p in pnames])
    n = max(nv, mesh.n_edges(), mesh.n_faces())
    # Python NFKC-normalizes identifiers (ϕ becomes φ): use the C++ spelling

    import unicodedata
    cpp_names = {unicodedata.normalize('NFKC', w): w for w in re.findall(r'\w+', outs['eigen'])}
    expected, calls = [], []
    for k in sorted(set(k for k in vars(obj) if not k.startswith('_')) | set(k for k in dir(cls) if not k.startswith('_'))):
        v = getattr(obj, k)
        if not callable(v):
            if k not in pnames:
                expected.append(norm(v))
                calls.append('obj.{}'.format(cpp_names.get(k, k)))
            continue
        arity = len(inspect.signature(v).parameters)
        for combo in itertools.product(range(n) if arity == 1 else range(nv), repeat=arity):
            try:
                res = v(*combo)
            except Exception:  # noqa: BLE001
                continue
            expected.append(norm(res))
            calls.append('obj.{}({})'.format(cpp_names.get(k, k), ', '.join(map(str, combo))))
    bm1, bm2 = mesh.BoundaryMatrices()
    main = ['#include "gen.h"', SHOW, 'int main() {', '    ' + cpp_matrix('bm1', bm1), '    ' + cpp_matrix('bm2', bm2), '    FaceMesh M(bm1, bm2);']
    args = []
    for p in pnames:
        if p == 'M':
            args.append('M')
        else:
            main.append('    std::vector<Eigen::Matrix<double, 3, 1>> {}({});'.format(p, nv))
            for i in range(nv):
                main.append('    {}[{}] << {};'.format(p, i, ', '.join(repr(float(c)) for c in x[i])))
            args.append(p)
    main.append('    heartlib obj({});'.format(', '.join(args)))
    for c in calls:
        main.append('    std::cout << show({}) << "\\n";'.format(c))
    main.append('}')
    open(os.path.join(TMP, 'gen.h'), 'w').write(outs['eigen'])
    open(os.path.join(TMP, 'main.cpp'), 'w').write('\n'.join(main))
    exe = os.path.join(TMP, 'main')
    srcs = [os.path.join(CPP, 'src', f) for f in ['MeshHelper.cpp', 'TriangleMesh.cpp', 'Connectivity.cpp', 'dec_util.cpp']]
    r = subprocess.run(['clang++', '-std=c++17', '-O1', '-I' + EIGEN, '-I' + os.path.join(CPP, 'include'), '-o', exe, os.path.join(TMP, 'main.cpp')] + srcs, capture_output=True, text=True)
    if r.returncode:
        errs = [l for l in r.stderr.splitlines() if 'error' in l][:6]
        return 'C++ compile error:\n  ' + '\n  '.join(errs)
    r = subprocess.run([exe], capture_output=True, text=True)
    if r.returncode:
        return 'C++ run error (exit {}): {}'.format(r.returncode, r.stderr[-300:])
    # (C++ prints NaN as nan or -nan)
    got = [renorm(json.loads(re.sub(r'-?\bnan\b', 'NaN', l))) for l in r.stdout.splitlines()]
    bad = [(c, e, g) for c, e, g in zip(calls, expected, got) if e != g]
    if len(got) != len(expected):
        return 'output count differs: {} vs {}'.format(len(got), len(expected))
    rep = '\n'.join('  {}: numpy {} c++ {}'.format(c, e, g) for c, e, g in bad[:10])
    return '{} ({} values compared, {} differ){}'.format('OK' if not bad else 'MISMATCH', len(calls), len(bad), '\n' + rep if bad else '')


if __name__ == '__main__':
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, 'rust', 'corpus', 'mesh', '*.ila'))) + [
        os.path.join(ROOT, 'iheartla', 'mesh', n + '.hlang') for n in ['FundamentalMeshAccessors', 'Neighborhoods']]
    for f in files:
        print('{}: {}'.format(os.path.basename(f), check(f)), flush=True)
