import getpass
import os
import requests
import jinja2
import twitter
import ircbot

from ConfigParser import ConfigParser
from fabric.api import puts, task
from marrow.mailer import Mailer, Message

from .config import config, CUSTOM_CONFIG_PATH, SCRIPT_PATH

TEMPLATE_FOLDER = os.path.join(SCRIPT_PATH, 'templates')
TEMPLATE_FILE = "announce.jinja"

session = requests.Session()
session.verify = False
session.headers.update({'X-Redmine-API-Key': config.get('redmine', 'token')})


@task
def prepare(old_version, version, path='announces'):
    '''(previous, current) create announce files for review'''
    if not os.path.exists(path):
        os.mkdir(path)

    for media in ('redmine', 'email'):
        filename = '{}.txt'.format(media)
        filepath = os.path.join(path, filename)

        puts("generating '{}'".format(filepath))
        with open(filepath, 'w') as f:
            text = _generate_announce(old_version, version, media)
            f.write(text)


@task
def publish(version, path='announces'):
    '''(current) publish reviewed announce files'''
    emailpath = os.path.join(path, 'email.txt')
    with open(emailpath) as f:
        email = f.read().decode('utf8')

    puts("Publishing email")
    _publish_email(version, email)
    puts("Publishing twitter")
    _publish_twitter(version)
    puts("Publishing irc")
    _publish_irc(version)


def _generate_announce(old_version, version, media):
    env = _setup_jinja()
    tpl_name = '{}.jinja'.format(media)

    template = env.get_template(tpl_name)
    metadata = _fetch_metadata(version)
    return template.render(old_version=old_version, **metadata)


def _setup_jinja():
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_FOLDER))
    env.filters['past_plural'] = _past_plural
    return env


def _past_plural(quantity, word):
    phrase = "{quantity} {word}{suffix} {verb}"
    if quantity == 1:
        suffix = ''
        verb = 'was'
    else:
        suffix = 's'
        verb = 'were'
    return phrase.format(quantity=quantity, word=word, suffix=suffix, verb=verb)


def _fetch_metadata(version):
    version_id = _find_version_id(version)
    issues = _issues_for_version(version_id)

    bugs = len([i for i in issues if i['tracker']['name'] == 'Bug'])
    features = len([i for i in issues if i['tracker']['name'] == 'Feature'])
    technicals = len([i for i in issues if i['tracker']['name'] == 'Technical'])

    return {'bugs': bugs,
            'features': features,
            'technicals': technicals,
            'version': version,
            'version_id': version_id}


def _find_version_id(version):
    url = "{}/projects/{}/versions.json".format(config.get('redmine', 'url'),
                                                config.get('redmine', 'project_id'))
    response = session.get(url)
    versions = response.json()['versions']
    found = [v for v in versions if v['name'] == version]
    return found[0]['id']


def _issues_for_version(version_id):
    url = "{}/issues.json".format(config.get('redmine', 'url'))
    params = {'fixed_version_id': version_id, 'status_id': '*'}
    response = session.get(url, params=params)
    return response.json()['issues']


def _get_email_password(username):
    if config.has_option('email', 'password'):
        return config.get('email', 'password')

    return getpass.getpass('Email password for {}: '.format(username))


def _publish_email(version, announce):
    subject = config.get('email', 'subject').format(version=version)
    username = config.get('email', 'username')

    mailer = Mailer({'manager': {'use': 'immediate'},
                     'transport': {'use': 'smtp',
                                   'host': config.get('email', 'host'),
                                   'username': username,
                                   'password': _get_email_password(username),
                                   'tls': 'optional'}
                     })

    message = Message(author=config.get('email', 'from'),
                      to=config.get('email', 'to'),
                      subject=subject,
                      plain=announce)

    puts("Sending email to {}".format(config.get('email', 'to')))
    mailer.start()
    mailer.send(message)
    mailer.stop()


def _publish_twitter(version):
    oauth_token, oauth_secret = _check_twitter_oauth()
    version_id = _find_version_id(version)
    status = config.get('twitter', 'status').format(version=version, version_id=version_id)

    server = twitter.Twitter(auth=twitter.OAuth(oauth_token,
                                                oauth_secret,
                                                config.get('twitter', 'api_key'),
                                                config.get('twitter', 'api_secret')))
    server.statuses.update(status=status)


def _check_twitter_oauth():
    if not (config.has_option('twitter', 'oauth_token')
            and config.has_option('twitter', 'oauth_secret')):
        oauth_token, oauth_secret = twitter.oauth_dance('releasetool',
                                                        config.get('twitter', 'api_key'),
                                                        config.get('twitter', 'api_secret'))
        _add_tokens_to_config(oauth_token, oauth_secret)
    else:
        oauth_token = config.get('twitter', 'oauth_token')
        oauth_secret = config.get('twitter', 'oauth_secret')

    return oauth_token, oauth_secret


def _add_tokens_to_config(oauth_token, oauth_secret):
    configfile = CUSTOM_CONFIG_PATH

    new_config = ConfigParser()
    new_config.read(configfile)
    if not new_config.has_section('twitter'):
        new_config.add_section('twitter')

    new_config.set('twitter', 'oauth_token', oauth_token)
    new_config.set('twitter', 'oauth_secret', oauth_secret)
    with open(configfile, 'w') as f:
        new_config.write(f)


def _publish_irc(version):
    ircbot.publish_irc_topic(config, version)
