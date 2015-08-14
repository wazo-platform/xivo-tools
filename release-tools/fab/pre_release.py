import requests

from fabric.api import execute, hosts, lcd, local, puts, run, task, settings

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
    execute(_stop_xivo_test_master)
    execute(_stop_xivo_test_slave)


@hosts(MASTER_HOST)
def _stop_xivo_test_master():
    run('/sbin/poweroff')


@hosts(SLAVE_HOST)
def _stop_xivo_test_slave():
    run('/sbin/poweroff')


@task
def binaries(version):
    """(current) copy ISO and xivo client debs onto mirror (but not publicly visible)"""

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

    new_directory = '/data/iso/archives/.xivo-{version}'.format(version=version)
    run('rsync -a /data/iso/xivo-current/ {}'.format(new_directory))
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
    dest = 'builder@mirror.xivo.io:/data/iso/archives/.xivo-{version}'.format(version=version)

    command = 'rsync {options} "{src}" "{dest}"'.format(options=options, src=src, dest=dest)
    run(command)

    puts('Created dot-directory "{dest}"'.format(dest=dest))


@hosts(MIRROR_HOST)
def _chown_binaries(version):
    command = 'chown -R www-data:www-data /data/iso/archives/.xivo-{version}'.format(version=version)
    run(command)

    command = 'chmod -R ug+rw /data/iso/archives/.xivo-{version}'.format(version=version)
    run(command)


@task
def xivo_load():
    """() run xivo-upgrade on xivo-load and restart load tests"""
    stop_load_tests()
    execute(stop_load_answer)
    execute(upgrade_xivo_load)
    execute(start_load_answer)
    start_load_tests()


@hosts(LOAD_HOST)
def upgrade_xivo_load():
    run('xivo-upgrade -f')


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
    """(previous) send git shortlog to dev@avencall.com"""
    repos = config.get('general', 'repos')

    with lcd(repos):
        cmd = "{repos}/xivo-tools/dev-tools/shortlog-xivo {version}"
        body = local(cmd.format(repos=repos, version=version), capture=True)

    subject = 'Shortlog entre {version} et origin/master'.format(version=version)
    send_email('dev@avencall.com', subject, body)
