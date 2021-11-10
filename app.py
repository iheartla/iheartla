import iheartla.la_tools.la_helper as la_helper
from iheartla.la_tools.la_helper import DEBUG_MODE, read_from_file, save_to_file
from iheartla.la_tools.la_logger import LaLogger
import logging
import argparse
import markdown
import os.path
from pathlib import Path


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
            json = read_from_file("{}/data.json".format(os.path.dirname(Path(paper_file))))
            html = r"""<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1"> 
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-BmbxuPwQa2lc/FVzBcNJ7UAyJxM6wuqIj61tLrc4wSX0szH/Ev+nYRRuWlolflfl" crossorigin="anonymous">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    <script type="text/javascript" id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <link rel="stylesheet" href="css/style.css">
</head>
<script>
const iheartla_data = JSON.parse('{}');
</script>
<body>
{}
</body>
</html>""".format(json, body)
            save_to_file(html, "/Users/pressure/Downloads/lib_paper/paper.html")
            print(html)
