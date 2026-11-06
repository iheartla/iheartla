import sys
sys.path.append('./')
import unittest
# (importing iheartla first puts the regex module in place of re, which TatSu then uses)
from iheartla.la_grammar import update_parsers
import tatsu


class TestParsers(unittest.TestCase):
    # The parsers in la_local_parsers/ are TatSu's output for the EBNF in la_grammar/, apart
    # from the rules rewritten by hand to read the parser configuration (update_parsers.HAND_WRITTEN).
    # A rule that differs otherwise was edited without changing the EBNF, or the EBNF without
    # regenerating it (python -m iheartla.la_grammar.update_parsers RULE).
    @unittest.skipUnless(tatsu.__version__ == update_parsers.TATSU_VERSION,
                         'the parsers were generated with TatSu ' + update_parsers.TATSU_VERSION)
    def test_parsers_match_grammar(self):
        self.assertEqual(update_parsers.check([]), 0)

    def test_regenerate_grammar_refuses(self):
        import subprocess
        r = subprocess.run([sys.executable, '-m', 'iheartla', '--regenerate-grammar'], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('update_parsers', r.stderr)
