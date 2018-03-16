#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import json
import requests
from app.service import jiupian


def find_pos_from_name(name):
    url = 'http://ditu.google.cn/maps/api/geocode/json?address=%s&language=zh-CN&sensor=true' % name

    try:
        res = requests.get(url)
    except:
        return []

    if res.status_code != 200:
        return []

    wpt_json = json.loads(res.content)
    if wpt_json['status'] != 'OK':
        return []

    results = []
    names = []
    for i in range(len(wpt_json['results'])):
        hx_lon = wpt_json['results'][0]['geometry']['location']['lng']
        hx_lat = wpt_json['results'][0]['geometry']['location']['lat']
        lon, lat = jiupian.gcj02_to_wgs84(hx_lon, hx_lat)
        new_name = wpt_json['results'][0]['formatted_address']
        # new_name = new_name[:new_name.find(' ')]  # 删除第一个空格后面的字符
        new_name = new_name.lstrip('中国')
        new_name = name + '.' + new_name
        if new_name not in names:
            names.append(new_name)
            results.append((new_name, lon, lat))
    return results


def find_name_from_pos(lon, lat):
    lon_gcj, lat_gcj = jiupian.wgs84_to_gcj02(lon, lat)
    url = 'http://ditu.google.cn/maps/api/geocode/json' \
          '?latlng=%.06f,%.06f&language=zh-CN&sensor=true' % (lat_gcj, lon_gcj)

    try:
        res = requests.get(url)
    except:
        return ''

    if res.status_code != 200:
        return ''

    place = json.loads(res.content)
    if place['status'] != 'OK':
        return ''

    name = place['results'][0]['formatted_address']
    # name = name[:name.find(' ')]  # 删除第一个空格后面的字符
    name = name.lstrip('中国')
    return name


def find_drive_route(start, end):
    start_gcj = jiupian.wgs84_to_gcj02(start[0], start[1])
    end_gcj = jiupian.wgs84_to_gcj02(end[0], end[1])
    url = 'http://ditu.google.cn/maps/api/directions/json?origin=%.06f,%.06f&destination=%.06f,%.06f' \
          '&mode=driving&alternatives=true&language=zh-CN&sensor=true' \
          % (start_gcj[1], start_gcj[0], end_gcj[1], end_gcj[0])
    
    try:
        res = requests.get(url)
    except:
        return []
    
    if res.status_code != 200:
        return []
    
    route_json = json.loads(res.content)
    if route_json['status'] != 'OK':
        return []
    
    results = []
    routes = route_json['routes']
    for route in routes:
        route_points = []
        legs = route['legs']
        for leg in legs:
            steps = leg['steps']
            for step in steps:
                points_encoded = step['polyline']['points']
                points = decode_points(points_encoded)
                route_points += points
        for point in route_points:
            point[0], point[1] = jiupian.gcj02_to_wgs84(point[0], point[1])
        results.append(route_points)
        
    return results


def decode_points(encoded):
    points = []
    index = 0
    length = len(encoded)
    lon_e5 = 0
    lat_e5 = 0
    while index < length:
        shift = 0
        result = 0
        while 1:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break

        dlat = ~(result >> 1) if result & 1 else result >> 1
        lat_e5 += dlat

        shift = 0
        result = 0
        while 1:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break

        dlon = ~(result >> 1) if result & 1 else result >> 1
        lon_e5 += dlon

        lon = float(lon_e5) / 100000.0
        lat = float(lat_e5) / 100000.0
        points.append([lon, lat])

    return points

