function drawArrow( startElement, endElement, style='' , color='blue', 
  offsetVerticalX=0, offsetStartY=0, offsetEndY=0, offsetEndX=20) {
    // This pseudocode creates an SVG element for each "arrow". As an alternative,
    // we could always have one SVG element present in the document
    // with absolute position 0,0 (or along the right side of the window)
    // whose width and height allows us to draw anywhere.
    // Then we would add and remove child nodes as needed.
    // You can use vanilla JS or svg.js or snap.js. Probably svg.js is a good fit.
    // Create a new SVG node
    // var svg = SVG().addTo('body').size('100%', '100%').move(-1010, -410);
    // console.log(`start is ${startElement}, end is ${endElement}`)
    var svg = SVG().addTo('body').size('100%', '100%').attr('left', '0px');
    // console.log(`svg is ${svg}`);
    var body = document.querySelector("body");
    var style = body.currentStyle || window.getComputedStyle(body);
    // Name it for selector queries so you can style it and also delete it
    svg.addClass("arrow")
    // Get the position of the start and end elements in absolute coordinates
    // console.log(startElement);
    // console.log(endElement);
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
    // console.log(style); 
    var arrowSize = 5;
    // var offsetEndX = 20;
    // var endPointX = endCenterX - bodyRect.x + marginLeft;
    // var endPointY = endCenterY - bodyRect.y + marginTop;
    var endPointX = bodyWidth+marginLeft-offsetEndX;
    var endPointY = endCenterY - bodyRect.y + marginTop;
    // console.log(`marginTop is ${marginTop}`);
    // svg.path(`M${startCenterX - bodyRect.x + marginLeft} ${startCenterY - bodyRect.y + marginTop} 
    svg.path(`M${bodyWidth+marginLeft-offsetEndX} ${startCenterY - bodyRect.y + marginTop+offsetStartY} 
      L ${bodyWidth+marginLeft+offsetVerticalX} ${startCenterY - bodyRect.y + marginTop+offsetStartY} 
      L ${bodyWidth+marginLeft+offsetVerticalX} ${endCenterY - bodyRect.y + marginTop+offsetEndY} 
      L ${endPointX} ${endPointY+offsetEndY} 
      L ${endPointX+arrowSize} ${endPointY-arrowSize+offsetEndY} 
      L ${endPointX} ${endPointY+offsetEndY} 
      L ${endPointX+arrowSize} ${endPointY+arrowSize+offsetEndY} 
      `).attr({fill: 'white', 'fill-opacity': 0, stroke: color, 'stroke-width': 1})
    svg.attr('offset', parseInt(style.marginLeft, 10))
    document.querySelector(".arrow").style.marginLeft = "0px"
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
  // console.log("type_info.type: " + type_info.type);

  return content;
};
function getGlossarySymInfo(symbol){
  content = ''
  data_list = sym_data[symbol];
  for (var i = 0; i < data_list.length; i++) {
      var data = data_list[i];
      content += `${symbol} is defined in module ${data.def_module}, ` 
      content += `type is : ${getSymTypeInfo(data.type_info)}`
      if (data.used_equations.length > 0) {
        for (var i = 0; i < data_list.length; i++) {

        }
      }
  }
  return `<pa>${content}</pa>`;
}
function parseSym(tag, symbol){
  data = sym_data[symbol];
  console.log(`You clicked ${symbol}`);
  if (typeof tag._tippy === 'undefined'){
    tippy(tag, {
        content: getGlossarySymInfo(symbol),
        placement: 'right',
        animation: 'fade',
        trigger: 'click', 
        // theme: 'material',
        showOnCreate: true,
        allowHTML: true,
        onShow(instance) {
          return true;  
        },
        onHide(instance) { 
          return true;  
        },
      });
  }
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
      content = `<pa onclick="parseSym(this, '${k}');"><pa class="clickable_sym">${k}</pa>: ${diff_length} different types</pa><br>`;
    }
    else{
      if (diff_list[0].is_defined){
        content = `<pa onclick="parseSym(this, '${k}');"><pa class="clickable_sym">${k}</pa>: defined </pa><br>`;
      }
      else{
        content = `<pa onclick="parseSym(this, '${k}');"><pa class="clickable_sym">${k}</pa>: ${diff_list[0].desc}</pa><br>`;
      }
    }
    // console.log(content);
    info += content;
  }
  // console.log(document.querySelector("#glossary"));
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
function showSymArrow(tag, symbol, func_name, color='blue', 
  offsetVerticalX=0, offsetStartY=0, offsetEndY=0, offsetEndX=20){
  const matches = document.querySelectorAll("mjx-mi[sym='" + symbol + "']");
    for (var i = matches.length - 1; i >= 0; i--) {
      matches[i].setAttribute('class', `highlight_${color}`);
      if (matches[i] !== tag ) {
        drawArrow(tag, matches[i],'',color,offsetVerticalX, offsetStartY, offsetEndY, offsetEndX);
      }
    }
}
function onClickSymbol(tag, symbol, func_name) {
  resetState();
  closeOtherTips();
  showSymArrow(tag, symbol, func_name, color='red');
    // d3.selectAll("mjx-mi[sym='" + symbol + "']").style("class", "highlight");
  if (typeof tag._tippy === 'undefined'){
    tippy(tag, {
        content: getSymInfo(symbol, func_name),
        placement: 'bottom',
        animation: 'fade',
        trigger: 'click', 
        theme: 'light',
        showOnCreate: true,
        onShow(instance) {
          // closeOtherTips();
          return true;  
        },
        onHide(instance) {
          resetState();
          return true;  
        },
      });
  }
  // console.log("clicked: " + symbol + " in " + func_name); 
};
function onClickEq(tag, func_name, sym_list) { 
  closeOtherTips();
  resetState();
  var colors =['red', 'green', 'blue', 'yellow']
  content = "This equation has " + sym_list.length + " symbols\n";
  var offsetVerticalX = 0;
  var offsetStartY = 0;
  var offsetEndY = 0;
  var offsetEndX = 30;
  for(var sym in sym_list){
    content += getSymInfo(sym_list[sym], func_name) + '\n';
    var symTag = tag.querySelector("mjx-mi[sym='" + sym_list[sym] + "']");
    const matches = document.querySelectorAll("mjx-mi[sym='" + sym_list[sym] + "']");
    // console.log(`tag is ${tag}, symTag is ${symTag}, matches is ${matches}, sym is ${sym_list[sym]}`);
    offsetVerticalX += 5;
    offsetStartY += 2;
    offsetEndY += 2;
    offsetEndX -= 5;
    showSymArrow(symTag, sym_list[sym], func_name, colors[sym], offsetVerticalX, offsetStartY, offsetEndY, offsetEndX);
  }
  if (typeof tag._tippy === 'undefined'){
    tippy(tag, {
        content: content,
        placement: 'bottom',
        animation: 'fade',
        trigger: 'click', 
        showOnCreate: true,
        onShow(instance) { 
          tag.setAttribute('class', 'highlight_fake');
          // console.log('onShow');
          return true;  
        },
        onHide(instance) {
          resetState();
          return true;  
        },
      });
  }
};
function resetState(){
  removeArrows();
  removeSymHighlight();
}
function removeArrows(){
  var matches = document.querySelectorAll(".arrow");
  if (matches) {
    for (var i = matches.length - 1; i >= 0; i--) {
      document.querySelector("body").removeChild(matches[i]);
    }
  }
}
function removeSymHighlight(){
  const matches = document.querySelectorAll("[class^=highlight]");
  for (var i = matches.length - 1; i >= 0; i--) {
    matches[i].removeAttribute('class');
  }
}
function closeOtherTips(){
  const matches = document.querySelectorAll("[class^=highlight]");
  for (var i = matches.length - 1; i >= 0; i--) {
    if (typeof matches[i]._tippy !== 'undefined'){
      matches[i]._tippy.hide();
    }
  }
};
function onClickGlossary(){
  alert('You clicked the glossary');
};