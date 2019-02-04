import time, pytest, inspect
from utils import *


def test_image_output(run_brave, create_config_file):
    output_image_location = create_output_image_location()

    config = {
    'mixers': [{'sources': [{'uid': 'input1', 'zorder': 2}]}],
    'inputs': [
        {'type': 'test_video', 'pattern': 4}, # pattern 4 is red
    ],
    'outputs': [
        {'type': 'local'}, # good for debugging
        {'type': 'image',  'location': output_image_location } 
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(4)
    check_brave_is_running()
    response = api_get('/api/all')
    assert response.status_code == 200
    assert_everything_in_playing_state(response.json())


    assert_image_file_color(output_image_location, (255,0,0))
