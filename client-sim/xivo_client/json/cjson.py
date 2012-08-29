# -*- coding: UTF-8 -*-

from __future__ import absolute_import

import cjson


encode = cjson.encode

def decode(data):
    return cjson.decode(data.replace('\\/', '/'))
