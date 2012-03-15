# -*- coding: UTF-8 -*-

import os.path
from xivo_reset.run import run_internal_command,\
    run_external_command_as_postgres, run_external_command

VAR_DIR = os.path.join(os.getcwd(), 'var')


def dump_db(db_name, filename):
    abs_filename = os.path.join(VAR_DIR, filename)
    run_internal_command(['dump-db', db_name, abs_filename])


def restore_db(db_name, filename):
    run_external_command_as_postgres('dropdb %s' % db_name)
    abs_filename = os.path.join(VAR_DIR, filename)
    run_internal_command(['restore-db', abs_filename])


def store_files(src_directory):
    dst_directory = os.path.join(VAR_DIR, os.path.basename(src_directory))
    run_external_command(['rm', '-rf', dst_directory])
    run_external_command(['cp', '-a', src_directory, dst_directory])


def restore_files(dst_directory):
    src_directory = os.path.join(VAR_DIR, os.path.basename(dst_directory))
    run_external_command(['rm', '-rf', dst_directory])
    run_external_command(['cp', '-a', src_directory, dst_directory])
