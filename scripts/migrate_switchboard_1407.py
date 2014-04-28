#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import sys
from itertools import chain
from provd.rest.client.client import new_provisioning_client
from provd.operation import parse_oip, OIP_SUCCESS, OIP_FAIL
from time import sleep


def main():
    parsed_args = parse_args()

    provd_client = new_provisioning_client(parsed_args.url)
    pg_mgr = provd_client.plugin_manager()
    pg_install_srv = pg_mgr.install_service()
    dev_mgr = provd_client.device_manager()

    installed_plugins = pg_install_srv.installed()

    # find all Aastra devices
    aastra_devices = dev_mgr.find({'plugin': 'xivo-aastra-switchboard'})

    # find all Snom devices
    snom_devices = dev_mgr.find({'plugin': 'xivo-snom-switchboard'})

    # if no devices found, exit
    if not aastra_devices and not snom_devices:
        print 'No switchboard devices found.'
        uninstall_old_plugins(pg_install_srv, installed_plugins)
        sys.exit(0)

    print 'Found %s devices using the xivo-aastra-switchboard plugin.' % len(aastra_devices)
    print 'Found %s devices using the xivo-snom-switchboard plugin.' % len(snom_devices)

    # update the list of plugins
    pg_install_srv = pg_mgr.install_service()
    update_pkgs(pg_install_srv, 'Updating the list of installable plugins...')

    # install the latest xivo-aastra plugin or upgrade it
    if aastra_devices:
        installable_plugins = pg_install_srv.installable()
        aastra_plugin_name = ''
        for plugin_name in installable_plugins:
            if plugin_name == 'xivo-aastra-switchboard':
                continue
            if plugin_name.startswith('xivo-aastra') and plugin_name > aastra_plugin_name:
                aastra_plugin_name = plugin_name

        if not aastra_plugin_name:
            print >>sys.stderr, 'No xivo-aastra plugins available. Aborting.'
            sys.exit(1)

        # install or upgrade the plugin
        if aastra_plugin_name in installed_plugins:
            upgrade_pkg(pg_install_srv, aastra_plugin_name, 'Upgrading the %s plugin...' % aastra_plugin_name)
        else:
            install_pkg(pg_install_srv, aastra_plugin_name, 'Installing the %s plugin...' % aastra_plugin_name)

        # install the firmware and language files
        aastra_plugin = pg_mgr.plugin(aastra_plugin_name)
        aastra_plugin_install_srv = aastra_plugin.install_service()
        installed_pkg_ids = aastra_plugin_install_srv.installed()
        models = set(device.get('model') for device in aastra_devices)
        if '6731i' in models:
            pkg_id = '6731i-fw'
            if pkg_id not in installed_pkg_ids:
                install_pkg(aastra_plugin_install_srv, pkg_id, 'Installing the 6731i firmware...')
        if '6755i' in models:
            pkg_id = '6755i-fw'
            if pkg_id not in installed_pkg_ids:
                install_pkg(aastra_plugin_install_srv, pkg_id, 'Installing the 6755i firmware...')
        if '6757i' in models:
            pkg_id = '6757i-fw'
            if pkg_id not in installed_pkg_ids:
                install_pkg(aastra_plugin_install_srv, pkg_id, 'Installing the 6757i firmware...')
        pkg_id = 'lang'
        if pkg_id not in installed_pkg_ids:
            install_pkg(aastra_plugin_install_srv, pkg_id, 'Installing the language files...')

    # install the latest xivo-snom plugin or upgrade it
    if snom_devices:
        installable_plugins = pg_install_srv.installable()
        snom_plugin_name = ''
        for plugin_name in installable_plugins:
            if plugin_name == 'xivo-snom-switchboard':
                continue
            if plugin_name.startswith('xivo-snom') and plugin_name > snom_plugin_name:
                snom_plugin_name = plugin_name

        if not snom_plugin_name:
            print >>sys.stderr, 'No xivo-snom plugins available. Aborting.'
            sys.exit(1)

        # install or upgrade the plugin
        if snom_plugin_name in installed_plugins:
            upgrade_pkg(pg_install_srv, snom_plugin_name, 'Upgrading the %s plugin...' % snom_plugin_name)
        else:
            install_pkg(pg_install_srv, snom_plugin_name, 'Installing the %s plugin...' % snom_plugin_name)

        # install the firmware and language files
        snom_plugin = pg_mgr.plugin(snom_plugin_name)
        snom_plugin_install_srv = snom_plugin.install_service()
        installed_pkg_ids = snom_plugin_install_srv.installed()
        models = set(device.get('model') for device in snom_devices)
        if '720' in models:
            pkg_id = '720-fw'
            if pkg_id not in installed_pkg_ids:
                install_pkg(snom_plugin_install_srv, pkg_id, 'Installing the 720 firmware...')
        pkg_id = 'lang'
        if pkg_id not in installed_pkg_ids:
            install_pkg(snom_plugin_install_srv, pkg_id, 'Installing the language files...')

    # migrate aastra devices
    for device in aastra_devices:
        device[u'plugin'] = aastra_plugin_name
        device[u'options'] = {u'switchboard': True}
        print 'Updating device %s...' % (device.get(u'mac', 'unknown')),
        sys.stdout.flush()
        dev_mgr.update(device)
        print 'ok.'

    # migrate snom devices
    for device in snom_devices:
        device[u'plugin'] = snom_plugin_name
        device[u'options'] = {u'switchboard': True}
        print 'Updating device %s...' % (device.get(u'mac', 'unknown')),
        sys.stdout.flush()
        dev_mgr.update(device)
        print 'ok.'

    # synchronize all the devices
    for device in chain(aastra_devices, snom_devices):
        sync_dev(dev_mgr, device, 'Synchronizing device %s...' % (device.get(u'mac', 'unknown')))

    uninstall_old_plugins(pg_install_srv, installed_plugins)


def uninstall_old_plugins(pg_install_srv, installed_plugins):
    if 'xivo-aastra-switchboard' in installed_plugins:
        print 'Uninstalling xivo-aastra-switchboard plugin...'
        pg_install_srv.uninstall('xivo-aastra-switchboard')
    if 'xivo-snom-switchboard' in installed_plugins:
        print 'Uninstalling xivo-snom-switchboard plugin...'
        pg_install_srv.uninstall('xivo-snom-switchboard')


def update_pkgs(install_srv, msg):
    print msg,
    sys.stdout.flush()
    oip = install_srv.update()
    _print_progress(oip)


def upgrade_pkg(install_srv, pkg_id, msg):
    print msg,
    sys.stdout.flush()
    oip = install_srv.upgrade(pkg_id)
    _print_progress(oip)


def install_pkg(install_srv, pkg_id, msg):
    print msg,
    sys.stdout.flush()
    oip = install_srv.install(pkg_id)
    _print_progress(oip)


def sync_dev(dev_mgr, device, msg):
    print msg,
    sys.stdout.flush()
    oip = dev_mgr.synchronize(device['id'])
    last_state = _print_progress(oip)


def _print_progress(oip):
    while True:
        sleep(1)
        sys.stdout.write('.')
        sys.stdout.flush()
        parsed_oip = parse_oip(oip.status())
        if parsed_oip.state == OIP_SUCCESS or parsed_oip.state == OIP_FAIL:
            break
    oip.delete()
    if parsed_oip.state == OIP_SUCCESS:
        print ' ok.'
    else:
        print ' fail.'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8666/provd',
                        help='xivo-provd base URL')
    return parser.parse_args()


main()
