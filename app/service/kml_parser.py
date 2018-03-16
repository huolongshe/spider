#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import io
import zipfile
import xml.etree.cElementTree as ET

from app.model.data_folder import DataFolder
from app.model.track_line import TrackLine
from app.model.track_point import TrackPoint
from app.model.way_point import WayPoint
from app.service.logger import do_log


BAD_NAMES = ('未命名', 'GPS device', 'Tracks')


def parse_kmz(path, parent_uuid):
    file_dir, file_name = os.path.split(path)
    file_name = file_name[:-4]
    
    if os.path.isfile(path):
        try:
            with open(path, 'rb') as fn:
                kmz_bytes = fn.read()
        except:
            return []
    else:
        return []
    
    if kmz_bytes:
        try:
            kmz_zip = zipfile.ZipFile(io.BytesIO(kmz_bytes))
            zip_info_list = kmz_zip.infolist()
            kml_file = kmz_zip.open(zip_info_list[0])
            return parse_kml(kml_file, parent_uuid, file_name=file_name)
        except:
            do_log('解析kmz文件出错！')
            return []
    else:
        return []


def parse_kml(path, parent_uuid, file_name=''):
    try:
        tree = ET.parse(path)
    except:
        do_log('解析kml文件出错！')
        return []

    root = tree.getroot()
    tag = trim_tag(root.tag)
    if tag != 'kml':
        do_log('解析kml文件出错！')
        return []

    if not file_name:
        file_dir, file_name = os.path.split(path)
        file_name = file_name[:-4]

    results = []
    for child in root:
        tag = trim_tag(child.tag)
        if tag == 'document' or tag == 'folder':
            folder = DataFolder(parent=parent_uuid)
            son_num, folder_data = parse_kml_document(child, folder)
            if son_num == 1:  # 如果document下只有一项内容，不建该文件夹，直接将底层内容提升至上一级
                folder_data[0].parent = parent_uuid
                if folder_data[0].name in BAD_NAMES:
                    folder_data[0].name = file_name
                results += folder_data
            elif son_num > 1:
                if folder.name in BAD_NAMES:
                    folder.name = file_name
                results.append(folder)
                results += folder_data
            else:
                pass  # 如果document下无内容，则不建该文件夹
        elif tag == 'placemark':
            datatype = get_placemark_datatype(child)
            if 'track_line' == datatype:
                track_line = TrackLine(parent=parent_uuid)
                parse_track_line(track_line, placemark=child)
                if track_line.track_points:
                    results.append(track_line)
            elif 'way_point' == datatype:
                name, lon, lat, alt, timestamp_str = parse_way_point(child)
                if lon:
                    wpt = WayPoint(name, lon, lat, alt, timestamp=timestamp_str, parent=parent_uuid)
                    results.append(wpt)
            else:
                pass
    return results


def parse_kml_document(kml_document, parent_folder):
    parent_folder_data = []
    document_styles = {}
    son_num = 0

    for child in kml_document:
        tag = trim_tag(child.tag)
        if tag == 'name':
            parent_folder.name = child.text
        elif tag == 'style':
            parse_kml_document_style(child, document_styles)
        elif tag == 'placemark':
            datatype = get_placemark_datatype(child)
            if 'track_line' == datatype:
                track_line = TrackLine(parent=parent_folder.uuid)
                parse_track_line(track_line, child, style_ref=document_styles)
                if track_line.track_points:
                    parent_folder_data.append(track_line)
                    son_num += 1
            elif 'way_point' == datatype:
                name, lon, lat, alt, timestamp_str = parse_way_point(child)
                if lon:
                    wpt = WayPoint(name, lon, lat, alt, timestamp=timestamp_str, parent=parent_folder.uuid)
                    parent_folder_data.append(wpt)
                    son_num += 1
            else:
                pass
        elif tag == 'document' or tag == 'folder':
            folder = DataFolder(parent=parent_folder.uuid)
            son_of_son_num, folder_data = parse_kml_document(child, folder)
            if son_of_son_num == 1:  # 如果document下只有一项内容，不建该文件夹，直接将底层内容提升至上一级
                folder_data[0].parent = parent_folder.uuid
                parent_folder_data += folder_data
                son_num += 1
            elif son_of_son_num > 1:
                parent_folder_data.append(folder)
                parent_folder_data += folder_data
                son_num += 1
            else:
                pass  # 如果document下无内容，则不建该文件夹
    return son_num, parent_folder_data


