#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx
import wx.lib.colourselect


class FolderStyleDlg(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, None, -1, '设置本文件夹所有轨迹显示样式', size=(400, 360))
        
        wx.StaticText(self, -1, '线段格式：', (50, 50))
        self.dash_style = wx.RadioBox(parent=self, id=-1, pos=(130, 25), choices=['实线', '虚线'],
                                      style=wx.RA_HORIZONTAL | wx.NO_BORDER)
        self.dash_style.SetSelection(0)
        
        wx.StaticText(self, -1, '线条宽度：', (50, 100))
        self.width = wx.SpinCtrl(self, -1, '', pos=(130, 100), size=(60, 28))
        self.width.SetRange(1, 10)
        self.width.SetValue(2)
        
        wx.StaticText(self, -1, '线条颜色：', (50, 150))
        self.color = (255, 0, 0)
        self.color_ctrl = wx.lib.colourselect.ColourSelect(self, -1, colour=self.color, pos=(130, 150), size=(60, 28))
        self.Bind(wx.lib.colourselect.EVT_COLOURSELECT, self.on_sel_color, self.color_ctrl)
        
        wx.StaticText(self, -1, '显示端点：', (50, 200))
        self.display_end_points = wx.CheckBox(self, pos=(130, 200))
        self.display_end_points.SetValue(True)
        
        wx.Button(self, id=wx.ID_OK, label='确定', pos=(65, 260))
        wx.Button(self, id=wx.ID_CANCEL, label='取消', pos=(230, 260))
    
    def on_sel_color(self, event):
        self.color = event.GetValue()

