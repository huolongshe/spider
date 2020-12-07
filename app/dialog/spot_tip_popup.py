#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import threading
import wx


class SpotTipPopup(wx.PopupWindow):
    def __init__(self, parent, spot):
        wx.PopupWindow.__init__(self, parent, wx.NO_BORDER)
        panel = wx.Panel(self)
        panel.SetBackgroundColour('#A8FFD3')
        self.parent = parent
        self.spot = spot
        st = wx.StaticText(panel, -1, spot.get_tip(), pos=(10, 10))
        sz = st.GetBestSize()
        self.SetSize((sz.width + 20, sz.height + 20))
        panel.SetSize((sz.width + 20, sz.height + 20))
        wx.CallAfter(self.Refresh)

        thread = threading.Thread(target=self.destroy_self, args=())
        thread.setDaemon(True)
        thread.start()

    def destroy_self(self):
        for i in range(150):
            wx.MilliSleep(2)
            try:
                self.Position(self.parent.ClientToScreen(self.spot.spx, self.spot.spy), (0, 0))
            except:
                break

        try:
            self.Show(False)
            wx.CallAfter(self.Destroy)
        except:
            pass






