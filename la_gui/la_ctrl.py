import wx
import wx.stc

BACKGROUND_COLOR = "#2B2B2B"


class LaTextControl(wx.stc.StyledTextCtrl):
    # Style IDs
    STC_STYLE_LA_DEFAULT, \
    STC_STYLE_LA_KW = range(2)

    def __init__(self, parent):
        super().__init__(parent)
        self.keywords = [ord(char) for char in "i"]
        self.SetKeyWords(0, "if")

        self.SetProperty("styling.within.preprocessor", "1")
        self.SetFont(wx.Font(14, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=u'Monaco'))
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

        style = self.STC_STYLE_LA_DEFAULT
        self.StyleSetSpec(style, "fore:#A9B7C6,back:{}".format(BACKGROUND_COLOR))
        style = self.STC_STYLE_LA_KW
        self.StyleSetSpec(style, "fore:#94558D,bold,back:{}".format(BACKGROUND_COLOR))
        self.SetLexer(wx.stc.STC_LEX_CONTAINER)
        # evt handler
        self.Bind(wx.stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
        self.Bind(wx.stc.EVT_STC_STYLENEEDED, self.OnStyleNeeded)

    def OnStyleNeeded(self, event):
        last_styled_pos = self.GetEndStyled()
        line = self.LineFromPosition(last_styled_pos)
        start_pos = self.PositionFromLine(line)
        end_pos = event.GetPosition()
        while start_pos < end_pos:
            self.StartStyling(start_pos)
            char = self.GetCharAt(start_pos)
            if char in self.keywords:
                style = self.STC_STYLE_LA_KW
            else:
                style = self.STC_STYLE_LA_DEFAULT
            self.SetStyling(1, style)
            start_pos += 1

    def OnMarginClick(self, event):
        pass
