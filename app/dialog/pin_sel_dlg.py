#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx
from app.globals import const


class PinSelDlg(wx.Dialog):
    def __init__(self, g, wpt):
        wx.Dialog.__init__(self, None, -1, '请选择路点图钉显示样式：', size=(640, 680))
        self.g = g
        self._wpt = wpt

        start_x = 30
        start_y = 30
        delta_x = 60
        delta_y = 60
        
        buttons = [None] * 100
        for i in range(100):
            line = i // 10
            col = i % 10
            x = start_x + col * delta_x
            y = start_y + line * delta_y
            buttons[i] = wx.Button(self, id=i, label='', pos=(x, y), size=(36, 36))
            buttons[i].SetBitmap(self.g.pin_bmps[i])
            self.Bind(wx.EVT_BUTTON, self.on_click_button, buttons[i], id=buttons[i].GetId())
            if self._wpt.bmp_index == i:
                buttons[i].SetFocus()
            
    def on_click_button(self, event):
        self._wpt.bmp_index = event.Id
        self.g.db_mgr.update_wpt_bmp_index(self._wpt)
        self.g.track_tree.set_wpt_image(self._wpt)
        self.g.map_canvas.repaint(const.REDRAW_COPY)
        self.Destroy()
        

