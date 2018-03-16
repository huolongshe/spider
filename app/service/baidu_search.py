#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import json
import requests
from urllib import parse
import hashlib
from app.service import jiupian


BAIDU_AK = b'jx6fBEGQhzCya0lwfsGC2CB9BwQnp1Rw'
BAIDU_SK = 'Zh39z1qmR3jDwntKjSFp2DIhqL4T9zcr'


def find_pos_from_name(name):
    url = get_baidu_url(name=name)

    try:
        res = requests.get(url)
    except:
        return []

    if res.status_code != 200:
        return []

    spot_json = json.loads(res.content)
    if spot_json['status'] != 0:
        return []

    hx_lon = spot_json['result']['location']['lng']
    hx_lat = spot_json['result']['location']['lat']
    lon, lat = jiupian.gcj02_to_wgs84(hx_lon, hx_lat)
    return [(name, lon, lat)]


def find_name_from_pos(lon, lat):
    url = get_baidu_url(pos=(lat, lon))

    try:
        res = requests.get(url)
    except:
        return ''

    if res.status_code != 200:
        return ''

    content = res.content.decode(encoding='utf-8')
    idx1 = content.find('{')
    idx2 = content.rfind('}')
    if idx1 >= 0 and idx2 >= 0:
        content = content[idx1:idx2 + 1]
    else:
        return ''

    place = json.loads(content)
    if place['status'] != 0:
        return ''
    return place['result']['formatted_address'] + '，' + place['result']['sematic_description']


def get_baidu_url(name=None, pos=None):
    if name:
        name_bytes = name.encode('utf-8')
        request_bytes = b'/geocoder/v2/?address=%s&output=json&ret_coordtype=gcj02ll&ak=%s' % (name_bytes, BAIDU_AK)
    elif pos:
        request_bytes = b'/geocoder/v2/?callback=renderReverse&location=%.06f,%.06f&output=json&coordtype=wgs84ll&ak=%s' % (pos[0], pos[1], BAIDU_AK)
    else:
        return ''

    # 对原始url进行转码，safe内的保留字符不转换
    request_str = parse.quote(request_bytes, safe=b"/:=&?#+!$,;'@()*[]")

    # 在最后直接追加上开发者sk
    raw_str = request_str + BAIDU_SK
    sn = hashlib.md5(parse.quote_plus(raw_str).encode('utf-8')).hexdigest()

    url = 'http://api.map.baidu.com%s&sn=%s' % (request_str, sn)
    return url
