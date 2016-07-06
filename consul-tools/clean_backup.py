#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2016 by Avencall
# SPDX-License-Identifier: GPL-3.0+

import json
import sys


def main():
    filename = sys.argv[1]
    with open(filename, 'r') as f:
        index, entries = json.load(f)

    new_entries = []
    user_personal_contacts = {}
    count, skip, dup, perso = 0, 0, 0, 0
    for entry in entries:
        count += 1
        key = entry.get('Key')

        if 'personal' not in key:
            new_entries.append(entry)
            continue
        try:
            _, __, user, ___, ____, contact_uuid, field = key.split('/')
        except ValueError:
            print 'Error', key
            continue

        if user not in user_personal_contacts:
            user_personal_contacts[user] = {}
        if contact_uuid not in user_personal_contacts[user]:
            user_personal_contacts[user][contact_uuid] = {}
        if field not in user_personal_contacts[user][contact_uuid]:
            user_personal_contacts[user][contact_uuid][field] = (entry.get('Value'), entry)

    for user, contacts in user_personal_contacts.iteritems():
        unique_contacts = set()
        for uuid, fields in contacts.iteritems():
            perso += 1
            this_contact = []
            for fieldname, values in fields.iteritems():
                if fieldname != 'id':
                    this_contact.append((fieldname, values[0]))
            sorted_contact = tuple(sorted(this_contact))
            if sorted_contact in unique_contacts:
                dup += 1
                skip += len(fields)
                continue
            unique_contacts.add(sorted_contact)
            for values in fields.itervalues():
                new_entries.append(values[1])

    new_filename = '{}-new'.format(filename)
    with open(new_filename, 'w') as f:
        json.dump([index, new_entries], f)

    print 'Backup cleanup complete: {}/{} KV have been removed'.format(skip, count)
    print 'Duplicate personal contacts {}/{}'.format(dup, perso)

if __name__ == '__main__':
    main()
