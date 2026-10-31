"""Collect I❤LA programs into rust/corpus/cases.jsonl.

Sources: programs recorded from the Python test suite (tests.jsonl), the
built-in I❤MESH modules, and *.ila files under rust/corpus/ (examples, mesh).
"""
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CORPUS = os.path.join(ROOT, 'rust', 'corpus')

cases = []
seen = set()


def add(cid, src, path=None):
    if src in seen:
        return
    seen.add(src)
    case = {'id': cid, 'src': src}
    if path:
        case['path'] = path
    cases.append(case)


counts = {}
with open(os.path.join(CORPUS, 'tests.jsonl'), encoding='utf-8') as f:
    for line in f:
        rec = json.loads(line)
        mod = rec['module'].replace('test.test_python_', '')
        counts[mod] = counts.get(mod, 0) + 1
        add('t_{}_{:02d}'.format(mod, counts[mod]), rec['src'])

for p in sorted(glob.glob(os.path.join(ROOT, 'iheartla', 'mesh', '*.hlang'))):
    with open(p, encoding='utf-8') as f:
        add('m_' + os.path.splitext(os.path.basename(p))[0], f.read(), 'iheartla/mesh')

for p in sorted(glob.glob(os.path.join(CORPUS, '**', '*.ila'), recursive=True) + glob.glob(os.path.join(CORPUS, '**', '*.ihla'), recursive=True)):
    rel = os.path.relpath(p, CORPUS)
    cid = 'x_' + os.path.splitext(rel)[0].replace(os.sep, '_').replace('-', '_')
    with open(p, encoding='utf-8') as f:
        add(cid, f.read())

with open(os.path.join(CORPUS, 'cases.jsonl'), 'w', encoding='utf-8') as f:
    for c in cases:
        f.write(json.dumps(c, ensure_ascii=False) + '\n')
print(len(cases), 'cases')
