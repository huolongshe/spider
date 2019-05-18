#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import copy
import uuid
import wx

from app.dialog.folder_style_dlg import FolderStyleDlg
from app.dialog.track_style_dlg import TrackStyleDlg
from app.globals import const
from app.resource import pin16_icons  # 必须存在
from app.service.kml_writer import write_kml
from app.service.kml_parser import parse_kml, parse_kmz
from app.service.gpx_parser import parse_gpx
from app.service.logger import do_log
from app.model.data_folder import DataFolder
from app.model.track_line import TrackLine
from app.model.way_point import WayPoint


class TrackTree(wx.TreeCtrl):
    def __init__(self, parent, g):
        wx.TreeCtrl.__init__(self, parent=parent, style=wx.TR_DEFAULT_STYLE | wx.TR_HAS_BUTTONS | wx.TR_EDIT_LABELS)
        self.g = g
        self._popup_context = {}  # 用于保存右键弹出菜单的菜单项上下文信息

        img_size = (16, 16)
        self._image_list = wx.ImageList(16, 16)  # 此处image_list必须设为成员变量，否则TreeCtrl显示不正常，原因不明
        self._folder_idx = self._image_list.Add(wx.ArtProvider.GetBitmap(wx.ART_NEW_DIR, wx.ART_OTHER, img_size))
        self._folder_open_idx = self._image_list.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER_OPEN, wx.ART_OTHER, img_size))
        self._wpt_idxes = [None] * 100
        for i in range(100):
            self._wpt_idxes[i] = self._image_list.Add(eval('pin16_icons.pin%02d' % i).GetBitmap())
        self.SetImageList(self._image_list)

        self._tree_root = self.AddRoot(text=self.g.data_root.name)
        self.SetItemData(self._tree_root, self.g.data_root)
        self.g.data_root.tree_node = self._tree_root
        self.SetItemImage(self._tree_root, self._folder_idx, wx.TreeItemIcon_Normal)
        self.SetItemImage(self._tree_root, self._folder_open_idx, wx.TreeItemIcon_Expanded)
        self.SetItemBold(self._tree_root)
        self.selected_track_line = None

        self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick, self)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down, self)
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_down, self)
        self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.on_begin_drag, self)
        self.Bind(wx.EVT_TREE_END_DRAG, self.on_end_drag, self)
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.on_begin_edit_label, self)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.on_end_edit_label, self)
        self.ExpandAll()

    def create_child_folder(self, parent_folder, name):
        child_folder = DataFolder(parent=parent_folder.uuid, name=name)
        self.g.add_data(parent_folder, child_folder)
        return child_folder

    def add_tree_node(self, parent, child):
        parent_node = parent.tree_node
        
        if self.GetChildrenCount(parent_node, False) == 0:
            if child.order_in_parent < 0:
                child.order_in_parent = 1000
            child_node = self.AppendItem(parent_node, child.name)
        else:
            prev_child = self.GetLastChild(parent_node)
            if child.order_in_parent < 0:
                child.order_in_parent = self.GetItemData(prev_child).order_in_parent + 1000
                child_node = self.AppendItem(parent_node, child.name)
            else:
                while prev_child.ID and child.order_in_parent < self.GetItemData(prev_child).order_in_parent:
                    prev_child = self.GetPrevSibling(prev_child)
                child_node = self.InsertItem(parent_node, prev_child, child.name)
        
        self.SetItemData(child_node, child)
        child.tree_node = child_node
        if isinstance(child, DataFolder):
            self.SetItemImage(child_node, self._folder_idx, wx.TreeItemIcon_Normal)
            self.SetItemImage(child_node, self._folder_open_idx, wx.TreeItemIcon_Expanded)
        else:
            if isinstance(child, TrackLine):
                self.set_track_image(child)
            elif isinstance(child, WayPoint):
                if child.bmp_index < 0:
                    child.bmp_index = self.g.default_wpt_bmp_index  # 不想在WayPoint类定义中注入全局变量g，所以把这两个参数的进一步初始化放到这儿
                if child.alt <= 0:
                    alt = self.g.srtm_mgr.get_alt_local(child.lon, child.lat)  # 同上, todo: 可能可以优化
                    if alt:
                        child.alt = alt
                self.set_wpt_image(child)
            if child.is_visible:
                self.SetItemBold(child_node, True)
            else:
                self.SetItemBold(child_node, False)
                
        return child_node

    def set_track_image(self, track_line):
        bmp = wx.Bitmap(16, 16)
        mdc = wx.MemoryDC(bmp)
        mdc.SetBackground(wx.Brush(self.GetBackgroundColour(), wx.BRUSHSTYLE_TRANSPARENT))
        mdc.Clear()
        mdc.SetPen(wx.Pen(wx.Colour(track_line.red, track_line.green, track_line.blue, track_line.alpha), 1, wx.PENSTYLE_SOLID))
        for (px, py) in track_line.points_list_for_draw[0]:
            mdc.DrawPoint(px, py)
        mdc.SelectObject(wx.NullBitmap)
        track_idx = self._image_list.Add(bmp)
        
        bmp1 = bmp.ConvertToDisabled()
        track_idx1 = self._image_list.Add(bmp1)
        
        self.SetItemImage(track_line.tree_node, track_idx1, wx.TreeItemIcon_Normal)
        self.SetItemImage(track_line.tree_node, track_idx, wx.TreeItemIcon_Selected)

    def set_wpt_image(self, wpt):
        self.SetItemImage(wpt.tree_node, self._wpt_idxes[wpt.bmp_index], wx.TreeItemIcon_Normal)

    def label_visible_data(self, data):
        if data.is_visible:
            self.SetItemBold(data.tree_node, True)
        else:
            self.SetItemBold(data.tree_node, False)

    def set_folder_visible(self, folder, visible):
        for lst in [self.g.track_list, self.g.wpt_list]:
            for child in lst:
                if child.parent == folder.uuid:
                    child.is_visible = visible
                    self.g.db_mgr.update_visible(child, commit=False)
                    self.label_visible_data(child)
        for child_folder in self.g.folder_list:
            if child_folder.parent == folder.uuid:
                self.set_folder_visible(child_folder, visible)
        self.g.db_mgr.commit()

    def on_left_down(self, event):
        pt = event.GetPosition()
        node, flags = self.HitTest(pt)
        if node:
            data = self.GetItemData(node)
            if isinstance(data, TrackLine):
                if data.is_visible:
                    self.selected_track_line = data
                    self.g.frame.repaint(canvas=const.REDRAW_TRACK)
        event.Skip()
        
    def on_left_dclick(self, event):
        pt = event.GetPosition()
        node, flags = self.HitTest(pt)
        if node:
            data = self.GetItemData(node)
            if isinstance(data, TrackLine):
                self.selected_track_line = data
                data.is_visible = True
                self.g.db_mgr.update_visible(data)
                self.label_visible_data(data)
                self.g.map_canvas.zoom_to_track_line(data)
            elif isinstance(data, WayPoint):
                data.is_visible = True
                self.g.db_mgr.update_visible(data)
                self.label_visible_data(data)
                self.g.map_canvas.zoom_to_lon_lat(13, data.lon, data.lat)
        event.Skip()

    def on_right_down(self, event):
        pt = event.GetPosition()
        node, flags = self.HitTest(pt)
        if node:
            data = self.GetItemData(node)
            if isinstance(data, DataFolder):
                self.popup_folder_operations(data)
            elif isinstance(data, TrackLine):
                self.popup_track_line_operations(data)
            elif isinstance(data, WayPoint):
                self.popup_wpt_operations(data)
            else:
                pass
        event.Skip()

    def popup_track_line_operations(self, track_line):
        menu = wx.Menu()
    
        text = '复制到编辑区'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = track_line
        self.Bind(wx.EVT_MENU, self.on_copy_to_edit, menu_item)
    
        menu.AppendSeparator()
        text = '保存至kml文件'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = track_line
        self.Bind(wx.EVT_MENU, self.on_save_kml, menu_item)
    
        menu.AppendSeparator()
        text = '编辑轨迹参数'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = track_line
        self.Bind(wx.EVT_MENU, self.on_edit_track_style, menu_item)
    
        menu.AppendSeparator()
        text = '隐藏轨迹' if track_line.is_visible else '显示轨迹'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = track_line
        self.Bind(wx.EVT_MENU, self.on_flap_track_visible, menu_item)
    
        menu.AppendSeparator()
        text = '删除轨迹'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = track_line
        self.Bind(wx.EVT_MENU, self.on_delete_track, menu_item)
    
        self.PopupMenu(menu)
        menu.Destroy()

    def popup_wpt_operations(self, wpt):
        menu = wx.Menu()
    
        menu.AppendSeparator()
        text = '隐藏路点' if wpt.is_visible else '显示路点'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = wpt
        self.Bind(wx.EVT_MENU, self.on_flap_wpt_visible, menu_item)
    
        menu.AppendSeparator()
        text = '删除路点'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = wpt
        self.Bind(wx.EVT_MENU, self.on_delete_wpt, menu_item)
    
        self.PopupMenu(menu)
        menu.Destroy()

    def on_copy_to_edit(self, event):
        track_line = self._popup_context[event.Id]
        temp_tree_node = track_line.tree_node
        track_line.tree_node = None
        track_line_copy = copy.deepcopy(track_line)
        track_line.tree_node = temp_tree_node
        track_line_copy.uuid = uuid.uuid1().__str__()
        track_line_copy.name = '副本_' + track_line.name
        track_line_copy.order_in_parent = -1
        self.g.track_edit.add_track_line(track_line_copy)

    def on_save_kml(self, event):
        data = self._popup_context[event.Id]
        if data:
            self.save_kml(data)
            
    def save_kml(self, data):
        dlg = wx.FileDialog(
            self, message='保存为...', defaultDir=os.getcwd(),
            defaultFile=data.name, wildcard=const.WILDCARD_KML, style=wx.FD_SAVE | wx.FD_CHANGE_DIR | wx.FD_OVERWRITE_PROMPT
        )
        dlg.SetFilterIndex(0)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            try:
                with open(path, 'wb') as fn:
                    fn.write(write_kml(data, self.g).encode('utf-8'))
            except:
                do_log('kml文件写入出错...')
        dlg.Destroy()

    def on_edit_track_style(self, event):
        track_line = self._popup_context[event.Id]
        if not track_line:
            return
    
        dlg = TrackStyleDlg(track_line)
        dlg.CentreOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            track_line.set_track_style(dlg.color[0],
                                       dlg.color[1],
                                       dlg.color[2],
                                       dlg.width.GetValue(),
                                       dlg.display_end_points.GetValue(),
                                       dlg.dash_style.GetSelection())
            self.set_track_image(track_line)
            self.g.db_mgr.update_track_style(track_line)
            self.g.frame.repaint(canvas=const.REDRAW_TRACK)
        dlg.Destroy()

    def on_flap_track_visible(self, event):
        track_line = self._popup_context[event.Id]
        track_line.is_visible = not track_line.is_visible
        self.g.db_mgr.update_visible(track_line)
        self.label_visible_data(track_line)
        if track_line is self.selected_track_line:
            self.selected_track_line = None
        self.g.frame.repaint(canvas=const.REDRAW_TRACK)

    def on_delete_track(self, event):
        dlg = wx.MessageDialog(self, '确认删除该轨迹？',
                               '确认删除？',
                               wx.YES_NO
                               )
        ret = dlg.ShowModal()
        dlg.Destroy()
        if ret != wx.ID_YES:
            return
    
        track_line = self._popup_context[event.Id]
        undo_action = {}
        undo_action['action'] = 'tree_del_track'
        undo_action['track'] = track_line
        self.g.undo_list = []
        self.g.undo_list.append(undo_action)
        if track_line is self.selected_track_line:
            self.selected_track_line = None
        self.g.del_track_line(track_line)
        self.g.frame.enable_undo()
        self.g.frame.repaint(canvas=const.REDRAW_TRACK)
        do_log('轨迹“%s”被删除...' % track_line.name)

    def on_flap_wpt_visible(self, event):
        wpt = self._popup_context[event.Id]
        wpt.is_visible = not wpt.is_visible
        self.g.db_mgr.update_visible(wpt)
        self.label_visible_data(wpt)
        self.g.frame.repaint(canvas=const.REDRAW_COPY)

    def on_delete_wpt(self, event):
        wpt = self._popup_context[event.Id]
        self.g.del_wpt(wpt)
        self.g.frame.repaint(canvas=const.REDRAW_COPY)
        do_log('路点“%s”被删除...' % wpt.name)

    def popup_folder_operations(self, folder):
        menu = wx.Menu()

        text = '导入轨迹文件'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = folder
        self.Bind(wx.EVT_MENU, self.on_open_file_in_folder, menu_item)
        menu.AppendSeparator()

        text = '保存至kml文件'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = folder
        self.Bind(wx.EVT_MENU, self.on_save_kml, menu_item)

        menu.AppendSeparator()
        text = '新建文件夹'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = folder
        self.Bind(wx.EVT_MENU, self.on_create_file_folder, menu_item)

        if folder is not self.g.data_root:
            menu.AppendSeparator()
            text = '删除文件夹'
            menu_item = menu.Append(-1, text)
            self._popup_context[menu_item.Id] = folder
            self.Bind(wx.EVT_MENU, self.on_delete_file_folder, menu_item)

        menu.AppendSeparator()
        text = '显示轨迹/路点'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = folder
        self.Bind(wx.EVT_MENU, self.on_display_all, menu_item)

        menu.AppendSeparator()
        text = '隐藏轨迹/路点'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = folder
        self.Bind(wx.EVT_MENU, self.on_hide_all, menu_item)

        menu.AppendSeparator()
        text = '修改轨迹样式'
        menu_item = menu.Append(-1, text)
        self._popup_context[menu_item.Id] = folder
        self.Bind(wx.EVT_MENU, self.on_edit_folder_style, menu_item)
    
        self.PopupMenu(menu)
        menu.Destroy()

    def on_open_file(self, event):
        self.choose_file_and_open(self.g.data_root)

    def on_open_file_in_folder(self, event):
        parent_folder = self._popup_context[event.Id]
        if parent_folder:
            self.choose_file_and_open(parent_folder)

    def choose_file_and_open(self, parent_folder):
        dlg = wx.FileDialog(
            self, message='请选择轨迹文件',
            defaultDir=os.getcwd(),
            defaultFile='',
            wildcard=const.WILDCARD,
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR
        )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            self.open_track_files(paths, parent_folder)
        dlg.Destroy()

    def open_track_files(self, paths, parent_folder):
        do_log('正在加载轨迹文件，请稍候...')
        self.CollapseAll()

        first_track = None
        first_wpt = None
        fpx_min_list = []
        fpx_max_list = []
        fpy_min_list = []
        fpy_max_list = []
        for path in paths:
            if path[-4:] == '.kml':
                data_list = parse_kml(path, parent_folder.uuid)
            elif path[-4:] == '.kmz':
                data_list = parse_kmz(path, parent_folder.uuid)
            elif path[-4:] == '.gpx':
                data_list = parse_gpx(path, parent_folder.uuid)
            else:
                do_log('轨迹文件后缀不符...')
                continue
            
            for data in data_list:
                data_parent = self.g.get_parent_folder(data)
                self.g.add_data(data_parent, data, commit=False)
                if isinstance(data, TrackLine):
                    fpx_min_list.append(data.fpx_min)
                    fpx_max_list.append(data.fpx_max)
                    fpy_min_list.append(data.fpy_min)
                    fpy_max_list.append(data.fpy_max)
                    if not first_track:
                        first_track = data
                elif isinstance(data, WayPoint):
                    fpx_min_list.append(data.fpx)
                    fpx_max_list.append(data.fpx)
                    fpy_min_list.append(data.fpy)
                    fpy_max_list.append(data.fpy)
                    if not first_wpt:
                        first_wpt = data
        self.g.db_mgr.commit()

        if fpx_min_list:
            if first_track:
                self.selected_track_line = first_track
                self.SelectItem(first_track.tree_node)
            elif first_wpt:
                self.SelectItem(first_wpt.tree_node)
            self.g.map_canvas.zoom_to_range(min(fpx_min_list), max(fpx_max_list), min(fpy_min_list), max(fpy_max_list))
            self.g.frame.repaint(const.REDRAW_NONE)
            do_log('轨迹文件加载完成...')
        else:
            do_log('轨迹文件无内容...')

    def on_create_file_folder(self, event):
        parent_folder = self._popup_context[event.Id]
        if parent_folder:
            folder = self.create_child_folder(parent_folder, '新建文件夹')
            self.SelectItem(folder.tree_node)

    def on_delete_file_folder(self, event):
        folder = self._popup_context[event.Id]
        if folder:
            dlg = wx.MessageDialog(self, '确认删除该文件夹？',
                                   '确认删除？',
                                   wx.YES_NO
                                   )
            ret = dlg.ShowModal()
            dlg.Destroy()
            if ret != wx.ID_YES:
                return
        
            deleted = self.g.del_folder(folder, commit=False)
            self.g.db_mgr.commit()
            if self.selected_track_line in deleted:
                self.selected_track_line = None

            undo_action = {}
            undo_action['action'] = 'tree_del_folder'
            undo_action['deleted'] = deleted
            self.g.undo_list = []
            self.g.undo_list.append(undo_action)

            self.g.frame.enable_undo()
            self.g.frame.repaint(canvas=const.REDRAW_TRACK)
            do_log('文件夹“%s”被删除...' % folder.name)

    def on_display_all(self, event):
        folder = self._popup_context[event.Id]
        if folder:
            self.set_folder_visible(folder, True)
        self.g.frame.repaint(canvas=const.REDRAW_TRACK)

    def on_hide_all(self, event):
        folder = self._popup_context[event.Id]
        if folder:
            self.set_folder_visible(folder, False)
        if self.selected_track_line and not self.selected_track_line.is_visible:
            self.selected_track_line = None
        self.g.frame.repaint(canvas=const.REDRAW_TRACK)

    def on_edit_folder_style(self, event):
        folder = self._popup_context[event.Id]
        if folder:
            dlg = FolderStyleDlg()
            dlg.CentreOnParent()
            if dlg.ShowModal() == wx.ID_OK:
                dashed = dlg.dash_style.GetSelection()
                width = dlg.width.GetValue()
                red = dlg.color[0]
                green = dlg.color[1]
                blue = dlg.color[2]
                draw_endpoints = dlg.display_end_points.GetValue()
                self.set_folder_style(folder, red, green, blue, width, draw_endpoints, dashed)

                self.g.frame.repaint(canvas=const.REDRAW_TRACK)
            dlg.Destroy()

    def set_folder_style(self, folder, red, green, blue, width, draw_endpoints, dashed):
        for child in self.g.track_list:
            if child.parent == folder.uuid:
                child.set_track_style(red, green, blue, width, draw_endpoints, dashed)
                self.set_track_image(child)
                self.g.db_mgr.update_track_style(child, commit=False)
        for child_folder in self.g.folder_list:
            if child_folder.parent == folder.uuid:
                self.set_folder_style(child_folder, red, green, blue, width, draw_endpoints, dashed)
        self.g.db_mgr.commit()

    def on_begin_drag(self, event):
        node = event.GetItem()
        if node == self._tree_root:
            do_log('根目录不能移动...')
            return
        self._src_node = node
        event.Allow()

    def on_end_drag(self, event):
        dst_node = event.GetItem()
        if not dst_node.IsOk():
            do_log('不能移动到这里...')
            return
        if self.is_ancestor(self._src_node, dst_node):
            do_log('不能移动到自己或自己的下级...')
            return

        src_data = self.GetItemData(self._src_node)
        src_parent_data = self.GetItemData(self.GetItemParent(self._src_node))

        dst_data = self.GetItemData(dst_node)
        if isinstance(dst_data, TrackLine) or isinstance(dst_data, WayPoint):
            dst_parent_node = self.GetItemParent(dst_node)
            dst_prev_node = self.GetPrevSibling(dst_node)
            prev_order = self.GetItemData(dst_prev_node).order_in_parent if dst_prev_node.ID else 0
            src_data.order_in_parent = (dst_data.order_in_parent + prev_order) / 2.0
        else:
            dst_parent_node = dst_node
            if self.GetChildrenCount(dst_parent_node) == 0:
                src_data.order_in_parent = 1000
            else:
                src_data.order_in_parent = self.GetItemData(self.GetLastChild(dst_parent_node)).order_in_parent + 1000
        self.g.db_mgr.update_order_in_parent(src_data)
        dst_parent_data = self.GetItemData(dst_parent_node)

        if dst_parent_data is not src_parent_data:
            src_data.parent = dst_parent_data.uuid
            self.g.db_mgr.update_parent_uuid(src_data, dst_parent_data.uuid)

        if isinstance(src_data, DataFolder):
            if self.g.folder_list.index(src_data) < self.g.folder_list.index(dst_parent_data):
                self.g.del_and_append_folder(src_data)

        self.Delete(self._src_node)

        if isinstance(src_data, DataFolder):
            node = self.add_tree_folder(dst_parent_data, src_data)
        else:
            node = self.add_tree_node(dst_parent_data, src_data)
        self.SelectItem(node)

    def add_tree_folder(self, parent, child):  # 仅在树上节点移动时在on_end_drag中被调用
        node = self.add_tree_node(parent, child)
        for folder in self.g.folder_list:
            if folder.parent == child.uuid:
                self.add_tree_folder(child, folder)
        for track_line in self.g.track_list:
            if track_line.parent == child.uuid:
                self.add_tree_node(child, track_line)
        for wpt in self.g.wpt_list:
            if wpt.parent == child.uuid:
                self.add_tree_node(child, wpt)
        return node
        
    def is_ancestor(self, src, dst):
        if dst == src:
            return True
        elif dst == self._tree_root:
            return False
        else:
            return self.is_ancestor(src, self.GetItemParent(dst))

    def on_begin_edit_label(self, event):
        node = event.GetItem()
        if not node:
            event.Veto()
            return
        if node == self._tree_root:
            do_log('根目录名不能更改...')
            event.Veto()
            return

    def on_end_edit_label(self, event):
        node = event.GetItem()
        name = event.GetLabel()
        if not node or not name:
            return
        data = self.GetItemData(node)
        data.name = name
        self.g.db_mgr.update_name(data)
        if self.selected_track_line is data:
            self.g.frame.repaint(canvas=const.REDRAW_NONE)

