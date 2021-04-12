import wx
import wx.stc as stc
from ..la_gui import base_ctrl as bc


class MatlabTextControl(bc.BaseTextControl):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetLexer(wx.stc.STC_LEX_MATLAB)
        kwlist = u"break case catch classdef continue else elseif end for function global if otherwise parfor " \
                 u"persistent return spmd switch try while "
        self.SetKeyWords(0, kwlist)
        # background
        self.StyleSetBackground(wx.stc.STC_MATLAB_DEFAULT, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_MATLAB_COMMAND, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_MATLAB_COMMENT, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_MATLAB_DOUBLEQUOTESTRING, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_MATLAB_IDENTIFIER, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_MATLAB_KEYWORD, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_MATLAB_NUMBER, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_MATLAB_OPERATOR, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_MATLAB_STRING, bc.BACKGROUND_COLOR)

        # Default
        self.StyleSetSpec(stc.STC_MATLAB_DEFAULT, "fore:#A9B7C6," + self.fonts)
        # Number
        self.StyleSetSpec(stc.STC_MATLAB_NUMBER, "fore:#9686F5," + self.fonts)
        # Keyword
        self.StyleSetSpec(stc.STC_MATLAB_KEYWORD, "fore:#FC5FA3,bold," + self.fonts)
        # String
        self.StyleSetSpec(stc.STC_MATLAB_STRING, "fore:#FC6A5D," + self.fonts)
        # Identifier
        self.StyleSetSpec(stc.STC_MATLAB_IDENTIFIER, "fore:#A9B7C6,bold," + self.fonts)
        # Operator
        self.StyleSetSpec(stc.STC_MATLAB_OPERATOR, "fore:#A9B7C6,bold," + self.fonts)

        self.StyleSetSpec(stc.STC_MATLAB_COMMAND, "fore:#FD8F3F," + self.fonts)
        self.StyleSetSpec(stc.STC_MATLAB_COMMENT, "fore:#6C7986," + self.fonts)
        self.StyleSetSpec(stc.STC_MATLAB_DOUBLEQUOTESTRING, "fore:#629755," + self.fonts)