function drawArrow( startElement, endElement, style='' ) {
    // This pseudocode creates an SVG element for each "arrow". As an alternative,
    // we could always have one SVG element present in the document
    // with absolute position 0,0 (or along the right side of the window)
    // whose width and height allows us to draw anywhere.
    // Then we would add and remove child nodes as needed.
    // You can use vanilla JS or svg.js or snap.js. Probably svg.js is a good fit.
    // Create a new SVG node
    // var svg = SVG().addTo('body').size('100%', '100%').move(-1010, -410);
    var svg = SVG().addTo('body').size('100%', '100%');
    var body = document.querySelector("body");
    var style = body.currentStyle || window.getComputedStyle(body);
    // Name it for selector queries so you can style it and also delete it
    svg.addClass("arrow")
    // Get the position of the start and end elements in absolute coordinates
    console.log(startElement);
    console.log(endElement);
    var bodyRect = body.getBoundingClientRect();
    var startRect = startElement.getBoundingClientRect();
    var startCenterX = startRect.x + startRect.width/2;
    var startCenterY = startRect.y + startRect.height/2;
    var endRect = endElement.getBoundingClientRect();
    var endCenterX = endRect.x + endRect.width/2;
    var endCenterY = endRect.y + endRect.height/2;
    var marginLeft = parseInt(style.marginLeft, 10)
    var bodyWidth = parseInt(style.width, 10)
    var marginTop = parseInt(style.marginTop, 10)
    console.log(style); 
    var arrowSize = 10;
    var offset = 10;
    var endPointX = endCenterX - bodyRect.x + marginLeft;
    var endPointY = endCenterY - bodyRect.y + marginTop;
    // var endPointX = bodyWidth+marginLeft-offset;
    // var endPointY = endCenterY - bodyRect.y + marginTop;
    // svg.path(`M${bodyWidth+marginLeft-offset} ${startCenterY - bodyRect.y + marginTop} 
    svg.path(`M${startCenterX - bodyRect.x + marginLeft} ${startCenterY - bodyRect.y + marginTop} 
      L ${bodyWidth+marginLeft} ${startCenterY - bodyRect.y + marginTop} 
      L ${bodyWidth+marginLeft} ${endCenterY - bodyRect.y + marginTop} 
      L ${endPointX} ${endPointY} 
      L ${endPointX+arrowSize} ${endPointY-arrowSize} 
      L ${endPointX} ${endPointY} 
      L ${endPointX+arrowSize} ${endPointY+arrowSize} 
      `).attr({fill: 'white', 'fill-opacity': 0, stroke: 'blue', 'stroke-width': 1})
}

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
  drawArrow(document.querySelector("#ff"), document.querySelector("#ss"));
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
          removeArrows();
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
function removeArrows(){
  var arrow = document.querySelector(".arrow");
  if (arrow) {
    document.querySelector("body").removeChild(arrow);
  }
}
function closeOtherTips(){
  removeArrows();
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