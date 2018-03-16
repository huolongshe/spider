#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx
from app.view.main_frame import MainFrame


class AppMain(wx.App):
    def OnInit(self):
        frame = MainFrame()
        self.SetTopWindow(frame)
        return True


if __name__ == '__main__':
    AppMain().MainLoop()
