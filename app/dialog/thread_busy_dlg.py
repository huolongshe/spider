#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import threading
import wx


class ThreadBusyDlg(wx.Dialog):
    def __init__(self, target_thread, args, tip):
        wx.Dialog.__init__(self, None, -1, tip, size=(600, 100))
        self.EnableCloseButton(False)
        
        self.gauge = wx.Gauge(self, -1, 100)
        self.percent_now = 0
        self.percent_unit = 1
        
        self.target_thread = target_thread
        self.args = args
        self.thread_runing = False
        thread = threading.Thread(target=self.busy_thread, args=())
        thread.setDaemon(True)
        thread.start()

        thread = threading.Thread(target=self.waiting_thread, args=())
        thread.setDaemon(True)
        thread.start()

    def busy_thread(self):
        self.thread_runing = True
        thread = threading.Thread(target=self.target_thread, args=self.args)
        thread.setDaemon(True)
        thread.start()
        thread.join()
        self.thread_runing = False
        
    def waiting_thread(self):
        wx.MilliSleep(100)
        while self.thread_runing:
            self.gauge.SetValue(self.percent_now)
            self.percent_now += self.percent_unit
            if self.percent_now > 100:
                self.percent_now = 0
            wx.MilliSleep(100)
        self.Destroy()