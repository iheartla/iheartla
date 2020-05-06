import wx
from enum import Enum
from la_gui.python_ctrl import PyTextControl
from la_gui.cpp_ctrl import CppTextControl


class MidPanelEnum(Enum):
    PYTHON = 1
    CPP = 2


class MidPanel(wx.Panel):
    def __init__(self, parent, **kwargs):
        super(MidPanel, self).__init__(parent, **kwargs)
        self.py_ctrl = PyTextControl(self)
        self.cpp_ctrl = CppTextControl(self)
        self.cur_type = MidPanelEnum.PYTHON
        self.panel_dict = {
            MidPanelEnum.PYTHON: self.py_ctrl,
            MidPanelEnum.CPP: self.cpp_ctrl
        }
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Layout()
        self.update_panel()

    def set_value(self, text):
        self.panel_dict[self.cur_type].SetValue(text)

    def set_panel(self, panel_type):
        self.cur_type = panel_type
        self.update_panel()

    def update_panel(self):
        if self.cur_type == MidPanelEnum.PYTHON:
            self.py_ctrl.Show()
            self.cpp_ctrl.Hide()
        elif self.cur_type == MidPanelEnum.CPP:
            self.py_ctrl.Hide()
            self.cpp_ctrl.Show()

    def OnSize(self, e):
        self.py_ctrl.SetPosition((0, 0))
        self.py_ctrl.SetSize((self.GetSize().width, self.GetSize().height))
        self.cpp_ctrl.SetPosition((0, 0))
        self.cpp_ctrl.SetSize((self.GetSize().width, self.GetSize().height))