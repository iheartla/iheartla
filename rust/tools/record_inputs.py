"""Run Python test modules while recording every I❤LA program passed to
compile_la_content. Appends {"module", "src"} lines to the given JSONL file.

usage: python rust/tools/record_inputs.py out.jsonl test.test_python_expr [...]
"""
import json
import sys
import unittest

sys.path.insert(0, '.')
import iheartla.la_parser.parser as P

out_path = sys.argv[1]
_orig = P.compile_la_content
current = None


def recording(la_content, *args, **kwargs):
    with open(out_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'module': current, 'src': la_content}, ensure_ascii=False) + '\n')
    return _orig(la_content, *args, **kwargs)


P.compile_la_content = recording
for current in sys.argv[2:]:
    suite = unittest.defaultTestLoader.loadTestsFromName(current)
    unittest.TextTestRunner(verbosity=0).run(suite)
