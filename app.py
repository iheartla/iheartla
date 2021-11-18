import iheartla.la_tools.la_helper as la_helper
from iheartla.la_tools.la_helper import DEBUG_MODE, read_from_file, save_to_file
from iheartla.la_tools.la_logger import LaLogger
import logging
import argparse
import markdown
import os.path
from pathlib import Path
import shutil


if __name__ == '__main__':
    LaLogger.getInstance().set_level(logging.DEBUG if DEBUG_MODE else logging.ERROR)
    arg_parser = argparse.ArgumentParser(description='I Heart LA paper compiler')
    arg_parser.add_argument('--regenerate-grammar', action='store_true', help='Regenerate grammar files')
    arg_parser.add_argument('--paper', nargs='*', help='paper text')
    args = arg_parser.parse_args()
    print(args.paper)
    if args.regenerate_grammar:
        la_helper.DEBUG_PARSER = True
        import iheartla.la_tools.parser_manager
        iheartla.la_tools.parser_manager.recreate_local_parser_cache()
    else:
        args.paper = ['/Users/pressure/Downloads/lib_paper/test.md']
        for paper_file in args.paper:
            content = read_from_file(paper_file)
            body = markdown.markdown(content, extensions=['markdown.extensions.iheartla_code', \
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
            equation_json = read_from_file("{}/data.json".format(os.path.dirname(Path(paper_file))))
            # equation_data = get_sym_data(json.loads(equation_json))
            sym_json = read_from_file("{}/sym_data.json".format(os.path.dirname(Path(paper_file))))
            dst = "{}/resource".format(os.path.dirname(Path(paper_file)))
            # if os.path.exists(dst):
            #     shutil.rmtree(dst)
            # shutil.copytree("./extras/resource", dst)
            script = r"""window.onload = parseAllSyms;
function reportWindowSize() {
  var arrow = document.querySelector(".arrow");
  if (arrow) {
    var body = document.querySelector("body");
    var style = body.currentStyle || window.getComputedStyle(body);
    var curOffset = parseInt(style.marginLeft, 10)
    var oldOffset = arrow.getAttribute('offset');
    arrow.setAttribute('offset', curOffset);
    // console.log(`oldOffset:${oldOffset}, curOffset:${curOffset}`);
    var arrowStyle = window.getComputedStyle(arrow); 
    var arrowOffset = parseInt(document.querySelector(".arrow").style.marginLeft, 10)
    arrow.style.marginLeft = `${arrowOffset+curOffset-oldOffset}px`;
    arrow.style.width = body.style.width;
    arrow.style.height = body.style.height; 
  }
}
window.onresize = reportWindowSize;"""
            html = r"""<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1"> 
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-BmbxuPwQa2lc/FVzBcNJ7UAyJxM6wuqIj61tLrc4wSX0szH/Ev+nYRRuWlolflfl" crossorigin="anonymous">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    <script type="text/javascript" id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <script src="https://unpkg.com/@popperjs/core@2"></script>
    <script src="https://unpkg.com/tippy.js@6"></script>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script type="text/javascript" src='./resource/paper.js'></script>
    <link rel="stylesheet" href="./resource/paper.css">
</head>
<script>
const iheartla_data = JSON.parse('{equation_json}');
const sym_data = JSON.parse('{sym_json}');
{script}
</script>
<body>
<img src="./resource/glossary.png" id="glossary" alt="glossary" width="22" height="28">
{body}
</body>
</html>""".format(equation_json=equation_json,  sym_json=sym_json, script=script, body=body)
            save_to_file(html, "/Users/pressure/Downloads/lib_paper/paper.html")
            print(html)
