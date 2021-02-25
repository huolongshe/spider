#!/usr/bin/env python
# -*- coding: UTF-8 -*-


google_map = {
    'id': 'map005',
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
    'id': 'map003',
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
    'id': 'map001',
    'name': '谷歌卫星混合地图',
    # 'url': 'http://mt{$serverpart}.google.cn/vt/lyrs=y&hl=zh-CN&gl=cn&src=app&x={$x}&y={$y}&z={$z}',
    'url': 'http://webst0{$serverpart}.is.autonavi.com/appmaptile?lang=zh_cn&style=6&z={$z}&x={$x}&y={$y}',  # Google无法访问，用高德的代替
    'zoom_min': 1,
    'zoom_max': 19,
    'server_part': '0,1,2,3',
    'coordinates': 'GCJ02',
    'transparent': False,
    'visible': False,
    'format': 'jpg'
}


google_topographic = {
    'id': 'map004',
    'name': '谷歌地形图',
    'url': 'http://mt{$serverpart}.google.cn/vt/lyrs=t,r&hl=zh-CN&gl=cn&src=app&x={$x}&y={$y}&z={$z}',
    'zoom_min': 1,
    'zoom_max': 18,
    'server_part': '0,1,2,3',
    'coordinates': 'WGS84',
    'transparent': False,
    'visible': False,
    'format': 'jpg'
}


google_landmark = {
    'id': 'map015',
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
    'id': 'map006',
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
    'id': 'map007',
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
    'id': 'map014',
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
    'id': 'map008',
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
    'id': 'map009',
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
    'id': 'map002',
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
    'id': 'map014',
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


tianditu_cia = {
    'id': 'map016',
    'name': '天地图卫星标记',
    'url': 'http://t{$serverpart}.tianditu.gov.cn/cia_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cia&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILECOL={$x}&TILEROW={$y}&TILEMATRIX={$z}&tk=c8e0b9ae169804fa3d0dbdcc04017804',
    'zoom_min': 1,
    'zoom_max': 18,
    'server_part': '0,1,2,3,4,5,6,7',
    'coordinates': 'WGS84',
    'transparent': True,
    'visible': False,
    'format': 'png'
}


tianditu_img = {
    'id': 'map017',
    'name': '天地图卫星地图',
    'url': 'http://t{$serverpart}.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILECOL={$x}&TILEROW={$y}&TILEMATRIX={$z}&tk=c8e0b9ae169804fa3d0dbdcc04017804',
    'zoom_min': 1,
    'zoom_max': 18,
    'server_part': '0,1,2,3,4,5,6,7',
    'coordinates': 'WGS84',
    'transparent': False,
    'visible': False,
    'format': 'png'
}


tianditu_cta= {
    'id': 'map018',
    'name': '天地图地形标记',
    'url': 'http://t{$serverpart}.tianditu.gov.cn/cta_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cta&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILECOL={$x}&TILEROW={$y}&TILEMATRIX={$z}&tk=c8e0b9ae169804fa3d0dbdcc04017804',
    'zoom_min': 1,
    'zoom_max': 18,
    'server_part': '0,1,2,3,4,5,6,7',
    'coordinates': 'WGS84',
    'transparent': True,
    'visible': False,
    'format': 'png'
}


tianditu_ter = {
    'id': 'map019',
    'name': '天地图地形图',
    'url': 'http://t{$serverpart}.tianditu.gov.cn/ter_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ter&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILECOL={$x}&TILEROW={$y}&TILEMATRIX={$z}&tk=c8e0b9ae169804fa3d0dbdcc04017804',
    'zoom_min': 1,
    'zoom_max': 18,
    'server_part': '0,1,2,3,4,5,6,7',
    'coordinates': 'WGS84',
    'transparent': False,
    'visible': False,
    'format': 'png'
}

tianditu_cva= {
    'id': 'map020',
    'name': '天地图矢量标记',
    'url': 'http://t{$serverpart}.tianditu.gov.cn/cva_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=cva&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILECOL={$x}&TILEROW={$y}&TILEMATRIX={$z}&tk=c8e0b9ae169804fa3d0dbdcc04017804',
    'zoom_min': 1,
    'zoom_max': 18,
    'server_part': '0,1,2,3,4,5,6,7',
    'coordinates': 'WGS84',
    'transparent': True,
    'visible': False,
    'format': 'png'
}


tianditu_vec = {
    'id': 'map021',
    'name': '天地图矢量图',
    'url': 'http://t{$serverpart}.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=vec&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILECOL={$x}&TILEROW={$y}&TILEMATRIX={$z}&tk=c8e0b9ae169804fa3d0dbdcc04017804',
    'zoom_min': 1,
    'zoom_max': 18,
    'server_part': '0,1,2,3,4,5,6,7',
    'coordinates': 'WGS84',
    'transparent': False,
    'visible': False,
    'format': 'png'
}


tianditu_ibo = {
    'id': 'map022',
    'name': '天地图全球境界',
    'url': 'http://t{$serverpart}.tianditu.gov.cn/ibo_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ibo&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILECOL={$x}&TILEROW={$y}&TILEMATRIX={$z}&tk=c8e0b9ae169804fa3d0dbdcc04017804',
    'zoom_min': 1,
    'zoom_max': 18,
    'server_part': '0,1,2,3,4,5,6,7',
    'coordinates': 'WGS84',
    'transparent': True,
    'visible': False,
    'format': 'png'
}

opencycle_map = {
    'id': 'map012',
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
    'id': 'map010',
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
    'id': 'map011',
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


main_map_list = [tianditu_vec, tianditu_img, tianditu_ter, google_satellite_hybrid, qq_topographic, google_satellite, google_topographic, google_map, gaode_map,
                 gaode_satellite, qq_map, qq_satellite, opencycle_map]
transparent_map_list =[tianditu_ibo, tianditu_cva, tianditu_cia, tianditu_cta, qq_landmark, gaode_landmark, google_landmark]
