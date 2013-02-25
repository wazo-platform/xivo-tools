# -*- coding: utf-8 -*-

# Copyright (C) 2013 Avencall
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

import sys
from ctiproxy import core
from ctiproxy.bin import common


def _new_argument_parser():
    return common.new_argument_parser(add_help=True)


def _parse_args(args):
    parser = _new_argument_parser()
    parsed_args = parser.parse_args(args)
    return parsed_args


def _new_proxy_establisher(args):
    bind_address = (args.listen_addr, args.listen_port)
    server_address = (args.hostname, args.port)
    return core.IPv4ProxyEstablisher(bind_address, server_address)


@common.hide_exception(KeyboardInterrupt)
def main():
    args = _parse_args(sys.argv[1:])
    common.init_logging(args.verbose)
    
    stat_listener = core.StatisticListener()
    proxy_establisher = _new_proxy_establisher(args)
    try:
        csocket, ssocket = proxy_establisher.establish_connections()
        socket_proxy = core.SocketProxy(csocket, ssocket, stat_listener)
        socket_proxy.start()
    finally:
        proxy_establisher.close()
        stat_listener.print_stats()


if __name__ == "__main__":
    main()
