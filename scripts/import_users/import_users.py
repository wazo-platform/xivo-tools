#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2013-2015 Avencall
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

import argparse
import csv
from xivo_ws import XivoServer, User, UserLine, UserVoicemail

COLUMNS = ['entity', 'firstname', 'lastname', 'language',
           'phonenumber', 'context', 'protocol',
           'voicemailname', 'voicemailmailbox', 'voicemailcontext', 'voicemailpassword',
           'mac']


def main():
    parsed_args = _parse_args()

    xivo_ws = XivoServer(parsed_args.hostname, parsed_args.username, parsed_args.password)

    import_users(xivo_ws, parsed_args.csv_file)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username',
                        help='authentication username')
    parser.add_argument('-p', '--password',
                        help='authentication password')
    parser.add_argument('-H', '--hostname', default='localhost',
                        help='hostname of xivo server')
    parser.add_argument('csv_file',
                        help='csv filename')
    return parser.parse_args()


def import_users(xivo_ws, filename):
    print 'Fetching devices and entities list...'
    device_id_by_mac = dict((device.mac, device.id) for device in xivo_ws.devices.list())
    entity_id_by_name = dict((entity.name, entity.id) for entity in xivo_ws.entities.list())

    print 'Reading file %s...' % filename
    users = []
    with open(filename, 'rb') as fobj:
        reader = csv.reader(fobj, delimiter=',')
        for row in reader:
            row_dict = convert_row_to_dict(row)

            user = User()
            user.firstname = row_dict['firstname']
            user.lastname = row_dict['lastname']
            user.language = row_dict['language']
            user.entity_id = entity_id_by_name[row_dict['entity']]

            user.line = UserLine()
            user.line.protocol = row_dict['protocol']
            user.line.context = row_dict['context']
            user.line.number = row_dict['phonenumber']
            user.line.device_id = device_id_by_mac[row_dict['mac']]

            user.voicemail = UserVoicemail()
            user.voicemail.name = row_dict['voicemailname']
            user.voicemail.number = row_dict['voicemailmailbox']
            user.voicemail.context = row_dict['voicemailcontext']
            user.voicemail.password = row_dict['voicemailpassword']

            users.append(user)

    nb_users = len(users)
    print 'Adding %d users...' % nb_users
    for i, user in enumerate(users, start=1):
        print '  Adding user %s %s (%d/%d)...' % (user.firstname, user.lastname, i, nb_users)
        xivo_ws.users.add(user)


def convert_row_to_dict(row):
    return dict(zip(COLUMNS, map(lambda s: s.decode('UTF-8'), row)))


if __name__ == '__main__':
    main()
