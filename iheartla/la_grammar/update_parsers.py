"""Regenerate rules of the parsers in la_local_parsers/ from the EBNF, with TatSu.

The compiler parses with la_local_parsers/init_parser.py (the simplified grammar,
SIMPLIFIED) and default_parser.py (the full grammar, LA). Both are TatSu output, but
some rules of default_parser.py were then rewritten by hand to read the parser's
configuration (declared multi-letter names, function names, imported builtins and
their renames, the constant e; see ParserManager.modify_default_parser). So the files
can't be regenerated whole: that would drop those rules (and `--regenerate-grammar`
refuses to). After changing the EBNF, regenerate just the rules you changed:

    python -m iheartla.la_grammar.update_parsers local_func where_conditions
    python -m iheartla.la_grammar.update_parsers --check            # every rule
    python -m iheartla.la_grammar.update_parsers --check local_func # these rules

A rule is regenerated in each parser whose grammar has it: in init_parser.py and
default_parser.py, and in their copies parser_<md5("init")>_*.py and
parser_<md5("default")>_*.py, which the DEBUG_PARSER mode loads. The hand-written rules
(HAND_WRITTEN) are refused, and their EBNF must be changed together with their code.

--check compares each rule's code with TatSu's, ignoring the text of error messages and
the numbering of nested blocks, and lists the rules that differ. HAND_WRITTEN rules are
expected to differ; any other rule that differs was edited by hand, and the next
regeneration of it would undo that edit. The exit status is 1 if a rule that isn't
HAND_WRITTEN differs.

The files were generated with TatSu 5.8.3. Other versions generate different code for
the same grammar, so the script refuses to run with another version.

The Rust compiler's parser is translated from these files: run
`python rust/tools/gen_parser.py` on the rust branch afterwards.
"""
import hashlib
import sys
from pathlib import Path

import regex

# (the grammar needs \\p{…} classes, so TatSu must use regex for re; importing the iheartla
# package, which this module is part of, swaps it in before TatSu is imported)
import iheartla  # noqa: F401
import tatsu  # noqa: E402

TATSU_VERSION = '5.8.3'
LOCAL = Path(__file__).resolve().parent.parent / 'la_local_parsers'

# Rules of default_parser.py that read the parser configuration (and the
# ParserManager sets it); their code is not TatSu's.
HAND_WRITTEN = {
    'identifier_alone', 'func_id', 'builtin_operators', 'constant', 'KEYWORDS',
    # renaming an imported builtin (sin as s) renames its keyword
    'TRACE', 'TR', 'VEC', 'DIAG', 'INV', 'DET', 'RANK', 'NULL', 'ORTH', 'SIN', 'ASIN',
    'ARCSIN', 'COS', 'ACOS', 'ARCCOS', 'TAN', 'ATAN', 'ARCTAN', 'SINH', 'ASINH', 'ARSINH',
    'COSH', 'ACOSH', 'ARCOSH', 'TANH', 'ATANH', 'ARTANH', 'COT', 'SEC', 'CSC', 'ATAN2', 'SVD',
}

RULE = regex.compile(r"(?m)^    @tatsumasu\([^)]*\)\n    def _(\w+)_\(self\):")
CLASS_END = regex.compile(r"\n(?=\S)")


def grammars():
    from iheartla.la_grammar.LA_ebnf import LA
    from iheartla.la_grammar.simplified_grammar_ebnf import SIMPLIFIED
    return {'init': SIMPLIFIED, 'default': LA}


def files(key):
    """The parser files of one grammar: <key>_parser.py and its timestamped copy."""
    digest = hashlib.md5(key.encode()).hexdigest()
    return [LOCAL / '{}_parser.py'.format(key)] + sorted(LOCAL.glob('parser_{}_*.py'.format(digest)))


def methods(src):
    """{rule: (start, end)} of each rule method in generated parser source."""
    found = list(RULE.finditer(src))
    spans = {}
    for k, m in enumerate(found):
        if k + 1 < len(found):
            end = found[k + 1].start()
        else:
            end = CLASS_END.search(src, m.end()).start() + 1
        spans[m.group(1)] = (m.start(), end)
    return spans


def method_text(src, span):
    return src[span[0]:span[1]].rstrip('\n') + '\n'


def normalized(code):
    # the expected-tokens text of error messages, and nested block numbers, don't change parsing
    code = regex.sub(r"self\._error\((?:[^()'\"]|'[^']*'|\"[^\"]*\"|\((?:[^()])*\))*\)", "self._error()", code)
    code = regex.sub(r"\bblock\d+\b", "block", code)
    return "\n".join(line for line in code.splitlines() if line.strip())


def generate(key):
    code = tatsu.to_python_sourcecode(grammars()[key], name='grammar' + key)
    return code, methods(code)


def check(rules):
    status = 0
    for key in ('init', 'default'):
        gen, gspans = generate(key)
        for f in files(key):
            src = f.read_text(encoding='utf-8')
            spans = methods(src)
            names = rules or sorted(spans)
            for r in names:
                if r not in spans or r not in gspans:
                    continue
                if normalized(method_text(src, spans[r])) != normalized(method_text(gen, gspans[r])):
                    hand = key == 'default' and r in HAND_WRITTEN
                    if not hand:
                        status = 1
                    print('{}: {} {}'.format(f.name, r, 'differs (hand-written)' if hand else 'DIFFERS from TatSu'))
            missing = [r for r in gspans if r not in spans] + [r for r in spans if r not in gspans]
            for r in missing:
                status = 1
                print('{}: {} is in only one of the file and the grammar'.format(f.name, r))
    if status == 0:
        print('every rule matches TatSu, apart from the hand-written ones')
    return status


def update(rules):
    generated = {key: generate(key) for key in ('init', 'default')}
    # (everything is checked before any file is written)
    unknown = [r for r in rules if not any(r in gspans for _, gspans in generated.values())]
    if unknown:
        sys.exit('no such rules in the grammar: {}'.format(', '.join(unknown)))
    refused = [r for r in rules if r in HAND_WRITTEN]
    if refused:
        sys.exit('refusing to regenerate hand-written rules: {}'.format(', '.join(refused)))
    edits = []
    for key, (gen, gspans) in generated.items():
        todo = [r for r in rules if r in gspans]
        for f in files(key):
            src = f.read_text(encoding='utf-8')
            for r in todo:
                spans = methods(src)
                if r not in spans:
                    sys.exit('{}: no rule {} (a new rule needs adding by hand once)'.format(f.name, r))
                a, b = spans[r]
                old = src[a:b]
                tail = old[len(old.rstrip('\n')):]   # (the blank lines before the next rule or class)
                src = src[:a] + method_text(gen, gspans[r]).rstrip('\n') + tail + src[b:]
            if todo:
                edits.append((f, src, todo))
    for f, src, todo in edits:
        f.write_text(src, encoding='utf-8')
        print('{}: regenerated {}'.format(f.name, ', '.join(todo)))


def main(argv):
    if tatsu.__version__ != TATSU_VERSION:
        sys.exit('TatSu {0} generated these parsers; this is {1}, which generates different code. Run with {0}:\n'
                 '  uv run --with tatsu=={0} python -m iheartla.la_grammar.update_parsers ...'.format(
                     TATSU_VERSION, tatsu.__version__))
    rules = [a for a in argv if not a.startswith('-')]
    if '--check' in argv:
        return check(rules)
    if not rules:
        sys.exit(__doc__)
    update(rules)
    return check(rules)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
