from la_gui.frame import *

if __name__ == '__main__':
    app = wx.App(False)
    frame = MainWindow(None, "Linear algebra example")
    app.MainLoop()