def parse_kml_document_style(style, document_styles):
    attrib = style.attrib
    style_id = attrib.get('id')
    if style_id:
        for child in style:
            if trim_tag(child.tag) == 'linestyle':
                line_style = {}
                for sub_child in child:
                    tag = trim_tag(sub_child.tag)
                    text = sub_child.text
                    line_style[tag] = text
                if line_style:
                    document_styles[style_id] = line_style


def parse_track_line(track_line, placemark, style_ref=None):
    for child in placemark:
        tag = trim_tag(child.tag)
        if tag == 'name':
            track_line.name = child.text if child.text else '未命名'
        elif tag == 'style':
            parse_style(track_line, child)
        elif tag == 'styleurl':
            style_id = child.text
            if style_id[0] == '#':
                style_id = style_id[1:]
                style = style_ref.get(style_id)
                if style:
                    for style_key in style:
                        if style_key not in track_line.style:
                            track_line.style[style_key] = style[style_key]
        elif tag == 'linestring':
            parse_line_string(track_line, child)
        elif tag == 'track':  # etree此时解析的tag是'track'而不是'gx:track'
            parse_gx_track(track_line, child)

    track_line.init_track_style()
    track_line.compute_track_line_args()


def parse_style(track_line, style):
    for child in style:
        if trim_tag(child.tag) == 'linestyle':
            for sub_child in child:
                tag = trim_tag(sub_child.tag)
                text = sub_child.text
                track_line.style[tag] = text


def parse_line_string(track_line, line_string):
    track_line.has_timestamp = False
    for child in line_string:
        if trim_tag(child.tag) == 'coordinates':
            coordinates = child.text
            coordinate_list = coordinates.split()
            for coord_str in coordinate_list:
                coord = coord_str.split(',')
                if len(coord) < 2:
                    continue
                if len(coord) < 3:
                    coord.append(0.0)
                track_point = TrackPoint(track_line=track_line, lon=float(coord[0]), lat=float(coord[1]), alt=float(coord[2]))
                track_line.track_points.append(track_point)


def parse_gx_track(track_line, gx_track):
    track_line.has_timestamp = True
    timestamp_list = []
    coord_str_list = []

    for child in gx_track:
        tag = trim_tag(child.tag)
        if tag == 'when':
            timestamp_list.append(child.text)
        elif tag == 'coord':  # etree此时解析的tag是 'coord'而不是 'gx:coord'
            coord_str_list.append(child.text)
    num_point = min(len(timestamp_list), len(coord_str_list))
    for i in range(num_point):
        coord = coord_str_list[i].split()
        track_point = TrackPoint(track_line=track_line, lon=float(coord[0]), lat=float(coord[1]), alt=float(coord[2]),
                                 timestamp=timestamp_list[i])
        track_line.track_points.append(track_point)


def parse_way_point(placemark):
    name = '未命名'
    lon = None
    lat = None
    alt = 0.0
    timestamp_str = None
    for child in placemark:
        tag = trim_tag(child.tag)
        if tag == 'name':
            name = child.text if child.text else '未命名'
        elif tag == 'point':
            for subchild in child:
                tag = trim_tag(subchild.tag)
                if tag == 'coordinates':
                    wpt = subchild.text.split(',')
                    if len(wpt) > 1:
                        lon = float(wpt[0])
                        lat = float(wpt[1])
                        if len(wpt) > 2:
                            alt = float(wpt[2])
        elif tag == 'timestamp':
            for subchild in child:
                tag = trim_tag(subchild.tag)
                if tag == 'when':
                    timestamp_str = subchild.text.strip(' ')
    return name, lon, lat, alt, timestamp_str


def get_placemark_datatype(placemark):
    datatype = None
    for child in placemark:
        tag = trim_tag(child.tag)
        if tag == 'linestring' or tag == 'track':
            datatype = 'track_line'
            break
        elif tag == 'point':
            datatype = 'way_point'
            break
        else:
            pass
    return datatype


def trim_tag(tag):
    if tag[0] == '{':
        index = tag.find('}')
        return tag[index + 1:].lower()
    else:
        return tag.lower()
