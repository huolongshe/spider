## Spider户外轨迹编辑器

    作者：霍龙社
    Email: huolongshe@126.com

---

[![GitHub releases](https://img.shields.io/github/release/huolongshe/spider.svg)](https://github.com/huolongshe/spider/releases)
[![GitHub downloads](https://img.shields.io/github/downloads/huolongshe/spider/total.svg)](https://github.com/huolongshe/spider/releases)
[![GitHub issues](https://img.shields.io/github/issues/huolongshe/spider.svg)](https://github.com/huolongshe/spider/issues)
[![GitHub forks](https://img.shields.io/github/forks/huolongshe/spider.svg)](https://github.com/huolongshe/spider/network)
[![GitHub stars](https://img.shields.io/github/stars/huolongshe/spider.svg)](https://github.com/huolongshe/spider/stargazers)
[![GitHub license](https://img.shields.io/github/license/huolongshe/spider.svg)](https://github.com/huolongshe/spider/blob/master/LICENSE)

### 功能特性：

1. 支持大多数市面上最常用的互联网在线地图的在线显示和浏览。

    目前支持的地图包括：谷歌地图、谷歌卫星地图、谷歌地形图、谷歌透明路网图、腾讯地图、腾讯卫星地图、腾讯地形图、腾讯透明路网图、高德地图、高德卫星地图、高德透明路网图、必应地图、必应卫星地图、天地图透明路网、OpenCycle Maps等。

2. 支持任意背景地图与透明路网图的叠加显示。

    多套透明路网图可任意组合叠加显示，透明路网图的上下层叠加显示顺序可按需调整。

3. 地图纠偏

    自动纠偏使用GCJ02坐标（所谓火星坐标）的在线地图。

    成功解决谷歌地形图中地标和路网标注不准确的问题。

4. 轨迹导入导出

    目前支持导入kml、kmz和gpx格式的轨迹文件，暂仅支持导出为kml格式轨迹文件。

5. 轨迹显示

    支持同时在地图上显示数百条轨迹，支持任意轨迹的隐藏与显示。支持鼠标直接点选轨迹进行操作。

6. 轨迹编辑

    支持轨迹分割，轨迹合并，轨迹点删除，轨迹段删除，轨迹起始点翻转，轨迹高程数据填充，轨迹点参数编辑，自绘轨迹，轨迹显示风格编辑，轨迹高程图显示等等。

7. 路点

    支持路点导入、导出，支持在任意位置放置路点图钉，支持路点显示图标变更，支持自动或手动获取路点海拔高度。

8. 照片

    支持添加照片并自动放置于地图上相应位置，支持显示照片拍摄朝向。

9. 地点和路径搜索

    支持根据地名搜索位置、根据位置搜索地名，支持根据地名或经纬度坐标搜索任意两点之间的行程路线。

10. 地图下载

    支持离线下载框选范围内任意缩放级别地图，并无缝拼接成一张大图片。


---

### 安装运行:

- **运行环境**
    
        Windows

- **使用源码安装**

    1. 安装Python 3.6。

    2. 下载wxPython4依赖包并安装。从 https://pypi.python.org/pypi/wxPython/4.0.1 选择相应的wxPython4依赖包下载，然后执行：

            pip install wheel
            pip install wxPython-4.0.1-cp36-cp36m-win_amd64.whl （替换为相应的下载版本）

    3. Clone或下载源代码。

    4. 进入spider.py所在文件夹，在命令行终端中执行：

            python spider.py

- **使用可执行文件安装**

    1. 进入release页面：https://github.com/huolongshe/spider/releases ，找到相应版本的spider.exe可执行文件并下载。

    2. 在电脑中新建一个空文件夹，将spider.exe文件拷贝至该文件夹。

    3. 鼠标双击该文件夹中的spider.exe，打开并运行轨迹编辑器。


