#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import json
import requests


def find_drive_route(start, end):

    url = 'http://api.tianditu.gov.cn/drive?postStr={"orig":"%.06f,%.06f","dest":"%.06f,%.06f","style":"1"}&type=search&tk=c8e0b9ae169804fa3d0dbdcc04017804' % (start[0], start[1], end[0], end[1])

    try:
        res = requests.get(url)
    except:
        return []
    
    if res.status_code != 200:
        return []

    text = res.text
    route = []
    while text.find('<streetLatLon>') >= 0:
        points = text[text.find('<streetLatLon>') + 14: text.find('</streetLatLon>') - 1].split(';')
        for point in points:
            tmp = point.split(',')
            route.append([float(tmp[0]), float(tmp[1])])
        text = text[text.find('</streetLatLon>') + 15:]

    if len(route) > 0:
        return [route]

    return []


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

