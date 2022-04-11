WHEEL_MODE = False
if WHEEL_MODE:
    from linear_algebra.iheartla.la_tools.la_helper import DEBUG_MODE, DEBUG_PARSER, read_from_file, save_to_file, get_file_base
    from linear_algebra.iheartla.la_tools.la_logger import LaLogger
    from linear_algebra.iheartla.la_parser.parser import ParserTypeEnum
    import linear_algebra.markdown
    from linear_algebra.markdown.core import *
    import linear_algebra.markdown.extensions
else:
    from iheartla.la_tools.la_helper import DEBUG_MODE, DEBUG_PARSER, read_from_file, save_to_file, get_file_base
    from iheartla.la_tools.la_logger import LaLogger
    from iheartla.la_parser.parser import ParserTypeEnum
    import markdown
    from markdown.core import *
    import markdown.extensions
import logging
import argparse
import os.path
from pathlib import Path
import shutil
import regex as re
from textwrap import dedent
import subprocess
import sys



# Match string: <figure>***</figure>
FIGURE_BLOCK_RE = re.compile(
    dedent(r'''<figure(?P<property>[^\n>]*)>(?P<figure>.*?)</figure>'''),
    re.MULTILINE | re.DOTALL | re.VERBOSE
)
# Match string: <img src='' ***>
IMAGE_BLOCK_RE = re.compile(
    dedent(r'''<img\ (?P<before>[^\n>]*)src=(?P<quote>"|')(?P<src>[^\n'">]*)(?P=quote)(?P<after>[^\n>]*)>'''),
    re.MULTILINE | re.DOTALL | re.VERBOSE
)
def handle_title(text, dict):
    content = ''
    if "title" in dict:
        title = dict["title"]
        content += "<div class='title'>{}</div>".format(title)
    if "author" in dict:
        authors = dict["author"]
        for author in authors:
            content += "<div class='author'>{}, {}</div>".format(author['name'], author['affiliation'])
    content += text
    return content

def handle_abstract(text, dict):
    # abstract = text[:text.index('\n<h1')]
    # ABSTRACT_RE = re.compile(
    #     dedent(r'''\<p\>(?P<abstract>[^<>]*)\<\/p\>\n\<h1'''),
    #     re.MULTILINE | re.DOTALL | re.VERBOSE
    # )
    # # print("abstract:{}".format())
    # res_abstract = ''
    # for m in ABSTRACT_RE.finditer(text):
    #     abstract = m.group('abstract')
    #     res_abstract = "<p class='abstract'>{}</p>".format(abstract)
    #     text = text.replace("<p>{}</p>".format(abstract), '')
    #     # print("abstract:{}".format(m.group('abstract')))
    #     break
    res_abstract = ''
    if "abstract" in dict:
        abstract = dict['abstract']
        res_abstract = "<p class='abstract'>{}</p>".format(abstract)
        text = text.replace("<p>{}</p>".format(abstract), '')
    return text, res_abstract

