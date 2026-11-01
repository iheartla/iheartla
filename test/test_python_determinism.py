import sys
sys.path.append('./')
import json
import os
import subprocess
import unittest

# Compile programs whose output used to depend on the iteration order of Python sets
# (summation bounds, dimension checks, MacroMathJax symbol lists, random-data code),
# which changes with PYTHONHASHSEED. Each seed needs a fresh interpreter.
PROGRAMS = [
    # summation bound: len(f) or len(p)
    """∑_i f_i²p_i - (∑_i f_i p_i)²
    where
    f_i: ℝ
    p_i: ℝ""",
    # dimension checks in NumPy, Eigen, and MATLAB
    """v_i = ∑_j w_i,j M_j u_i
    where
    w: ℝ^(4×4)
    M_j: ℝ^(4×4)
    u_i: ℝ^4""",
    # MacroMathJax symbol list
    """c = a b
    where
    a: scalar
    b: scalar""",
]

COMPILE = """
import json, sys, io, contextlib, warnings
warnings.simplefilter('ignore')
sys.path.insert(0, '.')
from iheartla.la_parser.parser import compile_la_content
out = []
for source in json.loads(sys.stdin.read()):
    for class_only in (True, False):
        with contextlib.redirect_stdout(io.StringIO()):
            result = compile_la_content(source, class_only=class_only)
        out.append({k.name: v for k, v in result.items()})
print(json.dumps(out))
"""


class TestDeterminism(unittest.TestCase):
    def compile_with_seed(self, seed):
        env = dict(os.environ, PYTHONHASHSEED=str(seed))
        proc = subprocess.run([sys.executable, '-c', COMPILE], input=json.dumps(PROGRAMS), env=env,
                              capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        return json.loads(proc.stdout.strip().splitlines()[-1])

    def test_output_independent_of_hash_seed(self):
        reference = self.compile_with_seed(0)
        for seed in range(1, 6):
            outputs = self.compile_with_seed(seed)
            for index, (expected, actual) in enumerate(zip(reference, outputs)):
                for target in expected:
                    self.assertEqual(expected[target], actual[target],
                                     "PYTHONHASHSEED={} changes {} output of program {} (class_only={})".format(
                                         seed, target, index // 2, index % 2 == 0))
