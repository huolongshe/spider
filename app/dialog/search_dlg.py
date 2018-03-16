#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx


class WptSearchDlg(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, None, -1, '搜索地点', size=(500,250))

        wx.StaticText(self, -1, '地名：', (50, 50))
        self.name = wx.TextCtrl(self, pos=(100, 48), size=(320,30))

        wx.Button(self, id=wx.ID_OK, label='确定', pos=(120, 130))
        wx.Button(self, id=wx.ID_CANCEL, label='取消', pos=(270, 130))
        
        
class RouteSearchDlg(wx.Dialog):
    def __init__(self, g):
        wx.Dialog.__init__(self, None, -1, '搜索行车路线', size=(500,320))

        wx.StaticText(self, -1, '起点：', (50, 50))
        self.start = wx.ComboBox(self, pos=(100, 48), size=(320, 30), choices=[], style=wx.CB_DROPDOWN)
        for wpt in g.wpt_list:
            self.start.Append(wpt.name)

        wx.StaticText(self, -1, '终点：', (50, 120))
        self.end = wx.ComboBox(self, pos=(100, 118), size=(320, 30), choices=[], style=wx.CB_DROPDOWN)
        for wpt in g.wpt_list:
            self.end.Append(wpt.name)

        wx.Button(self, id=wx.ID_OK, label='确定', pos=(120, 200))
        wx.Button(self, id=wx.ID_CANCEL, label='取消', pos=(270, 200))



        





