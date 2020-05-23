import unittest
import sys
import importlib
from importlib import reload
sys.path.append('./')
from la_parser.parser import parse_la, ParserTypeEnum
import subprocess
from time import sleep
import numpy as np
import logging
from la_tools.la_logger import LaLogger, LoggerTypeEnum
eigen_path = "/usr/local/Cellar/eigen/3.3.7/include/eigen3"       # required


class TestFuncInfo(object):
    def __init__(self, numpy_func=None, eig_file_name=None, eig_test_name=None, eig_func_name=None):
        super().__init__()
        # Numpy
        self.numpy_func = numpy_func  # func content
        # Eigen
        self.eig_file_name = eig_file_name   # generated cpp file name
        self.eig_func_name = eig_func_name   # func name
        self.eig_test_name = eig_test_name   # test func name


class BasePythonTest(unittest.TestCase):
    cnt = 0

    def __init__(self, *args, **kwargs):
        super(BasePythonTest, self).__init__(*args, **kwargs)
        if BasePythonTest.cnt == 0:
            LaLogger.getInstance().set_level(logging.WARNING)

    def gen_func_info(self, parse_str):
        func_name = "myExpression"   # can use different name in future
        # Numpy
        parse_type = ParserTypeEnum.NUMPY
        content = parse_la(parse_str, parse_type)
        module_name = 'la_test.generated_code{}'.format(BasePythonTest.cnt)
        file_name = 'la_test/generated_code{}.py'.format(BasePythonTest.cnt)
        try:
            file = open(file_name, 'w')
            file.write(content)
            file.close()
        except IOError:
            print("IO Error!")
        module = importlib.import_module(module_name)
        subprocess.run(["rm", file_name], capture_output=False)
        # Eigen
        parse_type = ParserTypeEnum.EIGEN
        content = parse_la(parse_str, parse_type)
        # add namespace
        namespace = "eigen_code{}".format(BasePythonTest.cnt)
        pos = content.rfind("#include")
        sub_content = content[pos:]
        pos += sub_content.find('\n')
        content = content[:pos+1] + 'namespace {}{{\n'.format(namespace) + content[pos+1:] + '\n}'
        try:
            eig_file_name = 'la_test/generated_code{}.cpp'.format(BasePythonTest.cnt)
            file = open(eig_file_name, 'w')
            file.write(content)
            file.close()
        except IOError:
            print("IO Error!")
        eig_test_name = "test_eigen{}".format(BasePythonTest.cnt)
        eig_func_name = "{}::{}".format(namespace, func_name)
        # update cnt
        BasePythonTest.cnt += 1
        return TestFuncInfo(getattr(module, func_name), eig_file_name, eig_test_name, eig_func_name)

    def assertDMatrixEqual(self, A, B):
        # dense matrix comparision
        assert A.shape == B.shape
        assert (A == B).all()

    def assertSMatrixEqual(self, A, B):
        # coo matrix comparision
        assert A.shape == B.shape
        assert (A.data == B.data).all()
        assert (A.row == B.row).all()
        assert (A.col == B.col).all()
