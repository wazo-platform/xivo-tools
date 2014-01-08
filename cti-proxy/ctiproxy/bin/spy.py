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

from ctiproxy import core
from ctiproxy.bin import common


def main():
    common.main(_parse_args, _new_listener)


def _parse_args():
    parser = common.new_argument_parser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--no-client', action='store_true', default=False,
                       help='don\'t display messages from client')
    group.add_argument('--no-server', action='store_true', default=False,
                       help='don\'t display messages from server')
    parser.add_argument('--raw', action='store_true', default=False,
                        help='display raw messages')
    parser.add_argument('--pretty-print', action='store_true', default=False,
                        help='pretty print messages')
    parser.add_argument('-s', '--strip', action='append',
                        help='strip the given fields from messages')
    parser.add_argument('-i', '--include', action='store',
                        help='include only the given messages')
    parser.add_argument('-e', '--exclude', action='store',
                        help='exclude the given messages')
    return parser.parse_args()


def _new_listener(parsed_args):
    if parsed_args.raw:
        listener = core.RawPrintListener()
    else:
        listener = core.PrintMsgListener(parsed_args.pretty_print)
        if parsed_args.strip:
            listener = core.StripListener(listener, parsed_args.strip)
        if parsed_args.include:
            key, value = parsed_args.include.split('=', 1)
            listener = core.IncludeListener(listener, key, value)
        if parsed_args.exclude:
            key, value = parsed_args.exclude.split('=', 1)
            listener = core.ExcludeListener(listener, key, value)
        listener = core.JsonDecoderListener(listener)
        listener = core.NewlineSplitListener(listener)
    if parsed_args.no_client:
        listener = core.NoClientListener(listener)
    elif parsed_args.no_server:
        listener = core.NoServerListener(listener)
    return listener


if __name__ == '__main__':
    main()
