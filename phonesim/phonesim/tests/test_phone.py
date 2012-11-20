# -*- coding: UTF-8 -*-

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
