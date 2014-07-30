# -*- coding: UTF-8 -*-

import argparse
import os
from repo_check.check_local_xivo_repositories import assert_no_missing_repos
from repo_check.git import find_repo_merged_branches, display_branches, fetch_all_repositories
from repo_check.repositories import xivo_repositories


def main():
    parsed_args = _parse_args()
    directory = parsed_args.directory

    assert_no_missing_repos(directory)
    fetch_all_repositories(os.path.join(directory, xivo_rep) for xivo_rep in xivo_repositories)
    leftover = _find_merged_branches(directory)
    display_branches(leftover)


def _find_merged_branches(directory):
    leftover = []
    for repository in xivo_repositories:
        repository_path = os.path.join(directory, repository)
        current_leftover = [(repository, branch)
                            for branch in find_repo_merged_branches(repository_path)]
        leftover.extend(current_leftover)

    return leftover


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory",
                        help='directory containing all xivo repositories (default : $HOME/xivo_src)',
                        default=os.environ['HOME'] + '/xivo_src')
    return parser.parse_args()


if __name__ == "__main__":
    main()
