import unittest
import sys
from importlib import reload
sys.path.append('./')
from la_parser.parser import parse_la, ParserTypeEnum
import subprocess
from time import sleep


class BasePythonTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(BasePythonTest, self).__init__(*args, **kwargs)
        self.cnt = 0

    def set_up(self, parse_str, parse_type):
        if parse_type is None:
            parse_type = ParserTypeEnum.NUMPY
        content = parse_la(parse_str, parse_type)
        try:
            file = open('la_test/generated_code.py', 'w')
            file.write(content)
            file.close()
        except IOError:
            print("IO Error!")
        self.cnt += 1
        # subprocess.run(["rm", "la_test/generated_code.py"], capture_output=False)
        import la_test.generated_code
        from la_test.generated_code import myExpression
        sleep(0.8)
        return reload(la_test.generated_code).myExpression
