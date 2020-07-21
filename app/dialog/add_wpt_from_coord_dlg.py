#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx


class AddWptFromCoordDlg(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, None, -1, '根据经纬度坐标添加路点', size=(550, 260))

        wx.StaticText(self, -1, '东经：', (60, 50))
        self.lon = wx.TextCtrl(self, pos=(100, 48), size=(120, 30))

        wx.StaticText(self, -1, '北纬：', (290, 50))
        self.lat = wx.TextCtrl(self, pos=(330, 48), size=(120, 30))

        wx.Button(self, id=wx.ID_OK, label='确定', pos=(140, 140))
        wx.Button(self, id=wx.ID_CANCEL, label='取消', pos=(310, 140))

