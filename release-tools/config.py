import os

from ConfigParser import ConfigParser

from jenkins import _Jenkins

SCRIPT_PATH = os.path.abspath(os.path.dirname(__file__))
DEFAULT_CONFIG_PATH = os.path.join(SCRIPT_PATH, 'defaults.ini')
CUSTOM_CONFIG_PATH = os.path.join(SCRIPT_PATH, 'defaults.ini.local')

config = ConfigParser()
config.read([DEFAULT_CONFIG_PATH, CUSTOM_CONFIG_PATH])

MASTER_HOST = "root@xivo-test"
SLAVE_HOST = "root@xivo-test-slave"
LOAD_HOST = "root@xivo-load"
BUILDER_HOST = "root@builder-wheezy"
MIRROR_HOST = "root@mirror.xivo.io"
GATEWAY_HOST = "root@xivo-dev-gateway"
TRAFGEN_HOST = "trafgen@trafgen"

jenkins = _Jenkins(config.get('jenkins', 'url'),
                   config.get('jenkins', 'token'))
