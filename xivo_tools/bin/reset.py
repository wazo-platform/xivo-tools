# -*- coding: UTF-8 -*-
#
# Copyright (C) 2014 Avencall
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
import logging
import subprocess

from xivo_tools.helpers.action import restart_xivo_services, sysconfd, \
    init_logging
from xivo.xivo_logging import DEFAULT_LOG_FORMAT


def main():
    parsed_args = _new_argument_parser()
    level = logging.DEBUG if parsed_args.debug else logging.INFO
    init_logging(DEFAULT_LOG_FORMAT, level=level)

    logging.info('Restarting postgresql')
    sysconfd('services', {'postgresql': 'restart'})
    logging.info('Initialazing database')
    subprocess.check_call(['xivo-init-db', '--drop', '--init'])
    logging.info('Cleaning provd')
    subprocess.check_call(['rm', '-rf', '/var/lib/xivo-provd/*'])
    logging.info('Restarting services')
    restart_xivo_services()


def _new_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', action='store_true',
                        dest='debug',
                        help='increase verbosity')
    return parser.parse_args()


if __name__ == '__main__':
    main()
