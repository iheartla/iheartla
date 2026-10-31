"""Print parts of golden files.

usage: python rust/tools/show_golden.py errors            # error summary of all cases
       python rust/tools/show_golden.py <id> [field]      # src | ast | numpy | eigen | ...
"""
import glob
import json
import os
import sys

GOLDEN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'corpus', 'golden')

if sys.argv[1] == 'errors':
    for p in sorted(glob.glob(os.path.join(GOLDEN, '*.json'))):
        d = json.load(open(p, encoding='utf-8'))
        if 'error' in d['outputs']:
            tb = d['outputs']['traceback'].strip().splitlines()
            where = next((l.strip() for l in reversed(tb) if l.strip().startswith('File')), '')
            print('{}: {}\n    {}'.format(d['id'], d['outputs']['error'][:240].replace('\n', ' | '), where[-120:]))
    sys.exit()

d = json.load(open(os.path.join(GOLDEN, sys.argv[1] + '.json'), encoding='utf-8'))
field = sys.argv[2] if len(sys.argv) > 2 else 'src'
if field == 'src':
    print(d['src'])
elif field == 'parses':
    for p in d['parses']:
        print(p['kind'], json.dumps(p['config'], ensure_ascii=False), 'error' in p and p['error'] or '')
elif field == 'ast':
    idx = int(sys.argv[3]) if len(sys.argv) > 3 else -1
    print(json.dumps(d['parses'][idx].get('ast'), ensure_ascii=False, indent=1))
else:
    print(d['outputs'].get(field))