def handle_sections(text, dict):
    map_dict = {}
    order_dict = {}
    def get_section_list(content, index=1, pre_str='', cur_base_list=[]):
        tag = ''
        sec_list = []
        title_list = []
        SECTION_RE = re.compile(
            dedent(r'''\<h{}\ id\=\"(?P<id>[^<>]*)\"\>(?P<title>[^<>]*)\<\/h{}\>\n'''.format(index, index)),
            re.DOTALL | re.VERBOSE
        )
        end_list = []
        cur_base = 1
        if len(cur_base_list) > 0:
            cur_base = cur_base_list.pop(0)
        cur_order = cur_base
        for m in SECTION_RE.finditer(content):
            # print("id:{}".format(m.group('id')))
            id_str = m.group('id')
            sec_list.append(id_str)
            if pre_str == '':
                title = "{}&nbsp;{}".format(cur_order, m.group('title'))
            else:
                title = "{}.{}&nbsp;{}".format(pre_str, cur_order, m.group('title'))
            title_list.append(title)
            order_dict[m.group()] = "<h{} id='{}'>{}</h{}>".format(index, id_str, title, index)
            cur_order += 1
            end_list.append(m.end())
        end_list.append(len(content))
        if len(sec_list) > 0:
            tag += "<ul>"
            pre_cur_index = cur_base
            for cur_index in range(len(sec_list)):
                tag += "<li><a href='#{}'>{}</a>".format(sec_list[cur_index], title_list[cur_index])
                cur_content = content[end_list[cur_index]:end_list[cur_index+1]]
                if pre_str == '':
                    new_pre = pre_cur_index
                else:
                    new_pre = "{}.{}".format(pre_str, pre_cur_index)
                cur_list, cur_tag = get_section_list(cur_content, index+1, new_pre, cur_base_list)
                if len(cur_list) > 0:
                    map_dict[sec_list[cur_index]] = cur_list
                    tag += cur_tag
                tag += "</li>"
                pre_cur_index += 1
            tag += "</ul>"
        return sec_list, tag
    section_base_list = []
    if 'sectionBase' in dict:
        section_base_list = dict['sectionBase']
    res_list, res_tag = get_section_list(text, 1, pre_str='', cur_base_list=section_base_list)
    # print("res_list:{}, map_dict:{}".format(res_list, map_dict))
    # print("res_tag:{}".format(res_tag))
    text = "{}\n{}".format(res_tag, text)
    for k, v in order_dict.items():
        text = text.replace(k, v)
    return text

def handle_context_block(text):
    # Match string: ❤ : context
    CONTEXT_RE = re.compile(
        dedent(r'''<div>❤(\s*):(?P<context>[^\n❤]*)<\/div>'''),
        re.MULTILINE | re.VERBOSE
    )
    start_index = 0
    text_list = []
    context_list = ['']
    matched_list = ['']
    context_dict = {}
    for m in CONTEXT_RE.finditer(text):
        cur_context = m.group('context').strip()
        # print("parsed context: {}".format(m.group('context')))
        context_list.append(cur_context)
        matched_list.append(m.group())
        text_list.append(text[start_index: m.start()])
        start_index = m.end()
        if cur_context not in context_dict:
            context_dict[cur_context] = 0
    text_list.append(text[start_index:len(text)])
    for index in range(len(text_list)):
        cur_context = context_list[index]
        if cur_context != '':
            text_list[index] = "<div class='context' id='context-{}-{}' context='{}'>{}</div>".format(cur_context.replace(" ", ""), context_dict[cur_context], cur_context, text_list[index])
            context_dict[cur_context] += 1
    return ''.join(text_list)


def handle_figure(text):
    start_index = 0
    text_list = []
    for m in FIGURE_BLOCK_RE.finditer(text):
        figure = m.group('figure')
        # print("figure: {}".format(figure))
        new_figure = None
        for img in IMAGE_BLOCK_RE.finditer(figure):
            src = img.group('src')
            path, name = get_file_base(src)
            print("img: {}, name:{}".format(path, name))
            source = "./extras/{}/{}.py".format(path, name)
            ret = subprocess.run(["python", source])
            if ret.returncode == 0:
                # figure generated
                new_figure = figure[:img.start()] + """<iframe id="{}" scrolling="no" style="border:none;" seamless="seamless" src="{}/{}.html" height="525" width="100%"></iframe>""".format(name, path, name) + figure[img.end():]
            else:
                print("failed, {}".format(source))
            break
        text_list.append(text[start_index: m.start()])
        start_index = m.end()
        if new_figure:
            text_list.append(new_figure)
        else:
            text_list.append(figure)
    if len(text_list) > 0:
        return ''.join(text_list)
    return text


def save_output_code(md, path):
    # if not WHEEL_MODE:
    if True:
        if md.lib_py != '':
            save_to_file(md.lib_py, "{}/lib.py".format(path))
        if md.lib_cpp != '':
            save_to_file(md.lib_cpp, "{}/lib.h".format(path))
        if md.lib_matlab != '':
            save_to_file(md.lib_matlab, "{}/lib.m".format(path))


