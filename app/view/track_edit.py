#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx

from app.globals.global_data import g
from app.dialog.point_edit_dlg import PointEditDlg
from app.dialog.srtm_track_dlg import SrtmTrackDialog
from app.globals import const
from app.service.checklist_mixin import CheckListCtrlMixin
from app.service.logger import do_log


class TrackEdit(wx.ListCtrl, CheckListCtrlMixin):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent=parent, style=wx.LC_REPORT | wx.LC_EDIT_LABELS)
        CheckListCtrlMixin.__init__(self)
        self._track_list = g.edit_track_list
        self.selected_track_line = None
        
        self._selected_index = 0
        self._popup_context = {}
        self._drag_from = 0
        self._dragging_item = False

        self.InsertColumn(0, '轨迹编辑区')
        self.SetColumnWidth(0, wx.LIST_AUTOSIZE_USEHEADER)

        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down, self)
        self.Bind(wx.EVT_MOTION, self.on_motion, self)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up, self)
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick, self)
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_down, self)
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.on_begin_edit_label, self)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.on_end_edit_label, self)
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_enter, self)

    # this is called by the base class when an item is checked/unchecked
    def OnCheckItem(self, index, flag):
        if flag:
            self._track_list[index].is_checked = True
        else:
            self._track_list[index].is_checked = False

        # 重画轨迹和chart以改变颜色
        g.frame.repaint(canvas=const.REDRAW_TRACK)

    def add_track_line(self, track_line):
        self._track_list.append(track_line)
        index = self.InsertStringItem(len(self._track_list), track_line.name)
        
    def set_selected_track_line(self, track_line):
        self.selected_track_line = track_line
        if track_line:
            self.Select(self._selected_index, on=0)
            self._selected_index = self._track_list.index(track_line)
            self.Select(self._selected_index)
            track_line.sel_start_idx = 0
            track_line.sel_end_idx = len(track_line.track_points) - 1
            track_line.compute_selected_segment_args()

    def on_left_down(self, event):
        CheckListCtrlMixin.OnLeftDown(self, event)
        index, flags = self.HitTest(event.GetPosition())
        if flags == wx.LIST_HITTEST_ONITEMLABEL:
            self._drag_from = index

        if 0 <= index <= len(self._track_list) - 1:
            track_line = self._track_list[index]
            self.set_selected_track_line(track_line)
            g.frame.repaint(canvas=const.REDRAW_TRACK)

    def on_motion(self, event):
        if event.Dragging() and event.LeftIsDown():
            self._dragging_item = True
            self.SetCursor(wx.Cursor(wx.CURSOR_BULLSEYE))
        else:
            self._dragging_item = False

    def on_enter(self, event):
        if self._dragging_item and not event.LeftIsDown():
            self._dragging_item = False
            self.SetCursor(wx.STANDARD_CURSOR)

    def on_left_up(self, event):
        if not self._dragging_item:
            return
        self._dragging_item = False
        self.SetCursor(wx.STANDARD_CURSOR)
        pt = event.GetPosition()
        index, flags = self.HitTest(event.GetPosition())
        if flags == wx.LIST_HITTEST_ONITEMLABEL:
            drag_to = index
            if drag_to == self._drag_from:
                do_log('自己不能移动到自己...')
                return
            self.DeleteItem(self._drag_from)
            self.InsertStringItem(drag_to, self._track_list[self._drag_from].name)
            self._track_list.insert(drag_to, self._track_list.pop(self._drag_from))
            if self._track_list[drag_to].is_checked:
                self.CheckItem(drag_to, True)
        else:
            event.Skip()

    def on_left_dclick(self, event):
        index, flags = self.HitTest(event.GetPosition())
        if flags == wx.LIST_HITTEST_ONITEMLABEL:
            if 0 <= index <= len(self._track_list) - 1:
                track_line = self._track_list[index]
                self.set_selected_track_line(track_line)
                g.map_canvas.zoom_to_track_line(track_line)

    def on_right_down(self, event):
        index, flags = self.HitTest(event.GetPosition())
        if flags == wx.LIST_HITTEST_ONITEMLABEL:
            self.popup_right_down(index)

    def popup_right_down(self, index, track_line=None):
        menu = wx.Menu()
        text = '移动至<用户数据>'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = index
        self.Bind(wx.EVT_MENU, self.on_move_to_user_data, menu_item)

        menu.AppendSeparator()
        text = '删除轨迹'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = index
        self.Bind(wx.EVT_MENU, self.on_delete_track, menu_item)
        menu.AppendSeparator()
        
        text = '删除高程数据'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = index
        self.Bind(wx.EVT_MENU, self.on_del_alt, menu_item)

        menu.AppendSeparator()
        text = '填充高程数据'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = index
        self.Bind(wx.EVT_MENU, self.on_download_alt, menu_item)

        menu.AppendSeparator()
        text = '轨迹起始点翻转'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = index
        self.Bind(wx.EVT_MENU, self.on_reverse_track, menu_item)

        if track_line and track_line is self.selected_track_line:
            menu.AppendSeparator()
            text = '编辑当前轨迹点'
            menu_item = menu.Append(-1, text)
            self._popup_context[menu_item.Id] = track_line
            self.Bind(wx.EVT_MENU, self.on_edit_track_point, menu_item)

        self.PopupMenu(menu)
        menu.Destroy()

    def on_move_to_user_data(self, event):
        index = self._popup_context[event.Id]
        track = self._track_list[index]
        track.parent = g.data_root.uuid
        g.add_data(g.data_root, track)
        g.track_tree.CollapseAll()
        g.track_tree.SelectItem(track.tree_node)
        self.DeleteItem(index)
        self._track_list.pop(index)
        if track is self.selected_track_line:
            self.selected_track_line = None
            g.frame.repaint(canvas=const.REDRAW_TRACK)
        
    def on_delete_track(self, event):
        dlg = wx.MessageDialog(self, '确认删除该轨迹？',
                               '确认删除？',
                               wx.YES_NO
                               )
        ret = dlg.ShowModal()
        dlg.Destroy()
        if ret != wx.ID_YES:
            return

        index = self._popup_context[event.Id]
        track_line = self._track_list[index]
        undo_action = {}
        undo_action['action'] = 'edit_del_track'
        undo_action['track'] = track_line
        g.undo_list = []
        g.undo_list.append(undo_action)
        if track_line is self.selected_track_line:
            self.selected_track_line = None
        self.DeleteItem(index)
        self._track_list.pop(index)
        g.frame.enable_undo()
        g.frame.repaint(canvas=const.REDRAW_TRACK)
        do_log('轨迹“%s”被删除...' % track_line.name)

    def on_reverse_track(self, event):
        index = self._popup_context[event.Id]
        track_line = self._track_list[index]

        if track_line.has_timestamp:
            dlg = wx.MessageDialog(self, '该轨迹含时间戳信息，翻转后时间信息将丢失。确认翻转？',
                                   '确认翻转？',
                                   wx.YES_NO
                                   )
            ret = dlg.ShowModal()
            dlg.Destroy()
            if ret != wx.ID_YES:
                return

        undo_action = {}
        undo_action['action'] = 'reverse'
        undo_action['track'] = track_line
        undo_action['has_timestamp'] = track_line.has_timestamp
        g.undo_list = []
        g.undo_list.append(undo_action)

        track_line.track_points.reverse()
        track_line.has_timestamp = False
        track_line.compute_track_line_args()
        self.set_selected_track_line(track_line)

        g.frame.enable_undo(False)
        do_log('轨迹“%s”方向已翻转...' % track_line.name)
        g.frame.repaint(canvas=const.REDRAW_TRACK)
        
    def on_edit_track_point(self, event):
        track_line = self._popup_context[event.Id]
        point = track_line.selected_point
        dlg = PointEditDlg(point=point)
        dlg.CentreOnParent()
        dlg.ShowModal()
        dlg.Destroy()
        g.frame.repaint(canvas=const.REDRAW_NONE)
        
    def on_del_alt(self, event):
        index = self._popup_context[event.Id]
        track_line = self._track_list[index]
        
        dlg = wx.MessageDialog(self, '将删除本轨迹中所有轨迹点的高程数据。该操作不可撤销，确认删除？',
                               '确认删除？',
                               wx.YES_NO
                               )
        ret = dlg.ShowModal()
        dlg.Destroy()
        if ret != wx.ID_YES:
            return
        
        for point in track_line.track_points:
            point.alt = 0.0
            
        do_log('已删除本轨迹中所有轨迹点的高程数据...')
        track_line.compute_track_line_args()
        self.set_selected_track_line(track_line)
        g.frame.repaint(canvas=const.REDRAW_TRACK)

    def on_download_alt(self, event):
        index = self._popup_context[event.Id]
        dialog = SrtmTrackDialog(track_line=self._track_list[index])
        dialog.CentreOnParent()
        dialog.Show()
            
    def on_begin_edit_label(self, event):
        item = event.GetItem()
        if not item:
            event.Veto()
            return

    def on_end_edit_label(self, event):
        item = event.GetItem()
        name = event.GetLabel()
        if item and name:
            self._track_list[item.Id].name = name
        if self.selected_track_line is self._track_list[item.Id]:
            g.frame.repaint(canvas=const.REDRAW_NONE)

