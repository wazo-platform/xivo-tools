#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2013-2014 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

'''
This is a very basic script to convert all sounds file ending .wav to .g729
if they are missing.

The output written to /tmp
you should chmod +r *.g729 and copy the files to the appropriate directory manually
The current working directory only is used and the script is not recursive

Usage:
cd /usr/share/asterisk/sounds/en_US
asterisk_g729.py
cd /tmp
chmod +r *.g729
rsync -av *.g729 /usr/share/asterisk/sounds/en_US

Asterisk g729 codec is required for the conversion
'''


import os
import subprocess


def _get_files(directory, extension):
    for subdir, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(extension):
                yield f


def _difference(first, second):
    wavs = set(f[:-4] for f in first)
    g729s = set(f[:-5] for f in second)
    return wavs - g729s


def _convert_to_g729(missing_files, in_directory, out_directory):
    command_pattern = 'asterisk -rx "file convert %(in)s/%(file)s.wav %(out)s/%(file)s.g729"'
    for f in missing_files:
        command = command_pattern % {'file': f, 'in': in_directory, 'out': out_directory}
        subprocess.check_call(command, shell=True)


def main():
    directory = os.getcwd()
    wavs = _get_files(directory, '.wav')
    g729s = _get_files(directory, '.g729')
    missings = _difference(wavs, g729s)
    _convert_to_g729(missings, directory, '/tmp')


if __name__ == '__main__':
    main()
