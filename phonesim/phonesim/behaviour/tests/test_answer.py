# -*- coding: UTF-8 -*-

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
