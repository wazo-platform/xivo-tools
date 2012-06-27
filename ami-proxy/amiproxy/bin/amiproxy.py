# -*- coding: UTF-8 -*-

from __future__ import absolute_import

import argparse
import logging
from amiproxy import core


def main():
    _init_logging()

    parsed_args = _parse_args()

    proxy_establisher = _new_proxy_establisher()
    try:
        if parsed_args.background:
            from xivo import daemonize
            daemonize.daemonize()

        while True:
            csocket, ssocket = proxy_establisher.establish_connections()
            socket_proxy = core.SocketProxy(csocket, ssocket)
            socket_proxy.start()
    finally:
        proxy_establisher.close()


def _parse_args():
    parser = _new_argument_parser()
    return parser.parse_args()


def _new_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--background', action='store_true')
    return parser


def _init_logging():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _new_proxy_establisher():
    bind_address = ('127.0.0.1', 5039)
    server_address = ('127.0.0.1', 5038)
    return core.IPv4ProxyEstablisher(bind_address, server_address)


if __name__ == "__main__":
    main()
