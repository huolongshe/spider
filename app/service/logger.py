#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx


class Logger(wx.Log):
    def __init__(self, logTime=0):
        wx.Log.__init__(self)
        self.logTime = logTime

    def DoLogText(self, message):
        self.GetActiveTarget().AppendText(message + '\n')

			
def do_log(text):
    if text[-1:] == '\n':
        text = text[:-1]
    wx.LogMessage(text)

