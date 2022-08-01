from enum import Enum


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
            ConfMgr.__instance = self
