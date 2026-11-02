"""Run the NumPy code of the Python and the Rust compilers on the same random
arguments and compare everything they compute.

usage: python rust/tools/value_check.py [id-prefix ...]   (default: x_heartdown)

For each corpus program with a Python NumPy golden output: the arguments come
from the Rust output's generateRandomData() (--main), with function-typed
arguments replaced by deterministic functions of their arguments, so both
classes see the same values. Both classes are instantiated and compared on
every attribute, and every method (local function) is called with probed
arguments: for each parameter, a scalar, an integer, a 2-, 3- or 12-vector or
a 3×3 matrix, taking the first combination the Python code accepts. A value
both fail to compute counts as agreement.
"""
import copy
import glob
import importlib.util
import inspect
import itertools
import json
import os
import subprocess
import sys
import tempfile
import traceback
import warnings

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BINARY = os.path.join(ROOT, 'rust', 'target', 'release', 'iheartla')
TMP = tempfile.mkdtemp()
warnings.filterwarnings('ignore')


def load(code, tag):
    path = os.path.join(TMP, 'gen_{}.py'.format(tag))
    open(path, 'w').write(code)
    spec = importlib.util.spec_from_file_location('gen_' + tag, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def norm(v):
    if callable(v):
        return ('function',)
    if isinstance(v, (set, frozenset)):
        return ('set', sorted(norm(x) for x in v))
    if isinstance(v, (list, tuple)):
        return ('seq', [norm(x) for x in v])
    if hasattr(v, 'toarray'):
        v = v.toarray()
    v = np.asarray(v)
    if v.dtype.kind in 'biuf':
        a = np.asarray(v, dtype=float)
        return ('arr', a.shape if a.ndim and 1 not in a.shape else a.size, np.where(np.isnan(a), np.inf, a.round(7)).ravel().tolist())
    return ('other', repr(v))


def same(a, b):
    """norm()s equal up to a relative tolerance."""
    if a[0] != b[0]:
        return False
    if a[0] == 'arr':
        return a[1] == b[1] and np.allclose(a[2], b[2], rtol=1e-6, atol=1e-9, equal_nan=True)
    if a[0] in ('seq', 'set'):
        return len(a[1]) == len(b[1]) and all(same(x, y) for x, y in zip(a[1], b[1]))
    return a == b


def deterministic(f):
    """A function returning what f returns in shape, but a fixed value per argument tuple."""
    def g(*args):
        shape = np.shape(f(*args))  # (a random value, sized by the arguments)
        key = abs(hash(tuple(np.round(np.asarray(a, dtype=float).ravel(), 9).tobytes() for a in args))) % 2 ** 32
        r = np.random.default_rng(key).standard_normal(shape)
        return float(r) if shape == () else r
    return g


PROBES = [0.7, 2, np.array([0.3, -1.2]), np.array([0.5, 1.5, -0.4]), np.array([[1.2, 0.3, -0.5], [0.1, 0.9, 0.4], [-0.3, 0.2, 1.1]]),
          np.linspace(-1.1, 1.3, 12)]


def call(f, args):
    try:
        with np.errstate(all='ignore'):
            return norm(f(*copy.deepcopy(args)))
    except Exception:  # noqa: BLE001
        return None


def compare(case):
    cwd = os.path.join(ROOT, case['path']) if case.get('path') else None
    r = subprocess.run([BINARY, 'compile', '--backend', 'numpy', '--main'], input=case['src'].encode(), capture_output=True, cwd=cwd)
    if r.returncode:
        return 'rust compile error: ' + r.stderr.decode().strip().splitlines()[0]
    try:
        py_mod = load(case['outputs']['numpy'], 'py')
    except Exception as e:  # noqa: BLE001
        return 'PYTHON OUTPUT BROKEN ({}: {})'.format(type(e).__name__, str(e).splitlines()[0][:80])
    rs_mod = load(r.stdout.decode(), 'rust')
    # (other draws when both fail: the random sizes may be too small, x₁₀ of x ∈ ℝ^n)
    for seed in range(20):
        np.random.seed(seed)
        args = list(rs_mod.generateRandomData() or [])
        args = [deterministic(a) if callable(a) else a for a in args]
        try:
            py = py_mod.heartlib(*copy.deepcopy(args))
        except Exception as e:  # noqa: BLE001
            py = e
        try:
            rs = rs_mod.heartlib(*copy.deepcopy(args))
        except Exception as e:  # noqa: BLE001
            rs = e
        if not (isinstance(py, Exception) and isinstance(rs, Exception)):
            break
    if isinstance(py, Exception) or isinstance(rs, Exception):
        if isinstance(py, Exception) and isinstance(rs, Exception):
            return 'both fail on the random arguments ({}: {})'.format(type(py).__name__, str(py)[:80])
        bad = py if isinstance(py, Exception) else rs
        return 'MISMATCH: only {} fails: {}: {}'.format('Python' if bad is py else 'Rust', type(bad).__name__, str(bad)[:120])
    checked, report, skipped = 0, [], 0
    names = sorted(set(k for k in vars(py) if not k.startswith('_')) | set(k for k in dir(type(py)) if not k.startswith('_')))
    pnames = list(inspect.signature(py_mod.heartlib.__init__).parameters)[1:]
    for k in names:
        va = getattr(py, k, None)
        if not hasattr(rs, k):
            report.append('  missing in Rust output: ' + k)
            continue
        vb = getattr(rs, k)
        if k in pnames:
            continue
        if not inspect.ismethod(va):
            checked += 1
            if not same(norm(va), norm(vb)):
                report.append('  {}: python {} rust {}'.format(k, str(norm(va))[:100], str(norm(vb))[:100]))
            continue
        arity = len(inspect.signature(va).parameters)
        for combo in itertools.product(PROBES, repeat=arity):
            ra = call(va, combo)
            if ra is not None:
                rb = call(vb, combo)
                checked += 1
                if rb is None or not same(ra, rb):
                    report.append('  {}{}: python {} rust {}'.format(k, tuple(np.shape(c) for c in combo), str(ra)[:100], str(rb)[:100]))
                break
        else:
            skipped += 1
    status = 'OK' if not report else 'MISMATCH'
    extra = ', {} functions not probed'.format(skipped) if skipped else ''
    return '{} ({} values compared{})\n{}'.format(status, checked, extra, '\n'.join(report)).rstrip()


if __name__ == '__main__':
    prefixes = sys.argv[1:] or ['x_heartdown']
    for p in sorted(glob.glob(os.path.join(ROOT, 'rust', 'corpus', 'golden', '*.json'))):
        case = json.load(open(p))
        if not any(case['id'].startswith(x) for x in prefixes) or not isinstance(case['outputs'].get('numpy'), str):
            continue
        try:
            res = compare(case)
        except Exception:  # noqa: BLE001
            res = 'driver error:\n' + traceback.format_exc(limit=2)
        print('{}: {}'.format(case['id'], res), flush=True)
