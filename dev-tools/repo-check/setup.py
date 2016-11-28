#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import fnmatch
import os

from distutils.core import setup


def is_package(path):
    is_svn_dir = fnmatch.fnmatch(path, '*/.svn*')
    is_test_module = fnmatch.fnmatch(path, '*tests')
    return not (is_svn_dir or is_test_module)

packages = [p for p, _, _ in os.walk('repo_check') if is_package(p)]


setup(
    name='repo-check',
    version='1.0',
    description='XiVO Merge assistant',
    author='Avencall',
    author_email='dev@avencall.com',
    url='https://github.com/wazo-pbx/xivo-tools',
    packages=packages,
    scripts=['bin/check_local_xivo_repositories',
             'bin/check_unmerged_branches'],
    license='GPLv3',
    long_description=open('README.md').read(),

)
