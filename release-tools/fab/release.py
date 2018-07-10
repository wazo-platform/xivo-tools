# -*- coding: utf-8 -*-
# Copyright 2015-2018 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import re

from contextlib import contextmanager
from fabric.api import abort, cd, execute, hosts, local, lcd, puts, run, task
from fabric.contrib.console import confirm

from .config import config
from .config import jenkins, jenkins_token
from .config import MIRROR_HOST
from .config import GATEWAY_HOST
from . import repos


@task
@hosts(MIRROR_HOST)
def binaries():
    """() make ISO and debs public"""

    with cd('/data/iso'):
        binaries_path = 'archives'
        candidates = _list_files(binaries_path, pattern='.wazo-*')
        if not candidates:
            abort('Nothing to publish')

        for hidden_name in candidates:
            visible_name = hidden_name[1:]
            if confirm('Do you want to publish {candidate}?'.format(candidate=visible_name)):
                command = 'mv "{path}/{hidden}" "{path}/{visible}"'.format(path=binaries_path,
                                                                           hidden=hidden_name,
                                                                           visible=visible_name)
                run(command)
                command = 'ln -sfn "archives/{candidate}" wazo-current'.format(candidate=visible_name)
                run(command)
                command = 'ln -sfn "archives/{candidate}"/wazoclient-*-x86.exe wazoclient-latest-x86.exe'.format(candidate=visible_name)
                run(command)
                command = 'ln -sfn "archives/{candidate}"/wazoclient-*.dmg wazoclient-latest.dmg'.format(candidate=visible_name)
                run(command)
                command = 'ln -sfn "archives/{candidate}"/wazoclient-*-amd64.deb wazoclient-latest-amd64.deb'.format(candidate=visible_name)
                run(command)
                command = 'ln -sfn "archives/{candidate}"/wazo-*amd64.iso wazo-latest-amd64.iso'.format(candidate=visible_name)
                run(command)
                command = 'ln -sfn "archives/{candidate}"/wazo-*i386.iso wazo-latest.iso'.format(candidate=visible_name)
                run(command)
                puts('{candidate} is now the current version'.format(candidate=visible_name))


def _list_files(path, pattern='*'):
    command = "find {path} -mindepth 1 -maxdepth 1 -name '{pattern}' -printf '%f\n' | sort".format(path=path,
                                                                                                   pattern=pattern)
    raw_output = run(command)
    if raw_output:
        return raw_output.split('\r\n')

    return []


@task
@hosts(GATEWAY_HOST)
def upgrade_dev_gateway():
    """() run wazo-upgrade on xivo-dev-gateway"""
    run('wazo-upgrade -f')


@task
def doc(prod, dev):
    """(current, next) update documentation to next version number"""
    doc_path = config.get('doc', 'repo')

    _git_pull_master(doc_path)
    # Freeze stable on 18.03
    # _merge_doc_to_stable()
    _update_doc_version(prod, dev)


def _merge_doc_to_stable():
    repo = config.get('doc', 'repo')
    with lcd(repo):
        local('git checkout stable')
        local('git pull')
        local('git merge --no-edit master')
        local('git push')


def _update_doc_version(prod, dev):
    repo = config.get('doc', 'repo')
    with lcd(repo):
        local('git checkout master')
    prod = re.escape(prod)
    cmd = "sed -i 's/{prod}/{dev}/g' {repo}/source/conf.py"
    local(cmd.format(prod=prod, dev=dev, repo=repo))
    _commit_and_push(repo, "bump version to {dev}".format(dev=dev))


@task
def tag(version):
    """(current) tag wazo repos with version number"""
    repos_dir = config.get('general', 'repos')
    repos.raise_missing_repos('python-tag', repos_dir)
    cmd = "{repos_dir}/xivo-tools/dev-tools/tag_wazo -v {version} -d {repos_dir}"
    local(cmd.format(repos_dir=repos_dir, version=version))


@task
@hosts(MIRROR_HOST)
def deb_dist():
    """() publish RC debian packages on official mirror"""
    if not confirm("Are you sure you want to publish packages on official mirror ?"):
        abort("publish cancelled")

    codename = "phoenix-stretch"
    path = "/data/reprepro/xivo/conf/distributions"

    with _active_distribution(codename, path):
        run("reprepro -vb /data/reprepro/xivo update phoenix-stretch")


@contextmanager
def _active_distribution(codename, path):
    uncomment_cmd = "sed -i '/Codename: {codename}/,/^$/ s/#Update/Update/' {path}"
    comment_cmd = "sed -i '/Codename: {codename}/,/^$/ s/Update/#Update/' {path}"

    run(uncomment_cmd.format(codename=codename, path=path))
    yield
    run(comment_cmd.format(codename=codename, path=path))


@task
def archive(version):
    """(current) create an archived version of wazo on mirror and PXE"""
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
    codename = "wazo-{version}".format(version=version)
    archive_path = "/data/reprepro/archive"
    distribution_file = "{}/conf/distributions".format(archive_path)

    with cd("{}/conf".format(archive_path)):
        run("git pull")

    run("reprepro -vb {path} export".format(path=archive_path))

    with _active_distribution(codename, distribution_file):
        cmd = "reprepro -vb {path} update wazo-{version}"
        run(cmd.format(path=archive_path, version=version))


@task
def version(stable, unstable):
    """(current, next) update wazo version numbers on mirror and debian package"""
    jenkins.job_build('public-versions', {'UNSTABLE': unstable, 'STABLE': stable}, jenkins_token)

    repo = config.get('version', 'repo')

    _git_pull_master(repo)
    local('echo {unstable} > {repo}/VERSION'.format(unstable=unstable, repo=repo))
    _commit_and_push(repo, "bump version ({unstable})".format(unstable=unstable))

    repo = config.get('alembic', 'repo')

    _git_pull_master(repo)
    filename = 'bump_version_{version}'.format(version=unstable.replace('.', '_'))
    with lcd(repo):
        local('alembic -x wazo_version={version} revision -m {filename}'.format(
            version=unstable,
            filename=filename
        ))
        local('git add -A *{filename}.py'.format(filename=filename))

        cmd = """sed -i -r '/^INSERT INTO "infos"/s/[0-9]+\.[0-9]+(\.[0-9]+)?/{}/' populate/populate.sql"""
        local(cmd.format(unstable))

    _commit_and_push(repo, "bump version ({unstable})".format(unstable=unstable))


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


@task
def api():
    """() update http://api.wazo.community (swagger)"""
    jenkins.job_build('deploy-swagger-doc', token=jenkins_token)
