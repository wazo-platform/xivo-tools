#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015-2018 The Wazo Authors  (see the AUTHORS file)
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

import argparse
import kombu
import logging

from kombu.mixins import ConsumerMixin
from pprint import pformat

EXCHANGE = kombu.Exchange('xivo', type='topic')

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(process)d] (%(levelname)s) (%(name)s): %(message)s')
logger = logging.getLogger(__name__)


class C(ConsumerMixin):

    def __init__(self, connection, routing_key):
        self.connection = connection
        self.routing_key = routing_key

    def get_consumers(self, Consumer, channel):
        return [Consumer(kombu.Queue(exchange=EXCHANGE, routing_key=self.routing_key, exclusive=True),
                callbacks=[self.on_message])]

    def on_message(self, body, message):
        logger.info('Received: %s', pformat(body))
        message.ack()


def main():
    parser = argparse.ArgumentParser('read RabbitMQ xivo exchange')
    parser.add_argument('-n', '--hostname', help='RabbitMQ server',
                        default='localhost')
    parser.add_argument('-p', '--port', help='Port of RabbitMQ',
                        default='5672')
    parser.add_argument('-r', '--routing-key', help='Routing key to bind on bus',
                        dest='routing_key', default='#')

    args = parser.parse_args()

    url_amqp = 'amqp://guest:guest@%s:%s//' % (args.hostname, args.port)

    with kombu.Connection(url_amqp) as conn:
        try:
            C(conn, args.routing_key).run()
        except KeyboardInterrupt:
            return


main()
