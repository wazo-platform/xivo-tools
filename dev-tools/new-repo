#!/usr/bin/env python
# SPDX-License-Identifier: GPL-3.0+

import argparse
import sys

from github3 import login
from getpass import getpass

parser = argparse.ArgumentParser()
parser.add_argument('repo_name', help='name of the Github repository to be created')
parser.add_argument('-u', '--user', required=True, help='Github username')
args = parser.parse_args()

repo_name = args.repo_name
user = args.user
password = getpass('GitHub password for {0}: '.format(user))

if not (user and password):
    print("Refusing to login without a username and password.")
    sys.exit(1)

github = login(user, password)
wazo_pbx = github.organization('wazo-platform')

repo = wazo_pbx.create_repository(repo_name)

if repo:
    print(repo.ssh_url)

repo.create_hook('web',
                 config={'url': 'https://jenkins.wazo.community/github-webhook/'})
