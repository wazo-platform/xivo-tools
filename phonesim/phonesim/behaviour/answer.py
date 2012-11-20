# -*- coding: UTF-8 -*-


class NoAnswerBehaviour(object):

    def on_clock_tick(self):
        pass

    @classmethod
    def new_factory(cls):
        no_answer_behaviour = cls()
        def no_answer_behaviour_factory(phone_line):
            return no_answer_behaviour
        return no_answer_behaviour_factory


class ConstantAnswerBehaviour(object):

    def __init__(self, phone_line, tick_before_answer):
        self._phone_line = phone_line
        self._tick_before_answer = tick_before_answer

    def on_clock_tick(self):
        self._tick_before_answer -= 1
        if self._tick_before_answer == 0:
            self._phone_line.answer()

    @classmethod
    def new_factory(cls, tick_before_answer):
        if tick_before_answer <= 0:
            raise ValueError(tick_before_answer)

        def constant_answer_behaviour_factory(phone_line):
            return cls(phone_line, tick_before_answer)
        return constant_answer_behaviour_factory


class ConstantRejectBehaviour(object):

    def __init__(self, phone_line, tick_before_reject):
        self._phone_line = phone_line
        self._tick_before_reject = tick_before_reject

    def on_clock_tick(self):
        self._tick_before_reject -= 1
        if self._tick_before_reject == 0:
            self._phone_line.hangup()

    @classmethod
    def new_factory(cls, tick_before_reject):
        if tick_before_reject <= 0:
            raise ValueError(tick_before_reject)

        def constant_answer_behaviour_factory(phone_line):
            return cls(phone_line, tick_before_reject)
        return constant_answer_behaviour_factory
