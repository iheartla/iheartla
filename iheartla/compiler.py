from .la_parser.parser import compile_la_file, compile_la_content, ParserTypeEnum


def show_gui():
    from .la_gui.frame import wx, MainWindow
    app = wx.App(False)
    MainWindow(None, "H❤️rtLang")
    app.MainLoop()


def compile(content):
    return compile_la_content(content)