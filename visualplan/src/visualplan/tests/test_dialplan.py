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

import unittest
from io import StringIO
from visualplan.dialplan import DialplanParser


class TestDialplanParser(unittest.TestCase):
    def _parse_content(self, content):
        fobj = StringIO(content)
        parser = DialplanParser()
        return parser.parse(fobj)

    def _parse_lines(self, lines):
        content = '\n'.join(lines) + '\n'
        parse_result = self._parse_content(content)
        return parse_result.lines

    def _assert_same_lines_content(self, lines, parsed_lines):
        self.assertEqual(len(lines), len(parsed_lines))
        for line, parsed_line in zip(lines, parsed_lines):
            self.assertEqual(line, parsed_line.content)

    def _assert_is_not_executable(self, parsed_line):
        self.assertFalse(parsed_line.is_executable)

    def _assert_is_executable(self, parsed_line, context, extension, priority):
        self.assertTrue(parsed_line.is_executable)
        self.assertEqual(context, parsed_line.context)
        self.assertEqual(extension, parsed_line.extension)
        self.assertEqual(priority, parsed_line.priority)

    def test_parse_empty_file(self):
        content = ''

        parse_result = self._parse_content(content)

        self.assertEqual(0, len(parse_result.lines))

    def test_parse_blank_line(self):
        lines = ['  ']

        parsed_lines = self._parse_lines(lines)

        self._assert_same_lines_content(lines, parsed_lines)
        self.assertFalse(parsed_lines[0].is_executable)

    def test_parse_comment_line(self):
        lines = ['; this is a comment  ']

        parsed_lines = self._parse_lines(lines)

        self._assert_same_lines_content(lines, parsed_lines)
        self._assert_is_not_executable(parsed_lines[0])

    def test_parse_context_line_with_comment(self):
        lines = ['[abc_def-1]  ; context ']

        parsed_lines = self._parse_lines(lines)

        self._assert_same_lines_content(lines, parsed_lines)
        self._assert_is_not_executable(parsed_lines[0])

    def test_parse_exten_with_number_priority_line(self):
        lines = ['[test]',
                 'exten = s,1,NoOp()']

        parsed_lines = self._parse_lines(lines)

        self._assert_same_lines_content(lines, parsed_lines)
        self._assert_is_executable(parsed_lines[1], 'test', 's', 1)

    def test_parse_exten_with_n_priority_line(self):
        lines = ['[test]',
                 'exten = s,1,NoOp()',
                 'exten = s,n,NoOp()']

        parsed_lines = self._parse_lines(lines)

        self._assert_same_lines_content(lines, parsed_lines)
        self._assert_is_executable(parsed_lines[2], 'test', 's', 2)

    def test_parse_exten_with_label_line(self):
        lines = ['[test]',
                 'exten = s,1(foo),NoOp()']

        parsed_lines = self._parse_lines(lines)

        self._assert_same_lines_content(lines, parsed_lines)
        self._assert_is_executable(parsed_lines[1], 'test', 's', 1)

    def test_parse_same_with_number_priority_line(self):
        lines = ['[test]',
                 'exten = s,1,NoOp()',
                 'same  =   2,NoOp()']

        parsed_lines = self._parse_lines(lines)

        self._assert_same_lines_content(lines, parsed_lines)
        self._assert_is_executable(parsed_lines[2], 'test', 's', 2)

    def test_parse_same_with_n_priority_line(self):
        lines = ['[test]',
                 'exten = s,1,NoOp()',
                 'same  =   n,NoOp()']

        parsed_lines = self._parse_lines(lines)

        self._assert_same_lines_content(lines, parsed_lines)
        self._assert_is_executable(parsed_lines[2], 'test', 's', 2)

    def test_parse_same_with_label_line(self):
        lines = ['[test]',
                 'exten = s,1,NoOp()',
                 'same  =   n(foo),NoOp()']

        parsed_lines = self._parse_lines(lines)

        self._assert_same_lines_content(lines, parsed_lines)
        self._assert_is_executable(parsed_lines[2], 'test', 's', 2)

    def test_parse_file_return_result_with_filename(self):
        filename = '/dev/null'

        parse_result = DialplanParser().parse_file(filename)

        self.assertEqual(filename, parse_result.filename)

    def test_has_extension(self):
        content = """\
[test]
exten = s,1,NoOp()
"""

        parse_result = self._parse_content(content)

        self.assertTrue(parse_result.has_extension('test', 's'))
        self.assertFalse(parse_result.has_extension('test', 'foo'))
        self.assertFalse(parse_result.has_extension('foo', 's'))
