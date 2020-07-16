#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import threading
import time
import wx

from app.globals import const
from app.globals.global_data import g
from app.service.logger import do_log


class SrtmWptDlg(wx.Dialog):
    def __init__(self, wpt):
        wx.Dialog.__init__(self, None, -1, '正在下载高程数据，请稍候...', size=(600, 250))
        self.EnableCloseButton(False)
        self.wpt = wpt

        self._ctl_gauge_point = wx.Gauge(self, -1, g.srtm_mgr.PROGRESS_RANGE, (30, 50), (540, 30))
        self._ctl_cancel = wx.Button(self, -1, '取消', pos=(250, 140))
        self.Bind(wx.EVT_BUTTON, self.on_cancel, self._ctl_cancel)
        
        thread = threading.Thread(target=self.download_wpt_alt_main_thread, args=())
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
        self.SetTitle('下载过程正在被中止，请稍候...')

    def download_wpt_alt_main_thread(self):
        do_log('正在为路点“%s”下载高程数据，请稍候...' % self.wpt.name)
        i = 0
        if self.wpt.alt <= 0:  # 本应用中假定海拔高度都应大于0
            g.srtm_mgr.progress_now = 3.0
            self._ctl_gauge_point.SetValue(g.srtm_mgr.progress_now)
            thread = threading.Thread(target=g.srtm_mgr.get_alt_network, args=(self.wpt.lon, self.wpt.lat))
            thread.setDaemon(True)
            thread.start()

            time.sleep(0.1)
            while g.srtm_mgr.downloading:
                self._ctl_gauge_point.SetValue(g.srtm_mgr.progress_now)
                time.sleep(0.1)

            alt = g.srtm_mgr.alt
            self._ctl_gauge_point.SetValue(g.srtm_mgr.PROGRESS_RANGE)

            if alt < 0:
                if alt == g.srtm_mgr.ERROR_NETWORK:
                    do_log('下载失败，可能网路故障或网速太慢，请稍后再试...')
                elif alt == g.srtm_mgr.ERROR_CANCELED:
                    do_log('下载过程被人为中止！')
                else:
                    do_log('获取高程数据有误...')
            else:
                self.wpt.alt = alt
                do_log('路点高程数据获取成功...')

        g.frame.repaint(const.REDRAW_COPY)
        self.Destroy()