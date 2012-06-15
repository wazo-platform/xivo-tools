# -*- coding: UTF-8 -*-

from __future__ import absolute_import

import argparse
import logging
import time
import sys
from ami_loader.ami import AMIClient


def main():
    logging.basicConfig(level=logging.INFO)

    parsed_args = _parse_args(sys.argv[1:])

    ami_client = AMIClient(parsed_args.hostname)
    ami_client.connect()
    ami_client.wait_recv()

    ami_client.action_login(parsed_args.username, parsed_args.password)
    ami_client.wait_recv()

    try:
        while True:
            ami_client.action_core_show_channels()
            ami_client.flush_recv()
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    #ami_client.action_command('module reload')
    #ami_client.action_show_dialplan()
    #ami_client.wait_recv()

    ami_client.wait_recv(0.5)
    ami_client.disconnect()


def _parse_args(args):
    parser = _new_argument_parser()
    return parser.parse_args(args)


def _new_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', default='xivo_cti_user',
                        help='authentication username')
    parser.add_argument('-p', '--password', default='phaickbebs9',
                        help='authentication password')
    parser.add_argument('hostname',
                        help='AMI server hostname')
    return parser
