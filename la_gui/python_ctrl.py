import wx
import wx.stc

BACKGROUND_COLOR = "#2B2B2B"
NUMBER_FORE_COLOR = "#A9B7C6"


class PyTextControl(wx.stc.StyledTextCtrl):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetFont(wx.Font(14, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=u'Monaco'))
        self.SetLexer(wx.stc.STC_LEX_PYTHON)
        self.IndicatorSetStyle(2, wx.stc.STC_INDIC_PLAIN)
        self.IndicatorSetForeground(0, wx.RED)

        self.SetKeyWords(0, "if")
        self.SetKeyWords(1, "if")

        self.SetProperty("styling.within.preprocessor", "1")
        self.SetProperty("fold.comment", "1")
        self.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        self.SetWindowStyle(self.GetWindowStyle() | wx.DOUBLE_BORDER)
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, "size:15,face:Courier New")
        self.SetWrapMode(wx.stc.STC_WRAP_WORD)
        self.SetMarginLeft(0)

        self.MarkerSetBackgroundSelected(1, wx.Colour(0xFF0000))
        self.MarkerEnableHighlight(True)

        # line number
        self.SetMarginCursor(0, wx.stc.STC_CURSORNORMAL)
        self.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        self.SetMarginSensitive(0, True)
        self.SetMarginWidth(1, 24)

        # caret setting
        self.SetCaretForeground(wx.Colour(0xBBBBBB))
        self.SetCaretLineVisible(True)
        self.SetCaretLineBackground(wx.Colour(0x323232))
        self.SetSelBackground(True, wx.Colour(0x43474A))

        self.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_STYLE_LINENUMBER, "#313335")
        self.StyleSetForeground(wx.stc.STC_STYLE_LINENUMBER, "#606366")

        # background
        self.StyleSetBackground(wx.stc.STC_P_DEFAULT, BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_COMMENTLINE, BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_NUMBER, BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_STRING, BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_CHARACTER, BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_WORD, BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_TRIPLE, BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_TRIPLEDOUBLE, BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_CLASSNAME, BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_DEFNAME, BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_OPERATOR, BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_IDENTIFIER, BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_COMMENTBLOCK, BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_STRINGEOL, BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_WORD2, BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_P_DECORATOR, BACKGROUND_COLOR)

        # foreground
        self.StyleSetForeground(wx.stc.STC_P_DEFAULT, NUMBER_FORE_COLOR)
        self.StyleSetForeground(wx.stc.STC_P_COMMENTLINE, NUMBER_FORE_COLOR)
        self.StyleSetForeground(wx.stc.STC_P_NUMBER, NUMBER_FORE_COLOR)
        self.StyleSetForeground(wx.stc.STC_P_STRING, NUMBER_FORE_COLOR)
        self.StyleSetForeground(wx.stc.STC_P_CHARACTER, NUMBER_FORE_COLOR)
        self.StyleSetForeground(wx.stc.STC_P_WORD, NUMBER_FORE_COLOR)
        self.StyleSetForeground(wx.stc.STC_P_TRIPLE, NUMBER_FORE_COLOR)
        self.StyleSetForeground(wx.stc.STC_P_TRIPLEDOUBLE, NUMBER_FORE_COLOR)
        self.StyleSetForeground(wx.stc.STC_P_CLASSNAME, NUMBER_FORE_COLOR)
        self.StyleSetForeground(wx.stc.STC_P_DEFNAME, NUMBER_FORE_COLOR)
        self.StyleSetForeground(wx.stc.STC_P_OPERATOR, NUMBER_FORE_COLOR)
        self.StyleSetForeground(wx.stc.STC_P_IDENTIFIER, NUMBER_FORE_COLOR)
        self.StyleSetForeground(wx.stc.STC_P_COMMENTBLOCK, NUMBER_FORE_COLOR)
        self.StyleSetForeground(wx.stc.STC_P_STRINGEOL, NUMBER_FORE_COLOR)
        self.StyleSetForeground(wx.stc.STC_P_WORD2, NUMBER_FORE_COLOR)
        self.StyleSetForeground(wx.stc.STC_P_DECORATOR, NUMBER_FORE_COLOR)