import unittest
import sys
import importlib
from importlib import reload
sys.path.append('./')
from la_parser.parser import parse_la, ParserTypeEnum
import subprocess
from time import sleep
import numpy as np


class BasePythonTest(unittest.TestCase):
    cnt = 0

    def __init__(self, *args, **kwargs):
        super(BasePythonTest, self).__init__(*args, **kwargs)

    def set_up(self, parse_str, parse_type):
        if parse_type is None:
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
        BasePythonTest.cnt += 1
        module = importlib.import_module(module_name)
        subprocess.run(["rm", file_name], capture_output=False)
        return module.myExpression

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
