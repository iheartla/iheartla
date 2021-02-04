import wx
import wx.stc
from ..la_gui import base_ctrl as bc


class MsgControl(wx.stc.StyledTextCtrl):
    # Style IDs
    STC_STYLE_MSG_DEFAULT, \
    STC_STYLE_MSG_ERROR  = range(2)

    def __init__(self, parent):
        super().__init__(parent)
        self.SetEditable(False)
        # change "Ctrl-Y" to "Ctrl-Shift-Z"
        self.CmdKeyClear(89, wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyAssign(90, wx.stc.STC_SCMOD_SHIFT | wx.stc.STC_SCMOD_CTRL, wx.stc.STC_CMD_REDO)
        self.text_font = wx.Font(14, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=u'Monaco')
        self.SetFont(self.text_font)
        self.fonts = "face:{},size:{}".format(self.text_font.GetFaceName(), self.text_font.GetPointSize())

        self.IndicatorSetStyle(2, wx.stc.STC_INDIC_PLAIN)
        self.IndicatorSetForeground(0, wx.RED)

        self.SetWindowStyle(self.GetWindowStyle() | wx.DOUBLE_BORDER)
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, "size:15,face:Courier New")
        self.SetWrapMode(wx.stc.STC_WRAP_WORD)
        self.SetMarginLeft(5)
        self.SetMarginWidth(1, 0)

        self.MarkerSetBackgroundSelected(1, wx.Colour(0xFF0000))
        self.MarkerEnableHighlight(True)

        # caret setting
        self.SetCaretForeground(wx.Colour(0xBBBBBB))
        self.SetCaretLineVisible(True)
        self.SetCaretLineBackground(wx.Colour(0x323232))
        self.SetSelBackground(True, wx.Colour(0x43474A))

        self.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, bc.BACKGROUND_COLOR)
        self.StyleSetSpec(self.STC_STYLE_MSG_DEFAULT, "fore:#FE6B68,back:{}".format(bc.BACKGROUND_COLOR))
        # self.StyleSetSpec(self.STC_STYLE_MSG_DEFAULT, "fore:#A9B7C6,back:{}".format(bc.BACKGROUND_COLOR))
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
            self.SetStyling(1, self.STC_STYLE_MSG_DEFAULT)
            start_pos += 1

    def OnMarginClick(self, event):
        pass