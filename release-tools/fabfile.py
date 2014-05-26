import requests
import os

from contextlib import contextmanager as _contextmanager
from fabric.api import run, hosts, env, local, lcd, abort, cd, execute
from fabric.contrib.console import confirm
from ConfigParser import ConfigParser as _ConfigParser

MASTER_HOST = "root@xivo-test"
SLAVE_HOST = "root@xivo-test-slave"
LOAD_HOST = "root@xivo-load"
BUILDER_HOST = "root@builder-wheezy"
MIRROR_HOST = "root@mirror.xivo.fr"
GATEWAY_HOST = "root@xivo-dev-gateway"

env.hosts = [MASTER_HOST]

SCRIPT_PATH = os.path.abspath(os.path.dirname(__file__))

config = _ConfigParser()
config.read(os.path.join(SCRIPT_PATH, 'defaults.ini'))


class _Jenkins(object):

    def __init__(self, url, token):
        self.url = url
        self.token = token

    def launch(self, job_name, **kwargs):
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


def build_report():
    """build HTML report on tests executed automatically"""
    jenkins.launch('report')


@hosts(MASTER_HOST)
def shutdown_master():
    """shutdown xivo-test (once all tests are finished)"""
    run('/sbin/poweroff')


@hosts(SLAVE_HOST)
def shutdown_slave():
    """shutdown xivo-test-slave (once all tests are finished)"""
    run('/sbin/poweroff')


@hosts(BUILDER_HOST)
def copy_binaries(version):
    """copy ISO and xivo client debs onto mirror"""
    run('/root/rsync-mirror-iso {version}'.format(version=version))


@hosts(MIRROR_HOST)
def publish_binaries():
    """make ISO and debs public"""
    run('/root/publish-binary')


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


def bump_doc(old, new):
    """update documentation to next version number"""
    doc_path = config.get('doc', 'repo')

    _git_pull_master(doc_path)
    update_doc_symlinks(old, new)
    _commit_and_push(doc_path, "bump doc to {new}".format(new=new))
    merge_doc_to_production()
    update_doc_version(old, new)


def update_doc_version(old, new):
    """update version number in sphinx config"""
    doc_repo = config.get('doc', 'repo')
    cmd = "sed -i 's/{old}/{new}/g' {repo}/source/conf.py"
    local(cmd.format(old=old, new=new, repo=doc_repo))


def merge_doc_to_production():
    """merge master branch into production"""
    repo = config.get('doc', 'repo')
    with lcd(repo):
        local('git checkout production')
        local('git pull')
        local('git merge master')
        local('git push')


def update_doc_symlinks(old, new):
    """update symlinks for production documentation"""
    doc_repo = config.get('doc', 'repo')
    path = "{repo}/source/_templates".format(repo=doc_repo)
    with lcd(path):
        local('./update-symlink {old} {new}'.format(old=old, new=new))


def build_doc():
    """build production documentation"""
    jenkins.launch('doc')


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
    add_pxe_archive(version)
    execute(update_archive_on_mirror, version)


def add_pxe_archive(version):
    """add entry to PXE for an archive"""
    path = config.get('pxe', 'repo')
    _git_pull_master(path)

    cmd = "grep {version} {path}/xivo_versions_data || sed -i '/xivo_versions/ a\\{version} \\\\' {path}/xivo_versions_data"
    local(cmd.format(path=path, version=version))

    with lcd(path):
        local('./create_archive_files')

    _commit_and_push(path, "add {version}".format(version=version))


@hosts(MIRROR_HOST)
def update_archive_on_mirror(version):
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
    comment_cmd = "sed -i '/Codename: {codename}/,/^$/ s/#Update/Update/' {path}"
    decomment_cmd = "sed -i '/Codename: {codename}/,/^$/ s/Update/#Update/' {path}"

    run(comment_cmd.format(codename=codename, path=path))
    yield
    run(decomment_cmd.format(codename=codename, path=path))