def process_input(content, input_dir='.', resource_dir='.', file_name='result', parser_type=ParserTypeEnum.NUMPY | ParserTypeEnum.EIGEN | ParserTypeEnum.MATLAB):
    """
    Given the source string, generate the html result
    :param content: Markdown source
    :param input_dir: Path to Markdown file
    :param resource_dir: Path to resource
    :param file_name: Markdown file without extension
    :param parser_type: Output code
    :return: html content
    """
    if True:
    # try:
        extension_list = ['markdown.extensions.mdx_bib', \
                           'markdown.extensions.iheartla_code', \
                           'markdown.extensions.mdx_math', \
                           'markdown.extensions.attr_list', \
                           'markdown.extensions.fenced_code', \
                           'markdown.extensions.abbr', \
                           'markdown.extensions.def_list', \
                           'markdown.extensions.footnotes', \
                           'markdown.extensions.md_in_html', \
                           'markdown.extensions.tables', \
                           'markdown.extensions.admonition', \
                           # 'markdown.extensions.codehilite', \
                           'markdown.extensions.legacy_attrs', \
                           'markdown.extensions.legacy_em', \
                           'markdown.extensions.meta', \
                           'markdown.extensions.nl2br', \
                           'markdown.extensions.sane_lists', \
                           'markdown.extensions.smarty', \
                           'markdown.extensions.toc', \
                           'markdown.extensions.wikilinks']
        if WHEEL_MODE:
            extension_list = ["linear_algebra.{}".format(ex) for ex in extension_list]
        md = Markdown(extensions=extension_list,
                               path=input_dir,
                               parser_type=parser_type,
                               bibtex_file='{}/{}.bib'.format(input_dir, file_name[0]))
        body = md.convert(content)
        body, abstract = handle_abstract(body, md.Meta)
        body = handle_sections(body, md.Meta)
        body = abstract + body
        body = handle_title(body, md.Meta)
        body = handle_context_block(body)
        # save_output_code(md, input_dir)
        save_output_code(md, './extras/resource/img')
        body = handle_figure(body)
        equation_json = md.json_data
        # equation_data = get_sym_data(json.loads(equation_json))
        sym_json = md.json_sym
        dst = "{}/resource".format(input_dir)
        # if os.path.exists(dst):
        #     shutil.rmtree(dst)
        # shutil.copytree("/Users/pressure/Downloads/linear_algebra/extras/resource", dst)
        script = r"""window.onload = onLoad;
        function reportWindowSize() {
          var arrows = document.querySelectorAll(".arrow");
          if (arrows) {
            for (var i = arrows.length - 1; i >= 0; i--) {
              var arrow = arrows[i];
              var body = document.querySelector("body");
              var style = window.getComputedStyle(body);
              var curOffset = parseInt(style.marginLeft, 10)
              var oldOffset = arrow.getAttribute('offset');
              arrow.setAttribute('offset', curOffset);
              // console.log(`oldOffset:${oldOffset}, curOffset:${curOffset}`);
              var arrowStyle = window.getComputedStyle(arrow); 
              var arrowOffset = parseInt(document.querySelector(".arrow").style.marginLeft, 10)
              arrow.style.marginLeft = `${arrowOffset+curOffset-oldOffset}px`;
              var newWidth = parseInt(style.width, 10) + parseInt(style.marginLeft, 10) + parseInt(style.marginRight, 10);
              arrow.style.width = `${newWidth}px`;
              arrow.style.height = style.height; 
              // console.log(`arrow.style.width:${arrow.style.width}, arrow.style.height:${arrow.style.height}`)
            }
          }
          adjsutGlossaryBtn();
        }
        window.onresize = reportWindowSize;
        document.addEventListener("click", function(evt){
            resetState();
        });
        """
        mathjax = r'''<script>
        MathJax = {
          loader: {
            load: ["[attrLabel]/attr-label.js"],
            paths: { attrLabel: "''' + resource_dir + '''/resource" },
          },
          tex: { packages: { "[+]": ["attr-label"] },
           inlineMath: [['$', '$']]
           },
           options: {
            enableAssistiveMml: false
          },
        };
            </script>'''
        html = r"""<html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1"> 
            {mathjax}
            <script type="text/javascript" id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
            <script src="https://unpkg.com/@popperjs/core@2"></script>
            <script src="https://unpkg.com/tippy.js@6"></script>
            <link rel="stylesheet" href="https://unpkg.com/tippy.js@6/dist/svg-arrow.css"/>
            <link rel="stylesheet" href="https://unpkg.com/tippy.js@6/dist/border.css" />
            <script src="{resource_dir}/resource/d3.min.js"></script>
            <script src="{resource_dir}/resource/svg.min.js"></script>
            <script type="text/javascript" src='{resource_dir}/resource/paper.js'></script>
            <link rel="stylesheet" href="{resource_dir}/resource/paper.css">
        </head>
        <script>
        const iheartla_data = JSON.parse('{equation_json}');
        const sym_data = JSON.parse('{sym_json}');
        {script}
        </script>
        <body>
        <div id="glossary" class="glossary"></div><br>
        {body}
        </body>
        </html>""".format(mathjax=mathjax, equation_json=equation_json, sym_json=sym_json, script=script, body=body,
                          resource_dir=resource_dir)
        # numbering
        EQ_BLOCK_RE = re.compile(
            dedent(r'''(?<!\\)((?<!\$)\${2}(?!\$))((?P<code>.*?))(?<!\\)(?<!\$)\1(?!\$)'''),
            re.MULTILINE | re.DOTALL | re.VERBOSE
        )
        num = md.Meta.get('eqBase', 1)
        for m in EQ_BLOCK_RE.finditer(html):
            equation = m.group('code')
            if '\\notag' not in equation:
                html = html.replace(m.group(), "$${}\\tag{{{}}}\\label{{{}}}$$".format(equation, num, num))
                num += 1
        ret = [html, md.lib_py, md.lib_cpp, md.lib_matlab]
    # except:
    #     ret = str(sys.exc_info()[0])
    # finally:
        return ret


