#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import random
import math

from app.globals import const


class MapSource:

    def __init__(self, source, visible=False):
        self.id = source['id']
        self.name = source['name']
        self.url_pattern = source['url']
        self.zoom_min = source['zoom_min']
        self.zoom_max = source['zoom_max']
        if self.zoom_max > const.MAX_ZOOM:
            self.zoom_max = const.MAX_ZOOM
        self.server_part = source['server_part']
        self.coordinates = source['coordinates']
        self.is_transparent = source['transparent']
        self.is_visible = visible
        self.format = source['format']
        self.tiles_to_be_displayed = []  # 元素为三元组，tile_id以及它在屏幕窗口的显示坐标：(tile_id, pixel_x, pixel_y)

    def make_tile_id(self, x, y, z):
        return '%s-z%02d-y%07d-x%07d' % (self.id, z, y, x)

    def make_url_from_tile_id(self, tile_id):
        x = int(tile_id[21:])
        y = int(tile_id[12:19])
        z = int(tile_id[8:10])
        return self.make_url(x, y, z)

    def make_url(self, x, y, z):
        url = self.url_pattern
        if self.server_part is not None:
            server_list = self.server_part.split(',')
            server_rand = server_list[random.randrange(0, len(server_list))]
            url = url.replace('{$serverpart}', server_rand)
            
        if self.is_bingying_map():
            return self.make_bingying_url(url, x, y, z)
        
        if self.is_QQ_map():
            y = int(math.pow(2, z)) - 1 - y
            dx = x // 16
            dy = y // 16
            url = url.replace('{$dx}', str(dx)).replace('{$dy}', str(dy))
            
        url = url.replace('{$x}', str(x)).replace('{$y}', str(y)).replace('{$z}', str(z))

        return url
    
    def make_bingying_url(self, url, x, y, z):
        x_bin = '{0:0{1}b}'.format(x, z)
        y_bin = '{0:0{1}b}'.format(y, z)
        quad_key = ''
        for i in range(z):
            quad_key += str(int(y_bin[i]) * 2 + int(x_bin[i]))
        url = url.replace('{$QuadKey}', quad_key)
        return url
    
    def is_google_map(self):
        return True if 'google.cn' in self.url_pattern else False
    
    def is_QQ_map(self):
        return True if 'map.gtimg.com' in self.url_pattern else False
    
    def is_bingying_map(self):
        return True if 'virtualearth.net' in self.url_pattern or 'ditu.live.com' in self.url_pattern else False
    
    def need_jiupian(self):
        return self.coordinates == 'GCJ02'
        


        
        
        
    
            
        
        
        
        
    