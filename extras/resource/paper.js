var colors =['red', 'YellowGreen', 'DeepSkyBlue', 'Gold', 'HotPink', 
             'Tomato', 'Orange', 'DarkRed', 'LightCoral', 'Khaki'];

var centerXDict = {};
var centerYDict = {};

function alreadyExist(dict, content){
  var threshold = 2;   // different symbols from the same line
  for (const [key, value] of Object.entries(centerYDict)) {
    if (Math.abs(key - content) < threshold) {
      // console.log(`Math.abs(key - content): ${Math.abs(key - content)}`)
      return true;
    }
  }
  return false;
}
function getDictValue(dict, content){
  var threshold = 2;   // different symbols from the same line
  for (const [key, value] of Object.entries(centerYDict)) {
    if (Math.abs(key - content) < threshold) { 
      return value;
    }
  }
  return 0;
}

function getXOffset(){
  // vertical left boundary
  var base = 20; // starting point
  var res = 0;
  var distance = 5; 
  if (base in centerXDict) { 
    cur_index = centerXDict[base];
    res = cur_index * distance;
    centerXDict[base] = cur_index + 1;
  }
  else{
    centerXDict[base] = 1;
    res = 0;
  } 
  // console.log(`getXOffset, res:${res}`);
  return base + res;
}

function getYOffset(base){ 
  var res = 0;
  var distance = 3; 
  if (alreadyExist(centerYDict, base)) { 
    cur_index = getDictValue(centerYDict, base);
    if (cur_index % 2 == 1) {
      res = parseInt(cur_index / 2, 10) * distance;
    }
    else{
      res = -parseInt(cur_index / 2, 10) * distance;
    }
    centerYDict[base] = cur_index + 1;
  }
  else{
    centerYDict[base] = 2;
    res = 0;
  }
  // for (const [key, value] of Object.entries(centerYDict)) {
  //   console.log(key, value);
  // }
  // console.log(`centerYDict, centerYDict:${centerYDict}`);
  return res;
}


var offsetEndXDict = {};
function getOffsetEndX(center){ 
  var base = 0; // starting point
  var res = 0;
  var distance = 5; 
  if (center in offsetEndXDict) { 
    cur_index = offsetEndXDict[center];
    res = cur_index * distance;
    offsetEndXDict[center] = cur_index + 1;
  }
  else{
    offsetEndXDict[center] = 1;
    res = 0;
  } 
  // console.log(`getOffsetEndX, center:${center}, res:${res}`);
  return base - res;
}

