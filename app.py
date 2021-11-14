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
            script = r"""function getSymTypeInfo(type_info){
  if(type_info.type == 'matrix'){
    content = "matrix, rows: " + type_info.rows + ", cols: " + type_info.cols;
  }
  else if(type_info.type == 'vector'){
    content = "vector, rows: " + type_info.rows;
  }
  else if(type_info.type == 'scalar'){
    content = "scalar";
  }
  else{
    content = "invalid type";
  }
  console.log("type_info.type: " + type_info.type);

  return content;
};
function getSymInfo(symbol, func_name){
  content = '';
  var found = false;
  for(var eq in iheartla_data.equations){
    if(iheartla_data.equations[eq].name == func_name){
      for(var param in iheartla_data.equations[eq].parameters){
        if (iheartla_data.equations[eq].parameters[param].sym == symbol){
          type_info = iheartla_data.equations[eq].parameters[param].type_info;
          found = true;
          content = symbol + " is a parameter as a " + getSymTypeInfo(type_info);
          break;
        }
      }
      if(found){
        break;
      }
      for(var param in iheartla_data.equations[eq].definition){
        if (iheartla_data.equations[eq].definition[param].sym == symbol){
          type_info = iheartla_data.equations[eq].definition[param].type_info;
          found = true;
          content = symbol + " is defined as a " + getSymTypeInfo(type_info);
          break;
        }
      }
      if(found){
        break;
      }
    }
  }
  return content;
}
function onClickSymbol(tag, symbol, func_name) {
if (typeof tag._tippy === 'undefined'){
    tippy(tag, {
        content: getSymInfo(symbol, func_name),
        placement: 'bottom',
        animation: 'fade',
        showOnCreate: true,
      });
  }
  console.log("clicked: " + symbol + " in " + func_name);
  // alert(getSymInfo(symbol, func_name));
  const matches = document.querySelectorAll("mjx-mi[sym='" + symbol + "']");
  for (var i = matches.length - 1; i >= 0; i--) {
     console.log(matches[i]);
     matches[i].setAttribute('class', 'highlight');
  }
  console.log(matches);
};
function onClickEq(tag, func_name, sym_list) { 
  content = "This equation has " + sym_list.length + " symbols\n";
  for(var sym in sym_list){
    content += getSymInfo(sym_list[sym], func_name) + '\n';
  }
  alert(content);
};"""
            style=r"""
<style>
body
{
  position:static !important;
  font-size: 12pt;
  padding-left:  10px;
  padding-right: 10px;
  width: 785px;
  min-height: none;
  min-height: 0%;
  border-radius: 8px;
  margin: auto;
}
.highlight {
 color: red; 
}
</style>
"""
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
</head>
{style}
<script>
const iheartla_data = JSON.parse('{json}');
{script}
</script>
<body>
{body}
</body>
</html>""".format(style=style, json=json, script=script, body=body)
            save_to_file(html, "/Users/pressure/Downloads/lib_paper/paper.html")
            print(html)
