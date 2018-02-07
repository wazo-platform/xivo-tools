import logging
import getpass

from fabric.api import puts
from marrow.mailer import Mailer, Message
from .config import config

logging.basicConfig()


def send_email(to, subject, body):
    host = config.get('email', 'host')
    author = config.get('email', 'from')
    username = config.get('email', 'username')
    password = _get_email_password(username)

    mailer = Mailer({'manager': {'use': 'immediate'},
                     'transport': {'use': 'smtp',
                                   'host': host,
                                   'port': '587',
                                   'username': username,
                                   'password': password,
                                   'tls': 'required'}
                     })

    message = Message(author=author, to=to, subject=subject, plain=body)

    puts("Sending email to {}".format(to))
    mailer.start()
    mailer.send(message)
    mailer.stop()


def _get_email_password(username):
    if config.has_option('email', 'password'):
        return config.get('email', 'password')

    return getpass.getpass('Email password for {}: '.format(username))
