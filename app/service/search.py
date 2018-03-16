#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from app.globals import const
from app.service import google_search
from app.service import baidu_search


def find_pos_from_name(name, api):
    result = []
    if api == const.SEARCH_API_GOOGLE:
        result = google_search.find_pos_from_name(name)
        if not result:
            result = baidu_search.find_pos_from_name(name)
    elif api == const.SEARCH_API_BAIDU:
        result = baidu_search.find_pos_from_name(name)
        if not result:
            result = google_search.find_pos_from_name(name)

    return result


def find_name_from_pos(lon, lat, api):
    result = ''
    if api == const.SEARCH_API_GOOGLE:
        result = google_search.find_name_from_pos(lon, lat)
        if not result:
            result = baidu_search.find_name_from_pos(lon, lat)
    elif api == const.SEARCH_API_BAIDU:
        result = baidu_search.find_name_from_pos(lon, lat)
        if not result:
            result = google_search.find_name_from_pos(lon, lat)

    return result


def find_drive_route(start, end, api):
    return google_search.find_drive_route(start, end)  # 百度路径搜索暂时没搞定，先用google的


