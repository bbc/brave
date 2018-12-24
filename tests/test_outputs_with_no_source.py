import time, pytest, inspect
from utils import *


def test_outputs_with_no_source(run_brave, create_config_file):
    start_with_two_outputs(run_brave, create_config_file)
    assert_outputs([
        {'type': 'image', 'id': 0, 'source': None},
        {'type': 'image', 'id': 1, 'source': 'mixer0'}
    ])

    update_output(0, {'state': 'ready'})
    update_output(1, {'state': 'ready'})

    update_output(0, {'source': 'mixer0'})
    update_output(1, {'source': 'none'})

    update_output(0, {'state': 'playing'})
    update_output(1, {'state': 'playing'})
    time.sleep(2)

    assert_outputs([
        {'type': 'image', 'id': 0, 'source': 'mixer0', 'state': 'PLAYING'},
        {'type': 'image', 'id': 1, 'source': None, 'state': 'PAUSED'}  # Goes PAUSED when no source
    ], check_playing_state=False)

def start_with_two_outputs(run_brave, create_config_file):
    output_video_location = create_output_video_location()

    config = {
    'default_mixers': [{}],
    'default_outputs': [
        {'type': 'image', 'source': 'none'},
        {'type': 'image'},  # Will default to mixer0
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(2)
    check_brave_is_running()

#     run_brave('config/empty.yaml')
#     check_brave_is_running()
#     subtest_can_connect_input_to_output()
#     subtest_can_connect_change_output_to_another_input()
#     subtest_can_connect_change_output_from_input_to_mixer()
#     subtest_deleting_mixer_removes_it_as_source()
#
# def subtest_can_connect_input_to_output():
#     add_input({'type': 'test_video', 'props': {'pattern': 4}}) # pattern 4 is green
#     add_output({'type': 'image', 'source': 'input0'})
#     time.sleep(1)
#     assert_outputs([{'type': 'image', 'id': 0, 'source': 'input0'}])
#     assert_everything_in_playing_state()
#     time.sleep(2)
#     assert_image_output_color(0, [255, 0, 0])
#
# def subtest_can_connect_change_output_to_another_input():
#     add_input({'type': 'test_video', 'props': {'pattern': 5}}) # pattern 5 is green
#
#     # Will fail whilst in PLAYING state:
#     update_output(0, {'source': 'input1'}, 400)
#     assert_outputs([{'type': 'image', 'id': 0, 'source': 'input0'}])
#
#     # But will succeed in the READY state
#     update_output(0, {'state': 'READY'})
#     update_output(0, {'source': 'input1'})
#     update_output(0, {'state': 'PLAYING'})
#     time.sleep(1)
#     assert_outputs([{'type': 'image', 'id': 0, 'source': 'input1'}])
#     assert_everything_in_playing_state()
#     time.sleep(2)
#     assert_image_output_color(0, [0, 255, 0])
#
# def subtest_can_connect_change_output_from_input_to_mixer():
#     add_mixer({'props': {'pattern': 6}}) # pattern 5 is blue
#     # Will fail whilst in PLAYING state:
#     update_output(0, {'source': 'mixer0'}, 400)
#     assert_outputs([{'type': 'image', 'id': 0, 'source': 'input1'}])
#
#     # But will succeed in the READY state
#     update_output(0, {'state': 'READY'})
#     update_output(0, {'source': 'mixer0'})
#     update_output(0, {'state': 'PLAYING'})
#     time.sleep(1)
#     assert_outputs([{'type': 'image', 'id': 0, 'source': 'mixer0'}])
#     assert_everything_in_playing_state()
#     time.sleep(2)
#     assert_image_output_color(0, [0, 0, 255])
#
# def subtest_deleting_mixer_removes_it_as_source():
#     delete_mixer(0)
#     time.sleep(1)
#     assert_everything_in_playing_state()
#     response = api_get('/api/outputs')
#     assert response.status_code == 200
#     assert len(response.json()) == 1
#     output_details = response.json()[0]
#     assert 'source' not in output_details
