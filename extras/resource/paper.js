var colors =['red', 'YellowGreen', 'DeepSkyBlue', 'Gold', 'HotPink', 
             'Tomato', 'Orange', 'DarkRed', 'LightCoral', 'Khaki'];

var centerXDict = {};
var centerYDict = {};
var offsetEndXDict = {};
var visibleDict = {};   // visiability for context div

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

function getOffsetEndX(center){ 
  var base = 0; // starting point
  var res = 0;
  var distance = 7; 
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

function getElementCenterY(element){
  // the height of different mjx-container tags in the same line should be the same
  var container = element.closest("mjx-container");
  if (container) {
    var containerRect = container.getBoundingClientRect();
    return containerRect.y + containerRect.height/2;
  }
  var eleRect = element.getBoundingClientRect();
  return eleRect.y + eleRect.height/2;
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
    var startCenterY = getElementCenterY(startElement);
    var endRect = endElement.getBoundingClientRect();
    var endCenterX = endRect.x + endRect.width/2;
    var endCenterY = getElementCenterY(endElement);

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
    var extraOffset = 0;
    if (endEq){ 
      extraOffset = 20; 
    }
    var endPointX = marginLeft+offsetEndX+extraOffset;  
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

function getTypeInfo(type_info){
  if(type_info.type == 'matrix'){
    content = `\\mathbb{R}^{${type_info.rows}×${type_info.cols}}`;
  }
  else if(type_info.type == 'vector'){
    content = `\\mathbb{R}^{${type_info.rows}}`;  
  }
  else if(type_info.type == 'scalar'){
    content = "\\mathbb{R}";
  }
  else if(type_info.type == 'sequence'){
    content = getTypeInfo(type_info.element);
  }
  else if(type_info.type == 'function'){
    var param_list = [];
    for (var i = 0; i <= type_info.params.length - 1; i++) {
      param_list.push(getTypeInfo(type_info.params[i])); 
    }
    var ret = getTypeInfo(type_info.ret)
    content = `${param_list.join()} \\rightarrow ${ret}`;
  }
  else{
    content = "special type";
  }
  return content;
}

function getSymTypeInfo(type_info){
  var info = getTypeInfo(type_info);
  if(type_info.type == 'matrix'){
    content = `$\\in ${info}$`;
  }
  else if(type_info.type == 'vector'){
    content = `$\\in ${info}$`;
  }
  else if(type_info.type == 'scalar'){
    content =  `$\\in ${info}$`;
  }
  else if(type_info.type == 'sequence'){
    content = `$\\in$ sequence of $${info}$`;
  }
  else if(type_info.type == 'function'){
    content = `$\\in ${info}$`;
  }
  else{
    content = `set type`;
  }
  // console.log("type_info.type: " + type_info.type);

  return content;
};

function getGlossarySymId(symbol, context){
  // console.log(`getGlossarySymId, symbol:${symbol}, context:${context}`)
  content = ''
  data_list = sym_data[symbol];
  for (var i = 0; i < data_list.length; i++) {
      var id_tag = symbol.replaceAll("\\","\\\\");
      var data = data_list[i];
      if (data.def_module == context) {
        content = `${data.def_module}-${id_tag}`
        break;
      }
  }
  return content;
}
function getGlossarySymType(symbol, context){
  // get from sym_data rather than iheartla_data
  var content = ''
  var desc = '' 
  var dollarSym = getDollarSym(symbol);
  var otherSym = getOtherSym(symbol);
  for (var k in sym_data) { 
    if (k == symbol || k == otherSym) {
      var cur_data = sym_data[k];
      for (var i = 0; i < cur_data.length; i++) {
        if (cur_data[i].def_module == context) {
          keys.push(k);
          content = cur_data[i].type_info;
          desc = cur_data[i].desc;
          break;
        }
      }
      break;
    }
  }
  return [content, desc];
}

function getGlossarySymInfo(symbol){
  content = ''
  data_list = sym_data[symbol];
  var cur_color = `highlight_${getSymColor(symbol)}`;
  // console.log(`symbol is ${symbol}, cur_color is ${cur_color}, length is ${data_list.length}`)
  for (var i = 0; i < data_list.length; i++) {
      var id_tag = symbol.replaceAll("\\","\\\\");
      var data = data_list[i];
      content += `<div> In module ${data.def_module}<br>
      <a class='${cur_color}' href="#${data.def_module}-${id_tag}">${symbol}</a> is ${getSymTypeInfo(data.type_info)}`
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
function parseSym(tag, symbol, module){
  var targetId = getGlossarySymId(symbol, module);
  if (targetId != '') {
    location.hash = targetId;
    // document.getElementById(targetId).scrollIntoView();
  }
  // data = sym_data[symbol];
  // console.log(`You clicked ${symbol}`);
  // if (typeof tag._tippy === 'undefined'){
  //   tippy(tag, {
  //       content: getGlossarySymInfo(symbol),
  //       placement: 'right',
  //       animation: 'fade',
  //       trigger: 'click', 
  //       theme: 'light',
  //       showOnCreate: true,
  //       allowHTML: true,
  //       interactive: true,
  //       arrow: tippy.roundArrow.repeat(2),
  //       onShow(instance) {
  //         return true;  
  //       },
  //       onHide(instance) { 
  //         return true;  
  //       },
  //     });
  //   MathJax.typeset();
  // }
}
function adjsutGlossaryBtn(){
  var body = document.querySelector("body");
  var style = window.getComputedStyle(body);
  var curWidth = parseInt(style.width, 10)
  var curOffset = parseInt(style.marginLeft, 10)
  var glossaryBtn = document.querySelector(".glossary");
  glossaryBtn.style.left = `${curOffset + curWidth +  30}px`;
}
function addObversers(){
  let options = {
    root: document.body,
    rootMargin: '0px',
    threshold: 0.5
  }
  var observer = new IntersectionObserver(changes => {
    for (const change of changes) {
      var cur_ = change.target.getAttribute('context');
      var curId = change.target.getAttribute('id');
      visibleDict[cur_] = change.isIntersecting;
      // console.log(`current:${cur_}, curId:${curId}, isVisible:${change.isVisible}, isIntersecting:${change.isIntersecting}`)
      if (change.isIntersecting) {
        updateGlossarySyms(cur_);
      }
      else{
        // find the visible context
        for (const [key, value] of Object.entries(visibleDict)) {
          if (value) {
            updateGlossarySyms(key);
            break;
          }
        }
      }
      // console.log(change.time);               // Timestamp when the change occurred
      // console.log(change.rootBounds);         // Unclipped area of root
      // console.log(change.boundingClientRect); // target.boundingClientRect()
      // console.log(change.intersectionRect);   // boundingClientRect, clipped by its containing block ancestors, and intersected with rootBounds
      // console.log(`${cur_}, change.intersectionRatio:${change.intersectionRatio}`);  // Ratio of intersectionRect area to boundingClientRect area
      // console.log(change.target);             // the Element target
      // console.log(`${cur_} isVisible:${change.isVisible}`);
      // console.log(`${cur_} isIntersecting:${change.isIntersecting}`);
    }
  }, {});
  context_dict = {}
  for (var index in iheartla_data.context) {
    var context = iheartla_data.context[index]
    if(!(context in context_dict)){
      context_dict[context] = 0
    }
    // console.log(`#context-${context}-${context_dict[context]}`)
    var noSpaceContext = context.replace(/ /g, "");
    var cur_context = document.querySelector(`#context-${noSpaceContext}-${context_dict[context]}`)
    context_dict[context] += 1;
    // console.log(`context is ${context}, cur_context is ${noSpaceContext}, index:${context_dict[context]}`)
    observer.observe(cur_context, options);
  } 
}
function onLoad(){
  adjsutGlossaryBtn();
  addObversers();
}
function updateGlossarySyms(cur_context){
  // console.log(`Current visible context: ${cur_context}`);
  keys = [];
  for (var k in sym_data) { 
    var cur_data = sym_data[k];
    for (var i = 0; i < cur_data.length; i++) {
      if (cur_data[i].def_module == cur_context) {
        keys.push(k);
      }
    }
  }
  keys.sort();
  info = `<p class='glosary_title'>Glossary of ${cur_context}</p>`
  for (i = 0; i < keys.length; i++) {
    k = keys[i];
    var cur_color = `highlight_${getSymColor(k)}`;
    diff_list = sym_data[k];
    ck = k.replaceAll("\\","\\\\");
    for (var j = 0; j < diff_list.length; j++) {
      if (diff_list[j].def_module == cur_context) {
        var cur_info = getSymTypeInfo(diff_list[j].type_info)
        if(diff_list[j].desc && diff_list[j].desc != 'None' ){
          content = `<span class='glosary_line' onclick="parseSym(this, '${ck}', '${diff_list[j].def_module}');"><span class="${cur_color} paperSymbol">${k}</span> ${cur_info}: ${diff_list[j].desc} </span><br>`;
        }
        else{
          content = `<span class='glosary_line' onclick="parseSym(this, '${ck}', '${diff_list[j].def_module}');"><span class="${cur_color} paperSymbol">${k}</span> ${cur_info} </span><br>`;
        }
        break;
      }
    }
    info += content;
  }
  // update
  var glossaryDiv = document.querySelector(".glossary");
  glossaryDiv.innerHTML = info;
  MathJax.typeset();
}
function getSymColor(symbol){
  color = 'red'
  if (sym_data.hasOwnProperty(symbol)) { 
    color = sym_data[symbol][0].color;
  }
  else{
    var dollarSym = getDollarSym(symbol);
    if (sym_data.hasOwnProperty(dollarSym)) {  
      color = sym_data[dollarSym][0].color;
    } 
  } 
  // console.log(`symbol is ${symbol}, color is ${color}`)
  return color;
}
function getSymInfo(symbol, func_name, isLocalParam=false, localFuncName='', color='red', attrs=''){
  var cur_color = getSymColor(symbol);
  var symAttr = symbol.replaceAll("\\", "\\\\");
  content = `<span class="highlight_${cur_color}" sym="${symAttr}" ${attrs}>`
  var dollarSym = getDollarSym(symbol);
  var otherSym = getOtherSym(symbol);
  var otherFuncName = getOtherSym(localFuncName);
  const [cur_type, cur_desc] = getGlossarySymType(symbol, func_name);
  if(cur_desc && cur_desc != 'None'){
    content += `${dollarSym}</span> ${getSymTypeInfo(cur_type)}: ${cur_desc}`;
  }
  else{
    content += `${dollarSym}</span> ${getSymTypeInfo(cur_type)}`;
  }
  return content;
  // var found = false;
  // for(var eq in iheartla_data.equations){
  //   if(iheartla_data.equations[eq].name == func_name){
  //     if (isLocalParam) {
  //       // local parameter
  //       for(var localFunc in iheartla_data.equations[eq].local_func){
  //         var curLocalFunc = iheartla_data.equations[eq].local_func[localFunc].name;
  //         if (curLocalFunc == localFuncName || curLocalFunc == otherFuncName) {
  //           for(var param in iheartla_data.equations[eq].local_func[localFunc].parameters){
  //             var curParam = iheartla_data.equations[eq].local_func[localFunc].parameters[param].sym;
  //             if (curParam == symbol || curParam == otherSym) {
  //               type_info = iheartla_data.equations[eq].local_func[localFunc].parameters[param].type_info;
  //               found = true;
  //               // content += dollarSym + "</span>"+ " is a local parameter as a " + getSymTypeInfo(type_info);
  //               // var glossarySymType = getGlossarySymType(symbol, func_name);
  //               if(iheartla_data.equations[eq].local_func[localFunc].parameters[param].desc){
  //                 content += `${dollarSym}</span> ${getSymTypeInfo(type_info)}: ${iheartla_data.equations[eq].local_func[localFunc].parameters[param].desc}`;
  //               }
  //               else{
  //                 content += `${dollarSym}</span> ${getSymTypeInfo(type_info)}`;
  //               }
  //             }
  //           }
  //         }
  //       }
  //       if(found){
  //         break;
  //       }
  //     }
  //     else{
  //       // parameters or definitions
  //       for(var param in iheartla_data.equations[eq].parameters){
  //         if (iheartla_data.equations[eq].parameters[param].sym == symbol || 
  //           iheartla_data.equations[eq].parameters[param].sym == otherSym ){
  //           type_info = iheartla_data.equations[eq].parameters[param].type_info;
  //           found = true;
  //           if(iheartla_data.equations[eq].parameters[param].desc){
  //             // content += dollarSym + "</span>"+ " is " + iheartla_data.equations[eq].parameters[param].desc;
  //             content += `${dollarSym}</span> ${getSymTypeInfo(type_info)}: ${iheartla_data.equations[eq].parameters[param].desc}`;
  //           }
  //           else{
  //             content += `${dollarSym}</span> ${getSymTypeInfo(type_info)}`
  //           }
  //           break;
  //         }
  //       }
  //       if(found){
  //         break;
  //       }
  //       for(var param in iheartla_data.equations[eq].definition){
  //         if (iheartla_data.equations[eq].definition[param].sym == symbol || 
  //           iheartla_data.equations[eq].definition[param].sym == otherSym){
  //           type_info = iheartla_data.equations[eq].definition[param].type_info;
  //           found = true;
  //           if(iheartla_data.equations[eq].definition[param].desc){
  //             // content += dollarSym + "</span>"+ " is " + iheartla_data.equations[eq].definition[param].desc;
  //             content += `${dollarSym}</span> ${getSymTypeInfo(type_info)}: ${iheartla_data.equations[eq].definition[param].desc}`;
  //           }
  //           else{
  //             // content += dollarSym + "</span>"+ " is defined as " + getSymTypeInfo(type_info);
  //             content += `${dollarSym}</span> ${getSymTypeInfo(type_info)}`;
  //           }
  //           break;
  //         }
  //       }
  //       if(found){
  //         break;
  //       }
  //     }
  //   }
  // }
  // if (content == '') {
  //   content = `${dollarSym} is a parameter in local function`;
  // } 
  // return content;
}
function showSymArrow(tag, symbol, func_name, type='def', color='blue', 
  isEquation=false, startEq=false, endEq=false){ 
  symbol = symbol.replaceAll("\\","\\\\\\\\");
  // console.log(`In showSymArrow, symbol:${symbol}`);
  showArrow(tag, symbol, func_name, type, color, isEquation, startEq, endEq);
  let asymbol = getOtherSym(symbol);
  showArrow(tag, asymbol, func_name, type, color, isEquation, startEq, endEq);
}
function showArrow(tag, symbol, func_name, type='def', color='blue', 
  isEquation=false, startEq=false, endEq=false){
  // tag.setAttribute('class', `highlight_${color}`);
  // console.log(`In showArrow, sym:${symbol}, color:${color}`); 
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
  symbol = symbol.replaceAll("\\","\\\\\\\\"); 
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
  let new_sym = symbol.replaceAll("\\\\\\\\", "\\\\"); 
  let spanMatches = document.querySelectorAll("span[sym*='" + symbol + "'][context='" + func_name + "']"); 
  for (var i = spanMatches.length - 1; i >= 0; i--) {
    var curClass = spanMatches[i].getAttribute('class');
    var curSym = spanMatches[i].getAttribute('sym');
    const curSymList = curSym.split(';'); 
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
  var cur_color = getSymColor(symbol);
  highlightSym(symbol, func_name, isLocalParam=false, localFuncName='', color=cur_color);
  // console.log(`onClickProse, cur_color:${cur_color}, symbol is ${symbol}`);
  if (type !== 'def') {
    showSymArrow(tag, symbol, func_name, 'use', color=cur_color);
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
  // console.log(`the type is ${type}, sym is ${symbol}, color is ${color}`,)
  resetState();
  // closeOtherTips();
  var cur_color = getSymColor(symbol);
  highlightSym(symbol, func_name, isLocalParam, localFuncName, cur_color);
  showSymArrow(tag, symbol, func_name, type, cur_color);
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
    sym = sym.replaceAll("\\","\\\\\\\\"); 
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
      var cur_color = getSymColor(sym);
      var isLocalParam = false;
      if (localParams.includes(sym)) {
        isLocalParam = true;
        // console.log(`sym:${sym}, isLocalParam:${isLocalParam}`)
      }
      highlightSym(sym, func_name, isLocalParam, localFunc, cur_color);
      // sym = sym.replace("\\","\\\\");
      sym = sym.replaceAll("\\","\\\\\\\\"); 
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
        showSymArrow(symTag, sym_list[i], func_name, t, cur_color, true, startEq, endEq);
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
    var glossaryTag = matches[i].closest("div.glossary");
    if(spanTag == null && glossaryTag == null){
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