function drawArrow(startElement, endElement, style='', color='blue', 
  isEquation=false, startEq=false, endEq=false) { 
    // This pseudocode creates an SVG element for each "arrow". As an alternative,
    // we could always have one SVG element present in the document
    // with absolute position 0,0 (or along the right side of the window)
    // whose width and height allows us to draw anywhere.
    // Then we would add and remove child nodes as needed.
    // You can use vanilla JS or svg.js or snap.js. Probably svg.js is a good fit.
    // Create a new SVG node
    // var svg = SVG().addTo('body').size('100%', '100%').move(-1010, -410);
    // console.log(`start is ${startElement}, end is ${endElement}`)
    // console.log(`svg is ${svg}`);
    var body = document.querySelector("body");
    var style = window.getComputedStyle(body);
    var newWidth = parseInt(style.width, 10) + parseInt(style.marginLeft, 10) + parseInt(style.marginRight, 10);
    var newHeight = parseInt(style.height, 10);
    var svg = SVG().addTo('body').size(`${newWidth}px`, `${newHeight}px`).attr('left', '0px');
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

    var offsetStartY = getYOffset(startCenterY); 
    var offsetEndY = getYOffset(endCenterY);
    var offsetVerticalX = getXOffset(); 

    var offsetEndX = getOffsetEndX(endCenterY);

    var marginLeft = parseInt(style.marginLeft, 10)
    var bodyWidth = parseInt(style.width, 10)
    var marginTop = parseInt(style.marginTop, 10)
    // console.log(style); 
    var arrowSize = 5;
    // var offsetEndX = 20;
    // var endPointX = endCenterX - bodyRect.x + marginLeft;
    // var endPointY = endCenterY - bodyRect.y + marginTop;
    // var endPointX = bodyWidth+marginLeft-offsetEndX;
    var endPointY = endCenterY - bodyRect.y + marginTop;
    // console.log(`marginTop is ${marginTop}`);
    // svg.path(`M${startCenterX - bodyRect.x + marginLeft} ${startCenterY - bodyRect.y + marginTop} 
    // svg.path(`M${bodyWidth+marginLeft-offsetEndX} ${startCenterY - bodyRect.y + marginTop+offsetStartY} 
    //   L ${bodyWidth+marginLeft+offsetVerticalX} ${startCenterY - bodyRect.y + marginTop+offsetStartY} 
    //   L ${bodyWidth+marginLeft+offsetVerticalX} ${endCenterY - bodyRect.y + marginTop+offsetEndY} 
    //   L ${endPointX} ${endPointY+offsetEndY} 
    //   L ${endPointX+arrowSize} ${endPointY-arrowSize+offsetEndY} 
    //   L ${endPointX} ${endPointY+offsetEndY} 
    //   L ${endPointX+arrowSize} ${endPointY+arrowSize+offsetEndY} 
    //   `).attr({fill: 'white', 'fill-opacity': 0, stroke: color, 'stroke-width': 2, 'stroke-linejoin': 'bevel', 'stroke-linecap': 'square'})
    var offsetStartX = 0; 
    if (startEq) { 
      offsetStartX = 20; 
    }
    if (endEq){ 
      offsetEndX = 20; 
    }
    // console.log(`offsetEndX is ${offsetEndX}`)
    var endPointX = marginLeft+offsetEndX; 
    svg.path(`M${(marginLeft+offsetStartX)} ${startCenterY - bodyRect.y + marginTop+offsetStartY} 
      L ${(marginLeft-offsetVerticalX)} ${startCenterY - bodyRect.y + marginTop+offsetStartY} 
      L ${(marginLeft-offsetVerticalX)} ${endCenterY - bodyRect.y + marginTop+offsetEndY} 

      L ${endPointX} ${endPointY+offsetEndY} 
      L ${endPointX-arrowSize} ${endPointY-arrowSize+offsetEndY} 
      L ${endPointX} ${endPointY+offsetEndY} 
      L ${endPointX-arrowSize} ${endPointY+arrowSize+offsetEndY} 
      `).attr({fill: 'white', 'fill-opacity': 0, stroke: color, 'stroke-width': 2, 'stroke-linejoin': 'bevel', 'stroke-linecap': 'square'})
    svg.attr('offset', parseInt(style.marginLeft, 10))
    document.querySelector(".arrow").style.marginLeft = "0px"
}

