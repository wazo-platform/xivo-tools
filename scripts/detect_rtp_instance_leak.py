#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
# For this script to work, asterisk core debug must at least be 1, i.e
#
#   asterisk -rx "core set debug 1 core"
#

import re
import sys

REGEX = re.compile(r"RTP instance '(\w+)'")


def main():
    fobj = sys.stdin

    first_line = fobj.next()
    result = process(fobj)

    print '{} First log line'.format(extract_date(first_line))
    for instance_id, line in result.iteritems():
        print '{} RTP instance {} never destroyed'.format(extract_date(line), instance_id)


def process(fobj):
    result = {}
    for line in fobj:
        if 'rtp_engine.c: Using engine' in line:
            instance_id = extract_instance_id(line)
            result[instance_id] = line
        elif 'rtp_engine.c: Destroyed' in line:
            instance_id = extract_instance_id(line)
            result.pop(instance_id, None)
    return result


def extract_instance_id(line):
    return REGEX.search(line).group(1)


def extract_date(line):
    return line[:17]


if __name__ == '__main__':
    main()
