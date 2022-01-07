from textwrap import dedent
from . import Extension
from ..preprocessors import Preprocessor
from ..postprocessors import Postprocessor
from .codehilite import CodeHilite, CodeHiliteExtension, parse_hl_lines
from .attr_list import get_attrs, AttrListExtension
from ..util import parseBoolValue
import regex as re
from iheartla.la_parser.parser import compile_la_content, ParserTypeEnum
from iheartla.la_tools.la_helper import DEBUG_MODE, read_from_file, save_to_file


class BlockData(Extension):
    def __init__(self, match_list=[], code_list=[], block_list=[], inline_list=[], module_name=''):
        self.module_name = module_name
        self.match_list = match_list
        self.code_list = code_list
        self.block_list = block_list
        self.inline_list = inline_list
        self.math_pre = ''
        self.math_list = []
        self.math_post = ''

    def add(self, match, code, block, inline=False):
        self.match_list.append(match)
        self.code_list.append(code)
        self.block_list.append(block)
        self.inline_list.append(inline)

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
            (\(\s*(?P<module>[^ \}\n]*)\s*\))                        # required {module} 
            \n                                                       # newline (end of opening fence)
            (?P<code>.*?)(?<=\n)                                     # the code block
            (?P=fence)[ ]*$                                          # closing fence
        '''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )
    # Match string: <span class="def:context:symbol">***</span>
    SPAN_BLOCK_RE = re.compile(
        dedent(r'''<span\ class=(?P<quote>"|')def:(?P<context>\b\w+\b)(:)(?P<symbol>[^:>'"]*)(?P=quote)>(?P<code>.*?)</span>'''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )
    # Match string: <span class="def:symbol">***</span>
    SPAN_SIMPLE_RE = re.compile(
        dedent(r'''<span\ class=(?P<quote>"|')def:(?P<symbol>[^:>'"]*)(?P=quote)>(?P<code>.*?)(</span>)'''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )
    # Match string: ❤️context: a=sin(θ)❤️
    INLINE_RE = re.compile(
        dedent(r'''❤(\s*)(?P<module>\b\w+\b)(\s*)(:)(?P<code>.*?)❤'''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )
    # Match string: # REFERENCES
    REFERENCE_RE = re.compile(
        dedent(r'''\#(\s*)REFERENCES'''),
        re.DOTALL | re.VERBOSE
    )
    # Match string: ❤ : context
    CONTEXT_RE = re.compile(
        dedent(r'''(?<=\n)(\s*)❤(\s*):(\s*)(?P<context>[^\n❤]*)\n'''),
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
    # Match string: ❤: a=sin(θ)❤
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
        escape_list = ['\\', '(', ')', '{', '}', '^', '+', '-', '.']
        for es in escape_list:
            sym = sym.replace(es, '\\' + es)
        return sym

    def handle_math(self, text, context, sym_list):
        for m in self.MATH_RE.finditer(text):
            content = m.group('code')
            # print("current equation:{}".format(m.group()))
            for sym in sym_list:
                PROSE_RE = re.compile(
                    dedent(r'''(?<!(    # negative begins
                    (\\(proselabel|prosedeflabel)({{([a-z\p{{Ll}}\p{{Lu}}\p{{Lo}}\p{{M}}\s]+)}})?{{([a-z\p{{Ll}}\p{{Lu}}\p{{Lo}}\p{{M}}_{{()\s]*)))
                    |
                    ([a-z\p{{Ll}}\p{{Lu}}\p{{Lo}}\p{{M}}\\])
                    ) # negative ends
                    ({})
                    (?![a-z\p{{Ll}}\p{{Lu}}\p{{Lo}}\p{{M}}\\])'''.format(self.escape_sym(sym))),
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

    def handle_prose_label(self, text, context):
        for m in self.PROSE_RE.finditer(text):
            # print("prose match: {}, def:{}, symbol:{}".format(m.group(), m.group('def'), m.group('symbol')))
            text = text.replace(m.group(), "{{\\prose{}label{{{}}}{{{{{}}}}}}}".format(m.group('def'), context, m.group('symbol')))
        return text

    def handle_raw_code(self, text, context):
        for m in self.RAW_CODE_BLOCK_RE.finditer(text):
            # print(m.group())
            text = text.replace(m.group(), "{}iheartla({})\n".format(m.group('fence'), context))
        return text

    def handle_inline_raw_code(self, text, context):
        for m in self.RAW_CODE_INLINE_RE.finditer(text):
            # print("inline_raw_code: {}".format(m.group()))
            if not self.INLINE_RE.fullmatch(m.group()):
                # print("new: {}".format("❤ {}:{}❤".format(context, m.group('code'))))
                text = text.replace(m.group(), "❤ {}:{}❤".format(context, m.group('code')))
        return text

    def handle_simple_span_code(self, text, context):
        for m in self.SPAN_SIMPLE_RE.finditer(text):
            # print("simple_span_code: {}".format(m.group()))
            # print("new: {}".format('<span class="def:{}:{}"> {} </span>'.format(context, m.group('symbol'), m.group('code'))))
            text = text.replace(m.group(), '<span class="def:{}:{}"> {} </span>'.format(context, m.group('symbol'), m.group('code')))
        return text

    def handle_span_code(self, text):
        for m in self.SPAN_BLOCK_RE.finditer(text):
            desc = m.group('code')
            sym_list = m.group('symbol').split(' ')
            for sym in sym_list:
                desc = desc.replace("${}$".format(sym), r"""$\prosedeflabel{{{}}}{{{{{}}}}}$""".format(m.group('context'), sym))
            text = text.replace(m.group(), "<span sym='{}' context='{}'> {} </span>".format(m.group('symbol'), m.group('context'), desc))
        return text

    def handle_context_pre(self, text):
        """
        Process context and fill missing context in iheartla code block
        """
        start_index = 0
        text_list = []
        context_list = ['']
        matched_list = ['']
        for m in self.CONTEXT_RE.finditer(text):
            # print("parsed context: {}".format(m.group('context')))
            context_list.append(m.group('context'))
            matched_list.append(m.group())
            text_list.append(text[start_index: m.start()])
            start_index = m.end()
        text_list.append(text[start_index:len(text)])
        full_text = ''
        for index in range(len(text_list)):
            full_text += matched_list[index]
            text_list[index] = self.handle_raw_code(text_list[index], context_list[index])
            text_list[index] = self.handle_inline_raw_code(text_list[index], context_list[index])
            full_text += text_list[index]
            # text_list[index] = self.handle_prose_label(text_list[index], context_list[index])
            # text_list[index] = self.handle_simple_span_code(text_list[index], context_list[index])
        return full_text

    def handle_context_post(self, text, equation_dict):
        """
        Process context and fill missing context based on the symbols generated by iheartla block
        """
        start_index = 0
        text_list = []
        context_list = ['']
        for m in self.CONTEXT_RE.finditer(text):
            # print("parsed context: {}".format(m.group('context')))
            cur_context = m.group('context')
            context_list.append(cur_context)
            text_list.append(text[start_index: m.start()])
            start_index = m.end()
        text_list.append(text[start_index:len(text)])
        for index in range(len(text_list)):
            sym_list = []
            cur_context = context_list[index]
            if cur_context in equation_dict:
                equation_data = equation_dict[cur_context]
                sym_list = equation_data.gen_sym_list()
                print("cur_context:{}, sym_list:{}".format(cur_context, sym_list))
            # text_list[index] = self.handle_raw_code(text_list[index], context_list[index])
            # text_list[index] = self.handle_inline_raw_code(text_list[index], context_list[index])
            text_list[index] = self.handle_prose_label(text_list[index], cur_context)
            text_list[index] = self.handle_simple_span_code(text_list[index], cur_context)
            text_list[index] = self.handle_math(text_list[index], cur_context, sym_list)
        return ''.join(text_list)

    def handle_iheartla_code(self, text):
        """
        Merge and compile code from iheartla block
        """
        file_dict = {}
        replace_dict = {}
        # Find all inline blocks
        for m in self.INLINE_RE.finditer(text):
            # print("Inline block: {}".format(m.group()))
            module_name = m.group('module')
            if module_name and m.group('code'):
                if module_name not in file_dict:
                    file_dict[module_name] = BlockData([m], [m.group('code')], [m.group(0)], [True], module_name)
                else:
                    file_dict[module_name].add(m, m.group('code'), m.group(0), True)
        # Find all blocks
        for m in self.FENCED_BLOCK_RE.finditer(text):
            module_name = m.group('module')
            if module_name and m.group('code'):
                if module_name not in file_dict:
                    file_dict[module_name] = BlockData([m], [m.group('code')], [m.group(0)], [False], module_name)
                else:
                    file_dict[module_name].add(m, m.group('code'), m.group(0), False)
        # Save to file
        for name, block_data in file_dict.items():
            source = '\n'.join(block_data.code_list)
            file_name = "{}/{}.ihla".format(self.md.path, name)
            save_to_file(source, file_name)
        # compile
        json_list = []
        equation_dict = {}
        full_code_sequence = []
        for name, block_data in file_dict.items():
            code_list, equation_data = compile_la_content(block_data.get_content(),
                                                          parser_type=self.md.parser_type | ParserTypeEnum.MACROMATHJAX,
                                                          func_name=name, path=self.md.path, struct=True,
                                                          get_json=True)
            equation_data.name = name
            json_list.append('''{{"name":"{}", {} }}'''.format(name, equation_data.gen_json_content()))
            equation_dict[name] = equation_data
            full_code_sequence.append(code_list[:-1])
            # Find all expr for each original iheartla block
            index_dict = {}
            expr_dict = code_list[-1].expr_dict
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
                else:
                    # more than one expr in a single block
                    order_list = []
                    for raw_str in index_dict[cur_index]:
                        order_list.append(text.index(raw_str))
                    sorted_index = sorted(range(len(order_list)), key=lambda k: order_list[k])
                    content = ''
                    for cur in range(len(sorted_index)):
                        raw_str = index_dict[cur_index][sorted_index[cur]]
                        content += expr_dict[raw_str]
                if block_data.inline_list[cur_index]:
                    content = r"""<span class='equation' code_block="{}">${}{}{}$</span>""".format(
                        block_data.module_name, code_list[1].pre_str, content, code_list[1].post_str)
                else:
                    content = r"""
        <div class='equation' code_block="{}">
        $${}{}{}$$</div>
        """.format(block_data.module_name, code_list[-1].pre_str, content, code_list[-1].post_str)
                content = self.md.htmlStash.store(content)
                text = text.replace(block_data.block_list[cur_index], content)
                replace_dict[block_data.block_list[cur_index]] = content
        json_content = '''{{"equations":[{}] }}'''.format(','.join(json_list))
        sym_dict = self.get_sym_dict(equation_dict.values())
        sym_json = self.get_sym_json(sym_dict)
        save_to_file(sym_json, "{}/sym_data.json".format(self.md.path))
        self.save_code(full_code_sequence)
        if json_content is not None:
            save_to_file(json_content, "{}/data.json".format(self.md.path))
        return text, equation_dict, replace_dict


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
        text = self.handle_context_pre(text)
        text = self.handle_span_code(text)
        text = self.handle_reference(text)
        text, equation_dict, replace_dict = self.handle_iheartla_code(text)
        text = self.handle_context_post(text, equation_dict)
        # for k, v in replace_dict.items():
        #     text = text.replace(k, v)
        return text.split("\n")

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
            save_to_file("#pragma once\n" + lib_header + lib_content, "{}/lib.h".format(self.md.path))

    def save_python(self, code_frame_list):
        lib_header = None
        lib_content = ''
        for code_frame in code_frame_list:
            if lib_header is None:
                lib_header = code_frame.include
            lib_content += code_frame.struct + '\n'
        if lib_header is not None:
            save_to_file(lib_header + lib_content, "{}/lib.py".format(self.md.path))

    def save_matlab(self, code_frame_list):
        lib_content = ''
        for code_frame in code_frame_list:
            lib_content += code_frame.struct + '\n'
        if lib_content != '':
            save_to_file(lib_content, "{}/lib.m".format(self.md.path))



    def _escape(self, txt):
        """ basic html escaping """
        txt = txt.replace('&', '&amp;')
        txt = txt.replace('<', '&lt;')
        txt = txt.replace('>', '&gt;')
        txt = txt.replace('"', '&quot;')
        return txt

    def get_sym_dict(self, equation_list):
        sym_dict = {}
        for equation in equation_list:
            # parameters
            for param in equation.parameters:
                sym_eq_data = SymEquationData(la_type=equation.symtable[param], desc=equation.desc_dict.get(param), module_name=equation.name, is_defined=False)
                if param not in sym_dict:
                    sym_data = SymData(param, sym_equation_list=[sym_eq_data])
                    sym_dict[param] = sym_data
                else:
                    sym_data = sym_dict[param]
                    sym_data.sym_equation_list.append(sym_eq_data)
            # new symbols
            for definition in equation.definition:
                sym_eq_data = SymEquationData(la_type=equation.symtable[definition], desc=equation.desc_dict.get(definition), module_name=equation.name, is_defined=True)
                if definition not in sym_dict:
                    sym_data = SymData(definition, sym_equation_list=[sym_eq_data])
                    sym_dict[definition] = sym_data
                else:
                    sym_data = sym_dict[definition]
                    sym_data.sym_equation_list.append(sym_eq_data)
            # local functions
            for func_name, func_params in equation.func_data_dict.items():
                sym_eq_data = SymEquationData(la_type=equation.symtable[func_name], desc=equation.desc_dict.get(func_name), module_name=equation.name, is_defined=True)
                if func_name not in sym_dict:
                    sym_data = SymData(func_name, sym_equation_list=[sym_eq_data])
                    sym_dict[func_name] = sym_data
                else:
                    sym_data = sym_dict[func_name]
                    sym_data.sym_equation_list.append(sym_eq_data)
        # sec loop
        for equation in equation_list:
            # dependence
            for dependence in equation.dependence:
                for name in dependence.name_list:
                    sym_data = sym_dict[name]
                    for sym_equation in sym_data.sym_equation_list:
                        if sym_equation.module_name == dependence.module:
                            sym_equation.used_list.append(equation.name)
        return sym_dict

    def get_sym_json(self, sym_dict):
        sym_list = []
        for sym, sym_data in sym_dict.items():
            eq_data_list = []
            for sym_eq_data in sym_data.sym_equation_list:
                used_list_str = '[]'
                if len(sym_eq_data.used_list) > 0:
                    used_list_str = '"' + '","'.join(sym_eq_data.used_list) + '"'
                eq_data_list.append('''{{"desc":"{}", "type_info":{}, "def_module":"{}", "is_defined":{}, "used_equations":{}}}'''.format(sym_eq_data.desc, sym_eq_data.la_type.get_json_content(),
                                                                             sym_eq_data.module_name, "true" if sym_eq_data.is_defined else "false", used_list_str ))
            sym_list.append('''"{}":[{}]'''.format(sym.replace('\\', '\\\\\\\\'), ",".join(eq_data_list)))
        content = '''{{{}}}'''.format(','.join(sym_list))
        content = content.replace('`', '')
        return content




class SymEquationData(object):
    def __init__(self, la_type, desc=None, module_name='', is_defined=True, used_list=[]):
        self.la_type = la_type            # type info
        self.desc = desc                  # comment for the symbol
        self.module_name = module_name    # the module that defines the symbol
        self.is_defined = is_defined      # whether defined or from parameters
        self.used_list = used_list        # the modules that import the symbol


class SymData(object):
    def __init__(self, sym_name, sym_equation_list=[]):
        self.sym_name = sym_name
        self.sym_equation_list = sym_equation_list


def makeExtension(**kwargs):  # pragma: no cover
    return IheartlaCodeExtension(**kwargs)
