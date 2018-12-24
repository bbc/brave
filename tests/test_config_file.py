import time, pytest, inspect
from utils import *


def test_brave_with_no_config_file(run_brave):
    run_brave()
    check_brave_is_running()


def test_brave_with_missing_config_file(run_brave):
    run_brave('not-a-real-config-file')
    check_return_value(1)


def test_brave_with_invalid_input_type(run_brave, create_config_file):
    config = {'default_inputs': [{'type': 'not-a-valid-type'}]}
    config_file = create_config_file(config)
    run_brave(config_file.name)
    check_return_value(1)

def test_brave_with_full_config_file(run_brave, create_config_file):
    output_image_location = create_output_image_location()
    output_video_location = create_output_video_location()

    file_asset = test_directory() + '/assets/5_second_video.mp4'

    config = {
    'default_inputs': [
        {'type': 'test_video'},
        {'type': 'test_audio', 'props': { 'freq': 200 } },
        {'type': 'test_audio', 'props': { 'freq': 600 } },
        {'type': 'uri', 'props': { 'uri': 'file://' + file_asset } }
    ],
    'default_outputs': [
        {'type': 'local'},
        {'type': 'tcp'},
        {'type': 'file', 'source': 'input0', 'props': { 'location': output_video_location}},
        {'type': 'image', 'source': 'input1', 'props': { 'location': output_image_location}}
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
    assert response.json()['inputs'][1]['props']['freq'] == 200
    assert response.json()['inputs'][2]['props']['freq'] == 600
    assert response.json()['outputs'][0]['type'] == 'local'
    assert response.json()['outputs'][1]['type'] == 'tcp'
    assert response.json()['outputs'][2]['type'] == 'file'
    assert response.json()['outputs'][3]['type'] == 'image'
    assert response.json()['outputs'][2]['props']['location'] == output_video_location
    assert response.json()['outputs'][2]['source'] == 'input0'
    assert response.json()['outputs'][3]['source'] == 'input1'
