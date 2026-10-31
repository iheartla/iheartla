"""Run the Python test suite with code from the Rust compiler.

The Python compiler still runs (its outputs are the fallback for backends the
Rust compiler does not generate yet); outputs for the backends listed in
IHEARTLA_RUST_BACKENDS (default: numpy) are replaced by the Rust compiler's.
A Rust compile error makes the test fail with the compiler's message.

usage: python rust/tools/run_tests_rust.py [test.test_python_expr ...]
       (no arguments: all test modules; prints a per-module summary)
"""
import glob
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
os.environ.setdefault('SDKROOT', '/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk')
BINARY = os.path.join(ROOT, 'rust', 'target', 'release', 'iheartla')
BACKENDS = os.environ.get('IHEARTLA_RUST_BACKENDS', 'numpy').split(',')

import iheartla.la_parser.parser as P
from iheartla.la_tools.la_helper import ParserTypeEnum

_orig = P.compile_la_content
TYPES = {'numpy': ParserTypeEnum.NUMPY}


class RustCompileError(Exception):
    pass


def compile_with_rust(la_content, parser_type=None, *args, **kwargs):
    ret = _orig(la_content, parser_type, *args, **kwargs)
    for b in BACKENDS:
        t = TYPES[b]
        if parser_type is not None and parser_type & t:
            r = subprocess.run([BINARY, 'compile', '--backend', b], input=la_content.encode(), capture_output=True)
            if r.returncode != 0:
                raise RustCompileError(r.stderr.decode())
            ret[t] = r.stdout.decode()
    return ret


P.compile_la_content = compile_with_rust

if __name__ == '__main__':
    mods = sys.argv[1:] or ['test.' + os.path.basename(p)[:-3] for p in sorted(glob.glob('test/test_*.py'))]
    total = failed = 0
    for m in mods:
        suite = unittest.defaultTestLoader.loadTestsFromName(m)
        res = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w')).run(suite)
        n, f = res.testsRun, len(res.failures) + len(res.errors)
        total += n
        failed += f
        print('{:32s} {:3d}/{:3d}'.format(m, n - f, n), flush=True)
        for case, tb in res.failures + res.errors:
            last = [l for l in tb.strip().splitlines() if l.strip()][-1]
            print('    {}: {}'.format(case.id().split('.')[-1], last[:150]))
    print('TOTAL {}/{} passed'.format(total - failed, total))
