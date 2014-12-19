#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# How to use it:
#
# On your XiVO, copy this file in /usr/local/bin and make sure it is executable
# by everyone.
#
# Then, edit /etc/asterisk/sccp.conf and add the following line near the end:
#
#    #exec sccp_conf_timezone.py --quiet

import argparse
import itertools
import shutil
import sys
from provd.rest.client.client import new_provisioning_client

MODELS = [u'7912G', u'7920', u'7940G', u'7960G']


def main():
    parsed_args = parse_args()

    try:
        devices, configs = get_provd_devices_and_configs(parsed_args)
    except Exception:
        if parsed_args.quiet:
            print_cache(parsed_args)
            sys.exit(0)
        else:
            raise

    configs_by_id = dict((c[u'id'], c) for c in configs)

    writer = new_writer(parsed_args)
    for device in filter_devices(devices):
        timezone = get_config_timezone(configs_by_id, device[u'config'])
        if not timezone:
            continue

        print_device_section(writer, device[u'mac'], timezone)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8666/provd',
                        help='xivo-provd base URL')
    parser.add_argument('--cache', default='/etc/asterisk/sccp-conf-timezone.cache')
    parser.add_argument('--quiet', action='store_true')
    return parser.parse_args()


def get_provd_devices_and_configs(parsed_args):
    provd_client = new_provisioning_client(parsed_args.url)
    dev_mgr = provd_client.device_manager()
    cfg_mgr = provd_client.config_manager()

    devices = dev_mgr.find()
    configs = cfg_mgr.find()
    return devices, configs


def print_cache(parsed_args):
    try:
        fobj = open(parsed_args.cache)
    except Exception:
        if parsed_args.quiet:
            sys.exit(1)
        else:
            raise

    with fobj:
        shutil.copyfileobj(fobj, sys.stdout)


def filter_devices(devices):
    return itertools.ifilter(_test_device, devices)


def _test_device(device):
    for key in [u'mac', u'plugin', u'config']:
        if key not in device:
            return False

    if not device[u'plugin'].startswith(u'xivo-cisco-sccp'):
        return False

    if device[u'config'].startswith(u'autoprov'):
        return False

    if u'model' in device and device[u'model'] not in MODELS:
        return False

    return True


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


def new_writer(parsed_args):
    try:
        cache_fobj = open(parsed_args.cache, 'w')
    except Exception:
        if parsed_args.quiet:
            return sys.stdout
        else:
            raise

    return _MultiWriter([sys.stdout, cache_fobj])


class _MultiWriter(object):

    def __init__(self, file_objects):
        self._file_objects = file_objects

    def write(self, str):
        for fobj in self._file_objects:
            fobj.write(str)


def print_device_section(writer, mac, timezone):
    print >>writer, '[SEP%s](+)' % mac.upper().replace(':', '')
    print >>writer, 'timezone =', timezone
    print >>writer


main()
