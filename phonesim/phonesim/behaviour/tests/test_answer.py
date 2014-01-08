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
from phonesim.behaviour.answer import NoAnswerBehaviour, ConstantAnswerBehaviour


class TestNoAnswerBehaviour(unittest.TestCase):

    def test_behaviour(self):
        phone_line = Mock()
        answer_factory = NoAnswerBehaviour.new_factory()
        answer_behaviour = answer_factory(phone_line)

        answer_behaviour.on_clock_tick()

        self.assertFalse(phone_line.answer.called)


class TestConstantAnswerBehaviour(unittest.TestCase):

    def test_behaviour(self):
        phone_line = Mock()
        answer_factory = ConstantAnswerBehaviour.new_factory(2)
        answer_behaviour = answer_factory(phone_line)

        answer_behaviour.on_clock_tick()
        self.assertFalse(phone_line.answer.called)

        answer_behaviour.on_clock_tick()
        self.assertTrue(phone_line.answer.called)
