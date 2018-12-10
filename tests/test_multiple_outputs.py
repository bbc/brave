import time, pytest, inspect
from utils import *


def start_with_multiple_outputs(run_brave, create_config_file, output_image_location0, output_image_location1):
    config = {
    'default_mixers': [
        {'props': {'pattern': 4}}, # 4 is red
        {'props': {'pattern': 5}} # 5 is green
    ],
    'default_outputs': [
        {'type': 'image', 'props': { 'location': output_image_location0, 'mixer_id': 1 }},
        {'type': 'image', 'props': { 'location': output_image_location1 } }
        # ,{'type': 'local'}
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(2)
    check_brave_is_running()


def test_multiple_outputs_at_startup(run_brave, create_config_file):
    output_image_location0 = create_output_image_location()
    output_image_location1 = create_output_image_location()
    start_with_multiple_outputs(run_brave, create_config_file, output_image_location0, output_image_location1)
    assert_outputs([
        {'type': 'image', 'props': { 'location': output_image_location0, 'mixer_id': 1 }},
        {'type': 'image', 'props': { 'location': output_image_location1, 'mixer_id': 0 }}
    ])
    assert_mixers([
        {'id': 0, 'props': {'pattern': 4}},
        {'id': 1, 'props': {'pattern': 5}}
    ])

    # If they've linked right, one will be red and the other will be green
    time.sleep(2)
    assert_image_file_color(output_image_location0, (0,255,0))
    assert_image_file_color(output_image_location1, (255,0,0))

def test_output_at_startup_to_missing_mixer(run_brave, create_config_file):
    config = {
    'default_outputs': [
        {'type': 'image', 'props': { 'mixer_id': 1 }},
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(1)
    check_return_value(1)

def test_multiple_outputs_at_runtime(run_brave):
    run_brave()
    time.sleep(1)

    # Mixer ID 0 exists:
    add_output({'type': 'image', 'props': {'mixer_id': 0}})

    # Mixer ID 1 does not exist:
    response = add_output({'type': 'image', 'props': {'mixer_id': 1}}, 400)
    assert 'Invalid mixer ID' in response['error']
    time.sleep(1)

    assert_outputs([{'type': 'image', 'id': 0, 'props': {'mixer_id': 0}}])

    add_mixer({})

    # Now we have a mixer, this will work:
    add_output({'type': 'image', 'props': {'mixer_id': 1}})
    # Do it again to prove we can  have multiple outputs on the same mixer
    add_output({'type': 'image', 'props': {'mixer_id': 1}})
    time.sleep(1)

    assert_outputs([{'type': 'image', 'props': {'mixer_id': 0}},
                    {'type': 'image', 'props': {'mixer_id': 1}},
                    {'type': 'image', 'props': {'mixer_id': 1}}])
