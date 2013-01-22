# -*- coding: utf-8 -*-

# Copyright (C) 2013 Avencall
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
from phonesim.phone import PhoneLineState

logger = logging.getLogger(__name__)


class AnswerAndHangupUser(object):

    def __init__(self, phone, answer_factory, hangup_factory):
        self._phone = phone
        self._answer_factory = answer_factory
        self._answer = None
        self._hangup_factory = hangup_factory
        self._hangup = None

    def close(self):
        self._phone.observer = None

    def start(self):
        self._phone.observer = self

    def on_phone_line_state_changed(self, phone_line):
        if phone_line.state == PhoneLineState.RINGING:
            self._answer = self._answer_factory(phone_line)
        elif phone_line.state == PhoneLineState.TALKING:
            self._answer = None
            self._hangup = self._hangup_factory(phone_line)
        elif phone_line.state == PhoneLineState.CLOSED:
            self._answer = None
            self._hangup = None

    def on_clock_tick(self):
        if self._answer is not None:
            self._answer.on_clock_tick()
        if self._hangup is not None:
            self._hangup.on_clock_tick()


class CallAndWaitUser(object):

    def __init__(self, phone, call_factory):
        self._phone = None
        self._call_factory = call_factory
        self._call = call_factory(phone)

    def close(self):
        self._phone.observer = None

    def start(self):
        self._phone.observer = self

    def on_phone_line_state_changed(self, phone_line):
        if phone_line.state == PhoneLineState.CLOSED:
            self._call = self._call_factory(self._phone)
        else:
            self._call = None

    def on_clock_tick(self):
        if self._call is not None:
            self._call.on_clock_tick()


class AnswerAndTransferUser(object):

    _TICK_BEFORE_ANSWER = 5
    _TICK_BEFORE_XFER = 12
    _TICK_BEFORE_FINAL_XFER = 5

    def __init__(self, phone):
        self._phone = phone
        self._state = 'idle'
        self._remaining_tick_before_answer = None
        self._remaining_tick_before_xfer = None
        self._remaining_tick_before_final_xfer = None
        self._phone_line = None

    def close(self):
        self._phone.observer = None

    def start(self):
        self._phone.observer = self

    def on_phone_line_state_changed(self, phone_line):
        if phone_line.state == PhoneLineState.RINGING:
            self._state = 'ringing'
            self._phone_line = phone_line
            self._remaining_tick_before_answer = self._TICK_BEFORE_ANSWER
        elif phone_line.state == PhoneLineState.TALKING:
            self._state = 'talking'
            self._remaining_tick_before_xfer = self._TICK_BEFORE_XFER
        elif phone_line.state == PhoneLineState.CLOSED:
            self._state = 'idle'
            self._phone_line = None

    def on_clock_tick(self):
        if self._state == 'ringing':
            self._remaining_tick_before_answer -= 1
            if self._remaining_tick_before_answer == 0:
                self._phone_line.answer()
        elif self._state == 'talking':
            self._remaining_tick_before_xfer -= 1
            if self._remaining_tick_before_xfer == 0:
                self._phone.exec_key_xfer()
                # FIXME hardcoded extension
                self._phone.exec_dial('1003')
                self._state = 'xferring'
                self._remaining_tick_before_final_xfer = self._TICK_BEFORE_FINAL_XFER
        elif self._state == 'xferring':
            self._remaining_tick_before_final_xfer -= 1
            if self._remaining_tick_before_final_xfer == 0:
                self._phone.exec_key_xfer()
                self._state = 'after-xferring'
