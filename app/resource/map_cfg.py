#!/usr/bin/env python
# -*- coding: UTF-8 -*-


google_map = {
    'name': '谷歌地图',
    'url': 'http://mt{$serverpart}.google.cn/vt/lyrs=m&hl=zh-CN&gl=cn&src=app&x={$x}&y={$y}&z={$z}',
    'zoom_min': 1,
    'zoom_max': 19,
    'server_part': '0,1,2,3',
    'coordinates': 'GCJ02',
    'transparent': False,
    'visible': False,
    'format': 'png'
}


google_satellite = {
    'name': '谷歌卫星地图',
    'url': 'http://mt{$serverpart}.google.cn/vt/lyrs=s&hl=zh-CN&gl=cn&src=app&x={$x}&y={$y}&z={$z}',
    'zoom_min': 1,
    'zoom_max': 19,
    'server_part': '0,1,2,3',
    'coordinates': 'GCJ02',
    'transparent': False,
    'visible': False,
    'format': 'jpg'
}


google_satellite_hybrid = {
    'name': '谷歌卫星混合地图',
    'url': 'http://mt{$serverpart}.google.cn/vt/lyrs=y&hl=zh-CN&gl=cn&src=app&x={$x}&y={$y}&z={$z}',
    'zoom_min': 1,
    'zoom_max': 19,
    'server_part': '0,1,2,3',
    'coordinates': 'GCJ02',
    'transparent': False,
    'visible': False,
    'format': 'jpg'
}


google_topographic = {
    'name': '谷歌地形图',
    'url': 'http://mt{$serverpart}.google.cn/vt/lyrs=t&hl=zh-CN&gl=cn&src=app&x={$x}&y={$y}&z={$z}',
    'zoom_min': 1,
    'zoom_max': 18,
    'server_part': '0,1,2,3',
    'coordinates': 'WGS84',
    'transparent': False,
    'visible': False,
    'format': 'jpg'
}


google_landmark = {
    'name': '谷歌透明路网',
    'url': 'http://mt{$serverpart}.google.cn/vt/lyrs=h&hl=zh-CN&gl=cn&src=app&x={$x}&y={$y}&z={$z}',
    'zoom_min': 1,
    'zoom_max': 19,
    'server_part': '0,1,2,3',
    'coordinates': 'GCJ02',
    'transparent': True,
    'visible': False,
    'format': 'png'
}


gaode_map = {
    'name': '高德地图',
    'url': 'http://webrd0{$serverpart}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&z={$z}&x={$x}&y={$y}',
    'zoom_min': 1,
    'zoom_max': 20,
    'server_part': '1,2,3,4',
    'coordinates': 'GCJ02',
    'transparent': False,
    'visible': False,
    'format': 'jpg'
}


gaode_satellite = {
    'name': '高德卫星地图',
    'url': 'http://webst0{$serverpart}.is.autonavi.com/appmaptile?lang=zh_cn&style=6&z={$z}&x={$x}&y={$y}',
    'zoom_min': 1,
    'zoom_max': 20,
    'server_part': '1,2,3,4',
    'coordinates': 'GCJ02',
    'transparent': False,
    'visible': False,
    'format': 'jpg'
}


gaode_landmark= {
    'name': '高德透明路网',
    'url': 'http://webst0{$serverpart}.is.autonavi.com/appmaptile?lang=zh_cn&style=8&z={$z}&x={$x}&y={$y}',
    'zoom_min': 1,
    'zoom_max': 18,
    'server_part': '1,2,3,4',
    'coordinates': 'GCJ02',
    'transparent': True,
    'visible': False,
    'format': 'png'
}


qq_map = {
    'name': '腾讯地图',
    'url': 'http://p{$serverpart}.map.gtimg.com/maptilesv3/{$z}/{$dx}/{$dy}/{$x}_{$y}.png',
    'zoom_min': 1,
    'zoom_max': 18,
    'server_part': '0,1,2,3',
    'coordinates': 'GCJ02',
    'transparent': False,
    'visible': False,
    'format': 'jpg'
}


qq_satellite = {
    'name': '腾讯卫星地图',
    'url': 'http://p{$serverpart}.map.gtimg.com/sateTiles/{$z}/{$dx}/{$dy}/{$x}_{$y}.jpg',
    'zoom_min': 1,
    'zoom_max': 18,
    'server_part': '0,1,2,3',
    'coordinates': 'GCJ02',
    'transparent': False,
    'visible': False,
    'format': 'jpg'
}


qq_topographic = {
    'name': '腾讯地形图',
    'url': 'http://p{$serverpart}.map.gtimg.com/demTiles/{$z}/{$dx}/{$dy}/{$x}_{$y}.jpg',
    'zoom_min': 1,
    'zoom_max': 18,
    'server_part': '0,1,2,3',
    'coordinates': 'GCJ02',
    'transparent': False,
    'visible': False,
    'format': 'jpg'
}


qq_landmark = {
    'name': '腾讯透明路网',
    'url': 'http://rt{$serverpart}.map.gtimg.com/tile?z={$z}&x={$x}&y={$y}&type=vector&styleid=3&version=251',
    'zoom_min': 1,
    'zoom_max': 18,
    'server_part': '0,1,2,3',
    'coordinates': 'GCJ02',
    'transparent': True,
    'visible': False,
    'format': 'png'
}


tianditu_landmark= {
    'name': '天地图透明路网',
    'url': 'http://t{$serverpart}.tianditu.cn/DataServer?T=cia_w&X={$x}&Y={$y}&L={$z}',
    'zoom_min': 3,
    'zoom_max': 18,
    'server_part': '0,1,2,3,4,5,6,7',
    'coordinates': 'WGS84',
    'transparent': True,
    'visible': False,
    'format': 'png'
}


opencycle_map = {
    'name': 'OpenCycle Map',
    'url': 'https://{$serverpart}.tile.thunderforest.com/outdoors/{$z}/{$x}/{$y}.png?apikey=351c7245beea4461bb88917bd2e9bfd4',
    'zoom_min': 1,
    'zoom_max': 22,
    'server_part': 'a,b,c',
    'coordinates': 'WGS84',
    'transparent': False,
    'visible': False,
    'format': 'png'
}


biying_map = {
    'name': '必应地图',
    'url': 'http://dynamic.t{$serverpart}.tiles.ditu.live.com/comp/ch/{$QuadKey}?it=G,TW,L,LA&mkt=zh-cn&og=109&cstl=w4c&ur=CN&n=z',
    'zoom_min': 1,
    'zoom_max': 19,
    'server_part': '0,1,2,3',
    'coordinates': 'GCJ02',
    'transparent': False,
    'visible': False,
    'format': 'png'
}

biying_satellite = {
    'name': '必应卫星地图',
    'url': 'http://ecn.t{$serverpart}.tiles.virtualearth.net/tiles/a{$QuadKey}?g=677&mkt=zh-CN',
    'zoom_min': 1,
    'zoom_max': 19,
    'server_part': '0,1,2,3',
    'coordinates': 'WGS84',
    'transparent': False,
    'visible': False,
    'format': 'jpg'
}


main_map_list = [google_satellite_hybrid, qq_topographic, google_satellite, google_topographic, google_map, gaode_map,
                 gaode_satellite, qq_map, qq_satellite, biying_map, biying_satellite, opencycle_map]
transparent_map_list =[qq_landmark, gaode_landmark, google_landmark, tianditu_landmark]
