import time, pytest
from utils import *


def test_uri_input_from_command_line(run_brave, create_config_file):
    uri = 'file://' + test_directory() + '/assets/5_second_video.mp4'
    config = {
        # 'enable_audio': False, # useful for debugging TODO remove
        'default_inputs': [
            {'type': 'uri', 'props': {'uri': uri}},
        ],
        'default_outputs': [
            {'type': 'local'} # good for debugging
        ]
    }

    response_json = run_brave_and_get_all_response(run_brave, create_config_file(config))
    assert_everything_in_playing_state(response_json)

    subtest_check_deleted_input_goes_away()


def test_missing_file_input_from_command_line(run_brave, create_config_file):
    uri = 'file:///does-not-exist'
    config = {
        # 'enable_audio': False, # useful for debugging TODO remove
        'default_inputs': [
            {'type': 'uri', 'props': {'uri': uri}},
        ],
        'default_outputs': [
            {'type': 'local'} # good for debugging
        ]
    }

    response_json = run_brave_and_get_all_response(run_brave, create_config_file(config))

    # Expect NULL state for the input, otherwise everything is PLAYING
    assert_outputs_in_playing_state(response_json)
    assert_mixers_in_playing_state(response_json)
    assert len(response_json['inputs']) == 1
    assert response_json['inputs'][0]['state'] == 'NULL'
    subtest_check_deleted_input_goes_away()


def subtest_check_deleted_input_goes_away():
    # Now delete the input, it should go away
    delete_input(1)
    time.sleep(1)
    response = api_get('/api/all')
    assert response.status_code == 200
    response_json = response.json()

    assert len(response_json['inputs']) == 0
    assert_everything_in_playing_state(response_json)


def run_brave_and_get_all_response(run_brave, config_file):
    run_brave(config_file.name)
    time.sleep(0.5)
    check_brave_is_running()
    time.sleep(1.5)
    response = api_get('/api/all')
    assert response.status_code == 200
    return response.json()
