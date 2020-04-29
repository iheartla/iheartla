import wx
import wx.stc
import la_gui.base_ctrl as bc


class LaTextControl(bc.BaseTextControl):
    # Style IDs
    STC_STYLE_LA_DEFAULT, \
    STC_STYLE_LA_KW = range(2)

    def __init__(self, parent):
        super().__init__(parent)
        self.keywords = [ord(char) for char in "ijk"]
        self.SetKeyWords(0, "if")

        style = self.STC_STYLE_LA_DEFAULT
        self.StyleSetSpec(style, "fore:#A9B7C6,back:{}".format(bc.BACKGROUND_COLOR))
        style = self.STC_STYLE_LA_KW
        self.StyleSetSpec(style, "fore:#94558D,bold,back:{}".format(bc.BACKGROUND_COLOR))
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
