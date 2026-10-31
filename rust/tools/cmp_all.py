"""Compare the Rust compiler's output for one backend with the Python
compiler's golden output, over the whole corpus.

usage: python rust/tools/cmp_all.py BACKEND [-v N] [-w]
  -v N  show the first differing line of up to N failing cases
  -w    compare with all whitespace removed (layout-insensitive)

Prints: identical / equal up to whitespace / different / Rust error counts.
"""
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BINARY = os.path.join(HERE, '..', 'target', 'release', 'iheartla')
backend = sys.argv[1]
show = int(sys.argv[sys.argv.index('-v') + 1]) if '-v' in sys.argv else 0
squash = (lambda s: re.sub(r'\s+', '', s)) if '-w' in sys.argv else (lambda s: re.sub(r'[ \t]+', ' ', s).strip())

counts = {'identical': 0, 'whitespace': 0, 'different': 0, 'error': 0}
shown = 0
for p in sorted(glob.glob(os.path.join(HERE, '..', 'corpus', 'golden', '*.json'))):
    d = json.load(open(p))
    want = d['outputs'].get(backend)
    if not isinstance(want, str):
        continue
    r = subprocess.run([BINARY, 'compile', '--backend', backend], input=d['src'].encode(), capture_output=True)
    got = r.stdout.decode()
    if r.returncode:
        counts['error'] += 1
        continue
    if got == want:
        counts['identical'] += 1
    elif squash(got) == squash(want):
        counts['whitespace'] += 1
    else:
        counts['different'] += 1
        if shown < show:
            shown += 1
            gl, wl = got.splitlines(), want.splitlines()
            for i in range(max(len(gl), len(wl))):
                g = gl[i] if i < len(gl) else '<end>'
                w = wl[i] if i < len(wl) else '<end>'
                if squash(g) != squash(w):
                    print('--- {}: {}'.format(d['id'], d['src'].strip().splitlines()[0][:70]))
                    print('  py:   ' + w[:220])
                    print('  rust: ' + g[:220])
                    break
print(counts)
