# -*- coding: UTF-8 -*-

import argparse
import os
from itertools import imap
from repo_check.repositories import xivo_repositories
from repo_check.check_local_xivo_repositories import assert_no_missing_repos
from sh import git

git_branches = git.bake('branch', '-a', '--no-color', '--no-merged', 'origin/master')


def main():
    parsed_args = _parse_args()
    directory = parsed_args.directory

    assert_no_missing_repos(directory)
    leftover = _find_prefixed_unmerged_branches(directory, parsed_args.prefix)
    _display_unmerged_branches(leftover)


def _clean_branch_name(raw_line):
    return raw_line[2:-1]


def _find_prefixed_unmerged_branches(directory, prefix):
    leftover = []
    for repository in xivo_repositories:
        repository_path = os.path.join(directory, repository)
        current_leftover = [(repository, branch)
                            for branch in _find_repo_unmerged_branches(repository_path)
                            if _is_prefixed(branch, prefix)]
        leftover.extend(current_leftover)

    return leftover


def _find_repo_unmerged_branches(repository_path):
    branches = imap(_clean_branch_name, git_branches(_cwd=repository_path, _iter=True))
    for branch in branches:
        yield branch


def _is_prefixed(branch, prefix):
    return branch.startswith(prefix) or branch.startswith('remotes/origin/' + prefix)


def _display_unmerged_branches(leftover):
    for repo, branch in leftover:
        print("{0} : {1}".format(repo, branch))


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("prefix",
                        help='prefix used to name all branches related to ticket')
    parser.add_argument("-d", "--directory",
                        help='directory containing all xivo repositories (default : $HOME/xivo_src)',
                        default=os.environ['HOME'] + '/xivo_src')
    return parser.parse_args()


if __name__ == "__main__":
    main()
