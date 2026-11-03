"""Run the generated main() (`iheartla compile --main`) of every corpus program
in Python, C++ and Octave, and report which fail.

usage: python rust/tools/main_check.py [numpy] [eigen] [matlab]   (default: all three)

NumPy runs with the I❤️MESH runtime (iheartla/mesh/Python) on the path; C++ is compiled with
clang++ against Eigen 3.4, LBFGSpp and the I❤️MESH C++ runtime; MATLAB runs in
octave-cli. A program the Rust compiler rejects is skipped.
"""
import glob
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BINARY = os.path.join(ROOT, 'rust', 'target', 'release', 'iheartla')
EIGEN = os.environ.get('EIGEN_PATH', os.path.join(ROOT, 'test', 'third_party', 'eigen'))
LBFGSPP = os.environ.get('LBFGSPP_PATH', os.path.join(ROOT, 'test', 'third_party', 'LBFGSpp', 'include'))
CPP = os.path.join(ROOT, 'iheartla', 'mesh', 'Cpp')
TMP = tempfile.mkdtemp()
backends = sys.argv[1:] or ['numpy', 'eigen', 'matlab']


def run(backend, src, k, cwd):
    r = subprocess.run([BINARY, 'compile', '--backend', backend, '--main'] + (['--name', 'prog{}'.format(k)] if backend == 'matlab' else []),
                       input=src.encode(), capture_output=True, cwd=cwd)
    if r.returncode:
        return None  # rejected by the compiler: not this tool's business
    code = r.stdout.decode()
    if backend == 'numpy':
        path = os.path.join(TMP, 'prog{}.py'.format(k))
        open(path, 'w').write(code)
        env = dict(os.environ, PYTHONPATH=os.path.join(HERE, '..', '..', 'iheartla', 'mesh', 'Python'))
        r = subprocess.run([sys.executable, path], capture_output=True, text=True, env=env, timeout=120)
    elif backend == 'eigen':
        path = os.path.join(TMP, 'prog{}.cpp'.format(k))
        open(path, 'w').write(code)
        exe = path[:-4]
        srcs = [os.path.join(CPP, 'src', f) for f in ['MeshHelper.cpp', 'TriangleMesh.cpp', 'Connectivity.cpp', 'dec_util.cpp']] if 'iheartmesh' in code else []
        r = subprocess.run(['clang++', '-std=c++17', '-O0', '-w', '-I' + EIGEN, '-I' + LBFGSPP, '-I' + os.path.join(CPP, 'include'),
                            '-I' + os.path.join(ROOT, 'test', 'third_party', 'autodiff'), '-o', exe, path] + srcs, capture_output=True, text=True, timeout=300)
        if r.returncode:
            return 'C++ compile: ' + next((l for l in r.stderr.splitlines() if 'error' in l), r.stderr[-200:]).split('error: ')[-1][:140]
        r = subprocess.run([exe], capture_output=True, text=True, timeout=120)
    else:
        path = os.path.join(TMP, 'prog{}.m'.format(k))
        open(path, 'w').write(code)
        r = subprocess.run(['octave-cli', '--no-gui', '--eval', "warning('off', 'all'); prog{}();".format(k)], capture_output=True, text=True, timeout=120, cwd=TMP)
    if r.returncode:
        lines = [l for l in (r.stderr or r.stdout).strip().splitlines() if l.strip()]
        return 'run: ' + (lines[-1][:160] if lines else 'exit {}'.format(r.returncode))
    return ''


progs = []
for p in sorted(glob.glob(os.path.join(ROOT, 'rust', 'corpus', 'golden', '*.json'))):
    d = json.load(open(p))
    if not d['id'].startswith('m_'):
        progs.append((d['id'], d['src'], os.path.join(ROOT, d['path']) if d.get('path') else None))
for b in backends:
    ok = fail = skipped = 0
    failures = []
    for k, (name, src, cwd) in enumerate(progs):
        try:
            res = run(b, src, k, cwd)
        except subprocess.TimeoutExpired:
            res = 'timeout'
        if res is None:
            skipped += 1
        elif res == '':
            ok += 1
        else:
            fail += 1
            failures.append('  {}: {}'.format(name, res))
    print('{}: {} ran, {} failed, {} rejected by the compiler'.format(b, ok, fail, skipped), flush=True)
    print('\n'.join(failures), flush=True)
