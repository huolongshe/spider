#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx


class PhotoViewDlg(wx.Dialog):
    def __init__(self, path, max_width, max_height):
        self.width = max_width
        
        self.raw_img = wx.Image()
        self.raw_img.LoadFile(path)
        self.raw_img_width = self.raw_img.GetWidth()
        self.raw_img_Height = self.raw_img.GetHeight()

        self.height = self.raw_img_Height * self.width // self.raw_img_width

        if self.height > max_height:
            self.height = max_height
            self.width = self.raw_img_width * self.height // self.raw_img_Height
            
        self.img = self.raw_img.Scale(self.width, self.height)
        self.bmp = wx.Bitmap(self.img)

        wx.Dialog.__init__(self, None, size=(self.width, self.height), style=wx.DEFAULT_DIALOG_STYLE | wx.SIMPLE_BORDER)
        self.dc = wx.ClientDC(self)

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase_background, self)
        self.Bind(wx.EVT_PAINT, self.on_paint, self)
        self.Bind(wx.EVT_RIGHT_UP, self.on_right_up, self)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mousewheel, self)

    def on_erase_background(self, event):
        pass

    def on_paint(self, event):
        self.dc.DrawBitmap(self.bmp, 0, 0, True)

    def on_right_up(self, event):
        menu = wx.Menu()
        text = '右旋'
        menu_item = menu.Append(-1, text)
        self.Bind(wx.EVT_MENU, self.on_rotate_right, menu_item)

        menu.AppendSeparator()
        text = '左旋'
        menu_item = menu.Append(-1, text)
        self.Bind(wx.EVT_MENU, self.on_rotate_left, menu_item)

        self.PopupMenu(menu)
        menu.Destroy()

    def on_rotate_left(self, event):
        self.raw_img = self.raw_img.Rotate90(clockwise=False)
        self.img = self.img.Rotate90(clockwise=False)
        self.bmp = wx.Bitmap(self.img)
        old_width = self.width
        self.width = self.height
        self.height = old_width
        self.DoSetClientSize(self.width, self.height)
        self.CentreOnParent()

    def on_rotate_right(self, event):
        self.raw_img = self.raw_img.Rotate90(clockwise=True)
        self.img = self.img.Rotate90(clockwise=True)
        self.bmp = wx.Bitmap(self.img)
        old_width = self.width
        self.width = self.height
        self.height = old_width
        self.DoSetClientSize(self.width, self.height)
        self.CentreOnParent()
        
    def on_mousewheel(self, event):
        rotation = event.GetWheelRotation()
        if rotation > 0:
            self.zoom_in()
        elif rotation < 0:
            self.zoom_out()
            
    def zoom_in(self):
        self.width = int(self.width * 1.1)
        self.height = int(self.height * 1.1)
        self.img = self.raw_img.Scale(self.width, self.height)
        self.bmp = wx.Bitmap(self.img)
        self.DoSetClientSize(self.width, self.height)
        self.CentreOnParent()
    
    def zoom_out(self):
        self.width = int(self.width * 0.9)
        self.height = int(self.height * 0.9)
        self.img = self.raw_img.Scale(self.width, self.height)
        self.bmp = wx.Bitmap(self.img)
        self.DoSetClientSize(self.width, self.height)
        self.CentreOnParent()
        self.dc.DrawBitmap(self.bmp, 0, 0, True)
        

