import wx
import wx.lib.sized_controls as sc
from wx.lib.pdfviewer import pdfViewer, pdfButtonPanel
from wx.lib.pdfviewer import images
import wx.lib.agw.buttonpanel as bp
import wx.stc as stc
from ..la_gui import base_ctrl as bc


class LatexControl(bc.BaseTextControl):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetLexer(wx.stc.STC_LEX_TEX)
        # background
        self.StyleSetBackground(wx.stc.STC_TEX_DEFAULT, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_TEX_SPECIAL, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_TEX_GROUP, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_TEX_SYMBOL, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_TEX_COMMAND, bc.BACKGROUND_COLOR)
        self.StyleSetBackground(wx.stc.STC_TEX_TEXT, bc.BACKGROUND_COLOR)

        # foreground
        self.StyleSetSpec(stc.STC_TEX_DEFAULT, "fore:#808080," + self.fonts)
        self.StyleSetSpec(stc.STC_TEX_SPECIAL, "fore:#ED7600," + self.fonts)
        self.StyleSetSpec(stc.STC_TEX_GROUP, "fore:#365A71," + self.fonts)  # {}
        self.StyleSetSpec(stc.STC_TEX_SYMBOL, "fore:#6A8759," + self.fonts)
        self.StyleSetSpec(stc.STC_TEX_COMMAND, "fore:#ED7600," + self.fonts)
        self.StyleSetSpec(stc.STC_TEX_TEXT, "fore:#668AA1,bold," + self.fonts)  # bmatrix


class LatexPanel(wx.Panel):
    def __init__(self, parent, **kwargs):
        super(LatexPanel, self).__init__(parent, **kwargs)
        self.percent_zoom = 0.3
        self.tex_panel = wx.Panel(self)
        self.tex_panel.SetPosition((0, 0))
        self.tex_panel.SetSize((self.GetSize().width, self.GetSize().height))
        self.zoomIn = wx.BitmapButton(self.tex_panel, -1, images.ZoomIn.GetBitmap())
        self.zoomOut = wx.BitmapButton(self.tex_panel, -1, images.ZoomOut.GetBitmap())
        self.Bind(wx.EVT_BUTTON, self.OnZoomIn, self.zoomIn)
        self.Bind(wx.EVT_BUTTON, self.OnZoomOut, self.zoomOut)
        self.viewer = pdfViewer(self.tex_panel, wx.NewId(), wx.DefaultPosition, wx.DefaultSize,
                                wx.HSCROLL | wx.VSCROLL | wx.SUNKEN_BORDER)
        # sizer
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer.Add(self.zoomIn, 1, wx.EXPAND)
        h_sizer.Add(self.zoomOut, 1, wx.EXPAND)
        self.pdf_sizer = wx.BoxSizer(wx.VERTICAL)
        self.pdf_sizer.Add(h_sizer, 0, wx.EXPAND)
        self.pdf_sizer.Add(self.viewer, 1, wx.EXPAND)
        self.tex_panel.SetSizer(self.pdf_sizer)
        self.pdf_sizer.Fit(self)
        #
        self.viewer.Bind(wx.EVT_BUTTON, self.OnButtonClicked)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.latex_ctrl = LatexControl(self)
        # self.latex_ctrl.Hide()
        self.Layout()
        self.show_pdf = True

    def render_content(self, tex, show_pdf):
        self.latex_ctrl.SetEditable(True)
        self.latex_ctrl.SetValue(tex)
        self.latex_ctrl.SetEditable(False)
        if show_pdf is None:
            # render text
            self.show_pdf = False
            self.tex_panel.Hide()
            self.latex_ctrl.Show()
        else:
            # render PDF
            self.show_pdf = True
            self.tex_panel.Show()
            self.latex_ctrl.Hide()
            self.viewer.LoadFile(show_pdf)

    def get_content(self):
        return self.latex_ctrl.GetValue()

    def OnSize(self, e):
        self.tex_panel.SetPosition((0, 0))
        self.tex_panel.SetSize((self.GetSize().width, self.GetSize().height))
        self.latex_ctrl.SetPosition((0, 0))
        self.latex_ctrl.SetSize((self.GetSize().width, self.GetSize().height))
        self.tex_panel.Layout()

    def OnButtonClicked(self, e):
        print('OnButtonClicked')

    def OnZoomIn(self, e):
        self.percent_zoom = min(self.percent_zoom*2, 1.2)
        self.viewer.SetZoom(self.percent_zoom)

    def OnZoomOut(self, e):
        self.percent_zoom = max(0.15, self.percent_zoom/2.0)
        self.viewer.SetZoom(self.percent_zoom)

    def update_panels(self):
        if self.show_pdf:
            self.tex_panel.Show()
            self.latex_ctrl.Hide()
        else:
            self.tex_panel.Hide()
            self.latex_ctrl.Show()

    def switch_panels(self):
        self.show_pdf = not self.show_pdf
        self.update_panels()