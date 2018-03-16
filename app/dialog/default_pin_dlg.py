#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx


class DefaultPinDlg(wx.Dialog):
    def __init__(self, g):
        wx.Dialog.__init__(self, None, -1, '请设置默认路点图钉样式：', size=(640, 680))
        self.g = g

        start_x = 30
        start_y = 30
        delta_x = 60
        delta_y = 60
        
        self.buttons = [None] * 100
        for i in range(100):
            line = i // 10
            col = i % 10
            x = start_x + col * delta_x
            y = start_y + line * delta_y
            self.buttons[i] = wx.Button(self, id=i, label='', pos=(x, y), size=(36, 36))
            self.buttons[i].SetBitmap(g.pin_bmps[i])
            self.Bind(wx.EVT_BUTTON, self.on_click_button, self.buttons[i], id=self.buttons[i].GetId())
            if i == self.g.default_wpt_bmp_index:
                self.buttons[i].SetFocus()
            
    def on_click_button(self, event):
        self.g.default_wpt_bmp_index = event.Id
        self.EndModal(wx.ID_OK)
        

