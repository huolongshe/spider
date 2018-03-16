#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import datetime
from app.service import transform


class TrackPoint:
    def __init__(self, track_line, lon, lat, alt=0.0, timestamp=None, fpx=None, fpy=None, restore_from_db=False):
        self.track_line = track_line
        
        self.lon = lon
        self.lat = lat
        self.alt = alt
        self.timestamp = timestamp  # 字符串形式的时间戳，缺省格式为：'yyyy-mm-ddThh:MM:ssZ'，例如：2017-06-29T13:01:19Z
        
        self.spx = None  # 屏幕像素坐标，地图变化时会变动
        self.spy = None

        self.timestamp_local = None
        self.timestamp_utc = None
        
        if restore_from_db:
            self.fpx = fpx
            self.fpy = fpy
        else:
            self.set_timestamp_from_str()
            self.fpx = transform.get_fpx_from_longitude(self.lon)
            self.fpy = transform.get_fpy_from_latitude(self.lat)
            
    def set_timestamp_from_str(self):
        if self.timestamp:
            try:
                self.timestamp_utc = datetime.datetime.strptime(self.timestamp, '%Y-%m-%dT%H:%M:%SZ')
            except ValueError:
                try:
                    self.timestamp_utc = datetime.datetime.strptime(self.timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
                except ValueError:
                    self.set_timestamp_now()
            self.timestamp_local = transform.utc2local(self.timestamp_utc)
        else:
            self.set_timestamp_now()

    def set_timestamp_now(self):
        self.timestamp_local = datetime.datetime.now()
        self.timestamp_utc = transform.local2utc(self.timestamp_local)
        self.timestamp = self.timestamp_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

    def set_timestamp_local(self, timestamp_local):
        self.timestamp_local = timestamp_local
        self.timestamp_utc = transform.local2utc(self.timestamp_local)
        self.timestamp = self.timestamp_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
