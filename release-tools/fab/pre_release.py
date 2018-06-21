# -*- coding: utf-8 -*-
# Copyright 2013-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import getpass
import requests

from fabric.api import abort, execute, hosts, lcd, local, put, puts, run, task, settings
from hamcrest import assert_that, contains_string
from xivo_auth_client.client import AuthClient
from xivo_confd_client.client import ConfdClient

from . import repos
from .config import config
from .config import jenkins, jenkins_token
from .config import MASTER_HOST
from .config import SLAVE_HOST
from .config import LOAD_HOST
from .config import BUILDER_HOST
from .config import MIRROR_HOST
from .config import TRAFGEN_HOST
from .email import send_email

LOAD_ANSWER_TMUX_SESSION = 'load-answer'


@task
def translations():
    """() update translations for dird and admin-ui"""
    jenkins.job_build('wazo-dird-translations', token=jenkins_token)
    jenkins.job_build('wazo-admin-ui-all-translations', token=jenkins_token)


@task
def report_auto():
    """() build HTML report on tests executed automatically"""
    jenkins.job_build('build-tests_report_auto', token=jenkins_token)


@task
def report_manual():
    """() build HTML report on tests executed manually"""
    jenkins.job_build('build-tests_report_manual', token=jenkins_token)


@task
def stop_xivo_test():
    """() shutdown xivo-test and xivo-test-slave (once all tests are finished)"""
    with settings(warn_only=True):
        execute(_stop_xivo_test_master)
        execute(_stop_xivo_test_slave)


@hosts(MASTER_HOST)
def _stop_xivo_test_master():
    run('systemctl poweroff')


@hosts(SLAVE_HOST)
def _stop_xivo_test_slave():
    run('systemctl poweroff')


@task
def binaries(version):
    """(current) copy ISO and wazo client debs onto mirror (but not publicly visible)"""

    file_names = execute(_get_binaries_file_names, version).get(BUILDER_HOST)
    execute(_copy_binaries_from_current_version, version, file_names)
    execute(_copy_binaries_delta, version)
    execute(_chown_binaries, version)


@hosts(BUILDER_HOST)
def _get_binaries_file_names(version):
    return _list_files('/var/www/builder/', '*{version}*'.format(version=version))


def _list_files(path, pattern='*'):
    command = "find {path} -mindepth 1 -maxdepth 1 -name '{pattern}' -printf '%f\n' | sort".format(path=path,
                                                                                                   pattern=pattern)
    raw_output = run(command)
    if raw_output:
        return raw_output.split('\r\n')

    return []


@hosts(MIRROR_HOST)
def _copy_binaries_from_current_version(version, new_file_names):
    """take ISO from current version and put it in place of the new ISO. This
    may seem wrong, but rsync will correct it, and the correction will be a lot
    faster than transferring the whole new ISO file, as only delta will be
    transferred"""

    new_directory = '/data/iso/archives/.wazo-{version}'.format(version=version)
    run('rsync -a /data/iso/wazo-current/ {}'.format(new_directory))
    old_file_names = _list_files(new_directory)
    for old, new in zip(old_file_names, new_file_names):
        if old == new:
            continue

        command = 'mv -f {new_dir}/{old_file} {new_dir}/{new_file}'.format(new_dir=new_directory,
                                                                           old_file=old,
                                                                           new_file=new)
        run(command)


@hosts(BUILDER_HOST)
def _copy_binaries_delta(version):
    options = "-v -rl --delete --progress --include '/*{version}*' --exclude '/*'".format(version=version)
    src = '/var/www/builder/'
    dest = 'builder@mirror.wazo.community:/data/iso/archives/.wazo-{version}'.format(version=version)

    command = 'rsync {options} "{src}" "{dest}"'.format(options=options, src=src, dest=dest)
    run(command)

    puts('Created dot-directory "{dest}"'.format(dest=dest))


@hosts(MIRROR_HOST)
def _chown_binaries(version):
    command = 'chown -R www-data:www-data /data/iso/archives/.wazo-{version}'.format(version=version)
    run(command)

    chmod_files_command = 'chmod -R 664 /data/iso/archives/.wazo-{version}'.format(version=version)
    run(chmod_files_command)

    chmod_dir_command = 'chmod 775 /data/iso/archives/.wazo-{version}'.format(version=version)
    run(chmod_dir_command)


@task
def xivo_load():
    """() run wazo-upgrade on xivo-load and restart load tests"""
    stop_load_tests()
    execute(stop_load_answer)
    execute(upgrade_xivo_load)
    execute(start_load_answer)
    start_load_tests()


@hosts(LOAD_HOST)
def upgrade_xivo_load():
    run('wazo-upgrade -f')


@hosts(TRAFGEN_HOST)
def stop_load_answer():
    with settings(warn_only=True):
        run('tmux kill-session -t {session}'.format(session=LOAD_ANSWER_TMUX_SESSION))


@hosts(TRAFGEN_HOST)
def start_load_answer():
    run('tmux new-session -d -s {session} "cd xivo-load-tester ; ./load-tester scenarios/answer-then-wait/"'.format(session=LOAD_ANSWER_TMUX_SESSION))


def stop_load_tests():
    """stop load tests on xivo-load"""
    url = '{}/stop'.format(_monitoring_url())
    requests.post(url)


def start_load_tests():
    """start load tests on xivo-load"""
    url = '{}/start'.format(_monitoring_url())
    response = requests.post(url)
    assert response.status_code == 200, "{}: {}".format(response.status_code, response.text)


def _monitoring_url():
    return "{}/api/{}".format(config.get('load_tests', 'monitor_url'),
                              config.get('load_tests', 'server_name'))


