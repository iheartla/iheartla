import sys
sys.path.append('./')
from test.base_python_test import *
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)


class TestSet(BasePythonTest):
    def test_set_init(self):
        # no return symbol
        la_str = """a =  {1, 2, 3}"""
        func_info = self.gen_func_info(la_str)
        self.assertEqual(list(func_info.numpy_func().a), [1,2,3])
        # MATLAB testv
        if TEST_MATLAB:
            mat_func = getattr(mat_engine, func_info.mat_func_name, None)
            self.assertEqual(np.array(mat_func()['a']), [1, 2, 3])
        # eigen test
        cppyy.include(func_info.eig_file_name)
        func_list = ["bool {}(){{".format(func_info.eig_test_name),
                     "    std::set<int > a = {}().a;".format(func_info.eig_func_name),
                     "    if(a.find(1) != a.end() && a.find(2) != a.end() && a.find(3) != a.end()){",
                     "        return true;",
                     "    }",
                     "    return false;",
                     "}"]
        cppyy.cppdef('\n'.join(func_list))
        self.assertTrue(getattr(cppyy.gbl, func_info.eig_test_name)())