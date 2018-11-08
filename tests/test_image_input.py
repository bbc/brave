import time, pytest
from utils import *


def test_image_input_from_command_line(run_brave, create_config_file):
    image_uri = 'file://' + test_directory() + '/assets/image_640_360.png'
    config = {
        'enable_audio': False, # useful for debugging TODO remove
        'default_inputs': [
            # {'type': 'test_video', 'props': {'pattern': 4, 'zorder': 2}}, # pattern 4 is red
            {'type': 'image', 'props': {'uri': image_uri}}, # pattern 4 is red
        ],
        'default_outputs': [
            {'type': 'local'} # good for debugging
        ]
    }
    # print('Config:', config)
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(0.5)
    check_brave_is_running()
    time.sleep(2)
    response = api_get('/api/all')
    assert response.status_code == 200
    assert_everything_in_playing_state(response.json())