@task
def shortlog(version):
    """(previous) send email: git shortlog"""
    repos_dir = config.get('general', 'repos')
    dev_email = config.get('general', 'dev_email')

    repos.raise_missing_repos('shortlog', repos_dir)
    with lcd(repos_dir), settings(warn_only=True):
        cmd = "{repos_dir}/xivo-tools/dev-tools/shortlog-xivo {version}"
        result = local(cmd.format(repos_dir=repos_dir, version=version), capture=True)

    if result.failed:
        abort(result.stderr)
    body = result

    subject = 'Shortlog entre {version} et origin/master'.format(version=version)
    send_email(dev_email, subject, body)


@task
@hosts(MASTER_HOST)
def list_tracebacks(version, start_date):
    """(current, test start date) send email: list of tracebacks (date format: 2018-01-04 14:30:00)"""
    repos = config.get('general', 'repos')
    dev_email = config.get('general', 'dev_email')

    local_path = '{repos}/xivo-tools/dev-tools/extract-traceback'.format(repos=repos)
    put(local_path, 'extract-traceback', mirror_local_mode=True)

    cmd = "./extract-traceback --after '{start_date}' /var/log/xivo-*.log* /var/log/wazo-*.log*"
    body = run(cmd.format(start_date=start_date))

    subject = 'Traceback lors de la journée de test {version}'.format(version=version)
    send_email(dev_email, subject, body)


@task
@hosts(MIRROR_HOST)
def update_wazo_rc():
    """() reprepro update wazo-rc-stretch"""

    run('reprepro -vb /data/reprepro/xivo update wazo-rc-stretch')


@task
def test_iso(host):
    """(iso_host) automatically create conditions for testing an ISO install"""

    ssh_host = 'root@{}'.format(host)

    print('Please make sure you can SSH into {}: /etc/ssh/sshd_config OR xivo-dev-ssh-pubkeys'.format(host))
    raw_input('Press a key to continue...')
    execute(_check_ssh_connection, host=ssh_host)

    password = getpass.getpass('Future webi password: ')
    confd = ConfdClient(host,
                        port=9486,
                        verify_certificate=False)

    print('Discovering wizard parameters...')
    discover = confd.wizard.discover()

    print('Configuring wizard...')
    wizard = {
        "admin_password": password,
        "license": True,
        "timezone": "America/Montreal",
        "language": "en_US",
        "entity_name": "Wazo",
        "network": {
            "hostname": "wazo-iso",
            "domain": "lan.proformatique.com",
            "interface": discover['interfaces'][0]['interface'],
            "ip_address": discover['interfaces'][0]['ip_address'],
            "netmask": discover['interfaces'][0]['netmask'],
            "gateway": discover['gateways'][0]['gateway'],
            "nameservers": discover['nameservers'],
        },
        "context_incall": {
            "display_name": "Incalls",
            "number_start": "1000",
            "number_end": "4999",
            "did_length": 4
        },
        "context_internal": {
            "display_name": "Default",
            "number_start": "1000",
            "number_end": "1999"
        },
        "context_outcall": {
            "display_name": "Outcalls"
        }
    }
    confd.wizard.create(wizard)

    print('Checking Debian installation')
    execute(_test_debian_mirrors, host=ssh_host)

    print('Checking Wazo version')
    xivo_version = execute(_get_xivo_version, host=ssh_host)[ssh_host]

    print('Creating WS user')
    execute(_create_ws_user, login='test-iso', password=password, host=ssh_host)

    auth = AuthClient(host, username='test-iso', password=password, verify_certificate=False)
    token = auth.token.new('xivo_service', expiration=60)['token']
    confd.set_token(token)

    print('Installed version of Wazo is: {}'.format(xivo_version))

    print('Creating user1')
    user1 = _create_user(confd=confd, firstname='user1', exten='1001', host=host)
    print('SIP registrar: {}'.format(host))
    print('SIP username: {}'.format(user1['endpoint']['username']))
    print('SIP password: {}'.format(user1['endpoint']['secret']))

    print('Creating user2')
    user2 = _create_user(confd=confd, firstname='user2', exten='1002', host=host)
    print('SIP registrar: {}'.format(host))
    print('SIP username: {}'.format(user2['endpoint']['username']))
    print('SIP password: {}'.format(user2['endpoint']['secret']))


def _check_ssh_connection():
    run('ls')


def _test_debian_mirrors():
    policy = run('apt-cache policy')
    assert_that(policy, contains_string('mirror.wazo.community'))

    install = run('apt-get install')
    assert_that(install, contains_string('0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.'))


def _get_xivo_version():
    return run('cat /usr/share/xivo/XIVO-VERSION')


def _create_ws_user(login, password):
    sql = "DELETE FROM accesswebservice WHERE login = 'test-iso'; INSERT INTO accesswebservice (name, login, passwd, acl) VALUES ('{login}', '{login}', '{password}', '{{confd.#, auth.#}}');".format(login=login, password=password)
    run('sudo -u postgres psql asterisk -c "{sql}" ; xivo-update-keys'.format(sql=sql))


def _create_user(confd, firstname, exten, host):
    body = {
        'firstname': firstname,
    }
    user = confd.users.create(body)

    endpoint = confd.endpoints_sip.create({})

    body = {
        'exten': exten,
        'context': 'default',
    }
    extension = confd.extensions.create(body)

    body = {
        'context': 'default',
    }
    line = confd.lines.create(body)

    confd.lines.relations(line['id']).add_endpoint_sip(endpoint['id'])
    confd.lines.relations(line['id']).add_extension(extension['id'])
    confd.lines.relations(line['id']).add_user(user['id'])

    return {'user': user,
            'line': line,
            'endpoint': endpoint,
            'extension': extension}
