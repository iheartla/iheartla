import wx
import wx.lib.sized_controls as sc
from wx.lib.pdfviewer import pdfViewer, pdfButtonPanel
from wx.lib.pdfviewer import images
import wx.lib.agw.buttonpanel as bp


class LatexPanel(wx.Panel):
    def __init__(self, parent, **kwargs):
        super(LatexPanel, self).__init__(parent, **kwargs)
        self.zoomIn = wx.Button(self, -1, "Zoom In")
        self.zoomOut = wx.Button(self, -1, "Zoom Out")
        self.Bind(wx.EVT_BUTTON, self.OnZoomIn, self.zoomIn)
        self.Bind(wx.EVT_BUTTON, self.OnZoomOut, self.zoomOut)
        self.viewer = pdfViewer(self, wx.NewId(), wx.DefaultPosition, wx.DefaultSize,
                                wx.HSCROLL | wx.VSCROLL | wx.SUNKEN_BORDER)
        # sizer
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer.Add(self.zoomIn, 1, wx.EXPAND)
        h_sizer.Add(self.zoomOut, 1, wx.EXPAND)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(h_sizer, 0 , wx.EXPAND)
        sizer.Add(self.viewer, 1, wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.viewer.LoadFile("la.pdf")
        self.viewer.Bind(wx.EVT_BUTTON, self.OnButtonClicked)
        self.percent_zoom = 0.3

    def render_content(self, tex):
        pass

    def OnButtonClicked(self, e):
        print('OnButtonClicked')

    def OnZoomIn(self, e):
        self.percent_zoom = min(self.percent_zoom*2, 1.2)
        self.viewer.SetZoom(self.percent_zoom)

    def OnZoomOut(self, e):
        self.percent_zoom = max(0.15, self.percent_zoom/2.0)
        self.viewer.SetZoom(self.percent_zoom)
