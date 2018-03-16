#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx
from app.globals import const


class MapSrcDlg(wx.Dialog):
    def __init__(self, g):
        wx.Dialog.__init__(self, None, -1, '配置在线地图', size=(500, 750))
        self.g = g

        wx.StaticText(self, -1, '透明地图源', (100, 35))
        self.trans_src_box = wx.CheckListBox(parent=self, id=-1, pos=(100, 60), size=(220, 120), name='透明地图源')
        for source in self.g.map_list_trans:
            self.trans_src_box.Append(source.name)
            if source.is_visible:
                self.trans_src_box.Check(self.trans_src_box.GetCount() - 1)
        self.trans_src_box.SetSelection(0)
        self.Bind(wx.EVT_CHECKLISTBOX, self.on_trans_checked, self.trans_src_box)

        trans_up_button = wx.Button(self, -1, '', pos=(350, 70), size=(30, 40))
        bmp = wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_OTHER, (16,16))
        trans_up_button.SetBitmap(bmp)
        self.Bind(wx.EVT_BUTTON, self.on_click_trans_up, trans_up_button)
        trans_down_button = wx.Button(self, -1, '', pos=(350, 130), size=(30, 40))
        bmp = wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_OTHER, (16, 16))
        trans_down_button.SetBitmap(bmp)
        self.Bind(wx.EVT_BUTTON, self.on_click_trans_down, trans_down_button)

        choices = []
        for source in self.g.map_list_main:
            choices.append(source.name)
        self.main_src_box = wx.RadioBox(parent=self, id=-1, label='背景地图源', pos=(100, 200), size=(220, 400), choices=choices, style=wx.RA_VERTICAL)
        self.main_src_box.SetBackgroundColour('WHITE')
        for i in range(len(self.g.map_list_main)):
            if self.g.map_list_main[i].is_visible:
                self.main_src_box.SetSelection(i)
        self.Bind(wx.EVT_RADIOBOX, self.on_main_selected, self.main_src_box)

        ok = wx.Button(self, wx.ID_OK, '确定', pos=(200, 630))
        ok.SetDefault()

    def on_trans_checked(self, event):
        sel_index = event.GetSelection()
        if self.trans_src_box.IsChecked(sel_index):
            self.g.map_list_trans[sel_index].is_visible = True
        else:
            self.g.map_list_trans[sel_index].is_visible = False
        self.repaint_map()

    def on_click_trans_up(self, event):
        sel_index = self.trans_src_box.GetSelection()
        if sel_index > 0:
            is_checked = self.trans_src_box.IsChecked(sel_index)
            self.trans_src_box.Delete(sel_index)
            self.trans_src_box.Insert(self.g.map_list_trans[sel_index].name, (sel_index - 1))
            self.trans_src_box.SetSelection(sel_index - 1)
            if is_checked:
                self.trans_src_box.Check(sel_index - 1)
            self.g.map_list_trans.insert(sel_index - 1, self.g.map_list_trans.pop(sel_index))
            self.repaint_map()

    def on_click_trans_down(self, event):
        sel_index = self.trans_src_box.GetSelection()
        if sel_index < self.trans_src_box.GetCount() - 1:
            is_checked = self.trans_src_box.IsChecked(sel_index)
            self.trans_src_box.Delete(sel_index)
            self.trans_src_box.Insert(self.g.map_list_trans[sel_index].name, (sel_index + 1))
            self.trans_src_box.SetSelection(sel_index + 1)
            if is_checked:
                self.trans_src_box.Check(sel_index + 1)
            self.g.map_list_trans.insert(sel_index + 1, self.g.map_list_trans.pop(sel_index))
            self.repaint_map()

    def on_main_selected(self, event):
        sel_index = event.GetInt()
        for i in range(len(self.g.map_list_main)):
            if i == sel_index:
                self.g.map_list_main[i].is_visible = True
            else:
                self.g.map_list_main[i].is_visible = False
        self.repaint_map()

    def repaint_map(self):
        self.g.map_canvas.repaint(mode=const.REDRAW_MAP)
        self.g.frame.show_status_info(show_map=True)

