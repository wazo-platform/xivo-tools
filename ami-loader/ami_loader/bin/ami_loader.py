# -*- coding: UTF-8 -*-

from __future__ import absolute_import

import argparse
import logging
import time
import sys
from ami_loader.ami import AMIClient


def main():
    _init_logging()

    parsed_args = _parse_args(sys.argv[1:])

    if parsed_args.verbose:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

    ami_client = AMIClient(parsed_args.hostname)
    ami_client.connect()
    ami_client.wait_recv()

    ami_client.action_login(parsed_args.username, parsed_args.password)
    ami_client.wait_recv()

    try:
        while True:
            #ami_client.action_core_show_channels()
            ami_client.action_status("SIP/abcdef-000001")
            ami_client.flush_recv()
            time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    #ami_client.action_command('module reload')
    #ami_client.action_show_dialplan()
    #ami_client.action_agent_logoff('9215')
    #ami_client.action_agent_callback_login('9215', 'default', '1215')
    #ami_client.wait_recv()

    ami_client.wait_recv(0.5)
    ami_client.disconnect()


def _init_logging():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _parse_args(args):
    parser = _new_argument_parser()
    return parser.parse_args(args)


def _new_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', default='xivo_cti_user',
                        help='authentication username')
    parser.add_argument('-p', '--password', default='phaickbebs9',
                        help='authentication password')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='increase verbosity')
    parser.add_argument('hostname',
                        help='AMI server hostname')
    return parser
