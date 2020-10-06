from enum import Enum, IntFlag
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