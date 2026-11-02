"""Extract each H❤️rtDown paper's I❤️LA programs, one per context, the way
H❤️rtDown's iheartla_code preprocessor groups them (handle_context_pre, then
handle_iheartla_code): inline ❤…❤ code first, then fenced blocks, joined by
newlines. Writes <out>/<paper dir>/<context>.ihla and an index.json.

usage: python rust/tools/extract_heartdown.py <papers-dir> <out-dir>
       (<papers-dir>/<paper>/<paper>.txt or .md, as in the gallery)
"""
import sys, os, json, glob
import regex as re
from textwrap import dedent
src_dir, out_dir = sys.argv[1], sys.argv[2]
FENCED = re.compile(dedent(r'''
    (?P<fence>^(?:~{3,}|`{3,}))[ ]*iheartla\s*(\((?P<module>[^\}\n]*)\))\n
    (?P<code>.*?)(?<=\n)(?P=fence)[ ]*$'''), re.MULTILINE | re.DOTALL | re.VERBOSE)
INLINE = re.compile(r'''❤(?P<module>[a-zA-Z0-9\.\t\r\f\v ]*)(:)(?P<code>.*?)❤''', re.MULTILINE)
CONTEXT = re.compile(r'''(?<=(\n)*)([\t\r\f\v ]*)❤(\s*):(?P<context>[^\n❤]*)(?=\n)''', re.MULTILINE)
RAW_BLOCK = re.compile(r'''(?P<fence>^(?:~{3,}|`{3,}))[ ]*iheartla\s*\n''', re.MULTILINE | re.DOTALL)
RAW_NUM_BLOCK = re.compile(r'''(?P<fence>^(?:~{3,}|`{3,}))[ ]*iheartla_unnumbered\s*\n''', re.MULTILINE | re.DOTALL)
RAW_INLINE = re.compile(r'''❤(?P<code>[^❤]*)❤''', re.MULTILINE)
BLANK = re.compile(r'''[\n\s]*''')

def tag(text, ctx):
    text = RAW_BLOCK.sub(lambda m: "{}iheartla({})\n".format(m.group('fence'), ctx), text)
    text = RAW_NUM_BLOCK.sub(lambda m: "{}iheartla({}, unnumbered)\n".format(m.group('fence'), ctx), text)
    return RAW_INLINE.sub(lambda m: m.group() if INLINE.fullmatch(m.group()) else "❤ {}:{}❤".format(ctx, m.group('code')), text)

index = []
for paper in sorted(glob.glob(os.path.join(src_dir, '*', '*.txt')) + glob.glob(os.path.join(src_dir, '*', '*.md'))):
    text = open(paper).read()
    # front matter (meta extension) is removed before this preprocessor runs
    if text.startswith('---\n'):
        text = text[text.index('\n---\n', 4) + 5:]
    parts, ctxs, last = [], [''], 0
    for m in CONTEXT.finditer(text):
        parts.append(text[last:m.start()]); ctxs.append(m.group('context').strip()); last = m.end()
    parts.append(text[last:])
    text = ''.join(tag(p, c) for p, c in zip(parts, ctxs))
    progs = {}
    for m in INLINE.finditer(text):
        name, code = m.group('module').strip(), m.group('code')
        if name and code:
            progs.setdefault(name, []).append(code)
    for m in FENCED.finditer(text):
        name, code = m.group('module').split(',')[0].strip(), m.group('code')
        if '.' in name and BLANK.fullmatch(code):
            code = open(os.path.join(os.path.dirname(paper), name)).read()
        if name and code:
            progs.setdefault(name, []).append(code)
    rel = os.path.basename(os.path.dirname(paper))
    os.makedirs(os.path.join(out_dir, rel), exist_ok=True)
    for name, codes in progs.items():
        open(os.path.join(out_dir, rel, name + '.ihla'), 'w').write('\n'.join(codes))
    index.append({'paper': os.path.relpath(paper, src_dir), 'contexts': list(progs)})
    print(os.path.relpath(paper, src_dir), list(progs))
json.dump(index, open(os.path.join(out_dir, 'index.json'), 'w'), ensure_ascii=False, indent=1)
