#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import csv
import json
import urllib2
import urllib
import sys

# TODO:
#   - lower case the MAC address in the CSV file before using it

URI_USERS = '/service/ipbx/json.php/%s/pbx_settings/users/'
URI_DEVICES = '/service/ipbx/json.php/%s/pbx_settings/devices/'
COLUMNS = ['phonenumber', 'mac']

## VARS
XIVO="10.152.8.251"
# XXX: there is an authenticaation problem (auth is lost (?) after two or three operations)
#   For now you MUST create a ws user authenticated BY IP and WITHOUT username/password 
USERNAME=None
PASSWORD=None


"""
Webservice basic class
"""
class WebServicesResponse(object):
    def __init__(self, url, code, data):
        self.url = url
        self.code = code
        self.data = data

class WebServices(object):
    def __init__(self, uri_prefix, uri_suffix, ws_username, ws_password):
        self._wsr = None
        self._path = self._compute_path(uri_prefix, uri_suffix)
        self._uri_prefix = uri_prefix
        self._uri_suffix = uri_suffix
        self._ws_username = ws_username
        self._ws_password = ws_password
        self._opener = self._build_opener(self._ws_username, self._ws_password)
        self._headers = {"Content-type": "application/json",
                         "Accept": "text/plain"}

    def _compute_path(self, uri_prefix, uri_suffix):
        if 'localhost' in uri_prefix or '127.0.0.1' in uri_prefix:
            method = 'private'
        else:
            method = 'restricted'

        return uri_suffix % method

    def _request_http(self, qry, data=None):
        if isinstance(data, dict):
            data = json.dumps(data)
        url = '%s%s?%s' % (self._uri_prefix, self._path, self._build_query(qry))
        request = urllib2.Request(url=url, data=data, headers=self._headers)
        handle = self._opener.open(request)
        try:
            self._wsr = WebServicesResponse(url, handle.code, handle.read())
        finally:
            handle.close()
        return self._wsr

    def _build_opener(self, username, password):
        handlers = []
        if username is not None or password is not None:
            pwd_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            pwd_manager.add_password(None, self._uri_prefix, username, password)
            handlers.append(urllib2.HTTPBasicAuthHandler(pwd_manager))
        return urllib2.build_opener(*handlers)

    def _build_query(self, qry):
        return urllib.urlencode(qry)

    def _get_path(self):
        return self._path

    def add(self, content):
        qry = {"act": "add"}
        return self._request_http(qry, content)

    def list(self):
        qry = {"act": "list"}
        return self._request_http(qry)

    def edit(self, content, id):
        qry = {"act": "edit", "id": id}
        return self._request_http(qry, content)

    def view(self, id):
        qry = {"act": "view", "id": id}
        return self._request_http(qry)

    def search(self, search):
        qry = {"act": "search", "search": search}
        return self._request_http(qry)

    def delete(self, id):
        qry = {"act": "delete", "id": id}
        return self._request_http(qry)

    def deleteall(self):
        qry = {"act": "deleteall"}
        return self._request_http(qry)

"""
Decode JSON from webservices
"""
#XXX: no error handling :)
def decode_ws_response(resp):
    if resp.code == 200:
        return json.loads(resp.data)
    if resp.code == 404:
        return "ERROR404"

"""
Function which parse args from standard input
"""
def _parse_args():
    parser = argparse.ArgumentParser()
    #    parser.add_argument('-u', '--username',
    #                        help='authentication username')
    #    parser.add_argument('-p', '--password',
    #                        help='authentication password')
    #    parser.add_argument('-H', '--hostname', default='localhost',
    #                        help='hostname of xivo server')
    parser.add_argument('csv_file',
                        help='csv filename')
    return parser.parse_args()

def convert_row_to_dict(row):
    return dict(zip(COLUMNS, map(lambda s: s.decode('UTF-8'), row)))

"""
Function which does the actual job :
    - fetching devices and creating a dict mac -> id,
    - reading the csv file,
    - for each line, 
        - find the user id and get the user parameters,
        - modify the line parameter to associate it to a device
        - edit the user
"""
def edit_users(user_ws, device_ws, filename):
    print 'Fetching devices list...'
    devices = decode_ws_response(device_ws.list())
    if devices is None:
        print '''Error: no devices on this XiVO.\
                \nDevices must first be created by provd before being able to associate a user to a device.'''
        sys.exit(1)
    else:
        device_id_by_mac = dict((device['devicefeatures']['mac'], device['devicefeatures']['id']) for device in devices)

    print 'Reading file %s...' % filename
    with open(filename, 'rb') as fobj:
        reader = csv.reader(fobj, delimiter=',')
        for row in reader:
            row_dict = convert_row_to_dict(row)
            if row_dict['mac'] not in device_id_by_mac:
                print '''Warn: no device with mac %s was found on XiVO \
                        \nUser with phonenumber %s is associated with device %s but no device with mac %s was found on XiVO''' \
                        % (row_dict['mac'], row_dict['phonenumber'], row_dict['mac'], row_dict['mac'])
                continue
            else:
                # Get user id which has this phonenumber
                my_user = decode_ws_response(user_ws.search(row_dict['phonenumber']))
                if my_user == "ERROR404":
                    print '''Warn: no user with phonenumber %s was found on XiVO''' % row_dict['phonenumber']
                    continue
                else:
                    my_user_id = my_user[0]['id']

                # Get all user parameters
                my_user_data = decode_ws_response(user_ws.view(my_user_id))
                
                my_user_data_lineid = my_user_data['linefeatures'][0]['id']
                my_user_data_linenumber = my_user_data['linefeatures'][0]['number']
                my_user_data_deviceid = device_id_by_mac[row_dict['mac']]
                
                # Delete key linefeatures since the view method does not return
                # the correct formating for the edit method for this specific key
                del my_user_data['linefeatures']
                my_user_data['linefeatures'] = {
                        "id": [my_user_data_lineid],
                        "number": [my_user_data_linenumber],
                        "device": [my_user_data_deviceid]
                } 


                response = user_ws.edit(my_user_data, my_user_id)
                if response.code == 200:
                    print "User %s, associated to Device %s successfully" % (row_dict['phonenumber'], row_dict['mac'])
                else:
                    print "ERROR: there was an error when associating %s to %s : Error %s" % (row_dict['phonenumber'],
                                                                                              row_dict['mac'], response.code)


def main():
    parsed_args = _parse_args()

    xivo = XIVO 
    username = USERNAME
    password = PASSWORD

    print "Connecting..."
    print " xivo : %s " % xivo

    user_ws = WebServices('https://%s' % xivo, URI_USERS, username, password)
    device_ws = WebServices('https://%s' % xivo, URI_DEVICES, username, password)

    edit_users(user_ws, device_ws, parsed_args.csv_file)


if __name__ == '__main__':
    main()
