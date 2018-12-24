import time, pytest, inspect
from utils import *
from PIL import Image

def test_overlays_on_multiple_mixers(run_brave, create_config_file):
    set_up_overlay_at_start(run_brave, create_config_file)
    assert_mixers([{'id': 0, 'state': 'PLAYING'},
                   {'id': 1, 'state': 'PLAYING'}])
    assert_overlays([{'id': 0, 'state': 'PLAYING', 'source': 'mixer1'},
                     {'id': 1, 'state': 'PLAYING', 'source': 'mixer1'},
                     {'id': 2, 'state': 'PLAYING', 'source': 'mixer0'}])

    add_overlay({'type': 'text', 'source': 'mixer0', 'props': {'text': 'Overlay #3', 'visible': True}})
    add_overlay({'type': 'text', 'source': 'mixer1', 'props': {'text': 'Overlay #4', 'visible': True}})
    time.sleep(1)
    assert_overlays([{'id': 0, 'state': 'PLAYING', 'source': 'mixer1'},
                     {'id': 1, 'state': 'PLAYING', 'source': 'mixer1'},
                     {'id': 2, 'state': 'PLAYING', 'source': 'mixer0'},
                     {'id': 3, 'state': 'PLAYING', 'source': 'mixer0'},
                     {'id': 4, 'state': 'PLAYING', 'source': 'mixer1'}])

    delete_overlay(1)
    delete_overlay(2)
    time.sleep(1)
    assert_overlays([{'id': 0, 'state': 'PLAYING', 'source': 'mixer1'},
                     {'id': 3, 'state': 'PLAYING', 'source': 'mixer0'},
                     {'id': 4, 'state': 'PLAYING', 'source': 'mixer1'}])

    # TODO confirm this returns a 400
    add_overlay({'type': 'text', 'source': 'mixer999', 'props': {'text': 'Overlay #3'}}, status_code=400)


def test_overlay_on_unknown_mixer_returns_error(run_brave, create_config_file):
    config = {'default_overlays': [
        {'type': 'text', 'source': 'mixer999', 'props': {'text': 'No such mixer', 'visible': False}},
    ]}
    config_file = create_config_file(config)
    run_brave(config_file.name)
    check_return_value(1)


def set_up_overlay_at_start(run_brave, create_config_file):
    output_video_location = create_output_video_location()

    config = {
    'default_overlays': [
        {'type': 'text', 'source': 'mixer1', 'props': {'text': 'Overlay #0', 'visible': False}},
        {'type': 'text', 'source': 'mixer1', 'props': {'text': 'Overlay #1', 'visible': True}},
        {'type': 'text', 'source': 'mixer0', 'props': {'text': 'Overlay #2', 'visible': True}}
    ],
    'default_mixers': [
        {},
        {}
    ],
    'default_outputs': [
        # {'type': 'local'} # good for debugging
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(2)
    check_brave_is_running()
