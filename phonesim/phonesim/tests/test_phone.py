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

import unittest
from mock import Mock
from phonesim.phone import AastraPhone, AastraPhoneLine, \
    PhoneLineState


class TestAastraPhone(unittest.TestCase):

    def test_phone_line_state_is_ringing_on_incoming_event(self):
        phone = self._new_phone()
        env = self._new_http_request_env('/incoming')

        phone._on_http_request_received(env)

        phone_line = phone.observer.on_phone_line_state_changed.call_args[0][0]
        self.assertEqual(PhoneLineState.RINGING, phone_line.state)
        self.assertEqual(None, phone_line.previous_state)

    def test_phone_line_state_is_calling_on_outgoing_event(self):
        phone = self._new_phone()
        env = self._new_http_request_env('/outgoing')

        phone._on_http_request_received(env)

        phone_line = phone.observer.on_phone_line_state_changed.call_args[0][0]
        self.assertEqual(PhoneLineState.CALLING, phone_line.state)
        self.assertEqual(None, phone_line.previous_state)

    def test_phone_line_state_is_talking_on_connected_event(self):
        phone = self._new_phone()
        phone._phone_line = AastraPhoneLine(phone)
        phone._phone_line._update_state(PhoneLineState.RINGING)
        env = self._new_http_request_env('/connected')

        phone._on_http_request_received(env)

        phone_line = phone.observer.on_phone_line_state_changed.call_args[0][0]
        self.assertEqual(PhoneLineState.TALKING, phone_line.state)
        self.assertEqual(PhoneLineState.RINGING, phone_line.previous_state)

    def _new_phone(self):
        phone = AastraPhone('1.1.1.1')
        phone.observer = Mock()
        return phone

    def _new_http_request_env(self, path, query_string=''):
        return {'PATH_INFO': path, 'QUERY_STRING': query_string}


class TestAastraPhoneLine(unittest.TestCase):

    def test_answer_exec_key_line(self):
        phone = Mock()
        phone_line = AastraPhoneLine(phone)

        phone_line.answer()

        phone.exec_key_line.assert_called_once_with(1)

    def test_hangup_exec_key_line_then_hangup(self):
        phone = Mock()
        phone_line = AastraPhoneLine(phone)

        phone_line.hangup()

        phone.exec_key_goodbye.assert_called_once_with()
