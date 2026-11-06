import sys
sys.path.append('./')
import unittest
# (importing iheartla first puts the regex module in place of re, which TatSu then uses)
from iheartla.la_grammar import update_parsers
import tatsu


class TestParsers(unittest.TestCase):
    # The parsers in la_local_parsers/ are TatSu's output for the EBNF in la_grammar/, unedited:
    # the rules that depend on a program's declarations are overridden in
    # la_tools/configured_parser.py. Regenerate them after changing the EBNF with
    # python -m iheartla.la_grammar.update_parsers.
    @unittest.skipUnless(tatsu.__version__ == update_parsers.TATSU_VERSION,
                         'the parsers are generated with TatSu ' + update_parsers.TATSU_VERSION)
    def test_parsers_are_tatsu_output(self):
        self.assertEqual(update_parsers.main(['--check']), 0)

    def test_overrides_exist_in_grammar(self):
        # each overridden rule is a rule of the generated parser, so the override replaces it
        from iheartla.la_local_parsers.default_parser import grammardefaultParser
        from iheartla.la_tools.configured_parser import CONFIGURED, ConfiguredParser
        for rule in CONFIGURED:
            name = '_{}_'.format(rule)
            self.assertTrue(hasattr(grammardefaultParser, name), rule)
            self.assertIsNot(getattr(ConfiguredParser, name), getattr(grammardefaultParser, name), rule)
