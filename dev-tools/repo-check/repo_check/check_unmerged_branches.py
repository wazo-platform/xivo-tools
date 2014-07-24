# -*- coding: UTF-8 -*-

import argparse
import os
from repo_check.repositories import xivo_repositories
from repo_check.check_local_xivo_repositories import assert_no_missing_repos
import sh


def main(directory, prefix):
    assert_no_missing_repos(directory)
    print _find_prefixed_leftover_branches(directory, prefix)


def _find_prefixed_leftover_branches(directory, prefix):
    leftover = []
    for repository in xivo_repositories:
        repository_path = os.path.join(directory, repository)
        current_leftover = [(repository, branch)
                            for branch in _find_repo_unmerged_branches(repository_path)
                            if _is_prefixed(branch, prefix)]
        leftover.extend(current_leftover)

    return leftover


def _find_repo_unmerged_branches(repository_path):
    raw_results = sh.git('branch',
                         '-a',
                         '--no-color',
                         '--no-merged',
                         'origin/master',
                         _cwd=repository_path)
    return [b[2:] for b in raw_results.split('\n')
            if b.strip()]


def _is_prefixed(branch, prefix):
    return branch.startswith(prefix) or branch.startswith('remotes/origin/' + prefix)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("prefix",
                        help='prefix used to name all branches related to ticket')
    parser.add_argument("-d", "--directory",
                        help='directory containing all xivo repositories (default : $HOME/xivo_src)',
                        default=os.environ['HOME'] + '/xivo_src')
    return parser.parse_args()


if __name__ == "__main__":
    parsed_args = _parse_args()
    main(parsed_args.directory, parsed_args.prefix)
