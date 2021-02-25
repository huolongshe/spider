#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import io
import datetime
import threading
import requests
import wx

from app.globals import const
from app.service.logger import do_log


class TileManager:
    def __init__(self, data_path, tile_transparent_bmp):
        self.tile_transparent_bmp = tile_transparent_bmp
        self._tile_cache = {}
        self._cache_path = os.path.join(data_path, 'mapcache')
        if not os.path.exists(self._cache_path):
            os.mkdir(self._cache_path)

    def get_cache_path(self):
        return self._cache_path

    def get_tile_sync(self, tile_url, tile_id, file_format):
        tile_bmp = self.get_tile_cache(tile_id)
        if tile_bmp and tile_bmp is not self.tile_transparent_bmp:
            return tile_bmp

        if tile_bmp is self.tile_transparent_bmp:  # 之前可能是因为超时等原因缓存的透明图标，重新尝试下载
            return self.get_tile_network(tile_url, tile_id, file_format,)

        return self.get_tile_file(tile_id, file_format) or self.get_tile_network(tile_url, tile_id, file_format,)

    def get_tile_async(self, tile_url, tile_id, file_format):
        tile_bmp = self.get_tile_cache(tile_id)
        if tile_bmp and tile_bmp is not self.tile_transparent_bmp:
            return

        if tile_bmp is self.tile_transparent_bmp:  # 之前可能是因为超时等原因缓存的透明图标，重新尝试下载
            thread = threading.Thread(target=self.get_tile_network, args=(tile_url, tile_id, file_format,))
            thread.setDaemon(True)
            thread.start()
            return

        if not self.get_tile_file(tile_id, file_format):
            thread = threading.Thread(target=self.get_tile_network, args=(tile_url, tile_id, file_format,))
            thread.setDaemon(True)
            thread.start()

    def get_tile_local(self, tile_id, file_format):
        return self.get_tile_cache(tile_id) or self.get_tile_file(tile_id, file_format)

    def get_tile_cache(self, tile_id):
        return self._tile_cache.get(tile_id)

    def get_tile_file(self, tile_id, file_format):
        tile_path = os.path.join(self._cache_path, '%s.%s' % (tile_id, file_format))
        if os.path.isfile(tile_path):
            file_time = os.path.getmtime(tile_path)
            now = datetime.datetime.now()
            time_delta = (now - datetime.datetime.fromtimestamp(file_time)).days
            if time_delta < 30 or tile_id.startswith('map001'):
                try:
                    with open(tile_path, 'rb') as fn:
                        self._tile_cache[tile_id] = wx.Bitmap(wx.Image(io.BytesIO(fn.read())))
                    return self._tile_cache[tile_id]
                except:
                    return None
            else:
                os.remove(tile_path)
                return None
        else:
            return None

    def get_tile_network(self, tile_url, tile_id, file_format):
        tile_path = os.path.join(self._cache_path, '%s.%s' % (tile_id, file_format))
        try:
            # headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(tile_url, timeout=const.DOWNLOAD_TIMEOUT)
            if 200 == response.status_code :
                img = response.content
                self._tile_cache[tile_id] = wx.Bitmap(wx.Image(io.BytesIO(img)))
                try:
                    with open(tile_path, 'wb') as fn:
                        fn.write(img)
                except:
                    do_log('写缓存文件失败：' + '%s.%s' % (tile_id, file_format))
            else:
                self._tile_cache[tile_id] = self.tile_transparent_bmp
                do_log('文件不存在，用透明图片替代：' + tile_url)
        except:
            self._tile_cache[tile_id] = self.tile_transparent_bmp
            do_log('下载失败，用透明图片替代：' + tile_url)

        return self._tile_cache[tile_id]

