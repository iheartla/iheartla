import unittest
import sys
import importlib
from importlib import reload
sys.path.append('./')
from iheartla.la_parser.parser import parse_la, ParserTypeEnum, compile_la_content
import subprocess
from time import sleep
import numpy as np
import logging
from iheartla.la_tools.la_logger import LaLogger, LoggerTypeEnum
eigen_path = "/usr/local/include/eigen3"       # required


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
        self.eps = 1e-7
        self.import_trig = "from trigonometry: sin,asin,arcsin,cos,acos,arccos,tan,atan,arctan,atan2,sinh,asinh,arsinh,cosh,acosh,arcosh,tanh,atanh,artanh,cot,sec,csc\n"
        self.import_trig += "from linearalgebra: trace,tr,trace,tr,diag,vec,det,rank,null,orth,inv\n"
        if BasePythonTest.cnt == 0:
            LaLogger.getInstance().set_level(logging.ERROR)

    def gen_func_info(self, parse_str):
        func_name = "myExpression"   # can use different name in future
        # Numpy
        results = compile_la_content(parse_str, ParserTypeEnum.NUMPY | ParserTypeEnum.EIGEN)
        module_name = 'test.generated_code{}'.format(BasePythonTest.cnt)
        file_name = 'test/generated_code{}.py'.format(BasePythonTest.cnt)
        try:
            file = open(file_name, 'w')
            file.write(results[0])
            file.close()
        except IOError:
            print("IO Error!")
        module = importlib.import_module(module_name)
        subprocess.run(["rm", file_name], capture_output=False)
        # Eigen
        content = results[1]
        # add namespace
        namespace = "eigen_code{}".format(BasePythonTest.cnt)
        pos = content.rfind("#include")
        sub_content = content[pos:]
        pos += sub_content.find('\n')
        content = content[:pos+1] + 'namespace {}{{\n'.format(namespace) + content[pos+1:] + '\n}'
        try:
            eig_file_name = 'test/generated_code{}.cpp'.format(BasePythonTest.cnt)
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

    def assertDMatrixApproximateEqual(self, A, B):
        # dense matrix comparision( with double value)
        assert A.shape == B.shape
        assert np.allclose(A, B, rtol=0, atol=self.eps)

    def assertSMatrixEqual(self, A, B):
        # coo matrix comparision
        assert A.shape == B.shape
        # assert (A.data == B.data).all()
        assert np.allclose(A.data, B.data, rtol=0, atol=self.eps)
        assert (A.row == B.row).all()
        assert (A.col == B.col).all()
