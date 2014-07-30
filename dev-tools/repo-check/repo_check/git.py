# -*- coding: UTF-8 -*-

from itertools import imap
from sh import git


def find_repo_unmerged_branches(repository_path):
    _fetch_repo(repository_path)
    git_branches = git.bake('branch', '-a', '--no-color', '--no-merged', 'origin/master')
    branches = imap(_clean_branch_name, git_branches(_cwd=repository_path, _iter=True))
    for branch in branches:
        yield branch


def find_repo_merged_branches(repository_path):
    _fetch_repo(repository_path)
    git_branches = git.bake('branch', '-a', '--no-color', '--merged', 'origin/master')
    for raw_branch in git_branches(_cwd=repository_path, _iter=True):
        if 'master' in raw_branch:
            continue
        yield _clean_branch_name(raw_branch)


def _clean_branch_name(raw_line):
    return raw_line[2:-1]


def _fetch_repo(repository_path):
    git_fetch = git.bake('fetch', '-p')
    git_fetch(_cwd=repository_path)


def display_branches(leftover):
    for repo, branch in leftover:
        print("{0} : {1}".format(repo, branch))
