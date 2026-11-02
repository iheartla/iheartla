"""List corpus programs that the Rust compiler rejects (but Python compiles).

usage: python rust/tools/rust_errors.py [id-prefix]
"""
import json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BIN = os.path.join(ROOT, 'rust', 'target', 'release', 'iheartla')
prefix = sys.argv[1] if len(sys.argv) > 1 else 't_'
n = bad = 0
for line in open(os.path.join(ROOT, 'rust', 'corpus', 'cases.jsonl')):
    c = json.loads(line)
    if not c['id'].startswith(prefix):
        continue
    g = json.load(open(os.path.join(ROOT, 'rust', 'corpus', 'golden', c['id'] + '.json')))
    if 'error' in g['outputs'] or isinstance(g['outputs'].get('numpy'), dict):
        continue
    n += 1
    r = subprocess.run([BIN, 'compile'], input=c['src'].encode(), capture_output=True,
                       cwd=os.path.join(ROOT, c['path']) if c.get('path') else None)
    if r.returncode:
        bad += 1
        msg = r.stderr.decode().strip().splitlines()
        print('{}: {}'.format(c['id'], ' | '.join(msg[:3])[:220]))
print('{}/{} compile'.format(n - bad, n))
