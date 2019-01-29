import time, pytest, inspect
import yaml
from utils import *

'''
Tests for /api/config/current.yaml
'''

def test_empty_config_file(run_brave, create_config_file):
    config = {}
    subtest_start_brave_and_check_config_file(run_brave, create_config_file, config)

def test_simple_config_file(run_brave, create_config_file):
    config = {
        'enable_video': False,
        'inputs': [{'type': 'test_video'}],
        'mixers': [{}],
        'outputs': [{'type': 'local', 'source': 'input1'}],
    }
    subtest_start_brave_and_check_config_file(run_brave, create_config_file, config)

def test_complex_config_file(run_brave, create_config_file):
    config = {
        'default_mixer_width': 123,
        'stun_server': 'some_stun_server',
        'inputs': [
            {'type': 'test_video'},
            {'type': 'test_audio',  'freq': 200 } ,
            {'type': 'test_audio',  'freq': 600, 'id': 6 }
        ],
        'mixers': [
            {'sources': [{'uid': 'input1'}, {'uid': 'input2'}]},
            {'state': 'READY', 'id': 2} ,
        ],
        'overlays': [
            {'type': 'clock', 'valignment': 'top', 'source': 'input1', 'id': 9}
        ],
        'outputs': [
            {'type': 'local', 'source': 'input6', 'id': 17},
            {'type': 'tcp', 'source': 'input2'},
            {'type': 'file', 'source': 'input1', 'location': '/tmp/x', 'state': 'NULL'},
            {'type': 'image', 'source': 'mixer2'}
        ]
    }

    subtest_start_brave_and_check_config_file(run_brave, create_config_file, config)

def subtest_start_brave_and_check_config_file(run_brave, create_config_file, config):
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(0.5)
    check_brave_is_running()
    subtest_validate_config_response(config)

def subtest_validate_config_response(orig):
    config_response = api_get('/api/config/current.yaml')
    assert config_response.status_code == 200
    parsed = yaml.load(config_response.text)

    check_first_dict_exists_in_second(orig, parsed)

def check_first_dict_exists_in_second(a, b):
    for key, value in a.items():
        assert key in b
        if isinstance(value, list):
            check_first_array_exists_in_second(value, b[key])
        else:
            # print('Comparing %s with %s' % (value, b[key]))
            assert value == b[key]

def check_first_array_exists_in_second(a, b):
    assert len(a) == len(b)
    for i in range(len(a)):
        check_first_dict_exists_in_second(a[i], b[i])
