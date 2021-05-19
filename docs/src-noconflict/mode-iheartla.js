ace.define("ace/mode/iheartla_highlight_rules",["require","exports","module","ace/lib/oop","ace/mode/text_highlight_rules"], function (require, exports, module) {
    "use strict";

    var oop = require("../lib/oop");
    var TextHighlightRules = require("./text_highlight_rules").TextHighlightRules;

    var IheartlaHighlightRules = function () {

        this.$rules = {
            start: [
                {
                    token: ['comment'],
                    regex: /(?<=.*[:∈].*:)[^`;\n\r\f]*/
                },
                {
                    token: ['string'],
                    regex: /`[^`]*`/
                },
                {
                    token: ['constant.numeric'],
                    regex: /[\u2070\u00B9\u00B2\u00B3\u2074-\u2079\u2080-\u2089\d]+/
                },
                {
                    token: ['keyword.control'],
                    regex: /(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])if(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])/
                },
                {
                    token: ['keyword.definition'],
                    regex: /(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])where(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])|(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])given(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])|(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])from(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])/
                },
                {
                    token: ['keyword.operator'],
                    regex: /->|⁻¹|\|\||[\+\-±⋅×/÷\^_><ᵀ∈‖\|\*]/
                },
                {
                    token: ['keyword.other'],
                    regex: /(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])sum(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])|(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])min(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])|(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])max(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])|(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])argmin(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])|(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])argmax(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])|(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])otherwise(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])|(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])subject to(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])|(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])s.t.(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])/
                },
                {
                    token: ['support.function'],
                    regex: /(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])exp(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])|(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])log(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])|(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])ln(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])|(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])sqrt(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])/
                },
                {
                    token: ['support.type'],
                    regex: /ℝ|ℤ|(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])scalar(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])|(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])vector(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])|(?<![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])matrix(?![A-Za-z\p{Ll}\p{Lu}\p{Lo}\d])/
                }

            ]
        };

        this.normalizeRules();
    };

    IheartlaHighlightRules.metaData = {
        fileTypes: ['iheartla'],
        name: 'Iheartla',
        scopeName: 'text.iheartlanotation'
    };


    oop.inherits(IheartlaHighlightRules, TextHighlightRules);

    exports.IheartlaHighlightRules = IheartlaHighlightRules;
});

ace.define("ace/mode/matching_brace_outdent",["require","exports","module","ace/lib/oop","ace/range"], function (require, exports, module) {
"use strict";

var Range = require("../range").Range;

var MatchingBraceOutdent = function() {};

(function() {

    this.checkOutdent = function(line, input) {
        if (! /^\s+$/.test(line))
            return false;

        return /^\s*\}/.test(input);
    };

    this.autoOutdent = function(doc, row) {
        var line = doc.getLine(row);
        var match = line.match(/^(\s*\})/);

        if (!match) return 0;

        var column = match[1].length;
        var openBracePos = doc.findMatchingBracket({row: row, column: column});

        if (!openBracePos || openBracePos.row == row) return 0;

        var indent = this.$getIndent(doc.getLine(openBracePos.row));
        doc.replace(new Range(row, 0, row, column-1), indent);
    };

    this.$getIndent = function(line) {
        return line.match(/^\s*/)[0];
    };

}).call(MatchingBraceOutdent.prototype);

exports.MatchingBraceOutdent = MatchingBraceOutdent;
});


