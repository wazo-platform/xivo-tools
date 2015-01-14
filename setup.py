#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import fnmatch
import os

from setuptools import setup
from setuptools import find_packages


setup(
    name='xivo-tools',
    version='0.1',
    description='XiVO Tools',
    author='Avencall',
    author_email='dev@avencall.com',
    url='https://github.com/xivo-pbx/xivo-tools',
    packages=find_packages(),
    scripts=['bin/xivo-configure', 'bin/xivo-reset'],
)
