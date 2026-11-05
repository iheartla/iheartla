import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)
if TEST_MATLAB:
    import matlab


class TestConstantE(BasePythonTest):
    # The constant e, imported from trigonometry (iheartla#146). Once imported, the parser takes e
    # as a keyword, which an import name could not be, so the import line itself failed to parse.
    def check(self, la_str, x, expected):
        func_info = self.gen_func_info(la_str)
        self.assertAlmostEqual(func_info.numpy_func(x).s, expected, places=12)
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertAlmostEqual(float(np.array(mat_func(matlab.double([x]))['s'])), expected, places=12)
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return std::abs({}({}).s - {}) < 1e-12;".format(func_info.eig_func_name, repr(float(x)), repr(float(expected))),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_import_e(self):
        self.check("""e from trigonometry
        s = e^x
        where
        x ∈ ℝ""", 2.0, np.e ** 2)

    def test_import_e_with_function(self):
        self.check("""sin, e from trigonometry
        s = e^x + sin(x)
        where
        x ∈ ℝ""", 0.5, np.e ** 0.5 + np.sin(0.5))

    def test_e_needs_import(self):
        with self.assertRaises(AssertionError) as cm:
            compile_la_content("""s = e^x
            where
            x ∈ ℝ""", ParserTypeEnum.NUMPY)
        self.assertIn('e from trigonometry', str(cm.exception))

    def test_name_starting_with_e_still_imports(self):
        # a function whose name starts with e is still a name, not the constant
        func_info = self.gen_func_info("""e from trigonometry
        s = e^x + exp(x)
        where
        x ∈ ℝ""")
        self.assertAlmostEqual(func_info.numpy_func(1.0).s, 2 * np.e, places=12)
