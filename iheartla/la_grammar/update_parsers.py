"""Regenerate the parsers in la_local_parsers/ from the EBNF in la_grammar/, with TatSu.

    python -m iheartla.la_grammar.update_parsers           # write both parsers
    python -m iheartla.la_grammar.update_parsers --check   # exit 1 if they aren't TatSu's output

init_parser.py is the simplified grammar (SIMPLIFIED), which the first parse uses to
collect declarations; default_parser.py is the full grammar (LA). Each is TatSu's parser
source followed by its object model, as TatSu generates them; nothing in them is edited
by hand. The rules that depend on what a program declares are overridden in
la_tools/configured_parser.py, which the compiler uses.

The files are generated with TatSu 5.15.1, the version iheartla runs with (pyproject.toml).
Other versions generate different code for the same grammar, so the script refuses to run
with another version. TatSu's object model gets two fix-ups (complete_model).

The Rust compiler's parser is translated from these files: on the rust branch, run
`python rust/tools/gen_parser.py` afterwards.
"""
import sys
from pathlib import Path

# (the grammar needs \\p{…} classes, so TatSu must use regex for re; importing the iheartla
# package, which this module is part of, swaps it in before TatSu is imported)
import iheartla  # noqa: F401
import regex  # noqa: E402
import tatsu  # noqa: E402

TATSU_VERSION = '5.15.1'
LOCAL = Path(__file__).resolve().parent.parent / 'la_local_parsers'


def grammars():
    from iheartla.la_grammar.LA_ebnf import LA
    from iheartla.la_grammar.simplified_grammar_ebnf import SIMPLIFIED
    return {'init': SIMPLIFIED, 'default': LA}


def node_fields(grammar):
    """{node class: the fields of every rule that builds it}, as the grammar names them."""
    from tatsu.util import compress_seq
    fields = {}
    for rule in tatsu.compile(grammar, asmodel=True).rules:
        if rule.params:
            cls = rule.params[0].split('::')[0]
            fields.setdefault(cls, set()).update(d for d, _ in compress_seq(rule.defines()))
    return fields


NODE_CLASS = r"@dataclass\(eq=False\)\nclass (\w+)\(ModelBase\):\n"


def complete_model(model, fields):
    """Two fix-ups of TatSu's object model, so the generated file is complete and stable.

    A node class can be built by several rules with different fields (IdentifierSubscript:
    x_i has exp and p, xᵢ doesn't). A node gets the fields its rule matched and its class
    supplies None for the others, but TatSu (since 5.9) renders each class from one of its
    rules, so reading a field only another rule defines is an AttributeError. Each class
    gets every field its rules define, as TatSu 5.8.3 generated them.

    TatSu also emits the classes in an order that varies from run to run (set iteration),
    so they are sorted, and a regenerated file only changes where the grammar did. (All
    are direct ModelBase subclasses, so their order doesn't matter.)"""

    def complete(m):
        declared = set(regex.findall(r"(?m)^    (\w+): Any = None$", m.group(2)))
        names = sorted(fields.get(m.group(1), set()) | declared)
        body = ''.join('    {}: Any = None\n'.format(n) for n in names) or '    pass\n'
        return 'class {}(ModelBase):\n{}'.format(m.group(1), body)
    model = regex.sub(r"class (\w+)\(ModelBase\):\n((?:    .*\n)+)", complete, model)
    m = regex.search(NODE_CLASS, model)
    if m:
        # (the node classes run to the end of the model)
        blocks = [b.strip('\n') for b in regex.split(r"(?=@dataclass\(eq=False\)\nclass )", model[m.start():]) if b.strip()]
        assert all(regex.match(NODE_CLASS, b + '\n') for b in blocks), 'unexpected model layout'
        blocks.sort(key=lambda b: b.splitlines()[1])
        model = model[:m.start()] + '\n\n\n'.join(blocks) + '\n'
    return model


def generate(key):
    """The parser file for one grammar: TatSu's parser source, then its object model."""
    grammar, name = grammars()[key], 'grammar' + key
    code = tatsu.to_python_sourcecode(grammar, name=name, filename='la_grammar/here')
    model = tatsu.to_python_model(grammar, name=name, filename='la_grammar/here')
    model = complete_model(model, node_fields(grammar))
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
