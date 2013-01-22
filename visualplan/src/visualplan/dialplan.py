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

import re


class DialplanParsingError(Exception):
    pass


class DialplanParser(object):
    def parse(self, fobj):
        parse_result = self._do_parse(fobj)
        parse_result.filename = '<fobj>'
        return parse_result

    def parse_file(self, filename):
        with open(filename) as fobj:
            parse_result = self._do_parse(fobj)
        parse_result.filename = filename
        return parse_result

    def _do_parse(self, fobj):
        parse_result = _DialplanParseResult()
        line_parser = _DialplanLineParser()
        for dialplan_line in fobj:
            line_parser.parse_next_line(dialplan_line)
            line = _DialplanLineParseResult(dialplan_line.rstrip('\n'),
                                            line_parser.is_executable)
            if line_parser.is_executable:
                line.context = line_parser.context
                line.extension = line_parser.extension
                line.priority = line_parser.priority
                parse_result._add_extension(line_parser.context, line_parser.extension)
            parse_result.lines.append(line)
        return parse_result


class _DialplanLineParser(object):
    def __init__(self):
        self.context = None
        self.extension = None
        self.priority = None
        self.is_executable = False

    _CONTEXT_REGEX = re.compile(r'^\[([a-zA-Z0-9_\-]+)\]')
    _EXTEN_REGEX = re.compile(r'^exten\s*=\s*([^,]+),(n|\d+)')
    _SAME_REGEX = re.compile(r'^same\s*=\s*(n|\d+)')

    def parse_next_line(self, line):
        stripped_line = line.strip()
        if not stripped_line:
            # blank line
            self.is_executable = False
        elif stripped_line.startswith(';'):
            # comment line
            self.is_executable = False
        elif self._try_parse_context_line(stripped_line):
            self.is_executable = False
        elif self._try_parse_extension_line(stripped_line):
            self.is_executable = True
        elif self._try_parse_same_line(stripped_line):
            self.is_executable = True
        else:
            # unknown line, probably an include or an #exec
            self.is_executable = False

    def _try_parse_context_line(self, stripped_line):
        mo = self._CONTEXT_REGEX.match(stripped_line)
        if mo:
            self.context = mo.group(1)
            self.extension = None
            self.priority = None
            return True

    def _try_parse_extension_line(self, stripped_line):
        mo = self._EXTEN_REGEX.match(stripped_line)
        if mo:
            if self.context is None:
                raise DialplanParsingError('extension defined outside a context')
            self.extension = mo.group(1)
            new_priority = mo.group(2)
            self._adjust_priority(new_priority)
            return True

    def _adjust_priority(self, new_priority):
        if new_priority == 'n':
            if self.priority is None:
                raise DialplanParsingError('n priority used before explicit priority')
            self.priority += 1
        else:
            self.priority = int(new_priority)

    def _try_parse_same_line(self, stripped_line):
        mo = self._SAME_REGEX.match(stripped_line)
        if mo:
            if self.context is None:
                raise DialplanParsingError('extension defined outside a context')
            if self.extension is None:
                raise DialplanParsingError('same extension before explicit extension')
            new_priority = mo.group(1)
            self._adjust_priority(new_priority)
            return True


class _DialplanParseResult(object):
    def __init__(self):
        self.lines = []
        self._contexts = {}

    def _add_extension(self, context, extension):
        self._contexts.setdefault(context, set()).add(extension)

    def has_extension(self, context, extension):
        return extension in self._contexts.get(context, ())


class _DialplanLineParseResult(object):
    def __init__(self, content, is_executable):
        self.content = content
        self.is_executable = is_executable
