"""Run I❤️MESH programs compiled by the Python and the Rust compilers on the
same mesh and compare everything they compute.

usage: python rust/tools/mesh_check.py [program.ila|Module.hlang ...]
  (default: rust/corpus/mesh/*.ila and the iheartla/mesh/*.hlang modules
   for triangle meshes)

For each program: both NumPy outputs are imported (with the runtime shim in
rust/tools/mesh_runtime), instantiated with a small closed triangle mesh
(plus a random per-vertex ℝ³ field for sequence parameters), and compared:
every attribute, and every method (of the program and of its nested module
instances) called with every combination of element indices and a point in ℝ³. A call that
fails in both counts as agreement.
"""
import glob
import importlib.util
import itertools
import os
import subprocess
import sys
import tempfile
import traceback

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, 'mesh_runtime'))
sys.path.insert(1, ROOT)
BINARY = os.path.join(ROOT, 'rust', 'target', 'release', 'iheartla')

import triangle_mesh  # noqa: E402  (the shim)
from iheartla.la_parser.parser import compile_la_content  # noqa: E402
from iheartla.la_tools.la_helper import ParserTypeEnum  # noqa: E402

# an octahedron: closed, 6 vertices, 12 edges, 8 faces
T = np.array([[0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1], [5, 2, 1], [5, 3, 2], [5, 4, 3], [5, 1, 4]])


def load(code, tag):
    d = tempfile.mkdtemp()
    path = os.path.join(d, 'gen_{}.py'.format(tag))
    open(path, 'w').write(code)
    spec = importlib.util.spec_from_file_location('gen_' + tag, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.heartlib


def norm(v):
    if isinstance(v, (set, frozenset)):
        return ('set', sorted(int(x) for x in v))
    if isinstance(v, (list, tuple)):
        if len(v) == 0:
            return ('set', [])  # the Python compiler pads a CellularSet with []
        return ('seq', [norm(x) for x in v])
    if hasattr(v, 'toarray'):
        return ('mat', np.asarray(v.toarray()).round(9).tolist())
    if isinstance(v, np.ndarray):
        return ('arr', np.where(np.isnan(v), np.inf, v.round(9)).tolist() if v.dtype.kind == 'f' else v.tolist())
    if isinstance(v, (int, np.integer)):
        return ('num', int(v))
    if isinstance(v, (float, np.floating)):
        return ('num', 'nan' if np.isnan(v) else round(float(v), 9))
    return ('other', repr(type(v)))


def call(f, args):
    try:
        return norm(f(*args))
    except Exception:  # noqa: BLE001
        return ('error',)  # (failing in both counts as agreement, whatever the exception)


def compare(src, name):
    py = compile_la_content(src, ParserTypeEnum.NUMPY)[ParserTypeEnum.NUMPY]
    r = subprocess.run([BINARY, 'compile', '--backend', 'numpy'], input=src.encode(), capture_output=True)
    if r.returncode:
        return 'rust compile error: ' + r.stderr.decode().strip().splitlines()[0]
    a_cls, b_cls = load(py, 'py'), load(r.stdout.decode(), 'rust')
    mesh = triangle_mesh.TriangleMesh(T)
    nv = mesh.n_vertices()
    import inspect
    pnames = list(inspect.signature(a_cls.__init__).parameters)[1:]
    rng = np.random.default_rng(1)
    args = [mesh if p == 'M' else rng.standard_normal((nv, 3)) for p in pnames]
    a, b = a_cls(*args), b_cls(*args)
    point = np.array([0.3, -0.2, 0.1])
    n = max(nv, mesh.n_edges(), mesh.n_faces())
    checked = mismatches = 0
    report = []
    names = sorted(set(k for k in vars(a) if not k.startswith('_')) | set(k for k in dir(a_cls) if not k.startswith('_')))
    for k in names:
        va, vb = getattr(a, k, None), getattr(b, k, None)
        if vb is None and va is not None:
            report.append('  missing in Rust output: ' + k)
            mismatches += 1
            continue
        if not callable(va):
            checked += 1
            if norm(va) != norm(vb):
                mismatches += 1
                report.append('  attribute {} differs'.format(k))
            continue
        arity = len(inspect.signature(va).parameters)
        # element indices, and a point for parameters in ℝ³ (𝐩 in winding_number)
        domain = list(range(n) if arity == 1 else range(nv)) + [point]
        for combo in itertools.product(domain, repeat=arity):
            ra, rb = call(va, combo), call(vb, combo)
            checked += 1
            if ra != rb:
                mismatches += 1
                if mismatches <= 40:
                    report.append('  {}{}: python {} rust {}'.format(k, combo, ra, rb))
    status = 'OK' if mismatches == 0 else 'MISMATCH'
    return '{} ({} values compared, {} differ)\n{}'.format(status, checked, mismatches, '\n'.join(report)).rstrip()


if __name__ == '__main__':
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, 'rust', 'corpus', 'mesh', '*.ila'))) + [
        os.path.join(ROOT, 'iheartla', 'mesh', n + '.hlang') for n in ['FundamentalMeshAccessors', 'Neighborhoods']]
    for f in files:
        try:
            res = compare(open(f).read(), os.path.basename(f))
        except Exception:  # noqa: BLE001
            res = 'driver error:\n' + traceback.format_exc(limit=3)
        print('{}: {}'.format(os.path.basename(f), res), flush=True)
