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

import argparse
import ConfigParser
import datetime
import logging
import socket
import os
import urllib2

from xivo_dao.helpers.db_utils import session_scope
from xivo_dao import init_db_from_config
from xivo_tools.helpers.http import provd_http_request
from xivo_tools.helpers.action import sysconfd, build_update_query, \
    build_insert_query, exec_sql, start_xivo_services, enable_xivo_services, \
    init_logging


def find_configured_file():
    for possible_directory in ['/var/lib/xivo', '/var/lib/pf-xivo']:
        if os.path.isdir(possible_directory):
            return possible_directory + '/configured'
    raise Exception('/var/lib/{pf-,}xivo: no such directory')

CONFIGURED_FILE = find_configured_file()
CONFIG_DIR_PATH = '/etc/xivo/xivo-tools/configure.d'
DEFAULT_CONFFILE = os.path.join(CONFIG_DIR_PATH, 'default.ini')
DEFAULT_LOG_FORMAT = '%(asctime)s (%(levelname)s): %(message)s'


class XivoConfigure(object):

    def __init__(self, parsed_args):
        config = ConfigParser.RawConfigParser()
        if parsed_args.conffile:
            logging.debug('Using conffile: %s', parsed_args.conffile)
            config.readfp(open(parsed_args.conffile))
        else:
            logging.debug('Using default conffile: %s', DEFAULT_CONFFILE)
            config.readfp(open(DEFAULT_CONFFILE))

        # GENERAL
        self.hostname = config.get('general', 'hostname')
        self.domain = config.get('general', 'domain')
        self.timezone = config.get('general', 'timezone')
        self.lang = config.get('general', 'lang')

        # NETWORK
        self.iface = config.get('network', 'iface')
        self.address = config.get('network', 'address') if config.get('network', 'address') else socket.gethostbyname(socket.gethostname())
        self.netmask = config.get('network', 'netmask')
        self.gateway = config.get('network', 'gateway')
        nameservers = config.get('network', 'nameservers')
        if nameservers:
            self.nameservers = tuple(nameservers.replace(' ', '').split(','))

        # ENTITY
        self.entity_dict = dict(config.items('entity'))

    def execute(self):
        enable_xivo_services()
        start_xivo_services()
        self.webi_user_root()
        self.hosts()
        self.resolvconf()
        self.entity()
        self.context()
        self.locale()
        self.provd()
        self.netiface()
        commonconf(self)
        sysconfd('dhcpd_update')

    def webi_user_root(self):
        logging.info('Logging to WEBI')
        data = {'passwd': 'superpass'}
        qry = build_update_query('user', data, {'id': 1})
        exec_sql(qry, data)

    def hosts(self):
        logging.info('Configuring hosts')
        hosts = {
            'hostname': self.hostname,
            'domain': self.domain
        }
        sysconfd('hosts', hosts)

    def resolvconf(self):
        logging.info('Configuring resolvconf')
        resolvconf = {
            'nameservers': list(self.nameservers),
            'search': [self.domain]
        }
        sysconfd('resolv_conf', resolvconf)

        data = {
            'hostname': self.hostname,
            'domain': self.domain,
            'nameserver1': self.nameservers[0],
            'nameserver2': self.nameservers[1],
            'search': self.domain,
            'description': 'wizard configuration'
        }

        with session_scope() as session:
            result = session.execute('SELECT id FROM "resolvconf" WHERE id=1')
            if result:
                qry = build_update_query('resolvconf', data, {'id': 1})
            else:
                qry = build_insert_query('resolvconf', data)
            session.execute(qry, data)

    def entity(self):
        logging.info('Configuring entity')
        exec_sql('DELETE FROM "entity"', {})
        entity_dict = {
            'name': 'entity',
            'displayname': 'Entity',
            'description': 'wizard configuration'
        }
        qry = build_insert_query('entity', entity_dict)
        exec_sql(qry, {})

    def context(self):
        """
        logging.info('Configuring context')
        switchboard_directory_context = {}
        internal = {}
        incall = {}
        outcall = {}
        db_ast('context', switchboard_directory_context)
        db_ast('context', internal)
        db_ast('context', incall)
        db_ast('context', outcall)
        """
        pass

    def locale(self):
        logging.info('Configuring locale')
        data = {'timezone': self.timezone}
        qry = build_update_query('general', data, {'id': 1})
        exec_sql(qry, data)

        data = {'var_val': self.lang}
        qry = build_update_query('staticsip', data, {'var_name': 'language', 'category': 'general'})
        exec_sql(qry, data)
        qry = build_update_query('staticiax', data, {'var_name': 'language', 'category': 'general'})
        exec_sql(qry, data)

        data = {'option_value': self.lang}
        qry = build_update_query('sccpgeneralsettings', data, {'option_name': 'language'})
        exec_sql(qry, data)

    def provd(self):
        logging.info('Configuring provd')
        autocreate_prefix = 'ap12345678'
        self._create_provd_autocreate_prefix(autocreate_prefix)

        config = {
            'X_type': 'registrar',
            'id': 'default',
            'deletable': False,
            'displayname': 'local',
            'parent_ids': [],
            'raw_config': {},
            'proxy_main': self.address,
            'registrar_main': self.address
        }
        self._create_provd_config(config)

        config = {
            'X_type': 'internal',
            'id': 'base',
            'deletable': False,
            'displayname': 'base',
            'parent_ids': [],
            'raw_config': {'ntp_enabled': True,
                           'ntp_ip': self.address,
                           'X_xivo_phonebook_ip': self.address},
        }
        self._create_provd_config(config)

        config = {
            'X_type': 'device',
            'id': 'defaultconfigdevice',
            'label': 'Default config device',
            'deletable': False,
            'parent_ids': [],
            'raw_config': {'ntp_enabled': True,
                           'ntp_ip': self.address},
        }
        self._create_provd_config(config)

        config = {
            'X_type': 'internal',
            'id': 'autoprov',
            'deletable': False,
            'parent_ids': ['base', 'defaultconfigdevice'],
            'role': 'autocreate',
            'raw_config': {
                'sccp_call_managers': {
                    '1': {'ip': self.address}
                },
                'sip_lines': {
                    '1': {
                          'display_name': 'Autoprov',
                          'number': 'autoprov',
                          'password': 'autoprov',
                          'proxy_ip': self.address,
                          'registrar_ip': self.address,
                          'username': autocreate_prefix
                    }
                }
            },
        }
        self._create_provd_config(config)

    def _create_provd_config(self, config):
        data = {'config': config}
        try:
            provd_http_request.run('provd/cfg_mgr/configs', data=data)
        except urllib2.HTTPError:
            logging.warning('Provd config %s already exist, pass.', config['id'])

    def _create_provd_autocreate_prefix(self, autocreate_prefix):
        data = {
            'var_val': autocreate_prefix
        }
        qry = build_update_query('staticsip', data, {'var_name': 'autocreate_prefix', 'category': 'general'})
        exec_sql(qry, data)

    def netiface(self):
        logging.info('Configuring network')
        data = {
            'ifname': self.iface,
            'hwtypeid': 1,
            'networktype': 'voip',
            'type': 'iface',
            'family': 'inet',
            'method': 'static',
            'address': self.address,
            'netmask': self.netmask,
            'broadcast': '',
            'gateway': self.gateway,
            'mtu': 1500,
            'options': '',
            'description': 'wizard configuration'
        }

        @daosession
        def sql_cmd(session, data):
            session.begin()
            row = session.execute('SELECT id FROM "netiface" WHERE ifname=:ifname', data).fetchone()
            if row:
                qry = build_update_query('netiface', data, {'id': row['id']})
            else:
                qry = build_insert_query('netiface', data)
            session.execute(qry, data)
            session.commit()
        sql_cmd(data)

        """
        data = {
            'address': self.address,
            'netmask': self.netmask,
            'gateway': self.gateway
        }
        qry = {'ifname': self.iface}
        sysconfd('modify_eth_ipv4', data, qry)
        """


