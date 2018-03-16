#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import math


pi = 3.1415926535897932384626
a = 6378245.0
ee = 0.00669342162296594323


def out_of_China(lon, lat):
    if lon < 72.004 or lon > 137.8347 or lat < 0.8293 or lat > 55.8271:
        return True
    else:
        return False
    

def transform_lon(x, y):
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1*math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * pi) + 20.0 * math.sin(2.0 * x * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * pi) + 40.0 * math.sin(x / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * pi) + 300.0 * math.sin(x / 30.0 * pi)) * 2.0 / 3.0
    return ret


def transform_lat(x, y):
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * pi) + 20.0 * math.sin(2.0 * x * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * pi) + 40.0 * math.sin(y / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * pi) + 320 * math.sin(y * pi / 30.0)) * 2.0 / 3.0
    return ret


def transform(lon, lat):
    if out_of_China(lon,lat):
        return lon, lat
    d_lat = transform_lat(lon - 105.0, lat - 35.0)
    d_lon = transform_lon(lon - 105.0, lat - 35.0)
    rad_lat = lat / 180.0 * pi
    magic = math.sin(rad_lat)
    magic = 1 - ee * magic * magic
    sqrt_magic = math.sqrt(magic)
    d_lat = (d_lat * 180.0) / ((a * (1 - ee)) / (magic * sqrt_magic) * pi)
    d_lon = (d_lon * 180.0) / (a / sqrt_magic * math.cos(rad_lat) * pi)
    mg_lat = lat + d_lat
    mg_lon = lon + d_lon
    return mg_lon, mg_lat


def wgs84_to_gcj02(lon, lat):
    if out_of_China(lon, lat):
        return lon, lat
    d_lat = transform_lat(lon - 105.0, lat - 35.0)
    d_lon = transform_lon(lon - 105.0, lat - 35.0)
    rad_lat = lat / 180.0 * pi
    magic = math.sin(rad_lat)
    magic = 1 - ee * magic * magic
    sqrt_magic = math.sqrt(magic)
    d_lat = (d_lat * 180.0) / ((a * (1 - ee)) / (magic * sqrt_magic) * pi)
    d_lon = (d_lon * 180.0) / (a / sqrt_magic * math.cos(rad_lat) * pi)
    gcj_lat = lat + d_lat
    gcj_lon = lon + d_lon
    return gcj_lon, gcj_lat


def gcj02_to_wgs84(gcj_lon, gcj_lat):
    if out_of_China(gcj_lon, gcj_lat):
        return gcj_lon, gcj_lat
    mg_lon, mg_lat = transform(gcj_lon, gcj_lat)
    lon = gcj_lon * 2 - mg_lon
    lat = gcj_lat * 2 - mg_lat
    return  lon, lat


def gcj02_to_bd09(gcj_lon, gcj_lat):
    x = gcj_lon
    y = gcj_lat
    z = math.sqrt(x * x + y * y) + 0.00002 * math.sin(y * pi)
    theta = math.atan2(y, x) + 0.000003 * math.cos(x * pi)
    bd_lon = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return bd_lon, bd_lat


def bd09_to_gcj02(bd_lon, bd_lat):
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * pi)
    gcj_lon = z * math.cos(theta)
    gcj_lat = z * math.sin(theta)
    return gcj_lon, gcj_lat


def bd09_to_wgs84(bd_lon, bd_lat):
    gcj_lon, gcj_lat = bd09_to_gcj02(bd_lon, bd_lat)
    lon, lat = gcj02_to_wgs84(gcj_lon, gcj_lat)
    return lon, lat


def wgs84_to_bd09(lon, lat):
    gcj_lon, gcj_lat = wgs84_to_gcj02(lon, lat)
    bd_lon, bd_lat = gcj02_to_bd09(gcj_lon, gcj_lat)
    return bd_lon, bd_lat


  