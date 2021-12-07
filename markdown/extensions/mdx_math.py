# -*- coding: utf-8 -*-

'''
Math extension for Python-Markdown
==================================

Adds support for displaying math formulas using
[MathJax](http://www.mathjax.org/).

Author: 2015-2020, Dmitry Shachnev <mitya57@gmail.com>.
'''

from xml.etree.ElementTree import Element
from markdown.inlinepatterns import InlineProcessor, Pattern
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.util import AtomicString
import cgi


class MathJaxPattern(Pattern):

    def __init__(self, md):
        Pattern.__init__(self, r'(?<!\\)(\$\$?)(.+?)\2', md)

    def handleMatch(self, m):
        # Pass the math code through, unmodified except for basic entity substitutions.
        # Stored in htmlStash so it doesn't get further processed by Markdown.
        # text = cgi.escape(m.group(2) + m.group(3) + m.group(2)) # & sym
        text = m.group(2) + m.group(3) + m.group(2)
        return self.markdown.htmlStash.store(text)

class MathJaxExtension(Extension):
    def extendMarkdown(self, md):
        # Needs to come before escape matching because \ is pretty important in LaTeX
        md.inlinePatterns.add('mathjax', MathJaxPattern(md), '<escape')

def makeExtension(**kwargs):  # pragma: no cover
    return MathJaxExtension(**kwargs)