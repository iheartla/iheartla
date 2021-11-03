from textwrap import dedent
from . import Extension
from ..preprocessors import Preprocessor
from .codehilite import CodeHilite, CodeHiliteExtension, parse_hl_lines
from .attr_list import get_attrs, AttrListExtension
from ..util import parseBoolValue
import re
from iheartla.la_parser.parser import compile_la_content, ParserTypeEnum
from iheartla.la_tools.la_helper import DEBUG_MODE, read_from_file, save_to_file


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
        pre_text = text
        source_list = []
        name_list = []
        match_list = []
        while 1:
            m = self.FENCED_BLOCK_RE.search(pre_text)
            if m:
                if m.group('attrs') and m.group('code'):
                    file_name = "{}/{}.ihla".format(kwargs['path'], m.group('attrs'))
                    save_to_file(m.group('code'), file_name)
                    source_list.append(m.group('code'))
                    name_list.append(m.group('attrs'))
                    match_list.append(m.start())
                pre_text = '{}\n{}\n{}'.format(text[:m.start()], '', pre_text[m.end():])
            else:
                break
        cur_index = 0
        lib_header = None
        lib_content = ''
        while 1:
            m = self.FENCED_BLOCK_RE.search(text)
            if m:
                code_list = compile_la_content(source_list[cur_index], parser_type=ParserTypeEnum.EIGEN | ParserTypeEnum.MATHJAX,
                                               func_name=name_list[cur_index], path=kwargs['path'], struct=True)
                if lib_header is None:
                    lib_header = code_list[0].include
                lib_content += code_list[0].struct + '\n'
                print("name:{} ".format(name_list[cur_index]))
                print("code_list:{} ".format(code_list))
                code = '<pre><mathjax>{code}</mathjax></pre>'.format(
                    code=code_list[1].get_mathjax_content()
                )
                placeholder = self.md.htmlStash.store(code)
                text = '{}\n{}\n{}'.format(text[:m.start()],
                                           placeholder,
                                           text[m.end():])
                cur_index += 1
            else:
                break
        if lib_header is not None:
            save_to_file(lib_header + lib_content, "{}/lib.h".format(kwargs['path']))
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