ace.define("ace/mode/folding/ihla",["require","exports","module","ace/lib/oop","ace/range","ace/mode/folding/fold_mode"], function(require, exports, module) {
"use strict";

var oop = require("../../lib/oop");
var Range = require("../../range").Range;
var BaseFoldMode = require("./fold_mode").FoldMode;

var FoldMode = exports.FoldMode = function(commentRegex) {
    if (commentRegex) {
        this.foldingStartMarker = new RegExp(
            this.foldingStartMarker.source.replace(/\|[^|]*?$/, "|" + commentRegex.start)
        );
        this.foldingStopMarker = new RegExp(
            this.foldingStopMarker.source.replace(/\|[^|]*?$/, "|" + commentRegex.end)
        );
    }
};
oop.inherits(FoldMode, BaseFoldMode);

(function() {
    this.foldingStartMarker = /(\[)[^\]]*$/;
    this.foldingStopMarker = /^[^\[]*(\])/;
    this._getFoldWidgetBase = this.getFoldWidget;
    this.getFoldWidget = function(session, foldStyle, row) {
        var line = session.getLine(row);
    
        var fw = this._getFoldWidgetBase(session, foldStyle, row);
        return fw;
    };

    this.getFoldWidgetRange = function(session, foldStyle, row, forceMultiline) {
        var line = session.getLine(row);

        var match = line.match(this.foldingStartMarker);
        if (match) {
            var i = match.index;

            if (match[1])
                return this.openingBracketBlock(session, match[1], row, i);
                
            var range = session.getCommentFoldRange(row, i + match[0].length, 1);
            
            if (range && !range.isMultiLine()) {
                if (forceMultiline) {
                    range = this.getSectionRange(session, row);
                } else if (foldStyle != "all")
                    range = null;
            }
            
            return range;
        }

        if (foldStyle === "markbegin")
            return;

        var match = line.match(this.foldingStopMarker);
        if (match) {
            var i = match.index + match[0].length;

            if (match[1])
                return this.closingBracketBlock(session, match[1], row, i);

            return session.getCommentFoldRange(row, i, -1);
        }
    };
    
    this.getSectionRange = function(session, row) {
        var line = session.getLine(row);
        var startIndent = line.search(/\S/);
        var startRow = row;
        var startColumn = line.length;
        row = row + 1;
        var endRow = row;
        var maxRow = session.getLength();
        while (++row < maxRow) {
            line = session.getLine(row);
            var indent = line.search(/\S/);
            if (indent === -1)
                continue;
            if  (startIndent > indent)
                break;
            var subRange = this.getFoldWidgetRange(session, "all", row);
            
            if (subRange) {
                if (subRange.start.row <= startRow) {
                    break;
                } else if (subRange.isMultiLine()) {
                    row = subRange.end.row;
                } else if (startIndent == indent) {
                    break;
                }
            }
            endRow = row;
        }
        
        return new Range(startRow, startColumn, endRow, session.getLine(endRow).length);
    };

}).call(FoldMode.prototype);

});

ace.define("ace/mode/iheartla",["require","exports","module","ace/lib/oop","ace/mode/text","ace/mode/iheartla_highlight_rules","ace/mode/folding/ihla"], function (require, exports, module) {
    "use strict";

    var oop = require("../lib/oop");
    var TextMode = require("./text").Mode;
    var IheartlaHighlightRules = require("./iheartla_highlight_rules").IheartlaHighlightRules;
    var FoldMode = require("./folding/ihla").FoldMode;
    var MatchingBraceOutdent = require("./matching_brace_outdent").MatchingBraceOutdent;

    var Mode = function () {
        this.HighlightRules = IheartlaHighlightRules;
        this.foldingRules = new FoldMode();
        this.$behaviour = this.$defaultBehaviour;
        this.$outdent = new MatchingBraceOutdent();
    };
    oop.inherits(Mode, TextMode);

    (function () {
        this.lineCommentStart = "%";
        
        this.$id = "ace/mode/iheartla";
        this.snippetFileId = "ace/snippets/iheartla";

        this.getNextLineIndent = function(state, line, tab) {
            var indent = this.$getIndent(line);
            return indent;
        };

        this.checkOutdent = function(state, line, input) {
            return this.$outdent.checkOutdent(line, input);
        };

        this.autoOutdent = function(state, doc, row) {
            this.$outdent.autoOutdent(doc, row);
        };
    }).call(Mode.prototype);

    exports.Mode = Mode;
});                (function() {
                    ace.require(["ace/mode/iheartla"], function(m) {
                        if (typeof module == "object" && typeof exports == "object" && module) {
                            module.exports = m;
                        }
                    });
                })();
            