#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx
from app.globals import const


class AboutDlg(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, None, -1, '关于...', size=(320, 240))
        wx.StaticText(self, -1, const.APP_NAME, (85, 40))
        wx.StaticText(self, -1, '霍龙社    2018年3月', (88, 90))
        wx.Button(self, id=wx.ID_OK, label='确定', pos=(100, 150))

