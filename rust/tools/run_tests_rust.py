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
if sys.platform == 'darwin' and 'SDKROOT' not in os.environ:
    # (cppyy's C++ compiler needs the macOS SDK: the current one, as xcrun reports it)
    _sdk = subprocess.run(['xcrun', '--show-sdk-path'], capture_output=True, text=True).stdout.strip()
    os.environ['SDKROOT'] = _sdk or '/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk'
BINARY = os.path.join(ROOT, 'rust', 'target', 'release', 'iheartla')
BACKENDS = [b for b in os.environ.get('IHEARTLA_RUST_BACKENDS', 'numpy').split(',') if b]   # empty: the Python compiler's own output

if 'matlab' in BACKENDS:
    # (the MATLAB checks run in GNU Octave: test/octave_engine.py, which the test suite
    # installs when IHEARTLA_OCTAVE is set; it can also be set without Rust's MATLAB)
    os.environ.setdefault('IHEARTLA_OCTAVE', '1')
if os.environ.get('RUST_TEST_VERBOSE'):
    os.environ.setdefault('IHEARTLA_OCTAVE_VERBOSE', '1')

import iheartla.la_parser.parser as P
from iheartla.la_tools.la_helper import ParserTypeEnum

_orig = P.compile_la_content
TYPES = {'numpy': ParserTypeEnum.NUMPY, 'eigen': ParserTypeEnum.EIGEN, 'matlab': ParserTypeEnum.MATLAB}


class RustCompileError(Exception):
    pass


def compile_with_rust(la_content, parser_type=None, *args, **kwargs):
    py_type = parser_type
    if parser_type is not None and 'matlab' in BACKENDS and parser_type & ParserTypeEnum.MATLAB:
        # (Rust supplies the MATLAB output; don't run the Python compiler's)
        py_type = parser_type & ~ParserTypeEnum.MATLAB
    ret = _orig(la_content, py_type, *args, **kwargs)
    for b in BACKENDS:
        t = TYPES[b]
        if parser_type is not None and parser_type & t:
            # (the test suite names MATLAB functions after `iheartla`)
            name = ['--name', 'iheartla'] if b == 'matlab' else []
            r = subprocess.run([BINARY, 'compile', '--backend', b] + name, input=la_content.encode(), capture_output=True)
            if r.returncode != 0:
                raise RustCompileError(r.stderr.decode())
            ret[t] = r.stdout.decode()
    return ret


P.compile_la_content = compile_with_rust

if __name__ == '__main__' and os.environ.get('RUST_TEST_VERBOSE'):
    unittest.main(module=None, argv=[sys.argv[0], '-v'] + sys.argv[1:])
elif __name__ == '__main__':
    mods = sys.argv[1:]
    if not mods:
        # one process per module: a cling crash (C++ backend) must not end the run
        lines = []
        for p in sorted(glob.glob('test/test_*.py')):
            r = subprocess.run([sys.executable, __file__, 'test.' + os.path.basename(p)[:-3]], capture_output=True, text=True)
            out = [l for l in r.stdout.splitlines() if not l.startswith('TOTAL')]
            if r.returncode != 0 and not out:
                out = ['{:32s} crashed: {}'.format('test.' + os.path.basename(p)[:-3], (r.stderr.strip().splitlines() or [''])[0][:120])]
            print('\n'.join(out), flush=True)
            lines += out
        import re
        counts = [re.search(r'(\d+)/\s*(\d+)$', l) for l in lines if not l.startswith(' ')]
        ok = sum(int(m.group(1)) for m in counts if m)
        n = sum(int(m.group(2)) for m in counts if m)
        print('TOTAL {}/{} passed'.format(ok, n))
        sys.exit(0)
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
