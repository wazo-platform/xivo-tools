import requests
import os
import wiki

from contextlib import contextmanager as _contextmanager
from fabric.api import abort, cd, execute, hosts, local, lcd, puts, run
from fabric.contrib.console import confirm
from ConfigParser import ConfigParser as _ConfigParser

MASTER_HOST = "root@xivo-test"
SLAVE_HOST = "root@xivo-test-slave"
LOAD_HOST = "root@xivo-load"
BUILDER_HOST = "root@builder-wheezy"
MIRROR_HOST = "root@mirror.xivo.io"
GATEWAY_HOST = "root@xivo-dev-gateway"


SCRIPT_PATH = os.path.abspath(os.path.dirname(__file__))

config_file_names = [os.path.join(SCRIPT_PATH, file_name) for file_name in ('defaults.ini', 'defaults.ini.local')]
config = _ConfigParser()
config.read(config_file_names)


class _Jenkins(object):

    def __init__(self, url, token):
        self.url = url
        self.token = token

    def launch(self, section, **kwargs):
        job_name = config.get(section, 'job_name')
        if kwargs:
            self._launch_post(job_name, kwargs)
        else:
            self._launch_get(job_name)

    def _launch_get(self, job_name):
        url = self._build_url('build', job_name)
        params = {'token': self.token}

        return self._get_response('GET', url, params)

    def _launch_post(self, job_name, params):
        url = self._build_url('buildWithParameters', job_name)
        params['token'] = self.token

        self._get_response('POST', url, params)

    def _build_url(self, endpoint, job_name):
        url = "{url}/job/{name}/{endpoint}".format(url=self.url,
                                                   endpoint=endpoint,
                                                   name=job_name)
        return url

    def _get_response(self, method, url, params):
        response = requests.request(method, url, params=params)
        msg = "{}: {}".format(response.status_code, response.text.encode('utf8'))
        assert response.status_code == 201, msg

        return response


jenkins = _Jenkins(config.get('jenkins', 'url'),
                   config.get('jenkins', 'token'))


def build_report_auto():
    """build HTML report on tests executed automatically"""
    jenkins.launch('report_auto')


def build_report_manual():
    """build HTML report on tests executed manually"""
    jenkins.launch('report_manual')


@hosts(MASTER_HOST)
def shutdown_master():
    """shutdown xivo-test (once all tests are finished)"""
    run('/sbin/poweroff')


@hosts(SLAVE_HOST)
def shutdown_slave():
    """shutdown xivo-test-slave (once all tests are finished)"""
    run('/sbin/poweroff')


def copy_binaries(version):
    """copy ISO and xivo client debs onto mirror (but not publicly visible)"""

    file_names = execute(_get_binaries_file_names, version).get(BUILDER_HOST)
    execute(_copy_binaries_from_current_version, version, file_names)
    execute(_copy_binaries_delta, version)


def _list_files(path, pattern='*'):
    command = "find {path} -mindepth 1 -maxdepth 1 -name '{pattern}' -printf '%f\n' | sort".format(path=path,
                                                                                                   pattern=pattern)
    raw_output = run(command)
    if raw_output:
        return raw_output.split('\r\n')

    return []


@hosts(BUILDER_HOST)
def _get_binaries_file_names(version):
    return _list_files('/var/www/builder/', '*{version}*'.format(version=version))


@hosts(MIRROR_HOST)
def _copy_binaries_from_current_version(version, new_file_names):
    """take ISO from current version and put it in place of the new ISO. This
    may seem wrong, but rsync will correct it, and the correction will be a lot
    faster than transferring the whole new ISO file, as only delta will be
    transferred"""

    new_directory = '/data/iso/archives/.xivo-{version}'.format(version=version)
    run('cp -rp /data/iso/xivo-current/ {}'.format(new_directory))
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
    options = "-v -rlpt --delete --progress --include '/*{version}*' --exclude '/*'".format(version=version)
    src = '/var/www/builder/'
    dest = 'www-data@mirror.xivo.io:/data/iso/archives/.xivo-{version}'.format(version=version)

    command = 'rsync {options} "{src}" "{dest}"'.format(options=options, src=src, dest=dest)
    run(command)

    puts('Created dot-directory "{dest}"'.format(dest=dest))


@hosts(MIRROR_HOST)
def publish_binaries():
    """make ISO and debs public"""

    with cd('/data/iso'):
        binaries_path = 'archives'
        candidates = _list_files(binaries_path, pattern='.xivo-*')
        if not candidates:
            abort('Nothing to publish')

        for hidden_name in candidates:
            visible_name = hidden_name[1:]
            if confirm('Do you want to publish {candidate}?'.format(candidate=visible_name)):
                command = 'mv "{path}/{hidden}" "{path}/{visible}"'.format(path=binaries_path,
                                                                           hidden=hidden_name,
                                                                           visible=visible_name)
                run(command)
                command = 'ln -sfn "archives/{candidate}" xivo-current'.format(candidate=visible_name)
                run(command)
                puts('{candidate} is now the current version'.format(candidate=visible_name))


@hosts(LOAD_HOST)
def upgrade_xivo_load():
    """run xivo-upgrade on xivo-load and restart load tests"""
    stop_load_tests()
    run('xivo-upgrade -f')
    start_load_tests()


@hosts(LOAD_HOST)
def stop_load_tests():
    """stop load tests on xivo-load"""
    url = '{}/stop'.format(_monitoring_url())
    requests.post(url)


