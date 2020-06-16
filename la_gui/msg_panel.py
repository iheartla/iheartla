import wx
import wx.stc
import la_gui.base_ctrl as bc


class MsgControl(bc.BaseTextControl):
    # Style IDs
    STC_STYLE_MSG_DEFAULT, \
    STC_STYLE_MSG_ERROR  = range(2)

    def __init__(self, parent):
        super().__init__(parent)
        self.text_font = wx.Font(14, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=u'Monaco')
        self.SetFont(self.text_font)
        self.fonts = "face:{},size:{}".format(self.text_font.GetFaceName(), self.text_font.GetPointSize())

        self.IndicatorSetStyle(2, wx.stc.STC_INDIC_PLAIN)
        self.IndicatorSetForeground(0, wx.RED)

        self.SetProperty("styling.within.preprocessor", "1")
        self.SetProperty("fold.comment", "1")
        self.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        self.SetWindowStyle(self.GetWindowStyle() | wx.DOUBLE_BORDER)
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, "size:15,face:Courier New")
        self.SetWrapMode(wx.stc.STC_WRAP_WORD)
        self.SetMarginLeft(0)

        self.MarkerSetBackgroundSelected(1, wx.Colour(0xFF0000))
        self.MarkerEnableHighlight(True)

        self.SetLexer(wx.stc.STC_LEX_CONTAINER)
        # evt handler
        self.Bind(wx.stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
        self.Bind(wx.stc.EVT_STC_STYLENEEDED, self.OnStyleNeeded)

    def OnStyleNeeded(self, event):
        pass

    def OnMarginClick(self, event):
        pass