@daosession
def commonconf(session, data_obj):
    logging.info('Applying configuration')
    session.begin()
    conf = {}
    row = session.execute('SELECT * FROM "dhcp" WHERE id=1').fetchone()
    if row:
        conf['dhcp_pool'] = '%s %s' % (row['pool_start'], row['pool_end'])
        conf['dhcp_extra_ifaces'] = row['extra_ifaces']
        conf['dhcp_active'] = int(row['active'])

    row = session.execute('SELECT * FROM "mail" WHERE id=1').fetchone()
    if row:
        conf['smtp_mydomain'] = row['mydomain']
        conf['smtp_origin'] = row['origin']
        conf['smtp_relayhost'] = row['relayhost']
        conf['smtp_fallback_relayhost'] = row['fallback_relayhost']
        conf['smtp_canonical'] = row['canonical']

    row = session.execute('SELECT * FROM "provisioning" WHERE id=1').fetchone()
    if row:
        conf['provd_net4_ip'] = row['net4_ip']
        conf['provd_http_port'] = row['http_port']
        conf['provd_username'] = row['username']
        conf['provd_password'] = row['password']
        conf['provd_rest_port'] = row['rest_port']
        conf['provd_rest_net4_ip'] = row['net4_ip_rest']
        conf['provd_rest_authentication'] = int(row['private'])
        conf['provd_rest_ssl'] = int(row['secure'])
        conf['provd_dhcp_integration'] = int(row['dhcp_integration'])

    row = session.execute('SELECT * FROM "monitoring" WHERE id=1').fetchone()
    if row:
        conf['maintenance'] = row['maintenance']
        if row['alert_emails']:
            conf['alert_emails'] = row['alert_emails'].replace('\r\n', ' ')
        conf['dahdi_monitor_ports'] = row['dahdi_monitor_ports']
        conf['max_call_duration'] = row['max_call_duration']

    row = session.execute('SELECT * FROM "resolvconf" WHERE id=1').fetchone()
    if row:
        conf['hostname'] = row['hostname']
        conf['domain'] = row['domain']
        conf['extra_dns_search'] = ''
        conf['nameservers'] = ' '.join(data_obj.nameservers)
    session.commit()

    conf['voip_ifaces'] = data_obj.iface
    conf['net4_ip'] = data_obj.address
    conf['net4_netmask'] = data_obj.netmask
    conf['astdb'] = 'postgresql://asterisk:proformatique@localhost/asterisk?charset=utf8'

    sysconfd('commonconf_generate', conf)
    sysconfd('commonconf_apply')


def main():
    parsed_args = _new_argument_parser()
    level = logging.DEBUG if parsed_args.debug else logging.INFO
    init_logging(DEFAULT_LOG_FORMAT, level=level)
    init_db_from_config()

    try:
        xivo_configure = XivoConfigure(parsed_args)
        xivo_configure.execute()
    except Exception, e:
        logging.exception(e)
    else:
        now = datetime.datetime.now()
        with open(CONFIGURED_FILE, 'w') as fobj:
            fobj.write(str(now))


def _new_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', action='store_true',
                        dest='debug',
                        help='increase verbosity')
    parser.add_argument('-c',
                       dest='conffile',
                       default=DEFAULT_CONFFILE,
                       help='Use configuration file <conffile> instead of %default')
    return parser.parse_args()


if __name__ == '__main__':
    main()
