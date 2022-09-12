import base64
import time
from enum import Enum, Flag
from tatsu._version import __version__
import sys
from textwrap import dedent
import keyword
from sympy import *
import regex as re
from .la_logger import *


DEBUG_MODE = True
DEBUG_PARSER = False  # used for new grammer files
DEBUG_TIME = False    # used for time recoding (to optimize)
TEST_MATLAB = False   # used for running tests for MATLAB
start_time = None
# constants used as folder name
INPUT_HISTORY = "input_history"
OUTPUT_CODE = "output_code"
IMG_CODE = "."
class ParserTypeEnum(Flag):
    INVALID = 0
    # DEFAULT = 15
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
    MACROMATHJAX = 1024
    GLSL = 2048
## TODO: Q: Do we want to store lists or sets instead of using bitwise enum functionality?
ParserTypeEnumDefaults = ParserTypeEnum.LATEX | ParserTypeEnum.NUMPY | ParserTypeEnum.EIGEN | ParserTypeEnum.MATLAB

def is_keyword(name, parser_type=ParserTypeEnumDefaults):
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


def mul_syms(lhs, rhs):
    if not isinstance(lhs, str) and not isinstance(rhs, str):
        res = lhs * rhs
    else:
        res = "{}*{}".format(lhs, rhs)
    return sympify(res)


def add_syms(lhs, rhs):
    if not isinstance(lhs, str) and not isinstance(rhs, str):
        res = lhs + rhs
    else:
        res = "{}+{}".format(lhs, rhs)
    return sympify(res)


def subtract_syms(lhs, rhs):
    if not isinstance(lhs, str) and not isinstance(rhs, str):
        res = lhs + rhs
    else:
        res = "{}-{}".format(lhs, rhs)
    return sympify(res)


def simpify_dims(dims):
    return sympify(dims)


def is_new_tatsu_version():
    return __version__ >= '5.0.0'


def base64_encode(content):
    if content is None:
        return content
    return base64.b64encode(content.encode("utf-8")).decode("utf-8")


def save_to_file(content, file_name):
    try:
        file = open(file_name, 'w', encoding='utf-8')
        file.write(content)
        file.close()
    except IOError as e:
        print("IO Error!:{}".format(e))


def get_file_base(name):
    sec = name.split('/')
    path = '/'.join(sec[:-1])
    return path if path != '' else '.', sec[-1].split('.')[0]


def get_file_suffix(name):
    return name.split('/')[-1].split('.')[-1]


def get_resource_dir():
    return "./extras/resource/img"


def record(msg=''):
    if DEBUG_TIME:
        global start_time
        if start_time is None or msg == '':
            start_time = time.time()
            print("%.2f seconds: " % (0) + "start")
        else:
            print("%.2f seconds: " % (time.time() - start_time) + msg)


def read_from_file(file_name):
    try:
        file = open(file_name, 'r', encoding='utf-8')
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


# BLOCK_RE = re.compile(
#         dedent(r'''(?P<main>(`[^`]*`)|([A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*)?)(\_)(?P<sub>((`[^`]*`)|([A-Za-z0-9\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*)?)+)'''),
#         re.MULTILINE | re.DOTALL | re.VERBOSE
#     )
BLOCK_RE = re.compile(
        dedent(
            r'''(?P<main>(`[^`]*`)|([A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*)?)(\_)(?P<sub>((`[^`]*`)|([A-Za-z0-9\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*)|(,)|(\*)?)+)'''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )
UNICODE_RE = re.compile(
        dedent(r'''(?P<main>(`[^`]*`)|([A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*)?)(?P<sub>[\u2080-\u2089,]+)'''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )

def filter_subscript(symbol):
    # x_i to x
    m = BLOCK_RE.fullmatch(symbol)
    if m:
        main = m.group('main')
        # print("filter_subscript, symbol:{}, main:{} ".format(symbol, main))
        return main
    else:
        m = UNICODE_RE.fullmatch(symbol)
        if m:
            return m.group('main')
    return symbol


def la_debug(msg):
    LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT).debug(msg)


def la_warning(msg):
    LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT).warning(msg)


def la_error(msg):
    LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT).error(msg)


def la_info(msg):
    LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT).info(msg)