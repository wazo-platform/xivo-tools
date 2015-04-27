import logging
import re

from irc.client import SimpleIRCClient

logger = logging.getLogger(__name__)


class Stop(Exception):
    pass


class IRCStatusUpdater(SimpleIRCClient):

    def __init__(self, channel, new_topic_function):
        SimpleIRCClient.__init__(self)
        self._channel = channel
        self._new_topic = new_topic_function
        self._current_topic = None
        self._is_operator = False

    def on_welcome(self, connection, event):
        logger.info('joining channel %s', self._channel)
        connection.join(self._channel)

    def on_currenttopic(self, connection, event):
        channel, current_topic = event.arguments
        if channel == self._channel:
            self._current_topic = current_topic

        logger.info("elevating privileges")
        self._elevate_privileges(connection)

    def _elevate_privileges(self, connection):
        message = "op {channel} {nickname}".format(channel=self._channel,
                                                   nickname=connection.get_nickname())
        connection.privmsg("chanserv", message)

    def on_mode(self, connection, event):
        mode, nickname = event.arguments

        if self._is_operator:
            return  # we get two consecutive identical MODE messages; ignore the second one

        if mode == '+o':
            self._is_operator = True

        if self._is_operator and self._current_topic is not None:
            new_topic = self._new_topic(self._current_topic)
            logger.info("updating topic to '%s'", new_topic)
            connection.topic(self._channel, new_topic)
        else:
            self._stop(connection)

    def on_topic(self, connection, event):
        self._stop(connection)

    def _stop(self, connection):
        logger.info('quitting')
        connection.disconnect()
        raise Stop()


def publish_irc_topic(config, version):
    pattern_to_replace = config.get('irc', 'topic_pattern_to_replace')
    topic_replacement = config.get('irc', 'topic_pattern_replacement').format(version=version)
    new_topic_function = lambda topic: re.sub(pattern_to_replace, topic_replacement, topic)
    client = IRCStatusUpdater(config.get('irc', 'channel'),
                              new_topic_function)

    logging.info('connecting to %s', config.get('irc', 'server'))
    client.connect(config.get('irc', 'server'),
                   6667,
                   config.get('irc', 'nickname'),
                   config.get('irc', 'password'))
    try:
        client.start()
    except Stop:
        pass
