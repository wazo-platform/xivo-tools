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

from ctiproxy import core
from ctiproxy.bin import common


def main():
    common.main(_parse_args, _new_listener)


def _parse_args():
    parser = common.new_argument_parser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-m', '--msg', action='store_true',
                       help='message stats')
    group.add_argument('-n', '--network', action='store_true',
                       help='network stats')
    return parser.parse_args()


def _new_listener(parsed_args):
    if parsed_args.network:
        listener = core.StatisticListener()
    else:
        listener = core.StatisticMsgListener()
        listener = core.JsonDecoderListener(listener)
        listener = core.NewlineSplitListener(listener)
    return listener


if __name__ == '__main__':
    main()
