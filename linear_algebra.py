from la_gui.frame import *
reload(sys)
sys.setdefaultencoding('utf8')

if __name__ == '__main__':
    app = wx.App(False)
    frame = MainWindow(None, "Linear algebra example")
    app.MainLoop()