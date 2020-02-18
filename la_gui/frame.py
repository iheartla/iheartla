import wx
import os
import sys

sys.path.append('../')
from la_parser.parser import parse_and_translate


class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        self.dirname = ''
        w, h = wx.DisplaySize()
        wx.Frame.__init__(self, parent, title=title, pos=(w / 4, h / 4), size=(w / 2, h / 2))
        self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(1)

        # Setting up the menu.
        filemenu = wx.Menu()
        menuOpen = filemenu.Append(wx.ID_OPEN, "&Open", " Open a file to edit")
        menuAbout = filemenu.Append(wx.ID_ABOUT, "&About", " Information about this program")
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu, "&File")
        self.SetMenuBar(menuBar)
        self.Bind(wx.EVT_MENU, self.OnOpen, menuOpen)
        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.translateBtn = wx.Button(self, -1, "Compile")
        self.Bind(wx.EVT_BUTTON, self.OnTranslate, self.translateBtn)

        self.staticTxt = wx.StaticText(self, -1)
        self.staticTxt = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.SetItemsPos()
        self.control.SetValue('a b(c(d(b+c)e)f)g')
        # self.control.SetValue('a+b-c; a*b+c; a*(b+c); a b+c; a (((b+c)))')
        # self.control.SetValue('[2;4]')

        self.Show()

    def SetItemsPos(self):
        w, h = self.GetSize()
        transW, transH = self.translateBtn.GetSize()
        sH = 40
        self.control.SetSize((w - transW) / 2, h - sH)
        self.control.SetPosition((0, 0))
        self.translateBtn.SetPosition(((w - transW) / 2, h / 2 - transH / 2))
        self.staticTxt.SetSize((w - transW) / 2, h - sH)
        self.staticTxt.SetPosition(((w + transW) / 2, 0))

    def OnSize(self, e):
        self.SetItemsPos()

    def OnAbout(self, e):
        dlg = wx.MessageDialog(self, "LA editor in wxPython", "About LA Editor", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def OnExit(self, e):
        self.Close(True)

    def OnTranslate(self, e):
        self.statusbar.SetStatusText("Compiling ...", 0)
        self.Update()
        result = parse_and_translate(self.control.GetValue())
        self.staticTxt.SetValue(result[0])
        if result[1] == 0:
            self.statusbar.SetStatusText("Finished", 0)
        else:
            self.statusbar.SetStatusText("Error", 0)

    def OnOpen(self, e):
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            f = open(os.path.join(self.dirname, self.filename), 'r')
            self.control.SetValue(f.read())
            f.close()
        dlg.Destroy()
