# -*- coding: UTF-8 -*-


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
