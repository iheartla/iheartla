"""Compile time of an I❤️MESH program (one that imports modules): Python vs Rust.

usage: python rust/tools/bench_mesh.py [program.ila]   (default: corpus/mesh/one_ring.ila)
"""
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
BINARY = os.path.join(ROOT, 'rust', 'target', 'release', 'iheartla')
from iheartla.la_parser.parser import compile_la_content  # noqa: E402
from iheartla.la_tools.la_helper import ParserTypeEnum as P  # noqa: E402

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'rust', 'corpus', 'mesh', 'one_ring.ila')
src = open(path).read()


def timed(f):
    t = time.perf_counter()
    f()
    return time.perf_counter() - t


def rust(backends):
    for b in backends:
        subprocess.run([BINARY, 'compile', '--backend', b], input=src.encode(), capture_output=True, check=True)


rows = [
    ('NumPy', P.NUMPY, ['numpy']),
    ('NumPy + LaTeX + MathJax', P.NUMPY | P.LATEX | P.MATHJAX, ['numpy', 'latex', 'mathjax']),
]
print('{}\n{:28s} {:>10s} {:>10s} {:>9s}'.format(os.path.basename(path), '', 'Python', 'Rust', 'speed-up'))
for label, t, b in rows:
    py = timed(lambda: compile_la_content(src, t))
    rs = min(timed(lambda: rust(b)) for _ in range(3))
    print('{:28s} {:9.2f}s {:9.3f}s {:8.0f}x'.format(label, py, rs, py / rs))
