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

from __future__ import absolute_import

import argparse
import logging
from gevent import sleep
from phonesim.phone import AastraPhoneFactory
from phonesim.user import CallAndWaitUser, AnswerAndHangupUser
from phonesim.behaviour.answer import ConstantAnswerBehaviour
from phonesim.behaviour.hangup import ConstantHangupBehaviour
from phonesim.behaviour.call import ConstantCallBehaviour


def main():
    _init_logging()

    parsed_args = _parse_args()

    if parsed_args.verbose:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

    phone_factory = AastraPhoneFactory(parsed_args.aastra_ip.split(','))
    try:
        phone1 = phone_factory()
        phone2 = phone_factory()

        user1 = _new_answer_and_hangup_user(phone1)
        user2 = _new_call_and_wait_user(phone2)
        try:
            user1.start()
            user2.start()
            while True:
                user1.on_clock_tick()
                user2.on_clock_tick()
                sleep(0.5 / parsed_args.rate)
        finally:
            user1.close()
            user2.close()
    finally:
        phone_factory.close()


def _init_logging():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--aastra-ip', default='',
                        help='comma separated list of Aastra phone IP address')
    parser.add_argument('-r', '--rate', default=1.0, type=float,
                        help='clock tick rate')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='increase verbosity')
    return parser.parse_args()


def _new_answer_and_hangup_user(phone):
    answer_factory = ConstantAnswerBehaviour.new_factory(5)
    hangup_factory = ConstantHangupBehaviour.new_factory(12)
    return AnswerAndHangupUser(phone, answer_factory, hangup_factory)


def _new_call_and_wait_user(phone):
    call_factory = ConstantCallBehaviour.new_factory('1001', 15)
    return CallAndWaitUser(phone, call_factory)


if __name__ == '__main__':
    main()
