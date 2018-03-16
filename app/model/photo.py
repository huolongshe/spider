#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import uuid
import PIL.Image
from PIL.ExifTags import TAGS, GPSTAGS
import wx

from app.service import transform


class Photo:
    def __init__(self, path, db_record=None):
        if db_record:
            self.restore_from_db_record(db_record)
            return
        
        self.uuid = uuid.uuid1().__str__()
        self.name = os.path.basename(path)
        self.path = path

        self.lon = None
        self.lat = None
        self.alt = None
        self.timestamp = None
        self.bmp = None
        
        self.fpx = None
        self.fpy = None
        self.spx = None
        self.spy = None
        self.img_direction = None

        exif_info = {}
        gps_info = {}
        if not os.path.isfile(self.path):
            return

        pil_image = PIL.Image.open(self.path)
        if hasattr(pil_image, '_getexif'):
            exif = pil_image._getexif()
            if exif:
                for tag, value in exif.items():
                    tag_name = TAGS.get(tag, tag)
                    exif_info[tag_name] = value
                if 'GPSInfo' in exif_info:
                    for tag, value in exif_info['GPSInfo'].items():
                        tag_name = GPSTAGS.get(tag, tag)
                        gps_info[tag_name] = value
        if not gps_info:
            return

        lon_ref = gps_info.get('GPSLongitudeRef')
        lat_ref = gps_info.get('GPSLatitudeRef')
        if not lon_ref or not lat_ref:
            return

        lon_d, lon_m, lon_s = gps_info.get('GPSLongitude')
        self.lon = lon_d[0] / lon_d[1] + lon_m[0] / lon_m[1] / 60 + lon_s[0] / lon_s[1] / 3600
        if lon_ref == 'W':
            self.lon = 0 - self.lon
        lat_d, lat_m, lat_s = gps_info.get('GPSLatitude')
        self.lat = lat_d[0] / lat_d[1] + lat_m[0] / lat_m[1] / 60 + lat_s[0] / lat_s[1] / 3600
        if lat_ref == 'S':
            self.lat = 0 - self.lat

        alt = gps_info.get('GPSAltitude')
        if alt:
            self.alt = alt[0] / alt[1]

        img_direction = gps_info.get('GPSImgDirection')
        if img_direction:
            self.img_direction = img_direction[0] / img_direction[1]

        self.timestamp = exif_info.get('DateTimeDigitized')

        pil_image32 = PIL.Image.new('RGBX', (32, 32), color=255)
        pil_image30 = pil_image.resize((30, 30))
        pil_image32.paste(pil_image30, (1, 1))
        img = wx.Image(32, 32)
        img.SetData(pil_image32.convert('RGB').tobytes())
        self.bmp = wx.Bitmap(img)

        self.fpx = transform.get_fpx_from_longitude(self.lon)
        self.fpy = transform.get_fpy_from_latitude(self.lat)
        
    def restore_from_db_record(self, record):
        self.uuid = record[1]
        self.name = record[2]
        self.path = record[3]
        self.lon = record[4]
        self.lat = record[5]
        self.alt = record[6]
        self.timestamp = record[7]
        self.fpx = record[8]
        self.fpy = record[9]
        self.img_direction = record[10]
        img = wx.Image(32, 32)
        img.SetData(record[11])
        self.bmp = wx.Bitmap(img)

    def get_tip(self):
        tip = '照片：%s\n东经：%.08f\n北纬：%.08f' % (self.name, self.lon, self.lat)
        if self.alt:
            tip += '\n海拔：%.01f米' % self.alt
        if self.img_direction:
            tip += '\n朝向：%.01f° ' % self.img_direction
            if 0 <= self.img_direction < 90:
                direction = '东北'
            elif 90 <= self.img_direction < 180:
                direction = '东南'
            elif 180 <= self.img_direction < 270:
                direction = '西南'
            else:
                direction = '西北'
            tip += direction
        if self.timestamp:
            tip += '\n时间：%s' % self.timestamp
        return tip
    
