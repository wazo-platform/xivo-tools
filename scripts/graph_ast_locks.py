#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012-2014 Avencall
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
import re


def main():
    parsed_args = _parse_args()

    with open(parsed_args.filename) as fobj:
        threads = _parse_core_show_locks_fobj(fobj)

    lock_owned_by_thread = dict((lock, thread.id) for thread in threads for lock in thread.locks)

    print 'digraph G {'
    for thread in threads:
        if thread.is_locked():
            print '    "%s" -> "%s";' % (thread.id, lock_owned_by_thread[thread.waiting_lock])
    print '}'


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    return parser.parse_args()


_THREAD_REGEX = re.compile(r'^=== Thread ID: (\w+)')

def _parse_core_show_locks_fobj(fobj):
    threads = []
    current_thread = None
    for line in fobj:
        if line.startswith('=== ---> Lock'):
            lock_id = _get_lock_id(line)
            current_thread.locks.append(lock_id)
        elif line.startswith('=== ---> Waiting for Lock'):
            lock_id = _get_lock_id(line)
            current_thread.waiting_lock = lock_id
        else:
            m = _THREAD_REGEX.match(line)
            if m:
                thread_id = m.group(1)
                current_thread = _Thread(thread_id)
                threads.append(current_thread)
    return threads


def _get_lock_id(line):
    tokens = line.split(' ')
    return tokens[-2]


class _Thread(object):

    def __init__(self, thread_id):
        self.id = thread_id
        self.locks = []
        self.waiting_lock = None

    def is_locked(self):
        return self.waiting_lock is not None


if __name__ == '__main__':
    main()
