# -*- coding: UTF-8 -*-

import requests

def  _xivo_repositories():
    response = requests.get("http://mirror.xivo.io/repos/all")
    if response.status_code == 200:
        return response.text.splitlines()
    else:
        raise RuntimeError("Unable to fetch repositories list. Reponse code: %s." %response.status_code)

xivo_repositories = _xivo_repositories()