@hosts(LOAD_HOST)
def start_load_tests():
    """start load tests on xivo-load"""
    url = '{}/start'.format(_monitoring_url())
    response = requests.post(url)
    assert response.status_code == 200, "{}: {}".format(response.status_code, response.text)


@hosts(GATEWAY_HOST)
def upgrade_dev_gateway():
    """run xivo-upgrade on xivo-dev-gateway"""
    run('xivo-upgrade -f')


def bump_doc(prod, dev):
    """update documentation to next version number"""
    doc_path = config.get('doc', 'repo')

    _git_pull_master(doc_path)
    _update_doc_symlinks(prod, dev)
    _merge_doc_to_production()
    _update_doc_version(prod, dev)


def _update_doc_symlinks(prod, dev):
    repo = config.get('doc', 'repo')
    path = "{repo}/source/_templates".format(repo=repo)
    with lcd(path):
        local('./update-symlink {prod} {dev}'.format(prod=prod, dev=dev))
    _commit_and_push(repo, "update symlinks for {prod}".format(prod=prod))


def _merge_doc_to_production():
    repo = config.get('doc', 'repo')
    with lcd(repo):
        local('git checkout production')
        local('git pull')
        local('git merge master')
        local('git push')


def _update_doc_version(prod, dev):
    repo = config.get('doc', 'repo')
    with lcd(repo):
        local('git checkout master')
    cmd = "sed -i 's/{prod}/{dev}/g' {repo}/source/conf.py"
    local(cmd.format(prod=prod, dev=dev, repo=repo))
    _commit_and_push(repo, "bump version to {dev}".format(dev=dev))


def tag_repos(version):
    """tag xivo repos with version number"""
    repos = config.get('general', 'repos')
    cmd = "{repos}/xivo-tools/dev-tools/tag_xivo -v {version} -d {repos}"
    local(cmd.format(repos=repos, version=version))


def build_xivo_fai():
    """build xivo-fai"""
    jenkins.launch('fai')


@hosts(MIRROR_HOST)
def backport_squeeze():
    """generate upgrade packages for squeeze"""
    run('/root/backport-squeeze')


@hosts(MIRROR_HOST)
def publish_rc_to_prod():
    """publish RC debian packages on official mirror"""
    if not confirm("Are you sure you want to publish packages on official mirror ?"):
        abort("publish cancelled")

    codename = "xivo-five"
    path = "/data/reprepro/xivo/conf/distributions"

    with _active_distribution(codename, path):
        run("reprepro -vb /data/reprepro/xivo update xivo-five")


def create_archive(version):
    """create an archived version of xivo on mirror and PXE"""
    _add_pxe_archive(version)
    execute(_update_archive_on_mirror, version)


def _add_pxe_archive(version):
    """add entry to PXE for an archive"""
    path = config.get('pxe', 'repo')
    _git_pull_master(path)

    cmd = "grep {version} {path}/xivo_versions_data || sed -i '/xivo_versions/ a\\{version} \\\\' {path}/xivo_versions_data"
    local(cmd.format(path=path, version=version))

    with lcd(path):
        local('./get_or_update_sources')
        local('./create_archive_files')

    _commit_and_push(path, "add {version}".format(version=version))


@hosts(MIRROR_HOST)
def _update_archive_on_mirror(version):
    """update distributions and mirrors for archive"""
    codename = "xivo-{version}".format(version=version)
    archive_path = "/data/reprepro/archive"
    distribution_file = "{}/conf/distributions".format(archive_path)

    with cd("{}/conf".format(archive_path)):
        run("git pull")

    run("reprepro -vb {path} export".format(path=archive_path))

    with _active_distribution(codename, distribution_file):
        cmd = "reprepro -vb {path} update xivo-{version}"
        run(cmd.format(path=archive_path, version=version))


def prepare_xivo_version(prod, dev):
    """update xivo version numbers on mirror"""
    jenkins.launch('version', XIVO_VERSION_DEV=dev, XIVO_VERSION_PROD=prod)


def bump_version(new):
    """bump version number in git repo"""
    repo = config.get('version', 'repo')

    _git_pull_master(repo)
    local('echo {new} > {repo}/VERSION'.format(new=new, repo=repo))
    _commit_and_push(repo, "bump version ({new})".format(new=new))


def _monitoring_url():
    return "{}/api/{}".format(config.get('load_tests', 'monitor_url'),
                              config.get('load_tests', 'server_name'))


def _git_pull_master(path):
    msg = '{path}: not on master ! (currently on {branch}). continue anyway ?'

    with lcd(path):
        current_branch = local('git rev-parse --abbrev-ref HEAD', capture=True).strip()
        msg = msg.format(path=path, branch=current_branch)

        if current_branch != 'master' and not confirm(msg):
            abort('{path} was not on master'.format(path=path))

        local('git pull')


def _commit_and_push(path, message):
    with lcd(path):
        local('git commit -a -m "{message}"'.format(message=message))
        local('git push')


@_contextmanager
def _active_distribution(codename, path):
    uncomment_cmd = "sed -i '/Codename: {codename}/,/^$/ s/#Update/Update/' {path}"
    comment_cmd = "sed -i '/Codename: {codename}/,/^$/ s/Update/#Update/' {path}"

    run(uncomment_cmd.format(codename=codename, path=path))
    yield
    run(comment_cmd.format(codename=codename, path=path))


def update_wiki_link(version):
    """Update download link on wiki.xivo.io"""
    wiki.update_link(config, version)
