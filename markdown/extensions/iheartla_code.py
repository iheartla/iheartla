from textwrap import dedent
from . import Extension, WHEEL_MODE
from ..preprocessors import Preprocessor
from ..postprocessors import Postprocessor
from .codehilite import CodeHilite, CodeHiliteExtension, parse_hl_lines
from .attr_list import get_attrs, AttrListExtension
from ..util import parseBoolValue
import copy
from collections import OrderedDict
import regex as re
import base64
if WHEEL_MODE:
    from linear_algebra.iheartla.la_parser.parser import compile_la_content, ParserTypeEnum
    from linear_algebra.iheartla.la_tools.la_helper import DEBUG_MODE, read_from_file, save_to_file, la_warning, la_debug, get_file_base
else:
    from iheartla.la_parser.parser import compile_la_content, ParserTypeEnum
    from iheartla.la_tools.la_helper import DEBUG_MODE, read_from_file, save_to_file, la_warning, la_debug, get_file_base


class BlockData(Extension):
    def __init__(self, match_list=[], code_list=[], block_list=[], inline_list=[], number_list=[], module_name=''):
        self.module_name = module_name
        self.match_list = match_list
        self.code_list = code_list
        self.block_list = block_list
        self.inline_list = inline_list
        self.number_list = number_list
        self.math_pre = ''
        self.math_list = []
        self.math_post = ''

    def add(self, match, code, block, inline=False, number=True):
        self.match_list.append(match)
        self.code_list.append(code)
        self.block_list.append(block)
        self.inline_list.append(inline)
        self.number_list.append(number)

    def get_content(self):
        return '\n'.join(self.code_list)


class IheartlaCodeExtension(Extension):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = {
            'lang_prefix': ['language-', 'Prefix prepended to the language. Default: "language-"']
        }

    def extendMarkdown(self, md):
        """ Add FencedBlockPreprocessor to the Markdown instance. """
        md.registerExtension(self)

        md.preprocessors.register(IheartlaBlockPreprocessor(md, self.getConfigs()), 'iheartla_code_block', 25)
        md.postprocessors.register(IheartlaBlockPostprocessor(md, self.getConfigs()), 'iheartla_code_post_block', 26)


class IheartlaBlockPostprocessor(Postprocessor):
    #
    REFERENCE_RE = re.compile(
        dedent(r'''\<p\>\[ref(?P<index>\d*)\]:(?P<context>[^<>]*)<\/p\>'''),
        re.DOTALL | re.VERBOSE
    )
    def __init__(self, md, config):
        super().__init__(md)
        self.config = config

    def run(self, text):
        # for m in self.REFERENCE_RE.finditer(text):
        #     # print("cur:{}".format(m.group('context')))
        #     text = text.replace(m.group(), "<p id='ref{}'>{}</p>".format(m.group('index'), m.group('context')))
        # return '<pre>\n' + re.sub('<', '&lt;', text) + '</pre>\n'
        return text


