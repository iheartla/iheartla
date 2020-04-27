import wx
import wx.stc as stc
import keyword

BACKGROUND_COLOR = "#2B2B2B"
NUMBER_FORE_COLOR = "#A9B7C6"


class PyTextControl(wx.stc.StyledTextCtrl):
    def __init__(self, parent):
        super().__init__(parent)
        # self.Disable()
        font = wx.Font(14, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=u'Monaco')
        self.SetFont(font)

        self.SetLexer(wx.stc.STC_LEX_PYTHON)
        self.IndicatorSetStyle(2, wx.stc.STC_INDIC_PLAIN)
        self.IndicatorSetForeground(0, wx.RED)

        kwlist = u" ".join(keyword.kwlist)
        self.SetKeyWords(0, kwlist)

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

        # Python styles
        fonts = "face:{},size:{}".format(font.GetFaceName(), font.GetPointSize())
        default = "fore:#A9B7C6," + fonts
        # Default
        self.StyleSetSpec(stc.STC_P_DEFAULT, default)
        # Comments
        self.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:#629755," + fonts)
        # Number
        self.StyleSetSpec(stc.STC_P_NUMBER, "fore:#6897BB," + fonts)
        # String
        self.StyleSetSpec(stc.STC_P_STRING, "fore:#6A8759," + fonts)
        # Single quoted string
        self.StyleSetSpec(stc.STC_P_CHARACTER, "fore:#6A8759," + fonts)
        # Keyword
        self.StyleSetSpec(stc.STC_P_WORD, "fore:#CC7832,bold," + fonts)
        # Triple quotes
        self.StyleSetSpec(stc.STC_P_TRIPLE, "fore:#629755," + fonts)
        # Triple double quotes
        self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:#629755," + fonts)
        # Class name definition
        self.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:#A9B7C6,bold," + fonts)
        # Function or method name definition
        self.StyleSetSpec(stc.STC_P_DEFNAME, "fore:#FFC66D,bold," + fonts)
        # Operators
        self.StyleSetSpec(stc.STC_P_OPERATOR, "fore:#A9B7C6,bold," + fonts)
        # Identifiers
        self.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:#A9B7C6,bold," + fonts)
        # Comment-blocks
        self.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "fore:#629755," + fonts)
        # End of line where string is not closed
        self.StyleSetSpec(stc.STC_P_STRINGEOL, "fore:#629755,eol," + fonts)

        # event
        self.Bind(wx.stc.EVT_STC_MODIFIED, self.OnModified)
        self.Bind(wx.stc.EVT_STC_ROMODIFYATTEMPT, self.OnRomodifyAttempt)

    def OnModified(self, evt):
        pass

    def OnRomodifyAttempt(self, evt):
        print("Modified attempt")
        pass