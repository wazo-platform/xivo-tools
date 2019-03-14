#!/usr/bin/env python3
# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import os
import sys

from pprint import pprint
from xivo_confd_client import Client as ConfdClient


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-H',
        '--hostname',
        default='localhost',
        help='Hostname of the Wazo server',
    )
    parser.add_argument(
        '-t',
        '--token',
        help='The token to use for the import (defaults to the WAZO_TOKEN environment var)',
        default=os.getenv('WAZO_TOKEN', None),
    )
    parser.add_argument(
        'filename',
        help='The CSV filename',
    )
    return parser.parse_args()


def csv_import(client, filename):
    with open(filename, 'r') as f:
        return client.users.import_csv(f.read())


def main():
    args = parse_args()
    print('Importing {} on {} using token {}'.format(args.filename, args.hostname, args.token))
    if not args.token:
        print('A token is required use -t or set the WAZO_TOKEN environment variable')
        sys.exit(1)

    client = ConfdClient(
        args.hostname,
        port=443,
        token=args.token,
        verify_certificate=False,
        prefix='api/confd',
    )

    result = csv_import(client, args.filename)

    pprint(result)


if __name__ == '__main__':
    main()
