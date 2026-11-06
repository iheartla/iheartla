from .la_helper import *
from .la_logger import *
from .la_package import *
from ..la_local_parsers.init_parser import grammarinitParser, grammarinitModelBuilderSemantics
from ..la_local_parsers.default_parser import grammardefaultModelBuilderSemantics
from .configured_parser import ConfiguredParser


class ParserManager(object):
    """The two parsers, both TatSu's output for the EBNF in la_grammar/ (regenerated with
    `python -m iheartla.la_grammar.update_parsers`): the init parser (the simplified grammar),
    which collects a program's declarations, and the default parser (the full grammar),
    which is configured with them before each parse (ConfiguredParser)."""
    __instance = None
    @staticmethod
    def getInstance(grammar_dir=''):
        if ParserManager.__instance is None:
            ParserManager(grammar_dir)
        return ParserManager.__instance

    def __init__(self, grammar_dir):
        if ParserManager.__instance is not None:
            raise Exception("Class ParserManager is a singleton!")
        self.init_parser = grammarinitParser(semantics=grammarinitModelBuilderSemantics())
        self.default_parser = ConfiguredParser(semantics=grammardefaultModelBuilderSemantics())
        # disable # as comment symbol
        # https://github.com/neogeny/TatSu/issues/293
        # https://github.com/neogeny/TatSu/issues/249
        for parser in (self.init_parser, self.default_parser):
            config = getattr(parser, "config", None)
            if config:
                # Work around BC break in Tatsu 5.7
                config.comments_re = None
                config.eol_comments_re = None
        ParserManager.__instance = self

    def get_parser(self, key, grammar='', extra_dict={}):
        """The init parser for key 'init'; otherwise the default parser, configured by
        extra_dict (the grammar argument is unused: both parsers are pregenerated)."""
        if key == 'init':
            return self.init_parser
        self.modify_default_parser(extra_dict)
        return self.default_parser

    def modify_default_parser(self, extra_dict):
        self.default_parser.new_id_list = []
        self.default_parser.new_func_list = []
        self.default_parser.builtin_list = []
        self.default_parser.conversion_dict = {}
        self.default_parser.const_e = False
        if "ids" in extra_dict:
            self.default_parser.new_id_list = extra_dict["ids"]
            la_debug("Modify default parser, ids:{}".format(extra_dict["ids"]))
        if 'funcs' in extra_dict:
            self.default_parser.new_func_list = extra_dict["funcs"]
            la_debug("Modify default parser, funcs:{}".format(extra_dict["funcs"]))
        if 'pkg' in extra_dict:
            funcs_list = extra_dict["pkg"]
            if 'e' in funcs_list:
                self.default_parser.const_e = True
                funcs_list.remove('e')
            self.default_parser.builtin_list = funcs_list
            la_debug("Modify default parser, pkg:{}".format(extra_dict["pkg"]))
        if 'rename' in extra_dict:
            self.default_parser.conversion_dict = extra_dict["rename"]
            la_debug("Modify default parser, rename:{}".format(extra_dict["rename"]))
