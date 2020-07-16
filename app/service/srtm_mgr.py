#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import threading
import time
import zipfile
import requests
import io
import math
from app.resource.srtm_continent_idx import srtm_continent_index


# dds.cr.usgs.gov网站下载参数
URL_PREFIX_usgs = 'https://dds.cr.usgs.gov/srtm/version2_1/SRTM3/'
CONTINENTS = ['', 'Eurasia', 'North_America', 'Australia', 'Islands', 'South_America', 'Africa']
ARRAY_LEN = 1442401
HGT_SIZE = 2884802

# srtm.csi.cgiar.org网站下载参数
URL_PREFIX_cagar = 'http://srtm.csi.cgiar.org/SRT-ZIP/SRTM_v41/SRTM_Data_ArcASCII/'
# Example: 'http://srtm.csi.cgiar.org/SRT-ZIP/SRTM_v41/SRTM_Data_ArcASCII/srtm_60_05.zip'
CELL_SIZE = 0.00083333   # 5/6000，精确到小数点后8位（与手机轨迹记录一致），一个单元对应的经纬度范围，约90米
HALF_CELL = 0.000416667

# 原始数据空值
VOID_VAL_cagar = -9999
VOID_VAL_usgs = -32768

# 特殊高程值设置
ZERO_VALUE = 0.1  # 原始数据为0、空值，或者下载和计算过程中出错时（除网络因素），设置为0.01

# 下载线程数和数据包大小设置
THREAD_NUM = 20
DATAGRAM_SIZE = 1380


