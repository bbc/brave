import time, pytest, inspect
from utils import *


def start_with_multiple_outputs(run_brave, create_config_file, output_image_location1, output_image_location2):
    config = {
    'mixers': [
        {'pattern': 4}, # 4 is red
        {'pattern': 5} # 5 is green
    ],
    'outputs': [
        {'type': 'image', 'source': 'mixer2',  'location': output_image_location1 },
        {'type': 'image',  'location': output_image_location2 } 
        # ,{'type': 'local'}
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(2)
    check_brave_is_running()


def test_multiple_outputs_at_startup(run_brave, create_config_file):
    output_image_location1 = create_output_image_location()
    output_image_location2 = create_output_image_location()
    start_with_multiple_outputs(run_brave, create_config_file, output_image_location1, output_image_location2)
    assert_outputs([
        {'type': 'image', 'source': 'mixer2',  'location': output_image_location1 },
        {'type': 'image', 'source': 'mixer1',  'location': output_image_location2 }
    ])
    assert_mixers([
        {'id': 1, 'pattern': 4},
        {'id': 2, 'pattern': 5}
    ])

    # If they've linked right, one will be red and the other will be green
    time.sleep(2)
    assert_image_file_color(output_image_location1, (0,255,0))
    assert_image_file_color(output_image_location2, (255,0,0))

def test_output_at_startup_to_missing_mixer(run_brave, create_config_file):
    config = {
    'outputs': [
        {'type': 'image', 'source': 'mixer2'},
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(1)
    check_return_value(1)

def test_multiple_outputs_at_runtime(run_brave):
    run_brave()
    time.sleep(1)

    # Mixer ID 1 exists:
    add_output({'type': 'image', 'source': 'mixer1'})

    # Mixer ID 2 does not exist:
    response = add_output({'type': 'image', 'source': 'mixer2'}, 400)
    assert 'does not exist' in response['error']
    time.sleep(0.5)

    assert_outputs([{'type': 'image', 'id': 1, 'source': 'mixer1'}])
    add_mixer({})

    # Now we have a second mixer, this will work:
    add_output({'type': 'image', 'source': 'mixer2'})
    # Do it again to prove we can  have multiple outputs on the same mixer
    add_output({'type': 'image', 'source': 'mixer2'})
    time.sleep(1)

    assert_outputs([{'type': 'image', 'source': 'mixer1'},
                    {'type': 'image', 'source': 'mixer2'},
                    {'type': 'image', 'source': 'mixer2'}])
