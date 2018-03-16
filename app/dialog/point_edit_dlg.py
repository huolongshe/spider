#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import datetime

import wx
import wx.adv
import wx.lib.masked

from app.globals import const


class PointEditDlg(wx.Dialog):
    def __init__(self, g, point):
        wx.Dialog.__init__(self, None, -1, '轨迹点数据', size=(560, 400))
        self.g = g
        self._point = point
        self._track = point.track_line
        self._point_idx = self._track.track_points.index(self._point)
        self._point_num = len(self._track.track_points)
        
        wx.StaticText(self, -1, '轨迹名：%s' % self._track.name, (20, 20))
        self._text_point = wx.StaticText(self, -1, '共 %d 轨迹点，第 %d 轨迹点' % (self._point_num, self._point_idx), (20, 60))
        self._text_lon = wx.StaticText(self, -1, '东经：%13.8f' % self._point.lon, (20, 100))
        self._text_lat = wx.StaticText(self, -1, '北纬：%13.8f' % self._point.lat, (20, 140))
        
        wx.StaticText(self, -1, '海拔：', (20, 190))
        self._alt_spin = wx.SpinCtrl(self, -1, '', pos=(70, 190), size=(120, 28))
        self._alt_spin.SetRange(0, 10000)
        self._alt_spin.SetValue(int(self._point.alt))
        wx.StaticText(self, -1, '米', (195, 190))
        set_alt_btn = wx.Button(self, id=-1, label='取两侧海拔平均值', pos=(230, 185))
        self.Bind(wx.EVT_BUTTON, self.on_set_alt_btn, set_alt_btn)
        
        if self._track.has_timestamp:
            time_str = self._point.timestamp_local.strftime('%H:%M:%S')
            ts = self._point.timestamp_local.timetuple()
            date = wx.DateTime()
            date.Set(year=ts.tm_year, month=ts.tm_mon - 1, day=ts.tm_mday)
            wx.StaticText(self, -1, '时间：', (20, 240))
            self.date = wx.adv.DatePickerCtrl(self, -1, pos=(70, 240), dt=date, style=wx.adv.DP_DROPDOWN | wx.adv.DP_SHOWCENTURY)
            spin = wx.SpinButton(self, -1, pos=(270, 240), size=(20, 28), style=wx.SP_VERTICAL)
            self.time = wx.lib.masked.TimeCtrl(self, -1, pos=(200, 240), size=(120, 28), value=time_str, fmt24hr=True,
                                               spinButton=spin)
        
        self._prev_btn = wx.Button(self, id=-1, label='<=前轨迹点', pos=(30, 300))
        self._next_btn = wx.Button(self, id=-1, label='后轨迹点=>', pos=(170, 300))
        self.Bind(wx.EVT_BUTTON, self.on_prev, self._prev_btn)
        self.Bind(wx.EVT_BUTTON, self.on_next, self._next_btn)
        if self._point_idx == 0:
            self._prev_btn.Enable(False)
        if self._point_idx == self._point_num - 1:
            self._next_btn.Enable(False)
        
        ok_btn = wx.Button(self, id=-1, label='确定', pos=(400, 300))
        self.Bind(wx.EVT_BUTTON, self.on_ok, ok_btn)
        self.g.frame.repaint(canvas=const.REDRAW_COPY)
    
    def on_set_alt_btn(self, event):
        point_pre = self._track.track_points[self._point_idx - 1] if self._point_idx > 0 else None
        point_next = self._track.track_points[self._point_idx + 1] if self._point_idx < self._point_num - 1 else None
        
        if point_pre and point_next:
            alt = (point_pre.alt + point_next.alt) / 2
        elif not point_next:
            alt = point_pre.alt
        elif not point_pre:
            alt = point_next.alt
        else:
            alt = self._point.alt
        
        self._alt_spin.SetValue(int(alt))
    
    def on_prev(self, event):
        self.save()
        
        if self._point_idx == 0:
            return
        self._point_idx -= 1
        self._point = self._track.track_points[self._point_idx]
        
        if self._point_idx == 0:
            self._prev_btn.Enable(False)
        if self._point_idx < self._point_num - 1:
            self._next_btn.Enable(True)
        
        self._text_point.SetLabelText('共 %d 轨迹点，第 %d 轨迹点' % (self._point_num, self._point_idx))
        self._text_lon.SetLabelText('东经：%13.8f' % self._point.lon)
        self._text_lat.SetLabelText('北纬：%13.8f' % self._point.lat)
        self._alt_spin.SetValue(int(self._point.alt))
        if self._track.has_timestamp:
            time_str = self._point.timestamp_local.strftime('%H:%M:%S')
            ts = self._point.timestamp_local.timetuple()
            date = wx.DateTime()
            date.Set(year=ts.tm_year, month=ts.tm_mon - 1, day=ts.tm_mday)
            self.date.SetValue(date)
            self.time.SetValue(time_str)
        
        self._track.selected_point = self._point
        self.g.frame.repaint(canvas=const.REDRAW_COPY)
    
    def on_next(self, event):
        self.save()
        
        if self._point_idx == self._point_num - 1:
            return
        self._point_idx += 1
        self._point = self._track.track_points[self._point_idx]
        
        if self._point_idx == self._point_num - 1:
            self._next_btn.Enable(False)
        if self._point_idx > 0:
            self._prev_btn.Enable(True)
        
        self._text_point.SetLabelText('共 %d 轨迹点，第 %d 轨迹点' % (self._point_num, self._point_idx))
        self._text_lon.SetLabelText('东经：%13.8f' % self._point.lon)
        self._text_lat.SetLabelText('北纬：%13.8f' % self._point.lat)
        self._alt_spin.SetValue(int(self._point.alt))
        if self._track.has_timestamp:
            time_str = self._point.timestamp_local.strftime('%H:%M:%S')
            ts = self._point.timestamp_local.timetuple()
            date = wx.DateTime()
            date.Set(year=ts.tm_year, month=ts.tm_mon - 1, day=ts.tm_mday)
            self.date.SetValue(date)
            self.time.SetValue(time_str)
        self._track.selected_point = self._point
        self.g.frame.repaint(canvas=const.REDRAW_COPY)
        
    def on_ok(self, event):
        self.save()
        self.EndModal(wx.ID_OK)
    
    def save(self):
        alt = self._alt_spin.GetValue()
        if alt != int(self._point.alt):
            self._point.alt = alt
        if self._track.has_timestamp:
            date = self.date.GetValue()
            year = date.GetYear()
            month = date.GetMonth() + 1
            day = date.GetDay()
            time_str = self.time.GetValue()
            hour = int(time_str[0:2])
            minute = int(time_str[3:5])
            second = int(time_str[6:8])
            self._point.set_timestamp_local(datetime.datetime(year, month, day, hour, minute, second))
        self._track.compute_track_line_args()


