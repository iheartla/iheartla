import wx
from enum import Enum
from ..la_gui.python_ctrl import PyTextControl
from ..la_gui.cpp_ctrl import CppTextControl
from ..la_gui.glsl_ctrl import GLSLTextControl
from ..la_gui.mat_ctrl import MatlabTextControl
from ..la_gui.latex_panel import LatexControl


class MidPanelEnum(Enum):
    PYTHON = 1
    CPP = 2
    MATHJAX = 3
    MATLAB = 4
    MATHML = 5
    GLSL = 6


class MidPanel(wx.Panel):
    def __init__(self, parent, **kwargs):
        super(MidPanel, self).__init__(parent, **kwargs)
        self.py_ctrl = PyTextControl(self)
        self.cpp_ctrl = CppTextControl(self)
        self.glsl_ctrl = GLSLTextControl(self)
        self.jax_ctrl = LatexControl(self)
        self.mat_ctrl = MatlabTextControl(self)
        self.mathml_ctrl = LatexControl(self)
        self.cur_type = MidPanelEnum.PYTHON
        self.panel_dict = {
            MidPanelEnum.PYTHON: self.py_ctrl,
            MidPanelEnum.CPP: self.cpp_ctrl,
            MidPanelEnum.GLSL: self.glsl_ctrl,
            MidPanelEnum.MATHJAX: self.jax_ctrl,
            MidPanelEnum.MATLAB: self.mat_ctrl,
            MidPanelEnum.MATHML: self.mathml_ctrl,
        }
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Layout()
        self.update_panel()

    def set_value(self, text):
        self.panel_dict[self.cur_type].SetEditable(True)
        self.panel_dict[self.cur_type].SetValue(text)
        self.panel_dict[self.cur_type].SetEditable(False)

    def set_panel(self, panel_type):
        self.cur_type = panel_type
        self.update_panel()

    def get_content(self, panel_type):
        return self.panel_dict[self.cur_type].GetValue()

    def update_panel(self):
        self.py_ctrl.Hide()
        self.cpp_ctrl.Hide()
        self.jax_ctrl.Hide()
        self.mat_ctrl.Hide()
        self.mathml_ctrl.Hide()
        if self.cur_type == MidPanelEnum.PYTHON:
            self.py_ctrl.Show()
        elif self.cur_type == MidPanelEnum.CPP:
            self.cpp_ctrl.Show()
        elif self.cur_type == MidPanelEnum.GLSL:
            self.glsl_ctrl.Show()
        elif self.cur_type == MidPanelEnum.MATHJAX:
            self.jax_ctrl.Show()
        elif self.cur_type == MidPanelEnum.MATLAB:
            self.mat_ctrl.Show()
        elif self.cur_type == MidPanelEnum.MATHML:
            self.mathml_ctrl.Show()

    def OnSize(self, e):
        self.py_ctrl.SetPosition((0, 0))
        self.py_ctrl.SetSize((self.GetSize().width, self.GetSize().height))
        self.cpp_ctrl.SetPosition((0, 0))
        self.cpp_ctrl.SetSize((self.GetSize().width, self.GetSize().height))
        self.glsl_ctrl.SetPosition((0, 0))
        self.glsl_ctrl.SetSize((self.GetSize().width, self.GetSize().height))
        self.jax_ctrl.SetPosition((0, 0))
        self.jax_ctrl.SetSize((self.GetSize().width, self.GetSize().height))
        self.mat_ctrl.SetPosition((0, 0))
        self.mat_ctrl.SetSize((self.GetSize().width, self.GetSize().height))
        self.mathml_ctrl.SetPosition((0, 0))
        self.mathml_ctrl.SetSize((self.GetSize().width, self.GetSize().height))