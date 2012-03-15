# -*- coding: UTF-8 -*-

from __future__ import absolute_import

import logging
from xivo_reset import actions
from xivo_reset.bin import commands


def main():
    _init_logging()
    commands.execute_command(_XivoResetCommand())


def _init_logging():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)


class _XivoResetCommand(commands.AbstractCommand):
    def configure_parser(self, parser):
        parser.add_argument("-v", "--verbose", action="store_true", default=False,
                            help="increase logging verbosity")

    def configure_subcommands(self, subcommands):
        subcommands.add_subcommand(_CleanSubcommand('clean'))
        subcommands.add_subcommand(_AddSubcommand('add'))
        subcommands.add_subcommand(_StoreSubcommand('store'))
        subcommands.add_subcommand(_RestoreSubcommand('restore'))
        subcommands.add_subcommand(_DoSubcommand('do'))

    def pre_execute(self, parsed_args):
        if parsed_args.verbose:
            logger = logging.getLogger()
            logger.setLevel(logging.INFO)


class _CleanSubcommand(commands.AbstractSubcommand):
    def execute(self, parsed_args):
        print "Cleaning up asterisk DB..."
        self._clean_asterisk_db()
        self._clean_provd_db()

    def _clean_asterisk_db(self):
        actions.stop_services()
        actions.drop_asterisk_db()
        actions.recreate_asterisk_db()
        actions.insert_autocreate_prefix()
        actions.start_services()

    def _clean_provd_db(self):
        actions.remove_provd_devices()
        actions.remove_provd_configs()
        actions.recreate_base_configs()
        actions.sip_reload()


class _AddSubcommand(commands.AbstractSubcommand):
    def execute(self, parsed_args):
        print "Adding contexts..."
        actions.add_contexts()
        print "Adding users..."
        actions.add_users()
        print "Adding agents..."
        actions.add_agents()
        print "Adding queues..."
        actions.add_queues()


class _StoreSubcommand(commands.AbstractSubcommand):
    def execute(self, parsed_args):
        print "Storing asterisk + xivo + provd data..."
        actions.dump_asterisk_db()
        actions.dump_xivo_db()
        actions.store_provd_data()


class _RestoreSubcommand(commands.AbstractSubcommand):
    def execute(self, parsed_args):
        print "Restoring asterisk + xivo + provd data..."
        actions.stop_services()
        actions.stop_provd()
        actions.restore_asterisk_db()
        actions.restore_xivo_db()
        actions.restore_provd_data()
        actions.start_provd()
        actions.start_services()


class _DoSubcommand(commands.AbstractSubcommand):
    def configure_parser(self, parser):
        parser.add_argument("action_name",
                            help="name of the action to carry on")

    def execute(self, parsed_args):
        print "Doing %r action..." % parsed_args.action_name
        action_fun = getattr(actions, parsed_args.action_name)
        action_fun()


if __name__ == "__main__":
    main()
