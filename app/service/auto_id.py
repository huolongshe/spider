#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import random


class AutoId:
    id = random.randrange(10, 99) * 1000


def get_id():
    AutoId.id += 1
    return AutoId.id
