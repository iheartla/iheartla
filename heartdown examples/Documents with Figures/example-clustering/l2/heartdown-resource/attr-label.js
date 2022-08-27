/*************************************************************
 *  Copyright (c) 2020 krautzource UG
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */
const { Configuration } = MathJax._.input.tex.Configuration;
const { CommandMap } = MathJax._.input.tex.SymbolMap;
const NodeUtil = MathJax._.input.tex.NodeUtil.default;

/**
 * Parses the math argument of the above commands and returns it as single
 * node (in an mrow if necessary). The HTML attributes are then
 * attached to this element.
 * @param {TexParser} parser The calling parser.
 * @param {string} name The calling macro name.
 * @return {MmlNode} The math node.
 */
let GetArgumentMML = function (parser, name) {
    // console.log(`parser :${parser}, name:${name}`)
    let arg = parser.ParseArg(name);
    if (!NodeUtil.isInferred(arg)) {
        return arg;
    }
    let children = NodeUtil.getChildren(arg);
    if (children.length === 1) {
        return children[0];
    }
    const mrow = parser.create('node', 'mrow');
    NodeUtil.copyChildren(arg, mrow);
    NodeUtil.copyAttributes(arg, mrow);
    return mrow;
};


let AttrlabelMethods = {};

/**
 * Implements \idlabel{name}{math}
 * @param {TexParser} parser The calling parser.
 * @param {string} name The TeX string
 */
AttrlabelMethods.IdLabel = function (parser, name) {
    let thelabel = parser.GetArgument(name);
    // console.log(`thelabel is ${thelabel}`)
    const arg = GetArgumentMML(parser, name);
    // NodeUtil.setAttribute(arg, 'attr-label', thelabel);
    let data = JSON.parse(thelabel);
    for (const [key, value] of Object.entries(data)) {
      // console.log(`${key}: ${value}`);
      NodeUtil.setAttribute(arg, key, value);
    }
    NodeUtil.setAttribute(arg, "class", 'paperSymbol');
    parser.Push(arg);
}

/**
 * Implements \eqlabel{euqation}{}
 * @param {TexParser} parser The calling parser.
 * @param {string} name The TeX string
 */
AttrlabelMethods.EqLabel = function (parser, name) {
    let thelabel = parser.GetArgument(); 
    const arg = parser.ParseArg(name); 
    let data = JSON.parse(thelabel); 
    // get row list
    let rows = parser.stack.Top(1).table;
    // current row
    let row = rows[rows.length - 1];
    for (const [key, value] of Object.entries(data)) {
      // set attributes
      NodeUtil.setAttribute(row, key, value);
    }
    parser.Push(arg); 
};

function getProseArg(parser, name, type='def'){
    let modulelabel = parser.GetArgument(); 
    // get the real tex string in \prose*{context}{real}
    let remain = parser.string.slice(parser.i)
    var endIndex = 0;
    var leftBrace = 0;
    for (var i = 1; i <= remain.length; i++) {
      if (remain[i] == '{') {
        leftBrace++;
      }
      else if (remain[i] == '}') {
        if (leftBrace == 0) {
          endIndex = i;
          break;
        }
        leftBrace--;
      }
    }
    let raw = remain.substring(1, endIndex);
    if (raw.substring(0,1) == '{' && raw.substring(raw.length-1, raw.length) == '}') {
      raw = raw.substring(1, raw.length-1);
    }
    const arg = parser.ParseArg(name);  
    // let param = arg.coreMO().childNodes[0].getText();
    let param = `${raw}`;
    // let param = `$${raw}$`;
    // console.log(`param is ${param}, string is ${parser.string}, raw is ${raw}`);
    param = param.replaceAll("\\","\\\\");
    param = param.replaceAll("'","\\'").replaceAll('"','\\"');
    // console.log(`param is ${param}, string is ${parser.string}, raw is ${raw}`);
    NodeUtil.setAttribute(arg, "module", modulelabel);
    NodeUtil.setAttribute(arg, "sym", param);
    NodeUtil.setAttribute(arg, "type", type);
    NodeUtil.setAttribute(arg, "class", 'paperSymbol');
    NodeUtil.setAttribute(arg, "onclick", `event.stopPropagation(); onClickProse(this, '${param}', '${modulelabel}', '${type}');`);
    return arg;
}

/**
 * Implements \eqlabel{euqation}{}
 * @param {TexParser} parser The calling parser.
 * @param {string} name The TeX string
 */
AttrlabelMethods.ProseLabel = function (parser, name) {
    parser.Push(getProseArg(parser, name, 'use')); 
};

/**
 * Implements \eqlabel{euqation}{}
 * @param {TexParser} parser The calling parser.
 * @param {string} name The TeX string
 */
AttrlabelMethods.ProseDefLabel = function (parser, name) { 
    parser.Push(getProseArg(parser, name, 'def')); 
};

new CommandMap('attr-label', {
    'idlabel': ['IdLabel'],
    'eqlabel': ['EqLabel'],
    'proselabel': ['ProseLabel'],
    'prosedeflabel': ['ProseDefLabel'],
}, AttrlabelMethods);

const configuration = Configuration.create('attr-label', {
    handler: {
        macro: ['attr-label']
    }
});
