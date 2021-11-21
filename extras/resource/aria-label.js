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

function parseAttributes(text, type) {
   const attr = {};
   if (text) {
      let match;
      while ((match = text.match(/^\s*((?:data-)?[a-z][-a-z]*)\s*=\s*(?:"([^"]*)"|(.*?))(?:\s+|,\s*|$)/i))) {
         const name = match[1], value = match[2] || match[3]
         if (type.defaults.hasOwnProperty(name) || ALLOWED.hasOwnProperty(name) || name.substr(0,5) === 'data-') {
            attr[name] = convertEscapes(value);
         } else {
            throw new TexError('BadAttribute', 'Unknown attribute "%1"', name);
         }
         text = text.substr(match[0].length);
      }
      if (text.length) {
         throw new TexError('BadAttributeList', 'Can\'t parse as attributes: %1', text);
      }
   }
   return attr;
}

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
    // console.log(`arg :${arg}`)
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
let ArialabelMethods = {};
/**
 * Implements \arialabel{name}{math}
 * @param {TexParser} parser The calling parser.
 * @param {string} name The TeX string
 */
ArialabelMethods.Arialabel = function (parser, name) {
    let thelabel = parser.GetArgument(name);
    console.log(`thelabel is ${thelabel}`)
    const arg = GetArgumentMML(parser, name);
    NodeUtil.setAttribute(arg, 'aria-label', thelabel);
    let data = JSON.parse(thelabel);
    for (const [key, value] of Object.entries(data)) {
      console.log(`${key}: ${value}`);
      NodeUtil.setAttribute(arg, key, value);
    }
    parser.Push(arg);
};
new CommandMap('aria-label', {
    'arialabel': ['Arialabel'],
}, ArialabelMethods);
const configuration = Configuration.create('aria-label', {
    handler: {
        macro: ['aria-label']
    }
});