class SrtmManager:
    def __init__(self, g):
        self.g = g
        self._srtm_cache_usgs = {}
        self._srtm_cache_cagar = {}
        self._srtm_cache_path = os.path.join(self.g.data_path, 'srtmcache')
        if not os.path.exists(self._srtm_cache_path):
            os.mkdir(self._srtm_cache_path)
            
        # 与调用者共享的的常量
        self.ERROR_NETWORK = -1001
        self.ERROR_CANCELED = -1002
        self.PROGRESS_RANGE = 100.0
        # 与调用者共享的的变量
        self.alt = ZERO_VALUE
        self.progress_unit = 1.0
        self.progress_now = 0.0
        self.manual_canceled = False
        self.downloading = False
        
        self._error_encountered = False
        self._running_threads = 0
        self._srtm_zip_segments = [b''] * THREAD_NUM
        
    def get_alt_local(self, lon, lat):
        if self.g.srtm_url_index == 1:
            return self.get_alt_local_cgiar(lon, lat)
        else:
            return self.get_alt_local_usgs(lon, lat)
            
    def get_alt_network(self, lon, lat):
        if self.g.srtm_url_index == 1:
            return self.get_alt_network_cagar(lon, lat)
        else:
            return self.get_alt_network_usgs(lon, lat)

    def get_alt_local_usgs(self, lon, lat):
        lon_i = math.floor(lon)
        lat_i = math.floor(lat)

        srtm_data = self._srtm_cache_usgs.get((lon_i, lat_i))  # 先从内存cache中读取，存在则返回
        if srtm_data:
            return self.compute_alt_usgs(lon, lat, srtm_data)

        url, file_name = self.gen_srtm_url_usgs(lon_i, lat_i)
        if not url:
            return ZERO_VALUE

        srtm_path = os.path.join(self._srtm_cache_path, file_name)
        if os.path.isfile(srtm_path):
            try:
                with open(srtm_path, 'rb') as fn:
                    srtm_zip = fn.read()
            except:
                return None
        else:
            return None

        if srtm_zip:
            try:
                zip_file = zipfile.ZipFile(io.BytesIO(srtm_zip))
                zip_info_list = zip_file.infolist()
                srtm = zip_file.open(zip_info_list[0]).read()
                srtm_data = [0] * ARRAY_LEN
                for i in range(0, ARRAY_LEN):
                    srtm_data[i] = (srtm[2 * i] << 8) + srtm[2 * i + 1]  # '<<'的运算优先级低于'+' ，需要用括弧
                    if srtm_data[i] >= 32768:
                        srtm_data[i] -= 65536
                self._srtm_cache_usgs[(lon_i, lat_i)] = srtm_data
                return self.compute_alt_usgs(lon, lat, srtm_data)
            except:
                os.remove(srtm_path)
                return None

    def get_alt_network_usgs(self, lon, lat):
        self.downloading = True
        self.manual_canceled = False
        self.alt = ZERO_VALUE

        lon_i = math.floor(lon)
        lat_i = math.floor(lat)
        ret = self.download_srtm_usgs(lon_i, lat_i)
        if ret < 0:  # 下载出错，直接返回
            self.alt = ret
            self.downloading =False
            return self.alt
        
        srtm_data = self._srtm_cache_usgs.get((lon_i, lat_i)) # 下载成功后数据缓存在内存cache
        if srtm_data:
            alt = self.compute_alt_usgs(lon, lat, srtm_data)
            self.alt = alt
            self.downloading = False
            return self.alt
        else: # 下载过程中出错
            self.alt = ZERO_VALUE
            self.downloading = False
            return self.alt

    def download_srtm_usgs(self, lon_i, lat_i):
        url, file_name = self.gen_srtm_url_usgs(lon_i, lat_i)
        if not url:
            return ZERO_VALUE
        srtm_path = os.path.join(self._srtm_cache_path, file_name)
        self.progress_now = 6.0

        try:
            res = requests.head(url)
            if res.status_code == 200:
                file_size = int(res.headers['Content-Length'])
            else:
                return self.ERROR_NETWORK
        except:
            return self.ERROR_NETWORK
        self.progress_now = 8.0
        
        thread_num = THREAD_NUM
        if file_size % THREAD_NUM == 0:
            segment_size = file_size // THREAD_NUM
        else:
            segment_size = file_size // (THREAD_NUM - 1)
            if file_size % (THREAD_NUM - 1) == 0:
                thread_num = THREAD_NUM - 1
            
        self.progress_unit = (self.PROGRESS_RANGE - 10) / (file_size // DATAGRAM_SIZE + 1)
        self.progress_now = 10.0

        self._srtm_zip_segments = [b''] * thread_num
        self._error_encountered = False
        self._running_threads = 0
        for i in range(thread_num):
            thread = threading.Thread(target=self.download_strm_thread, args=(url, i, segment_size))
            thread.setDaemon(True)
            thread.start()

        time.sleep(0.1)  # 创建新线程后，不能马上开始监听
        while self._running_threads > 0:
            time.sleep(0.1)
            if self._error_encountered:
                break

        if self.manual_canceled:
            return self.ERROR_CANCELED

        if None in self._srtm_zip_segments:
            return self.ERROR_NETWORK

        srtm_zip = b''.join(self._srtm_zip_segments)
        try:
            zip_file = zipfile.ZipFile(io.BytesIO(srtm_zip))
            zip_info_list = zip_file.infolist()
            srtm = zip_file.open(zip_info_list[0]).read()
        except:
            return self.ERROR_NETWORK

        srtm_data = [0] * ARRAY_LEN
        for i in range(0, ARRAY_LEN):
            srtm_data[i] = (srtm[2 * i] << 8) + srtm[2 * i + 1]  # '<<'的运算优先级低于'+' ，需要用括弧
            if srtm_data[i] >= 32768:
                srtm_data[i] -= 65536
        self._srtm_cache_usgs[(lon_i, lat_i)] = srtm_data

        with open(srtm_path, 'wb') as fn:  # 先加载数据，再保存至文件，如果数据有问题则可以不保存
            fn.write(srtm_zip)

        return 0
    
    def gen_srtm_url_usgs(self, lon, lat):
        ns = 'N' if lat >= 0 else 'S'
        ew = 'E' if lon >= 0 else 'W'
        file_name = '%s%02d%s%03d.hgt.zip' % (ns, abs(lat), ew, abs(lon))
        idx = (lat + 59) * 360 + (lon + 180)
        num = srtm_continent_index[idx]  # 将ASCII代表的数字转化成整数形式数字
        url = URL_PREFIX_usgs + CONTINENTS[num] + '/' + file_name if num > 0 else ''
        return url, file_name


    def download_strm_thread(self, url, segment_index, segment_size):
        self._running_threads += 1
        self._srtm_zip_segments[segment_index] = b''

        try:
            headers = {'Range': 'bytes=%s-%s' % (segment_index * segment_size, (segment_index + 1) * segment_size - 1)}
            response = requests.get(url, headers=headers, stream=True)
            if response.status_code // 100 == 2:  # 此处响应码应为206
                for data in response.iter_content(DATAGRAM_SIZE):
                    if self.manual_canceled:
                        self._error_encountered = True
                        break
                    if self._error_encountered:  # 其他线程遇到错误退出，本线程也应跟着退出，不要再继续下载了
                        break
                    self._srtm_zip_segments[segment_index] += data
                    self.progress_now += self.progress_unit
            else:
                self._srtm_zip_segments[segment_index] = None
                self._error_encountered = True
            response.close()
        except:
            self._srtm_zip_segments[segment_index] = None
            self._error_encountered = True
        self._running_threads -= 1

    def compute_alt_usgs(self, lon, lat, alts):
        x = (lon - math.floor(lon)) * 1200.0
        y = 1200.9999999 - (lat - math.floor(lat)) * 1200.0  # 不使用1201，以解决纬度坐标正好等于整数边界坐标的问题
        idx1 = int(y) * 1201 + int(x)
        four_alts = (alts[idx1], alts[idx1 + 1], alts[idx1 - 1201], alts[idx1 - 1200])  #
        num_voids = four_alts.count(VOID_VAL_usgs)

        if num_voids == 0:
            alt = self.bilinear_interpolate_usgs(four_alts, x, y)
        elif num_voids == 1:
            alt = self.bilinear_interpolate_usgs(self.fix_void_usgs(four_alts), x, y)
        elif num_voids == 2 or num_voids == 3:
            alt = self.average_non_void_usgs(four_alts)
        else:
            alt = VOID_VAL_usgs
            
        if alt <= 0:
            alt = ZERO_VALUE  # 计算出的高度无效时，人为设置一个有效的值
        return alt

    def bilinear_interpolate_usgs(self, four_alts, x, y):
        alpha = x - int(x)
        beta = 1 - (y - int(y))
        alt = (1 - alpha) * (1 - beta) * four_alts[0] + alpha * (1 - beta) * four_alts[1] \
              + (1 - alpha) * beta * four_alts[2] + alpha * beta * four_alts[3]
        return alt

    def fix_void_usgs(self, four_alts):
        fixed = []
        for alt in four_alts:
            if alt == VOID_VAL_usgs:
                fixed.append(int(round(self.average_non_void_usgs(four_alts))))
            else:
                fixed.append(alt)
        return fixed

    def average_non_void_usgs(self, four_alts):
        total_alt = 0.0
        num_alts = 0
        for alt in four_alts:
            if alt != VOID_VAL_usgs:
                total_alt += alt
                num_alts += 1
        if num_alts < 1:
            return VOID_VAL_usgs
        return total_alt // num_alts

    #  以下为从http://srtm.csi.cgiar.org网站下载相关函数
    def get_alt_local_cgiar(self, lon, lat):
        lon_block = int(((lon + HALF_CELL) + 180.0) / 5.0) + 1
        lat_block = int((60 - (lat + HALF_CELL)) / 5.0) + 1
    
        srtm_data = self._srtm_cache_cagar.get((lon_block, lat_block))  # 先从内存cache中读取，存在则返回
        if srtm_data:
            return self.compute_alt_cagar(lon, lat, srtm_data)
    
        url, file_name = self.gen_srtm_url_cagar(lon_block, lat_block)
        srtm_path = os.path.join(self._srtm_cache_path, file_name)
        if os.path.isfile(srtm_path):
            try:
                with open(srtm_path, 'rb') as fn:
                    srtm_zip = fn.read()
            except:
                return None
        else:
            return None
    
        if srtm_zip:
            try:
                zip_file = zipfile.ZipFile(io.BytesIO(srtm_zip))
                zip_info_list = zip_file.infolist()
                srtm_asc = zip_file.open(zip_info_list[1]).read()
                srtm_data = srtm_asc.split(b'\r\n')
                self._srtm_cache_cagar[(lon_block, lat_block)] = srtm_data  # 从本地文件读出到内存cache
                return self.compute_alt_cagar(lon, lat, srtm_data)
            except:
                os.remove(srtm_path)
                return None
        else:
            os.remove(srtm_path)
            return None

    def get_alt_network_cagar(self, lon, lat):
        self.downloading = True
        self.manual_canceled = False
        self.alt = ZERO_VALUE
    
        lon_block = int(((lon + HALF_CELL) + 180.0) / 5.0) + 1
        lat_block = int((60 - (lat + HALF_CELL)) / 5.0) + 1
        ret = self.download_srtm_cagar(lon_block, lat_block)
        if ret < 0:  # 下载出错，直接返回
            self.alt = ret
            self.downloading = False
            return self.alt
    
        srtm_data = self._srtm_cache_cagar.get((lon_block, lat_block))  # 下载成功后后数据缓存在内存cache
        if srtm_data:
            alt = self.compute_alt_cagar(lon, lat, srtm_data)
            self.alt = alt
            self.downloading = False
            return self.alt
        else:  # 下载过程中计算错误
            self.alt = ZERO_VALUE
            self.downloading = False
            return self.alt

    def download_srtm_cagar(self, lon_block, lat_block):
        url, file_name = self.gen_srtm_url_cagar(lon_block, lat_block)
        srtm_path = os.path.join(self._srtm_cache_path, file_name)
        self.progress_now = 5
    
        try:
            res = requests.head(url)
            if res.status_code == 200:
                file_size = int(res.headers['Content-Length'])
            else:
                return self.ERROR_NETWORK
        except:
            return self.ERROR_NETWORK
        self.progress_now = 7.0

        thread_num = THREAD_NUM
        if file_size % THREAD_NUM == 0:
            segment_size = file_size // THREAD_NUM
        else:
            segment_size = file_size // (THREAD_NUM - 1)
            if file_size % (THREAD_NUM - 1) == 0:
                thread_num = THREAD_NUM - 1

        self.progress_unit = (self.PROGRESS_RANGE - 8) / (file_size // DATAGRAM_SIZE + 1)
        self.progress_now = 8.0

        self._srtm_zip_segments = [b''] * thread_num
        self._error_encountered = False
        self._running_threads = 0
        for i in range(thread_num):
            thread = threading.Thread(target=self.download_strm_thread, args=(url, i, segment_size))
            thread.setDaemon(True)
            thread.start()

        time.sleep(0.1)  # 创建新线程后，不能马上开始监听
        while self._running_threads > 0:
            time.sleep(0.1)
            if self._error_encountered:
                break

        if self.manual_canceled:
            return self.ERROR_CANCELED

        if None in self._srtm_zip_segments:
            return self.ERROR_NETWORK

        srtm_zip = b''.join(self._srtm_zip_segments)
        try:
            zip_file = zipfile.ZipFile(io.BytesIO(srtm_zip))
            zip_info_list = zip_file.infolist()
            srtm_asc = zip_file.open(zip_info_list[1]).read()
        except:
            return self.ERROR_NETWORK
        srtm_data = srtm_asc.split(b'\r\n')
        self._srtm_cache_cagar[(lon_block, lat_block)] = srtm_data
    
        with open(srtm_path, 'wb') as fn:  # 先加载数据，再保存至文件，如果数据有问题则可以不保存
            fn.write(srtm_zip)
        return 0

    def gen_srtm_url_cagar(self, lon_block, lat_block):
        file_name = 'srtm_%02d_%02d.zip' % (lon_block, lat_block)
        url = URL_PREFIX_cagar + file_name
        return url, file_name

    def compute_alt_cagar(self, lon, lat, srtm_data):
        lon_llcorner = float(srtm_data[2].split()[1])
        lat_llcorner = float(srtm_data[3].split()[1])
    
        x = (lon - lon_llcorner) / CELL_SIZE
        y = 6000.99999999 - ((lat - lat_llcorner) / CELL_SIZE)  # 不使用6001，以解决纬度坐标正好等于CELL边界坐标的问题
    
        srtm_data_line1 = srtm_data[int(y) + 6].split()
        srtm_data_line2 = srtm_data[int(y) - 1 + 6].split()
    
        four_alts = (int(srtm_data_line1[int(x)]), int(srtm_data_line1[int(x) + 1]), int(srtm_data_line2[int(x)]),
                     int(srtm_data_line2[int(x) + 1]))
        num_voids = four_alts.count(VOID_VAL_cagar)
    
        if num_voids == 0:
            alt = self.bilinear_interpolate_cagar(four_alts, x, y)
        elif num_voids == 1:
            alt = self.bilinear_interpolate_cagar(self.fix_void_cagar(four_alts), x, y)
        elif num_voids == 2 or num_voids == 3:
            alt = self.average_non_void_cagar(four_alts)
        else:
            alt = VOID_VAL_cagar
            
        if alt <= 0:
            alt = ZERO_VALUE  # 计算出的高度无效时，人为设置一个有效的值
        return alt

    def bilinear_interpolate_cagar(self, four_alts, x, y):
        alpha = x - int(x)
        beta = 1 - (y - int(y))
        alt = (1 - alpha) * (1 - beta) * four_alts[0] + alpha * (1 - beta) * four_alts[1] \
              + (1 - alpha) * beta * four_alts[2] + alpha * beta * four_alts[3]
        return alt

    def fix_void_cagar(self, four_alts):
        fixed = []
        for alt in four_alts:
            if alt == VOID_VAL_cagar:
                fixed.append(int(round(self.average_non_void_cagar(four_alts))))
            else:
                fixed.append(alt)
        return fixed

    def average_non_void_cagar(self, four_alts):
        total_alt = 0.0
        num_alts = 0
        for alt in four_alts:
            if alt != VOID_VAL_cagar:
                total_alt += alt
                num_alts += 1
        if num_alts < 1:
            return VOID_VAL_cagar
        return total_alt / num_alts
