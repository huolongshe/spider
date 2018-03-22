#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import copy
import wx
import wx.adv
import wx.lib.agw.pybusyinfo as PBI

from app.globals import const
from app.globals.global_data import GlobalData
from app.resource import app_icons
from app.dialog.default_pin_dlg import DefaultPinDlg
from app.dialog.map_src_dlg import MapSrcDlg
from app.dialog.search_dlg import WptSearchDlg, RouteSearchDlg
from app.dialog.search_api_dlg import SearchApiDlg
from app.dialog.srtm_src_dlg import SrtmSrcDlg
from app.model.track_line import TrackLine
from app.model.way_point import WayPoint
from app.model.photo import Photo
from app.service import auto_id
from app.service import search
from app.service.logger import do_log
from app.view.map_canvas import MapCanvas
from app.view.track_chart import TrackChart
from app.view.track_edit import TrackEdit
from app.view.track_tree import TrackTree


class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title='%s - %s' % (const.APP_NAME, const.APP_VERSION))
        self.g = GlobalData(self)

        self.init_splitter_windows()  # 需要在frame对象初始化之后，show之前，执行
        self.create_menu_bar()  # 需要在self.init_splitter_windows()之后调用，因为其中引用到了生成的子窗口
        self._toolbar = self.create_tool_bar()
        self._status_bar = self.CreateStatusBar()
        self._status_bar.SetFieldsCount(4)
        self._status_bar.SetStatusWidths([-2, -1, -1, -2])
        self.show_status_info(show_map=True, show_edit_status=True)
        self.SetIcon(app_icons.zhangjiashan.GetIcon())
        self.SetMinSize((800, 600))
        self.Bind(wx.EVT_MAXIMIZE, self.on_maximize, self)  # 需要放在self.Maximize()之前调用，才能正确获取width和height的值
        self.Bind(wx.EVT_CLOSE, self.on_close, self)

        self.Maximize()  # 必须在frame内其他窗口都布置妥当，wx.EVT_MAXIMIZE事件绑定之后再调用执行
        self.Show(True)  # 需要在splitter窗口初始化之后再执行
        # self.Bind(wx.EVT_SIZE, self.on_resize, self)  # frame的EVT_SIZE事件需要推迟到现在才能绑定
        # EVT_SIZE绑定后，全屏会显示不全；目前wx4中解绑定失败，所以暂时注解掉...

        busy = PBI.PyBusyInfo('数据加载中，请稍候...', parent=None, title='正在启动>>>')
        self.g.map_canvas.init_after_frame_shown()  # 需要在frame对象初始化并show之后再执行
        self.g.init_data_and_add_to_tree()
        del busy

    def on_maximize(self, event):
        if self.g.full_screen:
            return
        self._splitter_left.SetSashPosition(self.GetSize().height * 3 // 5, True)
        self._splitter_middle.SetSashPosition(self.GetSize().height * 3 // 4, True)
        self._splitter_leftmiddle.SetSashPosition(self.GetSize().width * 1 // 9, True)
        self._splitter_right.SetSashPosition(self.GetSize().height * 3 // 5, True)
        self._splitter_top.SetSashPosition(self.GetSize().width * 7 // 8, True)

    def on_resize(self, event):
        if self.g.full_screen:
            return
        self._splitter_left.SetSashPosition(self.GetSize().height * 3 // 5, True)
        self._splitter_middle.SetSashPosition(self.GetSize().height * 3 // 4, True)
        self._splitter_leftmiddle.SetSashPosition(self.GetSize().width * 1 // 9, True)
        self._splitter_right.SetSashPosition(self.GetSize().height * 3 // 5, True)
        self._splitter_top.SetSashPosition(self.GetSize().width * 7 // 8, True)

    def on_close(self, event):
        if self.g.edit_track_list:
            dlg = wx.MessageDialog(self, '编辑区内容在退出时将清空，建议备份后再退出。\n确认退出？',
                                   '真的退出？',
                                   wx.YES_NO
                                   )
            ret = dlg.ShowModal()
            dlg.Destroy()
            if ret != wx.ID_YES:
                return

        self.g.write_cfg()

        self.g.db_mgr.close_db()
        self.Destroy()

    def show_status_info(self, show_map=False, show_edit_status=False, zoom=None, pos=None):
        if show_map:
            if self.g.hide_map:
                self._status_bar.SetStatusText('当前地图源：无')
                return
            current_maps_str = ''
            for map_source in self.g.map_list_main:
                if map_source.is_visible:
                    current_maps_str += (map_source.name + '  ')
            for map_source in self.g.map_list_trans[-1::-1]:
                if map_source.is_visible:
                    current_maps_str += (map_source.name + '  ')
            self._status_bar.SetStatusText('当前地图源：%s' % current_maps_str, 0)
            
        if show_edit_status:
            self._status_bar.SetStatusText('当前状态：' + ('编辑' if self.g.in_editing else '浏览'), 1)
            
        if zoom:
            self._status_bar.SetStatusText('缩放级别：%d' % zoom, 2)
            
        if pos:
            self._status_bar.SetStatusText('东经：%.08f，北纬：%.08f' % pos, 3)
            
    def enable_undo(self, enable=True):
        self._menu_undo.Enable(enable)
        self._tb_undo.Enable(enable)
        self._toolbar.Realize()

    def init_splitter_windows(self):
        self._splitter_top = wx.SplitterWindow(self, style=wx.SP_3D)
        self._splitter_top.SetMinimumPaneSize(1)

        self._splitter_leftmiddle = wx.SplitterWindow(self._splitter_top, style=wx.SP_3D)
        self._splitter_leftmiddle.SetMinimumPaneSize(1)

        self._splitter_left = wx.SplitterWindow(self._splitter_leftmiddle, style=wx.SP_3D)
        self._splitter_left.SetMinimumPaneSize(1)
        self.g.track_tree = TrackTree(parent=self._splitter_left, g=self.g)
        self.g.track_edit = TrackEdit(parent=self._splitter_left, g=self.g)
        self._splitter_left.SplitHorizontally(self.g.track_tree, self.g.track_edit)
        self._splitter_left.SetSashPosition(self.GetSize().height * 3 // 5, True)

        self._splitter_middle = wx.SplitterWindow(self._splitter_leftmiddle, style=wx.SP_3D)
        self._splitter_middle.SetMinimumPaneSize(1)
        self.g.map_canvas = MapCanvas(parent=self._splitter_middle, g=self.g)
        self.g.track_chart = TrackChart(parent=self._splitter_middle, g=self.g)
        self._splitter_middle.SplitHorizontally(self.g.map_canvas, self.g.track_chart)
        self._splitter_middle.SetSashPosition(self.GetSize().height * 3 // 4, True)

        self._splitter_leftmiddle.SplitVertically(self._splitter_left, self._splitter_middle)
        self._splitter_leftmiddle.SetSashPosition(self.GetSize().width * 1 // 9, True)

        self._splitter_right = wx.SplitterWindow(self._splitter_top, style=wx.SP_3D)
        self._splitter_right.SetMinimumPaneSize(1)
        self.g.track_details = wx.TextCtrl(self._splitter_right, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        self.g.logger = wx.TextCtrl(self._splitter_right, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        wx.Log.SetActiveTarget(wx.LogTextCtrl(self.g.logger))

        self._splitter_right.SplitHorizontally(self.g.track_details, self.g.logger)
        self._splitter_right.SetSashPosition(self.GetSize().height * 3 // 5, True)

        self._splitter_top.SplitVertically(self._splitter_leftmiddle, self._splitter_right)
        self._splitter_top.SetSashPosition(self.GetSize().width * 7 // 8, True)

        self.g.track_tree.Enable(True)
        self.g.track_edit.Enable(False)


    def create_menu_bar(self):
        menu_bar = wx.MenuBar()
        self.SetMenuBar(menu_bar)

        menu_file = wx.Menu()
        menu_bar.Append(menu_file, '文件')
        self._menu_open = menu_file.Append(-1, '导入轨迹文件', '导入轨迹文件')
        self.Bind(wx.EVT_MENU, self.g.track_tree.on_open_file, self._menu_open)
        menu_file.AppendSeparator()
        menu_quit = menu_file.Append(-1, '退出', '退出程序')
        self.Bind(wx.EVT_MENU, self.on_close, menu_quit)

        menu_map = wx.Menu()
        menu_bar.Append(menu_map, '地图')
        menu_map_dlg = menu_map.Append(-1, '配置在线地图', '查看/配置在线地图源')
        self.Bind(wx.EVT_MENU, self.on_map_src_dlg, menu_map_dlg)
        menu_map.AppendSeparator()
        self._menu_map_hide = menu_map.Append(-1, '隐藏所有地图', '隐藏/显示在线地图')
        self.Bind(wx.EVT_MENU, self.on_map_hide, self._menu_map_hide)
        menu_map.AppendSeparator()
        menu_map_full_screen = menu_map.Append(-1, '全屏显示地图', '全屏显示地图')
        self.Bind(wx.EVT_MENU, self.on_map_full_screen, menu_map_full_screen)
        menu_map.AppendSeparator()
        self._menu_map_clear_cache = menu_map.Append(-1, '清空地图缓存', '清空本地硬盘中缓存的地图瓦片')
        self.Bind(wx.EVT_MENU, self.on_map_clear_cache, self._menu_map_clear_cache)
        menu_map.AppendSeparator()
        self._menu_map_screenshot = menu_map.Append(-1, '地图窗口截屏', '地图窗口截屏并保存至文件')
        self.Bind(wx.EVT_MENU, self.on_map_screenshot, self._menu_map_screenshot)
        menu_map.AppendSeparator()
        self._menu_map_download = menu_map.Append(-1, '下载离线地图', '批量下载鼠标框选区域的地图瓦片并进行无缝拼接')
        self.Bind(wx.EVT_MENU, self.on_map_download, self._menu_map_download)

        menu_edit = wx.Menu()
        menu_bar.Append(menu_edit, '轨迹')
        self._menu_edit_status = menu_edit.Append(-1, '进入编辑状态', '进入/退出轨迹编辑状态')
        self.Bind(wx.EVT_MENU, self.on_edit_status, self._menu_edit_status)
        menu_edit.AppendSeparator()
        self._menu_set_start_pt = menu_edit.Append(-1, '设置起点', '设置轨迹段起点')
        self.Bind(wx.EVT_MENU, self.on_set_start_pt, self._menu_set_start_pt)
        self._menu_set_start_pt.Enable(False)
        self._menu_set_end_pt = menu_edit.Append(-1, '设置终点', '设置轨迹段终点')
        self.Bind(wx.EVT_MENU, self.on_set_end_pt, self._menu_set_end_pt)
        self._menu_set_end_pt.Enable(False)
        menu_edit.AppendSeparator()
        self._menu_delete_segment = menu_edit.Append(-1, '删除片段', '删除选中轨迹片段')
        self.Bind(wx.EVT_MENU, self.on_delete_segment, self._menu_delete_segment)
        self._menu_delete_segment.Enable(False)
        self._menu_delete_point = menu_edit.Append(-1, '删除点', '删除当前轨迹点')
        self.Bind(wx.EVT_MENU, self.on_delete_point, self._menu_delete_point)
        self._menu_delete_point.Enable(False)
        menu_edit.AppendSeparator()
        self._menu_split = menu_edit.Append(-1, '分割', '以当前轨迹点分割轨迹段')
        self.Bind(wx.EVT_MENU, self.on_split, self._menu_split)
        self._menu_split.Enable(False)
        self._menu_merge = menu_edit.Append(-1, '合并', '合并轨迹段')
        self.Bind(wx.EVT_MENU, self.on_merge, self._menu_merge)
        self._menu_merge.Enable(False)
        menu_edit.AppendSeparator()
        self._menu_undo = menu_edit.Append(-1, '回退', '撤销刚才操作，回退至前一步')
        self.Bind(wx.EVT_MENU, self.on_undo, self._menu_undo)
        self._menu_undo.Enable(False)

        menu_wpt_pin = wx.Menu()
        menu_bar.Append(menu_wpt_pin, '路点')
        self._menu_default_pin = menu_wpt_pin.Append(-1, '更改默认图钉', '更改路点图钉的默认显示样式')
        self.Bind(wx.EVT_MENU, self.on_default_pin, self._menu_default_pin)
        menu_wpt_pin.AppendSeparator()
        self._menu_hide_wpts = menu_wpt_pin.Append(-1, '隐藏所有图钉', '隐藏所有路点图钉')
        self.Bind(wx.EVT_MENU, self.on_hide_wpts, self._menu_hide_wpts)
        menu_wpt_pin.AppendSeparator()
        self._menu_del_all_wpts = menu_wpt_pin.Append(-1, '删除所有路点', '删除所有路点数据')
        self.Bind(wx.EVT_MENU, self.on_del_all_wpts, self._menu_del_all_wpts)

        menu_photo = wx.Menu()
        menu_bar.Append(menu_photo, '照片')
        self._menu_photo_add = menu_photo.Append(-1, '添加照片', '将有地理位置信息的照片添加至地图中相应位置')
        self.Bind(wx.EVT_MENU, self.on_photo_add, self._menu_photo_add)
        menu_photo.AppendSeparator()
        self._menu_photo_clear = menu_photo.Append(-1, '清空照片', '删除地图上所有照片')
        self.Bind(wx.EVT_MENU, self.on_photo_clear, self._menu_photo_clear)

        menu_srtm = wx.Menu()
        menu_bar.Append(menu_srtm, '高程')
        self._menu_srtm_src = menu_srtm.Append(-1, '高程数据源', '设置高程数据下载地址')
        self.Bind(wx.EVT_MENU, self.on_srtm_src, self._menu_srtm_src)

        menu_search = wx.Menu()
        menu_bar.Append(menu_search, '搜索')
        self._menu_search_wpt = menu_search.Append(-1, '搜索地点', '搜索地点')
        self.Bind(wx.EVT_MENU, self.on_search_wpt, self._menu_search_wpt)
        menu_search.AppendSeparator()
        self._menu_search_route = menu_search.Append(-1, '行车路线', '行车路线规划')
        self.Bind(wx.EVT_MENU, self.on_search_route, self._menu_search_route)
        menu_search.AppendSeparator()
        self._menu_search_api = menu_search.Append(-1, '接口配置', '选择搜索接口API')
        self.Bind(wx.EVT_MENU, self.on_search_api, self._menu_search_api)

        menu_help = wx.Menu()
        menu_bar.Append(menu_help, '帮助')
        menu_about = menu_help.Append(-1, '关于', '关于')
        self.Bind(wx.EVT_MENU, self.on_about, menu_about)

    def create_tool_bar(self):
        bar_size = (16, 16)
        open_bmp = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, bar_size)
        map_dlg_bmp = app_icons.map_dlg.GetBitmap()
        edit_enter_bmp = app_icons.edit_enter.GetBitmap()
        edit_quit_bmp = app_icons.edit_quit.GetBitmap()
        start_bmp = app_icons.start.GetBitmap()
        end_bmp = app_icons.end.GetBitmap()
        del_seg_bmp = app_icons.del_seg.GetBitmap()
        del_pt_bmp = app_icons.del_pt.GetBitmap()
        split_bmp = app_icons.split.GetBitmap()
        merge_bmp = app_icons.merge.GetBitmap()
        undo_bmp = wx.ArtProvider.GetBitmap(wx.ART_UNDO, wx.ART_TOOLBAR, bar_size)

        tb = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        tb.SetToolBitmapSize(bar_size)

        self._tb_open = tb.AddTool(-1, label='导入轨迹文件', bitmap=open_bmp, shortHelp='导入轨迹文件')
        self.Bind(wx.EVT_TOOL, self.g.track_tree.on_open_file, self._tb_open)
        tb.AddSeparator()
        tb_map_dlg = tb.AddTool(-1, label='配置在线地图', bitmap=map_dlg_bmp, shortHelp='查看/配置在线地图源')
        self.Bind(wx.EVT_TOOL, self.on_map_src_dlg, tb_map_dlg)
        tb.AddSeparator()
        self._tb_edit_enter = tb.AddTool(-1, label='进入编辑', bitmap=edit_enter_bmp, shortHelp='进入编辑状态')
        self.Bind(wx.EVT_TOOL, self.on_edit_status, self._tb_edit_enter)
        self._tb_edit_quit = tb.AddTool(-1, label='退出编辑', bitmap=edit_quit_bmp, shortHelp='退出编辑状态')
        self.Bind(wx.EVT_TOOL, self.on_edit_status, self._tb_edit_quit)
        tb.AddSeparator()
        self._tb_set_start_pt = tb.AddTool(-1, label='设置起点', bitmap=start_bmp, shortHelp='设置轨迹段起点')
        self.Bind(wx.EVT_TOOL, self.on_set_start_pt, self._tb_set_start_pt)
        self._tb_set_end_pt = tb.AddTool(-1, label='设置终点', bitmap=end_bmp, shortHelp='设置轨迹段终点')
        self.Bind(wx.EVT_TOOL, self.on_set_end_pt, self._tb_set_end_pt)
        tb.AddSeparator()
        self._tb_delete_segment = tb.AddTool(-1, label='删除片段', bitmap=del_seg_bmp, shortHelp='删除选中轨迹片段')
        self.Bind(wx.EVT_TOOL, self.on_delete_segment, self._tb_delete_segment)
        self._tb_delete_point = tb.AddTool(-1, label='删除点', bitmap=del_pt_bmp, shortHelp='删除当前轨迹点')
        self.Bind(wx.EVT_TOOL, self.on_delete_point, self._tb_delete_point)
        tb.AddSeparator()
        self._tb_split = tb.AddTool(-1, label='分割', bitmap=split_bmp, shortHelp='以当前轨迹点分割轨迹段')
        self.Bind(wx.EVT_TOOL, self.on_split, self._tb_split)
        self._tb_merge = tb.AddTool(-1, label='合并', bitmap=merge_bmp, shortHelp='合并轨迹段')
        self.Bind(wx.EVT_TOOL, self.on_merge, self._tb_merge)
        tb.AddSeparator()
        self._tb_undo = tb.AddTool(-1, label='回退', bitmap=undo_bmp, shortHelp='撤销刚才操作，回退至前一步')
        self.Bind(wx.EVT_TOOL, self.on_undo, self._tb_undo)

        self._tb_open.Enable(True)
        self._tb_edit_enter.Enable(True)
        self._tb_edit_quit.Enable(False)
        self._tb_set_start_pt.Enable(False)
        self._tb_set_end_pt.Enable(False)
        self._tb_delete_segment.Enable(False)
        self._tb_delete_point.Enable(False)
        self._tb_split.Enable(False)
        self._tb_merge.Enable(False)
        self._tb_undo.Enable(False)

        tb.Realize()
        return tb

    def on_map_src_dlg(self, event):
        dialog = MapSrcDlg(self.g)
        dialog.CentreOnParent()
        dialog.ShowModal()
        dialog.Destroy()

    def on_map_hide(self, event):
        if self.g.hide_map:
            self.g.hide_map = False
            self._menu_map_hide.SetItemLabel('隐藏所有地图')
        else:
            self.g.hide_map = True
            self._menu_map_hide.SetItemLabel('显示在线地图')
            self.show_status_info(show_map=True)
        self.repaint(canvas=const.REDRAW_MAP)

    def on_map_full_screen(self, event):
        if self.g.full_screen:
            self.g.full_screen = False
            self.ShowFullScreen(False)
            self.Maximize()
            # self.Bind(wx.EVT_SIZE, self.on_resize, self)
        else:
            self.g.full_screen = True
            # self.Unbind(wx.EVT_SIZE, handler=self.on_resize, source=self)  # 解除EVT_SIZE绑定后全屏才能成功。todo:此处解绑不成功
            self.ShowFullScreen(True, style=wx.FULLSCREEN_ALL)
            self._splitter_middle.SetSashPosition(self.GetSize().height-1, True)
            self._splitter_leftmiddle.SetSashPosition(1, True)
            self._splitter_top.SetSashPosition(self.GetSize().width-1, True)

    def on_map_clear_cache(self, event):
        dlg = wx.MessageDialog(self, '确认要清空本地硬盘中缓存的地图瓦片图片？',
                               '提示',
                               wx.YES_NO
                               )
        ret = dlg.ShowModal()
        dlg.Destroy()
        if ret != wx.ID_YES:
            return
        do_log('开始清空地图缓存...')
        self.g.map_canvas.SetCursor(wx.Cursor(wx.CURSOR_WAIT))
        root_dir = self.g.tile_mgr.get_cache_path()
        file_list = os.listdir(root_dir)
        for f in file_list:
            file_path = os.path.join(root_dir, f)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
        self.g.map_canvas.SetCursor(wx.STANDARD_CURSOR)
        do_log('地图缓存清空完毕！')

    def on_map_download(self, event):
        self.g.downloading_map = True
        do_log('请按住鼠标左键拖动来框选欲下载区域...')
        self.g.map_canvas.SetCursor(wx.Cursor(wx.CURSOR_SIZING))
        
    def on_map_screenshot(self, event):
        dlg = wx.FileDialog(
            self, message='保存为...', defaultDir=os.getcwd(),
            defaultFile='我的地图',
            wildcard='BMP文件 (*.bmp)|*.bmp|JPG文件 (*.jpg)|*.jpg|PNG文件 (*.png)|*.png',
            style=wx.FD_SAVE | wx.FD_CHANGE_DIR | wx.FD_OVERWRITE_PROMPT
        )
        dlg.SetFilterIndex(0)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            bmp = wx.Bitmap(self.g.map_canvas.GetSize().width, self.g.map_canvas.GetSize().height)
            mdc = wx.MemoryDC(bmp)
            mdc.Blit(0, 0, self.g.map_canvas.GetSize().width, self.g.map_canvas.GetSize().height, self.g.map_canvas._dc, 0, 0)
            mdc.SelectObject(wx.NullBitmap)

            if path[-4:] == '.bmp':  # JPG文件压缩失真太狠，无法调整，因此缺省将bmp格式放在第一个
                bmp.SaveFile(path, wx.BITMAP_TYPE_BMP)
            elif path[-4:] == '.jpg':
                bmp.SaveFile(path, wx.BITMAP_TYPE_JPEG)
            elif path[-4:] == '.png':
                bmp.SaveFile(path, wx.BITMAP_TYPE_PNG)

            del bmp
        dlg.Destroy()
        
    def on_edit_status(self, event):
        if self.g.in_editing:
            self.g.in_editing = False
            self._menu_edit_status.SetItemLabel('进入编辑状态')
            self._menu_map_download.Enable(True)
            self._menu_set_start_pt.Enable(False)
            self._menu_set_end_pt.Enable(False)
            self._menu_delete_segment.Enable(False)
            self._menu_delete_point.Enable(False)
            self._menu_split.Enable(False)
            self._menu_merge.Enable(False)
            self._menu_open.Enable(True)
            self._menu_search_wpt.Enable(True)
            self._menu_search_route.Enable(True)
            self._menu_default_pin.Enable(True)
            self._menu_hide_wpts.Enable(True)
            self._menu_del_all_wpts.Enable(True)
            self._menu_photo_add.Enable(True)
            self._menu_photo_clear.Enable(True)
            self._tb_edit_enter.Enable(True)
            self._tb_edit_quit.Enable(False)
            self._tb_set_start_pt.Enable(False)
            self._tb_set_end_pt.Enable(False)
            self._tb_delete_segment.Enable(False)
            self._tb_delete_point.Enable(False)
            self._tb_split.Enable(False)
            self._tb_merge.Enable(False)
            self._tb_open.Enable(True)
            self.g.track_tree.Enable(True)
            self.g.track_edit.Enable(False)
            self.g.track_tree.selected_track_line = None
        else:
            self.g.in_editing = True
            self._menu_edit_status.SetItemLabel('退出编辑状态')
            self._menu_map_download.Enable(False)
            self._menu_set_start_pt.Enable(True)
            self._menu_set_end_pt.Enable(True)
            self._menu_delete_segment.Enable(True)
            self._menu_delete_point.Enable(True)
            self._menu_split.Enable(True)
            self._menu_merge.Enable(True)
            self._menu_open.Enable(False)
            self._menu_search_wpt.Enable(False)
            self._menu_search_route.Enable(False)
            self._menu_default_pin.Enable(False)
            self._menu_hide_wpts.Enable(False)
            self._menu_del_all_wpts.Enable(False)
            self._menu_photo_add.Enable(False)
            self._menu_photo_clear.Enable(False)
            self._tb_edit_enter.Enable(False)
            self._tb_edit_quit.Enable(True)
            self._tb_set_start_pt.Enable(True)
            self._tb_set_end_pt.Enable(True)
            self._tb_delete_segment.Enable(True)
            self._tb_delete_point.Enable(True)
            self._tb_split.Enable(True)
            self._tb_merge.Enable(True)
            self._tb_open.Enable(False)
            self.g.track_tree.Enable(False)
            self.g.track_edit.Enable(True)
            self.g.track_edit.selected_track_line = None

        self.g.undo_list = []
        self.enable_undo(False)
        self.show_status_info(show_edit_status=True)
        self.repaint(canvas=const.REDRAW_TRACK)

    def on_set_start_pt(self, event):
        track_line = self.g.track_edit.selected_track_line
        if track_line and track_line.selected_point:
            track_point = track_line.selected_point
            track_line.sel_start_idx = track_line.track_points.index(track_point)
            if track_line.sel_start_idx > track_line.sel_end_idx:
                track_line.sel_end_idx = track_line.point_num - 1
            self.g.map_canvas.redraw_edit_selected_track_line()
            self.repaint(canvas=const.REDRAW_NONE)
        else:
            do_log('请先选择轨迹点...')

    def on_set_end_pt(self, event):
        track_line = self.g.track_edit.selected_track_line
        if track_line and track_line.selected_point:
            track_point = track_line.selected_point
            track_line.sel_end_idx = track_line.track_points.index(track_point)
            if track_line.sel_end_idx < track_line.sel_start_idx:
                track_line.sel_start_idx = 0
            self.g.map_canvas.redraw_edit_selected_track_line()
            self.repaint(canvas=const.REDRAW_NONE)
        else:
            do_log('请先选择轨迹点...')

    def on_delete_segment(self, event):
        track_line = self.g.track_edit.selected_track_line
        if track_line is None:
            do_log('请选择轨迹段...')
            return
        
        if track_line.sel_start_idx == 0 and track_line.sel_end_idx == track_line.point_num - 1:
            # 删除整个轨迹
            dlg = wx.MessageDialog(self, '已选择整段轨迹，确认删除该轨迹？',
                                   '确认删除？',
                                   wx.YES_NO
                                   )
            ret = dlg.ShowModal()
            dlg.Destroy()
            if ret != wx.ID_YES:
                return

            undo_action = {}
            undo_action['action'] = 'edit_del_track'
            undo_action['track'] = track_line
            self.g.undo_list = [undo_action]
            self.g.track_edit.set_selected_track_line(None)
            sel_index = self.g.edit_track_list.index(track_line)
            self.g.track_edit.DeleteItem(sel_index)
            self.g.edit_track_list.pop(sel_index)
            self.enable_undo()
            do_log('轨迹“%s”被删除...' % track_line.name)
        else:
            undo_action = {}
            undo_action['action'] = 'del_seg'
            undo_action['track'] = track_line
            undo_action['start'] = track_line.sel_start_idx
            undo_action['end'] = track_line.sel_end_idx
            undo_action['del_seg'] = track_line.track_points[track_line.sel_start_idx : track_line.sel_end_idx + 1]
            self.g.undo_list = [undo_action]
            track_line.track_points[track_line.sel_start_idx : track_line.sel_end_idx + 1] = []
            track_line.selected_point = None
            track_line.compute_track_line_args()
            self.g.track_edit.set_selected_track_line(None)
            self.enable_undo()
            do_log('选中轨迹段(%d点)被删除...' % len(undo_action['del_seg']))

        self.repaint(canvas=const.REDRAW_TRACK)

    def on_delete_point(self, event):
        track_line = self.g.track_edit.selected_track_line
        if track_line is None or track_line.selected_point is None:
            do_log('请先选择轨迹点...')
            return
        if track_line.point_num < 10:
            do_log('轨迹点过少，操作无效...')
            return
        
        track_point = track_line.selected_point
        index = track_line.track_points.index(track_point)

        undo_action = {}
        undo_action['action'] = 'del_point'
        undo_action['track'] = track_line
        undo_action['index'] = index
        undo_action['point'] = track_point
        self.g.undo_list = [undo_action]
        
        track_line.track_points.pop(index)
        track_line.compute_track_line_args()
        if index > track_line.point_num - 1:
            index -= 1
        track_line.selected_point = track_line.track_points[index]
        self.g.track_edit.set_selected_track_line(track_line)

        self.enable_undo()
        do_log('选中轨迹点(%d)被删除...' % undo_action['index'])

        self.repaint(canvas=const.REDRAW_TRACK)

    def on_split(self, event):
        track_line = self.g.track_edit.selected_track_line
        if track_line is None or track_line.selected_point is None:
            do_log('请先选择轨迹点...')
            return
        track_point = track_line.selected_point

        item = self.g.edit_track_list.index(track_line)
        index = track_line.track_points.index(track_point)
        if index < 10 or index > track_line.point_num - 10:
            do_log('分割点距起始点太近，操作无效...')
            return

        track1 = track_line
        track_org = copy.deepcopy(track1)
        track2 = copy.deepcopy(track1)
        track1.track_points[index + 1:] = []
        track1.compute_track_line_args()
        self.g.track_edit.set_selected_track_line(track1)
        track1.name = '分割1_' + track1.name

        track2.track_points[0:index + 1] = []
        for track_point in track2.track_points:
            track_point.track_line = track2
        track2.compute_track_line_args()
        track2.selected_point = None
        track2.name = '分割2_' + track2.name

        self.g.track_edit.SetItemText(item, track1.name)
        self.g.track_edit.InsertStringItem(item + 1, track2.name)
        self.g.edit_track_list.insert(item + 1, track2)

        undo_action = {}
        undo_action['action'] = 'split'
        undo_action['track_org'] = track_org
        undo_action['track1'] = track1
        undo_action['track2'] = track2
        self.g.undo_list = [undo_action]

        self.enable_undo()
        do_log('轨迹“%s”被分割为两段...' % track_org.name)
        self.repaint(canvas=const.REDRAW_TRACK)

    def on_merge(self, event):
        track1 = None
        item1 = 0
        i = 0
        org_track_list = []
        for track_line in self.g.edit_track_list:
            if track_line.is_checked:
                track1 = track_line
                org_track_list.append(copy.deepcopy(track1))
                item1 = i
                break
            i += 1

        if track1 is None:
            do_log('请先在多选框选择两条以上轨迹...')
            return

        item2_list = []
        for j in range(i + 1, len(self.g.edit_track_list)):
            if self.g.edit_track_list[j].is_checked:
                item2_list.append(j)

        if not item2_list:
            do_log('请先在多选框选择两条以上轨迹...')
            return

        for item2 in item2_list:
            track2 = self.g.edit_track_list[item2]
            track1.track_points[len(track1.track_points):] = track2.track_points
            if not track2.has_timestamp:
                track1.has_timestamp = False
        for track_point in track1.track_points:
            track_point.track_line = track1
        track1.compute_track_line_args()
        track1.selected_point = None
        track1.name = '合并%05d' % auto_id.get_id()

        for item2 in item2_list[-1::-1]:
            self.g.track_edit.DeleteItem(item2)
            org_track_list.append(self.g.edit_track_list.pop(item2))
        self.g.track_edit.DeleteItem(item1)
        self.g.edit_track_list.pop(item1)

        self.g.track_edit.InsertStringItem(len(self.g.edit_track_list), track1.name)
        self.g.edit_track_list.append(track1)
        track1.is_checked = False
        self.g.track_edit.set_selected_track_line(track1)

        undo_action = {}
        undo_action['action'] = 'merge'
        undo_action['org_track_list'] = org_track_list
        undo_action['new_track'] = track1
        self.g.undo_list = [undo_action]

        self.enable_undo()
        do_log('已将%d个轨迹合并为一个...' % len(org_track_list))
        self.repaint(canvas=const.REDRAW_TRACK)

    def on_undo(self, event):
        if not self.g.undo_list:
            self.enable_undo(False)
            return

        undo_action = self.g.undo_list.pop()
        if undo_action['action'] == 'tree_del_track':
            track_line = undo_action['track']
            parent = self.g.get_parent_folder(track_line)
            self.g.add_data(parent, track_line)
            self.enable_undo(False)
            self.repaint(const.REDRAW_TRACK)
            do_log('刚才删除的轨迹“%s”被恢复至文件夹“%s”' % (track_line.name, parent.name))
        elif undo_action['action'] == 'tree_del_folder':
            deleted = undo_action['deleted']
            for data in deleted:
                parent = self.g.get_parent_folder(data)
                self.g.add_data(parent, data, commit=False)
            self.g.db_mgr.commit()
            self.enable_undo(False)
            self.repaint(const.REDRAW_TRACK)
            do_log('刚才删除的文件夹“%s”被恢复')
        elif undo_action['action'] == 'edit_del_track':
            track_line = undo_action['track']
            self.g.track_edit.InsertStringItem(len(self.g.edit_track_list), track_line.name)
            self.g.edit_track_list.append(track_line)
            self.enable_undo(False)
            self.repaint(const.REDRAW_TRACK)
            do_log('刚才删除的轨迹“%s”已恢复' % track_line.name)
        elif undo_action['action'] == 'del_seg':
            track_line = undo_action['track']
            start_idx = undo_action['start']
            track_line.track_points[start_idx:start_idx] = undo_action['del_seg']
            self.g.track_edit.selected_track_line = track_line
            track_line.sel_start_idx = start_idx
            track_line.sel_end_idx = undo_action['end']
            track_line.compute_track_line_args()
            self.enable_undo(False)
            self.repaint(const.REDRAW_TRACK)
            do_log('刚才删除的轨迹段(%d点)已恢复' % len(undo_action['del_seg']))
        elif undo_action['action'] == 'del_point':
            track_line = undo_action['track']
            point = undo_action['point']
            index = undo_action['index']
            track_line.track_points[index:index] = [point]
            self.g.track_edit.selected_track_line = track_line
            track_line.sel_start_idx = index
            track_line.sel_end_idx = index
            track_line.selected_point = point
            track_line.compute_track_line_args()
            self.enable_undo(False)
            self.repaint(const.REDRAW_TRACK)
            do_log('刚才删除的轨迹点已恢复...')
        elif undo_action['action'] == 'split':
            track_org = undo_action['track_org']
            track1 = undo_action['track1']
            track2 = undo_action['track2']
            track_list = self.g.edit_track_list
            self.g.track_edit.DeleteItem(track_list.index(track2))
            self.g.track_edit.DeleteItem(track_list.index(track1))
            track_list.pop(track_list.index(track2))
            track_list.pop(track_list.index(track1))
            self.g.track_edit.InsertStringItem(len(track_list), track_org.name)
            track_list.append(track_org)
            self.g.track_edit.set_selected_track_line(track_org)
            self.enable_undo(False)
            self.repaint(const.REDRAW_TRACK)
            do_log('刚才被分割的轨迹已重新合并...')
        elif undo_action['action'] == 'merge':
            org_track_list = undo_action['org_track_list']
            new_track = undo_action['new_track']
            track_list = self.g.edit_track_list
            self.g.track_edit.DeleteItem(track_list.index(new_track))
            track_list.pop(track_list.index(new_track))
            
            for track_line in org_track_list:
                self.g.track_edit.InsertStringItem(len(track_list), track_line.name)
                track_list.append(track_line)
                track_line.is_checked = False
                for point in track_line.track_points:
                    point.track_line = track_line
            
            self.g.track_edit.set_selected_track_line(None)
            self.enable_undo(False)
            self.repaint(const.REDRAW_TRACK)
            do_log('刚才被合并的轨迹已重新分割为多个...')
        elif undo_action['action'] == 'reverse':
            track_line = undo_action['track']
            track_line.track_points.reverse()
            track_line.has_timestamp = undo_action['has_timestamp']
            track_line.compute_track_line_args()
            self.g.track_edit.set_selected_track_line(track_line)
            self.enable_undo(False)
            self.repaint(canvas=const.REDRAW_TRACK)
            do_log('刚才翻转的轨迹已恢复至原来方向...')
        elif undo_action['action'] == 'del_all_wpts':
            redo_dir = '被删路点恢复%05d' % auto_id.get_id()
            wpt_folder = self.g.track_tree.create_child_folder(self.g.data_root, redo_dir)
            for wpt in self.g.wpt_list_deleted:
                wpt.parent = wpt_folder.uuid
                self.g.add_data(wpt_folder, wpt, commit=False)
            self.g.db_mgr.commit()
            self.g.wpt_list_deleted = []
            self.repaint(canvas=const.REDRAW_COPY)
            do_log('刚才被删除的路点统一被恢复至<%s>文件夹...' % redo_dir)

    def on_search_wpt(self, event):
        dlg = WptSearchDlg()
        dlg.CentreOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.name.GetValue()
            if name:
                way_points = search.find_pos_from_name(name, self.g.search_api)
                if len(way_points) > 0:
                    folder_name = '地点搜索结果：%s' % name
                    new_folder = self.g.track_tree.create_child_folder(self.g.data_root, folder_name)
                    first_wpt = None
                    for point in way_points:
                        wpt = WayPoint(point[0], point[1], point[2], parent=new_folder.uuid,
                                       bmp_index=self.g.default_wpt_bmp_index)
                        self.g.add_data(new_folder, wpt)
                        if not first_wpt:
                            first_wpt = wpt
                    self.g.track_tree.SelectItem(first_wpt.tree_node)
                    self.g.map_canvas.zoom_to_lon_lat(15, first_wpt.lon, first_wpt.lat)
                    self.repaint(canvas=const.REDRAW_MAP)
                else:
                    do_log('地名搜索失败...')
            else:
                do_log('地名不能为空...')
        dlg.Destroy()

    def on_search_route(self, event):
        dlg = RouteSearchDlg(self.g)
        dlg.CentreOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            wpt_start = None
            wpt_end = None
            start_idx = dlg.start.GetCurrentSelection()
            if start_idx < 0:
                start_name = dlg.start.GetValue()
                if start_name:
                    way_points = search.find_pos_from_name(start_name, self.g.search_api)
                    if way_points:
                        wpt_start = WayPoint(way_points[0][0], way_points[0][1], way_points[0][2], 
                                             bmp_index=self.g.default_wpt_bmp_index)
                    else:
                        wpt_start = None
            else:
                wpt_start = self.g.wpt_list[start_idx]
                
            end_idx = dlg.end.GetCurrentSelection()
            if end_idx < 0:
                end_name = dlg.end.GetValue()
                if end_name:
                    way_points = search.find_pos_from_name(end_name, self.g.search_api)
                    if way_points:
                        wpt_end = WayPoint(way_points[0][0], way_points[0][1], way_points[0][2], 
                                           bmp_index=self.g.default_wpt_bmp_index)
                    else:
                        wpt_end = None
            else:
                wpt_end = self.g.wpt_list[end_idx]
            
            if wpt_start and wpt_end:
                routes = search.find_drive_route((wpt_start.lon, wpt_start.lat), (wpt_end.lon, wpt_end.lat), self.g.search_api)
                if len(routes) > 0:
                    folder_name = '路径搜索结果：%s --> %s' % (wpt_start.name, wpt_end.name)
                    new_folder = self.g.track_tree.create_child_folder(self.g.data_root, folder_name)
                    first_track = None
                    for route in routes:
                        track_line = TrackLine(new_folder.uuid, name='行车路径%05d' % auto_id.get_id())
                        track_line.load_from_points(route)
                        self.g.add_data(new_folder, track_line, commit=False)
                        if not first_track:
                            first_track = track_line
                        
                    if not wpt_start.parent:
                        wpt_start.parent = new_folder.uuid
                        self.g.add_data(new_folder, wpt_start, commit=False)
                        
                    if not wpt_end.parent:
                        wpt_end.parent = new_folder.uuid
                        self.g.add_data(new_folder, wpt_end, commit=False)

                    self.g.db_mgr.commit()
                        
                    self.g.track_tree.selected_track_line = first_track
                    self.g.track_tree.SelectItem(first_track.tree_node)
                    self.g.map_canvas.zoom_to_track_line(first_track)
                    do_log('找到%d条行车路线' % len(routes))
                else:
                    do_log('未找到合适的行车路线...')
            else:
                do_log('地名为空或无效...')
        dlg.Destroy()

    def on_search_api(self, event):
        dlg = SearchApiDlg(self.g)
        dlg.CentreOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            self.g.search_api = dlg.search_api.GetSelection()
        dlg.Destroy()
        
    def on_hide_wpts(self, event):
        for wpt in self.g.wpt_list:
            wpt.is_visible = False
            self.g.db_mgr.update_visible(wpt, commit=False)
            self.g.track_tree.SetItemBold(wpt.tree_node, False)
        self.g.db_mgr.commit()
        self.repaint(const.REDRAW_COPY)

    def on_default_pin(self, event):
        dlg = DefaultPinDlg(self.g)
        dlg.CentreOnParent()
        dlg.ShowModal()
        dlg.Destroy()
        
    def on_del_all_wpts(self, event):
        dlg = wx.MessageDialog(self, '真的要删除所有路点数据？',
                               '提示',
                               wx.YES_NO
                               )
        ret = dlg.ShowModal()
        dlg.Destroy()
        if ret != wx.ID_YES:
            return
        
        self.g.empty_wpt_list()
        self.g.map_canvas.repaint(const.REDRAW_COPY)
        
        undo_action = {}
        undo_action['action'] = 'del_all_wpts'
        self.g.undo_list = [undo_action]
        self.enable_undo()
        do_log('已删除所有路点数据...')
        
    def on_srtm_src(self, event):
        dlg = SrtmSrcDlg(self.g)
        dlg.CentreOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            self.g.srtm_url_index = dlg.srtm_src.GetSelection()
        dlg.Destroy()

    def on_photo_add(self, event):
        dlg = wx.FileDialog(
            self, message='请选择照片文件',
            defaultDir=os.getcwd(),
            defaultFile='',
            wildcard='照片文件 (*.jpg)|*.jpg',
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR
        )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            photo = Photo(paths[0])
            if photo.bmp:
                self.g.photo_list.append(photo)
                self.g.db_mgr.add_photo(photo)
                self.g.map_canvas.zoom_to_lon_lat(15, photo.lon, photo.lat)
            else:
                do_log('照片文件无GPS信息，无法放置到地图...')
        dlg.Destroy()

    def on_photo_clear(self, event):
        dlg = wx.MessageDialog(self, '真的要删除所有照片？',
                               '提示',
                               wx.YES_NO
                               )
        ret = dlg.ShowModal()
        dlg.Destroy()
        if ret != wx.ID_YES:
            return

        for photo in self.g.photo_list:
            self.g.db_mgr.del_photo(photo, commit=False)
        self.g.db_mgr.commit()
        self.g.photo_list = []
        self.g.map_canvas.repaint(const.REDRAW_COPY)

    def show_track_details(self, track_line=None):
        self.g.track_details.Clear()
        if track_line is None:
            return  # 当前无选中轨迹则仅做清空工作并返回

        name = '%s\n' % track_line.name
        time_begin = '起始时间：%s\n' % track_line.time_begin_str if track_line.has_timestamp else ''
        time_end = '结束时间：%s\n' % track_line.time_end_str if track_line.has_timestamp else ''
        time_duration = '时长：%s\n' % track_line.duration_str if track_line.has_timestamp else ''
        distance = '距离：%.1f公里\n' % track_line.distance
        distance_horizon = '水平距离：%.1f公里\n' % track_line.distance_horizon
        climb = '累计上升：%d米\n' % track_line.climb
        descent = '累计下降：%d米\n' % track_line.descent
        alt_range = '海拔范围：%d-%d米\n' % (track_line.alt_min, track_line.alt_max)
        point_num = '轨迹点数：%d\n' % track_line.point_num
        
        track_line_details = name + time_begin + time_end + time_duration + distance + distance_horizon \
                             + climb + descent + alt_range + point_num + '\n'

        if track_line is self.g.track_edit.selected_track_line:
            from_to = '%d-%d\n' % (track_line.sel_start_idx, track_line.sel_end_idx)
            time_begin = '起始时间：%s\n' % track_line.sel_time_begin_str if track_line.has_timestamp else ''
            time_end = '结束时间：%s\n' % track_line.sel_time_end_str if track_line.has_timestamp else ''
            time_duration = '时长：%s\n' % track_line.sel_duration_str if track_line.has_timestamp else ''
            distance = '距离：%.1f公里\n' % track_line.sel_distance
            distance_horizon = '水平距离：%.1f公里\n' % track_line.sel_distance_horizon
            climb = '累计上升：%d米\n' % track_line.sel_climb
            descent = '累计下降：%d米\n' % track_line.sel_descent
            alt_range = '海拔范围：%d-%d米\n' % (track_line.sel_alt_min, track_line.sel_alt_max)
            point_num = '轨迹点数：%d\n' % track_line.sel_point_num
            sel_segment_details = '当前轨迹段：  ' + from_to + time_begin + time_end + time_duration + distance \
                                 + distance_horizon + climb + descent + alt_range + point_num + '\n'
        else:
            sel_segment_details = ''
            
        if track_line is self.g.track_edit.selected_track_line and track_line.selected_point:
            point = '%d\n' % track_line.track_points.index(track_line.selected_point)
            timestamp = '时间：%s\n' % track_line.sel_point_time_str if track_line.has_timestamp else ''
            lon = '东经：%.08f\n' % track_line.selected_point.lon
            lat = '北纬：%.08f\n' % track_line.selected_point.lat
            alt = '海拔：%.01f米\n' % track_line.selected_point.alt
            sel_point_details = '当前轨迹点：  ' + point + timestamp + lon + lat + alt + '\n'
        else:
            sel_point_details = ''

        self.g.track_details.WriteText(track_line_details + sel_segment_details + sel_point_details)
        
    def repaint(self, canvas=const.REDRAW_MAP):
        if canvas != const.REDRAW_NONE:
            self.g.map_canvas.repaint(mode=canvas)

        track_line = self.g.track_edit.selected_track_line if self.g.in_editing else self.g.track_tree.selected_track_line
        
        if track_line:
            track_line.compute_time_args_after_restore()
            if self.g.in_editing:
                track_line.compute_selected_segment_args()
        self.show_track_details(track_line)
        self.g.track_chart.draw_alt_chart(track_line)

    def on_about(self, event):
        about_info = wx.adv.AboutDialogInfo()
        about_info.SetIcon(wx.Icon(app_icons.zhangjiashan.GetIcon()))
        about_info.SetName(const.APP_NAME)
        about_info.SetVersion(const.APP_VERSION)
        about_info.SetCopyright('Copyright (C) 2017-2018 霍龙社')
        about_info.SetWebSite('https://github.com/huolongshe/spider')
        wx.adv.AboutBox(about_info)
        
