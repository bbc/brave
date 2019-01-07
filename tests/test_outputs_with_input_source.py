import time, pytest, inspect
from utils import *


def test_outputs_with_input_source(run_brave):
    run_brave('config/empty.yaml')
    check_brave_is_running()
    subtest_can_connect_input_to_output()
    subtest_can_connect_change_output_to_another_input()
    subtest_can_connect_change_output_from_input_to_mixer()
    subtest_deleting_mixer_removes_it_as_source()

def subtest_can_connect_input_to_output():
    add_input({'type': 'test_video', 'pattern': 4}) # pattern 4 is green
    add_output({'type': 'image', 'source': 'input1'})
    time.sleep(1)
    assert_outputs([{'type': 'image', 'id': 1, 'source': 'input1'}])
    assert_everything_in_playing_state()
    time.sleep(2)
    assert_image_output_color(1, [255, 0, 0])

def subtest_can_connect_change_output_to_another_input():
    add_input({'type': 'test_video', 'pattern': 5}) # pattern 5 is green

    # Will fail whilst in PLAYING state:
    update_output(1, {'source': 'input2'}, 400)
    assert_outputs([{'type': 'image', 'id': 1, 'source': 'input1'}])

    # But will succeed in the READY state
    update_output(1, {'state': 'READY'})
    update_output(1, {'source': 'input2'})
    update_output(1, {'state': 'PLAYING'})
    time.sleep(1)
    assert_outputs([{'type': 'image', 'id': 1, 'source': 'input2'}])
    assert_everything_in_playing_state()
    time.sleep(2)
    assert_image_output_color(1, [0, 255, 0])

def subtest_can_connect_change_output_from_input_to_mixer():
    add_mixer({'pattern': 6}) # pattern 5 is blue
    # Will fail whilst in PLAYING state:
    update_output(1, {'source': 'mixer1'}, 400)
    assert_outputs([{'type': 'image', 'id': 1, 'source': 'input2'}])

    # But will succeed in the READY state
    update_output(1, {'state': 'READY'})
    update_output(1, {'source': 'mixer1'})
    update_output(1, {'state': 'PLAYING'})
    time.sleep(1)
    assert_outputs([{'type': 'image', 'id': 1, 'source': 'mixer1'}])
    assert_everything_in_playing_state()
    time.sleep(2)
    assert_image_output_color(1, [0, 0, 255])

def subtest_deleting_mixer_removes_it_as_source():
    delete_mixer(1)
    time.sleep(1)
    assert_everything_in_playing_state()
    response = api_get('/api/outputs')
    assert response.status_code == 200
    assert len(response.json()) == 1
    output_details = response.json()[0]
    assert output_details['source'] is None
