import wx
import wx.stc

BACKGROUND_COLOR = "#2B2B2B"

def getBestFont():
    e = wx.FontEnumerator()
    e.EnumerateFacenames()
    fontnames = e.GetFacenames( fixedWidthOnly = True )
    for name in [ 'DejaVu Sans Mono', 'Courier New' ]:
        if name in fontnames:
            return name
    return None

class BaseTextControl(wx.stc.StyledTextCtrl):
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

        self.SetProperty("styling.within.preprocessor", "1")
        self.SetProperty("fold.comment", "1")
        self.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        self.SetWindowStyle(self.GetWindowStyle() | wx.DOUBLE_BORDER)
        
        fontname = getBestFont()
        if fontname is None: fontname = self.text_font.GetFaceName()
        
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, f"size:15,face:{fontname}")
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