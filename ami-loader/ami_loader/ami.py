# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import logging
import socket
import select

logger = logging.getLogger(__name__)


class AMIClient(object):
    _BUFSIZE = 4096
    _TIMEOUT = 15

    def __init__(self, hostname):
        self._hostname = hostname
        self._sock = None

    def connect(self):
        logger.info('Connecting to %s', self._hostname)

        new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            new_sock.connect((self._hostname, 5038))
        except Exception:
            new_sock.close()
            raise
        else:
            self._sock = new_sock

    def wait_recv(self, timeout=_TIMEOUT):
        if self._is_recv_ready(timeout):
            self.flush_recv()

    def _is_recv_ready(self, timeout=0):
        r_rlist = select.select([self._sock], [], [], timeout)[0]
        return bool(r_rlist)

    def flush_recv(self):
        while self._is_recv_ready():
            data = self._sock.recv(self._BUFSIZE)
            if not data:
                raise Exception('remote end closed the connection')
            logger.debug('Received %r', data)

    def action_login(self, username, password):
        logger.debug('Action login')

        lines = [
            'Action: Login',
            'Username: %s' % username,
            'Secret: %s' % password,
        ]
        self._send_request(lines)

    def _send_request(self, lines):
        data = '\r\n'.join(lines) + '\r\n\r\n'
        self._sock.send(data)

    def action_command(self, cli_command):
        logger.debug('Action command')

        lines = [
            'Action: Command',
            'Command: %s' % cli_command,
        ]
        self._send_request(lines)

    def action_core_show_channels(self):
        logger.debug('Action core show channels')

        lines = [
            'Action: CoreShowChannels',
        ]
        self._send_request(lines)

    def action_show_dialplan(self):
        logger.debug('Action show dialplan')

        lines = [
            'Action: ShowDialPlan',
        ]
        self._send_request(lines)

    def disconnect(self):
        logger.info('Disconnecting from %s', self._hostname)

        self._sock.close()
        self._sock = None
