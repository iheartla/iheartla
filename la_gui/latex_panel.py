import wx
import wx.lib.sized_controls as sc
from wx.lib.pdfviewer import pdfViewer, pdfButtonPanel


class LatexPanel(wx.Panel):
    def __init__(self, parent, **kwargs):
        super(LatexPanel, self).__init__(parent, **kwargs)
        self.button_panel = pdfButtonPanel(self, wx.NewId(), wx.DefaultPosition, wx.DefaultSize, 0)
        # self.button_panel.SetSizerProps(expand=True)
        self.viewer = pdfViewer(self, wx.NewId(), wx.DefaultPosition, wx.DefaultSize,
                                wx.HSCROLL | wx.VSCROLL | wx.SUNKEN_BORDER)
        # self.viewer.SetSizerProps(expand=True, proportion=1)
        self.button_panel.viewer = self.viewer
        self.viewer.button_panel = self.button_panel
        # sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.button_panel, 0, wx.EXPAND)
        sizer.Add(self.viewer, 1, wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.viewer.LoadFile("la.pdf")

    def render_content(self, tex):
        pass
