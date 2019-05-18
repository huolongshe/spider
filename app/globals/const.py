#!/usr/bin/env python
# -*- coding: UTF-8 -*-


APP_NAME = 'Spider户外轨迹编辑器'
APP_VERSION = 'v2.0.7'

DB_FILE_NAME = 'data.db'
CFG_FILE_NAME = 'last.yml'
#WILDCARD = 'KML files (*.kml)|*.kml|GPX files (*.gpx)|*.gpx'
WILDCARD = '轨迹文件 (*.kml;*.gpx;*.kmz)|*.kml;*.gpx;*.kmz'
WILDCARD_KML = 'KML文件 (*.kml)|*.kml'

EARTH_RADIUS_KM = 6372.795
ALT_WIGGLE_LIMIT = 8.0

MAP_TILE_SIZE = 256  # Width and height of each tile of map
MIN_ZOOM = 1
MAX_ZOOM = 19  # Maximum zoom level
FULL_MAP_WIDTH = MAP_TILE_SIZE << MAX_ZOOM
PAN_THRESHOLD = 10

DOWNLOAD_TIMEOUT = 1  # 下载瓦片时的超时等待时间，单位为秒

DEFAULT_LINE_WIDTH = '2'
DEFAULT_LINE_COLOR = 'ffff0000'  # 采用KML格式，顺序为：透明度，蓝，绿，红。wxpython中正好与此相反。
SELECTED_LINE_BG_COLOR_RED = 255
SELECTED_LINE_BG_COLOR_GREEN = 105
SELECTED_LINE_BG_COLOR_BLUE = 87
SELECTED_LINE_BG_COLOR_ALPHA = 155

REDRAW_MAP = 1  # 在mdc1中重画地图，备份至mdc2，在mdc1中重画轨迹，从mdc1中拷贝地图和轨迹镜像至dc（屏幕）
REDRAW_TRACK = 2  # 从mdc2中拷贝地图至mdc1，在mdc1中重画轨迹，从mdc1中拷贝地图和轨迹镜像至dc（屏幕）
REDRAW_COPY = 3  # 从mdc1中拷贝地图和轨迹镜像至dc（屏幕）
REDRAW_NONE = 4  # 不做地图刷新

WPT_BMP_INDEX = 41

SEARCH_API_GOOGLE = 0
SEARCH_API_BAIDU = 1

