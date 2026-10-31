"""Compare compile times of the Python and Rust compilers.

usage: python rust/tools/bench.py   (from the repository root)

1. The `T₁` program of test_gallery_10 (as in PERFORMANCE.md): NumPy, and
   NumPy + Eigen, in-process for Python and as a subprocess for Rust (so the
   Rust numbers include process start-up).
2. Every test-suite program (rust/corpus/tests.jsonl), NumPy + Eigen: total.
3. Parsing alone: iheartla/mesh/Neighborhoods.hlang (TatSu: about 1.7 s per
   parse; each module is parsed twice).
"""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
BINARY = os.path.join(ROOT, 'rust', 'target', 'release', 'iheartla')

from iheartla.la_parser.parser import compile_la_content
from iheartla.la_tools.la_helper import ParserTypeEnum

T1 = """`T₁` = 1/sqrt(2)U[0 0 0
                  0 0 -1
                  0 1 0]Vᵀ
        where
        U: ℝ^(3×3)
        V: ℝ^(3×3)"""


def best(f, n=5):
    times = []
    for _ in range(n):
        t = time.perf_counter()
        f()
        times.append(time.perf_counter() - t)
    return min(times)


def rust(src, backends):
    for b in backends:
        r = subprocess.run([BINARY, 'compile', '--backend', b], input=src.encode(), capture_output=True)
        if r.returncode:
            raise RuntimeError(r.stderr.decode())


def python(src, t):
    compile_la_content(src, t)


def row(label, py, rs):
    print('{:44s} {:9.4f} s {:9.4f} s {:8.0f}x'.format(label, py, rs, py / rs))


print('{:44s} {:>11s} {:>11s} {:>9s}'.format('', 'Python', 'Rust', 'speed-up'))
NP, EI = ParserTypeEnum.NUMPY, ParserTypeEnum.EIGEN
python(T1, NP)  # warm up imports and grammar construction
row('T1, NumPy', best(lambda: python(T1, NP)), best(lambda: rust(T1, ['numpy'])))
row('T1, NumPy + Eigen', best(lambda: python(T1, NP | EI)), best(lambda: rust(T1, ['numpy', 'eigen'])))

tests = [json.loads(l)['src'] for l in open('rust/corpus/tests.jsonl')]
ok = []
for s in tests:
    try:
        python(s, NP | EI)
        rust(s, ['numpy', 'eigen'])
        ok.append(s)
    except Exception:
        pass
py = best(lambda: [python(s, NP | EI) for s in ok], 1)
rs = best(lambda: [rust(s, ['numpy', 'eigen']) for s in ok], 1)
row('{} test programs, NumPy + Eigen'.format(len(ok)), py, rs)

# parsing alone
hlang = open('iheartla/mesh/Neighborhoods.hlang').read()
from iheartla.la_parser.parser import get_default_parser
parser = get_default_parser()  # (the first-pass parser)
rs = best(lambda: subprocess.run([BINARY, 'parse', '--init'], input=hlang.encode(), capture_output=True, check=True), 3)
try:
    py = best(lambda: parser.parse(hlang, parseinfo=True), 1)
    row('parse Neighborhoods.hlang (first pass)', py, rs)
except Exception as e:
    print('parse Neighborhoods.hlang: Rust {:.4f} s (Python parse failed: {})'.format(rs, str(e).splitlines()[0][:60]))
