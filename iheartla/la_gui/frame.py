# -*- coding: utf-8 -*
import wx
import os
import sys
import time
import threading
import wx.lib.agw.aui as aui
from enum import Enum


from ..la_parser.parser import create_parser_background, parse_in_background, ParserTypeEnum, clean_parsers
from ..la_gui.la_ctrl import LaTextControl
from ..la_gui.python_ctrl import PyTextControl
from ..la_gui.cpp_ctrl import CppTextControl
from ..la_gui.latex_panel import LatexPanel
from ..la_gui.msg_panel import MsgControl
from ..la_gui.mid_panel import MidPanel, MidPanelEnum
from ..la_tools.la_msg import *


class FileType(Enum):
    INVALID = -1
    LA = 0
    NUMPY = 1
    EIGEN = 2
    LATEX = 3
    GLSL = 4


class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        self.cur_timestamp = 0
        self.cur_la_file = None
        self.cur_la_code = ''
        self.timer = wx.Timer
        self.parser_type = ParserTypeEnum.NUMPY
        w, h = wx.DisplaySize()
        wx.Frame.__init__(self, parent, title=title, pos=(w / 4, h / 4))
        self.SetPosition((0, 50))
        self.SetSize((1280, 600))
        # status
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(2)
        self.statusbar.SetStatusStyles([wx.SB_SUNKEN, wx.SB_RAISED])
        # Menu
        menu_file = wx.Menu()
        item_open = menu_file.Append(wx.ID_OPEN, "&Open LA file\tCTRL+O", " Open a file to edit")
        item_save_default_la = menu_file.Append(wx.NewId(), "&Save LA\tCTRL+S", " Save LA code")
        item_save_la = menu_file.Append(wx.NewId(), "&Save LA As...", " Save LA code to a file")
        item_save_python = menu_file.Append(wx.NewId(), "&Save Numpy As...", " Save Numpy code to a file")
        item_save_eigen = menu_file.Append(wx.NewId(), "&Save Eigen As...", " Save Eigen code to a file")
        item_save_glsl = menu_file.Append(wx.NewId(), "&Save GLSL As...", " Save GLSL code to a file")
        item_save_tex = menu_file.Append(wx.NewId(), "&Save Latex As...", " Save Latex code to a file")
        item_about = menu_file.Append(wx.ID_ABOUT, "&About", " Information about this program")
        menu_run = wx.Menu()
        item_run = menu_run.Append(wx.NewId(), "&Run program\tCTRL+R", "Let's run LA code")
        menu_bar = wx.MenuBar()
        # edit
        self.menu_edit = wx.Menu()
        self.undo_item = self.menu_edit.Append(wx.NewId(), "&Undo\tCTRL+Z")
        self.redo_item = self.menu_edit.Append(wx.NewId(), "&Redo\tCTRL+SHIFT+Z")
        self.cut_item = self.menu_edit.Append(wx.NewId(), "&Cut\tCTRL+X")
        self.copy_item = self.menu_edit.Append(wx.NewId(), "&Copy\tCTRL+C")
        self.paste_item = self.menu_edit.Append(wx.NewId(), "&Paste\tCTRL+V")
        self.Bind(wx.EVT_MENU_OPEN, self.OnMenuOpen)
        # languages
        menu_language = wx.Menu()
        py_lang = menu_language.AppendRadioItem(wx.NewId(), "&Python with NumPy")
        cpp_lang = menu_language.AppendRadioItem(wx.NewId(), "&C++ with Eigen")
        glsl_lang = menu_language.AppendRadioItem(wx.NewId(), "&GLSL frag shader")
        mathjax_lang = menu_language.AppendRadioItem(wx.NewId(), "&MathJax")
        matlab_lang = menu_language.AppendRadioItem(wx.NewId(), "&Matlab")
        mathml_lang = menu_language.AppendRadioItem(wx.NewId(), "&MathML")
        cpp_lang.Check(True)
        # view
        menu_view = wx.Menu()
        item_reset = menu_view.Append(wx.NewId(), "&Reset", "Reset all panels")
        # tools
        tools_view = wx.Menu()
        item_clean = tools_view.Append(wx.NewId(), "&Clean cache", "Delete all cached parsers")
        item_switch = tools_view.Append(wx.NewId(), "&Switch Latex panel", "Switch between source code and pdf")
        # line
        menu_bar.Append(menu_file, "&File")
        menu_bar.Append(self.menu_edit, "Edit")
        menu_bar.Append(menu_run, "&Run")
        menu_bar.Append(menu_language, "&Languages")
        menu_bar.Append(menu_view, "&View")
        menu_bar.Append(tools_view, "&Tools")
        self.SetMenuBar(menu_bar)
        # File
        self.Bind(wx.EVT_MENU, self.OnOpen, item_open)
        self.Bind(wx.EVT_MENU, self.OnSaveLADefault, item_save_default_la)
        self.Bind(wx.EVT_MENU, self.OnSaveLA, item_save_la)
        self.Bind(wx.EVT_MENU, self.OnSavePython, item_save_python)
        self.Bind(wx.EVT_MENU, self.OnSaveEigen, item_save_eigen)
        self.Bind(wx.EVT_MENU, self.OnSaveGLSL, item_save_glsl)
        self.Bind(wx.EVT_MENU, self.OnSaveTex, item_save_tex)
        # Edit
        self.Bind(wx.EVT_MENU, self.OnUndo, self.undo_item)
        self.Bind(wx.EVT_MENU, self.OnRedo, self.redo_item)
        self.Bind(wx.EVT_MENU, self.OnCut, self.cut_item)
        self.Bind(wx.EVT_MENU, self.OnCopy, self.copy_item)
        self.Bind(wx.EVT_MENU, self.OnPaste, self.paste_item)
        #
        self.Bind(wx.EVT_MENU, self.OnAbout, item_about)
        self.Bind(wx.EVT_MENU, self.OnKeyEnter, item_run)
        self.Bind(wx.EVT_MENU, self.OnClickNumpy, py_lang)
        self.Bind(wx.EVT_MENU, self.OnClickEigen, cpp_lang)
        self.Bind(wx.EVT_MENU, self.OnClickGLSL, glsl_lang)
        self.Bind(wx.EVT_MENU, self.OnClickMathjax, mathjax_lang)
        self.Bind(wx.EVT_MENU, self.OnClickMatlab, matlab_lang)
        self.Bind(wx.EVT_MENU, self.OnClickMathml, mathml_lang)
        self.Bind(wx.EVT_MENU, self.OnResetPanel, item_reset)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        # tools
        self.Bind(wx.EVT_MENU, self.OnCleanCache, item_clean)
        self.Bind(wx.EVT_MENU, self.OnSwitchPanel, item_switch)
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
        self.aui_info4.BestSize(wx.Size(self.GetSize().width, self.GetSize().height/6))
        self.mgr.AddPane(self.msgPanel, self.aui_info4)

        self.mgr.Update()
        #self.msgPanel.Hide()
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
        save_id = wx.NewId()
        self.Bind(wx.EVT_MENU, self.OnSaveLADefault, id=save_id)
        zoom_in_id = wx.NewId()
        self.Bind(wx.EVT_MENU, self.OnZoomIn, id=zoom_in_id)
        zoom_out_id = wx.NewId()
        self.Bind(wx.EVT_MENU, self.OnZoomOut, id=zoom_out_id)
        acc_zoom_out = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('R'), r_new_id),
                                            (wx.ACCEL_CTRL, ord('O'), wx.ID_OPEN),
                                            (wx.ACCEL_CTRL, ord('S'), save_id),
                                            (wx.ACCEL_CTRL, ord('='), zoom_in_id),
                                            (wx.ACCEL_CTRL, ord('-'), zoom_out_id)])
        self.SetAcceleratorTable(acc_zoom_out)

        self.Show()
        self.control.SetValue('''B = [ A C ]

where

A: ℝ ^ (4 × 4): a matrix
C: ℝ ^ (4 × 4): a matrix
E: { ℤ × ℤ }''')

        self.Bind(wx.EVT_BUTTON, self.OnButtonClicked)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        #
        self.control.Bind(wx.stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
        self.msgPanel.Bind(wx.stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
        self.latexPanel.latex_ctrl.Bind(wx.stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
        self.midPanel.py_ctrl.Bind(wx.stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
        self.midPanel.cpp_ctrl.Bind(wx.stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
        self.control.IndicatorSetStyle(0, wx.stc.STC_INDIC_POINTCHARACTER)
        self.error_pos = 0

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

    def UpdateTexPanel(self, tex, show_pdf):
        self.latexPanel.render_content(tex, show_pdf)

    def UpdateMidPanel(self, result):
        if result[1] == 0:
            self.midPanel.set_value(result[0])
            self.statusbar.SetStatusText("Finished", 0)
            self.set_msg("{}Compile succeeded\n".format(self.msgPanel.GetValue()))
            self.update_indicator(False)
        else:
            if self.msgPanel.GetValue() == '':
                msg = result[0]
            else:
                msg = "{}{}".format(self.msgPanel.GetValue(), result[0])
            self.set_msg(msg)
            self.statusbar.SetStatusText("Error", 0)
            self.update_indicator(True, self.control.FindColumn(LaMsg.getInstance().cur_line, LaMsg.getInstance().cur_col))

    def update_indicator(self, on, pos=0):
        self.control.IndicatorClearRange(0, len(self.control.GetValue()))
        if on:
            self.error_pos = pos
            self.control.IndicatorFillRange(pos, 1)

    def set_msg(self, msg):
        self.msgPanel.SetEditable(True)
        self.msgPanel.SetValue(msg)
        self.msgPanel.ScrollToEnd()
        self.msgPanel.SetEditable(False)

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
        print('Start compiling')
        self.OnTranslate(e)

    def OnClickNumpy(self, e):
        self.midPanel.set_panel(MidPanelEnum.PYTHON)
        self.parser_type = ParserTypeEnum.NUMPY

    def OnClickEigen(self, e):
        self.midPanel.set_panel(MidPanelEnum.CPP)
        self.parser_type = ParserTypeEnum.EIGEN

    def OnClickMathjax(self, e):
        self.midPanel.set_panel(MidPanelEnum.MATHJAX)
        self.parser_type = ParserTypeEnum.MATHJAX

    def OnClickMatlab(self, e):
        self.midPanel.set_panel(MidPanelEnum.MATLAB)
        self.parser_type = ParserTypeEnum.MATLAB

    def OnClickMathml(self, e):
        self.midPanel.set_panel(MidPanelEnum.MATHML)
        self.parser_type = ParserTypeEnum.MATHML

    def OnClickGLSL(self, e):
        self.midPanel.set_panel(MidPanelEnum.GLSL)
        self.parser_type = ParserTypeEnum.GLSL

    def OnCleanCache(self, e):
        clean_parsers()

    def OnSwitchPanel(self, e):
        self.latexPanel.switch_panels()

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
        parse_in_background(self.control.GetValue(), self, self.parser_type, self.cur_la_file)

    def OnOpen(self, e):
        dlg = wx.FileDialog(self, "Choose LA source file", "", "", "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.load_la_content(dlg.GetPath())
        dlg.Destroy()

    def OnSave(self, e):
        print(self.control.Active())
        self.OnSaveLA(e)

    def OnSaveLADefault(self, e):
        if self.cur_la_file is None:
            self.save_content(FileType.LA)
        else:
            try:
                content = self.control.GetValue()
                file = open(self.cur_la_file, 'w')
                file.write(content)
                file.close()
                self.cur_timestamp = os.path.getmtime(self.cur_la_file)
                self.cur_la_code = content
                self.statusbar.SetStatusText("Saved Successfully", 0)
            except IOError:
                print("IO Error!")
                self.statusbar.SetStatusText("Fail to save", 0)

    def OnSaveLA(self, e):
        self.save_content(FileType.LA)

    def OnSavePython(self, e):
        self.save_content(FileType.NUMPY)

    def OnSaveEigen(self, e):
        self.save_content(FileType.EIGEN)

    def OnSaveGLSL(self, e):
        self.save_content(FileType.GLSL)

    def OnSaveTex(self, e):
        self.save_content(FileType.LATEX)

    def OnShowEdit(self, e):
        self.update_edit_menu_item()

    def OnUndo(self, e):
        self.control.Undo()

    def OnRedo(self, e):
        self.control.Redo()

    def OnCut(self, e):
        self.control.Cut()

    def OnCopy(self, e):
        self.control.Copy()

    def OnPaste(self, e):
        self.control.Paste()

    def OnMenuOpen(self, e):
        if e.GetMenu() == self.menu_edit:
            self.update_edit_menu_item()

    def OnUpdateUI(self, e):
        self.OnPositionChanged(e.EventObject.GetCurrentLine(), e.EventObject.GetColumn(e.EventObject.GetInsertionPoint()))

    def OnPositionChanged(self, line, col):
        self.statusbar.SetStatusText("{}:{}".format(line+1, col+1), 1)

    def update_edit_menu_item(self):
        self.undo_item.Enable(self.control.CanUndo())
        self.redo_item.Enable(self.control.CanRedo())
        self.cut_item.Enable(self.control.CanCut())
        self.copy_item.Enable(self.control.CanCopy())
        self.paste_item.Enable(self.control.CanPaste())

    def load_la_content(self, file_name):
        self.cur_la_file = file_name
        self.cur_timestamp = os.path.getmtime(self.cur_la_file)
        f = open(file_name, 'r', encoding="utf8")
        self.cur_la_code = f.read()
        f.close()
        self.control.SetValue(self.cur_la_code)
        # compile after load
        self.OnTranslate(None)
        # start timer
        self.on_timer()

    def on_timer(self):
        self.refresh_la_file()
        wx.CallLater(5000, self.on_timer)

    def refresh_la_file(self):
        if self.control.GetValue() == self.cur_la_code:  # not modified in editor
            disk_time = os.path.getmtime(self.cur_la_file)
            if disk_time > self.cur_timestamp:
                self.load_la_content(self.cur_la_file)

    def save_content(self, file_type):
        if file_type == FileType.LA:
            tips = "Save LA code"
        elif file_type == FileType.EIGEN:
            tips = "Save Eigen code"
        elif file_type == FileType.GLSL:
            tips = "Save GLSL code"
        elif file_type == FileType.NUMPY:
            tips = "Save Numpy code"
        elif file_type == FileType.LATEX:
            tips = "Save Latex code"
        with wx.FileDialog(self, tips,
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            if file_type == FileType.LA:
                content = self.control.GetValue()
            elif file_type == FileType.LATEX:
                content = self.latexPanel.get_content()
            else:
                content = self.midPanel.get_content()
            if content == "":
                self.statusbar.SetStatusText("Blank content", 0)
                return
            try:
                with open(pathname, 'w') as file:
                    file.write(content)
                    file.close()
                    self.statusbar.SetStatusText("Saved Successfully", 0)
                    if file_type == FileType.LA:
                        print("la file")
                        self.cur_la_file = pathname
                        self.cur_timestamp = os.path.getmtime(pathname)
                        self.cur_la_code = content
            except IOError:
                print("Cannot save current data in file '%s'." % pathname)
                self.statusbar.SetStatusText("Fail to save", 0)


