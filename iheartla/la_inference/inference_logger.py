import logging


class InfLogger(object):
    __instance = None
    @staticmethod
    def getInstance():
        if InfLogger.__instance is None:
            InfLogger()
        return InfLogger.__instance

    def __init__(self):
        if InfLogger.__instance is not None:
            raise Exception("Class LaLogger is a singleton!")
        else:
            self.level = logging.INFO
            self.logger = logging.getLogger("inference")
            self.logger.setLevel(self.level)
            ch = logging.StreamHandler()
            ch.setLevel(self.level)
            # formatter = logging.Formatter('%(asctime)s:%(message)s')
            formatter = logging.Formatter('%(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
            InfLogger.__instance = self


def log_content(content):
    InfLogger.getInstance().logger.info(content)


def log_perm(content):
    InfLogger.getInstance().logger.error(content)


def set_level(level=logging.INFO):
    InfLogger.getInstance().logger.setLevel(level)