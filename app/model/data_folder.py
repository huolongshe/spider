#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import uuid


class DataFolder:
    def __init__(self, parent='', name='未命名', data_uuid=None, order_in_parent=-1):
        if data_uuid:
            self.uuid = data_uuid
        else:
            self.uuid = uuid.uuid1().__str__()
        self.name = name
        self.parent = parent  # 父亲节点的uuid
        self.order_in_parent = order_in_parent
        self.tree_node = None
        
