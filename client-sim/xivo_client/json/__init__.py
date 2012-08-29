# -*- coding: UTF-8 -*-

from xivo_client.json import json


def install_coder(coder):
    global encode
    global decode
    encode = coder.encode
    decode = coder.decode


encode = None
decode = None

install_coder(json)
