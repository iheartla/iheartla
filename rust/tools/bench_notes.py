"""Timings of the Python and Rust compilers for notes/Performance.md.

usage: python rust/tools/bench_notes.py

Python: compile time inside a fresh process (after imports), first and repeat
compile. Rust: wall time of the `iheartla` process (start-up included; one
process per output, as the CLI compiles one backend per run), best of 5.
"""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BINARY = os.path.join(ROOT, 'rust', 'target', 'release', 'iheartla')
T1 = """`T₁` = 1/sqrt(2)U[0 0 0
                  0 0 -1
                  0 1 0]Vᵀ
        where
        U: ℝ^(3×3)
        V: ℝ^(3×3)"""
MESH = open(os.path.join(ROOT, 'rust', 'corpus', 'mesh', 'one_ring.ila')).read()
ALL = ['numpy', 'eigen', 'latex', 'mathjax', 'matlab', 'macromathjax']

PY = r'''
import sys, time, json
sys.path.insert(0, %r)
from iheartla.la_parser.parser import compile_la_content
from iheartla.la_tools.la_helper import ParserTypeEnum as P
src = json.loads(sys.argv[1]); which = sys.argv[2]
t = P.NUMPY if which == 'numpy' else (P.NUMPY | P.EIGEN | P.LATEX | P.MATHJAX | P.MATLAB | P.MACROMATHJAX)
times = []
for _ in range(2):
    a = time.perf_counter(); compile_la_content(src, t); times.append(time.perf_counter() - a)
print(json.dumps(times))
''' % ROOT


def python(src, which):
    r = subprocess.run([sys.executable, '-c', PY, json.dumps(src), which], capture_output=True, text=True, cwd=ROOT)
    return json.loads(r.stdout.strip().splitlines()[-1])


def rust(src, backends, n=5):
    best = None
    for _ in range(n):
        t = time.perf_counter()
        for b in backends:
            subprocess.run([BINARY, 'compile', '--backend', b], input=src.encode(), capture_output=True, check=True)
        e = time.perf_counter() - t
        best = e if best is None else min(best, e)
    return best


rows = []
for label, src in [('Plain program (T₁)', T1), ('I❤️MESH program (one_ring)', MESH)]:
    for which, backends in [('numpy', ['numpy']), ('all', ALL)]:
        first, repeat = python(src, which)
        rs = rust(src, backends)
        rows.append((label, 'NumPy' if which == 'numpy' else 'all 6 outputs', first, repeat, rs))
print('| Program | Outputs | Python first | Python repeat | Rust | Speed-up (first) |')
print('|---|---|---|---|---|---|')
for label, outs, first, repeat, rs in rows:
    print('| {} | {} | {:.3f} s | {:.3f} s | {:.3f} s | {:.0f}× |'.format(label, outs, first, repeat, rs, first / rs))

# the test programs
tests = [json.loads(l)['src'] for l in open(os.path.join(ROOT, 'rust', 'corpus', 'tests.jsonl'))]
PYALL = r'''
import sys, time, json
sys.path.insert(0, %r)
from iheartla.la_parser.parser import compile_la_content
from iheartla.la_tools.la_helper import ParserTypeEnum as P
srcs = json.load(open(sys.argv[1])); ok = 0
a = time.perf_counter()
for s in srcs:
    try:
        compile_la_content(s, P.NUMPY | P.EIGEN); ok += 1
    except Exception:
        pass
print(json.dumps([time.perf_counter() - a, ok]))
''' % ROOT
path = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'bench_tests.json')
json.dump(tests, open(path, 'w'))
r = subprocess.run([sys.executable, '-c', PYALL, path], capture_output=True, text=True, cwd=ROOT)
py_t, ok = json.loads(r.stdout.strip().splitlines()[-1])
t = time.perf_counter()
for s in tests:
    for b in ['numpy', 'eigen']:
        subprocess.run([BINARY, 'compile', '--backend', b], input=s.encode(), capture_output=True)
rs_t = time.perf_counter() - t
print('\n{} test programs ({} compile in Python), NumPy + Eigen: Python {:.1f} s (one process), Rust {:.1f} s ({} processes)'.format(
    len(tests), ok, py_t, rs_t, 2 * len(tests)))
