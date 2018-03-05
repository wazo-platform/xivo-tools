import os

from ConfigParser import ConfigParser

from jenkins import Jenkins

SCRIPT_PATH = os.path.abspath(os.path.dirname(__file__))
DEFAULT_CONFIG_PATH = os.path.join(SCRIPT_PATH, '..', 'defaults.ini')
CUSTOM_CONFIG_PATH = os.path.join(SCRIPT_PATH, '..', 'defaults.ini.local')

config = ConfigParser()
config.read([DEFAULT_CONFIG_PATH, CUSTOM_CONFIG_PATH])

MASTER_HOST = "root@xivo-test"
SLAVE_HOST = "root@xivo-test-slave"
LOAD_HOST = "root@xivo-load"
BUILDER_HOST = "builder@builder-32"
MIRROR_HOST = "root@mirror.wazo.community"
GATEWAY_HOST = "root@wazo-dev-gateway"
TRAFGEN_HOST = "trafgen@trafgen"

jenkins = Jenkins(config.get('jenkins', 'url'))
jenkins_token = config.get('jenkins', 'token')
