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


class NoHangupBehaviour(object):

    def on_clock_tick(self):
        pass

    @classmethod
    def new_factory(cls):
        no_hangup_behaviour = cls()
        def no_hangup_behaviour_factory(phone_line):
            return no_hangup_behaviour
        return no_hangup_behaviour_factory


class ConstantHangupBehaviour(object):

    def __init__(self, phone_line, tick_before_hangup):
        self._phone_line = phone_line
        self._tick_before_hangup = tick_before_hangup

    def on_clock_tick(self):
        self._tick_before_hangup -= 1
        if self._tick_before_hangup == 0:
            self._phone_line.hangup()

    @classmethod
    def new_factory(cls, tick_before_hangup):
        if tick_before_hangup <= 0:
            raise ValueError(tick_before_hangup)

        def constant_hangup_behaviour_factory(phone_line):
            return cls(phone_line, tick_before_hangup)
        return constant_hangup_behaviour_factory
