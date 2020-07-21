#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx


class AddWptFromTileDlg(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, None, -1, '根据瓦片坐标添加路点', size=(800, 360))

        wx.StaticText(self, -1, '瓦片x坐标：', (60, 50))
        self.tile_x = wx.TextCtrl(self, pos=(150, 48), size=(100, 30))

        wx.StaticText(self, -1, '瓦片y坐标：', (290, 50))
        self.tile_y = wx.TextCtrl(self, pos=(380, 48), size=(100, 30))

        wx.StaticText(self, -1, '瓦片z坐标：', (520, 50))
        self.tile_z = wx.TextCtrl(self, pos=(610, 48), size=(100, 30))

        self.need_jiupian = wx.CheckBox(self, -1, '纠偏', (60, 100), (200, 30), wx.NO_BORDER)
        self.need_jiupian.SetValue(True)
        wx.StaticText(self, -1, '注：常用在线地图中，需要纠偏的包括：谷歌中国地图(谷歌地形图除外)，腾讯地图，高德地图等等', (60, 150))
        wx.StaticText(self, -1, '                                     不需要纠偏的包括：谷歌地形图，OpenCycleMap，天地图等等', (60, 180))
        wx.Button(self, id=wx.ID_OK, label='确定', pos=(420, 250))
        wx.Button(self, id=wx.ID_CANCEL, label='取消', pos=(590, 250))

