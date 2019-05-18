#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import datetime
import math
import wx

from app.globals import const
from app.resource import app_icons
from app.dialog.map_download_dlg import MapDownloadDialog
from app.dialog.pin_sel_dlg import PinSelDlg
from app.dialog.srtm_wpt_dlg import SrtmWptDlg
from app.dialog.track_select_dlg import TrackSelectDlg
from app.dialog.spot_tip_popup import SpotTipPopup
from app.dialog.photo_view_dlg import PhotoViewDlg
from app.model.track_line import TrackLine
from app.model.track_point import TrackPoint
from app.model.way_point import WayPoint
from app.service import auto_id
from app.service import search
from app.service import jiupian
from app.service import transform
from app.service.logger import do_log


'''
# 统一本程序中位置坐标命名：
# (lon, lat)             : WGS-84坐标系中的经纬度坐标
# 在本应用中，将最大缩放级别下的Web墨卡托投影像素地图称为全图，
#            将某一位置在全图中对应的像素坐标标记为(fpx, fpy)。
#            在已知某一坐标点的全图像素坐标以及缩放级别后，就可以唯一确定该坐标点的当前显示位置，找到其对应的瓦片地图
# (fpx, fpy, zoom)       : 全图像素坐标及缩放级别（坐标原点在左上角），唯一确定一个显示位置
# (px, py, zoom)         : 缩放图图像素坐标及缩放级别（坐标原点在左上角）
# (spx, spy)             : 地图位置在当前屏幕窗口中对应的像素坐标（坐标原点在左上角）
# (tile_x, tile_y, zoom) : 在缩放级别zoom下，Google瓦片坐标系中的瓦片坐标（坐标原点在左上角）
# (tile_spx, tile_spy)   : 地图瓦片左上角在当前屏幕窗口中的像素坐标（坐标原点在左上角）
# (width, height)        : 当前屏幕窗口的宽高度
'''


