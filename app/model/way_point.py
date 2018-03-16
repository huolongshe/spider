#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import datetime
import uuid

from app.service import transform


class WayPoint:
    def __init__(self, name='', lon=0.0, lat=0.0, alt=0.0, timestamp='', parent='', bmp_index=-1):
        self.tree_node = None

        self.uuid = uuid.uuid1().__str__()
        self.name = name
        self.description = ''
        self.parent = parent  # 父亲节点的uuid
        self.order_in_parent = -1

        self.lon = lon
        self.lat = lat
        self.alt = alt
        self.timestamp = timestamp  # 字符串形式的时间戳，缺省格式为：'yyyy-mm-ddThh:MM:ssZ'，例如：2017-06-29T13:01:19Z

        self.fpx = transform.get_fpx_from_longitude(self.lon)
        self.fpy = transform.get_fpy_from_latitude(self.lat)

        self.bmp_index = bmp_index
        self.is_visible = True
    
        self.timestamp_local = None
        self.timestamp_utc = None
        if timestamp:
            self.set_timestamp_from_str(timestamp)
        self.spx = None
        self.spy = None

    def set_timestamp_from_str(self, timestamp_str):
        try:
            self.timestamp_utc = datetime.datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            try:
                self.timestamp_utc = datetime.datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                self.timestamp_utc = None
                self.timestamp_local = None
                return
        self.timestamp_local = transform.utc2local(self.timestamp_utc)

    def get_tip(self):
        tip = '%s\n东经：%.08f\n北纬：%.08f' % (self.name, self.lon, self.lat)
        if self.alt > 0:
            tip += '\n海拔：%.01f米' % self.alt
        if self.timestamp_local:
            time_tuple = self.timestamp_local.timetuple()
            time_str = '%04d-%02d-%02d %02d:%02d:%02d' % (time_tuple.tm_year, time_tuple.tm_mon,
                                                           time_tuple.tm_mday, time_tuple.tm_hour,
                                                           time_tuple.tm_min, time_tuple.tm_sec,)
            tip += '\n时间：%s' % time_str
        return tip
    
    def restore_from_db_record(self, record):
        self.uuid = record[1]
        self.name = record[2]
        self.description = record[3]
        self.parent = record[4]
        self.order_in_parent = record[5]
        self.lon = record[6]
        self.lat = record[7]
        self.alt = record[8]
        self.timestamp = record[9]
        self.fpx = record[10]
        self.fpy = record[11]
        self.bmp_index = record[12]
        self.is_visible = True if record[13] else False
