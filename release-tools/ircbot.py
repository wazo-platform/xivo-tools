from irc.client import SimpleIRCClient
import logging

logger = logging.getLogger(__name__)


class Stop(Exception):
    pass


class IRCStatusUpdater(SimpleIRCClient):

    def __init__(self, channel, message):
        SimpleIRCClient.__init__(self)
        self._channel = channel
        self._message = message

    def on_welcome(self, connection, event):
        logger.info('joining channel %s', self._channel)
        connection.join(self._channel)

    def on_join(self, connection, event):
        logger.info("elevating privileges")
        self._elevate_privileges(connection)

    def _elevate_privileges(self, connection):
        message = "op {channel} {nickname}".format(channel=self._channel,
                                                   nickname=connection.get_nickname())
        connection.privmsg("chanserv", message)

    def on_mode(self, connection, event):
        logger.info("updating status to '%s'", self._message)
        self._update_status(connection)

    def _update_status(self, connection):
        connection.topic(self._channel, self._message)

    def on_topic(self, connection, event):
        logger.info('quitting')
        connection.disconnect()
        raise Stop()


def publish_irc_topic(config, version):
    topic = config.get('irc', 'topic').format(version=version)
    client = IRCStatusUpdater(config.get('irc', 'channel'),
                              topic)

    logging.info('connecting to %s', config.get('irc', 'server'))
    client.connect(config.get('irc', 'server'),
                   6667,
                   config.get('irc', 'nickname'),
                   config.get('irc', 'password'))
    try:
        client.start()
    except Stop:
        pass
