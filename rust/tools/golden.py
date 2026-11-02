"""Generate golden outputs from the Python (TatSu) I❤LA compiler.

For each case in rust/corpus/cases.jsonl ({"id", "src", "path"?}), writes
rust/corpus/golden/<id>.json with:
  parses:  every TatSu parse performed, as JSON ASTs, with the parser
           configuration (declared multi-letter ids, function ids, imported
           builtins, renames, whether `e` is a constant)
  outputs: generated code per backend, or "error" with the message

Each case runs in a fresh process, because the Python compiler keeps state
(code generators, parsers) between compiles.

usage: python rust/tools/golden.py [case-id ...]
"""
import json
import multiprocessing
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CORPUS = os.path.join(ROOT, 'rust', 'corpus')
# mathml is omitted: the Python MathML backend crashes on every assignment
BACKENDS = ['numpy', 'eigen', 'latex', 'mathjax', 'matlab', 'macromathjax']


def ast_json(node):
    from tatsu.objectmodel import Node
    if isinstance(node, Node):
        d = {'_': type(node).__name__}
        if node.parseinfo is not None:
            d['@'] = [node.parseinfo.pos, node.parseinfo.endpos]
        ast = node.ast if isinstance(node.ast, dict) else {}
        for k, v in ast.items():
            if k == 'parseinfo':
                continue
            d[k] = ast_json(getattr(node, k, v))
        return d
    if isinstance(node, (list, tuple)):
        return [ast_json(x) for x in node]
    if isinstance(node, dict):
        return {'{}': {k: ast_json(v) for k, v in node.items() if k != 'parseinfo'}}
    return node


def run_case(case):
    sys.path.insert(0, ROOT)
    import iheartla  # noqa: F401  (installs the regex module for TatSu)
    from iheartla.la_parser import parser as P
    from iheartla.la_parser.parser import ParserTypeEnum
    from iheartla.la_tools.parser_manager import ParserManager
    P.CACHE_MODULE = False  # the on-disk module cache is unreliable (see PERFORMANCE.md)

    parses = []
    mgr = ParserManager.getInstance()

    def wrap(parser, kind):
        orig = parser.parse

        def parse(text, *a, **kw):
            cfg = None
            if kind == 'default':
                cfg = {'ids': list(parser.new_id_list), 'funcs': list(parser.new_func_list),
                       'builtins': list(parser.builtin_list), 'rename': dict(parser.conversion_dict),
                       'const_e': parser.const_e}
            entry = {'kind': kind, 'config': cfg, 'text': text}
            try:
                model = orig(text, *a, **kw)
                entry['ast'] = ast_json(model)
            except Exception as e:
                entry['error'] = '{}: {}'.format(type(e).__name__, str(e).splitlines()[0] if str(e) else '')
                parses.append(entry)
                raise
            parses.append(entry)
            return model
        parser.parse = parse

    wrap(mgr.init_parser, 'init')
    wrap(mgr.default_parser, 'default')

    types = {'numpy': ParserTypeEnum.NUMPY, 'eigen': ParserTypeEnum.EIGEN, 'latex': ParserTypeEnum.LATEX,
             'mathjax': ParserTypeEnum.MATHJAX, 'matlab': ParserTypeEnum.MATLAB,
             'macromathjax': ParserTypeEnum.MACROMATHJAX, 'mathml': ParserTypeEnum.MATHML}
    # one compile per backend, so that a crash in one backend does not hide the others;
    # outputs[b] is the code, or {"error", "traceback"}
    outputs = {}
    path = case.get('path')
    if path:
        path = os.path.join(ROOT, path)
    for b in BACKENDS:
        try:
            ret = P.compile_la_content(case['src'], parser_type=types[b], path=path)
            outputs[b] = ret[types[b]]
        except BaseException as e:
            msg = e.args[0] if isinstance(e, AssertionError) and e.args else '{}: {}'.format(type(e).__name__, e)
            outputs[b] = {'error': str(msg), 'traceback': traceback.format_exc(limit=-3).replace(ROOT + os.sep, '')}
    if all(isinstance(v, dict) for v in outputs.values()) and \
            len({v['error'] for v in outputs.values()}) == 1:
        # the same error in every backend: a front-end (parse or type) error
        outputs = {'error': outputs[BACKENDS[0]]['error'], 'traceback': outputs[BACKENDS[0]]['traceback']}
    # dedupe identical parses (same parser kind, config, text)
    seen, unique = set(), []
    for p in parses:
        key = json.dumps([p['kind'], p['config'], p['text']], ensure_ascii=False, sort_keys=True)
        if key not in seen:
            seen.add(key)
            unique.append(p)
    result = {'id': case['id'], 'src': case['src'], 'parses': unique, 'outputs': outputs}
    if case.get('path'):
        result['path'] = case['path']
    with open(os.path.join(CORPUS, 'golden', case['id'] + '.json'), 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    return case['id'], ' '.join(b for b, v in outputs.items() if isinstance(v, dict) or b == 'error') or 'ok'


def main():
    os.makedirs(os.path.join(CORPUS, 'golden'), exist_ok=True)
    with open(os.path.join(CORPUS, 'cases.jsonl'), encoding='utf-8') as f:
        cases = [json.loads(line) for line in f if line.strip()]
    if len(sys.argv) > 1:
        cases = [c for c in cases if c['id'] in sys.argv[1:]]
    ctx = multiprocessing.get_context('spawn')
    with ctx.Pool(processes=max(1, os.cpu_count() - 2), maxtasksperchild=1) as pool:
        for cid, err in pool.imap_unordered(run_case, cases):
            print(cid, err, flush=True)


if __name__ == '__main__':
    main()
