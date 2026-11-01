"""Check continuous optimization (min/max/argmin/argmax over real scalars,
vectors and matrices) in the Eigen backend against the NumPy backend.

usage: python rust/tools/opt_check_cpp.py
  (LBFGSpp: set LBFGSPP_PATH to its include directory; Eigen 3.4: EIGEN_PATH)

For each optimization program of the test suite, with fixed inputs: the
Rust compiler's NumPy output (scipy.optimize; checked against the Python
test suite) and its Eigen output (LBFGSpp) are run and their results
compared. The Python compiler's Eigen output is run too, for reference.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from mesh_check_cpp import SHOW  # noqa: E402

BINARY = os.path.join(ROOT, 'rust', 'target', 'release', 'iheartla')
EIGEN = os.environ.get('EIGEN_PATH', os.path.join(ROOT, 'test', 'third_party', 'eigen'))
LBFGSPP = os.environ.get('LBFGSPP_PATH', os.path.join(ROOT, 'test', 'third_party', 'LBFGSpp', 'include'))
TMP = tempfile.mkdtemp()
rng = np.random.default_rng(3)

CASES = {
    't_gallery_02': [[rng.standard_normal((3, 2)) for _ in range(2)], rng.standard_normal(2), [rng.standard_normal(3) for _ in range(2)]],
    't_gallery_13': [[rng.standard_normal(3) for _ in range(4)] for _ in range(3)],
    't_gallery_14': [[rng.standard_normal(3) for _ in range(4)], [rng.standard_normal((3, 3)) for _ in range(4)]],
    't_others_04': [5.0],
    't_others_05': [np.array([1.0, 2.0, 3.0])],
    't_others_06': [np.array([1.0, -2.0, 3.0])],
    't_others_07': [5.0],
    't_others_08': [[3.0, -2.0, 5.0]],
    't_others_09': [5.0],
    't_others_10': [5.0],
    't_others_11': [5.0],
}


def cpp_value(name, ctype, v):
    """C++ statements defining `name` (of type `ctype`) as the value `v`."""
    flat = lambda a: ', '.join(repr(float(x)) for x in np.asarray(a, dtype=float).ravel())
    if isinstance(v, float):
        return '{} {} = {};'.format(ctype, name, repr(v))
    if isinstance(v, np.ndarray):
        r, c = (v.shape[0], 1) if v.ndim == 1 else v.shape
        return '{} {} = Eigen::Map<const Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>>(std::vector<double>{{{}}}.data(), {}, {});'.format(ctype, name, flat(v), r, c)
    if all(isinstance(x, float) for x in v):  # a set of reals
        return '{} {}{{{}}};'.format(ctype, name, flat(sorted(v)))
    item = re.match(r'std::vector<(.*)>$', ctype).group(1)
    lines = ['{} {};'.format(ctype, name)]
    for k, x in enumerate(v):
        lines.append(cpp_value('{}_{}'.format(name, k), item, x).replace('{} = '.format(item), '{} = '.format(item), 1))
        lines.append('{}.push_back({}_{});'.format(name, name, k))
    return '\n    '.join(lines)


def run_cpp(header, args, attr):
    m = re.search(r'\n\s*heartlib\(\s*(const [^)]*)\)', header)
    params = [re.match(r'const (.*) & (\S+)$', p.strip()).groups() for p in re.split(r',\s*(?=const )', m.group(1).strip())] if m else []
    main = ['#include "gen.h"', SHOW, 'int main() {']
    names = []
    for k, ((ctype, _), v) in enumerate(zip(params, args)):
        main.append('    ' + cpp_value('p{}'.format(k), ctype, v))
        names.append('p{}'.format(k))
    main.append('    std::cout << show(heartlib({}).{}) << std::endl;'.format(', '.join(names), attr))
    main.append('}')
    open(os.path.join(TMP, 'gen.h'), 'w').write(header)
    open(os.path.join(TMP, 'main.cpp'), 'w').write('\n'.join(main))
    exe = os.path.join(TMP, 'main')
    r = subprocess.run(['clang++', '-std=c++17', '-O1', '-I' + EIGEN, '-I' + LBFGSPP, '-I' + os.path.join(ROOT, 'iheartla', 'mesh', 'Cpp', 'include'),
                        '-I' + os.path.join(ROOT, 'test', 'third_party', 'autodiff'), '-o', exe, os.path.join(TMP, 'main.cpp')], capture_output=True, text=True)
    if r.returncode:
        return 'compile error: ' + next((l for l in r.stderr.splitlines() if 'error' in l), '?')[:150]
    r = subprocess.run([exe], capture_output=True, text=True)
    if r.returncode:
        return 'run error: ' + (r.stderr.strip().splitlines() or ['?'])[-1][:150]
    return json.loads(r.stdout)


def values(x):
    """A result as a flat list of floats."""
    if isinstance(x, list) and len(x) == 2 and isinstance(x[0], str):
        return np.asarray(x[1], dtype=float).ravel()
    return np.asarray(x, dtype=float).ravel()


for case, args in CASES.items():
    d = json.load(open(os.path.join(ROOT, 'rust', 'corpus', 'golden', case + '.json')))
    src = d['src']
    outs = {b: subprocess.run([BINARY, 'compile', '--backend', b], input=src.encode(), capture_output=True).stdout.decode() for b in ['numpy', 'eigen']}
    path = os.path.join(TMP, 'np_{}.py'.format(case))
    open(path, 'w').write(outs['numpy'])
    spec = importlib.util.spec_from_file_location('np_' + case, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    attr = 'b' if src.strip().startswith('b =') else 'ret'
    py_args = [set(a) if case == 't_others_08' else a for a in args]
    want = values(np.asarray(getattr(mod.heartlib(*py_args), attr), dtype=float))
    got = run_cpp(outs['eigen'], args, attr)
    py_cpp = run_cpp(d['outputs']['eigen'], args, attr)
    if isinstance(got, str):
        status = 'RUST C++ ' + got
    else:
        g = values(got)
        ok = g.shape == want.shape and np.allclose(g, want, rtol=1e-4, atol=1e-4)
        status = '{}  numpy {}  rust c++ {}'.format('OK' if ok else 'MISMATCH', np.round(want, 5).tolist(), np.round(g, 5).tolist())
    pyc = py_cpp if isinstance(py_cpp, str) else np.round(values(py_cpp), 5).tolist()
    print('{:13s} {}   (python c++: {})'.format(case, status, pyc), flush=True)
