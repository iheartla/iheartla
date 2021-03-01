import logging
from enum import Enum


class LoggerTypeEnum(Enum):
    DEFAULT = 0
    LATEX = 1
    NUMPY = 2


class LaLogger(object):
    __instance = None
    @staticmethod
    def getInstance():
        if LaLogger.__instance is None:
            LaLogger()
        return LaLogger.__instance

    def __init__(self):
        if LaLogger.__instance is not None:
            raise Exception("Class LaLogger is a singleton!")
        else:
            self.level = logging.ERROR
            self.logger_dict = {}
            self.name_dict = {
                LoggerTypeEnum.DEFAULT: "la_default",
                LoggerTypeEnum.LATEX: "la_latex",
                LoggerTypeEnum.NUMPY: "la_numpy",
            }
            LaLogger.__instance = self

    def get_logger(self, logger_type):
        if logger_type in self.logger_dict:
            logger = self.logger_dict[logger_type]
        else:
            logger = logging.getLogger(self.name_dict[logger_type])
            logger.setLevel(self.level)
            ch = logging.StreamHandler()
            ch.setLevel(self.level)
            # formatter = logging.Formatter('%(asctime)s:%(message)s')
            formatter = logging.Formatter('%(message)s')
            ch.setFormatter(formatter)
            logger.addHandler(ch)
            self.logger_dict[logger_type] = logger
        return logger

    def log_content(self, content, logger_type=LoggerTypeEnum.DEFAULT):
        self.get_logger(logger_type).debug(content)

    def set_level(self, level):
        self.level = level
        for logger in self.logger_dict.values():
            logger.setLevel(level)
