#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import fnmatch
import os

from distutils.core import setup


def is_package(path):
    is_svn_dir = fnmatch.fnmatch(path, '*/.svn*')
    is_test_module = fnmatch.fnmatch(path, '*tests')
    return not (is_svn_dir or is_test_module)

packages = [p for p, _, _ in os.walk('xivo_tools') if is_package(p)]


setup(
    name='xivo-tools',
    version='0.1',
    description='XiVO Tools',
    author='Avencall',
    author_email='dev@avencall.com',
    url='https://github.com/xivo-pbx/xivo-tools',
    packages=packages,
    scripts=['bin/xivo-configure', 'bin/xivo-reset'],
)
