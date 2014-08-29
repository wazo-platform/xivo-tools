#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
from provd.rest.client.client import new_provisioning_client

MODELS = [u'', u'7912G', u'7920', u'7940G', u'7960G']


def main():
    parsed_args = parse_args()

    provd_client = new_provisioning_client(parsed_args.url)
    dev_mgr = provd_client.device_manager()
    cfg_mgr = provd_client.config_manager()

    devices = dev_mgr.find()
    configs = cfg_mgr.find()
    configs_by_id = dict((c[u'id'], c) for c in configs)

    for device in filter_devices(devices):
        timezone = get_config_timezone(configs_by_id, device.get(u'config'))
        if not timezone:
            continue

        print_device_section(device[u'mac'], timezone)


def filter_devices(devices):
    for device in devices:
        if (u'mac' in device and
            device.get(u'plugin', u'').startswith(u'xivo-cisco-sccp') and
            device.get(u'model', u'') in MODELS):
            yield device


def get_config_timezone(configs_by_id, config_id):
    config = configs_by_id.get(config_id)
    if not config:
        return None

    timezone = config[u'raw_config'].get(u'timezone')
    if timezone:
        return timezone

    for parent_config_id in config[u'parent_ids']:
        timezone = get_config_timezone(configs_by_id, parent_config_id)
        if timezone:
            return timezone

    return None


def print_device_section(mac, timezone):
    print '[SEP%s](+)' % mac.upper().replace(':', '')
    print 'timezone =', timezone
    print


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8666/provd',
                        help='xivo-provd base URL')
    return parser.parse_args()


main()
