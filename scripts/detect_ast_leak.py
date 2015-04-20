#!/usr/bin/python
# -*- coding: UTF-8 -*-

import argparse
import collections
import itertools
import operator
import re
import sys


class Check(object):

    def __init__(self, name, alloc, destroy):
        self.name = name
        self._alloc = alloc
        self._destroy = destroy
        self._cache = {}

    def process(self, line):
        if self._check_alloc(line):
            return
        if self._check_destroy(line):
            return

    def _check_alloc(self, line):
        m = self._alloc.search(line)
        if m:
            obj_id = m.group(1)
            self._cache[obj_id] = line
            return True
        return False

    def _check_destroy(self, line):
        m = self._destroy.search(line)
        if m:
            obj_id = m.group(1)
            self._cache.pop(obj_id, None)
            return True
        return False

    def results(self):
        for obj_id, line in self._cache.iteritems():
            yield CheckResult(self.name, extract_date(line), obj_id)


class SIPDialogCheck(Check):

    _ALLOC = re.compile(r"chan_sip.c: Allocating new SIP dialog for ([^ ]+)")
    _DESTROY = re.compile(r"chan_sip.c: Destroying SIP dialog ([^ ]+)\b")

    def __init__(self, name):
        super(SIPDialogCheck, self).__init__(name, self._ALLOC, self._DESTROY)
        self._change = re.compile(r"chan_sip.c: SIP call-id changed from '([^']+)' to '([^']+)'")

    def process(self, line):
        if self._check_alloc(line):
            return
        if self._check_destroy(line):
            return
        if self._check_change(line):
            return

    def _check_change(self, line):
        m = self._change.search(line)
        if m:
            old_id, new_id = m.groups()
            self._cache.pop(old_id, None)
            self._cache[new_id] = line
            return True
        return False


CheckResult = collections.namedtuple('CheckResult', ['name', 'date', 'obj_id'])


def new_rtp_instance_check():
    # need "core set debug 1 core"
    return Check(
        'RTP instance',
        re.compile(r"rtp_engine.c: Using engine 'asterisk' for RTP instance '(\w+)"),
        re.compile(r"rtp_engine.c: Destroyed RTP instance '(\w+)'"),
    )


def new_sip_dialog_check():
    # need "core set debug 3 chan_sip"
    return SIPDialogCheck('SIP dialog')


def main():
    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('--rtp', action='store_true',
                        help='enable ast_rtp_instance check')
    parser.add_argument('--sip', action='store_true',
                        help='enable sip_pvt check')
    parsed_args = parser.parse_args()

    # instantiate checks
    checks = []
    if parsed_args.rtp:
        checks.append(new_rtp_instance_check())
    if parsed_args.sip:
        checks.append(new_sip_dialog_check())
    if not checks:
        print >>sys.stderr, 'No check enabled. Exiting'
        sys.exit(1)

    # process stdin
    fobj = sys.stdin

    first_line = fobj.next()
    for check in checks:
        check.process(first_line)

    for line in fobj:
        for check in checks:
            check.process(line)
    last_line = line

    # display results
    check_results = sorted(itertools.chain.from_iterable(c.results() for c in checks), key=operator.attrgetter('date'))

    print '{} First log line'.format(extract_date(first_line))
    for check_result in check_results:
        print '{} {} {}'.format(check_result.date, check_result.name, check_result.obj_id)
    print '{} Last log line'.format(extract_date(last_line))


def extract_date(line):
    return line[:17]


if __name__ == '__main__':
    main()
