#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import sqlite3

from app.globals import const
from app.model.data_folder import DataFolder
from app.model.track_line import TrackLine
from app.model.way_point import WayPoint
from app.model.photo import Photo


class DbManager:
    def __init__(self, data_path):
        self._db_path = os.path.join(data_path, const.DB_FILE_NAME)
        self._conn = None
        self._cursor = None
        self.open_db()
        self.create_table_folder()
        self.create_table_track_line()
        self.create_table_way_point()
        self.create_table_photo()

    def open_db(self):
        self._conn = sqlite3.connect(self._db_path)
        self._cursor = self._conn.cursor()
        
    def close_db(self):
        self._cursor.close()
        self._conn.close()

    def commit(self):
        self._conn.commit()

    def create_table_folder(self):
        sql = '''
                    CREATE TABLE IF NOT EXISTS data_folder (
                        id                INTEGER PRIMARY KEY  NOT NULL,
                        uuid              TEXT,
                        data_name         TEXT,
                        parent            TEXT,
                        order_in_parent  REAL
                    );
                    '''
        self._cursor.execute(sql)
        sql = 'CREATE UNIQUE INDEX  IF NOT EXISTS index_data_folder on data_folder(uuid);'
        self._cursor.execute(sql)
        self._conn.commit()
        
    def create_table_track_line(self):
        sql = '''
                    CREATE TABLE IF NOT EXISTS track_line (
                        id                             INTEGER   PRIMARY KEY  NOT NULL,
                        uuid                           TEXT,
                        data_name                     TEXT,
                        description                   TEXT,
                        parent                         TEXT,
                        order_in_parent               REAL,
                        track_points_str             TEXT,
                        points_list_for_draw_str    TEXT,
                        has_timestamp                 INT,
                        red                            INT,
                        green                          INT,
                        blue                           INT,
                        alpha                          INT,
                        width                          INT,
                        draw_endpoints                INT,
                        draw_line_dashed              INT,
                        draw_arrow                    INT,
                        is_visible                    INT,
                        lon_min                       REAL,
                        lon_max                       REAL,
                        lat_min                       REAL,
                        lat_max                       REAL,
                        alt_min                       REAL,
                        alt_max                       REAL,
                        fpx_min                       INT,
                        fpx_max                       INT,
                        fpy_min                       INT,
                        fpy_max                       INT,
                        distance                      REAL,
                        distance_horizon             REAL,
                        climb                         REAL,
                        descent                       REAL
                    );
                    '''
        self._cursor.execute(sql)
        sql = 'CREATE UNIQUE INDEX  IF NOT EXISTS index_track_line on track_line(uuid);'
        self._cursor.execute(sql)
        self._conn.commit()
        
    def create_table_way_point(self):
        sql = '''
                    CREATE TABLE IF NOT EXISTS way_point (
                        id                 INTEGER PRIMARY KEY  NOT NULL,
                        uuid               TEXT,
                        data_name         TEXT,
                        description       TEXT,
                        parent             TEXT,
                        order_in_parent   REAL,
                        lon                REAL,
                        lat                REAL,
                        alt                REAL,
                        timestamp         TEXT,
                        fpx                INT,
                        fpy                INT,
                        bmp_index         INT,
                        is_visible        INT
                    );
                    '''
        self._cursor.execute(sql)
        sql = 'CREATE UNIQUE INDEX  IF NOT EXISTS index_way_point on way_point(uuid);'
        self._cursor.execute(sql)
        self._conn.commit()

    def create_table_photo(self):
        sql = '''
                    CREATE TABLE IF NOT EXISTS photo (
                        id                INTEGER PRIMARY KEY  NOT NULL,
                        uuid              TEXT,
                        data_name         TEXT,
                        path              TEXT,
                        lon                REAL,
                        lat                REAL,
                        alt               REAL,
                        timestamp        TEXT,
                        fpx               INT,
                        fpy               INT,
                        img_direction     REAL,
                        photo_img         BLOB
                    );
                    '''
        self._cursor.execute(sql)
        sql = 'CREATE UNIQUE INDEX  IF NOT EXISTS index_photo on photo(uuid);'
        self._cursor.execute(sql)
        self._conn.commit()

    def add_folder(self, folder, commit=True):
        sql = '''
                    INSERT INTO data_folder
                    (uuid, data_name, parent, order_in_parent)
                    VALUES \
                    (?, ?, ?, ?)
                    '''
        values = (folder.uuid, folder.name, folder.parent, folder.order_in_parent)

        self._cursor.execute(sql, values)
        if commit:
            self._conn.commit()
        
    def add_track_line(self, track_line, commit=True):
        sql = '''
                    INSERT INTO track_line
                    (
                        uuid,
                        data_name,
                        description,
                        parent,
                        order_in_parent,
                        track_points_str,
                        points_list_for_draw_str,
                        has_timestamp,
                        red,
                        green,
                        blue,
                        alpha,
                        width,
                        draw_endpoints,
                        draw_line_dashed,
                        draw_arrow,
                        is_visible,
                        lon_min,
                        lon_max,
                        lat_min,
                        lat_max,
                        alt_min,
                        alt_max,
                        fpx_min,
                        fpx_max,
                        fpy_min,
                        fpy_max,
                        distance,
                        distance_horizon,
                        climb,
                        descent
                    )
                    VALUES \
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''
        values = (
            track_line.uuid,
            track_line.name,
            track_line.description,
            track_line.parent,
            track_line.order_in_parent,
            track_line.track_points_str,
            track_line.points_list_for_draw_str,
            1 if track_line.has_timestamp else 0,
            track_line.red,
            track_line.green,
            track_line.blue,
            track_line.alpha,
            track_line.width,
            1 if track_line.draw_endpoints else 0,
            1 if track_line.draw_line_dashed else 0,
            1 if track_line.draw_arrow else 0,
            1 if track_line.is_visible else 0,
            track_line.lon_min,
            track_line.lon_max,
            track_line.lat_min,
            track_line.lat_max,
            track_line.alt_min,
            track_line.alt_max,
            track_line.fpx_min,
            track_line.fpx_max,
            track_line.fpy_min,
            track_line.fpy_max,
            track_line.distance,
            track_line.distance_horizon,
            track_line.climb,
            track_line.descent
        )
        self._cursor.execute(sql, values)
        if commit:
            self._conn.commit()

    def add_way_point(self, wpt, commit=True):
        sql = '''
                    INSERT INTO way_point
                    (
                        uuid,
                        data_name,
                        description,
                        parent,
                        order_in_parent,
                        lon,
                        lat,
                        alt,
                        timestamp,
                        fpx,
                        fpy,
                        bmp_index,
                        is_visible
                    )
                    VALUES \
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''
        values = (
            wpt.uuid,
            wpt.name,
            wpt.description,
            wpt.parent,
            wpt.order_in_parent,
            wpt.lon,
            wpt.lat,
            wpt.alt,
            wpt.timestamp,
            wpt.fpx,
            wpt.fpy,
            wpt.bmp_index,
            1 if wpt.is_visible else 0
        )
        self._cursor.execute(sql, values)
        if commit:
            self._conn.commit()
            
    def add_photo(self, photo, commit=True):
        sql = '''
                    INSERT INTO photo
                    (
                        uuid,
                        data_name,
                        path,
                        lon,
                        lat,
                        alt,
                        timestamp,
                        fpx,
                        fpy,
                        img_direction,
                        photo_img
                    )
                    VALUES \
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''
        values = (
            photo.uuid,
            photo.name,
            photo.path,
            photo.lon,
            photo.lat,
            photo.alt,
            photo.timestamp,
            photo.fpx,
            photo.fpy,
            photo.img_direction,
            photo.bmp.ConvertToImage().GetData()
        )
        self._cursor.execute(sql, values)
        if commit:
            self._conn.commit()

    def del_folder(self, folder, commit=True):
        sql = 'DELETE FROM data_folder WHERE uuid = ?'
        self._cursor.execute(sql, (folder.uuid,))
        if commit:
            self._conn.commit()
        
    def del_track_line(self, track_line, commit=True):
        sql = 'DELETE FROM track_line WHERE uuid = ?'
        self._cursor.execute(sql, (track_line.uuid,))
        if commit:
            self._conn.commit()
        
    def del_way_point(self, wpt, commit=True):
        sql = 'DELETE FROM way_point WHERE uuid = ?'
        self._cursor.execute(sql, (wpt.uuid,))
        if commit:
            self._conn.commit()
            
    def del_photo(self, photo, commit=True):
        sql = 'DELETE FROM photo WHERE uuid = ?'
        self._cursor.execute(sql, (photo.uuid,))
        if commit:
            self._conn.commit()

    def update_parent_uuid(self, data, parent_uuid, commit=True):
        if isinstance(data, DataFolder):
            sql = 'UPDATE data_folder SET parent = ? WHERE uuid = ?'
        elif isinstance(data, TrackLine):
            sql = 'UPDATE track_line SET parent = ? WHERE uuid = ?'
        elif isinstance(data, WayPoint):
            sql = 'UPDATE way_point SET parent = ? WHERE uuid = ?'
        else:
            return

        self._cursor.execute(sql, (parent_uuid, data.uuid))
        if commit:
            self._conn.commit()
        
    def update_name(self, data, commit=True):
        if isinstance(data, DataFolder):
            sql = 'UPDATE data_folder SET data_name = ? WHERE uuid = ?'
        elif isinstance(data, TrackLine):
            sql = 'UPDATE track_line SET data_name = ? WHERE uuid = ?'
        elif isinstance(data, WayPoint):
            sql = 'UPDATE way_point SET data_name = ? WHERE uuid = ?'
        else:
            return

        self._cursor.execute(sql, (data.name, data.uuid))
        if commit:
            self._conn.commit()
            
    def update_order_in_parent(self, data, commit=True):
        if isinstance(data, DataFolder):
            sql = 'UPDATE data_folder SET order_in_parent = ? WHERE uuid = ?'
        elif isinstance(data, TrackLine):
            sql = 'UPDATE track_line SET order_in_parent = ? WHERE uuid = ?'
        elif isinstance(data, WayPoint):
            sql = 'UPDATE way_point SET order_in_parent = ? WHERE uuid = ?'
        else:
            return

        self._cursor.execute(sql, (data.order_in_parent, data.uuid))
        if commit:
            self._conn.commit()
        
    def update_visible(self, data, commit=True):
        if isinstance(data, TrackLine):
            sql = 'UPDATE track_line SET is_visible = ? WHERE uuid = ?'
        elif isinstance(data, WayPoint):
            sql = 'UPDATE way_point SET is_visible = ? WHERE uuid = ?'
        else:
            return

        self._cursor.execute(sql, (1 if data.is_visible else 0, data.uuid))
        if commit:
            self._conn.commit()

    def update_track_style(self, track_line, commit=True):
        sql = 'UPDATE track_line ' \
              'SET red = ?, green = ?, blue = ?, width= ?, draw_endpoints = ?, draw_line_dashed = ?  ' \
              'WHERE uuid = ?'
        values = (track_line.red, track_line.green, track_line.blue, track_line.width,
                  1 if track_line.draw_endpoints else 0, 1 if track_line.draw_line_dashed else 0, track_line.uuid)

        self._cursor.execute(sql, values)
        if commit:
            self._conn.commit()
        
    def update_wpt_bmp_index(self, wpt, commit=True):
        sql = 'UPDATE way_point SET bmp_index = ? WHERE uuid = ?'

        self._cursor.execute(sql, (wpt.bmp_index, wpt.uuid))
        if commit:
            self._conn.commit()

    def read_folders(self):
        sql = 'SELECT * FROM data_folder'
        records = self._cursor.execute(sql).fetchall()
        folder_list = []
        for record in records:
            folder_list.append(DataFolder(parent=record[3], name=record[2], data_uuid=record[1], order_in_parent=record[4]))
            
        return folder_list

    def read_track_lines(self):
        sql = 'SELECT * FROM track_line'
        records = self._cursor.execute(sql).fetchall()

        track_list = []
        for record in records:
            track_line = TrackLine()
            track_line.restore_from_db_record(record)
            track_list.append(track_line)

        return track_list

    def read_way_points(self):
        sql = 'SELECT * FROM way_point'
        records = self._cursor.execute(sql).fetchall()
        wpt_list = []
        for record in records:
            wpt = WayPoint()
            wpt.restore_from_db_record(record)
            wpt_list.append(wpt)
    
        return wpt_list

    def read_photos(self):
        sql = 'SELECT * FROM photo'
        records = self._cursor.execute(sql).fetchall()
        photo_list = []
        for record in records:
            photo = Photo('', db_record=record)
            photo_list.append(photo)
    
        return photo_list

