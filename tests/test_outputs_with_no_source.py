import time, pytest, inspect
from utils import *


def test_outputs_with_no_source(run_brave, create_config_file):
    start_with_two_outputs(run_brave, create_config_file)
    assert_outputs([
        {'type': 'image', 'id': 1, 'source': None},
        {'type': 'image', 'id': 2, 'source': 'mixer1'}
    ])

    update_output(1, {'state': 'ready'})
    update_output(2, {'state': 'ready'})

    update_output(1, {'source': 'mixer1'})
    update_output(2, {'source': None})

    update_output(1, {'state': 'playing'})
    update_output(2, {'state': 'playing'})
    time.sleep(2)

    assert_outputs([
        {'type': 'image', 'id': 1, 'source': 'mixer1', 'state': 'PLAYING'},
        {'type': 'image', 'id': 2, 'source': None, 'state': 'PAUSED'}  # Goes PAUSED when no source
    ], check_playing_state=False)

def start_with_two_outputs(run_brave, create_config_file):
    output_video_location = create_output_video_location()

    config = {
    'mixers': [{}],
    'outputs': [
        {'type': 'image', 'source': None},
        {'type': 'image'},  # Will default to mixer1
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(2)
    check_brave_is_running()
