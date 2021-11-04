from enum import Enum, IntFlag
from tatsu._version import __version__
import sys
import keyword
from sympy import *
import regex as re


DEBUG_MODE = True
DEBUG_PARSER = False  # used for new grammer files
TEST_MATLAB = False   # used for running tests for MATLAB
class ParserTypeEnum(IntFlag):
    INVALID = 0
    DEFAULT = 15
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
    MATHML = 512


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


def is_same_expr(lhs, rhs):
    return sympify('{} == {}'.format(lhs, rhs))


def mul_dims(lhs, rhs):
    if not isinstance(lhs, str) and not isinstance(rhs, str):
        res = lhs * rhs
    else:
        res = "{}*{}".format(lhs, rhs)
    return sympify(res)


def simpify_dims(dims):
    return sympify(dims)


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


def contains_sub_symbol(identifier):
    # Check whether a raw string contains _
    if '`' in identifier:
        new_id = identifier
        results = re.findall("`[^`]*`", new_id)
        for item in results:
            new_id = new_id.replace(item, '')
        return '_' in new_id
    return '_' in identifier


def split_sub_string(identifier):
    # Check whether a raw string contains _
    if '`' in identifier:
        new_id = identifier
        results = re.findall("`[^`]*`", new_id)
        convert_dict = {}
        for item in results:
            if '_' in item:
                new_item = item.replace('_', '``')
                convert_dict[new_item] = item
                new_id = new_id.replace(item, new_item)
        results = new_id.split('_')
        if len(convert_dict) > 0:
            for i in range(len(results)):
                if results[i] in convert_dict:
                    results[i] = convert_dict[results[i]]
        return results
    return identifier.split('_')