function getSymTypeInfo(type_info){
  if(type_info.type == 'matrix'){
    content = "a matrix, rows: " + type_info.rows + ", cols: " + type_info.cols;
  }
  else if(type_info.type == 'vector'){
    content = "a vector, rows: " + type_info.rows;
  }
  else if(type_info.type == 'scalar'){
    content = "a scalar";
  }
  else if(type_info.type == 'sequence'){
    content = "a sequence";
  }
  else if(type_info.type == 'function'){
    content = "a function";
  }
  else{
    content = "an invalid type";
  }
  // console.log("type_info.type: " + type_info.type);

  return content;
};
function getGlossarySymInfo(symbol){
  content = ''
  data_list = sym_data[symbol];
  console.log(`symbol is ${symbol}, length is ${data_list.length}`)
  for (var i = 0; i < data_list.length; i++) {
      var data = data_list[i];
      content += `<div> In module ${data.def_module}<br>
      <a class='detail' href="#${data.def_module}-${symbol}">${symbol}</a> is ${getSymTypeInfo(data.type_info)}`
      content += `` ;
      if (data.used_equations.length > 0) {
        content += `<br>${symbol} is used in ` ;
        for (var j = 0; j < data.used_equations.length; j++) {
          content += data.used_equations[j];
        }
      }
      content += `</div>`;
  }
  return `<span>${content}</span>`;
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
        theme: 'light',
        showOnCreate: true,
        allowHTML: true,
        interactive: true,
        arrow: tippy.roundArrow.repeat(2),
        onShow(instance) {
          return true;  
        },
        onHide(instance) { 
          return true;  
        },
      });
    MathJax.typeset();
  }
}
function adjsutGlossaryBtn(){
  var body = document.querySelector("body");
  var style = window.getComputedStyle(body);
  var curWidth = parseInt(style.width, 10)
  var curOffset = parseInt(style.marginLeft, 10)
  var glossaryBtn = document.querySelector(".glossary");
  glossaryBtn.style.left = `${curOffset + curWidth +  30}px`;
}
function onLoad(){
  parseAllSyms();
  adjsutGlossaryBtn();
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
    ck = k.replace("\\","\\\\");
    if (diff_length > 1) {
      content = `<span onclick="parseSym(this, '${ck}');"><span class="clickable_sym">${k}</span>: ${diff_length} different types</span><br>`;
    }
    else{
      if (diff_list[0].is_defined){
        content = `<span onclick="parseSym(this, '${ck}');"><span class="clickable_sym">${k}</span>: defined </span><br>`;
      }
      else{
        content = `<span onclick="parseSym(this, '${ck}');"><span class="clickable_sym">${k}</span>: ${diff_list[0].desc}</span><br>`;
      }
    }
    // console.log(content);
    info += content;
  }
  // console.log(document.querySelector("#glossary"));
  tippy(document.querySelector("#glossary"), {
        content: info,
        placement: 'right',
        animation: 'fade',
        trigger: 'click', 
        theme: 'light',
        allowHTML: true,
        interactive: true,
        arrow: tippy.roundArrow.repeat(2),
        onShown(instance) {
          MathJax.typeset();
          return true;  
        },
      }); 
  MathJax.typeset();
}
function getSymInfo(symbol, func_name, isLocalParam=false, localFuncName='', color='red', attrs=''){
  content = `<span class="highlight_${color}" sym="${symbol}" ${attrs}>`
  var found = false;
  var dollarSym = getDollarSym(symbol);
  var otherSym = getOtherSym(symbol);
  var otherFuncName = getOtherSym(localFuncName);
  for(var eq in iheartla_data.equations){
    if(iheartla_data.equations[eq].name == func_name){
      if (isLocalParam) {
        // local parameter
        for(var localFunc in iheartla_data.equations[eq].local_func){
          var curLocalFunc = iheartla_data.equations[eq].local_func[localFunc].name;
          if (curLocalFunc == localFuncName || curLocalFunc == otherFuncName) {
            for(var param in iheartla_data.equations[eq].local_func[localFunc].parameters){
              var curParam = iheartla_data.equations[eq].local_func[localFunc].parameters[param].sym;
              if (curParam == symbol || curParam == otherSym) {
                type_info = iheartla_data.equations[eq].local_func[localFunc].parameters[param].type_info;
                found = true;
                content += dollarSym + "</span>"+ " is a local parameter as a " + getSymTypeInfo(type_info);
              }
            }
          }
        }
        if(found){
          break;
        }
      }
      else{
        // parameters or definitions
        for(var param in iheartla_data.equations[eq].parameters){
          if (iheartla_data.equations[eq].parameters[param].sym == symbol || 
            iheartla_data.equations[eq].parameters[param].sym == otherSym ){
            type_info = iheartla_data.equations[eq].parameters[param].type_info;
            found = true;
            if(iheartla_data.equations[eq].parameters[param].desc){
              content += dollarSym + "</span>"+ " is " + iheartla_data.equations[eq].parameters[param].desc + ", the type is " + getSymTypeInfo(type_info);
            }
            else{
              content += dollarSym + "</span>"+ " is a parameter as a " + getSymTypeInfo(type_info);
            }
            break;
          }
        }
        if(found){
          break;
        }
        for(var param in iheartla_data.equations[eq].definition){
          if (iheartla_data.equations[eq].definition[param].sym == symbol || 
            iheartla_data.equations[eq].definition[param].sym == otherSym){
            type_info = iheartla_data.equations[eq].definition[param].type_info;
            found = true;
            content += dollarSym + "</span>"+ " is defined as a " + getSymTypeInfo(type_info);
            break;
          }
        }
        if(found){
          break;
        }
      }
    }
  }
  if (content == '') {
    content = `${dollarSym} is a parameter in local function`;
  } 
  return content;
}
function showSymArrow(tag, symbol, func_name, type='def', color='blue', 
  isEquation=false, startEq=false, endEq=false){ 
  symbol = symbol.replace("\\","\\\\\\\\");
  // console.log(`In showSymArrow, symbol:${symbol}`);
  showArrow(tag, symbol, func_name, type, color, isEquation, startEq, endEq);
  let asymbol = getOtherSym(symbol);
  showArrow(tag, asymbol, func_name, type, color, isEquation, startEq, endEq);
}
function showArrow(tag, symbol, func_name, type='def', color='blue', 
  isEquation=false, startEq=false, endEq=false){
  // tag.setAttribute('class', `highlight_${color}`);
  // console.log(`In showArrow, sym:${symbol}`); 
  if (type === 'def' ) {
    // Point to usage
    const matches = document.querySelectorAll("[case='equation'][sym='" + symbol + "'][func='"+ func_name + "'][type='use']");
    // console.log(`matches length:${matches.length}`);
    var cur_list = [];
    for (var i = matches.length - 1; i >= 0; i--) {
      // matches[i].setAttribute('class', `highlight_${color}`);
      // console.log(`${i} is ${matches[i].innerHTML}`)
      if (matches[i] !== tag && matches[i].tagName.startsWith("MJX")) {
        var curRect = matches[i].getBoundingClientRect();
        var curCenterY = curRect.y + curRect.height/2;
        if (!(cur_list.includes(curCenterY))) {
          cur_list.push(curCenterY);
          drawArrow(tag, matches[i],'',color, isEquation, startEq, endEq);
        } 
      }
    }
    // prose label
    // const prose = document.querySelectorAll("mjx-mi[sym='" + symbol + "'][module='"+ func_name + "']");
    // if (prose !== 'undefined') {
    //   for (var i = prose.length - 1; i >= 0; i--) {
    //     // matches[i].setAttribute('class', `highlight_${color}`);
    //     if (prose[i] !== tag ) {
    //       drawArrow(tag, prose[i], '',color,offsetVerticalX, offsetStartY, offsetEndY, offsetEndX);
    //     }
    //   }
    // }
  }
  else{
    // Point from def
    const matches = document.querySelectorAll("[case='equation'][sym='" + symbol + "'][func='"+ func_name + "'][type='def']");
    // console.log(`matches.length is ${matches.length}`)
    if (matches !== 'undefined' && matches.length !== 0) {
      // console.log(`${matches.length} prose`)
      var cur_list = [];
      for (var i = matches.length - 1; i >= 0; i--) {
        // console.log(`${i} is ${matches[i].innerHTML}, tag is ${matches[i].tagName}`)
        // matches[i].setAttribute('class', `highlight_${color}`);
        if (matches[i] !== tag && matches[i].tagName.startsWith("MJX")) {
          var curRect = matches[i].getBoundingClientRect();
          var curCenterY = curRect.y + curRect.height/2; 
          if (!(cur_list.includes(curCenterY))) {
            cur_list.push(curCenterY);
            drawArrow(matches[i], tag, '',color, isEquation, startEq, endEq);
          } 
        }
      }
    }
    else{
      // defined in prose: mjx-mi mjx-msub
      // const prose = document.querySelectorAll("mjx-mi[sym='" + symbol + "'][module='"+ func_name + "'][type='def']");
      const prose = document.querySelectorAll("[sym='" + symbol + "'][module='"+ func_name + "'][type='def']");
      // console.log(`prose.length is ${prose.length}`);
      // let new_sym = symbol.replace("\\\\\\\\", "\\"); 
      // new_sym = symbol;
      // const prose = document.querySelectorAll("[sym='" + new_sym + "'][module='"+ func_name + "'][type='def']");
      // console.log(`prose.length is ${prose.length}`);
      if (prose !== 'undefined') {
        var cur_list = [];
        for (var i = prose.length - 1; i >= 0; i--) {
          // console.log(`${i} is ${prose[i].innerHTML}, tag is ${prose[i].tagName}, parentElement:${prose[i].parentElement.innerHTML}`)
          if (prose[i] !== tag ) {
            // prose[i].setAttribute('class', `highlight_${color}`);
            var curRect = prose[i].getBoundingClientRect();
            var curCenterY = curRect.y + curRect.height/2; 
            if (!(cur_list.includes(curCenterY))) {
                cur_list.push(curCenterY);
                drawArrow(prose[i], tag, '',color, isEquation, startEq, endEq);
            } 
          }
        }
      }
    }
  }
}
function getOtherSym(symbol){
  if (symbol.includes('$')){
    symbol = symbol.replaceAll('$','');
  }
  else{
    symbol = `$${symbol}$`;
  }
  return symbol;
}
function getDollarSym(symbol){
  if (symbol.includes('$')){
    return symbol;
  }
  else{
    return `$${symbol}$`;
  }
}
function highlightSym(symbol, func_name, isLocalParam=false, localFuncName='', color='red'){ 
  symbol = symbol.replace("\\","\\\\\\\\"); 
  // console.log(`In highlightSym, symbol: ${symbol}`)
  highlightSymInProseAndEquation(symbol, func_name, isLocalParam, localFuncName, color);
  let asymbol = getOtherSym(symbol);
  highlightSymInProseAndEquation(asymbol, func_name, isLocalParam, localFuncName, color);
}
function highlightSymInProseAndEquation(symbol, func_name, isLocalParam=false, localFuncName='', color='red'){ 
  // if (isLocalParam) {
  //   // console.log(`localFuncName is ${localFuncName}`)
  //   var search = "[sym='" + symbol + "'][module='" + func_name + "'][func='" + localFuncName + "']";
  //   // console.log(`search str is ${search}`)
  //   // only hightlight the same symbols in the local function
  //   let matches = document.querySelectorAll("[sym='" + symbol + "'][func='" + func_name + "'][localfunc='" + localFuncName + "']");
  //   for (var i = matches.length - 1; i >= 0; i--) {
  //     var curClass = matches[i].getAttribute('class');
  //     if (curClass !== '') {
  //       curClass = `highlight_${color}` + ' ' + curClass;
  //     }
  //     else{
  //       curClass = `highlight_${color}`;
  //     }
  //     matches[i].setAttribute('class', curClass);
  //   }
  //   return;
  // }
  // console.log(`symbol is ${symbol}`);
  // syms in prose and derivations
  let matches = document.querySelectorAll("[sym='" + symbol + "'][module='" + func_name + "']");
  for (var i = matches.length - 1; i >= 0; i--) {
    var curClass = matches[i].getAttribute('class');
    if (curClass !== '') {
      curClass = `highlight_${color}` + ' ' + curClass;
    }
    else{
      curClass = `highlight_${color}`;
    }
    matches[i].setAttribute('class', curClass);
  }
  // span prose 
  let new_sym = symbol.replace("\\\\\\\\", "\\"); 
  let spanMatches = document.querySelectorAll("span[sym*='" + new_sym + "'][context='" + func_name + "']");
  for (var i = spanMatches.length - 1; i >= 0; i--) {
    var curClass = spanMatches[i].getAttribute('class');
    var curSym = spanMatches[i].getAttribute('sym');
    const curSymList = curSym.split(' ');
    // console.log(`i is ${i}, curSymList is ${curSymList} `)
    for (var j = curSymList.length - 1; j >= 0; j--) {
      if (curSymList[j] === new_sym) {
        if (curClass !== '') {
          curClass = `highlight_${color}` + ' ' + curClass;
        }
        else{
          curClass = `highlight_${color}`;
        }
        spanMatches[i].setAttribute('class', curClass);
        break;
      }
    }
  }
  // syms in equation
  let eqMatches = document.querySelectorAll("[case='equation'][sym='" + symbol + "'][func='"+ func_name + "']");
  for (var i = eqMatches.length - 1; i >= 0; i--) {
    var curClass = eqMatches[i].getAttribute('class');
    if (curClass !== '') {
      curClass = `highlight_${color}` + ' ' + curClass;
    }
    else{
      curClass = `highlight_${color}`;
    }
    eqMatches[i].setAttribute('class', curClass);
  }
}
function onClickProse(tag, symbol, func_name, type='def') {
  resetState();
  // console.log(`onClickProse, ${tag}, symbol is ${symbol}, ${func_name}`);
  highlightSym(symbol, func_name);
  if (type !== 'def') {
    showSymArrow(tag, symbol, func_name, 'use', color='red');
  }
  if (typeof tag._tippy === 'undefined'){
    tippy(tag, {
        content: getSymInfo(symbol, func_name),
        placement: 'bottom',
        animation: 'fade',
        trigger: 'click', 
        theme: 'light',
        showOnCreate: true,
        allowHTML: true,
        arrow: tippy.roundArrow.repeat(2),
        onShow(instance) {
          // closeOtherTips();
          return true;  
        },
        onHide(instance) {
          resetState();
          return true;  
        },
      });
    MathJax.typeset();
  }
}
/**
 * Click a symbol in equations
 *
 * @param {object} tag The current xml tag
 * @param {string} symbol The symbol name
 * @param {string} func_name The equation/context name
 * @param {string} type The type for the symbol: 'def','prose','use'
 * @param {string} isLocalParam whether it's a parameter
 * @param {string} localFuncName function name
 * @param {string} color 
 * @return 
 */
