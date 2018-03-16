#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import math
import time
import datetime

from app.globals import const


def get_x_from_longitude(lon):
    # 将经度-180度~180度之间的值归一化为0~1之间的实数，经度0度对应值为0.5，西经180度对应值为0，东经180度对应值为1
    return (lon + 180.0) / 360.0


def get_y_from_latitude(lat):
    # 将纬度大约-85.05度~85.05度之间的值归一化为1~0之间的实数，北纬85.05度对应值约为0，赤道对应值为0.5，南纬85.05度对应值约为1
    return (1 - math.log(math.tan(lat * math.pi / 180) + 1 / math.cos(lat * math.pi / 180)) / math.pi) / 2


def get_fpx_from_longitude(lon):
    # 将经度-180度~180度之间的值转换为Web墨卡托投影像素坐标系中的全图像素横坐标
    return int(const.FULL_MAP_WIDTH * (lon + 180.0) / 360.0)


def get_fpy_from_latitude(lat):
    # 将将纬度大约-85.05度~85.05度之间的值转换为Web墨卡托投影像素坐标系中的全图像素纵坐标
    return int(const.FULL_MAP_WIDTH * (1 - math.log(math.tan(lat * math.pi / 180) + 1 / math.cos(lat * math.pi / 180)) / math.pi) / 2)


def get_longitude_from_x(x):
    # Transform an x coordinate into a longitude
    x = ((x % 1.0) + 1.0) % 1.0  # Ensure x is really between 0 and 1 (to wrap longitudes)
    # Note: First %1.0 restricts range to (-1,1), then +1.0 shifts to (0,2)
    # Finally, %1.0 to give (0,1)
    return x * 360.0 - 180.0


def get_latitude_from_y(y):
    # Transform a y coordinate into a latitude
    n = math.pi * (1 - 2 * y)
    return 180 / math.pi * math.atan(0.5 * (math.exp(n) - math.exp(-n)))


def get_longitude_from_fpx(fpx):
    x = fpx / const.FULL_MAP_WIDTH
    # Transform an x coordinate into a longitude
    x = ((x % 1.0) + 1.0) % 1.0  # Ensure x is really between 0 and 1 (to wrap longitudes)
    # Note: First %1.0 restricts range to (-1,1), then +1.0 shifts to (0,2)
    # Finally, %1.0 to give (0,1)
    return x * 360.0 - 180.0


def get_latitude_from_fpy(fpy):
    y = fpy / const.FULL_MAP_WIDTH
    # Transform a y coordinate into a latitude
    n = math.pi * (1 - 2 * y)
    return 180 / math.pi * math.atan(0.5 * (math.exp(n) - math.exp(-n)))


def get_px_from_fpx(fpx, zoom):
    return fpx >> (const.MAX_ZOOM - zoom)


def get_py_from_fpy(fpy, zoom):
    return fpy >> (const.MAX_ZOOM - zoom)


def get_fpx_from_px(px, zoom):
    return px << (const.MAX_ZOOM - zoom)


def get_fpy_from_py(py, zoom):
    return py << (const.MAX_ZOOM - zoom)


def compute_radian_between(lon1, lat1, lon2, lat2):
    TO_RADIANS = math.pi / 180.0
    lon1 *= TO_RADIANS
    lat1 *= TO_RADIANS
    lon2 *= TO_RADIANS
    lat2 *= TO_RADIANS
    # Formula given by Wikipedia: Great - circle_distance as follows:
    # angle = 2 arcsin(sqrt((sin((lat2 - lat1) / 2))^^2 + cos(lat1) + cos(lat2)(sin((lon2 - lon1) / 2))^^2))
    first_sine = math.sin((lat2 - lat1) / 2.0)
    second_sine = math.sin((lon2 - lon1) / 2.0)
    term2 = math.cos(lat1) * math.cos(lat2) * second_sine * second_sine
    radian = 2 * math.asin(math.sqrt(first_sine * first_sine + term2))
    return radian


def utc2local(utc_st):
    # UTC时间转本地时间（+8:00）
    now_stamp = time.time()
    local_time = datetime.datetime.fromtimestamp(now_stamp)
    utc_time = datetime.datetime.utcfromtimestamp(now_stamp)
    offset = local_time - utc_time
    local_st = utc_st + offset
    return local_st


def local2utc(local_st):
    # 本地时间转UTC时间（-8:00）
    time_struct = time.mktime(local_st.timetuple())
    utc_st = datetime.datetime.utcfromtimestamp(time_struct)
    return utc_st


def local2utcstr(local_st):
    return local2utc(local_st).strftime('%Y-%m-%dT%H:%M:%SZ')




    

