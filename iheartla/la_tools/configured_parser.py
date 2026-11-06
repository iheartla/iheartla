"""The full-grammar parser, configured for one program.

iheartla/la_local_parsers/default_parser.py is TatSu's output for the EBNF in
la_grammar/ (python -m iheartla.la_grammar.update_parsers regenerates it). What a
program declares changes what parses, so the parser is configured before each parse
(ParserManager.modify_default_parser):

- new_id_list: declared multi-letter names (`AB` is one name, not `A` times `B`);
- new_func_list: the names of local functions and function parameters;
- builtin_list: the builtin functions the program imports (`sin, cos from trigonometry`);
- conversion_dict: their renames (`sin as s from trigonometry`: `s` is `sin`);
- const_e: whether the constant `e` is imported.

ConfiguredParser overrides the rules that read the configuration. Each override runs the
generated rule (the EBNF's static form) when its part of the configuration is empty, so
an unconfigured parse is exactly TatSu's. TatSu calls rules by method name
(self._identifier_alone_()), so the overrides apply wherever the grammar uses them.

The Rust compiler's parser (rust/tools/gen_parser.py on the rust branch) translates the
generated rules and has these in rust/src/grammar/special.rs; it reads CONFIGURED and
RENAMABLE_KEYWORDS from here.
"""
from tatsu.parsing import tatsumasu

from ..la_local_parsers.default_parser import grammardefaultParser, IdentifierAlone

# The keyword rules of builtin functions that an import may rename, and their names.
RENAMABLE_KEYWORDS = {name: name.lower() for name in [
    'TRACE', 'TR', 'VEC', 'DIAG', 'INV', 'DET', 'RANK', 'NULL', 'ORTH',
    'SIN', 'ASIN', 'ARCSIN', 'COS', 'ACOS', 'ARCCOS', 'TAN', 'ATAN', 'ARCTAN',
    'SINH', 'ASINH', 'ARSINH', 'COSH', 'ACOSH', 'ARCOSH', 'TANH', 'ATANH', 'ARTANH',
    'COT', 'SEC', 'CSC', 'ATAN2', 'SVD']}

# The rules ConfiguredParser overrides.
CONFIGURED = {'identifier_alone', 'func_id', 'builtin_operators', 'constant', 'KEYWORDS'} | set(RENAMABLE_KEYWORDS)

# A declared multi-letter name is an IdentifierAlone with `const` set (and no `value`).
if not hasattr(IdentifierAlone, 'const'):
    IdentifierAlone.const = None


def generated(rule):
    """The generated rule's body, to run inside the override's own rule call."""
    return getattr(grammardefaultParser, '_{}_'.format(rule)).__wrapped__


class ConfiguredParser(grammardefaultParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_id_list = []
        self.new_func_list = []
        self.builtin_list = []
        self.conversion_dict = {}
        self.const_e = False

    def _patterns(self, patterns):
        with self._choice():
            for p in patterns:
                with self._option():
                    self._pattern(p)
            self._error('no available options')

    @tatsumasu('IdentifierAlone')
    def _identifier_alone_(self):  # noqa
        if not self.new_id_list:
            return generated('identifier_alone')(self)
        # a declared name; or a name, as in the EBNF, that is neither a keyword nor a
        # declared name; or a name after a prefix keyword (sumd) or a declared name
        with self._choice():
            with self._option():
                with self._group():
                    self._patterns(self.new_id_list)
                self.name_last_node('const')
            with self._option():
                with self._ifnot():
                    with self._group():
                        with self._choice():
                            with self._option():
                                self._KEYWORDS_()
                            for new_id in self.new_id_list:
                                with self._option():
                                    self._pattern(new_id)
                            self._error('no available options')
                with self._group():
                    with self._choice():
                        with self._option():
                            with self._group():
                                self._pattern('[A-Za-z\\p{Ll}\\p{Lu}\\p{Lo}]\\p{M}*')
                            self.name_last_node('value')
                        with self._option():
                            self._token('`')
                            self._pattern('[^`]*')
                            self.name_last_node('id')
                            self._token('`')
                            self._define(['id'], [])
                        self._error("expecting one of: '`' [A-Za-z\\p{Ll}\\p{Lu}\\p{Lo}]\\p{M}*")
                self._define(['id', 'value'], [])
            with self._option():
                with self._group():
                    with self._choice():
                        with self._option():
                            self._PREFIX_KEYWORD_()
                        for new_id in self.new_id_list:
                            with self._option():
                                self._pattern(new_id)
                        self._error('no available options')
                    with self._group():
                        self._pattern('[A-Za-z\\p{Ll}\\p{Lu}\\p{Lo}]\\p{M}*')
                self.name_last_node('value')
            self._error('expecting an identifier')
        self._define(['const', 'id', 'value'], [])

    @tatsumasu()
    def _func_id_(self):  # noqa
        if not self.new_func_list:
            return generated('func_id')(self)
        self._patterns(self.new_func_list)

    @tatsumasu()
    def _builtin_operators_(self):  # noqa
        if not self.builtin_list:
            return generated('builtin_operators')(self)
        # an imported builtin (each name is the rule of its function: sin_func), or a predefined one
        with self._choice():
            for new_builtin in self.builtin_list:
                with self._option():
                    getattr(self, '_{}_'.format(new_builtin))()
            with self._option():
                self._predefined_built_operators_()
            self._error('no available options')

    @tatsumasu()
    def _constant_(self):  # noqa
        if not self.const_e:
            return generated('constant')(self)
        with self._choice():
            with self._option():
                self._pi_()
            with self._option():
                self._infinity_()
            with self._option():
                self._e_()
            self._error('no available options')

    @tatsumasu()
    def _KEYWORDS_(self):  # noqa
        if not self.const_e:
            return generated('KEYWORDS')(self)
        with self._choice():
            with self._option():
                self._BUILTIN_KEYWORDS_()
            with self._option():
                self._e_()
            self._error('no available options')


def _renamable(rule, name):
    def impl(self):
        if name in self.conversion_dict:
            self._pattern(self.conversion_dict[name])
        else:
            generated(rule)(self)
    impl.__name__ = impl.__qualname__ = '_{}_'.format(rule)
    return tatsumasu()(impl)


for _rule, _name in RENAMABLE_KEYWORDS.items():
    setattr(ConfiguredParser, '_{}_'.format(_rule), _renamable(_rule, _name))
