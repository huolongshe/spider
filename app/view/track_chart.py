#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx
from wx.lib import plot

from app.globals import const
from app.globals.global_data import g


class TrackChart(plot.PlotCanvas):
    def __init__(self, parent):
        plot.PlotCanvas.__init__(self, parent=parent, style=wx.BORDER_DOUBLE | wx.TE_PROCESS_TAB)
        self.canvas.Bind(wx.EVT_LEFT_DOWN, self.on_left_down, self.canvas)

    def draw_alt_chart(self, track_line=None):
        if track_line is None:
            self.Clear()
            return  # 当前无选中轨迹则仅做清空工作并返回

        alt_min = int(track_line.alt_min)
        alt_max = int(track_line.alt_max)
        if alt_max == alt_min:
            self.Clear()
            return  # 当前无海拔数据则仅做清空工作并返回
        
        line_list = []
        for i in range(0, track_line.point_num):
            line_value = int(track_line.track_points[i].alt)
            line_ends = [(i, alt_min), (i, line_value)]
            if not g.in_editing:
                color = 'blue'
            elif track_line.sel_start_idx <= i <= track_line.sel_end_idx:
                color = 'green'
            elif track_line.is_checked:
                color = 'yellow'
            else:
                color = 'blue'
            line = plot.PolyLine(line_ends, colour=color)
            line_list.append(line)

        if g.in_editing and track_line.selected_point:
            i = track_line.track_points.index(track_line.selected_point)
            line_ends = [(i, alt_min), (i, alt_max)]
            color = 'red'
            line = plot.PolyLine(line_ends, colour=color)
            line_list.append(line)

        plot_graphics = plot.PlotGraphics(line_list, yLabel='海拔（米）')
        self.Draw(plot_graphics, xAxis=(0, track_line.point_num), yAxis=(alt_min, alt_max))

    def on_left_down(self, event):
        self.canvas.SetFocus()
        self.canvas.SetFocusFromKbd()
        if g.in_editing and g.track_edit.selected_track_line:
            x, y = self.GetXY(event)
            index = int(x)
            track_line = g.track_edit.selected_track_line
            if 0 <= index <= len(track_line.track_points):
                track_line.selected_point = track_line.track_points[index]
                g.frame.repaint(canvas=const.REDRAW_COPY)
        g.logger.SetFocus()
        g.logger.Bind(wx.EVT_KEY_DOWN, self.on_key_down, g.logger)

    def on_key_down(self, event):
        if g.in_editing and g.track_edit.selected_track_line:
            track_line = g.track_edit.selected_track_line
            if track_line.selected_point:
                index = track_line.track_points.index(track_line.selected_point)
                if event.GetKeyCode() == wx.WXK_LEFT and index > 0:
                    index -= 1
                elif event.GetKeyCode() == wx.WXK_RIGHT and index < len(track_line.track_points) - 1:
                    index += 1
                else:
                    return
                track_line.selected_point = track_line.track_points[index]
                g.frame.repaint(canvas=const.REDRAW_COPY)
