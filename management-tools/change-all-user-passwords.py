#!/usr/bin/env python3
# Copyright 2020 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
from requests import HTTPError
from wazo_auth_client import Client as AuthClient
from wazo_confd_client import Client as ConfdClient
from xivo.chain_map import ChainMap
from xivo.config_helper import read_config_file_hierarchy, parse_config_file

_DEFAULT_CONFIG = {
    'config_file': '/etc/wazo-upgrade/config.yml',
    'auth': {
        'key_file': '/var/lib/wazo-auth-keys/wazo-upgrade-key.yml'
    }
}


def load_config():
    file_config = read_config_file_hierarchy(_DEFAULT_CONFIG)
    key_config = _load_key_file(ChainMap(file_config, _DEFAULT_CONFIG))
    return ChainMap(key_config, file_config, _DEFAULT_CONFIG)


def _load_key_file(config):
    key_file = parse_config_file(config['auth']['key_file'])
    return {'auth': {'username': key_file['service_id'],
                     'password': key_file['service_key']}}


def list_user_uuids(confd_client):
    response = confd_client.users.list(recurse=True)
    return [item['uuid'] for item in response['items']]


def update_passwords(auth_client, user_uuids, password):
    for uuid in user_uuids:
        print('updating password for user', uuid)
        try:
            auth_client.users.set_password(uuid, password)
        except HTTPError as e:
            response = getattr(e, 'response', None)
            status_code = getattr(response, 'status_code', None)
            if status_code == 404:
                print('ignoring', uuid, 'no matching user in wazo-auth')
                continue
            raise


def main():
    password = sys.argv[1]
    print('new password', password)

    config = load_config()
    auth_client = AuthClient(**config['auth'])
    confd_client = ConfdClient(**config['confd'])

    token_data = auth_client.token.new(expiration=900)
    auth_client.set_token(token_data['token'])
    confd_client.set_token(token_data['token'])


    user_uuids = list_user_uuids(confd_client)
    update_passwords(auth_client, user_uuids, password)


if __name__ == '__main__':
    main()
