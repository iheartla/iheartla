from enum import Enum, IntFlag
from tatsu._version import __version__
import sys
import keyword


DEBUG_MODE = False
class ParserTypeEnum(IntFlag):
    INVALID = 0
    DEFAULT = 7
    #
    LATEX = 1
    NUMPY = 2
    EIGEN = 4
    MATLAB = 8
    JULIA = 16
    PYTORCH = 32
    ARMADILLO = 64
    TENSORFLOW = 128
    MATHJAX = 256


def is_keyword(name, parser_type=ParserTypeEnum.DEFAULT):
    if parser_type == ParserTypeEnum.NUMPY:
        return keyword.iskeyword(name)
    elif parser_type == ParserTypeEnum.EIGEN:
        kwlist = "Asm auto bool break case catch char class const_cast continue default delete do double else \
                enum dynamic_cast extern false float for union unsigned using friend goto if \
                inline int long mutable virtual namespace new operator private protected public \
                register void reinterpret_cast return short signed sizeof static static_cast volatile \
                struct switch template this throw true try typedef typeid unsigned wchar_t while"
        keywords = kwlist.split(' ')
        return name in keywords
    else:
        return is_keyword(name, parser_type=ParserTypeEnum.NUMPY) or is_keyword(name, parser_type=ParserTypeEnum.EIGEN)


def is_new_tatsu_version():
    return __version__ >= '5.0.0'


def save_to_file(content, file_name):
    try:
        file = open(file_name, 'w')
        file.write(content)
        file.close()
    except IOError as e:
        print("IO Error!:{}".format(e))


def read_from_file(file_name):
    try:
        file = open(file_name, 'r')
        content = file.read()
        file.close()
    except IOError as e:
        content = ''
        print("IO Error!:{}".format(e))
    return content