if __name__ == '__main__':
    # LaLogger.getInstance().set_level(logging.DEBUG if DEBUG_MODE else logging.ERROR)
    LaLogger.getInstance().set_level(logging.ERROR)
    arg_parser = argparse.ArgumentParser(description='I Heart LA paper compiler')
    arg_parser.add_argument('--regenerate-grammar', action='store_true', help='Regenerate grammar files')
    arg_parser.add_argument('--resource_dir', help='resource path')
    arg_parser.add_argument('-o', '--output', help='The output language', choices=['numpy', 'eigen', 'latex','matlab'])
    arg_parser.add_argument('--paper', nargs='*', help='paper text')
    args = arg_parser.parse_args()
    resource_dir = args.resource_dir if args.resource_dir else '.'
    # print("args.paper is {}, resource_dir is {}".format(args.paper, resource_dir))
    if args.regenerate_grammar:
        DEBUG_PARSER = True
        import iheartla.la_tools.parser_manager
        iheartla.la_tools.parser_manager.recreate_local_parser_cache()
    else:
        parser_type = ParserTypeEnum.DEFAULT
        out_dict = {"numpy": ParserTypeEnum.NUMPY, "eigen": ParserTypeEnum.EIGEN, "latex": ParserTypeEnum.LATEX,
                    "mathjax": ParserTypeEnum.MATHJAX, "matlab": ParserTypeEnum.MATLAB}
        if args.output:
            # when output args are present _only_ output those
            parser_type = ParserTypeEnum.INVALID
            out_list = args.output.split(",")
            for out in out_list:
                assert out in out_dict, "Parameters after -o or --output can only be numpy, eigen, latex, or matlab"
                parser_type = parser_type | out_dict[out]
        else:
            parser_type = ParserTypeEnum.NUMPY | ParserTypeEnum.EIGEN | ParserTypeEnum.MATLAB
        for paper_file in args.paper:
            content = read_from_file(paper_file)
            base_name = os.path.basename(Path(paper_file))
            ret = process_input(content, os.path.dirname(Path(paper_file)), resource_dir, os.path.splitext(base_name)[0], parser_type)
            html = ret[0]
            save_to_file(html, "{}/{}.html".format(os.path.dirname(Path(paper_file)), os.path.splitext(base_name)[0]))
            # print(html)
