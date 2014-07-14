# -*- coding: UTF-8 -*-
#
# Copyright (C) 2014 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import urllib
import urllib2
import json


class HTTPRequest(object):

    def __init__(self, host='127.0.0.1', port=80, headers=None, username=None, password=None):
        self._host = host
        self._port = port
        self._url = '%s:%s' % (self._host, self._port)
        self._headers = {
            'Content-Type': 'application/json',
            'Accept': 'text/plain'
        }
        if headers:
            self._headers.update(headers)
        self._opener = self._build_opener(username, password)

    def run(self, uri='', qry=None, data=None):
        url = self._url
        if uri:
            url = '%s/%s' % (url, uri)
        if qry is not None:
            url = '%s?%s' % (url, self._build_qry(qry))
        if isinstance(data, dict):
            data = json.dumps(data)
        request = urllib2.Request(url=url, data=data, headers=self._headers)
        handle = self._opener.open(request)
        try:
            response = handle.read()
            response_code = handle.code
        finally:
            handle.close()
        return response_code, response

    def _build_opener(self, username, password):
        handlers = []
        if username is not None and password is not None:
            pwd_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            pwd_manager.add_password(None, self._host, username, password)
            handlers.append(urllib2.HTTPDigestAuthHandler(pwd_manager))
        return urllib2.build_opener(*handlers)

    def _build_qry(self, qry):
        return urllib.urlencode(qry)


provd_http_request = HTTPRequest('http://127.0.0.1',
                                 8666,
                                 {'Content-Type': 'application/vnd.proformatique.provd+json'},
                                 'admin',
                                 'admin')
sysconfd_http_request = HTTPRequest('http://127.0.0.1', 8668)
