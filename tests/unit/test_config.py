import sys, os
sys.path.append('tests')
sys.path.append('.')
from utils import create_config_file
import brave.config

'''
Unit test for brave/config.py
'''

def test_stun_server_config(create_config_file):
    config = {'stun_server': 'a-stun-server'}
    config_file = create_config_file(config)
    brave.config.init(config_file.name)
    assert brave.config.stun_server() == 'a-stun-server'


def test_stun_server_via_env_var():
    os.environ['STUN_SERVER'] = 'a-stun-server-from-env-var'
    brave.config.init()
    assert brave.config.stun_server() == 'a-stun-server-from-env-var'


def test_api_host_and_port_config(create_config_file):
    config = {'api_host': 'api-host', 'api_port': 12345}
    config_file = create_config_file(config)
    brave.config.init(config_file.name)
    assert brave.config.api_host() == 'api-host'
    assert brave.config.api_port() == 12345


def test_api_host_and_port_vir_env_var():
    os.environ['HOST'] = 'host-via-env'
    os.environ['PORT'] = '23456'
    brave.config.init()
    assert brave.config.api_host() == 'host-via-env'
    assert brave.config.api_port() == 23456
