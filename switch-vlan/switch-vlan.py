#!/usr/bin/env python2
import urllib2
import cookielib
import sys

from urllib import urlencode

SWITCH_IP = "192.168.0.0"
PASSWORD = "password"

LOGIN_URL = "http://%s/base/main_login.html" % SWITCH_IP
VLAN_URL = "http://%s/switching/dot1q/qnp_port_cfg_rw.html" % SWITCH_IP

cookie_handler = urllib2.HTTPCookieProcessor(cookielib.CookieJar())
browser = urllib2.build_opener(cookie_handler)

def login_post(password):
    params = {
        'pwd': password,
        'login.x': 0,
        'login.y': 0,
        'err_flag': 0,
        'err_msg': ''
    }

    return urlencode(params)

def port_vlan_post(vlan, ports):
    params = {
        'cncel'               : '',
        'err_flag'            : '0',
        'err_msg'             : '',
        'filter'              : 'Blank',
        'ftype'               : 'Blank',
        'inputBox_interface1' : '',
        'inputBox_interface2' : '',
        'java_port'           : '',
        'multiple_ports'      : '3',
        'priority'            : '',
        'pvid'                : vlan,
        'refrsh'              : '',
        'submt'               : '16',
        'unit_no'             : '1'
    }

    post = params.items()
    post.extend(('CBox_1', 'checkbox') for x in ports)
    gports = ('selectedPorts', ';'.join('g%s' % x for x in ports))
    post.append(gports)

    return urlencode(post)

def open_url(url, post):
    resp = browser.open(url, post)
    if resp.getcode() >= 400:
        raise Exception("Error %s while opening %s" % (resp.getcode(), url))


if __name__ == "__main__":
    if len(sys.argv) <= 2:
        print "Usage: %s vlan ports" % sys.argv[0]
        sys.exit(0)

    vlan = int(sys.argv[1])
    ports = [int(x) for x in sys.argv[2].split(",")]

    print "Connecting to switch..."
    open_url(LOGIN_URL, login_post(PASSWORD))

    print "Adjusting VLAN ports..."
    open_url(VLAN_URL, port_vlan_post(vlan, ports))

    print "Done"

