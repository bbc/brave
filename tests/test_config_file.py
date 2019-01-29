import time, pytest, inspect
import yaml
from utils import *


def test_brave_with_no_config_file(run_brave):
    run_brave()
    check_brave_is_running()


def test_brave_with_missing_config_file(run_brave):
    run_brave('not-a-real-config-file')
    check_return_value(1)


def test_brave_with_invalid_input_type(run_brave, create_config_file):
    config = {'inputs': [{'type': 'not-a-valid-type'}]}
    config_file = create_config_file(config)
    run_brave(config_file.name)
    check_return_value(1)

def test_brave_with_full_config_file(run_brave, create_config_file):
    output_image_location = create_output_image_location()
    output_video_location = create_output_video_location()

    file_asset = test_directory() + '/assets/5_second_video.mp4'

    config = {
    'inputs': [
        {'type': 'test_video'},
        {'type': 'test_audio',  'freq': 200 } ,
        {'type': 'test_audio',  'freq': 600 } ,
        {'type': 'uri',  'uri': 'file://' + file_asset }
    ],
    'outputs': [
        {'type': 'local', 'source': 'input4'},
        {'type': 'tcp'},
        {'type': 'file', 'source': 'input1',  'location': output_video_location},
        {'type': 'image', 'source': 'input2',  'location': output_image_location}
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(3)
    check_brave_is_running()
    response = api_get('/api/all')
    assert response.status_code == 200
    assert_everything_in_playing_state(response.json())
    assert response.json()['inputs'][0]['type'] == 'test_video'
    assert response.json()['inputs'][1]['type'] == 'test_audio'
    assert response.json()['inputs'][2]['type'] == 'test_audio'
    assert response.json()['inputs'][1]['freq'] == 200
    assert response.json()['inputs'][2]['freq'] == 600
    assert response.json()['outputs'][0]['type'] == 'local'
    assert response.json()['outputs'][1]['type'] == 'tcp'
    assert response.json()['outputs'][2]['type'] == 'file'
    assert response.json()['outputs'][3]['type'] == 'image'
    assert response.json()['outputs'][2]['location'] == output_video_location
    assert response.json()['outputs'][2]['source'] == 'input1'
    assert response.json()['outputs'][3]['source'] == 'input2'


def test_non_string_keys(run_brave, create_config_file):
    config = {
        'inputs': [
            { 1: 'oh look 1 is not a string'}
        ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    check_return_value(1)


def test_config_file_with_ids(run_brave, create_config_file):
    config = {
    'inputs': [
        {'type': 'test_video'},
        {'type': 'test_video', 'id': 10}
    ],
    'outputs': [
        {'type': 'image', 'id': 1},
        {'type': 'image'},
        {'type': 'image'}
    ],
    'mixers': [
        {},
        {'id': 2}
    ],
    'overlays': [
        {'type': 'clock', 'id': 7}
    ],
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    check_brave_is_running()
    response = api_get('/api/all')
    assert response.status_code == 200
    assert len(response.json()['inputs']) == 2
    assert len(response.json()['outputs']) == 3
    assert len(response.json()['mixers']) == 2
    assert len(response.json()['overlays']) == 1
    assert response.json()['inputs'][0]['id'] == 1
    assert response.json()['inputs'][1]['id'] == 10
    assert response.json()['outputs'][0]['id'] == 1
    assert response.json()['outputs'][1]['id'] == 2
    assert response.json()['outputs'][2]['id'] == 3
    assert response.json()['mixers'][0]['id'] == 1
    assert response.json()['mixers'][1]['id'] == 2
    assert response.json()['overlays'][0]['id'] == 7
