#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import csv
import sys
from provd.rest.client.client import new_provisioning_client

FIELDS = [u'id', u'mac', u'ip', u'vendor', u'model', u'version', u'config', u'plugin']


def main():
    parsed_args = parse_args()

    provd_client = new_provisioning_client(parsed_args.url)
    dev_mgr = provd_client.device_manager()

    devices = dev_mgr.find()

    writer = csv.writer(sys.stdout)
    writer.writerow([f.encode('utf-8') for f in FIELDS])
    for device in devices:
	writer.writerow([device.get(f, u'').encode('utf-8') for f in FIELDS])


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8666/provd',
                        help='xivo-provd base URL')
    return parser.parse_args()


main()
