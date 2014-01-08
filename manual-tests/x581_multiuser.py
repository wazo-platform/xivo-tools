# -*- coding: utf-8 -*-

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

import requests
import json


def check_status(response):
    if response.status_code >= 300:
        raise Exception("STATUS %s. %s" % (response.status_code, response.text))
    return response


URL = 'https://xivo-test.lan-quebec.avencall.com:50051/1.1'
USERNAME = 'admin'
PASSWORD = 'proformatique'

users = [
    {
        'firstname': 'Hakuna',
        'lastname': 'Matata',
    },
    {
        'firstname': 'Lion',
        'lastname': 'King',
    },
]

lineinfo = {
    'context': 'default',
    'device_slot': 1,
}

exteninfo = {
    'exten': '1200',
    'context': 'default',
}

created_users = []

auth = requests.auth.HTTPDigestAuth(USERNAME, PASSWORD)
headers = {'Accept': 'application/json',
           'Content-Type': 'application/json'}

session = requests.Session()
session.auth = auth
session.headers = headers
session.verify = False

print "creating extension %s" % exteninfo
resp = check_status(session.post('%s/extensions' % URL, json.dumps(exteninfo)))
extension = resp.json()


print "creating line %s" % lineinfo
resp = check_status(session.post('%s/lines_sip' % URL, json.dumps(lineinfo)))
line = resp.json()


for userinfo in users:
    print "creating user %s" % userinfo
    resp = check_status(session.post('%s/users' % URL, json.dumps(userinfo)))
    created_users.append(resp.json())


for user in created_users:
    linkinfo = {
        'user_id': user['id'],
        'extension_id': extension['id'],
        'line_id': line['id'],
    }
    print "linking %s" % linkinfo
    resp = check_status(session.post('%s/user_links' % URL, json.dumps(linkinfo)))
    link = resp.json()


resp = check_status(session.get('%s/lines_sip/%s' % (URL, line['id'])))
line = resp.json()

print "Done ! Your provisioning number is %s" % line['provisioning_extension']
