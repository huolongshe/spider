#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx
from app.globals.global_data import g


class SrtmSrcDlg(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, None, -1, '', size=(480, 250))

        choices = ['https://dds.cr.usgs.gov    下载速度快，但缓冲范围小',
                   'http://srtm.csi.cgiar.org   下载速度慢，但缓冲范围大']
        self.srtm_src = wx.RadioBox(parent=self, id=-1, label='请选择高程数据下载网站',
                                    pos=(30, 30), size=(410, 100),
                                    choices=choices, style=wx.RA_VERTICAL)
        self.srtm_src.SetSelection(g.srtm_url_index)

        ok = wx.Button(self, wx.ID_OK, '确定', pos=(100, 150))
        ok.SetDefault()
        wx.Button(self, wx.ID_CANCEL, '取消', pos=(250, 150))

        
