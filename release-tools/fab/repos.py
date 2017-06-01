# -*- coding: utf-8 -*-
# Copyright 2017 The Wazo Authors  (see AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import logging
import os
import requests

logger = logging.getLogger(__name__)


def tagged_repos(tag):
    url = "http://mirror.wazo.community/repos/{}".format(tag)
    response = requests.get(url)
    response.raise_for_status()
    return response.text.splitlines()


def existing_repos(base_dir):
    return os.listdir(base_dir)


def missing_repos(tag, base_dir):
    return set(tagged_repos(tag)) - set(existing_repos(base_dir))


def raise_missing_repos(tag, base_dir):
    _missing_repos = missing_repos(tag, base_dir)
    if _missing_repos:
        message = 'Some repos are missing:\n'
        message += '\n'.join(_missing_repos)
        logger.error(message)

        command = 'git clone git@github.com:wazo-pbx/{repo} {base_dir}/{repo}'

        message = 'Here are the clone commands:\n'
        message += '\n'.join(command.format(repo=missing_repo, base_dir=base_dir) for missing_repo in _missing_repos)
        logger.error(message)

    raise SystemExit(1)
