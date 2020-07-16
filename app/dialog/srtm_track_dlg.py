#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import threading
import time

import wx

from app.globals import const
from app.globals.global_data import g
from app.service.logger import do_log


class SrtmTrackDialog(wx.Dialog):
    def __init__(self, track_line):
        wx.Dialog.__init__(self, None, -1, '高程数据下载', size=(600, 350))
        self.EnableCloseButton(False)

        self._track_line = track_line

        self._ctl_gauge_point = wx.Gauge(self, -1, g.srtm_mgr.PROGRESS_RANGE, (50, 50), (500, 30))
        self._ctl_gauge_total = wx.Gauge(self, -1, g.srtm_mgr.PROGRESS_RANGE, (50, 100), (500, 30))

        self._total_progress_unit = float(g.srtm_mgr.PROGRESS_RANGE) / len(self._track_line.track_points)
        self._total_progress_now = 0

        self._ctl_progress_tip = wx.StaticText(self, -1, '下载进度提示：', (50, 160), (800, 30))

        self._ctl_cancel = wx.Button(self, -1, '取消', pos=(260, 240))
        self.Bind(wx.EVT_BUTTON, self.on_cancel, self._ctl_cancel)
        
        thread = threading.Thread(target=self.download_track_alt_main_thread, args=())
        thread.setDaemon(True)
        thread.start()
        
    def on_cancel(self, event):
        dlg = wx.MessageDialog(self, '你真的要中止高程数据下载过程吗？',
                               '提示',
                               wx.YES_NO
                               )
        ret = dlg.ShowModal()
        dlg.Destroy()
        if ret != wx.ID_YES:
            return
        g.srtm_mgr.manual_canceled = True
        self._ctl_cancel.Enable(False)
        self._ctl_progress_tip.SetLabelText('高程数据下载过程被人为中止，等待关闭对话框...')

    def download_track_alt_main_thread(self):
        do_log('正在为轨迹“%s”下载高程数据，请稍候...' % self._track_line.name)
        num_filled = 0
        num_error = 0
        self._total_progress_now = 0
        self._ctl_gauge_total.SetValue(0)
        
        i = 0
        for point in self._track_line.track_points:
            i += 1
            self._ctl_progress_tip.SetLabelText('正在为第%d个轨迹点填充高程数据...' % i)
            if point.alt <= 0:  # 本应用中假定海拔高度都应大于0
                g.srtm_mgr.progress_now = 3.0
                self._ctl_gauge_point.SetValue(g.srtm_mgr.progress_now)
                alt = g.srtm_mgr.get_alt_local(point.lon, point.lat)
                if alt is None:
                    thread = threading.Thread(target=g.srtm_mgr.get_alt_network, args=(point.lon, point.lat))
                    thread.setDaemon(True)
                    thread.start()
                    
                    time.sleep(0.01)
                    while g.srtm_mgr.downloading:
                        self._ctl_gauge_point.SetValue(g.srtm_mgr.progress_now)
                        time.sleep(0.01)
                        
                    alt = g.srtm_mgr.alt
                    
                self._ctl_gauge_point.SetValue(g.srtm_mgr.PROGRESS_RANGE)

                if alt < 0:
                    num_error += 1
                    if alt == g.srtm_mgr.ERROR_NETWORK:
                        do_log('因网络原因下载失败，请稍后再试...')
                        break
                    elif alt == g.srtm_mgr.ERROR_CANCELED:
                        do_log('下载过程被人为中止！')
                        break
                    else:
                        do_log('为第%d个轨迹点获取的高程数据有误...' % i)
                else:
                    point.alt = alt
                    num_filled += 1
            self._total_progress_now = i * self._total_progress_unit
            self._ctl_gauge_total.SetValue(int(self._total_progress_now))

        if num_filled > 0:
            do_log('已为%d轨迹点添加高程数据...' % num_filled)
            self._track_line.compute_track_line_args()
            if g.in_editing:
                g.track_edit.set_selected_track_line(self._track_line)
                g.frame.repaint(canvas=const.REDRAW_TRACK)
        elif num_error == 0:
            do_log('本轨迹所有轨迹点已有高程数据，不需下载...')
            
        self._ctl_gauge_total.SetValue(g.srtm_mgr.PROGRESS_RANGE)
        if not g.srtm_mgr.manual_canceled:
            self._ctl_progress_tip.SetLabelText('高程数据填充完成！')
            time.sleep(1)
        self.Destroy()

