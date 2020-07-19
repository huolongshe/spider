#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import yaml

from app.globals import const
from app.resource import map_cfg
from app.resource import app_icons
from app.resource import pin_icons  # 必须存在，在eval的字符串中被引用，所以是灰的
from app.model.map_source import MapSource
from app.model.data_folder import DataFolder
from app.model.track_line import TrackLine
from app.model.way_point import WayPoint
from app.service.srtm_mgr import SrtmManager
from app.service.tile_mgr import TileManager
from app.service.db_mgr import DbManager


class GlobalData:
    def __init__(self):
        self.app_path = os.getcwd()  # 本程序启动时所在目录
        self.data_path = os.path.join(self.app_path, '.cache')  # 本程序数据目录，配置文件、数据缓存文件等保存在此目录
        if not os.path.exists(self.data_path):
            os.mkdir(self.data_path)
        self.cfg_path = os.path.join(self.data_path, const.CFG_FILE_NAME)

        self.tile_transparent_bmp = None
        self.tile_blank_bmp = None
        self.pin_bmps = None

        # 单实例缓存区
        self.db_mgr = None
        self.tile_mgr = None
        self.srtm_mgr = None
        self.undo_list = []

        # 配置数据
        self.search_api = const.SEARCH_API_GOOGLE
        self.default_wpt_bmp_index = const.WPT_BMP_INDEX
        self.srtm_url_index = 0
        self.init_cfg = self.read_cfg(self.cfg_path)
        if self.init_cfg:
            if os.path.exists(self.init_cfg['path']):
                os.chdir(self.init_cfg['path'])
            self.default_wpt_bmp_index = self.init_cfg['bmp_index']
            self.srtm_url_index = self.init_cfg['srtm']
            if 'search_api' in self.init_cfg:
                self.search_api = self.init_cfg['search_api']

        # 全局用户数据
        self.data_root = DataFolder(parent='root_of_root', name='用户数据')
        self.data_root.uuid = 'data_root_uuid'
        self.folder_list = [self.data_root]
        self.track_list = []
        self.wpt_list = []
        self.wpt_list_deleted = []
        self.photo_list = []

        self.edit_track_list = []
        self.map_list_main = []
        self.map_list_trans = []
        self.init_map_list()

        # views
        self.frame = None
        self.map_canvas = None
        self.track_tree = None
        self.track_edit = None
        self.track_chart = None
        self.track_details = None
        self.logger = None

        # 状态控制布尔变量
        self.in_editing = False
        self.hide_map = False
        self.full_screen = False
        self.downloading_map = False  # 进入离线地图下载状态，点击左键开始拖拽并选择下载区域，松开后弹出下载对话框

    def load_global_data(self, frame):
        self.tile_transparent_bmp = app_icons.tile_transparent.GetBitmap()
        self.tile_blank_bmp = app_icons.tile_blank.GetBitmap()
        self.pin_bmps = [None] * 100
        for i in range(100):
            self.pin_bmps[i] = eval('pin_icons.pin%02d' % i).GetBitmap()

        self.db_mgr = DbManager(self.data_path)
        self.tile_mgr = TileManager(self.data_path, self.tile_transparent_bmp)
        self.srtm_mgr = SrtmManager(self.data_path)
        self.frame = frame

    def read_cfg(self, path):
        self.init_cfg = None
        if os.path.isfile(self.cfg_path):
            try:
                with open(self.cfg_path, 'r') as fn:
                    cfg = yaml.load(fn, Loader=yaml.FullLoader)
                if cfg and isinstance(cfg, dict) \
                        and 'path' in cfg \
                        and 'bmp_index' in cfg \
                        and 'srtm' in cfg \
                        and 'pos' in cfg \
                        and 'map' in cfg:
                    self.init_cfg = cfg
                else:
                    os.remove(self.cfg_path)
            except:
                os.remove(self.cfg_path)
        return self.init_cfg

    def write_cfg(self):
        self.init_cfg = dict(path=os.getcwd(),
                             search_api=self.search_api,
                             bmp_index=self.default_wpt_bmp_index,
                             srtm=self.srtm_url_index,
                             pos=dict(zoom=self.map_canvas._zoom,
                                      fpx=self.map_canvas._centre_fpx,
                                      fpy=self.map_canvas._centre_fpy),
                             map=dict(main_sel=0, trans_ord=[], trans_sel=[]))
        for source in self.map_list_main:
            if source.is_visible:
                self.init_cfg['map']['main_sel'] = self.map_list_main.index(source)
                break
        trans_name_list = [source['name'] for source in map_cfg.transparent_map_list]
        for source in self.map_list_trans:
            self.init_cfg['map']['trans_ord'].append(trans_name_list.index(source.name))
            self.init_cfg['map']['trans_sel'].append(1 if source.is_visible else 0)

        with open(self.cfg_path, 'w') as fn:
            yaml.dump(self.init_cfg, fn, default_flow_style=False, allow_unicode=True, encoding='utf-8')

    def init_map_list(self):
        if self.init_cfg and len(map_cfg.main_map_list) > self.init_cfg['map']['main_sel']\
                and len(map_cfg.transparent_map_list) == len(self.init_cfg['map']['trans_ord']):
            i = 0
            for map in map_cfg.main_map_list:
                visible = (self.init_cfg['map']['main_sel'] == i)  # 利用配置文件信息配置地图源是否显示
                map_source = MapSource(map, visible=visible)
                self.map_list_main.append(map_source)
                i += 1
            i = 0
            for ord in self.init_cfg['map']['trans_ord']:  # 利用配置文件信息配置透明层地图源显示顺序
                visible = self.init_cfg['map']['trans_sel'][i]  # 利用配置文件信息配置地图源是否显示
                map_source = MapSource(map_cfg.transparent_map_list[ord], visible=visible)
                self.map_list_trans.append(map_source)
                i += 1
        else:
            i = 0
            for map in map_cfg.main_map_list:
                visible = True if i == 0 else False
                map_source = MapSource(map, visible=visible)
                self.map_list_main.append(map_source)
                i += 1
            for map in map_cfg.transparent_map_list:
                map_source = MapSource(map, visible=False)
                self.map_list_trans.append(map_source)
                
    def init_data_and_add_to_tree(self):
        self.folder_list += self.db_mgr.read_folders()
        self.track_list = self.db_mgr.read_track_lines()
        self.wpt_list = self.db_mgr.read_way_points()
        self.photo_list = self.db_mgr.read_photos()
        
        for folder in self.folder_list[1:]:
            self.track_tree.add_tree_node(self.get_parent_folder(folder), folder)
        for track_line in self.track_list:
            self.track_tree.add_tree_node(self.get_parent_folder(track_line), track_line)
        for wpt in self.wpt_list:
            self.track_tree.add_tree_node(self.get_parent_folder(wpt), wpt)

        self.track_tree.Expand(self.track_tree._tree_root)
        self.frame.repaint(const.REDRAW_TRACK)
                
    def add_data(self, parent, child, commit=True):
        self.track_tree.add_tree_node(parent, child)  # 加树节点放在更新数据结构之前，因为wpt在加树时做了些初始化操作
        if isinstance(child, DataFolder):
            self.folder_list.append(child)
            self.db_mgr.add_folder(child, commit=commit)
        elif isinstance(child, TrackLine):
            self.track_list.append(child)
            self.db_mgr.add_track_line(child, commit=commit)
        elif isinstance(child, WayPoint):
            self.wpt_list.append(child)
            self.db_mgr.add_way_point(child, commit=commit)

    def del_folder(self, folder, commit=True):
        self.folder_list.remove(folder)
        self.db_mgr.del_folder(folder, commit=commit)
        deleted = [folder]

        to_be_deleted = []
        for child_folder in self.folder_list:
            if child_folder.parent == folder.uuid:
                to_be_deleted.append(child_folder)
        for to_be_del in to_be_deleted:
            deleted += self.del_folder(to_be_del, commit=commit)

        to_be_deleted = []
        for track_line in self.track_list:
            if track_line.parent == folder.uuid:
                to_be_deleted.append(track_line)
        for track_line in to_be_deleted:
            self.del_track_line(track_line, commit=commit)
        deleted += to_be_deleted

        to_be_deleted = []
        for wpt in self.wpt_list:
            if wpt.parent == folder.uuid:
                to_be_deleted.append(wpt)
        for wpt in to_be_deleted:
            self.del_wpt(wpt, commit=commit)
        deleted += to_be_deleted
        
        self.track_tree.Delete(folder.tree_node)
        return deleted

    def del_and_append_folder(self, folder):
        folders = [folder] + self.find_descendant_folders(folder)
        for data in folders:
            self.folder_list.remove(data)
            self.db_mgr.del_folder(data, commit=False)
            self.folder_list.append(data)
            self.db_mgr.add_folder(data, commit=False)
        self.db_mgr.commit()

    def find_descendant_folders(self, folder):
        descendant = []
        for child in self.folder_list:
            if child.parent == folder.uuid:
                descendant.append(child)
                descendant += self.find_descendant_folders(child)
        return descendant

    def del_track_line(self, track_line, commit=True):
        self.track_list.remove(track_line)
        self.db_mgr.del_track_line(track_line, commit=commit)
        self.track_tree.Delete(track_line.tree_node)
        return track_line

    def del_wpt(self, wpt, commit=True):
        self.wpt_list.remove(wpt)
        self.db_mgr.del_way_point(wpt, commit=commit)
        self.track_tree.Delete(wpt.tree_node)
        return wpt
    
    def empty_wpt_list(self):
        for wpt in self.wpt_list:
            self.db_mgr.del_way_point(wpt, commit=False)
            self.track_tree.Delete(wpt.tree_node)
        self.db_mgr.commit()
        self.wpt_list_deleted = self.wpt_list
        self.wpt_list = []

    def get_parent_folder(self, child):
        for folder in self.folder_list:
            if child.parent == folder.uuid:
                return folder
        return None


g = GlobalData()
