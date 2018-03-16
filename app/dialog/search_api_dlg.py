#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx


class SearchApiDlg(wx.Dialog):
    def __init__(self, g):
        wx.Dialog.__init__(self, None, -1, '', size=(480, 250))

        choices = ['谷歌',
                   '百度']
        self.search_api = wx.RadioBox(parent=self, id=-1, label='请选择地名搜索优先接口',
                                    pos=(30, 30), size=(410, 100),
                                    choices=choices, style=wx.RA_VERTICAL)
        self.search_api.SetSelection(g.search_api)

        ok = wx.Button(self, wx.ID_OK, '确定', pos=(100, 150))
        ok.SetDefault()
        wx.Button(self, wx.ID_CANCEL, '取消', pos=(250, 150))
