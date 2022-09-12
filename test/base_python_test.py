import unittest
import sys
import importlib
from importlib import reload
sys.path.append('./')
from iheartla.la_parser.parser import parse_la, ParserTypeEnum, compile_la_content
from iheartla.la_tools.la_helper import TEST_MATLAB, save_to_file
import subprocess
from time import sleep
import numpy as np
import logging
from iheartla.la_tools.la_logger import LaLogger, LoggerTypeEnum
eigen_path = "/usr/local/include/eigen3"       # required
if TEST_MATLAB:
    # Install the library using the following link
    # https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html
    import matlab
    import matlab.engine
    mat_engine = matlab.engine.start_matlab()
    mat_engine.addpath(mat_engine.genpath('test'), nargout=0)


class TestFuncInfo(object):
    def __init__(self, numpy_func=None, eig_file_name=None, eig_test_name=None, eig_func_name=None, mat_file_name=None, mat_func_name=None):
        super().__init__()
        # Numpy
        self.numpy_func = numpy_func  # func content
        # Eigen
        self.eig_file_name = eig_file_name   # generated cpp file name
        self.eig_func_name = eig_func_name   # func name
        self.eig_test_name = eig_test_name   # test func name
        # MATLAB
        self.mat_file_name = mat_file_name   # generated cpp file name
        self.mat_func_name = mat_func_name  # func name


class BasePythonTest(unittest.TestCase):
    cnt = 0

    def __init__(self, *args, **kwargs):
        super(BasePythonTest, self).__init__(*args, **kwargs)
        self.eps = 1e-7
        self.import_trig = "sin,asin,arcsin,cos,acos,arccos,tan,atan,arctan,atan2,sinh,asinh,arsinh,cosh,acosh,arcosh,tanh,atanh,artanh,cot,sec,csc from trigonometry\n"
        self.import_trig += "trace,tr,trace,tr,diag,vec,det,rank,null,orth,inv from linearalgebra\n"
        if BasePythonTest.cnt == 0:
            LaLogger.getInstance().set_level(logging.ERROR)

    def gen_func_info(self, parse_str):
        func_name = "iheartla"   # can use different name in future
        parse_type = ParserTypeEnum.NUMPY | ParserTypeEnum.EIGEN | ParserTypeEnum.GLSL
        if TEST_MATLAB:
            parse_type = parse_type | ParserTypeEnum.MATLAB
        # Numpy
        results = compile_la_content(parse_str, parse_type)
        module_name = 'test.generated_code{}'.format(BasePythonTest.cnt)
        file_name = 'test/generated_code{}.py'.format(BasePythonTest.cnt)
        save_to_file(results[ParserTypeEnum.NUMPY], file_name)
        module = importlib.import_module(module_name)
        subprocess.run(["rm", file_name], capture_output=False)
        # Eigen
        content = results[ParserTypeEnum.EIGEN]
        # add namespace
        namespace = "eigen_code{}".format(BasePythonTest.cnt)
        pos = content.rfind("#include")
        sub_content = content[pos:]
        pos += sub_content.find('\n')
        content = content[:pos+1] + 'namespace {}{{\n'.format(namespace) + content[pos+1:] + '\n}'
        eig_file_name = 'test/generated_code{}.cpp'.format(BasePythonTest.cnt)
        save_to_file(content, eig_file_name)
        eig_test_name = "test_eigen{}".format(BasePythonTest.cnt)
        eig_func_name = "{}::{}".format(namespace, func_name)
        # MATLAB
        mat_file_name = None
        mat_func_name = None
        if TEST_MATLAB:
            mat_content = results[ParserTypeEnum.MATLAB]
            mat_func_name = "iheartla_{}".format(BasePythonTest.cnt)
            mat_content = mat_content.replace('iheartla', mat_func_name)
            mat_file_name = 'test/{}.m'.format(mat_func_name)
            save_to_file(mat_content, mat_file_name)
        # update cnt
        BasePythonTest.cnt += 1
        return TestFuncInfo(getattr(module, func_name), eig_file_name, eig_test_name, eig_func_name, mat_file_name, mat_func_name)

    def assertDMatrixEqual(self, A, B):
        # dense matrix comparision
        assert A.shape == B.shape
        # assert (A == B).all()
        assert np.allclose(A, B, rtol=0, atol=self.eps)

    def assertDMatrixApproximateEqual(self, A, B):
        # dense matrix comparision( with double value)
        assert A.shape == B.shape
        assert np.allclose(A, B, rtol=0, atol=self.eps)

    def assertSMatrixEqual(self, A, B):
        # coo matrix comparision
        assert A.shape == B.shape
        # assert (A.data == B.data).all()
        # assert np.allclose(A.data, B.data, rtol=0, atol=self.eps)
        assert (abs(A-B) > self.eps).nnz == 0
        # assert (A.row == B.row).all()
        # assert (A.col == B.col).all()
