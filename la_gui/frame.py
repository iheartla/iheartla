# -*- coding: utf-8 -*
import wx
import os
import sys
import threading
import wx.lib.agw.aui as aui

sys.path.append('../')
from la_parser.parser import create_parser_background, parse_in_background, ParserTypeEnum
from la_gui.la_ctrl import LaTextControl
from la_gui.python_ctrl import PyTextControl
from la_gui.cpp_ctrl import CppTextControl
from la_gui.latex_panel import LatexPanel
from la_gui.msg_panel import MsgControl
from la_gui.mid_panel import MidPanel, MidPanelEnum


class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        self.parser_type = ParserTypeEnum.NUMPY
        w, h = wx.DisplaySize()
        wx.Frame.__init__(self, parent, title=title, pos=(w / 4, h / 4))
        self.SetPosition((200, 200))
        self.SetSize((1300, 600))
        # status
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(1)
        # Menu
        menu_file = wx.Menu()
        item_open = menu_file.Append(wx.ID_OPEN, "&Open", " Open a file to edit")
        item_about = menu_file.Append(wx.ID_ABOUT, "&About", " Information about this program")
        menu_run = wx.Menu()
        item_run = menu_run.Append(wx.NewId(), "&Run program", "Let's run LA code")
        menu_bar = wx.MenuBar()
        # languages
        menu_language = wx.Menu()
        py_lang = menu_language.AppendRadioItem(wx.NewId(), "&Python with Numpy")
        cpp_lang = menu_language.AppendRadioItem(wx.NewId(), "&C++ with Eigen")
        cpp_lang.Check(True)
        # view
        menu_view = wx.Menu()
        item_reset = menu_view.Append(wx.NewId(), "&Reset", "Reset all panels")
        # line
        menu_bar.Append(menu_file, "&File")
        menu_bar.Append(menu_run, "&Run")
        menu_bar.Append(menu_language, "&Languages")
        menu_bar.Append(menu_view, "&View")
        self.SetMenuBar(menu_bar)
        self.Bind(wx.EVT_MENU, self.OnOpen, item_open)
        self.Bind(wx.EVT_MENU, self.OnAbout, item_about)
        self.Bind(wx.EVT_MENU, self.OnKeyEnter, item_run)
        self.Bind(wx.EVT_MENU, self.OnClickNumpy, py_lang)
        self.Bind(wx.EVT_MENU, self.OnClickEigen, cpp_lang)
        self.Bind(wx.EVT_MENU, self.OnResetPanel, item_reset)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        # panel
        self.control = LaTextControl(self)
        self.midPanel = MidPanel(self)
        self.latexPanel = LatexPanel(self)
        self.msgPanel = MsgControl(self)
        #
        self.mgr = aui.AuiManager(self)
        self.mgr.SetManagedWindow(self)
        self.aui_info1 = aui.framemanager.AuiPaneInfo().CaptionVisible(False).PaneBorder(False).CloseButton(False).Left()
        self.aui_info1.BestSize(wx.Size(self.GetSize().width/3, self.GetSize().height))
        self.mgr.AddPane(self.control, self.aui_info1)

        self.aui_info2 = aui.framemanager.AuiPaneInfo().CaptionVisible(False).PaneBorder(False).CloseButton(False).Center()
        self.aui_info2.BestSize(wx.Size(self.GetSize().width/3, self.GetSize().height))
        self.mgr.AddPane(self.midPanel, self.aui_info2)

        self.aui_info3 = aui.framemanager.AuiPaneInfo().CaptionVisible(False).PaneBorder(False).CloseButton(False).Right()
        self.aui_info3.BestSize(wx.Size(self.GetSize().width/3, self.GetSize().height))
        self.mgr.AddPane(self.latexPanel, self.aui_info3)
        #
        self.aui_info4 = aui.framemanager.AuiPaneInfo().CaptionVisible(False).PaneBorder(False).CloseButton(
            False).Bottom()
        self.aui_info4.BestSize(wx.Size(self.GetSize().width, self.GetSize().height/4))
        self.mgr.AddPane(self.msgPanel, self.aui_info4)

        self.mgr.Update()
        self.msgPanel.Hide()
        # sizer
        # sizer = wx.BoxSizer(wx.HORIZONTAL)
        # sizer.Add(self.control, 1, wx.EXPAND, 100)
        # sizer.Add(self.midPanel, 1, wx.EXPAND, 100)
        # sizer.Add(self.latexPanel, 1, wx.EXPAND, 100)
        # self.SetSizer(sizer)
        # sizer.Fit(self)
        # hot key
        r_new_id = wx.NewId()
        self.Bind(wx.EVT_MENU, self.OnKeyEnter, id=r_new_id)
        zoom_in_id = wx.NewId()
        self.Bind(wx.EVT_MENU, self.OnZoomIn, id=zoom_in_id)
        zoom_out_id = wx.NewId()
        self.Bind(wx.EVT_MENU, self.OnZoomOut, id=zoom_out_id)
        acc_zoom_out = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('R'), r_new_id), (wx.ACCEL_CTRL, ord('='), zoom_in_id), (wx.ACCEL_CTRL, ord('-'), zoom_out_id)])
        self.SetAcceleratorTable(acc_zoom_out)

        self.Show()
        self.control.SetValue('''B = [ A C ]

where

A: ℝ ^ (4 × 4): a matrix
C: ℝ ^ (4 × 4): a matrix
E: { ℤ × ℤ }''')

        self.Bind(wx.EVT_BUTTON, self.OnButtonClicked)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        create_parser_background()
        self.OnClickEigen(None)  # Eigen default

    def OnButtonClicked(self, e):
        print('frame clicked')

    def SetItemsPos(self):
        w, h = self.GetSize()
        transW, transH = self.translateBtn.GetSize()
        sH = 40
        self.control.SetSize((w - transW) / 2, h - sH)
        self.control.SetPosition((0, 0))
        self.translateBtn.SetPosition(((w - transW) / 2, h / 2 - transH / 2))
        # self.latexPanel.SetSize((w - transW) / 2, h - sH)
        # self.latexPanel.SetPosition(((w + transW) / 2, 0))
        self.pyPanel.SetSize((w - transW) / 2, h - sH)
        self.pyPanel.SetPosition(((w + transW) / 2, 0))

    def UpdateTexPanel(self, tex):
        self.latexPanel.render_content(tex)

    def UpdateMidPanel(self, result):
        self.midPanel.set_value(result[0])
        if result[1] == 0:
            self.statusbar.SetStatusText("Finished", 0)
        else:
            self.statusbar.SetStatusText("Error", 0)

    def OnIdle(self, e):
        pass

    def OnSize(self, e):
        self.Layout()

    def OnAbout(self, e):
        dlg = wx.MessageDialog(self, "LA editor in wxPython", "About LA Editor", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def OnExit(self, e):
        self.Close(True)

    def OnKeyEnter(self, e):
        print('Start compilingr')
        self.OnTranslate(e)

    def OnClickNumpy(self, e):
        self.midPanel.set_panel(MidPanelEnum.PYTHON)
        self.parser_type = ParserTypeEnum.NUMPY

    def OnClickEigen(self, e):
        self.midPanel.set_panel(MidPanelEnum.CPP)
        self.parser_type = ParserTypeEnum.EIGEN

    def OnResetPanel(self, e):
        self.control.SetSize(self.GetSize().width/3, self.GetSize().height)
        self.midPanel.SetSize(self.GetSize().width/3, self.GetSize().height)
        self.midPanel.Move(self.GetSize().width/3, self.GetSize().height)
        self.latexPanel.SetSize(self.GetSize().width/3, self.GetSize().height)
        self.latexPanel.Move(self.GetSize().width*2/3, self.GetSize().height)
        self.mgr.Update()
        self.Layout()

    def OnZoomIn(self, e):
        self.latexPanel.OnZoomIn(e)

    def OnZoomOut(self, e):
        self.latexPanel.OnZoomOut(e)

    def OnTranslate(self, e):
        self.statusbar.SetStatusText("Compiling ...", 0)
        self.Update()
        parse_in_background(self.control.GetValue(), self, self.parser_type)

    def OnOpen(self, e):
        dlg = wx.FileDialog(self, "Choose a file", "", "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()
            f = open(os.path.join(dirname, filename), 'r')
            self.control.SetValue(f.read())
            f.close()
        dlg.Destroy()
