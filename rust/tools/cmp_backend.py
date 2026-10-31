"""Show the Python compiler's golden output next to the Rust compiler's.

usage: python rust/tools/cmp_backend.py BACKEND 'substring of the source'
       python rust/tools/cmp_backend.py BACKEND -f source.la
"""
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BINARY = os.path.join(HERE, '..', 'target', 'release', 'iheartla')

backend = sys.argv[1]
if sys.argv[2] == '-f':
    src = open(sys.argv[3]).read()
    golden = None
else:
    golden = None
    for p in sorted(glob.glob(os.path.join(HERE, '..', 'corpus', 'golden', '*.json'))):
        d = json.load(open(p))
        if sys.argv[2] in d['src']:
            src, golden = d['src'], d['outputs'].get(backend)
            break
    else:
        sys.exit('no golden case contains that text')
print(src)
if golden is not None:
    print('==== python ' + '=' * 60)
    print(golden if isinstance(golden, str) else json.dumps(golden))
print('==== rust ' + '=' * 62)
r = subprocess.run([BINARY, 'compile', '--backend', backend], input=src.encode(), capture_output=True)
print(r.stdout.decode() + r.stderr.decode())