class IheartlaBlockPreprocessor(Preprocessor):
    # Match string: ``` iheartla (context)
    FENCED_BLOCK_RE = re.compile(
        dedent(r'''
            (?P<fence>^(?:~{3,}|`{3,}))[ ]*                          # opening fence
            iheartla\s*
            (\((?P<module>[^\}\n]*)\))                        # required {module} 
            \n                                                       # newline (end of opening fence)
            (?P<code>.*?)(?<=\n)                                     # the code block
            (?P=fence)[ ]*$                                          # closing fence
        '''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )
    # ``` python
    FIGURE_CODE_RE = re.compile(
        dedent(r'''
                (?P<fence>^(?:~{3,}|`{3,}))[ ]*                          # opening fence
                python\s* 
                \n                                                       # newline (end of opening fence)
                (?P<code>.*?)(?<=\n)                                     # the code block
                (?P=fence)[ ]*$                                          # closing fence
            '''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )
    # Match string: <figure>***</figure>
    FIGURE_BLOCK_RE = re.compile(
        dedent(r'''<figure>(?P<figure>.*?)</figure>'''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )
    # Match string: <img src='' ***>
    IMAGE_BLOCK_RE = re.compile(
        dedent(r'''<img\ (?P<before>[^\n>]*)src=(?P<quote>"|')(?P<src>[^\n'">]*)(?P=quote)(?P<after>[^\n>]*)>'''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )
    # Match string: <span class="def">***</span>
    EASY_SPAN_BLOCK_RE = re.compile(
        dedent(r'''<span\ class=(?P<quote>"|')def(?P=quote)>(?P<code>.*?)</span>'''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )
    # Match string: <span class="def:context:symbol">***</span>
    EASY_SPAN_CONTEXT_BLOCK_RE = re.compile(
        dedent(r'''<span\ class=(?P<quote>"|')def:(?P<context>[^\n:❤'"]*)(?P=quote)>(?P<code>.*?)</span>'''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )
    # Match string: <span class="def:context:symbol">***</span>
    SPAN_BLOCK_RE = re.compile(
        dedent(r'''<span\ class=(?P<quote>"|')def:(?P<context>[^\n:❤'"]*)(:)(?P<symbol>[^:>'"]*)(?P=quote)>(?P<code>.*?)</span>'''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )
    # Match string: <span class="def:symbol">***</span>
    SPAN_SIMPLE_RE = re.compile(
        dedent(r'''<span\ class=(?P<quote>"|')def:(?P<symbol>[^:>'"]*)(?P=quote)>(?P<code>.*?)(</span>)'''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )
    # Match string: ❤️context: a=sin(θ)❤️
    INLINE_RE = re.compile(
        dedent(r'''❤(?P<module>[a-zA-Z0-9\.\t\r\f\v ]*)(:)(?P<code>.*?)❤'''),
        re.MULTILINE | re.VERBOSE
    )
    # Match string: # REFERENCES
    REFERENCE_RE = re.compile(
        dedent(r'''\#(\s*)REFERENCES'''),
        re.DOTALL | re.VERBOSE
    )
    # Match string: ❤ : context
    CONTEXT_RE = re.compile(
        dedent(r'''(?<=(\n)*)([\t\r\f\v ]*)❤(\s*):(?P<context>[^\n❤]*)(?=\n)'''),
        re.MULTILINE | re.VERBOSE
    )
    # Match string: ``` iheartla
    RAW_CODE_BLOCK_RE = re.compile(
        dedent(r'''
            (?P<fence>^(?:~{3,}|`{3,}))[ ]*                          # opening fence
            iheartla\s*
            \n                                                       # newline (end of opening fence)
        '''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )
    # Match string: ``` iheartla_unnumbered
    RAW_NUM_CODE_BLOCK_RE = re.compile(
        dedent(r'''
            (?P<fence>^(?:~{3,}|`{3,}))[ ]*                          # opening fence
            iheartla_unnumbered\s*
            \n                                                       # newline (end of opening fence)
        '''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )
    # Match string: ❤ a=sin(θ)❤
    RAW_CODE_INLINE_RE = re.compile(
        dedent(r'''❤(?P<code>[^❤]*)❤'''),
        re.MULTILINE | re.VERBOSE
    )
    # Match string: \proselabel{A}  \prosedeflabel{A}
    PROSE_RE = re.compile(
        dedent(r'''\\prose(?P<def>(def)?)label\{(?P<symbol>[^{}$]*)\}(?!\{)'''),
        re.MULTILINE | re.VERBOSE
    )
    # Match string:  $$ eq $$, $ eq $
    MATH_RE = re.compile(
        dedent(r'''(?<!\\)    # negative look-behind to make sure start is not escaped 
        ((?<!\$)\${1,2}(?!\$))
        ((?P<code>.*?))(?<!\\)
        (?<!\$)\1(?!\$)'''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )
    # Match string:  \n \s
    BLANK_RE = re.compile(
        dedent(r'''[\n\s]*'''),
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

    def escape_sym(self, sym):
        """
        Escape special characters in regular expression
        """
        escape_list = ['\\', '(', ')', '{', '}', '^', '+', '-', '.', '*', ' ']
        for es in escape_list:
            sym = sym.replace(es, '\\' + es)
        return sym

    def handle_math(self, text, context, sym_list):
        """
        Based on the symbol list from iheartla code, search those symbols in math expression
        :param text: raw text in current context
        :param context: current context name
        :param sym_list: symbol list
        :return: replaced text
        """
        for m in self.MATH_RE.finditer(text):
            content = m.group('code')
            # print("current equation:{}".format(m.group()))
            for sym in sym_list:
                PROSE_RE = re.compile(
                    dedent(r'''(?<!(    # negative begins
                    (\\(proselabel|prosedeflabel)({{([a-z\p{{Ll}}\p{{Lu}}\p{{Lo}}\p{{M}}\s]+)}})?{{([a-z\p{{Ll}}\p{{Lu}}\p{{Lo}}\p{{M}}_{{()\s\\]*)))
                    |
                    ([a-zA-Z]+)
                    ) # negative ends
                    ({})
                    (?![a-zA-Z]+)'''.format(self.escape_sym(sym))),
                    re.MULTILINE | re.DOTALL | re.VERBOSE
                )
                changed = True
                while changed:
                    changed = False
                    for target in PROSE_RE.finditer(content):
                        changed = True
                        content = content[:target.start()] + "{{\\proselabel{{{}}}{{{{{}}}}}}}".format(context,
                                                                                               sym) + content[
                                                                                                      target.end():]
                        break
            if content != m.group('code'):
                # print("text is{}".format(text))
                # print("handle_math, content:{}, group:{}, full:{}".format(content, m.group(), m.group()))
                text = text.replace(m.group(), "{}{}{}".format(m.group(1), content, m.group(1)))
                # print("handle_math, m.group():{}, replaced:{}".format(m.group(), "{}{}{}".format(m.group(1), content, m.group(1))))
                # print("handle_math, after:{}".format(text))
        # print("after, text:{}\n".format(text))
        return text

    def handle_easy_span_context_math(self, text, equation_dict, span_dict):
        """
        Based on the symbol list from iheartla code, search those symbols from math block in current span
        :param text: raw text
        :param equation_dict: equation_data -> euqationData
        :param span_dict: context -> dict (sym -> desc)
        :return: replaced text
        """
        for m in self.EASY_SPAN_CONTEXT_BLOCK_RE.finditer(text):
            sym_list = equation_dict[m.group('context')].gen_sym_list()
            found_list = []
            desc = m.group('code')
            # sym_list = m.group('symbol').split(';')
            cur_dict = {}
            if m.group('context') in span_dict:
                cur_dict = span_dict[m.group('context')]
            print("easy_span_context, matched:{}".format(m.group()))
            # Multiple math blocks
            for math in self.MATH_RE.finditer(desc):
                code = math.group("code")
                modified = False
                for sym in sym_list:
                    PROSE_RE = re.compile(
                        dedent(r'''(?<!(    # negative begins
                                                    (\\(proselabel|prosedeflabel)({{([a-z\p{{Ll}}\p{{Lu}}\p{{Lo}}\p{{M}}\s]+)}})?{{([a-z\p{{Ll}}\p{{Lu}}\p{{Lo}}\p{{M}}_{{()\s]*)))
                                                    |
                                                    ([a-zA-Z]+)
                                                    ) # negative ends
                                                    ({})
                                                    (?![a-zA-Z]+)'''.format(self.escape_sym(sym))),
                        re.MULTILINE | re.DOTALL | re.VERBOSE
                    )
                    changed = True
                    while changed:
                        changed = False
                        for target in PROSE_RE.finditer(code):
                            modified = True
                            changed = True
                            code = code[:target.start()] + "{{\\prosedeflabel{{{}}}{{{{{}}}}}}}".format(
                                m.group('context'), sym) + code[target.end():]
                            found_list.append(sym)
                            # print("code:{}".format(code))
                            break
                if modified:
                    desc = desc.replace(math.group(), r"""${}$""".format(code))
            # print("handle_span_code, desc:{}".format(desc))
            found_list = list(set(found_list))
            for sym in found_list:
                cur_dict[sym] = m.group('code')
            text = text.replace(m.group(), "<span sym='{}' context='{}'> {} </span>".format(
                ';'.join(found_list).replace('\\', '\\\\'), m.group('context'), desc))
            span_dict[m.group('context')] = cur_dict
        # print("after, text:{}\n".format(text))
        return text, span_dict

    def handle_prose_label(self, text, context):
        for m in self.PROSE_RE.finditer(text):
            # print("prose match: {}, def:{}, symbol:{}".format(m.group(), m.group('def'), m.group('symbol')))
            text = text.replace(m.group(), "{{\\prose{}label{{{}}}{{{{{}}}}}}}".format(m.group('def'), context, m.group('symbol')))
        return text

    def handle_raw_code(self, text, context):
        for m in self.RAW_CODE_BLOCK_RE.finditer(text):
            # print(m.group())
            text = text.replace(m.group(), "{}iheartla({})\n".format(m.group('fence'), context))
        for m in self.RAW_NUM_CODE_BLOCK_RE.finditer(text):
            # print(m.group())
            text = text.replace(m.group(), "{}iheartla({}, unnumbered)\n".format(m.group('fence'), context))
        return text

    def handle_inline_raw_code(self, text, context):
        for m in self.RAW_CODE_INLINE_RE.finditer(text):
            # print("inline_raw_code: {}".format(m.group()))
            if not self.INLINE_RE.fullmatch(m.group()):
                # print("new: {}".format("❤ {}:{}❤".format(context, m.group('code'))))
                text = text.replace(m.group(), "❤ {}:{}❤".format(context, m.group('code')))
        return text

    def handle_raw_span_code(self, text, context):
        """
        add context name to span tag -> def:context:symbol
        """
        for m in self.SPAN_SIMPLE_RE.finditer(text):
            # print("simple_span_code: {}".format(m.group()))
            # print("new: {}".format('<span class="def:{}:{}"> {} </span>'.format(context, m.group('symbol'), m.group('code'))))
            text = text.replace(m.group(), '<span class="def:{}:{}"> {} </span>'.format(context, m.group('symbol'), m.group('code')))
        return text

    def handle_easy_span_code(self, text, context):
        """
        add context name to span tag -> def:context
        :param text: raw text in current context
        :param context: current context name
        :return: replaced text
        """
        for m in self.EASY_SPAN_BLOCK_RE.finditer(text):
            print("easy_span_code: {}".format(m.group()))
            # print("new: {}".format('<span class="def:{}:{}"> {} </span>'.format(context, m.group('symbol'), m.group('code'))))
            text = text.replace(m.group(), '<span class="def:{}"> {} </span>'.format(context, m.group('code')))
        return text

    def handle_span_code(self, text):
        """
        Based on the symbol list in the span tag, search and replace the math block in the span
        """
        span_dict = {}
        for m in self.SPAN_BLOCK_RE.finditer(text):
            cur_dict = {}
            if m.group('context') in span_dict:
                cur_dict = span_dict[m.group('context')]
            desc = m.group('code')
            sym_list = m.group('symbol').split(';')
            for sym in sym_list:
                cur_dict[sym] = desc
            la_debug("handle_span_code, matched:{}".format(m.group()))
            # Multiple math blocks
            for math in self.MATH_RE.finditer(desc):
                code = math.group("code")
                modified = False
                for sym in sym_list:
                    PROSE_RE = re.compile(
                        dedent(r'''(?<!(    # negative begins
                        (\\(proselabel|prosedeflabel)({{([a-z\p{{Ll}}\p{{Lu}}\p{{Lo}}\p{{M}}\s]+)}})?{{([a-z\p{{Ll}}\p{{Lu}}\p{{Lo}}\p{{M}}_{{()\s]*)))
                        |
                        ([a-zA-Z]+)
                        ) # negative ends
                        ({})
                        (?![a-zA-Z]+)'''.format(self.escape_sym(sym))),
                        re.MULTILINE | re.DOTALL | re.VERBOSE
                    )
                    changed = True
                    while changed:
                        changed = False
                        for target in PROSE_RE.finditer(code):
                            modified = True
                            changed = True
                            code = code[:target.start()] + "{{\\prosedeflabel{{{}}}{{{{{}}}}}}}".format(m.group('context'), sym) + code[target.end():]
                            # print("code:{}".format(code))
                            break
                if modified:
                    desc = desc.replace(math.group(), r"""${}$""".format(code))
            # print("handle_span_code, desc:{}".format(desc))
            text = text.replace(m.group(), "<span sym='{}' context='{}'> {} </span>".format(m.group('symbol').replace('\\','\\\\'), m.group('context'), desc))
            span_dict[m.group('context')] = cur_dict
        return text, span_dict

    def handle_context_pre(self, text):
        """
        Process context and fill missing context in various blocks (iheartla code, span code)
        """
        start_index = 0
        text_list = []
        context_list = ['']
        matched_list = ['']
        for m in self.CONTEXT_RE.finditer(text):
            # print("parsed context: {}".format(m.group('context')))
            context_list.append(m.group('context').strip())
            matched_list.append(m.group())
            text_list.append(text[start_index: m.start()])
            start_index = m.end()
        text_list.append(text[start_index:len(text)])
        full_text = ''
        for index in range(len(text_list)):
            full_text += matched_list[index]
            text_list[index] = self.handle_raw_code(text_list[index], context_list[index])
            text_list[index] = self.handle_inline_raw_code(text_list[index], context_list[index])
            text_list[index] = self.handle_raw_span_code(text_list[index], context_list[index])
            text_list[index] = self.handle_easy_span_code(text_list[index], context_list[index])
            full_text += text_list[index]
            # text_list[index] = self.handle_prose_label(text_list[index], context_list[index])
        return full_text, context_list

    def handle_context_post(self, text, equation_dict):
        """
        Process context and fill missing context based on the symbols generated by iheartla block
        (prose label, symbols in both iheartla and latex)
        """
        start_index = 0
        text_list = []
        context_list = ['']
        raw_context = ['']
        for m in self.CONTEXT_RE.finditer(text):
            # print("parsed context: {}".format(m.group('context')))
            cur_context = m.group('context').strip()
            context_list.append(cur_context)
            raw_context.append(m.group())
            text_list.append(text[start_index: m.start()])
            start_index = m.end()
        text_list.append(text[start_index:len(text)])
        for index in range(len(text_list)):
            sym_list = []
            cur_context = context_list[index]
            if cur_context in equation_dict:
                equation_data = equation_dict[cur_context]
                sym_list = equation_data.gen_sym_list()
                la_debug("cur_context:{}, sym_list:{}".format(cur_context, sym_list))
            # text_list[index] = self.handle_raw_code(text_list[index], context_list[index])
            # text_list[index] = self.handle_inline_raw_code(text_list[index], context_list[index])
            text_list[index] = self.handle_prose_label(text_list[index], cur_context)
            text_list[index] = self.handle_math(text_list[index], cur_context, sym_list)
            text_list[index] = self.handle_figure(text_list[index])
            if context_list[index] != '':
                text_list[index] = "<div>❤:{}</div>".format(context_list[index]) + text_list[index]
        return ''.join(text_list)

    def handle_figure(self, text):
        # Find all images
        for m in self.FIGURE_BLOCK_RE.finditer(text):
            figure = m.group('figure')
            # print("figure: {}".format(figure))
            for img in self.IMAGE_BLOCK_RE.finditer(figure):
                src = img.group('src')
                path, name = get_file_base(src)
                for c in self.FIGURE_CODE_RE.finditer(figure):
                    # print("img: {}, name:{}".format(path, name))
                    self.md.need_gen_figure = True
                    code = c.group('code')
                    save_to_file(code, "./extras/{}/{}.py".format(path, name))
                    self.md.figure_list.append(name)
                    # import os
                    # save_to_file(code, "{}/extras/resource/img/fig3.py".format(os.getcwd()))
                    text = text.replace(c.group(), '')
                    text = text.replace("<figure>", """<figure onclick="clickFigure(this, '{}')" name="{}">""".format(name, name))
                    break
                break
        return text

    def handle_iheartla_code(self, text):
        """
        Merge and compile code from iheartla block
        """
        file_dict = {}
        replace_dict = {}
        math_dict = {}
        # Find all inline blocks
        for m in self.INLINE_RE.finditer(text):
            # print("Inline block: {}".format(m.group()))
            module_name = m.group('module').strip()
            code = m.group('code')
            if '.' in module_name and self.BLANK_RE.fullmatch(code):
                code = read_from_file("{}/{}".format(self.md.path, module_name))
            if module_name and code:
                if module_name not in file_dict:
                    file_dict[module_name] = BlockData([m], [code], [m.group(0)], [True], [False], module_name)
                else:
                    file_dict[module_name].add(m, code, m.group(0), True, False)
        # Find all blocks
        for m in self.FENCED_BLOCK_RE.finditer(text):
            module_attr_list = m.group('module').strip().split(',')
            module_attr_list = [t.strip() for t in module_attr_list]
            module_name = module_attr_list[0].strip()
            numbered = True
            if 'unnumbered' in module_attr_list[1:]:
                numbered = False
            code = m.group('code')
            if '.' in module_name and self.BLANK_RE.fullmatch(code):
                code = read_from_file("{}/{}".format(self.md.path, module_name))
            if module_name and code:
                if module_name not in file_dict:
                    file_dict[module_name] = BlockData([m], [code], [m.group(0)], [False], [numbered], module_name)
                else:
                    file_dict[module_name].add(m, code, m.group(0), False, numbered)
        # Save to file
        if not WHEEL_MODE:
            for name, block_data in file_dict.items():
                source = '\n'.join(block_data.code_list)
                file_name = "{}/{}.ihla".format(self.md.path, name)
                save_to_file(source, file_name)
        # compile
        equation_dict = {}
        full_code_sequence = []
        for name, block_data in file_dict.items():
            code_list, equation_data = compile_la_content(block_data.get_content(),
                                                          parser_type=self.md.parser_type | ParserTypeEnum.MATHJAX | ParserTypeEnum.MACROMATHJAX,
                                                          func_name=name, path=self.md.path, struct=True,
                                                          get_json=True)
            equation_data.name = name
            equation_dict[name] = equation_data
            full_code_sequence.append(code_list[:-2])
            # Find all expr for each original iheartla block
            index_dict = {}
            expr_dict = code_list[-1].expr_dict
            expr_raw_dict = code_list[-2].expr_dict
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
                    content = expr_dict[raw_str]
                    raw_content = expr_raw_dict[raw_str]
                else:
                    # more than one expr in a single block
                    order_list = []
                    for raw_str in index_dict[cur_index]:
                        order_list.append(text.index(raw_str))
                    sorted_index = sorted(range(len(order_list)), key=lambda k: order_list[k])
                    content = ''
                    raw_content = ''
                    for cur in range(len(sorted_index)):
                        raw_str = index_dict[cur_index][sorted_index[cur]]
                        content += expr_dict[raw_str]
                        raw_content += expr_raw_dict[raw_str]
                original_block = block_data.block_list[cur_index]
                if block_data.inline_list[cur_index]:
                    raw_math = r"""$\begin{{align*}}{}\end{{align*}}$""".format(raw_content)
                    math_code = r"""${}{}{}$""".format(code_list[-1].pre_str, content, code_list[-1].post_str)
                    content = r"""<span class='equation' code_block="{}">{}</span>""".format(
                        block_data.module_name, math_code)
                else:
                    tag_info = ''
                    if not block_data.number_list[cur_index]:
                        tag_info = r"""\notag"""
                    raw_math = r"""$${}$$""".format(raw_content)
                    math_code = r"""$${}{}{}{}$$""".format(code_list[-1].pre_str, content, code_list[-1].post_str, tag_info)
                    content = r"""
        <div class='equation' code_block="{}" code="{}">
        {}</div>
        """.format(block_data.module_name, base64.urlsafe_b64encode("\n".join(original_block.split("\n")[1:-1]).encode("utf-8")).decode("utf-8"), math_code)
                content = self.md.htmlStash.store(content)
                text = text.replace(block_data.block_list[cur_index], content)
                replace_dict[block_data.block_list[cur_index]] = content
                math_dict[block_data.block_list[cur_index]] = raw_math
        self.save_code(full_code_sequence)
        return text, equation_dict, replace_dict, math_dict


    def handle_reference(self, text):
        res_list = self.REFERENCE_RE.findall(text)
        if len(res_list) == 0 and self.md.Meta.get("full_paper", True):
            text += "\n# REFERENCE\n"
        # ref_list = []
        # for m in self.REFERENCE_RE.finditer(text):
        #     ref_list.append(m)
        #     # print("m is :{}".format(m.group()))
        # if len(ref_list) > 0:
        #     m = ref_list[len(ref_list) - 1]
        #     remain_lines = text[m.end():].split('\n')
        #     ref_index = 0
        #     # print(remain_lines)
        #     for index in range(len(remain_lines)):
        #         if dedent(remain_lines[index]) != '':
        #             remain_lines[index] = "[ref{}]:{}".format(ref_index, remain_lines[index])
        #             ref_index += 1
        #     text = text[:m.end()] + '\n'.join(remain_lines)
        return text

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
        #
        text, context_list = self.handle_context_pre(text)
        text = self.handle_reference(text)
        text, equation_dict, replace_dict, math_dict = self.handle_iheartla_code(text)
        text, span_dict = self.handle_span_code(text)
        text, span_dict = self.handle_easy_span_context_math(text, equation_dict, span_dict)
        # convert span dict
        for context, new_dict in span_dict.items():
            for sym in new_dict.keys():
                for k in math_dict.keys():
                    if k in new_dict[sym]:
                        new_dict[sym] = new_dict[sym].replace(k, math_dict[k])
                        print("sym:{}, k:{}".format(sym, k))
        equation_dict = self.merge_desc(equation_dict, span_dict)
        self.process_metadata(equation_dict, context_list)
        text = self.handle_context_post(text, equation_dict)
        # for k, v in replace_dict.items():
        #     text = text.replace(k, v)
        #     print("k:{}, v:{}".format(k, v))
        return text.split("\n")

    def process_metadata(self, equation_dict, context_list):
        # Save sym data to file
        sym_dict = self.get_sym_dict(equation_dict.values())
        sym_json = self.get_sym_json(sym_dict)
        # save_to_file(sym_json, "{}/sym_data.json".format(self.md.path))
        self.md.json_sym = sym_json
        #
        json_list = []
        for name, equation_data in equation_dict.items():
            json_list.append('''{{"name":"{}", {} }}'''.format(name, equation_data.gen_json_content()))
        context_json_list = []
        for context in context_list:
            if context != '':
                context_json_list.append('"{}"'.format(context))
        json_content = '''{{"equations":[{}], "context":[{}] }}'''.format(','.join(json_list), ','.join(context_json_list))
        if json_content is not None:
            # save_to_file(json_content, "{}/data.json".format(self.md.path))
            self.md.json_data = json_content
        #

    def merge_desc(self, equation_dict, span_dict):
        # merge description from span tags
        for context, cur_dict in span_dict.items():
            if context in equation_dict:
                for sym, desc in cur_dict.items():
                    # print("sym:{}, desc:{}".format(sym, desc))
                    cur_sym = sym
                    if cur_sym not in equation_dict[context].sym_list:
                        # need to convert sym to the right symbol in symtable, e.g. \command -> `$\command$`
                        for cur_key in equation_dict[context].sym_list:
                            if cur_sym in cur_key:
                                cur_sym = cur_key
                                # print("converted, before:{}, after:{}".format(sym, cur_sym))
                    if cur_sym not in equation_dict[context].desc_dict:
                        equation_dict[context].desc_dict[cur_sym] = desc
                        # print("assign:{}, desc:{}".format(cur_sym, desc))
            # for k, v in equation_dict[context].desc_dict.items():
            #     print("k:{}, v:{}".format(k, v))
        return equation_dict

    def save_code(self, full_code_sequence):
        def get_frame_list(index):
            frame_list = []
            for code_list in full_code_sequence:
                frame_list.append(code_list[index])
            return frame_list
        cur_index = 0
        for cur_type in [ParserTypeEnum.NUMPY, ParserTypeEnum.EIGEN, ParserTypeEnum.LATEX, ParserTypeEnum.MATHJAX,
                         ParserTypeEnum.MATHML, ParserTypeEnum.MATLAB, ParserTypeEnum.MACROMATHJAX]:
            if self.md.parser_type & cur_type:
                self.save_with_type(get_frame_list(cur_index), cur_type)
                cur_index += 1

    def save_with_type(self, code_frame_list, parser_type):
        if parser_type == ParserTypeEnum.EIGEN:
            self.save_cpp(code_frame_list)
        elif parser_type == ParserTypeEnum.NUMPY:
            self.save_python(code_frame_list)
        elif parser_type == ParserTypeEnum.MATLAB:
            self.save_matlab(code_frame_list)

    def save_cpp(self, code_frame_list):
        lib_header = None
        lib_content = ''
        for code_frame in code_frame_list:
            if lib_header is None:
                lib_header = code_frame.include
            lib_content += code_frame.struct + '\n'
        if lib_header is not None:
            self.md.lib_cpp = "#pragma once\n" + lib_header + lib_content
            # save_to_file("#pragma once\n" + lib_header + lib_content, "{}/lib.h".format(self.md.path))

    def save_python(self, code_frame_list):
        lib_header = None
        lib_content = ''
        for code_frame in code_frame_list:
            if lib_header is None:
                lib_header = code_frame.include
            lib_content += code_frame.struct + '\n'
        if lib_header is not None:
            self.md.lib_py = lib_header + lib_content
            # save_to_file(lib_header + lib_content, "{}/lib.py".format(self.md.path))

    def save_matlab(self, code_frame_list):
        lib_content = ''
        for code_frame in code_frame_list:
            lib_content += code_frame.struct + '\n'
        if lib_content != '':
            self.md.lib_matlab = lib_content
            # save_to_file(lib_content, "{}/lib.m".format(self.md.path))



    def _escape(self, txt):
        """ basic html escaping """
        txt = txt.replace('&', '&amp;')
        txt = txt.replace('<', '&lt;')
        txt = txt.replace('>', '&gt;')
        txt = txt.replace('"', '&quot;')
        return txt

    def get_sym_dict(self, equation_list):
        sym_dict = {}
        node_dict = {}
        for equation in equation_list:
            # parameters
            for param in equation.parameters:
                sym_eq_data = SymEquationData(la_type=equation.symtable[param], desc=equation.desc_dict.get(param), module_name=equation.name, is_defined=False)
                if param not in sym_dict:
                    sym_data = SymData(param, sym_equation_list=[sym_eq_data])
                    node_dict[param] = SymNode(param)
                    sym_dict[param] = sym_data
                else:
                    sym_data = sym_dict[param]
                    sym_data.sym_equation_list.append(sym_eq_data)
            # new symbols
            for definition in equation.definition:
                sym_eq_data = SymEquationData(la_type=equation.symtable[definition], desc=equation.desc_dict.get(definition), module_name=equation.name, is_defined=True)
                if definition not in sym_dict:
                    sym_data = SymData(definition, sym_equation_list=[sym_eq_data])
                    node_dict[definition] = SymNode(definition)
                    sym_dict[definition] = sym_data
                else:
                    sym_data = sym_dict[definition]
                    sym_data.sym_equation_list.append(sym_eq_data)
            # local functions
            for func_name, func_params in equation.func_data_dict.items():
                sym_eq_data = SymEquationData(la_type=equation.symtable[func_name], desc=equation.desc_dict.get(func_name), module_name=equation.name, is_defined=True)
                if func_name not in sym_dict:
                    sym_data = SymData(func_name, sym_equation_list=[sym_eq_data])
                    node_dict[func_name] = SymNode(func_name)
                    sym_dict[func_name] = sym_data
                else:
                    sym_data = sym_dict[func_name]
                    sym_data.sym_equation_list.append(sym_eq_data)
                for local_param in func_params.params_data.parameters:
                    param_eq_data = SymEquationData(la_type=func_params.params_data.symtable[local_param],
                                                    desc=equation.desc_dict.get(local_param), module_name=equation.name,
                                                    is_defined=False)
                    if local_param not in sym_dict:
                        sym_data = SymData(local_param, sym_equation_list=[param_eq_data])
                        node_dict[local_param] = SymNode(local_param)
                        sym_dict[local_param] = sym_data
                    else:
                        # In a context, there may be multiple local parameters, check
                        sym_data = sym_dict[local_param]
                        existed = False
                        for cur_eq_data in sym_data.sym_equation_list:
                            if cur_eq_data.module_name == param_eq_data.module_name:
                                existed = True
                                # print("existed, name:{}, desc:{}".format(local_param, param_eq_data.desc))
                                if cur_eq_data.desc == '' and param_eq_data.desc != '':
                                    cur_eq_data.desc = param_eq_data.desc
                                    # print("Update param desc, name:{}, desc:{}".format(local_param, param_eq_data.desc))
                        if not existed:
                            sym_data.sym_equation_list.append(param_eq_data)
            for dep_data in equation.dependence:
                for dep_sym in dep_data.name_list:
                    sym_eq_data = SymEquationData(la_type=equation.symtable[dep_sym],
                                                  desc=equation.desc_dict.get(dep_sym), module_name=equation.name,
                                                  is_defined=True)
                    if dep_sym not in sym_dict:
                        sym_data = SymData(dep_sym, sym_equation_list=[sym_eq_data])
                        node_dict[dep_sym] = SymNode(dep_sym)
                        sym_dict[dep_sym] = sym_data
                    else:
                        sym_data = sym_dict[dep_sym]
                        sym_data.sym_equation_list.append(sym_eq_data)
            # expr list
            for sym_list in equation.expr_dict.values():
                # print("cur sym_list:{}".format(sym_list))
                # print("node_dict:{}".format(node_dict))
                for sym in sym_list:
                    if sym not in node_dict:
                        node_dict[sym] = SymNode(sym)
                        # Maybe local param in local func
                    node_dict[sym].add_neighbors(sym_list)
                # for k, v in node_dict.items():
                #     print("k:{}, v.name:{}, v.neighbors:{}".format(k, v.name, v.neighbors))
        # sec loop
        for equation in equation_list:
            # dependence
            for dependence in equation.dependence:
                for name in dependence.name_list:
                    sym_data = sym_dict[name]
                    for sym_equation in sym_data.sym_equation_list:
                        if sym_equation.module_name == dependence.module:
                            sym_equation.used_list.append(equation.name)
        #
        self.assign_colors(node_dict, sym_dict)
        return sym_dict

    def assign_colors(self, node_dict, sym_dict):
        """
        Implementation of Algorithm 3 from https://arxiv.org/pdf/2104.13755.pdf
        """
        # sort keys
        sym_list = list(node_dict.keys())
        def partition(arr, low, high):
            i = (low - 1)
            pivot = len(node_dict[arr[high]].neighbors)
            for j in range(low, high):
                if len(node_dict[arr[j]].neighbors) <= pivot:
                    i = i + 1
                    arr[i], arr[j] = arr[j], arr[i]
            arr[i + 1], arr[high] = arr[high], arr[i + 1]
            return (i + 1)
        def quickSort(arr, low, high):
            if len(arr) == 1:
                return arr
            if low < high:
                pi = partition(arr, low, high)
                quickSort(arr, low, pi - 1)
                quickSort(arr, pi + 1, high)
        quickSort(sym_list, 0, len(sym_list)-1)
        # assign colors
        pallette = []
        color_dict = {}
        def get_color_list():
            return ['red', 'YellowGreen', 'DeepSkyBlue', 'Gold', 'HotPink',
                    'Tomato', 'Orange', 'DarkRed', 'LightCoral', 'Khaki']
        all_colors = get_color_list()
        def get_new_color(all_colors):
            if len(all_colors) == 0:
                all_colors = get_color_list()
            return all_colors.pop(0)
        def get_neighbor_colors(sym):
            nei_colors = []
            for nei in node_dict[sym].neighbors:
                if nei in color_dict:
                    nei_colors.append(color_dict[nei])
            return nei_colors
        sym_list.reverse()
        for cur_sym in sym_list:
            cur_nei_colors = get_neighbor_colors(cur_sym)
            c = None
            for cur_color in pallette:
                if cur_color not in cur_nei_colors:
                    c = cur_color
                    break
            if c is None:
                c = get_new_color(all_colors)
                pallette.append(c)
            else:
                # shuffle c to the back of pallete
                pallette.remove(c)
                pallette.append(c)
            color_dict[cur_sym] = c
        for cur_sym, cur_color in color_dict.items():
            if cur_sym in sym_dict:
                sym_dict[cur_sym].color = cur_color

    def get_sym_json(self, sym_dict):
        sym_list = []
        for sym, sym_data in sym_dict.items():
            eq_data_list = []
            for sym_eq_data in sym_data.sym_equation_list:
                used_list_str = '[]'
                if len(sym_eq_data.used_list) > 0:
                    used_list_str = '"' + '","'.join(sym_eq_data.used_list) + '"'
                cur_desc = sym_eq_data.desc
                if sym_eq_data.desc:
                    cur_desc = cur_desc.replace('\\', '\\\\\\\\').replace('"', '\\\\"').replace("'", "\\\\'")
                if not cur_desc:
                    la_warning("missing description for sym {}".format(sym))
                # print(" sym_eq_data.desc:{}".format( sym_eq_data.desc))
                eq_data_list.append('''{{"desc":"{}", "type_info":{}, "def_module":"{}", "is_defined":{}, "used_equations":{}, "color":"{}"}}'''.format(
                    cur_desc, sym_eq_data.la_type.get_json_content(),
                    sym_eq_data.module_name, "true" if sym_eq_data.is_defined else "false", used_list_str,
                    sym_data.color))
            sym_list.append('''"{}":[{}]'''.format(sym.replace('\\', '\\\\\\\\').replace('"', '\\"').replace("'", "\\'"), ",".join(eq_data_list)))
        content = '''{{{}}}'''.format(','.join(sym_list))
        content = content.replace('`', '')
        return content


class SymNode(object):
    def __init__(self, name='', neighbors=None):
        if neighbors is None:
            neighbors = []
        self.name = name
        self.neighbors = neighbors

    def add_neighbors(self, neighbors=None):
        if neighbors is None:
            neighbors = []
        for nei in neighbors:
            if (nei != self.name) and (nei not in self.neighbors):
                self.neighbors.append(nei)


class SymEquationData(object):
    def __init__(self, la_type, desc=None, module_name='', is_defined=True, used_list=None):
        if used_list is None:
            used_list = []
        self.la_type = la_type            # type info
        self.desc = desc                  # comment for the symbol
        self.module_name = module_name    # the module that defines the symbol
        self.is_defined = is_defined      # whether defined or from parameters
        self.used_list = used_list        # the modules that import the symbol


class SymData(object):
    def __init__(self, sym_name, sym_equation_list=None, color=None):
        if sym_equation_list is None:
            sym_equation_list = []
        self.sym_name = sym_name
        self.sym_equation_list = sym_equation_list
        self.color = color


def makeExtension(**kwargs):  # pragma: no cover
    return IheartlaCodeExtension(**kwargs)
