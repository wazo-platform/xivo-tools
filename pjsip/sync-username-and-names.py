#!/usr/bin/env python3
# Copyright 2020 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import sys

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
    return {'auth': {'username': key_file['service_id'], 'password': key_file['service_key']}}


def list_broken_endpoints(confd_client):
    endpoints = []
    response = confd_client.lines.list()
    for line in response['items']:
        endpoint = line['endpoint_sip']
        if not endpoint:
            continue
        name = endpoint.get('name')
        auth_section_options = endpoint.get('auth_section_options', [])
        username = None
        for key, value in auth_section_options:
            if key == 'username':
                username = value
                break
        if name == username:
            continue
        endpoints.append(endpoint['uuid'])
    return endpoints


def fix_endpoint(confd_client, endpoint_uuid):
    endpoint = confd_client.endpoints_sip.get(endpoint_uuid)
    name = endpoint['name']
    auth_section_options = endpoint.get('auth_section_options', [])
    for key, value in auth_section_options:
        if key == 'username':
            auth_section_options.remove(['username', value])
    auth_section_options.append(['username', name])
    confd_client.endpoints_sip.update(endpoint)


def main(tenant_uuid):
    config = load_config()

    auth_client = AuthClient(**config['auth'])
    auth_client.set_tenant(tenant_uuid)
    token_data = auth_client.token.new(expiration=300)
    confd_client = ConfdClient(token=token_data['token'], **config['confd'])
    confd_client.set_tenant(tenant_uuid)

    endpoints_to_update = list_broken_endpoints(confd_client)
    print('updating', len(endpoints_to_update), 'endpoints')
    for endpoint_uuid in endpoints_to_update:
        print('.', end='')
        fix_endpoint(confd_client, endpoint_uuid)
    print('done')



if __name__ == '__main__':
    main(sys.argv[1])