function onClickSymbol(tag, symbol, func_name, type='def', isLocalParam=false, localFuncName='', color='red') {
  console.log(`the type is ${type}, sym is ${symbol}`)
  resetState();
  // closeOtherTips();
  highlightSym(symbol, func_name, isLocalParam, localFuncName, color);
  showSymArrow(tag, symbol, func_name, type, color);
    // d3.selectAll("mjx-mi[sym='" + symbol + "']").style("class", "highlight");
  if (typeof tag._tippy === 'undefined'){
    tippy(tag, {
        content: getSymInfo(symbol, func_name, isLocalParam, localFuncName, color),
        placement: 'bottom',
        animation: 'fade',
        trigger: 'click', 
        theme: 'light',
        showOnCreate: true,
        allowHTML: true,
        arrow: tippy.roundArrow.repeat(2),
        onShow(instance) {
          // closeOtherTips();
          return true;  
        },
        onHide(instance) {
          resetState();
          return true;  
        },
      });
    MathJax.typeset();
  }
  // console.log("clicked: " + symbol + " in " + func_name); 
};
function getEquationContent(func_name, sym_list, isLocalFunc=false, localFunc='', localParams=[]){
  content = `<span class="highlight_grey">This equation has ${sym_list.length} symbols:</span><br>`;
  for (var i = sym_list.length - 1; i >= 0; i--) {
    sym = sym_list[i];
    sym = sym.replace("\\","\\\\\\\\"); 
    var isLocalParam = false;
    if (localParams.includes(sym)) {
      isLocalParam = true;
    }
    content += getSymInfo(sym_list[i], func_name, isLocalParam, localFunc, colors[i], `case='equationInfo'`) + '<br>';
  }
  return content;
}

