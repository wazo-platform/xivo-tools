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

from __future__ import print_function
from __future__ import unicode_literals

import os
import subprocess
import tempfile
from operator import attrgetter
from xivo.cli import utils
from xivo_ctl.command.base import BaseXivoServerCommand
from xivo_ws import User, UserLine, WebServiceRequestError


class UsersAddCommand(BaseXivoServerCommand):

    help = 'Add one user'
    usage = None

    @utils.wraps_error_as_usage_error
    def prepare(self, command_args):
        user = User()
        user.firstname = raw_input('  Firstname []: ')
        user.lastname = raw_input('  Lastname []: ')
        add_line = raw_input('  Line [Y/n] ? ')
        if not add_line or add_line.lower() == 'y':
            user.line = UserLine()
            user.line.context = raw_input('  Context []: ')
            user.line.number = raw_input('  Number []: ')
        return (user,)

    def execute(self, user):
        self._xivo_server.users.add(user)


class UsersDeleteCommand(BaseXivoServerCommand):

    help = 'Delete one or more users'
    usage = '<user_id list>'

    @utils.wraps_error_as_usage_error
    def prepare(self, command_args):
        user_id_list = command_args[0]
        user_ids = utils.compute_ids(user_id_list)
        return (user_ids,)

    def execute(self, user_ids):
        nb_users = len(user_ids)
        for user_no, user_id in enumerate(user_ids, start=1):
            try:
                print('Deleting user {0} of {1}'.format(user_no, nb_users))
                self._xivo_server.users.delete(user_id)
            except WebServiceRequestError as e:
                if e.code == 404:
                    print('could not delete user {0}: no such user'.format(user_id))
                else:
                    raise


class UsersListCommand(BaseXivoServerCommand):

    help = 'List users'
    usage = None

    def execute(self):
        user_list = self._xivo_server.users.list()
        user_list.sort(key=attrgetter('firstname', 'lastname'))
        for user in user_list:
            print('{0.id:4} {0.firstname} {0.lastname}'.format(user))



class UsersMassAddCommand(BaseXivoServerCommand):

    help = 'Add many users'
    usage = '<nb of users>'

    _MASS_ADD_TPL = """\

def user_generator():
    for no in xrange(%(nb_users)s):
        user = User()
        # add user configuration here
        start_no = 10000
        user.firstname = 'Test'
        user.lastname = '{}'.format(start_no + no)
        user.line = UserLine()
        user.line.number = start_no + no
        user.line.context = 'default'
        yield user
"""

    @utils.wraps_error_as_usage_error
    def prepare(self, command_args):
        nb_users = int(command_args[0])

        # XXX ugly ugly
        fd, filename = tempfile.mkstemp('.py')
        fobj = os.fdopen(fd, 'w')
        fobj.write('# available attributes:\n')
        for attr in User._ATTRIBUTES:
            fobj.write('#   %s' % attr.name)
            if attr.required:
                fobj.write(' (required)')
            fobj.write('\n')
        fobj.write(self._MASS_ADD_TPL % {'nb_users': nb_users})
        fobj.close()

        subprocess.call(['vim', filename])
        fobj = open(filename)
        content = fobj.read()
        fobj.close()
        os.remove(filename)

        global_dict = {'User': User, 'UserLine': UserLine}
        exec content in global_dict

        generator = global_dict[u'user_generator']
        users = list(generator())

        return (users,)

    def execute(self, users):
        nb_users = len(users)
        print('Importing {0} users...'.format(nb_users))
        self._xivo_server.users.import_(users)


class UsersMassDeleteCommand(BaseXivoServerCommand):

    help = 'Delete many users'
    usage = None

    def prepare(self, command_args):
        users = self._xivo_server.users.list()
        users.sort(key=attrgetter('firstname', 'lastname'))
        users_by_name = dict(('{0.firstname} {0.lastname}'.format(user), user.id)
                             for user in users)

        # XXX ugly ugly
        fd, filename = tempfile.mkstemp()
        fobj = os.fdopen(fd, 'w')
        for user_name in users_by_name:
            fobj.write('o {}\n'.format(user_name).encode('UTF-8'))
        fobj.close()

        subprocess.call(['vim', filename])
        fobj = open(filename)
        content = fobj.read().decode('UTF-8')
        fobj.close()
        os.remove(filename)

        user_ids = []
        for line in content.split('\n'):
            if line:
                car, user_name = line.split(' ', 1)
                if car == 'x':
                    user_ids.append(users_by_name[user_name])
        return (user_ids,)

    def execute(self, user_ids):
        nb_users = len(user_ids)
        for user_no, user_id in enumerate(user_ids, start=1):
            try:
                print('Deleting user {0} of {1}'.format(user_no, nb_users))
                self._xivo_server.users.delete(user_id)
            except WebServiceRequestError as e:
                if e.code == 404:
                    print('could not delete user {0}: no such user'.format(user_id))
                else:
                    raise
