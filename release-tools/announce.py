import getpass
import os
import requests
import jinja2
import click
import twitter
import ircbot
from ConfigParser import ConfigParser
from marrow.mailer import Mailer, Message

SCRIPT_PATH = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_FOLDER = os.path.join(SCRIPT_PATH, 'templates')
TEMPLATE_FILE = "announce.jinja"

config_files = [os.path.join(SCRIPT_PATH, filename) for filename in ('defaults.ini', 'defaults.ini.local')]
config = ConfigParser()
config.read(config_files)

session = requests.Session()
session.verify = False
session.headers.update({'X-Redmine-API-Key': config.get('redmine', 'token')})


@click.command()
@click.argument('old_version')
@click.argument('version')
@click.option('--path', default='announces', help='create and place generated files in this directory (default: announces)')
def prepare_announces(old_version, version, path):
    if not os.path.exists(path):
        os.mkdir(path)

    for media in ('redmine', 'email'):
        filename = '{}.txt'.format(media)
        filepath = os.path.join(path, filename)

        click.echo("generating '{}'".format(filepath))
        with open(filepath, 'w') as f:
            text = generate_announce(old_version, version, media)
            f.write(text)


@click.command()
@click.argument('version')
@click.option('--path', default='announces', help='announces to publish (default: announces)')
def publish_announces(version, path):
    emailpath = os.path.join(path, 'email.txt')
    with open(emailpath) as f:
        email = f.read().decode('utf8')

    # click.echo("Publishing email")
    # publish_email(version, email)
    # click.echo("Publishing twitter")
    # publish_twitter(version)
    click.echo("Publishing irc")
    publish_irc(version)


def generate_announce(old_version, version, media):
    env = setup_jinja()
    tpl_name = '{}.jinja'.format(media)

    template = env.get_template(tpl_name)
    metadata = fetch_metadata(version)
    return template.render(old_version=old_version, **metadata)


def setup_jinja():
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_FOLDER))
    env.filters['past_plural'] = past_plural
    return env


def past_plural(quantity, word):
    phrase = "{quantity} {word}{suffix} {verb}"
    if quantity == 1:
        suffix = ''
        verb = 'was'
    else:
        suffix = 's'
        verb = 'were'
    return phrase.format(quantity=quantity, word=word, suffix=suffix, verb=verb)


def fetch_metadata(version):
    version_id = find_version_id(version)
    issues = issues_for_version(version_id)

    bugs = len([i for i in issues if i['tracker']['name'] == 'Bug'])
    features = len([i for i in issues if i['tracker']['name'] == 'Feature'])
    technicals = len([i for i in issues if i['tracker']['name'] == 'Technical'])

    return {'bugs': bugs,
            'features': features,
            'technicals': technicals,
            'version': version,
            'version_id': version_id}


def find_version_id(version):
    url = "{}/projects/{}/versions.json".format(config.get('redmine', 'url'),
                                                config.get('redmine', 'project_id'))
    response = session.get(url)
    versions = response.json()['versions']
    found = [v for v in versions if v['name'] == version]
    return found[0]['id']


def issues_for_version(version_id):
    url = "{}/issues.json".format(config.get('redmine', 'url'))
    params = {'fixed_version_id': version_id, 'status_id': '*'}
    response = session.get(url, params=params)
    return response.json()['issues']


def get_email_password(username):
    if config.has_option('email', 'password'):
        return config.get('email', 'password')

    return getpass.getpass('Email password for {}: '.format(username))


def publish_email(version, announce):
    subject = config.get('email', 'subject').format(version=version)
    username = config.get('email', 'username')

    mailer = Mailer({'manager': {'use': 'immediate'},
                     'transport': {'use': 'smtp',
                                   'host': config.get('email', 'host'),
                                   'username': username,
                                   'password': get_email_password(username),
                                   'tls': 'optional'}
                     })

    message = Message(author=config.get('email', 'from'),
                      to=config.get('email', 'to'),
                      subject=subject,
                      plain=announce)

    click.echo("Sending email to {}".format(config.get('email', 'to')))
    mailer.start()
    mailer.send(message)
    mailer.stop()


def publish_twitter(version):
    oauth_token, oauth_secret = check_twitter_oauth()
    version_id = find_version_id(version)
    status = config.get('twitter', 'status').format(version=version, version_id=version_id)

    server = twitter.Twitter(auth=twitter.OAuth(oauth_token,
                                                oauth_secret,
                                                config.get('twitter', 'api_key'),
                                                config.get('twitter', 'api_secret')))
    server.statuses.update(status=status)


def check_twitter_oauth():
    if not (config.has_option('twitter', 'oauth_token')
            and config.has_option('twitter', 'oauth_secret')):
        oauth_token, oauth_secret = twitter.oauth_dance('releasetool',
                                                        config.get('twitter', 'api_key'),
                                                        config.get('twitter', 'api_secret'))
        add_tokens_to_config(oauth_token, oauth_secret)
    else:
        oauth_token = config.get('twitter', 'oauth_token')
        oauth_secret = config.get('twitter', 'oauth_secret')

    return oauth_token, oauth_secret


def add_tokens_to_config(oauth_token, oauth_secret):
    configfile = os.path.join(SCRIPT_PATH, 'defaults.ini.local')

    new_config = ConfigParser()
    new_config.read(configfile)
    if not new_config.has_section('twitter'):
        new_config.add_section('twitter')

    new_config.set('twitter', 'oauth_token', oauth_token)
    new_config.set('twitter', 'oauth_secret', oauth_secret)
    with open(configfile, 'w') as f:
        new_config.write(f)


def publish_irc(version):
    ircbot.publish_irc_topic(config, version)


if __name__ == "__main__":
    cli = click.Group()
    cli.add_command(prepare_announces)
    cli.add_command(publish_announces)
    cli()
