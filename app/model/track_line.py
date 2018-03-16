#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import math
import uuid
import datetime

from app.globals import const
from app.model.track_point import TrackPoint
from app.service import transform


class TrackLine:
    def __init__(self, parent='', name=''):
        self.tree_node = None
        
        self.uuid = uuid.uuid1().__str__()
        self.name = name
        self.description = ''
        self.parent = parent  # 父亲节点的uuid
        self.order_in_parent = -1

        self.track_points = []  # 不存入数据库
        self.track_points_str = ''
        self.points_list_for_draw = []  # 不存入数据库
        self.points_list_for_draw_str = ''
        
        self.has_timestamp = True
        
        # 轨迹显示风格参数
        self.red = 255
        self.green = 0
        self.blue = 0
        self.alpha = 255
        self.width = 2
        self.draw_endpoints = True
        self.draw_line_dashed = False
        self.draw_arrow = False
        self.is_visible = True  # 在TrackTree中是否可见

        # 轨迹统计数据，存入数据库
        self.lon_min = 0
        self.lon_max = 0
        self.lat_min = 0
        self.lat_max = 0
        self.alt_min = 0
        self.alt_max = 0
        self.fpx_min = 0
        self.fpx_max = 0
        self.fpy_min = 0
        self.fpy_max = 0
        self.distance = 0
        self.distance_horizon = 0
        self.climb = 0
        self.descent = 0

        # 时间相关轨迹统计数据，当在需要显示该轨迹统计数据时再计算，不存入数据库
        # （因轨迹点根据时间戳字符串计算时间对象耗时较长）
        self.time_begin_str = ''
        self.time_end_str = ''
        self.duration_str = ''
        
        self.point_num = 0
        
        # 轨迹编辑状态参数，不存入数据库
        self.is_checked = False  # 在TrackEdit中是否选中
        self.selected_point = None
        self.sel_point_num = 0
        self.sel_start_idx = 0
        self.sel_end_idx = -1
        self.sel_alt_min = 0
        self.sel_alt_max = 0
        self.sel_distance = 0
        self.sel_distance_horizon = 0
        self.sel_climb = 0
        self.sel_descent = 0
        self.sel_time_begin_str = ''
        self.sel_time_end_str = ''
        self.sel_duration_str = ''
        self.sel_point_time_str = ''
        
        # 绘图或其他辅助参数，不存入数据库
        self.style = {}
        self.screen_coords = []
        self.restored_from_db = False
        
    def restore_from_db_record(self, record):
        self.uuid = record[1]
        self.name = record[2]
        self.description = record[3]
        self.parent = record[4]
        self.order_in_parent = record[5]
        self.track_points_str = record[6]
        self.restore_track_points_from_str()
        self.points_list_for_draw_str = record[7]
        self.restore_points_list_for_draw_from_str()
        self.has_timestamp = True if record[8] else False
        self.red = record[9]
        self.green = record[10]
        self.blue = record[11]
        self.alpha = record[12]
        self.width = record[13]
        self.draw_endpoints = True if record[14] else False
        self.draw_line_dashed = True if record[15] else False
        self.draw_arrow = True if record[16] else False
        self.is_visible = True if record[17] else False
        self.lon_min = record[18]
        self.lon_max = record[19]
        self.lat_min = record[20]
        self.lat_max = record[21]
        self.alt_min = record[22]
        self.alt_max = record[23]
        self.fpx_min = record[24]
        self.fpx_max = record[25]
        self.fpy_min = record[26]
        self.fpy_max = record[27]
        self.distance = record[28]
        self.distance_horizon = record[29]
        self.climb = record[30]
        self.descent = record[31]

        #  以下不存于数据库，但可能随时用到，所以数据恢复后立即计算
        self.point_num = len(self.track_points)
        self.sel_end_idx = self.point_num - 1
        
        self.restored_from_db = True

    def load_from_points(self, points):
        # self.has_timestamp = False
        timestamp_utc_str = transform.local2utcstr(datetime.datetime.now())
        for point in points:
            self.track_points.append(TrackPoint(self, point[0], point[1], timestamp=timestamp_utc_str))  # 所有轨迹点设一个统一时间
        self.init_track_style()
        self.compute_track_line_args()

    def set_track_style(self, red, green, blue, width, draw_endpoints, dashed):
        self.red = red
        self.green = green
        self.blue = blue
        self.width = width
        self.draw_endpoints = draw_endpoints
        self.draw_line_dashed = dashed

    def init_track_style(self):
        if 'color' not in self.style:
            self.style['color'] = const.DEFAULT_LINE_COLOR
        if 'width' not in self.style:
            self.style['width'] = const.DEFAULT_LINE_WIDTH
        self.red = int(self.style['color'][6:8], 16)
        self.green = int(self.style['color'][4:6], 16)
        self.blue = int(self.style['color'][2:4], 16)
        self.alpha = int(self.style['color'][0:2], 16)
        self.width = int(self.style['width'])

    def compute_time_args_after_restore(self):
        if self.restored_from_db:
            for point in self.track_points:
                point.set_timestamp_from_str()
            if self.has_timestamp:
                self.compute_time_args()
            self.restored_from_db = False

    def compute_track_line_args(self):
        lon_list = [point.lon for point in self.track_points]
        lat_list = [point.lat for point in self.track_points]
        alt_list = [point.alt for point in self.track_points]
        fpx_list = [point.fpx for point in self.track_points]
        fpy_list = [point.fpy for point in self.track_points]
        self.lon_min = min(lon_list)
        self.lon_max = max(lon_list)
        self.lat_min = min(lat_list)
        self.lat_max = max(lat_list)
        self.alt_min = min(alt_list)
        self.alt_max = max(alt_list)
        self.fpx_min = min(fpx_list)
        self.fpx_max = max(fpx_list)
        self.fpy_min = min(fpy_list)
        self.fpy_max = max(fpy_list)

        self.point_num = len(self.track_points)
        self.sel_end_idx = self.point_num - 1
        self.distance, self.distance_horizon = self.compute_distance(0, self.point_num - 1)
        self.climb, self.descent = self.compute_climb_and_descent(0, self.point_num - 1)
        if self.has_timestamp:
            self.compute_time_args()
            
        self.compute_points_list_for_draw()
        self.gen_points_list_for_draw_str()
        self.gen_track_points_str()

    def compute_distance_horizon(self, start_idx, end_idx):  # 包含end_idx
        if (end_idx - start_idx) < 1:
            return
        distance_radian = 0.0
        lon1 = self.track_points[start_idx].lon
        lat1 = self.track_points[start_idx].lat
        for i in range(start_idx+1, end_idx+1):
            lon2 = self.track_points[i].lon
            lat2 = self.track_points[i].lat
            delta_radian = transform.compute_radian_between(lon1, lat1, lon2, lat2)
            distance_radian += delta_radian
            lon1 = lon2
            lat1 = lat2
        distance_km = distance_radian * const.EARTH_RADIUS_KM
        return distance_km

    def compute_distance_with_slope(self, start_idx, end_idx):  # 包含end_idx
        if (end_idx - start_idx) < 1:
            return 0
        distance = 0.0
        lon1 = self.track_points[start_idx].lon
        lat1 = self.track_points[start_idx].lat
        alt1 = self.track_points[start_idx].alt
        for i in range(start_idx + 1, end_idx + 1):
            lon2 = self.track_points[i].lon
            lat2 = self.track_points[i].lat
            alt2 = self.track_points[i].alt
            delta_radian = transform.compute_radian_between(lon1, lat1, lon2, lat2)
            delta_km = delta_radian * const.EARTH_RADIUS_KM
            delta_vertical = abs(alt2 - alt1) / 1000.0
            delta = math.pow(delta_km * delta_km + delta_vertical * delta_vertical, 0.5)
            
            distance += delta
            lon1 = lon2
            lat1 = lat2
            alt1 = alt2
        return distance

    def compute_distance(self, start_idx, end_idx):  # 包含end_idx
        if (end_idx - start_idx) < 1:
            return 0, 0
        distance_horizon = 0.0
        distance_with_slope = 0.0
        lon1 = self.track_points[start_idx].lon
        lat1 = self.track_points[start_idx].lat
        alt1 = self.track_points[start_idx].alt
        for i in range(start_idx + 1, end_idx + 1):
            lon2 = self.track_points[i].lon
            lat2 = self.track_points[i].lat
            alt2 = self.track_points[i].alt
            delta_radian = transform.compute_radian_between(lon1, lat1, lon2, lat2)
            delta_km = delta_radian * const.EARTH_RADIUS_KM
            delta_vertical = abs(alt2 - alt1) / 1000.0
            delta_with_slope = math.pow(delta_km * delta_km + delta_vertical * delta_vertical, 0.5)
            distance_horizon += delta_km
            distance_with_slope += delta_with_slope
            lon1 = lon2
            lat1 = lat2
            alt1 = alt2
        return distance_with_slope, distance_horizon

    def compute_climb_and_descent(self, start_idx, end_idx):  # 包含end_idx
        if (end_idx - start_idx) < 1:
            return 0, 0
        climb = 0.0
        descent = 0.0
        got_pre_minimum = False
        got_pre_maximum = False
        pre_extreme = 0.0
        alt_pre = self.track_points[start_idx].alt
        for i in range(start_idx + 1, end_idx + 1):
            alt_now = self.track_points[i].alt
            locally_up = alt_now > alt_pre
            overall_up = got_pre_minimum and alt_pre > pre_extreme
            overall_dn = got_pre_maximum and alt_pre < pre_extreme
            more_than_wiggle = abs(alt_now - alt_pre) > const.ALT_WIGGLE_LIMIT

            if not got_pre_minimum and not got_pre_maximum:
                if more_than_wiggle:
                    if locally_up:
                        got_pre_minimum = True
                    else:
                        got_pre_maximum = True
                    pre_extreme = alt_pre
                    alt_pre = alt_now
            elif overall_up:
                if locally_up:
                    alt_pre = alt_now
                elif more_than_wiggle:
                    climb += (alt_pre - pre_extreme)
                    pre_extreme = alt_pre
                    got_pre_minimum = False
                    got_pre_maximum = True
                    alt_pre = alt_now
            elif overall_dn:
                if locally_up:
                    if more_than_wiggle:
                        descent += (pre_extreme - alt_pre)
                        pre_extreme = alt_pre
                        got_pre_minimum = True
                        got_pre_maximum = False
                        alt_pre = alt_now
                    else:
                        pass
                else:
                    alt_pre = alt_now
        # 最后一段
        if got_pre_minimum and alt_pre > pre_extreme:
            climb += (alt_pre - pre_extreme)
        if got_pre_maximum and alt_pre < pre_extreme:
            descent += (pre_extreme - alt_pre)

        return int(climb), int(descent)

    def compute_time_args(self):
        time_begin = self.track_points[0].timestamp_local
        time_begin_tuple = time_begin.timetuple()
        self.time_begin_str = '%04d-%02d-%02d %02d:%02d:%02d' % (time_begin_tuple.tm_year, time_begin_tuple.tm_mon,
                                                            time_begin_tuple.tm_mday, time_begin_tuple.tm_hour,
                                                            time_begin_tuple.tm_min,time_begin_tuple.tm_sec,)
        time_end = self.track_points[-1].timestamp_local
        time_end_tuple = time_end.timetuple()
        self.time_end_str = '%04d-%02d-%02d %02d:%02d:%02d' % (time_end_tuple.tm_year, time_end_tuple.tm_mon,
                                                            time_end_tuple.tm_mday, time_end_tuple.tm_hour,
                                                            time_end_tuple.tm_min, time_end_tuple.tm_sec,)
        
        duration = time_end - time_begin
        dur_days = duration.days
        dur_seconds = duration.seconds
        dur_hours = dur_seconds // 3600
        dur_minutes = (dur_seconds % 3600) // 60
        dur_secs = (dur_seconds % 3600) % 60
        str_day = ('%d天' % dur_days) if dur_days else ''
        self.duration_str = '%s%02d:%02d:%02d' % (str_day, dur_hours, dur_minutes, dur_secs)
            
    def compute_selected_segment_args(self):
        start_idx = self.sel_start_idx
        end_idx = self.sel_end_idx
        self.sel_point_num = end_idx - start_idx + 1
        alt_list = [point.alt for point in self.track_points[start_idx:end_idx + 1]]

        self.sel_alt_min = min(alt_list)
        self.sel_alt_max = max(alt_list)

        self.sel_distance, self.sel_distance_horizon = self.compute_distance(start_idx, end_idx)
        self.sel_climb, self.sel_descent = self.compute_climb_and_descent(start_idx, end_idx)

        if self.has_timestamp:
            self.compute_sel_time_args()

    def compute_sel_time_args(self):
        time_begin = self.track_points[self.sel_start_idx].timestamp_local
        time_begin_tuple = time_begin.timetuple()
        self.sel_time_begin_str = '%04d-%02d-%02d %02d:%02d:%02d' % (time_begin_tuple.tm_year, time_begin_tuple.tm_mon,
                                                             time_begin_tuple.tm_mday, time_begin_tuple.tm_hour,
                                                             time_begin_tuple.tm_min, time_begin_tuple.tm_sec,)
        time_end = self.track_points[self.sel_end_idx].timestamp_local
        time_end_tuple = time_end.timetuple()
        self.sel_time_end_str = '%04d-%02d-%02d %02d:%02d:%02d' % (time_end_tuple.tm_year, time_end_tuple.tm_mon,
                                                           time_end_tuple.tm_mday, time_end_tuple.tm_hour,
                                                           time_end_tuple.tm_min, time_end_tuple.tm_sec,)
    
        duration = time_end - time_begin
        dur_days = duration.days
        dur_seconds = duration.seconds
        dur_hours = dur_seconds // 3600
        dur_minutes = (dur_seconds % 3600) // 60
        dur_secs = (dur_seconds % 3600) % 60
        str_day = ('%d天' % dur_days) if dur_days else ''
        self.sel_duration_str = '%s%02d:%02d:%02d' % (str_day, dur_hours, dur_minutes, dur_secs)

        if self.selected_point:
            time_tuple = self.selected_point.timestamp_local.timetuple()
            self.sel_point_time_str = '%04d-%02d-%02d %02d:%02d:%02d' % (time_tuple.tm_year, time_tuple.tm_mon,
                                                                          time_tuple.tm_mday, time_tuple.tm_hour,
                                                                          time_tuple.tm_min, time_tuple.tm_sec,)
            
    def compute_points_list_for_draw(self):
        if self.point_num < 1:
            return
        
        self.points_list_for_draw = [None] * (const.MAX_ZOOM + 1)  # 不同zoom级别(0-MAX_ZOOM)下对应的需要在屏幕上画点/线的轨迹点列表
        for zoom in range(0, (const.MAX_ZOOM + 1)):
            self.points_list_for_draw[zoom] = []
            if zoom == 0:
                continue  # 本应用中用不到zoom 0，故跳过；后面将利用zoom 0缓存一些别的信息

            self.points_list_for_draw[zoom].append(0)

            pre_px = transform.get_px_from_fpx(self.track_points[0].fpx, zoom)
            pre_py = transform.get_py_from_fpy(self.track_points[0].fpy, zoom)
            i = 0
            for point in self.track_points[1:-1]:
                i += 1
                px = transform.get_px_from_fpx(point.fpx, zoom)
                py = transform.get_py_from_fpy(point.fpy, zoom)

                if abs(px - pre_px) > 5 or abs(py - pre_py) > 5:  # 去除临近坐标点，只保留第一个
                    self.points_list_for_draw[zoom].append(i)
                    pre_px = px
                    pre_py = py

            self.points_list_for_draw[zoom].append(len(self.track_points) - 1)

            self.compute_points_list_for_thumbnail()

    def compute_points_list_for_thumbnail(self):
        fpx_range = self.fpx_max - self.fpx_min + 1
        fpy_range = self.fpy_max - self.fpy_min + 1

        if fpx_range > fpy_range:
            fpx_base = self.fpx_min
            ratio = fpx_range // 16
            rem = fpx_range % 16
            if rem > 0:
                ratio += 1
                fpx_range += (16 - rem)
                fpx_base -= (16 - rem) // 2
            fpy_base = self.fpy_min - (fpx_range - fpy_range) // 2
        else:
            fpy_base = self.fpy_min
            ratio = fpy_range // 16
            rem = fpy_range % 16
            if rem > 0:
                ratio += 1
                fpy_range += (16 - rem)
                fpy_base -= (16 - rem) // 2
            fpx_base = self.fpx_min - (fpy_range - fpx_range) // 2

        pre_px = (self.track_points[0].fpx - fpx_base) // ratio
        pre_py = (self.track_points[0].fpy - fpy_base) // ratio
        self.points_list_for_draw[0].append((pre_px, pre_py))
        i = 0
        for point in self.track_points[1:-1]:  # 利用self.points_list_for_draw[0]来保存缩略图轨迹点
            i += 1
            px = (point.fpx - fpx_base) // ratio
            py = (point.fpy - fpy_base) // ratio
            if px != pre_px or py != pre_py:
                self.points_list_for_draw[0].append((px, py))
                pre_px = px
                pre_py = py

    def gen_track_points_str(self):
        track_points_str_list = []
        for point in self.track_points:
            track_points_str_list.append('%.8f,%.8f,%.6f,%s,%d,%d' % (point.lon, point.lat, point.alt, point.timestamp, point.fpx, point.fpy))

        self.track_points_str = ';'.join(track_points_str_list)
        
    def restore_track_points_from_str(self):
        self.track_points = []
        track_points_str_list = self.track_points_str.split(';')
        for pt_str in track_points_str_list:
            pt = pt_str.split(',')
            point = TrackPoint(self, float(pt[0]), float(pt[1]), float(pt[2]), pt[3], int(pt[4]), int(pt[5]), restore_from_db=True)
            self.track_points.append(point)
            
    def gen_points_list_for_draw_str(self):
        str_list = []
        thumbnail_point_list = []
        for (px, py) in self.points_list_for_draw[0]:
            thumbnail_point_list.append('%d.%d' % (px, py))
        str_list.append(','.join(thumbnail_point_list))

        for zoom in range(1, (const.MAX_ZOOM + 1)):
            index_list = []
            for i in self.points_list_for_draw[zoom]:
                index_list.append('%d' % i)

            str_list.append(','.join(index_list))

        self.points_list_for_draw_str = ';'.join(str_list)
        
    def restore_points_list_for_draw_from_str(self):
        self.points_list_for_draw = []
        points_lists = self.points_list_for_draw_str.split(';')

        points_list_str = points_lists[0]
        list_str = points_list_str.split(',')
        point_list = []
        for point_str in list_str:
            point = point_str.split('.')
            point[0] = int(point[0])
            point[1] = int(point[1])
            point_list.append(tuple(point))
        self.points_list_for_draw.append(point_list)

        for points_list_str in points_lists[1:]:
            list_str = points_list_str.split(',')
            list_int = [int(i) for i in list_str]
            self.points_list_for_draw.append(list_int)