/**
 * Click an equation
 *
 * @param {object} tag The current xml tag
 * @param {string} func_name The current module name
 * @param {string} sym_list The symbols in the equation, the last one is the function name
 * @param {string} isLocalFunc whether it's a local function
 * @param {string} localParams the parameters
 * @return 
 */
function onClickEq(tag, func_name, sym_list, isLocalFunc=false, localFunc='', localParams=[]) { 
  // closeOtherTips();
  resetState();
  content = getEquationContent(func_name, sym_list, isLocalFunc, localFunc, localParams);
  // Scale equation and append new div
  document.body.classList.add("opShallow");
  var div = tag.closest("div.equation");
  //
  function showAllArrows(){
    for (var i = sym_list.length - 1; i >= 0; i--) {
      sym = sym_list[i];
      var isLocalParam = false;
      if (localParams.includes(sym)) {
        isLocalParam = true;
        console.log(`sym:${sym}, isLocalParam:${isLocalParam}`)
      }
      highlightSym(sym, func_name, isLocalParam, localFunc, colors[i]);
      // sym = sym.replace("\\","\\\\");
      sym = sym.replace("\\","\\\\\\\\"); 
      var symTag;
      if (div) {
        var parentTag = tag.closest("div");
        symTag = parentTag.querySelector("[case='equationInfo'][sym='" + sym + "']");
      }
      else{
        // inline
        symTag = tag.querySelector("[case='equation'][sym='" + sym + "']");
      }
      const matches = document.querySelectorAll("[case='equation'][sym='" + sym + "']");
      // console.log(`tag is ${tag}, sym is ${sym}, symTag is ${symTag}, matches is ${matches}`);
      if (symTag !== null){
        // console.log(`symTag is ${symTag}`);
        var t = 'use';
        var startEq = false;
        var endEq = false;
        if (i === sym_list.length - 1) {
          t = 'def';
          startEq = true;
        }
        else{
          endEq = true;
        } 
        if (!div) {
          startEq = false;
          endEq = false;
        }
        showSymArrow(symTag, sym_list[i], func_name, t, colors[i], true, startEq, endEq);
      }
    }
  }
  if (div) {
    // not inline
    var mjx = tag.closest("mjx-container");
    mjx.classList.remove("eqNormal");
    mjx.classList.add("eqHighlight");
    div.classList.add("eqDivHighlight");
    const symDiv = document.createElement("div");
    symDiv.innerHTML = content
    // content = `<div class='euqation_highlight'> ${content} </div>`
    div.appendChild(symDiv);
    var topLine = document.createElement("HR");
    div.prepend(topLine)
    topLine.className = "eqInfo";
    var bottomLine = document.createElement("HR");
    bottomLine.className = "eqInfo";
    div.appendChild(bottomLine)
    symDiv.classList.add("eqInfoDiv");
    MathJax.typeset();
    // console.log(`div is ${div.innerHTML}`);
    setTimeout(showAllArrows, 500);
  }
  else{
    showAllArrows();
    if (typeof tag._tippy === 'undefined'){
      tippy(tag, {
          content: content,
          placement: 'bottom',
          animation: 'fade',
          trigger: 'click', 
          theme: 'light',
          showOnCreate: true,
          allowHTML: true,
          arrow: tippy.roundArrow.repeat(2),
          // interactive: true,
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
      MathJax.typeset();
    }
  }
};
function resetState(){
  centerXDict = {};
  centerYDict = {};
  offsetEndXDict = {};
  // console.log(`reset all`);
  document.body.classList.remove("opShallow");
  removeArrows();
  removeSymHighlight();
  removeAddedDiv();
  resetEqScale();
  closeOtherTips();
}
function resetEqScale(argument) {
  const matches = document.querySelectorAll(".eqHighlight");
  for (var i = matches.length - 1; i >= 0; i--) {
    matches[i].classList.remove('eqHighlight');
    matches[i].classList.add('eqNormal');
  }
  // 
  const matchesDiv = document.querySelectorAll(".eqDivHighlight");
  for (var i = matchesDiv.length - 1; i >= 0; i--) {
    matchesDiv[i].classList.remove('eqDivHighlight'); 
  }
}
function removeAddedDiv() {
  const matches = document.querySelectorAll("[class*=eqInfo]");
  for (var i = matches.length - 1; i >= 0; i--) {
    matches[i].parentNode.removeChild(matches[i]);
  }
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
  // ^= matches "start with", *= matches "contains"
  const matches = document.querySelectorAll("[class*=highlight]");
  for (var i = matches.length - 1; i >= 0; i--) {
    var spanTag = matches[i].closest("div.tippy-box");
    if(spanTag == null){
      var cur = matches[i].getAttribute('class');
      const classArray = cur.split(' ');
      let new_classes = [];
      for (var j = classArray.length - 1; j >= 0; j--) {
        if (classArray[j] !== ' ' && ! classArray[j].includes('highlight')) {
          new_classes.push(classArray[j]);
        }
      }
      matches[i].setAttribute('class', new_classes.join(' '));
    }
  }
}
function closeOtherTips(){
  const matches = document.querySelectorAll("[class*=highlight]");
  for (var i = matches.length - 1; i >= 0; i--) {
    if (typeof matches[i]._tippy !== 'undefined'){
      matches[i]._tippy.hide();
    }
  }
};
function onClickGlossary(){
  alert('You clicked the glossary');
};