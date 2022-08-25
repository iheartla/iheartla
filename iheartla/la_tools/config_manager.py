from enum import Enum
import os.path
from pathlib import Path
from ..la_tools.la_helper import *
from ..la_tools.parser_manager import ParserManager
from ..de_companion.config_walker import ConfigWalker


class ConfMgr(object):
    __instance = None
    @staticmethod
    def getInstance():
        if ConfMgr.__instance is None:
            ConfMgr()
        return ConfMgr.__instance

    def __init__(self):
        if ConfMgr.__instance is not None:
            raise Exception("Class ConfMgr is a singleton!")
        else:
            self.path = os.getcwd()  # path for iheartla source file
            self.source_file = 'iheartla'
            self.conf_file = None
            self.parser = ParserManager.getInstance().get_parser('config', '')
            self.walker = ConfigWalker()
            self.has_de = False
            ConfMgr.__instance = self

    def reset(self):
        self.has_de = False
        self.walker.reset()

    def set_source(self, source):
        p = Path(source)
        base_name = os.path.basename(p)
        self.source_file = os.path.splitext(base_name)[0]
        self.path = os.path.dirname(p)

    def set_conf(self, conf):
        self.conf_file = conf

    def get_conf_content(self):
        content = None
        if self.conf_file:
            content = read_from_file(self.conf_file)
        else:
            src = "{}/{}.conf".format(self.path, self.source_file)
            if os.path.exists(src):
                content = read_from_file(src)
        return content

    def parse(self, de_light_walker):
        self.has_de = True
        content = self.get_conf_content()
        if content:
            model = self.parser.parse(content, parseinfo=True)
            self.walker.set_env(de_light_walker)
            start_node = self.walker.walk(model)
            print(content)


