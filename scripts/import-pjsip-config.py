#!/usr/bin/env python3
# Copyright 2020 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import sys
import argparse
import configparser
import os

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
IGNORED_OPTIONS = [
    'endpoint',
]


def load_config():
    file_config = read_config_file_hierarchy(_DEFAULT_CONFIG)
    key_config = _load_key_file(ChainMap(file_config, _DEFAULT_CONFIG))
    return ChainMap(key_config, file_config, _DEFAULT_CONFIG)


def _load_key_file(config):
    key_file = parse_config_file(config['auth']['key_file'])
    return {'auth': {'username': key_file['service_id'],
                     'password': key_file['service_key']}}



argument_parser = argparse.ArgumentParser(
    'Import an Asterisk pjsip configuration file',
)
argument_parser.add_argument('filename', help='The file to import')


def migrate_section(confd_client, block_name, options):
    # if the names is reg_<endpoint_name>@host we are in a registration section
    if not block_name or 'reg_' not in block_name or '@' not in block_name:
        print('ignoring', block_name, 'invalid section, only registration sections can be overridden')
        return

    endpoint_name = None
    section = 'registration_section_options'

    to_add = []
    for key, value in options.items():
        if key == 'type':
            section = '{}_section_options'.format(value)
        elif key == 'endpoint':
            endpoint_name = value
        else:
            to_add.append([key, value])

    if not to_add:
        print('ignoring', block_name, 'nothing to add')
        return

    if section is None or endpoint_name is None:
        print('ignoring', block_name, 'missing section or endpoint information')
        return

    response = confd_client.endpoints_sip.list(name=endpoint_name, recurse=True)
    if response['total'] == 0:
        print('ignoring', block_name, 'no matching endpoints')
        return
    elif response['total'] > 1:
        print('ignoring', block_name, 'multiple endpoint match this name')
        return

    endpoint = response['items'][0]
    endpoint[section] += to_add

    print('updating', endpoint['name'])
    try:
        confd_client.endpoints_sip.update(endpoint)
    except HTTPError as e:
        print('ignoring', block_name, 'see error message below')
        print(e)
        return


def main():
    config = load_config()
    args = argument_parser.parse_args()
    print('Importing', args.filename)

    if not os.path.exists(args.filename):
        print('No such file or directory', args.filename)
        sys.exit(1)

    auth_client = AuthClient(**config['auth'])
    token_data = auth_client.token.new(expiration=300)
    confd_client = ConfdClient(token=token_data['token'], **config['confd'])

    content = configparser.ConfigParser()
    content.read(args.filename)

    if not content.sections():
        print('Nothing to import')
        sys.exit(0)

    for section in content.sections():
        migrate_section(confd_client, section, content[section])


if __name__ == '__main__':
    main()
