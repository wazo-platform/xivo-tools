# -*- coding: UTF-8 -*-
#
# Copyright (C) 2014 Avencall
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


import logging
import urllib2

from xivo_dao.helpers.db_manager import daosession
from xivo_tools.helpers.http import sysconfd_http_request


def enable_xivo_services():
    logging.info('Enabling XiVO services')
    data = {'xivo-service': 'enable'}
    sysconfd('xivoctl', data)


def start_xivo_services():
    logging.info('Starting XiVO services')
    data = {'xivo-service': 'start xivo'}
    sysconfd('xivoctl', data)


def stop_xivo_services():
    logging.info('Stopping XiVO services')
    data = {'xivo-service': 'stop xivo'}
    sysconfd('xivoctl', data)


def restart_xivo_services():
    stop_xivo_services()
    start_xivo_services()


def build_update_query(table, data, where_dict):
    fields_str = ','.join(['%s=:%s' % (key, key) for key in data.iterkeys()])
    where = ' AND '.join('"%s"=\'%s\'' % (key, value) for (key, value) in where_dict.items())
    return 'UPDATE "%s" SET %s WHERE %s' % (table, fields_str, where)


def build_insert_query(table, data):
    columns = '","'.join(['%s' % key for key in data.iterkeys()])
    values = '\',\''.join(['%s' % value for value in data.itervalues()])
    return 'INSERT INTO "%s" ("%s") VALUES(\'%s\')' % (table, columns, values)


def init_logging(log_format, level):
    logging.basicConfig(format=log_format, level=level)


@daosession
def exec_sql(session, qry, data={}):
    session.begin()
    session.execute(qry, data)
    session.commit()


def sysconfd(action, data=None, qry=None):
    try:
        sysconfd_http_request.run('%s' % action, qry=qry, data=data)
    except urllib2.HTTPError, e:
        logging.error('sysconfd command %s with msg %s', action, e)
