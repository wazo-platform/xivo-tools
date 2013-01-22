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
import select
import socket

logger = logging.getLogger(__name__)


class _RemoteSocketClosedError(Exception):
    pass


class SocketProxy(object):
    _BUFSIZE = 4096

    def __init__(self, client_socket, server_socket):
        """
        Note that the sockets are owned by the newly created instance.
        """
        self._client_socket = client_socket
        self._server_socket = server_socket

    def start(self):
        """
        Return only if at least one side of the connection is closed (or if
        a socket error occurs).
        
        """
        try:
            self._do_start()
        except _RemoteSocketClosedError:
            pass
        finally:
            self._client_socket.close()
            self._server_socket.close()

    def _do_start(self):
        self._client_socket.setblocking(0)
        self._server_socket.setblocking(0)
        client_buf = "" # buffer of data to send to client
        server_buf = "" # buffer of data to send to server
        while True:
            # compute rlist and wlist
            rlist = [self._client_socket, self._server_socket]
            wlist = []
            if server_buf:
                wlist.append(self._server_socket)
            if client_buf:
                wlist.append(self._client_socket)

            r_rlist, r_wlist, _ = select.select(rlist, wlist, [])
            for cur_socket in r_wlist:
                if cur_socket == self._client_socket:
                    assert client_buf
                    logger.debug("Sending data to client")
                    try:
                        n = self._client_socket.send(client_buf)
                    except socket.error:
                        raise _RemoteSocketClosedError("send to client")
                    else:
                        client_buf = client_buf[n:]
                elif cur_socket == self._server_socket:
                    assert server_buf
                    logger.debug("Sending data to server")
                    try:
                        n = self._server_socket.send(server_buf)
                    except socket.error:
                        raise _RemoteSocketClosedError("send to server")
                    else:
                        server_buf = server_buf[n:]
                else:
                    raise AssertionError("cur_socket is: %r" % cur_socket)

            for cur_socket in r_rlist:
                if cur_socket == self._client_socket:
                    logger.debug("Receiving data from client")
                    try:
                        buf = self._client_socket.recv(self._BUFSIZE)
                    except socket.error:
                        raise _RemoteSocketClosedError("recv from client")
                    else:
                        if not buf:
                            raise _RemoteSocketClosedError("recv from client")
                        server_buf += buf
                elif cur_socket == self._server_socket:
                    logger.debug("Receiving data from server")
                    try:
                        buf = self._server_socket.recv(self._BUFSIZE)
                    except socket.error:
                        raise _RemoteSocketClosedError("recv from server")
                    else:
                        if not buf:
                            raise _RemoteSocketClosedError("recv from server")
                        client_buf += buf
                else:
                    raise AssertionError("cur_socket is: %r" % cur_socket)


class IPv4ProxyEstablisher(object):
    def __init__(self, bind_address, server_address):
        self._server_address = server_address
        self._listen_socket = self._new_listen_socket(bind_address)

    def _new_listen_socket(self, address):
        lsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            lsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            lsocket.bind(address)
            lsocket.listen(2)
        except Exception:
            lsocket.close()
            raise
        return lsocket

    def close(self):
        self._listen_socket.close()

    def establish_connections(self):
        logger.info("Waiting for client connection")
        client_socket, addr = self._listen_socket.accept()
        logger.info("Client connection from %s", addr)
        try:
            server_socket = self._new_server_socket()
        except Exception, e:
            logger.error("Error while establishing server connection: %s", e)
            client_socket.close()
            raise
        else:
            return client_socket, server_socket

    def _new_server_socket(self):
        ssocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssocket.connect(self._server_address)
        logger.info("Server connection to %s", self._server_address)
        return ssocket
