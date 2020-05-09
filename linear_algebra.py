from la_gui.frame import *
from la_tools.la_logger import LaLogger, LoggerTypeEnum
import logging

if __name__ == '__main__':
    LaLogger.getInstance().set_level(logging.INFO)
    app = wx.App(False)
    frame = MainWindow(None, "I heart LA")
    app.MainLoop()