# -*- coding: utf-8 -*-

# Copyright (C) 2013-2014 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import argparse
import itertools
import logging
from ctiproxy import core

logger = logging.getLogger(__name__)


def main(parse_args, new_listener):
    parsed_args = parse_args()

    _init_logging(parsed_args)

    proxy_establisher = _new_proxy_establisher(parsed_args)
    try:
        loop_ctrl = _new_loop_ctrl(parsed_args)
        for _ in loop_ctrl:
            listener = new_listener(parsed_args)
            try:
                csocket, ssocket = proxy_establisher.establish_connections()
                socket_proxy = core.SocketProxy(csocket, ssocket, listener)
                socket_proxy.start()
            finally:
                listener.close()
    except KeyboardInterrupt:
        pass
    finally:
        proxy_establisher.close()


def _init_logging(parsed_args):
    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    root_logger.addHandler(handler)
    if parsed_args.verbose:
        root_logger.setLevel(logging.INFO)
    else:
        root_logger.setLevel(logging.ERROR)


def _new_proxy_establisher(parsed_args):
    bind_address = (parsed_args.listen_addr, parsed_args.listen_port)
    server_address = (parsed_args.hostname, parsed_args.port)
    return core.IPv4ProxyEstablisher(bind_address, server_address)


def _new_loop_ctrl(parsed_args):
    if parsed_args.loop:
        return itertools.repeat(True)
    else:
        return [True]


def new_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--listen-port', type=_port_number, default=5003,
                        help='bind to this port')
    parser.add_argument('--listen-addr', default='',
                        help='bind to this address')
    parser.add_argument('--port', type=_port_number, default=5003,
                        help='CTI server port number')
    parser.add_argument('--loop', action='store_true', default=False,
                        help='wait for another connection when one is closed')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='increase logging verbosity')
    parser.add_argument('hostname',
                        help='CTI server hostname')
    return parser


def _port_number(value):
    try:
        port = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError('%r is not a valid port number' % value)
    if port < 1 or port > 65535:
        raise argparse.ArgumentTypeError('%r is not a valid port number' % value)
    return port
