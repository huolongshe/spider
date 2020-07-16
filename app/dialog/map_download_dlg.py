#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import threading
import time
import PIL.Image  # 安装： pip install Pillow
import requests
import wx

from app.globals import const
from app.globals.global_data import g
from app.service import jiupian
from app.service import transform


class MapDownloadDialog(wx.Dialog):
    def __init__(self, corner1_fpx, corner1_fpy, corner2_fpx, corner2_fpy):
        wx.Dialog.__init__(self, None, -1, '下载离线地图', size=(880, 720))
        self.EnableCloseButton(False)
        self._corner1_fpx_wgs84 = corner1_fpx
        self._corner1_fpy_wgs84 = corner1_fpy
        self._corner2_fpx_wgs84 = corner2_fpx
        self._corner2_fpy_wgs84 = corner2_fpy
        self._corner1_lon_wgs84 = transform.get_longitude_from_fpx(self._corner1_fpx_wgs84)
        self._corner1_lat_wgs84 = transform.get_latitude_from_fpy(self._corner1_fpy_wgs84)
        self._corner2_lon_wgs84 = transform.get_longitude_from_fpx(self._corner2_fpx_wgs84)
        self._corner2_lat_wgs84 = transform.get_latitude_from_fpy(self._corner2_fpy_wgs84)
        self.compute_coordinate(original=True)

        choices = []
        for source in g.map_list_main:
            choices.append(source.name)
        for source in g.map_list_trans:
            choices.append(source.name)

        self._ctl_map_src = wx.RadioBox(parent=self, id=-1, label='选择地图源', pos=(35, 35), size=(220, 520), choices=choices, style=wx.RA_VERTICAL)
        for i in range(len(g.map_list_main)):
            if g.map_list_main[i].is_visible:
                self._ctl_map_src.SetSelection(i)
                self.map_src = g.map_list_main[i]

        wx.StaticText(self, -1, '地图缩放级别：', (50, 575))
        self._ctl_zoom = wx.SpinCtrl(self, -1, '', pos=(160, 573), size=(80, 28))
        self._ctl_zoom.SetRange(5, 19)
        self._ctl_zoom.SetValue(10)
        self._zoom = 10

        self._ctl_HD_resolution = wx.CheckBox(self, -1, '下载高清地图（仅对谷歌系列地图有效）', (50, 610), (300, 30), wx.NO_BORDER)
        self._ctl_HD_resolution.SetValue(False)
        
        wx.StaticText(self, -1, '地图名称：', (300, 35))
        self._ctl_map_name = wx.TextCtrl(self, -1, '我的地图', pos=(380, 33), size=(300, 30))
        self._map_name = '我的地图'

        wx.StaticBox(self, -1, '左上角坐标', pos=(300, 90), size=(250, 150))
        wx.StaticText(self, -1, '东经：', (320, 130))
        self._ctl_corner1_lon = wx.TextCtrl(self, -1, '', pos=(370, 130), size=(150, 30))
        self._ctl_corner1_lon.SetValue('%.08f' % self._corner1_lon_wgs84)
        wx.StaticText(self, -1, '北纬：', (320, 180))
        self._ctl_corner1_lat = wx.TextCtrl(self, -1, '', pos=(370, 180), size=(150, 30))
        self._ctl_corner1_lat.SetValue('%.08f' % self._corner1_lat_wgs84)

        wx.StaticBox(self, -1, '右下角坐标', pos=(580, 90), size=(250, 150))
        wx.StaticText(self, -1, '东经：', (600, 130))
        self._ctl_corner2_lon = wx.TextCtrl(self, -1, '', pos=(650, 130), size=(150, 30))
        self._ctl_corner2_lon.SetValue('%.08f' % self._corner2_lon_wgs84)
        wx.StaticText(self, -1, '北纬：', (600, 180))
        self._ctl_corner2_lat = wx.TextCtrl(self, -1, '', pos=(650, 180), size=(150, 30))
        self._ctl_corner2_lat.SetValue('%.08f' % self._corner2_lat_wgs84)

        wx.StaticText(self, -1, '保存路径：', (300, 260))
        self._ctl_dir = wx.TextCtrl(self, -1, '', pos=(300, 290), size=(500, 30))
        self._ctl_dir.Enable(False)
        self._save_dir = ''
        self._ctl_dir_button = wx.BitmapButton(self, -1, wx.ArtProvider.GetBitmap(wx.ART_FOLDER_OPEN, size=(16, 16)), (810, 290))
        self.Bind(wx.EVT_BUTTON, self.on_dir_button, self._ctl_dir_button)

        self._ctl_del_tiles = wx.CheckBox(self, -1, '下载拼接后删除原始地图瓦片', (600, 330), (300, 30), wx.NO_BORDER)
        self._ctl_del_tiles.SetValue(False)

        self._ctl_download_button = wx.Button(self, -1, '开始下载', pos=(300, 380), size=(100, 50))
        self.Bind(wx.EVT_BUTTON, self.on_download_button, self._ctl_download_button)
        self._ctl_download_button.SetDefault()
        self._downloading = False

        self._ctl_download_percent = wx.Gauge(self, -1, 100, (410, 390), (420, 30))

        self._ctl_log = wx.TextCtrl(self, -1, '', pos=(300, 450), size=(530, 140), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER|wx.TE_READONLY)

        self._ctl_quit = wx.Button(self, wx.ID_OK, '退出', pos=(720, 620))

        self._tile_name_array = []
        self._thread_max = 10
        self._running_threads = 0

    def compute_coordinate(self, original=True):
        if not original:
            self._corner1_fpx_wgs84 = transform.get_fpx_from_longitude(self._corner1_lon_wgs84)
            self._corner1_fpy_wgs84 = transform.get_fpy_from_latitude(self._corner1_lat_wgs84)
            self._corner2_fpx_wgs84 = transform.get_fpx_from_longitude(self._corner2_lon_wgs84)
            self._corner2_fpy_wgs84 = transform.get_fpy_from_latitude(self._corner2_lat_wgs84)

        self._corner1_lon_gcj02, self._corner1_lat_gcj02 = jiupian.wgs84_to_gcj02(self._corner1_lon_wgs84,
                                                                                  self._corner1_lat_wgs84)
        self._corner1_fpx_gcj02 = transform.get_fpx_from_longitude(self._corner1_lon_gcj02)
        self._corner1_fpy_gcj02 = transform.get_fpy_from_latitude(self._corner1_lat_gcj02)

        self._corner2_lon_gcj02, self._corner2_lat_gcj02 = jiupian.wgs84_to_gcj02(self._corner2_lon_wgs84,
                                                                                  self._corner2_lat_wgs84)
        self._corner2_fpx_gcj02 = transform.get_fpx_from_longitude(self._corner2_lon_gcj02)
        self._corner2_fpy_gcj02 = transform.get_fpy_from_latitude(self._corner2_lat_gcj02)

    def on_dir_button(self, event):
        dlg = wx.DirDialog(self, '请选择离线地图保存目录：',
                           style=wx.DD_DEFAULT_STYLE
                           # | wx.DD_DIR_MUST_EXIST
                           # | wx.DD_CHANGE_DIR
                           )
    
        if dlg.ShowModal() == wx.ID_OK:
            self._save_dir = dlg.GetPath()
            self._ctl_dir.SetValue(self._save_dir)
    
        dlg.Destroy()

    def on_download_button(self, event):
        if self._downloading:
            dlg = wx.MessageDialog(self, '你真的要中止下载吗？',
                                   '确认中止下载？',
                                   wx.YES_NO
                                   )
            ret = dlg.ShowModal()
            dlg.Destroy()
            if ret != wx.ID_YES:
                return
            self._downloading = False
            return
        
        self._corner1_lon_wgs84 = float(self._ctl_corner1_lon.GetValue())
        self._corner1_lat_wgs84 = float(self._ctl_corner1_lat.GetValue())
        self._corner2_lon_wgs84 = float(self._ctl_corner2_lon.GetValue())
        self._corner2_lat_wgs84 = float(self._ctl_corner2_lat.GetValue())
        self.compute_coordinate(original=False)
        
        map_src_index = self._ctl_map_src.GetSelection()
        if map_src_index < len(g.map_list_main):
            self._map_src = g.map_list_main[map_src_index]
        else:
            self._map_src = g.map_list_trans[map_src_index - len(g.map_list_main)]
        
        self._zoom = self._ctl_zoom.GetValue()
        if self._zoom > self._map_src.zoom_max:
            dlg = wx.MessageDialog(self, '所选择缩放级别大于当前地图源的最大缩放级别，请重新选择！', '提示', wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        self._download_HD_map = self._ctl_HD_resolution.GetValue()
        self._to_del_tiles_after_merge = self._ctl_del_tiles.GetValue()
        
        self._map_name = self._ctl_map_name.GetValue()
        if not self._map_name:
            self._map_name = '我的地图'
        
        self._save_dir = self._ctl_dir.GetValue()
        if not self._save_dir:
            dlg = wx.MessageDialog(self, '请选择保存路径！', '提示', wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return

        thread = threading.Thread(target=self.download_map, args=())
        thread.setDaemon(True)
        thread.start()
                
    def download_map(self):
        self._ctl_download_button.SetLabel('停止下载')
        self.enable_all_ctrls(False)
        self._downloading = True
        
        if self._map_src.need_jiupian():
            corner1_fpx = self._corner1_fpx_gcj02
            corner1_fpy = self._corner1_fpy_gcj02
            corner2_fpx = self._corner2_fpx_gcj02
            corner2_fpy = self._corner2_fpy_gcj02
        else:
            corner1_fpx = self._corner1_fpx_wgs84
            corner1_fpy = self._corner1_fpy_wgs84
            corner2_fpx = self._corner2_fpx_wgs84
            corner2_fpy = self._corner2_fpy_wgs84

        corner1_px = transform.get_px_from_fpx(corner1_fpx, self._zoom)
        corner1_py = transform.get_py_from_fpy(corner1_fpy, self._zoom)
        corner2_px = transform.get_px_from_fpx(corner2_fpx, self._zoom)
        corner2_py = transform.get_py_from_fpy(corner2_fpy, self._zoom)

        corner1_tile_x = corner1_px // const.MAP_TILE_SIZE
        corner1_tile_y = corner1_py // const.MAP_TILE_SIZE
        corner2_tile_x = corner2_px // const.MAP_TILE_SIZE
        corner2_tile_y = corner2_py // const.MAP_TILE_SIZE
        
        tile_number = (corner2_tile_x - corner1_tile_x + 1) * (corner2_tile_y - corner1_tile_y + 1)
        tile_percent = 90.0 / tile_number
        i = 0
        self._running_threads = 0
        self._tile_name_array = []
        for tile_y in range(corner1_tile_y, corner2_tile_y + 1):
            tile_name_line = []
            for tile_x in range(corner1_tile_x, corner2_tile_x + 1):
                if not self._downloading:
                    while self._running_threads > 0:
                        time.sleep(0.001)  # 等待所有线程都结束
                    self._ctl_log.AppendText('下载过程被强行中止，请手动清除已下载瓦片文件！\r\n')
                    self._ctl_download_percent.SetValue(100)
                    self._ctl_download_button.SetLabel('开始下载')
                    self.enable_all_ctrls(True)
                    return
                tile_id = '%s-z%02d-y%07d-x%07d' % (self._map_src.id, self._zoom, tile_y, tile_x)
                file_name = '%s.%s' % (tile_id, self._map_src.format)
                tile_path = os.path.join(self._save_dir, file_name)
                tile_url = self._map_src.make_url(tile_x, tile_y, self._zoom)
                if self._download_HD_map and self._map_src.is_google_map():
                    tile_url += '&scale=2'

                while self._running_threads >= self._thread_max:
                    time.sleep(0.001)
                thread = threading.Thread(target=self.download_tile_thread, args=(tile_url, tile_path))
                thread.setDaemon(True)
                thread.start()
                
                i += 1
                download_percent = i * tile_percent
                self._ctl_download_percent.SetValue(int(download_percent))
                self._ctl_log.AppendText('下载： %s\r\n' % file_name)
                tile_name_line.append(tile_path)
            self._tile_name_array.append(tile_name_line)
        while self._running_threads > 0:
            time.sleep(0.001)
        self._ctl_log.AppendText('所有地图瓦片下载完成！\r\n')
        self.merge_tiles()

        self._downloading = False
        self._ctl_download_button.SetLabel('开始下载')
        self.enable_all_ctrls(True)

    def download_tile_thread(self, tile_url, tile_path):
        self._running_threads += 1
        if os.path.isfile(tile_path):
            os.remove(tile_path)
        for i in range(5):
            try:
                # headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(tile_url)
                if response.status_code != 200:
                    break  # 文件不存在，跳出循环，不再下载该文件
                image = response.content
                with open(tile_path, 'wb') as fn:
                    fn.write(image)
                break  # 下载成功，跳出循环
            except:
                time.sleep(0.2) # 其他原因下载失败，休息一段时间后重试，最多5遍
        self._running_threads -= 1
        
    def merge_tiles(self):
        if not self._tile_name_array:
            return

        self._ctl_log.AppendText('正在拼接图片...\r\n')
        line_num = len(self._tile_name_array)
        row_num = len(self._tile_name_array[0])
        
        tile_size = const.MAP_TILE_SIZE
        if self._download_HD_map and self._map_src.is_google_map():
            tile_size = const.MAP_TILE_SIZE * 2

        if self._map_src.format == 'jpg':
            mode = 'RGBX'
        elif self._map_src.format == 'png':
            mode = 'RGBA'
        else:
            self._ctl_log.AppendText('图片格式不支持：%s\r\n' %self._map_src.format)
            self._ctl_download_percent.SetValue(100)
            return

        big_image = PIL.Image.new(mode, (row_num * tile_size, line_num * tile_size), color=None)

        line = 0
        for tile_name_line in self._tile_name_array:
            row = 0
            for tile_name in tile_name_line:
                if os.path.isfile(tile_name):
                    image = PIL.Image.open(tile_name)
                    big_image.paste(image, (row * tile_size, line * tile_size))
                    image.close()
                row += 1
            line += 1

        self._ctl_log.AppendText('图片拼接完成，正在保存地图文件...\r\n')
        self._ctl_download_percent.SetValue(93)
        big_image.save(os.path.join(self._save_dir, '%s.%s' % (self._map_name, self._map_src.format)))
        self._ctl_log.AppendText('拼接后地图文件保存完成！\r\n')
        self._ctl_download_percent.SetValue(97)

        if self._to_del_tiles_after_merge:
            self._ctl_log.AppendText('正在删除原始瓦片文件...\r\n')
            for tile_name_line in self._tile_name_array:
                for tile_name in tile_name_line:
                    if os.path.isfile(tile_name):
                        try:
                            os.remove(tile_name)
                        except:
                            head, tail = os.path.split(tile_name)
                            self._ctl_log.AppendText('文件%s删除出错，请手动删除...\r\n' % tail)
            self._ctl_log.AppendText('原始瓦片文件删除完成！\r\n')
        self._ctl_download_percent.SetValue(100)

    def enable_all_ctrls(self, enable=True):
        self._ctl_map_src.Enable(enable)
        self._ctl_zoom.Enable(enable)
        self._ctl_HD_resolution.Enable(enable)
        self._ctl_map_name.Enable(enable)
        self._ctl_corner1_lat.Enable(enable)
        self._ctl_corner1_lon.Enable(enable)
        self._ctl_corner2_lat.Enable(enable)
        self._ctl_corner2_lon.Enable(enable)
        self._ctl_dir_button.Enable(enable)
        self._ctl_del_tiles.Enable(enable)
        self._ctl_quit.Enable(enable)
