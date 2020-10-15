from enum import Enum, IntFlag
from tatsu._version import __version__
import sys
import keyword


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


def check_version():
    version_info = sys.version_info
    tatsu_version = __version__
    valid = False
    msg = ''
    if tatsu_version >= '5.0.0':
        if version_info.major >= 3 and version_info.minor >= 8:
            valid = True
        else:
            msg = 'Tatsu {} requires Python >= 3.8'.format(tatsu_version)
    else:
        valid = True
    return valid, msg


def is_new_tatsu_version():
    return __version__ >= '5.0.0'
