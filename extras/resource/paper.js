function getSymTypeInfo(type_info){
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
      content = `<pa onclick="parseSym('${k}');"><pa class="clickable_sym">${k}</pa>: ${diff_length} different types</pa><br>`;
    }
    else{
      if (diff_list[0].is_defined){
        content = `<pa onclick="parseSym('${k}');"><pa class="clickable_sym">${k}</pa>: defined </pa><br>`;
      }
      else{
        content = `<pa onclick="parseSym('${k}');"><pa class="clickable_sym">${k}</pa>: ${diff_list[0].desc}</pa><br>`;
      }
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
};