# -*- coding: utf-8 -*-

import requests
import json
from pprint import pprint


URL = 'https://skaro-rc.lan-quebec.avencall.com:50051/1.1'
USERNAME = 'admin'
PASSWORD = 'proformatique'

USERS = ['Mufasa Rawr', 'Simba King']
EXTENSION = '1201'

auth = requests.auth.HTTPDigestAuth(USERNAME, PASSWORD)
headers = {'Accept': 'application/json',
           'Content-Type': 'application/json'}

session = requests.Session()
session.auth = auth
session.headers = headers
session.verify = False


def check_status(response):
    if response.status_code >= 300:
        raise Exception("STATUS %s. %s" % (response.status_code, response.text))
    return response


def request(verb, url, params=None):
    fullurl = '%s/%s' % (URL, url)

    method = getattr(session, verb)

    if params:
        response = method(fullurl, json.dumps(params))
    else:
        response = method(fullurl)

    check_status(response)
    return response.json()


def find_users():
    users = request('get', 'users')['items']

    found = [u for u in users
             if '%s %s' % (u['firstname'], u['lastname']) in USERS]

    user_names = ['%s %s' % (u['firstname'], u['lastname']) for u in found]

    if len(found) != len(USERS):
        raise Exception("only found the following users: %s" % ', '.join(user_names))

    return reorder_users(USERS, found)


def reorder_users(order, users):
    stash = dict(
        ('%s %s' % (u['firstname'], u['lastname']), u)
        for u in users)

    return [stash[name] for name in order]


def find_or_create_extension():
    extensions = request('get', 'extensions')['items']

    found = [e for e in extensions if e['exten'] == EXTENSION]
    if not found:
        return create_extension()

    return found[0]


def create_extension():
    extension = {
        'exten': EXTENSION,
        'context': 'default',
    }

    return request('post', 'extensions', extension)


def find_or_create_line(users, extension):
    user_links = find_user_links(users, extension)
    if not user_links:
        return create_line()

    line_ids = set(u['line_id'] for u in user_links)
    if len(line_ids) > 1:
        raise Exception("More than one line associated to users and extension (%s)" % line_ids)

    line_id = line_ids.pop()

    return request('get', 'lines_sip/%s' % line_id)


def create_line():
    line = {
        'context': 'default',
        'device_slot': 1,
    }

    return request('post', 'lines_sip', line)


def find_user_links(users, extension):
    user_ids = [u['id'] for u in users]

    user_links = request('get', 'user_links')['items']

    found = [u for u in user_links
             if u['user_id'] in user_ids and u['extension_id'] == extension['id']]

    return found


def find_or_create_links(users, extension, line):
    user_links = find_user_links(users, extension)

    if not user_links:
        return create_user_links(users, extension, line)

    if len(user_links) != len(USERS):
        raise Exception("not the same number of links as users")

    return user_links


def create_user_links(users, extension, line):
    created_links = []

    for user in users:
        link = {
            'user_id': user['id'],
            'line_id': line['id'],
            'extension_id': extension['id']
        }

        created_links.append(request('post', 'user_links', link))

    return created_links


def main():
    print "finding users"
    users = find_users()
    pprint(users)
    print

    print "finding extension"
    extension = find_or_create_extension()
    pprint(extension)
    print

    print "finding line"
    line = find_or_create_line(users, extension)
    pprint(line)
    print

    print "finding links"
    links = find_or_create_links(users, extension, line)
    pprint(links)
    print

    main_user = users[0]
    print "Done. Provisining code for %s %s is %s" % (main_user['firstname'], main_user['lastname'], line['provisioning_extension'])

if __name__ == '__main__':
    main()
