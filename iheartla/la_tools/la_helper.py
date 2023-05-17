import base64
import copy
import os
import time
from enum import Enum, Flag
from tatsu._version import __version__
import sys
from textwrap import dedent
import keyword
from sympy import *
import regex as re
from pathlib import Path
from .la_logger import *


DEBUG_MODE = True
DEBUG_PARSER = False  # used for new grammer files
DEBUG_TIME = False    # used for time recoding (to optimize)
TEST_MATLAB = False   # used for running tests for MATLAB
CLASS_ONLY = True     # output class without random data and main func
CACHE_MODULE = True   # whether to cache compiled module into local files
start_time = None
# constants used as folder name
INPUT_HISTORY = "input_history"
OUTPUT_CODE = "output_code"
IMG_CODE = "."
CLASS_NAME = "heartlib"   # class name for generated code
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
## TODO: Q: Do we want to store lists or sets instead of using bitwise enum functionality?
ParserTypeEnumDefaults = ParserTypeEnum.LATEX | ParserTypeEnum.NUMPY | ParserTypeEnum.EIGEN | ParserTypeEnum.MATLAB
ParserTypeDict = {ParserTypeEnum.LATEX: "latex",
                  ParserTypeEnum.NUMPY: "numpy",
                  ParserTypeEnum.EIGEN: "eigen",
                  ParserTypeEnum.MATLAB: "matlab",
                  ParserTypeEnum.JULIA: "julia",
                  ParserTypeEnum.PYTORCH: "pytorch",
                  ParserTypeEnum.MATHJAX: "mathjax",
                  ParserTypeEnum.MACROMATHJAX: "macromathjax"}

TEMPLATE_RE = re.compile(
        dedent(
            r'''template<class[^\n]*\n'''),
        re.DOTALL | re.VERBOSE
    )

def remove_submodule_template(text):
    # remove template in nested struct
    result = text
    for m in TEMPLATE_RE.finditer(text):
        result = result.replace(m.group(), '')
    return result


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


def delete_ast_files():
    # delete visualized files
    if DEBUG_MODE:
        for f in Path('.').glob('AST*'):
            os.remove(f)

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

def is_ast_assignment(node):
    # check the original node from tatsu
    return type(node).__name__ == 'Assignment' or type(node).__name__ == 'Destructure'


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


def replace_sym_dims(sym_dict, mapping_dict):
    # given symtable, replace the dimensions for each la_type
    for sym in sym_dict:
        sym_dict[sym].replace_sym_dims(mapping_dict)
    return sym_dict


def la_debug(msg):
    LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT).debug(msg)


def la_warning(msg):
    LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT).warning(msg)


def la_error(msg):
    LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT).error(msg)


def la_info(msg):
    LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT).info(msg)


def get_unicode_number(unicode):
    # 0:\u2070,1:\u00B9,2:\u00B2,3:\u00B3,4-9:[\u2074-\u2079]
    number_dict = {'⁰':0,'¹':1,'²':2, '³':3,'⁴':4,'⁵':5,'⁶':6,'⁷':7,'⁸':8,'⁹':9 }
    return number_dict[unicode] if unicode in number_dict else unicode

def get_unicode_sub_number(unicode):
    # 0-9:[\u2080-\u2089]
    number_dict = {'₀':0,'₁':1,'₂':2, '₃':3,'₄':4,'₅':5,'₆':6,'₇':7,'₈':8,'₉':9 }
    return number_dict[unicode] if unicode in number_dict else unicode

def get_unicode_fraction(unicode):
    fraction_dict = {'¼':[1,4],'½':[1,2],'¾':[3,4],'⅐':[1,7],'⅑':[1,9],'⅒':[1,10],'⅓':[1,3],'⅔':[2,3],
                   '⅕':[1,5],'⅖':[2,5],'⅗':[3,5],'⅘':[4,5],'⅙':[1,6],'⅚':[5,6],'⅛':[1,8],'⅜':[3,8],'⅝':[5,8],
                   '⅞':[7,8]}
    return fraction_dict[unicode] if unicode in fraction_dict else unicode

def get_unicode_subscript(unicode):
    subscript_dict = {'ₐ':'a', 'ₑ':'e', 'ₒ':'o', 'ₓ':'x', 'ₕ':'h', 'ₖ':'k', 'ₗ':'l', 'ₘ':'m', 'ₙ':'n', 'ₚ':'p', 'ₛ':'s', 'ₜ':'t', 'ᵢ':'i', 'ⱼ':'j'}
    return subscript_dict[unicode] if unicode in subscript_dict else unicode

def get_unicode_superscript(unicode):
    superscript_dict = {'ᵃ':'a', 'ᵇ':'b', 'ᶜ':'c', 'ᵈ':'d', 'ᵉ':'e', 'ᶠ':'f', 'ᵍ':'g', 'ʰ':'h', 'ⁱ':'i', 'ʲ':'j', 'ᵏ':'k',
                        'ˡ':'l', 'ᵐ':'m', 'ⁿ':'n', 'ᵒ':'o', 'ᵖ':'p', 'ʳ':'r', 'ˢ':'s', 'ᵗ':'t', 'ᵘ':'u', 'ᵛ':'v', 'ʷ':'w',
                        'ˣ':'x', 'ʸ':'y', 'ᶻ':'z', 'ᴬ':'A', 'ᴮ':'B', 'ᴰ':'D', 'ᴱ':'E', 'ᴳ':'G', 'ᴴ':'H', 'ᴵ':'I', 'ᴶ':'J',
                        'ᴷ':'K', 'ᴸ':'L', 'ᴹ':'M', 'ᴺ':'N', 'ᴼ':'O', 'ᴾ':'P', 'ᴿ':'R', 'ᵀ':'T', 'ᵁ':'U', 'ⱽ':'V', 'ᵂ':'W'}
    return superscript_dict[unicode] if unicode in superscript_dict else unicode