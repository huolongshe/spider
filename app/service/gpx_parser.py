#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import xml.etree.cElementTree as ET

from app.model.data_folder import DataFolder
from app.model.track_line import TrackLine
from app.model.track_point import TrackPoint
from app.model.way_point import WayPoint
from app.service.logger import do_log


def parse_gpx(path, parent_uuid):
    try:
        tree = ET.parse(path)
    except:
        do_log('解析gpx文件出错！')
        return []
    
    root = tree.getroot()
    tag = trim_tag(root.tag)
    if tag != 'gpx':
        do_log('解析gpx文件出错！')
        return []
    
    file_dir, file_name = os.path.split(path)
    file_name = file_name[:-4]
    folder = DataFolder(parent=parent_uuid, name=file_name)
    folder_data = []
    wpt_folder = DataFolder(parent=folder.uuid, name='路点')
    wpt_data = []
    for child in root:
        tag = trim_tag(child.tag)
        if tag == 'name':
            folder.name = child.text
        elif tag == 'metadata':
            for sub_child in child:
                sub_tag = trim_tag(sub_child.tag)
                if sub_tag == 'name':
                    folder.name = sub_child.text
        elif tag == 'wpt':
            name = '未命名'
            lon = float(child.attrib['lon'])
            lat = float(child.attrib['lat'])
            alt = 0.0
            timestamp_str = None
            for sub_child in child:
                tag1 = trim_tag(sub_child.tag)
                if tag1 == 'name':
                    name = sub_child.text
                elif tag1 == 'ele':
                    alt = float(sub_child.text)
                elif tag1 == 'time':
                    timestamp_str = sub_child.text
            wpt = WayPoint(name, lon, lat, alt, timestamp=timestamp_str, parent=wpt_folder.uuid)
            wpt_data.append(wpt)
        elif tag == 'trk':
            name = file_name
            for sub_child in child:
                sub_tag = trim_tag(sub_child.tag)
                if sub_tag == 'name':
                    name = sub_child.text
                elif sub_tag == 'trkseg':
                    track_line = TrackLine(parent=folder.uuid)
                    parse_trkseg(track_line, trkseg=sub_child, name=name)
                    if track_line.track_points:
                        folder_data.append(track_line)
                        
    if not folder_data and not wpt_data:
        return []  # 文件夹内容为空，不新建文件夹
    
    if wpt_data and not folder_data:
        wpt_folder.parent = parent_uuid
        wpt_folder.name = file_name
        return [wpt_folder] + wpt_data
    
    if folder_data and not wpt_data:
        if len(folder_data) == 1:
            folder_data[0].parent = parent_uuid
            return folder_data
        else:
            return [folder] + folder_data

    if len(wpt_data) == 1:
        wpt_data[0].parent = folder.uuid
        return [folder] + wpt_data + folder_data

    return [folder] + [wpt_folder] + wpt_data + folder_data


def parse_trkseg(track_line, trkseg, name):
    track_line.has_timestamp = False
    track_line.name = name
    for trkpt in trkseg:
        tag = trim_tag(trkpt.tag)
        if tag == 'trkpt':
            lon = trkpt.attrib['lon']
            lat = trkpt.attrib['lat']
            alt = '0'
            timestamp = None
            for child in trkpt:
                tag1 = trim_tag(child.tag)
                if tag1 == 'ele':
                    alt = child.text
                elif tag1 == 'time':
                    timestamp = child.text
                    track_line.has_timestamp = True
            track_point = TrackPoint(track_line=track_line, lon=float(lon), lat=float(lat), alt=float(alt), timestamp=timestamp)
            track_line.track_points.append(track_point)

    track_line.init_track_style()
    track_line.compute_track_line_args()


def trim_tag(tag):
    if tag[0] == '{':
        index = tag.find('}')
        return tag[index + 1:].lower()
    else:
        return tag.lower()
