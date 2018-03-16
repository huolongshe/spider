#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx


class TrackSelectDlg(wx.Dialog):
    def __init__(self, track_line_list):
        wx.Dialog.__init__(self, None, -1, '当前位置有多个轨迹，请选择其中一个：', size=(640, 480))

        self.image_list = wx.ImageList(16, 16)
        self.list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL)
        self.list.SetImageList(self.image_list, wx.IMAGE_LIST_SMALL)
        self.list.InsertColumn(0, '')
        self.list.SetColumnWidth(0, 600)
        for track_line in track_line_list:
            bmp = wx.Bitmap(16, 16)
            mdc = wx.MemoryDC(bmp)
            mdc.SetBackground(wx.Brush(self.list.GetBackgroundColour(), wx.BRUSHSTYLE_TRANSPARENT))
            mdc.Clear()
            mdc.SetPen(wx.Pen(wx.Colour(track_line.red, track_line.green, track_line.blue, track_line.alpha), 1,
                              wx.PENSTYLE_SOLID))
            for (px, py) in track_line.points_list_for_draw[0]:
                mdc.DrawPoint(px, py)
            mdc.SelectObject(wx.NullBitmap)
            track_idx = self.image_list.Add(bmp)
            
            self.list.InsertItem(999, track_line.name, track_idx)
            
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_selected, self.list)
        self.sel_idx = 0
    
    def on_selected(self, event):
        self.sel_idx = event.Index
        self.EndModal(wx.ID_OK)
