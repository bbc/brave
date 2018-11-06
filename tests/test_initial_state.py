import time, pytest, inspect
from utils import *


def test_initial_state_option_on_startup(run_brave, create_config_file):
    '''
    Test that if 'initial_state' is set as a property, it is honored.
    It can be set for inputs, outputs and mixers.
    '''
    output_image_location0 = create_output_image_location()
    output_image_location1 = create_output_image_location()

    config = {
    'default_inputs': [
        {'type': 'test_video', 'props': {'pattern': 4, 'initial_state': 'PLAYING'}},
        {'type': 'test_video', 'props': {'pattern': 5, 'initial_state': 'PAUSED'}},
        {'type': 'test_video', 'props': {'pattern': 6, 'initial_state': 'READY'}},
        {'type': 'test_video', 'props': {'pattern': 7, 'initial_state': 'NULL'}},
    ],
    'default_mixers': [
        {'props': {'initial_state': 'PLAYING'}},
        {'props': {'initial_state': 'PAUSED'}},
        {'props': {'initial_state': 'READY'}},
        {'props': {'initial_state': 'NULL'}},
    ],
    'default_outputs': [
        {'type': 'image', 'props': {'location': output_image_location0, 'initial_state': 'PLAYING'}},
        {'type': 'image', 'props': {'location': output_image_location0, 'initial_state': 'PAUSED'}},
        {'type': 'image', 'props': {'location': output_image_location0, 'initial_state': 'READY'}},
        {'type': 'image', 'props': {'location': output_image_location0, 'initial_state': 'NULL'}},
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(2)
    check_brave_is_running()
    response = api_get('/api/all')
    assert response.status_code == 200
    details = response.json()
    assert details['inputs'][0]['state'] == 'PLAYING'
    assert details['inputs'][1]['state'] == 'PAUSED'
    assert details['inputs'][2]['state'] == 'READY'
    assert details['inputs'][3]['state'] == 'NULL'
    assert details['mixers'][0]['state'] == 'PLAYING'
    assert details['mixers'][1]['state'] == 'PAUSED'
    assert details['mixers'][2]['state'] == 'READY'
    assert details['mixers'][3]['state'] == 'NULL'
    assert details['outputs'][0]['state'] == 'PLAYING'
    assert details['outputs'][1]['state'] == 'PAUSED'
    assert details['outputs'][2]['state'] == 'READY'
    assert details['outputs'][3]['state'] == 'NULL'


def test_initial_state_option_via_api(run_brave):
    '''
    Test that if 'initial_state' is set as a property, it is honored.
    It can be set for inputs, outputs and mixers.
    '''
    run_brave()
    check_brave_is_running()
    response = api_get('/api/all')
    assert response.status_code == 200
    assert_everything_in_playing_state(response.json())
    output_image_location0 = create_output_image_location()

    add_input({'type': 'test_audio', 'props': {'initial_state': 'NULL'}})
    add_input({'type': 'test_audio', 'props': {'initial_state': 'READY'}})
    add_input({'type': 'test_audio', 'props': {'initial_state': 'PAUSED'}})
    add_input({'type': 'test_audio', 'props': {'initial_state': 'PLAYING'}})

    # TODO Uncomment when the API adds support for creating new mixers
    # add_mixer({'props': {'initial_state': 'NULL'}})
    # add_mixer({'props': {'initial_state': 'READY'}})
    # add_mixer({'props': {'initial_state': 'PAUSED'}})
    # add_mixer({'props': {'initial_state': 'PLAYING'}})

    add_output({'type': 'image', 'props': {'location': output_image_location0, 'initial_state': 'NULL'}})
    add_output({'type': 'image', 'props': {'location': output_image_location0, 'initial_state': 'READY'}})
    add_output({'type': 'image', 'props': {'location': output_image_location0, 'initial_state': 'PAUSED'}})
    add_output({'type': 'image', 'props': {'location': output_image_location0, 'initial_state': 'PLAYING'}})

    time.sleep(1)

    response = api_get('/api/all')
    assert response.status_code == 200
    details = response.json()
    print(response.json())
    assert details['inputs'][0]['state'] == 'NULL'
    assert details['inputs'][1]['state'] == 'READY'
    assert details['inputs'][2]['state'] == 'PAUSED'
    assert details['inputs'][3]['state'] == 'PLAYING'

    # Mixer 0 is the default:
    assert details['mixers'][0]['state'] == 'PLAYING'

    # TODO Uncomment when the API adds support for creating new mixers
    # assert details['mixers'][1]['state'] == 'NULL'
    # assert details['mixers'][2]['state'] == 'READY'
    # assert details['mixers'][3]['state'] == 'PAUSED'
    # assert details['mixers'][4]['state'] == 'PLAYING'

    assert details['outputs'][0]['state'] == 'NULL'
    assert details['outputs'][1]['state'] == 'READY'
    assert details['outputs'][2]['state'] == 'PAUSED'
    assert details['outputs'][3]['state'] == 'PLAYING'
