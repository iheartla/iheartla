import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)


class TestFunctionArguments(BasePythonTest):
    # A local function has at least one argument: a parameter in ( ) or [ ], or a subscript.
    # `y = b + c` followed by `where b ∈ ℝ, c ∈ ℝ` used to define a function y() with no
    # arguments, whose b and c had no values; it now defines y from the parameters b and c.
    def check_definition(self, la_str):
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(1.0, 2.0).y, 3.0)
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    return {}(1.0, 2.0).y == 3.0;".format(func_info.eig_func_name),
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())

    def test_where_on_next_line(self):
        self.check_definition("""y = b + c
        where b ∈ ℝ, c ∈ ℝ""")

    def test_where_on_same_line(self):
        self.check_definition("""y = b + c where b ∈ ℝ, c ∈ ℝ""")

    def test_where_block_with_commas(self):
        self.check_definition("""y = b + c
        where
        b ∈ ℝ, c ∈ ℝ""")

    def test_functions_still_take_arguments(self):
        for la_str in ["""f(x) = x + 1 where x ∈ ℝ
        y = f(2)""", """f_x = x + 1 where x ∈ ℝ
        y = f_2""", """fᵢ = i + 1 where i ∈ ℤ
        y = f₂"""]:
            self.assertEqual(self.gen_func_info(la_str).numpy_func().y, 3, la_str)

    def test_function_without_arguments_is_an_error(self):
        with self.assertRaises(Exception):
            compile_la_content("""f() = 1 where x ∈ ℝ""", ParserTypeEnum.NUMPY)
