import time, pytest, inspect
from utils import *
from PIL import Image

'''
This test ensures that if there are multiple mixers, sharing multiple playing inputs,
they all successfully share without imacting each other.
'''

MIXER1 = {
    'width': 160,
    'height': 90,
    'pattern': 3 # Black
}
MIXER2 = {
    'width': 640,
    'height': 360
}

# INPUT1 is RED and INPUT2 is GREEN:
INPUT1 = {'type': 'test_video', 'pattern': 4 }
INPUT2 = {'type': 'test_video', 'pattern': 5 }
OUTPUT1 = {'type': 'image', 'source': 'mixer1'}
OUTPUT2 = {'type': 'image', 'source': 'mixer2'}


def test_mixer_from_config(run_brave, create_config_file):
    subtest_start_brave_with_mixers(run_brave, create_config_file)

    # Both mixers will be green because green INPUT1 has a higher zorder
    assert_image_output_color(1, [0, 255, 0])
    assert_image_output_color(2, [0, 255, 0])

    subtest_ensure_one_mixer_does_not_affect_another()
    subtest_addition_of_input()
    subtest_overlay_of_new_input()

    subtest_addition_of_mixer()
    subtest_addition_of_destination_to_new_mixer()
    subtest_overlay_of_input_onto_new_mixer()


def subtest_ensure_one_mixer_does_not_affect_another():
    # Set mixer1 to just use INPUT1. It should go RED, leaving mixer 2 on GREEN:
    cut_to_source('input1', 1)
    time.sleep(3)
    assert_image_output_color(1, [255, 0, 0])
    assert_image_output_color(2, [0, 255, 0])


def subtest_addition_of_input():
    # Create a third input. This is BLUE
    new_input = add_input({'type': 'test_video', 'pattern': 6})
    cut_to_source(new_input['uid'], 1)
    time.sleep(3)

    # We added this to mixer 1 only, so it will be blue whilst mixer 2 remains green:
    assert_image_output_color(1, [0, 0, 255])
    assert_image_output_color(2, [0, 255, 0])


def subtest_overlay_of_new_input():
    # We overlay the new input onto mixer 2, but to a lower zorder than the existing content:
    overlay_source('input3', 2, details={'zorder': 5})
    time.sleep(3)

    # Mixer 2 will not have changed, because the zorder is too low
    assert_image_output_color(2, [0, 255, 0])

    # Now, let's increase the zorder, to bring it to the front
    overlay_source('input3', 2, details={'zorder': 40})
    time.sleep(3)
    assert_image_output_color(2, [0, 0, 255])


def subtest_start_brave_with_mixers(run_brave, create_config_file):
    config = {
        'mixers': [
            # TODO different zorders for different mixers:
            {**MIXER1, 'sources': [{'uid': 'input1', 'zorder': 10}, {'uid': 'input2', 'zorder': 20}]},
            {**MIXER2, 'sources': [{'uid': 'input1', 'zorder': 10}, {'uid': 'input2', 'zorder': 20}]}
        ],
        'inputs': [INPUT1, INPUT2],
        'outputs': [OUTPUT1, OUTPUT2]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    check_brave_is_running()
    time.sleep(4)
    assert_mixers([
        {'id': 1, **MIXER1},
        {'id': 2, **MIXER2}
    ])
    assert_inputs([INPUT1, INPUT2])
    assert_outputs([OUTPUT1, OUTPUT2])


def subtest_addition_of_mixer():
    response = add_mixer({})
    assert response['id'] == 3
    time.sleep(3)
    response = api_get('/api/all')
    assert response.status_code == 200
    assert_everything_in_playing_state(response.json())
    response_json = response.json()

    # By default, a new mixer gets no sources:
    assert response_json['mixers'][2]['sources'] == []


def subtest_addition_of_destination_to_new_mixer():
    add_output({'type': 'image', 'source': 'mixer2'})
    time.sleep(2)
    response = api_get('/api/all')
    assert response.status_code == 200
    assert_everything_in_playing_state(response.json())


def subtest_overlay_of_input_onto_new_mixer():
    cut_to_source('input3', 3, details={'zorder': 30})
    time.sleep(2)

    # Now all three outputs will be input 2, i.e. blue
    assert_image_output_color(1, [0, 0, 255])
    assert_image_output_color(2, [0, 0, 255])
    assert_image_output_color(3, [0, 0, 255])
