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
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree("./extras/resource", dst)
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
function parseSym(symbol){
  data = sym_data[symbol];
  console.log(`You clicked ${symbol}`);
}
function parseAllSyms(){
  keys = [];
  for (var k in sym_data) { 
    keys.push(k);
  }
  keys.sort();
  info = '<p>Glossary of symbols</p>'
  for (i = 0; i < keys.length; i++) {
    k = keys[i];
    diff_list = sym_data[k];
    diff_length = diff_list.length;
    if (diff_length > 1) {
      content = `<pa onclick="parseSym('${k}');"><pa class="clickable_sym">${k}</pa>: ${diff_length} different definitions</pa><br>`;
    }
    else{
      content = `<pa onclick="parseSym('${k}');"><pa class="clickable_sym">${k}</pa>: ${diff_list[0].desc}</pa><br>`;
    }
    console.log(content);
    info += content;
  }
  console.log(document.querySelector("#glossary"));
  tippy(document.querySelector("#glossary"), {
        content: info,
        placement: 'bottom',
        animation: 'fade',
        trigger: 'click', 
        allowHTML: true,
        interactive: true,
      }); 
}
window.onload = parseAllSyms;
function getSymInfo(symbol, func_name){
  content = '';
  var found = false;
  for(var eq in iheartla_data.equations){
    if(iheartla_data.equations[eq].name == func_name){
      for(var param in iheartla_data.equations[eq].parameters){
        if (iheartla_data.equations[eq].parameters[param].sym == symbol){
          type_info = iheartla_data.equations[eq].parameters[param].type_info;
          found = true;

          if(iheartla_data.equations[eq].parameters[param].desc){
            content = symbol + " is " + iheartla_data.equations[eq].parameters[param].desc + ", the type is " + getSymTypeInfo(type_info);
          }
          else{
            content = symbol + " is a parameter as a " + getSymTypeInfo(type_info);
          }
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
  closeOtherTips();
  if (typeof tag._tippy === 'undefined'){
    tippy(tag, {
        content: getSymInfo(symbol, func_name),
        placement: 'bottom',
        animation: 'fade',
        trigger: 'click', 
        showOnCreate: true,
        onShow(instance) { 
          tag.setAttribute('class', 'highlight');
          console.log('onShow');
          return true;  
        },
        onHide(instance) {
          tag.removeAttribute('class');
          console.log('onHide');
          return true;  
        },
      });
  }
  console.log("clicked: " + symbol + " in " + func_name); 
};
function onClickEq(tag, func_name, sym_list) { 
  closeOtherTips();
  content = "This equation has " + sym_list.length + " symbols\n";
  for(var sym in sym_list){
    content += getSymInfo(sym_list[sym], func_name) + '\n';
  }
  if (typeof tag._tippy === 'undefined'){
    tippy(tag, {
        content: content,
        placement: 'bottom',
        animation: 'fade',
        trigger: 'click', 
        showOnCreate: true,
        onShow(instance) { 
          tag.setAttribute('class', 'highlight');
          console.log('onShow');
          return true;  
        },
        onHide(instance) {
          tag.removeAttribute('class');
          console.log('onHide');
          return true;  
        },
      });
  }
};
function closeOtherTips(){
  const matches = document.querySelectorAll(".highlight");
  for (var i = matches.length - 1; i >= 0; i--) {
    matches[i].removeAttribute('class');
    if (typeof matches[i]._tippy !== 'undefined'){
      matches[i]._tippy.hide();
    }
  }
};
function onClickGlossary(){
  alert('You clicked the glossary');
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
.normal {
 color: black; 
}
.clickable_sym{
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
const iheartla_data = JSON.parse('{equation_json}');
const sym_data = JSON.parse('{sym_json}');
{script}
</script>
<body>
<img src="./resource/glossary.png" id="glossary" alt="glossary" width="22" height="28">
{body}
</body>
</html>""".format(style=style, equation_json=equation_json,  sym_json=sym_json, script=script, body=body)
            save_to_file(html, "/Users/pressure/Downloads/lib_paper/paper.html")
            print(html)
