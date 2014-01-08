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
import sys
from visualplan.analyzer import DialplanExecutionAnalyzer
from visualplan.log import LogParser
from visualplan.dialplan import DialplanParser
from visualplan.html import HTMLVisualizer


def main():
    parsed_args = _parse_args(sys.argv[1:])

    log_parser = LogParser()
    dialplan_parser = DialplanParser()
    dialplan_analyzer = DialplanExecutionAnalyzer()

    log_parse_result = log_parser.parse_file(parsed_args.log_file)
    analyses = []
    for diaplan_file in parsed_args.dialplan_files:
        dialplan_parse_result = dialplan_parser.parse_file(diaplan_file)
        analyses.append(dialplan_analyzer.analyze(dialplan_parse_result, log_parse_result))

    visualizer = HTMLVisualizer('visualplan.html')
    visualizer.write(analyses)


def _parse_args(args):
    parser = _new_argument_parser()
    return parser.parse_args(args)


def _new_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('log_file',
                        help='asterisk log file')
    parser.add_argument('dialplan_files', nargs='+',
                        help='dialplan files')
    return parser


if __name__ == '__main__':
    main()
