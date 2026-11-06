"""Regenerate the parsers in la_local_parsers/ from the EBNF in la_grammar/, with TatSu.

    python -m iheartla.la_grammar.update_parsers           # write both parsers
    python -m iheartla.la_grammar.update_parsers --check   # exit 1 if they aren't TatSu's output

init_parser.py is the simplified grammar (SIMPLIFIED), which the first parse uses to
collect declarations; default_parser.py is the full grammar (LA). Each is TatSu's parser
source followed by its object model, as TatSu generates them; nothing in them is edited
by hand. The rules that depend on what a program declares are overridden in
la_tools/configured_parser.py, which the compiler uses.

The files are generated with TatSu 5.8.3. Other versions generate different code for the
same grammar, so the script refuses to run with another version:

    uv run --with tatsu==5.8.3 python -m iheartla.la_grammar.update_parsers

The Rust compiler's parser is translated from these files: on the rust branch, run
`python rust/tools/gen_parser.py` afterwards.
"""
import sys
from pathlib import Path

# (the grammar needs \\p{…} classes, so TatSu must use regex for re; importing the iheartla
# package, which this module is part of, swaps it in before TatSu is imported)
import iheartla  # noqa: F401
import tatsu  # noqa: E402

TATSU_VERSION = '5.8.3'
LOCAL = Path(__file__).resolve().parent.parent / 'la_local_parsers'


def grammars():
    from iheartla.la_grammar.LA_ebnf import LA
    from iheartla.la_grammar.simplified_grammar_ebnf import SIMPLIFIED
    return {'init': SIMPLIFIED, 'default': LA}


def generate(key):
    """The parser file for one grammar: TatSu's parser source, then its object model."""
    grammar, name = grammars()[key], 'grammar' + key
    code = tatsu.to_python_sourcecode(grammar, name=name, filename='la_grammar/here')
    model = tatsu.to_python_model(grammar, name=name, filename='la_grammar/here')
    # (the parser source already starts with this import)
    return code + model.replace('from __future__ import annotations', '')


def path(key):
    return LOCAL / '{}_parser.py'.format(key)


def main(argv):
    if tatsu.__version__ != TATSU_VERSION:
        sys.exit('TatSu {0} generates these parsers; this is {1}, which generates different code. Run with {0}:\n'
                 '  uv run --with tatsu=={0} python -m iheartla.la_grammar.update_parsers'.format(
                     TATSU_VERSION, tatsu.__version__))
    status = 0
    for key in ('init', 'default'):
        code = generate(key)
        if '--check' in argv:
            if path(key).read_text(encoding='utf-8') != code:
                print('{} is not TatSu\'s output for the grammar; regenerate it'.format(path(key).name))
                status = 1
        else:
            path(key).write_text(code, encoding='utf-8')
            print('wrote', path(key))
    if '--check' in argv and status == 0:
        print('both parsers are TatSu\'s output for the grammar')
    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
