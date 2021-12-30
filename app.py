import iheartla.la_tools.la_helper as la_helper
from iheartla.la_tools.la_helper import DEBUG_MODE, read_from_file, save_to_file
from iheartla.la_tools.la_logger import LaLogger
import logging
import argparse
import markdown
import os.path
from pathlib import Path
import shutil
import re
from textwrap import dedent


def handle_title(text, dict):
    content = ''
    if "title" in dict:
        title = dict["title"]
        content += "<div class='title'>{}</div>".format(title[0])
    if "author" in dict:
        author = dict["author"]
        content += "<div class='author'>{}</div>".format(author[0])
    content += text
    return content

def handle_abstract(text):
    # abstract = text[:text.index('\n<h1')]
    ABSTRACT_RE = re.compile(
        dedent(r'''\<p\>(?P<abstract>[^<>]*)\<\/p\>\n\<h1'''),
        re.MULTILINE | re.DOTALL | re.VERBOSE
    )
    # print("abstract:{}".format())
    res_abstract = ''
    for m in ABSTRACT_RE.finditer(text):
        abstract = m.group('abstract')
        res_abstract = "<p class='abstract'>{}</p>".format(abstract)
        text = text.replace("<p>{}</p>".format(abstract), '')
        # print("abstract:{}".format(m.group('abstract')))
        break
    return text, res_abstract

def handle_sections(text):
    map_dict = {}
    order_dict = {}
    def get_section_list(content, index=1, pre_str=''):
        tag = ''
        sec_list = []
        title_list = []
        SECTION_RE = re.compile(
            dedent(r'''\<h{}\ id\=\"(?P<id>[^<>]*)\"\>(?P<title>[^<>]*)\<\/h{}\>\n'''.format(index, index)),
            re.DOTALL | re.VERBOSE
        )
        end_list = []
        cur_order = 1
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
            for cur_index in range(len(sec_list)):
                tag += "<li><a href='#{}'>{}</a>".format(sec_list[cur_index], title_list[cur_index])
                cur_content = content[end_list[cur_index]:end_list[cur_index+1]]
                if pre_str == '':
                    new_pre = cur_index+1
                else:
                    new_pre = "{}.{}".format(pre_str, cur_index+1)
                cur_list, cur_tag = get_section_list(cur_content, index+1, new_pre)
                if len(cur_list) > 0:
                    map_dict[sec_list[cur_index]] = cur_list
                    tag += cur_tag
                tag += "</li>"
            tag += "</ul>"
        return sec_list, tag
    res_list, res_tag = get_section_list(text, 1, pre_str='')
    # print("res_list:{}, map_dict:{}".format(res_list, map_dict))
    # print("res_tag:{}".format(res_tag))
    text = "{}\n{}".format(res_tag, text)
    for k, v in order_dict.items():
        text = text.replace(k, v)
    return text

if __name__ == '__main__':
    LaLogger.getInstance().set_level(logging.DEBUG if DEBUG_MODE else logging.ERROR)
    arg_parser = argparse.ArgumentParser(description='I Heart LA paper compiler')
    arg_parser.add_argument('--regenerate-grammar', action='store_true', help='Regenerate grammar files')
    arg_parser.add_argument('--resource_dir', help='resource path')
    arg_parser.add_argument('--paper', nargs='*', help='paper text')
    args = arg_parser.parse_args()
    resource_dir = args.resource_dir if args.resource_dir else '.'
    # print("args.paper is {}, resource_dir is {}".format(args.paper, resource_dir))
    if args.regenerate_grammar:
        la_helper.DEBUG_PARSER = True
        import iheartla.la_tools.parser_manager
        iheartla.la_tools.parser_manager.recreate_local_parser_cache()
    else:
        for paper_file in args.paper:
            content = read_from_file(paper_file)
            md = markdown.Markdown(extensions=['markdown.extensions.iheartla_code', \
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
                                                          'markdown.extensions.wikilinks'], path=os.path.dirname(Path(paper_file)))
            body = md.convert(content)
            body, abstract = handle_abstract(body)
            body = handle_sections(body)
            body = abstract + body
            body = handle_title(body, md.Meta)
            equation_json = read_from_file("{}/data.json".format(os.path.dirname(Path(paper_file))))
            # equation_data = get_sym_data(json.loads(equation_json))
            sym_json = read_from_file("{}/sym_data.json".format(os.path.dirname(Path(paper_file))))
            dst = "{}/resource".format(os.path.dirname(Path(paper_file)))
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree("/Users/pressure/Downloads/linear_algebra/extras/resource", dst)
            script = r"""window.onload = parseAllSyms;
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
<img src="{resource_dir}/resource/glossary.png" id="glossary" alt="glossary" width="22" height="28"><br>
{body}
</body>
</html>""".format(mathjax=mathjax, equation_json=equation_json,  sym_json=sym_json, script=script, body=body, resource_dir=resource_dir)
            # numbering
            EQ_BLOCK_RE = re.compile(
                dedent(r'''(\$\$)(?P<code>.*?)(\$\$)'''),
                re.MULTILINE | re.DOTALL | re.VERBOSE
            )
            num = 1
            for m in EQ_BLOCK_RE.finditer(html):
                equation = m.group('code')
                if '\\notag' not in equation:
                    html = html.replace(equation, "{}\\tag{{{}}}\\label{{{}}}".format(equation, num, num))
                    num += 1
            base_name = os.path.basename(Path(paper_file))
            save_to_file(html, "{}/{}.html".format(os.path.dirname(Path(paper_file)), os.path.splitext(base_name)[0]))
            # print(html)