class MapCanvas(wx.Window):
    def __init__(self, parent, g):
        wx.Window.__init__(self, parent)
        self.g = g

        self._self_drawing = False  # 自绘轨迹状态
        self._drawing_track = None  # 自绘轨迹时创建的轨迹对象
        self._to_drag_point = False  # 进入拖拽轨迹点状态，还未开始点击拖拽
        self._dragging_point = False  # 进入拖拽轨迹点状态，并点击左键开始拖拽
        self._dragged_point = None  # 拖拽轨迹点状态下被拖拽的轨迹点对象

        self.Bind(wx.EVT_PAINT, self.on_paint, self)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mousewheel, self)
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_enter, self, self)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down, self)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up, self)
        self.Bind(wx.EVT_MOTION, self.on_motion, self)
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick, self)
        self.Bind(wx.EVT_RIGHT_UP, self.on_right_up, self)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down, self)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda event: 1, self)  # 为了正确显示透明按钮，必须定义此绑定，lambda表达式不做任何事情（不知为何不能用pass）

    def init_after_frame_shown(self):  # called later when the parent view be set shown
        self._width = self.GetSize().width
        self._height = self.GetSize().height
        self._half_width = self._width // 2
        self._half_height = self._height // 2

        self._dc = wx.ClientDC(self)
        screen_width = wx.SystemSettings().GetMetric(wx.SYS_SCREEN_X)
        screen_height = wx.SystemSettings().GetMetric(wx.SYS_SCREEN_Y)
        self._mdc1 = wx.MemoryDC(wx.Bitmap(screen_width, screen_height))  # MemoryDC
        self._mdc2 = wx.MemoryDC(wx.Bitmap(screen_width, screen_height))  # MemoryDC

        # 恢复上次退出时的屏幕画面，否则显示中国地图
        if self.g.init_cfg and 'pos' in self.g.init_cfg \
                and 'fpx' in self.g.init_cfg['pos'] and 'fpy' in self.g.init_cfg['pos']:
            self.set_centre_position(self.g.init_cfg['pos']['zoom'],
                                 self.g.init_cfg['pos']['fpx'],
                                 self.g.init_cfg['pos']['fpy'])
        else:
            self.zoom_to_fit_China()

    def get_max_zoom(self):
        max_zoom = const.MAX_ZOOM
        for map_list in [self.g.map_list_main, self.g.map_list_trans]:
            for map_source in map_list:
                if map_source.is_visible and map_source.zoom_max < max_zoom:
                    max_zoom = map_source.zoom_max
        return max_zoom

    def get_min_zoom(self):
        min_zoom = 1
        for map_list in [self.g.map_list_main, self.g.map_list_trans]:
            for map_source in map_list:
                if map_source.is_visible and map_source.zoom_min > min_zoom:
                    min_zoom = map_source.zoom_min
        return min_zoom

    def zoom_to_fit_China(self):
        lon_min, lon_max = (73.5, 135.05)  # 中国陆地经度范围
        lat_min, lat_max = (3.5, 53.55)  # 中国陆地纬度范围
        fpx_min = transform.get_fpx_from_longitude(lon_min)
        fpx_max = transform.get_fpx_from_longitude(lon_max)
        fpy_min = transform.get_fpy_from_latitude(lat_min)
        fpy_max = transform.get_fpy_from_latitude(lat_max)
        self.zoom_to_range(fpx_min, fpx_max, fpy_min, fpy_max)

    def set_centre_position(self, zoom, fpx, fpy, fpx_gcj02=None, fpy_gcj02=None):
        # (self._zoom, self._centre_fpx, self._centre_fpy)：当前缩放级别，以及当前屏幕中心点在像素地图全图中的像素坐标
        # 当需要在屏幕窗口中重新刷新显示地图时，只需要确定当前的缩放级别和屏幕中心点的全图像素坐标，就可以唯一确定所有需要显示的地图瓦片
        self._zoom = zoom
        self._centre_fpx = fpx
        self._centre_fpy = fpy
        self._centre_px = transform.get_px_from_fpx(self._centre_fpx, self._zoom) # 屏幕中心点在当前缩放级别像素地图中的像素坐标
        self._centre_py = transform.get_py_from_fpy(self._centre_fpy, self._zoom)  # 屏幕中心点在当前缩放级别像素地图中的像素坐标
    
        centre_changed = self.check_map_bound()

        if fpx_gcj02 and fpy_gcj02 and not centre_changed:
            self._centre_fpx_gcj02 = fpx_gcj02
            self._centre_fpy_gcj02 = fpy_gcj02
            self._centre_px_gcj02 = transform.get_px_from_fpx(self._centre_fpx_gcj02, self._zoom)  # 屏幕中心点在当前缩放级别像素地图中的像素坐标
            self._centre_py_gcj02 = transform.get_py_from_fpy(self._centre_fpy_gcj02, self._zoom)  # 屏幕中心点在当前缩放级别像素地图中的像素坐标
        else:
            centre_lon_wgs84 = transform.get_longitude_from_fpx(self._centre_fpx)
            centre_lat_wgs84 = transform.get_latitude_from_fpy(self._centre_fpy)
            centre_lon_gcj02, centre_lat_gcj02 = jiupian.wgs84_to_gcj02(centre_lon_wgs84, centre_lat_wgs84)
            self._centre_fpx_gcj02 = transform.get_fpx_from_longitude(centre_lon_gcj02)
            self._centre_fpy_gcj02 = transform.get_fpy_from_latitude(centre_lat_gcj02)
            self._centre_px_gcj02 = transform.get_px_from_fpx(self._centre_fpx_gcj02, self._zoom)
            self._centre_py_gcj02 = transform.get_py_from_fpy(self._centre_fpy_gcj02, self._zoom)
        
        self._corner1_px = self._centre_px - self._half_width
        self._corner1_py = self._centre_py - self._half_height
        self._corner2_px = self._centre_px + self._half_width
        self._corner2_py = self._centre_py + self._half_height
        self._corner1_px_gcj02 = self._centre_px_gcj02 - self._half_width
        self._corner1_py_gcj02 = self._centre_py_gcj02 - self._half_height
        self._corner2_px_gcj02 = self._centre_px_gcj02 + self._half_width
        self._corner2_py_gcj02 = self._centre_py_gcj02 + self._half_height

        self._corner1_tile_x = self._corner1_px // const.MAP_TILE_SIZE  # 由位置像素坐标获取tile坐标
        self._corner1_tile_y = self._corner1_py // const.MAP_TILE_SIZE
        self._corner2_tile_x = self._corner2_px // const.MAP_TILE_SIZE
        self._corner2_tile_y = self._corner2_py // const.MAP_TILE_SIZE
        self._corner1_tile_x_gcj02 = self._corner1_px_gcj02 // const.MAP_TILE_SIZE  # 由位置像素坐标获取tile坐标
        self._corner1_tile_y_gcj02 = self._corner1_py_gcj02 // const.MAP_TILE_SIZE
        self._corner2_tile_x_gcj02 = self._corner2_px_gcj02 // const.MAP_TILE_SIZE
        self._corner2_tile_y_gcj02 = self._corner2_py_gcj02 // const.MAP_TILE_SIZE

        self._corner1_px_offset_in_tile = self._corner1_px % const.MAP_TILE_SIZE  # 由位置像素坐标获取其在所处tile中与左上角像素的偏移值
        self._corner1_py_offset_in_tile = self._corner1_py % const.MAP_TILE_SIZE
        self._corner1_px_gcj02_offset_in_tile = self._corner1_px_gcj02 % const.MAP_TILE_SIZE  # 由位置像素坐标获取其在所处tile中与左上角像素的偏移值
        self._corner1_py_gcj02_offset_in_tile = self._corner1_py_gcj02 % const.MAP_TILE_SIZE
    
        self.repaint(const.REDRAW_MAP)

    def check_map_bound(self):
        centre_changed = False

        # 在中国地图右侧重复显示一半世界地图（美洲），以使中国地图可始终居中
        map_display_width = (const.MAP_TILE_SIZE << self._zoom) * 3 // 2
        if map_display_width <= self._width:
            # 当地图尺寸缩小至小于屏幕窗口尺寸时，将地图中心点作为屏幕中心点，固定显示于窗口正中央
            self._centre_px = map_display_width // 2
            centre_changed = True
        elif self._centre_px < self._half_width:
            # 地图宽度大于屏幕窗口宽度，当向右拖拽地图使地图左边界离开屏幕左边界时，使两个边界重叠锚定，不再向右偏离
            # 即：self._centre_px最小值应为self._half_width
            self._centre_px = self._half_width
            centre_changed = True
        elif (self._centre_px + self._half_width) > map_display_width:
            # 地图宽度大于屏幕窗口宽度，当向左拖拽地图使地图右边界离开屏幕右边界时，使两个边界重叠锚定，不再向左偏离
            # 即：self._centre_px最大值应为map_display_width - self._half_width
            self._centre_px = map_display_width - self._half_width
            centre_changed = True

        map_display_height = const.MAP_TILE_SIZE << self._zoom
        if map_display_height <= self._height:
            self._centre_py = map_display_height // 2
            centre_changed = True
        elif self._centre_py < self._half_height:
            self._centre_py = self._half_height
            centre_changed = True
        elif (self._centre_py + self._half_height) > map_display_height:
            self._centre_py = map_display_height - self._half_height
            centre_changed = True

        if centre_changed:
            self._centre_fpx = transform.get_fpx_from_px(self._centre_px, self._zoom)
            self._centre_fpy = transform.get_fpy_from_py(self._centre_py, self._zoom)

        return centre_changed

    def zoom_to_lon_lat(self, zoom, lon, lat):
        self.set_centre_position(zoom, transform.get_fpx_from_longitude(lon), transform.get_fpy_from_latitude(lat))

    # 缩放地图使能够最大程度地显示相应范围所确定的轨迹
    def zoom_to_range(self, min_fpx, max_fpx, min_fpy, max_fpy):
        diff_fpx = abs(max_fpx - min_fpx)
        diff_fpy = abs(max_fpy - min_fpy)
    
        zoom = const.MAX_ZOOM
        while zoom >= 1:
            if transform.get_px_from_fpx(diff_fpx, zoom) < self._width \
                    and transform.get_py_from_fpy(diff_fpy, zoom) < self._height:
                break
            zoom -= 1
        if zoom < 1:
            zoom = 1
    
        self.set_centre_position(zoom, (min_fpx + max_fpx) // 2, (min_fpy + max_fpy) // 2)

    def get_fpx_from_spx(self, spx):
        return transform.get_fpx_from_px((spx - self._half_width) + self._centre_px, self._zoom)

    def get_fpy_from_spy(self, spy):
        return transform.get_fpy_from_py((spy - self._half_height) + self._centre_py, self._zoom)

    def get_lon_from_spx(self, spx):
        return transform.get_longitude_from_fpx(self.get_fpx_from_spx(spx))

    def get_lat_from_spy(self, spy):
        return transform.get_latitude_from_fpy(self.get_fpy_from_spy(spy))

    def get_spx_from_fpx(self, fpx):
        return transform.get_px_from_fpx(fpx, self._zoom) - self._corner1_px

    def get_spy_from_fpy(self, fpy):
        return transform.get_py_from_fpy(fpy, self._zoom) - self._corner1_py

    def get_spx_from_px(self, px):
        return px - self._centre_px + self._half_width

    def get_spy_from_py(self, py):
        return py - self._centre_py + self._half_height

    def zoom_in(self):
        if self._zoom < self.get_max_zoom():
            self.set_centre_position(self._zoom + 1,
                                     self._centre_fpx,
                                     self._centre_fpy,
                                     fpx_gcj02=self._centre_fpx_gcj02,
                                     fpy_gcj02=self._centre_fpy_gcj02)

    def zoom_out(self):
        if self._zoom > self.get_min_zoom():
            self.set_centre_position(self._zoom - 1,
                                     self._centre_fpx,
                                     self._centre_fpy,
                                     fpx_gcj02=self._centre_fpx_gcj02,
                                     fpy_gcj02=self._centre_fpy_gcj02)

    def pan(self, delta_px, delta_py):
        delta_fpx = transform.get_fpx_from_px(delta_px, self._zoom)
        delta_fpy = transform.get_fpy_from_py(delta_py, self._zoom)
        px = self._centre_px + delta_px
        py = self._centre_py + delta_py
        self.set_centre_position(self._zoom,
                                 self._centre_fpx + delta_fpx,
                                 self._centre_fpy + delta_fpy,
                                 fpx_gcj02=(self._centre_fpx_gcj02 + delta_fpx),
                                 fpy_gcj02=(self._centre_fpy_gcj02 + delta_fpy))

    def on_paint(self, event):
        if self.GetSize().width != self._width or self.GetSize().height != self._height:
            self._width = self.GetSize().width
            self._height = self.GetSize().height
            self._half_width = self._width // 2
            self._half_height = self._height // 2
            self.set_centre_position(self._zoom, self._centre_fpx, self._centre_fpy,
                                     fpx_gcj02=self._centre_fpx_gcj02,
                                     fpy_gcj02=self._centre_fpy_gcj02)
        else:
            self.repaint(mode=const.REDRAW_COPY)
        
    def repaint(self, mode=const.REDRAW_MAP):
        if mode == const.REDRAW_MAP:
            self.draw_map()
            self._mdc2.Blit(0, 0, self._width, self._height, self._mdc1, 0, 0)
            self.draw_tracks()
            self._dc.Blit(0, 0, self._width, self._height, self._mdc1, 0, 0)
        elif mode == const.REDRAW_TRACK:
            self._mdc1.Blit(0, 0, self._width, self._height, self._mdc2, 0, 0)
            self.draw_tracks()
            self._dc.Blit(0, 0, self._width, self._height, self._mdc1, 0, 0)
        elif mode == const.REDRAW_COPY:
            self._dc.Blit(0, 0, self._width, self._height, self._mdc1, 0, 0)
        else:
            pass
        self.redraw_selected_track_line()
        self.draw_way_points()
        self.draw_photos()
        self.g.frame.show_status_info(zoom=self._zoom)

    def draw_way_points(self):
        if self.g.in_editing:
            return
        
        # 每次重绘wpt时必须初始化的参数
        self._pixel2wpt = {}  # 屏幕坐标点与wpt对象的对应关系，以便鼠标选择
        self._popup_context_wpt = {}  # 右键弹出窗口的上下文信息
        for wpt in self.g.wpt_list:
            self.draw_way_point(wpt)
            
    def draw_way_point(self, wpt):
        wpt.spx = self.get_spx_from_fpx(wpt.fpx)
        wpt.spy = self.get_spy_from_fpy(wpt.fpy)
        if wpt.is_visible:
            if self.pos_in_screen((wpt.spx, wpt.spy)):
                spx = wpt.spx - 16
                spy = wpt.spy - 32
                self._dc.DrawBitmap(self.g.pin_bmps[wpt.bmp_index], spx, spy, True)
                for spy1 in range(spy, spy+32):
                    for spx1 in range(spx, spx + 32):
                        self._pixel2wpt[(spx1, spy1)] = wpt  # 添加坐标与wpt对应关系，以便鼠标选择
                pass

    def draw_photos(self):
        if self.g.in_editing:
            return

        # 每次重绘wpt时必须初始化的参数
        self._pixel2photo = {}  # 屏幕坐标点与photo对象的对应关系，以便鼠标选择
        self._popup_context_photo = {}  # 右键弹出窗口的上下文信息
        for photo in self.g.photo_list:
            self.draw_photo(photo)

    def draw_photo(self, photo):
        photo.spx = self.get_spx_from_fpx(photo.fpx)
        photo.spy = self.get_spy_from_fpy(photo.fpy)
        if self.pos_in_screen((photo.spx, photo.spy)):
            spx = photo.spx - 16
            spy = photo.spy - 16
            self._dc.DrawBitmap(photo.bmp, spx, spy, True)
            for spy1 in range(spy, spy + 32):
                for spx1 in range(spx, spx + 32):
                    self._pixel2photo[(spx1, spy1)] = photo  # 添加坐标与wpt对应关系，以便鼠标选择
            pass

    def draw_map(self):
        if self.g.hide_map:
            self._mdc1.Clear()
            return
        
        self._drag_start_pos = None
        for map_list in [self.g.map_list_main, self.g.map_list_trans]:
            for map_source in map_list[-1::-1]:
                if map_source.is_visible:
                    map_source.tiles_to_be_displayed = []
                    if self.need_jiupian() and map_source.need_jiupian():
                        corner1_tile_x = self._corner1_tile_x_gcj02
                        corner1_tile_y = self._corner1_tile_y_gcj02
                        corner2_tile_x = self._corner2_tile_x_gcj02
                        corner2_tile_y = self._corner2_tile_y_gcj02
                        corner1_px_offset_in_tile = self._corner1_px_gcj02_offset_in_tile
                        corner1_py_offset_in_tile = self._corner1_py_gcj02_offset_in_tile
                    else:
                        corner1_tile_x = self._corner1_tile_x
                        corner1_tile_y = self._corner1_tile_y
                        corner2_tile_x = self._corner2_tile_x
                        corner2_tile_y = self._corner2_tile_y
                        corner1_px_offset_in_tile = self._corner1_px_offset_in_tile
                        corner1_py_offset_in_tile = self._corner1_py_offset_in_tile
                    for tile_y in range(corner1_tile_y, corner2_tile_y + 1):
                        spy = (tile_y - corner1_tile_y) * const.MAP_TILE_SIZE - corner1_py_offset_in_tile
                        for tile_x in range(corner1_tile_x, corner2_tile_x + 1):
                            spx = (tile_x - corner1_tile_x) * const.MAP_TILE_SIZE - corner1_px_offset_in_tile

                            # 当zoom_out至整个世界地图小于屏幕窗口时，地图之外的位置显示空白图片，不下载直接绘制
                            # 在中国地图右侧重复显示一半世界地图（美洲），以使中国地图可始终居中
                            if tile_y < 0 \
                                    or tile_y >= (1 << self._zoom) \
                                    or tile_x < 0 \
                                    or tile_x >= (1 << self._zoom) * 3 // 2:
                                self.draw_tile(self.g.tile_blank_bmp, spx, spy)
                                continue
                            tile_x %= (1 << self._zoom)  # 针对右侧重复显示的一半地图

                            tile_id = map_source.make_tile_id(tile_x, tile_y, self._zoom)
                            tile_url = map_source.make_url(tile_x, tile_y, self._zoom)
                            self.g.tile_mgr.get_tile_async(tile_url, tile_id, map_source.format)
                            map_source.tiles_to_be_displayed.append((tile_id, spx, spy))
        for map_list in [self.g.map_list_main, self.g.map_list_trans]:
            for map_source in map_list[-1::-1]:
                if map_source.is_visible:
                    while map_source.tiles_to_be_displayed:
                        i = len(map_source.tiles_to_be_displayed)
                        for (tile_id, spx, spy) in map_source.tiles_to_be_displayed[-1::-1]:
                            i -= 1
                            tile_bmp = self.g.tile_mgr.get_tile_cache(tile_id)
                            if tile_bmp:
                                map_source.tiles_to_be_displayed.pop(i)
                                self.draw_tile(tile_bmp, spx, spy)

    def need_jiupian(self):
        return True if self._zoom > 4 else False  # 只有显示级别大于4时，才进行地图纠偏

    def draw_tile(self, tile_bmp, spx, spy):
        self._mdc1.DrawBitmap(tile_bmp, spx, spy, True)

    def draw_tracks(self):
        # 每次重绘轨迹时必须初始化的参数
        self._pixel2point = {}  # 屏幕坐标点与轨迹点对象的对应关系，以便鼠标选择
        self._popup_context = {}  # 右键弹出窗口的上下文信息
        if self.g.in_editing:
            self.draw_edit_tracks()
        else:
            for track in self.g.track_list:
                if track.is_visible and self.track_line_in_screen(track):
                    self.draw_track_line(self._mdc1, track)
            
    def draw_track_line(self, dc, track_line):
        coords = track_line.screen_coords = []
        for i in track_line.points_list_for_draw[self._zoom]:
            point = track_line.track_points[i]
            point.spx = spx = self.get_spx_from_fpx(point.fpx)
            point.spy = spy = self.get_spy_from_fpy(point.fpy)
            coords.append((spx, spy))
            if self.pos_in_screen((spx, spy)):
                try:
                    self._pixel2point[(spx, spy)].append(point)  # 添加坐标与轨迹点对应关系，以便鼠标选择
                except KeyError:
                    self._pixel2point[(spx, spy)] = [point]

        if track_line is self.g.track_tree.selected_track_line:
            return    # 当前选中轨迹会再最后重绘，所以暂时不画，但屏幕坐标计算以及坐标与轨迹点映射仍在这里进行

        color = wx.Colour(track_line.red, track_line.green, track_line.blue, track_line.alpha)
        width = track_line.width
        if not track_line.draw_line_dashed:
            dc.SetPen(wx.Pen(color, width))
        else:
            dc.SetPen(wx.Pen(color, width, wx.PENSTYLE_LONG_DASH))
        num = len(coords)
        for i in range(0, num-1):
            self.draw_line_between_points(dc, coords[i], coords[i + 1])
        if track_line.draw_endpoints:
            self.draw_track_end_points(dc, track_line)

    def draw_edit_tracks(self):
        for track_line in self.g.edit_track_list:
            if not track_line.is_checked:
                self.draw_edit_track_line(self._mdc1, track_line)
        for track_line in self.g.edit_track_list:
            if track_line.is_checked:
                self.draw_edit_track_line(self._mdc1, track_line)

    def draw_edit_track_line(self, dc, track_line):
        coords = track_line.screen_coords = []
        for point in track_line.track_points:
            spx = point.spx = self.get_spx_from_fpx(point.fpx)
            spy = point.spy = self.get_spy_from_fpy(point.fpy)
            if not coords or (spx, spy) != coords[-1]:  # 去除重复坐标点，只保留第一个
                coords.append((spx, spy))
                if self.pos_in_screen((spx, spy)):
                    if (spx, spy) not in self._pixel2point:
                        self._pixel2point[(spx, spy)] = []
                    self._pixel2point[(spx, spy)].append(point)  # 添加坐标与轨迹点对应关系，以便鼠标选择

        if track_line is self.g.track_edit.selected_track_line:
            return  # 以后还要重画

        num = len(coords)
        if track_line.is_checked:
            color = wx.Colour(255, 255, 0, 255)
        else:
            color = wx.Colour(0, 0, 255, 255)
        width = 2
    
        dc.SetPen(wx.Pen(color, 1))
        dc.SetBrush(wx.Brush(color))
        for i in range(0, num):
            self.draw_point(dc, coords[i])
    
        dc.SetPen(wx.Pen(color, width))
        for i in range(0, num - 1):
            self.draw_line_between_points(dc, coords[i], coords[i + 1])
    
        if track_line.draw_endpoints:
            self.draw_track_end_points(dc, track_line)

    def redraw_selected_track_line(self):
        if self.g.in_editing:
            self.redraw_edit_selected_track_line()
        else:
            self.redraw_noedit_selected_track_line()
            
    def redraw_noedit_selected_track_line(self):
        track_line = self.g.track_tree.selected_track_line
        if track_line is None or not track_line.is_visible or not self.track_line_in_screen(track_line):
            return
        coords = track_line.screen_coords
        num = len(coords)
        
        if num < 1:
            return

        color = wx.Colour(track_line.red, track_line.green, track_line.blue, track_line.alpha)
        bg_color = wx.Colour(const.SELECTED_LINE_BG_COLOR_RED, const.SELECTED_LINE_BG_COLOR_GREEN,
                             const.SELECTED_LINE_BG_COLOR_BLUE, const.SELECTED_LINE_BG_COLOR_ALPHA)
        width = 2
        bg_width = width + 4

        self._dc.SetPen(wx.Pen(bg_color, bg_width))
        for i in range(0, num-1):
            self.draw_line_between_points(self._dc, coords[i], coords[i+1])

        if not track_line.draw_line_dashed:
            self._dc.SetPen(wx.Pen(color, width))
        else:
            self._dc.SetPen(wx.Pen(color, width, wx.PENSTYLE_LONG_DASH))
        for i in range(0, num-1):
            self.draw_line_between_points(self._dc, coords[i], coords[i+1])

        if track_line.draw_endpoints:
            self.draw_track_end_points(self._dc, track_line)

    def redraw_edit_selected_track_line(self):
        track_line = self.g.track_edit.selected_track_line
        if not track_line:
            return

        coords_1 = []
        coords_sel = []
        coords_2 = []
        
        i = 0
        for point in track_line.track_points:
            spx = point.spx = self.get_spx_from_fpx(point.fpx)
            spy = point.spy = self.get_spy_from_fpy(point.fpy)
            if i <= track_line.sel_start_idx:
                if not coords_sel or (spx, spy) != coords_sel[-1]:
                    coords_1.append((spx, spy))
            if track_line.sel_start_idx <= i <= track_line.sel_end_idx:
                if not coords_sel or (spx, spy) != coords_sel[-1]:
                    coords_sel.append((spx, spy))
            if i >= track_line.sel_end_idx:
                if not coords_2 or (spx, spy) != coords_2[-1]:
                    coords_2.append((spx, spy))
            i += 1
        num_1 = len(coords_1)
        num_sel = len(coords_sel)
        num_2 = len(coords_2)

        if track_line.is_checked:
            color = wx.Colour(255, 255, 0, 255)
        else:
            color = wx.Colour(0, 0, 255, 255)
        sel_color = wx.Colour(0, 255, 0, 255)
        width = 2

        self._dc.SetPen(wx.Pen(color, 1))
        self._dc.SetBrush(wx.Brush(color))
        for pos in (coords_1 + coords_2):
            self.draw_point(self._dc, pos)
            
        self._dc.SetPen(wx.Pen(color, width))
        for i in range (0, num_1 - 1):
            self.draw_line_between_points(self._dc, coords_1[i], coords_1[i + 1])
        for i in range(0, num_2 - 1):
            self.draw_line_between_points(self._dc, coords_2[i], coords_2[i + 1])

        self._dc.SetPen(wx.Pen(sel_color, 1))
        self._dc.SetBrush(wx.Brush(sel_color))
        for pos in coords_sel:
            self.draw_point(self._dc, pos)

        self._dc.SetPen(wx.Pen(sel_color, width))
        for i in range(0, num_sel - 1):
            self.draw_line_between_points(self._dc, coords_sel[i], coords_sel[i + 1])

        if track_line.draw_endpoints:
            self.draw_track_end_points(self._dc, track_line)

        # 在选中轨迹的当前轨迹点上做标记，用以作为轨迹段起始点或结束点
        if track_line.selected_point:
            spx = track_line.selected_point.spx
            spy = track_line.selected_point.spy
            self.cross_hair(self._dc, spx, spy)

    def cross_hair(self, dc, spx, spy):
        dc.SetPen(wx.Pen(wx.Colour(255, 0, 0, 255), 1))
        dc.DrawLine(spx, 0, spx, self._height)
        dc.DrawLine(0, spy, self._width, spy)

    def draw_track_end_points(self, dc, track_line):
        point_1 = track_line.track_points[0]
        point_2 = track_line.track_points[-1]
        spx1 = point_1.spx
        spy1 = point_1.spy
        spx2 = point_2.spx
        spy2 = point_2.spy
        if self.pos_in_screen((spx1, spy1)):
            dc.SetPen(wx.Pen(wx.Colour(255, 125, 0, 255), 2))
            dc.SetBrush(wx.Brush(wx.Colour(0, 255, 0, 255)))
            dc.DrawCircle(spx1, spy1, 5)
        if self.pos_in_screen((spx2, spy2)):
            dc.SetPen(wx.Pen(wx.Colour(255, 0, 0, 255), 2))
            dc.SetBrush(wx.Brush(wx.Colour(255, 255, 255, 255)))
            dc.DrawCircle(spx2, spy2, 5)
            dc.SetPen(wx.Pen(wx.Colour(255, 0, 0, 255), 1))
            dc.SetBrush(wx.Brush(wx.Colour(255, 0, 0, 255)))
            dc.DrawCircle(spx2, spy2, 2)
    
    def draw_line_between_points(self, dc, pos1, pos2):
        if self.pos_in_screen(pos1) or self.pos_in_screen(pos2):
            dc.DrawLine(pos1[0], pos1[1], pos2[0], pos2[1])
   
    def draw_point(self, dc, pos):
        if self.pos_in_screen(pos):
            dc.DrawCircle(pos[0], pos[1], 2)
            
    def pos_in_screen(self, pos):
        return True if 0 <= pos[0] < self._width and 0 <= pos[1] < self._height else False
    
    def track_line_in_screen(self, track_line):
        px_min = transform.get_px_from_fpx(track_line.fpx_min, self._zoom)
        px_max = transform.get_px_from_fpx(track_line.fpx_max, self._zoom)
        py_min = transform.get_py_from_fpy(track_line.fpy_min, self._zoom)
        py_max = transform.get_py_from_fpy(track_line.fpy_max, self._zoom)
        if px_min > self._corner2_px or px_max < self._corner1_px or py_min > self._corner2_py or py_max < self._corner1_py:
            return False
        else:
            return True

    def on_enter(self, event):
        self.SetFocus()

    def on_mousewheel(self, event):
        rotation = event.GetWheelRotation()
        if rotation > 0:
            self.zoom_in()
        elif rotation < 0:
            self.zoom_out()
            
    def on_left_down(self, event):
        pos = event.GetPosition()
        self._drag_start_pos = pos

        if self.g.in_editing and self._self_drawing:  # 编辑状态下自绘轨迹，左键单击，创建一新的轨迹点
            spx = self._drag_start_pos.x
            spy = self._drag_start_pos.y
            lon = self.get_lon_from_spx(spx)
            lat = self.get_lat_from_spy(spy)
            track_point = TrackPoint(self._drawing_track, lon, lat)
            track_point.spx = spx
            track_point.spy = spy
            self._drawing_track.track_points.append(track_point)
            self.repaint(mode=const.REDRAW_TRACK)
        elif self.g.in_editing and self._to_drag_point: # 编辑状态下拖拽轨迹点，左键单击，开始拖拽
            track_line = self.get_nearest_track_line(pos, manual_select=False)
            if track_line:
                if track_line.selected_point is self._dragged_point:
                    self.SetCursor(wx.Cursor(wx.CURSOR_BULLSEYE))
                    self._dragging_point = True
                    self.g.track_edit.set_selected_track_line(None)  # 去除选中以避免屏幕抖动
                    self.repaint(mode=const.REDRAW_TRACK)  # 重绘一次轨迹，把去除选中的轨迹画上

    def on_left_up(self, event):
        self.SetCursor(wx.STANDARD_CURSOR)
        pos = event.GetPosition()

        if self.g.in_editing:
            if not self._self_drawing and not self._to_drag_point:
                # 编辑状态，左键单击，首次选中该轨迹，之后选择轨迹段起始点和结束点
                track_line = self.get_nearest_track_line(pos, manual_select=True)
                if not track_line:
                    # 左键单击，未选中轨迹
                    if self.g.track_edit.selected_track_line:
                        # 已有选中轨迹段仍选中，但不再选中轨迹段，不再显示十字光标
                        if self.g.track_edit.selected_track_line.selected_point:
                            self.g.track_edit.selected_track_line.selected_point = None
                            self.g.frame.repaint(canvas=const.REDRAW_COPY)
                    return
                # 左键单击，选中轨迹
                if track_line is not self.g.track_edit.selected_track_line:
                    self.g.track_edit.set_selected_track_line(track_line)
                self.g.frame.repaint(canvas=const.REDRAW_TRACK)
            elif self._to_drag_point and self._dragging_point:  # 编辑状态下拖拽轨迹点，左键松开，结束拖拽
                spx = pos.x
                spy = pos.y
                fpx = self.get_fpx_from_spx(spx)
                fpy = self.get_fpy_from_spy(spy)
                lon = transform.get_longitude_from_fpx(fpx)
                lat = transform.get_latitude_from_fpy(fpy)
                self._dragged_point.lon = lon
                self._dragged_point.lat = lat
                self._dragged_point.fpx = fpx
                self._dragged_point.fpy = fpy
                self._dragged_point.spx = spx
                self._dragged_point.spy = spy
                self._dragged_point.track_line.compute_track_line_args()
                self.g.track_edit.set_selected_track_line(self._dragged_point.track_line)
                self.g.frame.repaint(canvas=const.REDRAW_TRACK)
                self.SetCursor(wx.STANDARD_CURSOR)
                self._to_drag_point = False
                self._dragging_point = False
                self._dragged_point = None
            elif self._to_drag_point and not self._dragging_point:  # 编辑状态下拖拽轨迹点，未选中需要拖拽的点，左键松开，结束拖拽
                self.SetCursor(wx.STANDARD_CURSOR)
                self._to_drag_point = False
                self._dragging_point = False
                self._dragged_point = None
        else:
            if self.g.downloading_map:
                # 非编辑状态，左键松开，弹出对话框下载离线地图
                pos1 = self._drag_start_pos
                pos2 = event.GetPosition()
                rectangle_selected = True
                if pos2.x > pos1.x and pos2.y > pos1.y:
                    corner1_spx = pos1.x
                    corner1_spy = pos1.y
                    corner2_spx = pos2.x
                    corner2_spy = pos2.y
                elif pos2.x < pos1.x and pos2.y < pos1.y:
                    corner1_spx = pos2.x
                    corner1_spy = pos2.y
                    corner2_spx = pos1.x
                    corner2_spy = pos1.y
                elif pos2.x < pos1.x and pos2.y > pos1.y:
                    corner1_spx = pos2.x
                    corner1_spy = pos1.y
                    corner2_spx = pos1.x
                    corner2_spy = pos2.y
                elif pos2.x > pos1.x and pos2.y < pos1.y:
                    corner1_spx = pos1.x
                    corner1_spy = pos2.y
                    corner2_spx = pos2.x
                    corner2_spy = pos1.y
                else:
                    rectangle_selected = False
                    
                if rectangle_selected:
                    self.SetCursor(wx.STANDARD_CURSOR)
                    corner1_fpx = self.get_fpx_from_spx(corner1_spx)
                    corner1_fpy = self.get_fpy_from_spy(corner1_spy)
                    corner2_fpx = self.get_fpx_from_spx(corner2_spx)
                    corner2_fpy = self.get_fpy_from_spy(corner2_spy)
                    
                    dialog = MapDownloadDialog(g=self.g, corner1_fpx=corner1_fpx, corner1_fpy=corner1_fpy,
                                               corner2_fpx=corner2_fpx, corner2_fpy=corner2_fpy)
                    dialog.CentreOnParent()
                    dialog.ShowModal()
                    dialog.Destroy()
                    
                self.g.downloading_map = False
                self.repaint(mode=const.REDRAW_COPY)
            else:
                # 非编辑状态，左键单击
                photo = self.get_photo_from_pos((pos.x, pos.y,))
                if photo:  # 如果在photo上方
                    self.on_click_photo(photo)
                else:
                    wpt = self.get_wpt_from_pos((pos.x, pos.y,))
                    if wpt:  # 如果在wpt上方
                        self.on_click_wpt(wpt)
                    else:  # 如果在轨迹点附近，选中该轨迹，不缩放
                        track_line = self.get_nearest_track_line((pos.x, pos.y,), manual_select=True)
                        if not track_line:
                            return
                        if track_line is not self.g.track_tree.selected_track_line:
                            self.g.track_tree.selected_track_line = track_line
                            self.g.track_tree.SelectItem(self.g.track_tree.selected_track_line.tree_node)
                            self.g.frame.repaint(canvas=const.REDRAW_TRACK)

    def on_motion(self, event):
        pos = event.GetPosition()
        if event.Dragging() and event.LeftIsDown():
            if self.g.in_editing and self._to_drag_point and self._dragging_point:
                # 编辑状态下拖拽轨迹点，正在拖拽， 画橡皮筋线条
                self.repaint(mode=const.REDRAW_COPY)
                track_line = self._dragged_point.track_line
                index = track_line.track_points.index(self._dragged_point)
                if index > 0:
                    spx_pre = track_line.track_points[index-1].spx
                    spy_pre = track_line.track_points[index-1].spy
                    self._dc.SetPen(wx.Pen(wx.Colour(255, 0, 0, 255), 1))
                    self._dc.DrawLine(spx_pre, spy_pre, pos.x, pos.y)
                if index < len(track_line.track_points) - 1:
                    spx_next = track_line.track_points[index + 1].spx
                    spy_next = track_line.track_points[index + 1].spy
                    self._dc.SetPen(wx.Pen(wx.Colour(255, 0, 0, 255), 1))
                    self._dc.DrawLine(spx_next, spy_next, pos.x, pos.y)
            elif not self.g.in_editing and self.g.downloading_map:
                # 非编辑状态，下载离线地图，拖拽选择地图区域
                pos1 = self._drag_start_pos
                pos2 = event.GetPosition()
                self.repaint(mode=const.REDRAW_COPY)
                self._dc.SetPen(wx.Pen(wx.Colour(255, 0, 0, 255), 1))
                self._dc.SetBrush(wx.Brush(wx.Colour(255, 0, 0, 255), wx.BRUSHSTYLE_CROSSDIAG_HATCH))
                self._dc.DrawRectangle(pos1.x, pos1.y, pos2.x-pos1.x, pos2.y-pos1.y)
            else:
                # 编辑或非编辑状态，非拖拽轨迹点状态，拖动地图
                self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
                if self._drag_start_pos is not None:
                    delta_px = abs(pos.x - self._drag_start_pos.x)
                    delta_py = abs(pos.y - self._drag_start_pos.y)
                    if delta_px <= const.PAN_THRESHOLD and delta_py <= const.PAN_THRESHOLD:
                        return
                    self.pan(self._drag_start_pos.x - pos.x, self._drag_start_pos.y - pos.y)
                    self._drag_start_pos = event.GetPosition()
        else:
            # 鼠标非拖拽状态下移动，显示光标位置经纬度坐标
            lon = self.get_lon_from_spx(pos.x)
            lat = self.get_lat_from_spy(pos.y)
            self.g.frame.show_status_info(pos=(lon, lat))

            photo = self.get_photo_from_pos((pos.x, pos.y))
            if photo:
                self.display_spot_info(photo)
            else:
                wpt = self.get_wpt_from_pos((pos.x, pos.y))
                if wpt:
                    self.display_spot_info(wpt)

            if self.g.in_editing and self._self_drawing:  # 编辑状态下自绘轨迹，显示橡皮筋线条
                if len(self._drawing_track.track_points) > 0:
                    self.repaint(const.REDRAW_COPY)
                    self.draw_edit_track_line(self._dc, self._drawing_track)
                    spx_pre = self._drawing_track.track_points[-1].spx
                    spy_pre = self._drawing_track.track_points[-1].spy
                    self._dc.SetPen(wx.Pen(wx.Colour(255, 0, 0, 255), 1))
                    self._dc.DrawLine(spx_pre, spy_pre, pos.x, pos.y)
            elif self.g.in_editing and self._to_drag_point: # 编辑状态下准备拖拽轨迹点，遇到可拖拽轨迹点时改变光标
                track_line = self.get_nearest_track_line(pos, manual_select=False)
                if track_line:
                    self._dragged_point = track_line.selected_point
                    self.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
                else:
                    self.SetCursor(wx.Cursor(wx.CURSOR_WATCH))

    def on_left_dclick(self, event):
        pos = event.GetPosition()
        if not self.g.in_editing:
            # 非编辑状态，左键双击选中该轨迹并缩放至适合屏幕
            track_line = self.get_nearest_track_line(pos, manual_select=True)
            if not track_line:
                return
            self.g.track_tree.selected_track_line = track_line
            self.g.track_tree.SelectItem(self.g.track_tree.selected_track_line.tree_node)
            track_line.is_visible = True
            self.g.db_mgr.update_visible(track_line)
            self.g.track_tree.label_visible_data(track_line)
            self.zoom_to_track_line(track_line)
        elif self.g.in_editing and self._self_drawing: # 编辑状态下自绘轨迹，双击结束
            if len(self._drawing_track.track_points) < 1:
                self.g.edit_track_list.pop()
            else:
                now = datetime.datetime.now()
                for point in self._drawing_track.track_points:
                    point.set_timestamp_local(now)   # 所有轨迹点设一个统一时间
                    
                self._drawing_track.compute_track_line_args()
                self.g.track_edit.InsertStringItem(len(self.g.edit_track_list), self._drawing_track.name)
                # self.repaint(REDRAW_TRACK) # 单击生成线段时已经重画过，结束后不必重复
            self._self_drawing = False

    def on_key_down(self, event):
        if self.g.in_editing and self._self_drawing:
            if event.GetKeyCode() == wx.WXK_DELETE or event.GetKeyCode() == wx.WXK_BACK:
                if len(self._drawing_track.track_points) > 1:
                    self._drawing_track.track_points.pop()
                    self.repaint(mode=const.REDRAW_TRACK)
        else:
            self.g.track_chart.on_key_down(event)
        
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.g.full_screen = False
            self.g.frame.ShowFullScreen(False)
            self.g.frame.Maximize()
            # self.g.frame.Bind(wx.EVT_SIZE, self.g.frame.on_resize, self.g.frame)

    def get_nearest_track_line(self, pos, manual_select=False):
        spx, spy = pos
        if self.g.in_editing:
            near_pos = [(spx, spy), (spx - 1, spy), (spx, spy - 1), (spx + 1, spy), (spx, spy + 1), (spx - 1, spy - 1),
                        (spx + 1, spy - 1), (spx - 1, spy + 1), (spx + 1, spy + 1), (spx - 2, spy - 2),
                        (spx - 1, spy - 2), (spx, spy - 2), (spx + 1, spy - 2), (spx + 2, spy - 2), (spx - 2, spy - 1),
                        (spx + 2, spy - 1), (spx - 2, spy), (spx + 2, spy), (spx - 2, spy + 1),(spx + 2, spy + 1),
                        (spx - 2, spy + 2), (spx - 1, spy + 2), (spx, spy + 2), (spx + 1, spy + 2), (spx + 2, spy + 2)]
        else:
            near_pos = [(spx, spy)]
            for i in range(-9, 10):
                for j in range(-9, 10):
                    if i != 0 and j != 0:
                        near_pos.append((spx + i, spy + j))

        track_line_list = []
        for (spx1, spy1) in near_pos:
            if (spx1, spy1) in self._pixel2point:
                for track_point in self._pixel2point[(spx1, spy1)]:
                    if track_point.track_line not in track_line_list:
                        track_point.track_line.selected_point = track_point
                        track_line_list.append(track_point.track_line)
        if not track_line_list:
            return None
        elif len(track_line_list) == 1:
            if manual_select:
                return track_line_list[0]
            elif self.g.in_editing and track_line_list[0] is self.g.track_edit.selected_track_line:
                return track_line_list[0]
            return None
        elif manual_select:
            dlg = TrackSelectDlg(track_line_list)
            dlg.CentreOnParent()
            ret = -1
            if dlg.ShowModal() == wx.ID_OK:
                ret = dlg.sel_idx
            dlg.Destroy()
            return track_line_list[ret] if ret >= 0 else None
        elif self.g.in_editing and self.g.track_edit.selected_track_line in track_line_list:
            return self.g.track_edit.selected_track_line
        else:
            return None

    def get_wpt_from_pos(self, pos):
        return self._pixel2wpt.get(pos)

    def get_photo_from_pos(self, pos):
        return self._pixel2photo.get(pos)

    def zoom_to_track_line(self, track_line):
        self.zoom_to_range(track_line.fpx_min, track_line.fpx_max, track_line.fpy_min, track_line.fpy_max)
        self.g.frame.repaint(canvas=const.REDRAW_NONE)

    def on_right_up(self, event):
        pos = event.GetPosition()
        wpt = self.get_wpt_from_pos((pos.x, pos.y,))
        if wpt:  # 如果在wpt上方
            self.on_click_wpt(wpt)
        else:
            photo = self.get_photo_from_pos((pos.x, pos.y,))
            if photo:  # 如果在photo上方
                self.on_click_photo(photo)
            else:
                track_line = self.get_nearest_track_line(pos, manual_select=True)
                if track_line:
                    if self.g.in_editing:
                        if track_line is not self.g.track_edit.selected_track_line:
                            self.g.track_edit.set_selected_track_line(track_line)
                            self.g.frame.repaint(canvas=const.REDRAW_TRACK)
                        self.g.track_edit.popup_right_down(self.g.edit_track_list.index(track_line), track_line=track_line)
                    else:
                        if track_line is not self.g.track_tree.selected_track_line:
                            self.g.track_tree.selected_track_line = track_line
                            self.g.track_tree.SelectItem(self.g.track_tree.selected_track_line.tree_node)
                            self.g.frame.repaint(canvas=const.REDRAW_TRACK)
                        self.g.track_tree.popup_track_line_operations(track_line)
                else:
                    self.popup_right_up(pos)

    def popup_right_up(self, pos):
        menu = wx.Menu()
        if self.g.in_editing:
            text = '退出编辑状态'
            menu_item = menu.Append(-1, text)
            self.Bind(wx.EVT_MENU, self.g.frame.on_edit_status, menu_item)
    
            menu.AppendSeparator()
            text = '自绘轨迹'
            menu_item = menu.Append(-1, text)
            self.Bind(wx.EVT_MENU, self.on_self_drawing, menu_item)
    
            menu.AppendSeparator()
            text = '拖拽调整轨迹点'
            menu_item = menu.Append(-1, text)
            self.Bind(wx.EVT_MENU, self.on_drag_point, menu_item)

            menu.AppendSeparator()
            text = '配置在线地图'
            menu_item = menu.Append(-1, text)
            self.Bind(wx.EVT_MENU, self.g.frame.on_map_src_dlg, menu_item)

            menu.AppendSeparator()
            text = '显示在线地图' if self.g.hide_map else '隐藏所有地图'
            menu_item = menu.Append(-1, text)
            self.Bind(wx.EVT_MENU, self.g.frame.on_map_hide, menu_item)

            menu.AppendSeparator()
            text = '退出全屏显示' if self.g.full_screen else '全屏显示地图'
            menu_item = menu.Append(-1, text)
            self.Bind(wx.EVT_MENU, self.g.frame.on_map_full_screen, menu_item)

            menu.AppendSeparator()
            text = '地图窗口截屏'
            menu_item = menu.Append(-1, text)
            self.Bind(wx.EVT_MENU, self.g.frame.on_map_screenshot, menu_item)
        else:
            text = '放置路点'
            menu_item = menu.Append(-1, text)
            self._popup_context[menu_item.Id] = pos
            self.Bind(wx.EVT_MENU, self.on_place_pin, menu_item)

            menu.AppendSeparator()
            text = '进入编辑状态'
            menu_item = menu.Append(-1, text)
            self.Bind(wx.EVT_MENU, self.g.frame.on_edit_status, menu_item)

            menu.AppendSeparator()
            text = '导入轨迹文件'
            menu_item = menu.Append(-1, text)
            self.Bind(wx.EVT_MENU, self.g.track_tree.on_open_file, menu_item)

            menu.AppendSeparator()
            text = '配置在线地图'
            menu_item = menu.Append(-1, text)
            self.Bind(wx.EVT_MENU, self.g.frame.on_map_src_dlg, menu_item)

            menu.AppendSeparator()
            text = '显示在线地图' if self.g.hide_map else '隐藏所有地图'
            menu_item = menu.Append(-1, text)
            self.Bind(wx.EVT_MENU, self.g.frame.on_map_hide, menu_item)

            menu.AppendSeparator()
            text = '退出全屏显示' if self.g.full_screen else '全屏显示地图'
            menu_item = menu.Append(-1, text)
            self.Bind(wx.EVT_MENU, self.g.frame.on_map_full_screen, menu_item)

            menu.AppendSeparator()
            text = '地图窗口截屏'
            menu_item = menu.Append(-1, text)
            self.Bind(wx.EVT_MENU, self.g.frame.on_map_screenshot, menu_item)

        self.PopupMenu(menu)
        menu.Destroy()

    def on_drag_point(self, event):
        if self.g.track_edit.selected_track_line is None:
            do_log('请先选择轨迹再调整轨迹点...')
            return
        self._to_drag_point = True
        self.SetCursor(wx.Cursor(wx.CURSOR_WATCH))

    def on_self_drawing(self, event):
        self._self_drawing = True
        self.g.track_edit.selected_track_line = None # 自绘轨迹时时，去选其他轨迹，以避免画面抖动
        self._drawing_track = TrackLine()
        self._drawing_track.name = '自绘轨迹%05d' % auto_id.get_id()
        # self._drawing_track.has_timestamp = False  # 还是保留时间好一点
        self.g.edit_track_list.append(self._drawing_track)
        
    def on_place_pin(self, event):
        pos = self._popup_context[event.Id]
        spx = pos[0]
        spy = pos[1]
        lon = self.get_lon_from_spx(spx)
        lat = self.get_lat_from_spy(spy)
        name = search.find_name_from_pos(lon, lat, self.g.search_api)
        if not name:
            name = '未命名'
        wpt = WayPoint(name, lon, lat, parent=self.g.data_root.uuid, bmp_index=self.g.default_wpt_bmp_index)
        wpt.spx = spx
        wpt.spy = spy
        self.g.add_data(self.g.data_root, wpt)
        self.g.track_tree.SelectItem(wpt.tree_node)
        self.repaint(const.REDRAW_COPY)

    def on_click_wpt(self, wpt):
        self.g.track_tree.SelectItem(wpt.tree_node)
        menu = wx.Menu()

        if wpt.alt <= 0:
            text = '获取高度'
            menu_item = menu.Append(-1, text)
            self._popup_context_wpt[menu_item.Id] = wpt
            self.Bind(wx.EVT_MENU, self.on_get_wpt_alt, menu_item)
            menu.AppendSeparator()

        text = '更改图标'
        menu_item = menu.Append(-1, text)
        self._popup_context_wpt[menu_item.Id] = wpt
        self.Bind(wx.EVT_MENU, self.on_change_wpt_pin, menu_item)

        menu.AppendSeparator()
        text = '隐藏路点'
        menu_item = menu.Append(-1, text)
        self._popup_context_wpt[menu_item.Id] = wpt
        self.Bind(wx.EVT_MENU, self.on_hide_wpt, menu_item)

        menu.AppendSeparator()
        text = '删除路点'
        menu_item = menu.Append(-1, text)
        self._popup_context_wpt[menu_item.Id] = wpt
        self.Bind(wx.EVT_MENU, self.on_del_wpt, menu_item)

        self.PopupMenu(menu)
        menu.Destroy()
            
    def on_del_wpt(self, event):
        wpt = self._popup_context_wpt[event.Id]
        self.g.del_wpt(wpt)
        self.repaint(const.REDRAW_COPY)
        do_log('路点“%s”被删除...' % wpt.name)

    def on_hide_wpt(self, event):
        wpt = self._popup_context_wpt[event.Id]
        wpt.is_visible = False
        self.g.db_mgr.update_visible(wpt)
        self.g.track_tree.label_visible_data(wpt)
        self.repaint(const.REDRAW_COPY)
        do_log('路点“%s”被隐藏...' % wpt.name)

    def on_change_wpt_pin(self, event):
        wpt = self._popup_context_wpt[event.Id]
        dlg = PinSelDlg(self.g, wpt)
        dlg.CentreOnParent()
        dlg.Show()
            
    def on_get_wpt_alt(self, event):
        wpt = self._popup_context_wpt[event.Id]
        alt = self.g.srtm_mgr.get_alt_local(wpt.lon, wpt.lat)
        if alt is not None:
            wpt.alt = alt
            self.repaint(const.REDRAW_COPY)
            do_log('路点高程数据获取成功...')
        else:
            dialog = SrtmWptDlg(g=self.g, wpt=wpt)
            dialog.CentreOnParent()
            dialog.Show()

    def display_spot_info(self, spot):
        tip = spot.get_tip()
        win = SpotTipPopup(self, spot)
        win.Position(self.ClientToScreen(spot.spx, spot.spy), (0, 0))
        win.Show()

    def on_click_photo(self, photo):
        menu = wx.Menu()
        text = '查看大图'
        menu_item = menu.Append(-1, text)
        self._popup_context_photo[menu_item.Id] = photo
        self.Bind(wx.EVT_MENU, self.on_see_big_photo, menu_item)

        menu.AppendSeparator()
        text = '显示朝向'
        menu_item = menu.Append(-1, text)
        self._popup_context_photo[menu_item.Id] = photo
        self.Bind(wx.EVT_MENU, self.on_show_photo_direction, menu_item)

        menu.AppendSeparator()
        text = '删除照片'
        menu_item = menu.Append(-1, text)
        self._popup_context_photo[menu_item.Id] = photo
        self.Bind(wx.EVT_MENU, self.on_del_photo, menu_item)

        self.PopupMenu(menu)
        menu.Destroy()

    def on_see_big_photo(self, event):
        photo = self._popup_context_photo[event.Id]
        height = wx.SystemSettings().GetMetric(wx.SYS_SCREEN_Y) - 100
        if os.path.isfile(photo.path):
            dlg = PhotoViewDlg(photo.path, height, height)
            dlg.CentreOnParent()
            dlg.Show()
        else:
            do_log('照片文件不存在...')

    def on_show_photo_direction(self, event):
        photo = self._popup_context_photo[event.Id]
        spx = photo.spx
        spy = photo.spy
        direction = photo.img_direction
        direction_pi = math.pi * (360.0 - direction) / 180
        dir_img = app_icons.lighting96.GetImage().Rotate(direction_pi, wx.Point(48, 48))
        dir_bmp = wx.Bitmap(dir_img)
        size = dir_img.GetSize()
        self._dc.DrawBitmap(dir_bmp, spx - size.width // 2, spy - size.height // 2, True)
        
        angle = math.pi * direction / 180
        line2 = 2 * self._width
        x_delta2 = line2 * math.sin(angle)
        y_delta2 = line2 * math.cos(angle)
        spx2 = spx + int(x_delta2)
        spy2 = spy - int(y_delta2)
        line1 = 48
        x_delta1 = line1 * math.sin(angle)
        y_delta1 = line1 * math.cos(angle)
        spx1 = spx + int(x_delta1)
        spy1 = spy - int(y_delta1)
        
        self._dc.SetPen(wx.Pen(wx.Colour(255, 0, 0, 255), 2, wx.PENSTYLE_DOT))
        self._dc.DrawLine(spx1, spy1, spx2, spy2)
        
    def on_del_photo(self, event):
        photo = self._popup_context_photo[event.Id]
        self.g.photo_list.remove(photo)
        self.g.db_mgr.del_photo(photo)
        self.repaint(const.REDRAW_COPY)
        do_log('照片“%s”被删除...' % photo.name)



