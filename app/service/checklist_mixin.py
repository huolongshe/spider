#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import wx


"""
FILENAME: CheckListCtrlMixin.py
AUTHOR:   Bruce Who (bruce.who.hk at gmail.com)
DATE:     2006-02-09
$Revision$
DESCRIPTION:
    This script provide a mixin for ListCtrl which add a checkbox in the first
    column of each row. It is inspired by limodou's CheckList.py(which can be
    got from his NewEdit) and improved:
        - You can just use InsertStringItem() to insert new items;
        - Once a checkbox is checked/unchecked, the corresponding item is not
          selected;
        - You can use SetItemData() and GetItemData();
        - Interfaces are changed to OnCheckItem(), IsChecked(), CheckItem().

    You should not set a imagelist for the ListCtrl once this mixin is used.

HISTORY:
1.3     - You can check/uncheck a group of sequential items by <Shift-click>:
          First click(or <Shift-Click>) item1 to check/uncheck it, then
          Shift-click item2 to check/uncheck it, and you'll find that all
          items between item1 and item2 are check/unchecked!
1.2     - Add ToggleItem()
1.1     - Initial version
"""


class CheckListCtrlMixin:
    """
    This is a mixin for ListCtrl which add a checkbox in the first
    column of each row. It is inspired by limodou's CheckList.py(which
    can be got from his NewEdit) and improved:

        - You can just use InsertStringItem() to insert new items;

        - Once a checkbox is checked/unchecked, the corresponding item
          is not selected;

        - You can use SetItemData() and GetItemData();

        - Interfaces are changed to OnCheckItem(), IsChecked(),
          CheckItem().

    You should not set a imagelist for the ListCtrl once this mixin is used.
    """
    
    def __init__(self, check_image=None, uncheck_image=None, imgsz=(16, 16)):
        if check_image is not None:
            imgsz = check_image.GetSize()
        elif uncheck_image is not None:
            imgsz = check_image.GetSize()
        
        self.__imagelist_ = wx.ImageList(*imgsz)
        
        # Create default checkbox images if none were specified
        if check_image is None:
            check_image = self.__CreateBitmap(wx.CONTROL_CHECKED, imgsz)
        
        if uncheck_image is None:
            uncheck_image = self.__CreateBitmap(0, imgsz)
        
        self.uncheck_image = self.__imagelist_.Add(uncheck_image)
        self.check_image = self.__imagelist_.Add(check_image)
        self.SetImageList(self.__imagelist_, wx.IMAGE_LIST_SMALL)
        self.__last_check_ = None
        
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        
        # override the default methods of ListCtrl/ListView
        self.InsertStringItem = self.__InsertStringItem_
    
    def __CreateBitmap(self, flag=0, size=(16, 16)):
        """Create a bitmap of the platforms native checkbox. The flag
        is used to determine the checkboxes state (see wx.CONTROL_*)

        """
        bmp = wx.Bitmap(*size)
        dc = wx.MemoryDC(bmp)
        dc.Clear()
        wx.RendererNative.Get().DrawCheckBox(self, dc, (0, 0, size[0], size[1]), flag)
        dc.SelectObject(wx.NullBitmap)
        return bmp
    
    # NOTE: if you use InsertItem, InsertImageItem or InsertImageStringItem,
    #       you must set the image yourself.
    def __InsertStringItem_(self, index, label):
        index = self.InsertItem(index, label, 0)
        return index
    
    def OnLeftDown(self, evt):
        (index, flags) = self.HitTest(evt.GetPosition())
        if flags == wx.LIST_HITTEST_ONITEMICON:
            img_idx = self.GetItem(index).GetImage()
            flag_check = img_idx == 0
            begin_index = index
            end_index = index
            if self.__last_check_ is not None \
                    and wx.GetKeyState(wx.WXK_SHIFT):
                last_index, last_flag_check = self.__last_check_
                if last_flag_check == flag_check:
                    # XXX what if the previous item is deleted or new items
                    # are inserted?
                    item_count = self.GetItemCount()
                    if last_index < item_count:
                        if last_index < index:
                            begin_index = last_index
                            end_index = index
                        elif last_index > index:
                            begin_index = index
                            end_index = last_index
                        else:
                            assert False
            while begin_index <= end_index:
                self.CheckItem(begin_index, flag_check)
                begin_index += 1
            self.__last_check_ = (index, flag_check)
        else:
            evt.Skip()
    
    def OnCheckItem(self, index, flag):
        pass
    
    def IsChecked(self, index):
        return self.GetItem(index).GetImage() == 1
    
    def CheckItem(self, index, check=True):
        img_idx = self.GetItem(index).GetImage()
        if img_idx == 0 and check is True:
            self.SetItemImage(index, 1)
            self.OnCheckItem(index, True)
        elif img_idx == 1 and check is False:
            self.SetItemImage(index, 0)
            self.OnCheckItem(index, False)
    
    def ToggleItem(self, index):
        self.CheckItem(index, not self.IsChecked(index))
