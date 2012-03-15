# -*- coding: UTF-8 -*-

import os.path
import subprocess

COMMANDS_DIR = os.path.join(os.path.dirname(__file__), 'commands')


def run_internal_command(args):
    new_args = list(args)
    new_args[0] = os.path.join(COMMANDS_DIR, new_args[0])
    _run_command(new_args)


def _run_command(args):
    process = subprocess.Popen(args)
    process.communicate()
    if process.returncode:
        raise Exception(process)


def run_external_command(args):
    _run_command(args)


def run_provd_pycli_command(pycli_command):
    new_args = ['provd_pycli', '-p', '', '-c', pycli_command]
    _run_command(new_args)


def run_external_command_as_postgres(psql_command):
    new_args = ['su', '-', '-c', psql_command, 'postgres']
    _run_command(new_args)
