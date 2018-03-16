#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx
import wx.lib.colourselect


class TrackStyleDlg(wx.Dialog):
    def __init__(self, track_line):
        wx.Dialog.__init__(self, None, -1, '编辑轨迹显示样式', size=(640, 400))
                
        wx.StaticText(self, -1, '轨迹名：%s' % track_line.name, (20, 30))
        
        wx.StaticText(self, -1, '线段格式：', (20, 100))
        self.dash_style = wx.RadioBox(parent=self, id=-1, pos=(100, 75), choices=['实线', '虚线'], style=wx.RA_HORIZONTAL | wx.NO_BORDER)
        if track_line.draw_line_dashed:
            self.dash_style.SetSelection(1)
        else:
            self.dash_style.SetSelection(0)
       
        wx.StaticText(self, -1, '线条宽度：', (20, 150))
        self.width = wx.SpinCtrl(self, -1, '', pos=(100, 150), size=(60, 28))
        self.width.SetRange(1, 90)
        self.width.SetValue(int(track_line.width))

        wx.StaticText(self, -1, '线条颜色：', (20, 200))
        self.color = (track_line.red, track_line.green, track_line.blue)
        self.color_ctrl = wx.lib.colourselect.ColourSelect(self, -1, colour=self.color, pos=(100, 200), size=(60, 28))
        self.Bind(wx.lib.colourselect.EVT_COLOURSELECT, self.on_sel_color, self.color_ctrl)

        wx.StaticText(self, -1, '显示端点：', (20, 250))
        self.display_end_points = wx.CheckBox(self, pos=(100, 250))
        if track_line.draw_endpoints:
            self.display_end_points.SetValue(True)
        else:
            self.display_end_points.SetValue(False)

        wx.Button(self, id=wx.ID_OK, label='确定', pos=(170, 300))
        wx.Button(self, id=wx.ID_CANCEL, label='取消', pos=(390, 300))
    
    def on_sel_color(self, event):
        self.color = event.GetValue()
