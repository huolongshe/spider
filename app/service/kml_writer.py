#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from app.globals.global_data import g
from app.model.data_folder import DataFolder
from app.model.track_line import TrackLine
from app.model.way_point import WayPoint


def write_kml(data):
    out_lines = []

    out_lines.append('<?xml version="1.0" encoding="UTF-8"?>\n')
    out_lines.append('<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">\n')

    if isinstance(data, DataFolder):
        write_document(data, out_lines)
    elif isinstance(data, TrackLine):
        write_track_line(data, out_lines)
    elif isinstance(data, WayPoint):
        write_way_point(data, out_lines)
    else:
        pass  # 其他类型节点，待补充

    out_lines.append('</kml>\n')
    return ''.join(out_lines)


def write_track_line(track_line, out_lines):
    out_lines.append('    <Placemark>\n')
    out_lines.append('        <name>%s</name>\n' % track_line.name)
    out_lines.append('        <Style>\n')
    out_lines.append('            <LineStyle>\n')
    color_str = '%02x%02x%02x%02x' % (track_line.alpha, track_line.blue, track_line.green, track_line.red)
    out_lines.append('                <color>%s</color>\n' % color_str)
    out_lines.append('                <width>%d</width>\n' % track_line.width)
    out_lines.append('            </LineStyle>\n')
    out_lines.append('        </Style>\n')
    if track_line.has_timestamp:
        write_points_with_time(track_line, out_lines)
    else:
        write_points_without_time(track_line, out_lines)
    out_lines.append('    </Placemark>\n')


def write_points_without_time(track_line, out_lines):
    out_lines.append('        <LineString>\n')
    out_lines.append('            <coordinates>\n')
    for pt in track_line.track_points:
        out_lines.append('                %.08f,%.08f,%.06f\n' % (pt.lon, pt.lat, pt.alt))
    out_lines.append('            </coordinates>\n')
    out_lines.append('        </LineString>\n')


def write_points_with_time(track_line, out_lines):
    out_lines.append('        <gx:Track>\n')
    for pt in track_line.track_points:
        out_lines.append('            <when>%s</when>\n' % pt.timestamp)
    for pt in track_line.track_points:
        out_lines.append('            <gx:coord>%.08f %.08f %.06f</gx:coord>\n' % (pt.lon, pt.lat, pt.alt))
    out_lines.append('        </gx:Track>\n')


def write_way_point(wpt, out_lines):
    out_lines.append('    <Placemark>\n')
    out_lines.append('        <name>%s</name>\n' % wpt.name)
    out_lines.append('        <Point>\n')
    out_lines.append('            <coordinates>%.08f,%.08f,%.06f</coordinates>\n'
                          % (wpt.lon, wpt.lat, wpt.alt))
    out_lines.append('        </Point>\n')
    if wpt.timestamp:
        out_lines.append('        <Timestamp>\n')
        out_lines.append('            <when>%s</when>\n' % wpt.timestamp)
        out_lines.append('        </Timestamp>\n')
    out_lines.append('    </Placemark>\n')


def write_document(doc, out_lines):
    children_list = []
    for lst in [g.folder_list, g.track_list, g.wpt_list]:
        for child in lst:
            if child.parent == doc.uuid:
                children_list.append(child)
    children_list.sort(key=lambda child: child.order_in_parent)

    out_lines.append('    <Document>\n')
    out_lines.append('        <name>%s</name>\n' % doc.name)

    for child in children_list:
        if isinstance(child, DataFolder):
            write_document(child, out_lines)
        elif isinstance(child, TrackLine):
            write_track_line(child, out_lines)
        elif isinstance(child, WayPoint):
            write_way_point(child, out_lines)

    out_lines.append('    </Document>\n')
