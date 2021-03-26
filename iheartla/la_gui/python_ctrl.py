import wx
import wx.stc as stc
import keyword
from ..la_gui import base_ctrl as bc


class PyTextControl(bc.BaseTextControl):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetLexer(wx.stc.STC_LEX_PYTHON)
        kwlist = u" ".join(keyword.kwlist)
        self.SetKeyWords(0, kwlist)
        # background
        self.StyleSetBackground(wx.stc.STC_P_DEFAULT, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_COMMENTLINE, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_NUMBER, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_STRING, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_CHARACTER, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_WORD, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_TRIPLE, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_TRIPLEDOUBLE, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_CLASSNAME, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_DEFNAME, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_OPERATOR, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_IDENTIFIER, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_COMMENTBLOCK, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_STRINGEOL, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_WORD2, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_DECORATOR, bc.BACKGROUND_COLOR)

        # Default
        self.StyleSetSpec(stc.STC_P_DEFAULT, "fore:#A9B7C6," + self.fonts)
        # Comments
        self.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:#629755," + self.fonts)
        # Number
        self.StyleSetSpec(stc.STC_P_NUMBER, "fore:#6897BB," + self.fonts)
        # String
        self.StyleSetSpec(stc.STC_P_STRING, "fore:#6A8759," + self.fonts)
        # Single quoted string
        self.StyleSetSpec(stc.STC_P_CHARACTER, "fore:#6A8759," + self.fonts)
        # Keyword
        self.StyleSetSpec(stc.STC_P_WORD, "fore:#CC7832,bold," + self.fonts)
        # Triple quotes
        self.StyleSetSpec(stc.STC_P_TRIPLE, "fore:#629755," + self.fonts)
        # Triple double quotes
        self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:#629755," + self.fonts)
        # Class name definition
        self.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:#A9B7C6,bold," + self.fonts)
        # Function or method name definition
        self.StyleSetSpec(stc.STC_P_DEFNAME, "fore:#FFC66D,bold," + self.fonts)
        # Operators
        self.StyleSetSpec(stc.STC_P_OPERATOR, "fore:#A9B7C6,bold," + self.fonts)
        # Identifiers
        self.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:#A9B7C6,bold," + self.fonts)
        # Comment-blocks
        self.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "fore:#629755," + self.fonts)
        # End of line where string is not closed
        self.StyleSetSpec(stc.STC_P_STRINGEOL, "fore:#629755,eol," + self.fonts)

        # event
        self.Bind(wx.stc.EVT_STC_MODIFIED, self.OnModified)
        self.Bind(wx.stc.EVT_STC_ROMODIFYATTEMPT, self.OnRomodifyAttempt)

    def OnModified(self, evt):
        pass

    def OnRomodifyAttempt(self, evt):
        pass