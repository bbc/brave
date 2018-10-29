import time, pytest, inspect
from utils import *


def test_image_output(run_brave, create_config_file):
    output_image_location = create_output_image_location()

    config = {
    'default_inputs': [
        {'type': 'test_video', 'props': {'pattern': 4, 'zorder': 2}}, # pattern 4 is red
    ],
    'default_outputs': [
        {'type': 'local'}, # good for debugging
        {'type': 'image', 'props': { 'location': output_image_location } }
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(4)
    check_brave_is_running()
    response = api_get('/api/all')
    assert response.status_code == 200
    assert_everything_in_playing_state(response.json())


    assert_image_color(output_image_location, (255,0,0))
