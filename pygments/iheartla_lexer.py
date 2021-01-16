# Plugin-able lexer for pygments
# See README for usage

from pygments.lexer import ExtendedRegexLexer, bygroups, words, include
from pygments.token import *

import regex

class CustomLexer(ExtendedRegexLexer):
    name = "A Lexer for IHeartLA"
    functions = [
        'trace',
        'tr',
        'vec',
        'diag',
        'eig',
        'conj',
        'Re',
        'Im',
        'inv',
        'det',
        'svd',
        'rank',
        'null',
        'orth',
        'qr',
        'sum',
        '∑',
        'min',
        'max',
        'argmin',
        'argmax',
        'sin',
        'asin',
        'arcsin',
        'cos',
        'acos',
        'arccos',
        'tanh',
        'cot',
        'sec',
        'csc',
        'atan2',
        'exp',
        'log',
        'ln',
        'sqrt'
    ]
    word_operators = [
        'for',
        'if',
        'else'
    ]

    def ident_callback(lexer, match, ctx):
        m = regex.match(r'[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*', ctx.text[ctx.pos:ctx.end])
        if m:
            yield ctx.pos+m.start(), Name.Variable, m[0]
            ctx.pos += m.end()
            return
        else:
            print("Unable to treat %s as identifier\n" % match)
            raise
            return


    tokens = {
        'root': [
            (r'where|given', Keyword.Namespace),
            (r'from', Keyword.Namespace, 'import_state'),
            (r'\s=\s', Keyword.Declaration), # a bit of a stretch, but it should be colored differently
            (r'->|⁻¹|\|\||[\+\-±⋅×/÷\^_><ᵀ∈‖\|\*]', Operator), # non-word operators
            (words(word_operators), Operator.Word),
            (r':', Keyword, 'where_rhs'),
            (words(functions), Name.Function),
            (r'[()\[\],{};]', Punctuation),
            (r'ℝ|ℤ', Name.Builtin),
            (r'(`)(.*?)(`)', bygroups(Comment, Name.Variable, Comment)), # make backticks separate color
            (r'[\u2070\u00B9\u00B2\u00B3\u2074-\u2079]|[\u2080-\u2089]|\d+', Literal.Number),
            (r'\w', ident_callback),
            (r'\s+?', Text),
            (r'.*\n', Text)
        ],
        'where_rhs': [
            (r'\s*:', Keyword, 'comment'),
            (r'$', Generic, '#pop'),
            include('root')
        ],
        'comment': [
            (r'.*$', Comment, '#pop:2')
        ],
        'import_state': [
            (r'([^:]+?)(\s*:\s*)(.*$)', bygroups(Name.Class, Keyword, Name.Function), '#pop')
        ]
    }
