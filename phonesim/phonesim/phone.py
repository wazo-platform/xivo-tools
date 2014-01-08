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

import logging
import urllib2
from gevent.pywsgi import WSGIServer

logger = logging.getLogger(__name__)


class PhoneLineState(object):

    CALLING = 'calling'
    RINGING = 'ringing'
    TALKING = 'talking'
    CLOSED = 'closed'


class AastraPhoneFactory(object):

    def __init__(self, phone_addrs, bind_port=8000):
        self._available_phone_addrs = list(reversed(phone_addrs))
        self._phones_by_addr = {}
        self._http_server = self._create_http_server(bind_port)

    def _create_http_server(self, bind_port):
        logger.info('Listening for HTTP requests on port %s', bind_port)
        http_server = WSGIServer(('0.0.0.0', bind_port), self._handle_http_request, log=None)
        http_server.start()
        return http_server

    def _handle_http_request(self, env, start_response):
        phone_addr = env['REMOTE_ADDR']
        phone = self._phones_by_addr.get(phone_addr)
        if phone is not None:
            try:
                phone._on_http_request_received(env)
            except Exception:
                logger.exception('Error while handling HTTP request')
        start_response('200 OK', [('Content-Type', 'text/xml')])
        return ['<AastraIPPhoneExecute><ExecuteItem URI="" /></AastraIPPhoneExecute>']

    def close(self):
        self._http_server.stop()
        self._phones_by_addr = {}

    def __call__(self):
        phone_addr = self._available_phone_addrs.pop()
        phone = AastraPhone(phone_addr)
        self._phones_by_addr[phone_addr] = phone
        return phone


class AastraPhone(object):

    _PATH_INFO_TO_STATE = {
        '/outgoing': PhoneLineState.CALLING,
        '/incoming': PhoneLineState.RINGING,
        '/connected': PhoneLineState.TALKING,
        '/disconnected': PhoneLineState.CLOSED,
    }
    _VALID_STATE_TRANSITIONS = [
        (None, PhoneLineState.CALLING),
        (None, PhoneLineState.RINGING),
        (PhoneLineState.CALLING, PhoneLineState.TALKING),
        (PhoneLineState.CALLING, PhoneLineState.CLOSED),
        (PhoneLineState.RINGING, PhoneLineState.TALKING),
        (PhoneLineState.RINGING, PhoneLineState.CLOSED),
        (PhoneLineState.TALKING, PhoneLineState.CLOSED),
    ]

    def __init__(self, phone_addr):
        logger.info('Creating phone %s', phone_addr)
        self._phone_addr = phone_addr
        self._url = 'http://%s/' % phone_addr
        self._phone_line = None
        self.observer = None

    def dial(self, extension):
        self.exec_dial(extension)

    def exec_dial(self, extension):
        xml_data = '<ExecuteItem URI="Dial:%s" />' % extension
        self._send_ip_phone_execute(xml_data)

    def exec_dial_line(self, line_no, extension):
        xml_data = '<ExecuteItem URI="DialLine:%s:%s" />' % (line_no, extension)
        self._send_ip_phone_execute(xml_data)

    def exec_key_goodbye(self):
        xml_data = '<ExecuteItem URI="Key:Goodbye" />'
        self._send_ip_phone_execute(xml_data)

    def exec_key_line(self, line_no):
        xml_data = '<ExecuteItem URI="Key:Line%s" />' % line_no
        self._send_ip_phone_execute(xml_data)

    def exec_key_xfer(self):
        xml_data = '<ExecuteItem URI="Key:Xfer" />'
        self._send_ip_phone_execute(xml_data)

    def _send_ip_phone_execute(self, xml_data):
        data = 'xml=<AastraIPPhoneExecute>%s</AastraIPPhoneExecute>\n' % xml_data
        request = urllib2.Request(self._url, data, {'Content-Type': 'text/xml'})
        fobj = urllib2.urlopen(request)
        try:
            fobj.read()
        finally:
            fobj.close()

    def _on_http_request_received(self, env):
        path_info = env['PATH_INFO']
        query_string = env['QUERY_STRING']
        logger.info('Received HTTP request from %s: %r %r', self._phone_addr, path_info, query_string)

        old_state = self._get_phone_line_state()
        new_state = self._PATH_INFO_TO_STATE[path_info]
        if self._is_valid_state_transition(old_state, new_state):
            if self._phone_line is None:
                self._phone_line = AastraPhoneLine(self)
            self._phone_line._update_state(new_state)
            if new_state == PhoneLineState.CLOSED:
                self._phone_line = None
        else:
            self._handle_invalid_state_transition(old_state, new_state)

    def _get_phone_line_state(self):
        phone_line = self._phone_line
        if phone_line is None:
            return None
        else:
            return phone_line.state

    def _is_valid_state_transition(self, old_state, new_state):
        return (old_state, new_state) in self._VALID_STATE_TRANSITIONS

    def _handle_invalid_state_transition(self, old_state, new_state):
        logger.warning('Ignoring state transition from %s to %s', new_state, old_state)


class AastraPhoneLine(object):

    def __init__(self, phone):
        self._phone = phone
        self.state = None
        self.previous_state = None

    def answer(self):
        self._phone.exec_key_line(1)

    def hangup(self):
        self._phone.exec_key_goodbye()

    def _update_state(self, new_state):
        if new_state != self.state:
            self.previous_state = self.state
            self.state = new_state
            observer = self._phone.observer
            if observer is not None:
                try:
                    observer.on_phone_line_state_changed(self)
                except Exception:
                    logger.exception('Exception during observer notification')
