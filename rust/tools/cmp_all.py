"""Compare the Rust compiler's output for one backend with the Python
compiler's golden output, over the whole corpus.

usage: python rust/tools/cmp_all.py BACKEND [-v N] [-w] [-p PREFIX]
  -v N  show the first differing line of up to N failing cases
  -p    only the cases whose id starts with PREFIX (x_heartdown, x_iheartmesh, t_, ...)
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
prefix = sys.argv[sys.argv.index('-p') + 1] if '-p' in sys.argv else ''
squash = (lambda s: re.sub(r'\s+', '', s)) if '-w' in sys.argv else (lambda s: re.sub(r'[ \t]+', ' ', s).strip())

if backend == 'macromathjax':
    # the Python compiler lists an equation's symbols in hash order: compare as sets
    _sq = squash
    def squash(t, _sq=_sq):
        return _sq(re.sub(r"onClickEq\(this, '([^']*)', \[([^\]]*)\]",
                          lambda m: "onClickEq(this, '{}', [{}]".format(m.group(1), ', '.join(sorted(x.strip() for x in m.group(2).split(',')))), t))

counts = {'identical': 0, 'whitespace': 0, 'different': 0, 'error': 0}
shown = 0
for p in sorted(glob.glob(os.path.join(HERE, '..', 'corpus', 'golden', '*.json'))):
    d = json.load(open(p))
    if not d['id'].startswith(prefix):
        continue
    want = d['outputs'].get(backend)
    if not isinstance(want, str):
        continue
    # (in the case's directory, where its imported modules are)
    r = subprocess.run([BINARY, 'compile', '--backend', backend], input=d['src'].encode(), capture_output=True,
                       cwd=os.path.join(HERE, '..', '..', d['path']) if d.get('path') else None)
    got = r.stdout.decode()
    if r.returncode:
        counts['error'] += 1
        if shown < show:
            shown += 1
            print('--- {}: Rust error: {}'.format(d['id'], r.stderr.decode().strip().splitlines()[0][:200]))
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
                    k = next((j for j in range(min(len(g), len(w))) if g[j] != w[j]), min(len(g), len(w)))
                    k = max(0, k - 60)
                    print('  py:   ' + w[k:k + 200])
                    print('  rust: ' + g[k:k + 200])
                    break
if backend == 'macromathjax':
    # (equal after sorting equation symbol lists, which Python orders by hash)
    counts['equal up to symbol order'] = counts.pop('whitespace')
print(counts)
