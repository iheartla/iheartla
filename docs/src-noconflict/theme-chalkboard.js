ace.define("ace/theme/chalkboard",["require","exports","module","ace/lib/dom"], function(require, exports, module) {

exports.isDark = true;
exports.cssClass = "ace-chalkboard";
exports.cssText = ".ace-chalkboard .ace_gutter {\
background: #8e864e;\
color: #C5C8C6\
}\
.ace-chalkboard .ace_print-margin {\
width: 1px;\
background: #3d4d3e\
}\
.ace-chalkboard {\
background-color: #445b45;\
color: #FFF\
}\
.ace-chalkboard .ace_cursor {\
color: #AAA\
}\
.ace-chalkboard .ace_marker-layer .ace_selection {\
background: #373B41\
}\
.ace-chalkboard.ace_multiselect .ace_selection.ace_start {\
box-shadow: 0 0 3px 0px #1D1F21;\
}\
.ace-chalkboard .ace_marker-layer .ace_step {\
background: rgb(102, 82, 0)\
}\
.ace-chalkboard .ace_marker-layer .ace_bracket {\
margin: -1px 0 0 -1px;\
border: 1px solid #4B4E55\
}\
.ace-chalkboard .ace_marker-layer .ace_active-line {\
background: #3d4d3e\
}\
.ace-chalkboard .ace_gutter-active-line {\
background-color: #75704c\
}\
.ace-chalkboard .ace_marker-layer .ace_selected-word {\
border: 1px solid #373B41\
}\
.ace-chalkboard .ace_invisible {\
color: #4B4E55\
}\
.ace-chalkboard .ace_keyword,\
.ace-chalkboard .ace_meta,\
.ace-chalkboard .ace_storage,\
.ace-chalkboard .ace_storage.ace_type,\
.ace-chalkboard .ace_support.ace_type {\
color: #B5ADCC\
}\
.ace-chalkboard .ace_keyword.ace_operator {\
color: #fdecb0\
}\
.ace-chalkboard .ace_constant.ace_character,\
.ace-chalkboard .ace_constant.ace_language,\
.ace-chalkboard .ace_constant.ace_numeric,\
.ace-chalkboard .ace_keyword.ace_other.ace_unit,\
.ace-chalkboard .ace_support.ace_constant,\
.ace-chalkboard .ace_variable.ace_parameter {\
color: #D9B08D\
}\
.ace-chalkboard .ace_constant.ace_other {\
color: #CED1CF\
}\
.ace-chalkboard .ace_invalid {\
color: #CED2CF;\
background-color: #DF5F5F\
}\
.ace-chalkboard .ace_invalid.ace_deprecated {\
color: #CED2CF;\
background-color: #B798BF\
}\
.ace-chalkboard .ace_fold {\
background-color: #81A2BE;\
border-color: #C5C8C6\
}\
.ace-chalkboard .ace_entity.ace_name.ace_function,\
.ace-chalkboard .ace_support.ace_function,\
.ace-chalkboard .ace_variable {\
color: #81A2BE\
}\
.ace-chalkboard .ace_support.ace_class,\
.ace-chalkboard .ace_support.ace_type {\
color: #F0C674\
}\
.ace-chalkboard .ace_heading,\
.ace-chalkboard .ace_markup.ace_heading,\
.ace-chalkboard .ace_string {\
color: #B5BD68\
}\
.ace-chalkboard .ace_entity.ace_name.ace_tag,\
.ace-chalkboard .ace_entity.ace_other.ace_attribute-name,\
.ace-chalkboard .ace_meta.ace_tag,\
.ace-chalkboard .ace_string.ace_regexp,\
.ace-chalkboard .ace_variable {\
color: #CC6666\
}\
.ace-chalkboard .ace_bracket,\
.ace-chalkboard .ace_paren_color_0 {\
color: #f00\
}\
.ace-chalkboard .ace_comment {\
color: #aaa\
}\
.ace-chalkboard .ace_indent-guide {\
background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAACCAYAAACZgbYnAAAAEklEQVQImWNgYGBgYHB3d/8PAAOIAdULw8qMAAAAAElFTkSuQmCC) right repeat-y\
}";

var dom = require("../lib/dom");
dom.importCssString(exports.cssText, exports.cssClass);
});                (function() {
                    ace.require(["ace/theme/tomorrow_night"], function(m) {
                        if (typeof module == "object" && typeof exports == "object" && module) {
                            module.exports = m;
                        }
                    });
                })();
            
