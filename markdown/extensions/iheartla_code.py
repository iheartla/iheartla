from textwrap import dedent
from . import Extension
from ..preprocessors import Preprocessor
from .codehilite import CodeHilite, CodeHiliteExtension, parse_hl_lines
from .attr_list import get_attrs, AttrListExtension
from ..util import parseBoolValue
import re
from iheartla.la_parser.parser import compile_la_content, ParserTypeEnum
from iheartla.la_tools.la_helper import DEBUG_MODE, read_from_file, save_to_file


class BlockData(Extension):
    def __init__(self, match_list=[], code_list=[], block_list=[]):
        self.match_list = match_list
        self.code_list = code_list
        self.block_list = block_list
        self.math_pre = ''
        self.math_list = []
        self.math_post = ''

    def add(self, match, code, block):
        self.match_list.append(match)
        self.code_list.append(code)
        self.block_list.append(block)

    def get_content(self):
        return '\n'.join(self.code_list)


class IheartlaCodeExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {
            'lang_prefix': ['language-', 'Prefix prepended to the language. Default: "language-"']
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        """ Add FencedBlockPreprocessor to the Markdown instance. """
        md.registerExtension(self)

        md.preprocessors.register(IheartlaBlockPreprocessor(md, self.getConfigs()), 'iheartla_code_block', 25)


class IheartlaBlockPreprocessor(Preprocessor):
    FENCED_BLOCK_RE = re.compile(
        dedent(r'''
            (?P<fence>^(?:~{3,}|`{3,}))[ ]*                          # opening fence
            iheartla
            ((\((?P<attrs>[^\}\n]*)\))|                              # (optional {attrs} or
            (\.?(?P<lang>[\w#.+-]*)[ ]*)?                            # optional (.)lang
            (hl_lines=(?P<quot>"|')(?P<hl_lines>.*?)(?P=quot)[ ]*)?) # optional hl_lines)
            \n                                                       # newline (end of opening fence)
            (?P<code>.*?)(?<=\n)                                     # the code block
            (?P=fence)[ ]*$                                          # closing fence
        '''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )

    def __init__(self, md, config):
        super().__init__(md)
        self.config = config
        self.checked_for_deps = False
        self.codehilite_conf = {}
        self.use_attr_list = False
        # List of options to convert to bool values
        self.bool_options = [
            'linenums',
            'guess_lang',
            'noclasses',
            'use_pygments'
        ]

    def run(self, lines, **kwargs):
        """ Match and store Fenced Code Blocks in the HtmlStash. """
        # Check for dependent extensions
        if not self.checked_for_deps:
            for ext in self.md.registeredExtensions:
                if isinstance(ext, CodeHiliteExtension):
                    self.codehilite_conf = ext.getConfigs()
                if isinstance(ext, AttrListExtension):
                    self.use_attr_list = True

            self.checked_for_deps = True
        text = "\n".join(lines)
        file_dict = {}
        # Find all blocks
        for m in self.FENCED_BLOCK_RE.finditer(text):
            module_name = m.group('attrs')
            if module_name and m.group('code'):
                if module_name not in file_dict:
                    file_dict[module_name] = BlockData([m], [m.group('code')], [m.group(0)])
                else:
                    file_dict[module_name].add(m, m.group('code'), m.group(0))
        # Save to file
        for name, block_data in file_dict.items():
            source = '\n'.join(block_data.code_list)
            file_name = "{}/{}.ihla".format(kwargs['path'], name)
            save_to_file(source, file_name)
        # compile
        lib_header = None
        lib_content = ''
        json_list = []
        for name, block_data in file_dict.items():
            code_list, json = compile_la_content(block_data.get_content(), parser_type=ParserTypeEnum.EIGEN | ParserTypeEnum.MATHML,
                                           func_name=name, path=kwargs['path'], struct=True, get_json=True)
            json_list.append('''{{"name":"{}", {} }}'''.format(name, json))
            if lib_header is None:
                lib_header = code_list[0].include
            lib_content += code_list[0].struct + '\n'
            # Find all expr for each original iheartla block
            index_dict = {}
            expr_dict = code_list[1].expr_dict
            for raw_text, math_code in expr_dict.items():
                for cur_index in range(len(block_data.code_list)):
                    if raw_text in block_data.code_list[cur_index]:
                        if cur_index not in index_dict:
                            index_dict[cur_index] = [raw_text]
                        else:
                            index_dict[cur_index].append(raw_text)
                        break
            # Replace math code
            for cur_index in range(len(block_data.code_list)):
                if len(index_dict[cur_index]) == 1:
                    raw_str = index_dict[cur_index][0]
                    text = text.replace(block_data.block_list[cur_index], code_list[1].pre_str+expr_dict[raw_str]+code_list[1].post_str)
                else:
                    # more than one expr in a single block
                    order_list = []
                    for raw_str in index_dict[cur_index]:
                        order_list.append(text.index(raw_str))
                    sorted_index = sorted(range(len(order_list)), key=lambda k: order_list[k])
                    content = code_list[1].pre_str
                    for cur in range(len(sorted_index)):
                        raw_str = index_dict[cur_index][sorted_index[cur]]
                        content += expr_dict[raw_str] + '\n'
                    content += code_list[1].post_str
                    text = text.replace(block_data.block_list[cur_index], content)
        json_content = '''{{"equations":[{}] }}'''.format(','.join(json_list))
        if lib_header is not None:
            save_to_file("#pragma once\n" + lib_header + lib_content, "{}/lib.h".format(kwargs['path']))
        if json_content is not None:
            save_to_file(json_content, "{}/data.json".format(kwargs['path']))
        return text.split("\n")


    def _escape(self, txt):
        """ basic html escaping """
        txt = txt.replace('&', '&amp;')
        txt = txt.replace('<', '&lt;')
        txt = txt.replace('>', '&gt;')
        txt = txt.replace('"', '&quot;')
        return txt


def makeExtension(**kwargs):  # pragma: no cover
    return IheartlaCodeExtension(**kwargs)
