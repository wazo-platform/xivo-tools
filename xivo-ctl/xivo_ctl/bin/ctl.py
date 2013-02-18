# -*- coding: utf-8 -*-

# Copyright (C) 2013  Avencall
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

from __future__ import unicode_literals

import argparse
from xivo.cli import Interpreter
from xivo_ctl.command import user
from xivo_ws import XivoServer


def main():
    parsed_args = _parse_args()

    xivo_server = XivoServer(parsed_args.hostname, parsed_args.username, parsed_args.password)

    interpreter = Interpreter(prompt='xivo-ctl> ',
                              history_file='~/.xivoctl_history')
    interpreter.add_command('users add', user.UsersAddCommand(xivo_server))
    interpreter.add_command('users delete', user.UsersDeleteCommand(xivo_server))
    interpreter.add_command('users list', user.UsersListCommand(xivo_server))
    interpreter.add_command('users mass add', user.UsersMassAddCommand(xivo_server))
    interpreter.add_command('users mass delete', user.UsersMassDeleteCommand(xivo_server))

    if parsed_args.command:
        interpreter.execute_command_line(parsed_args.command)
    else:
        interpreter.loop()


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--command',
                        help='run command')
    parser.add_argument('-u', '--username',
                        help='authentication username')
    parser.add_argument('-p', '--password',
                        help='authentication password')
    parser.add_argument('hostname',
                        help='hostname of xivo server')
    return parser.parse_args()


if __name__ == '__main__':
    main()
