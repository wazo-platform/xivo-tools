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

class ConstantCallBehaviour(object):

    def __init__(self, phone, extension, tick_before_call):
        self._phone = phone
        self._extension = extension
        self._tick_before_answer = tick_before_call

    def on_clock_tick(self):
        self._tick_before_call -= 1
        if self._tick_before_call == 0:
            self._phone.dial(self._extension)

    @classmethod
    def new_factory(cls, extension, tick_before_call):
        if tick_before_call <= 0:
            raise ValueError(tick_before_call)

        def constant_call_behaviour_factory(phone):
            return cls(phone, extension, tick_before_call)
        return constant_call_behaviour_factory
