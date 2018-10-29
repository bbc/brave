import time, pytest, inspect
from utils import *
from PIL import Image

def test_overlays_on_multiple_mixers(run_brave, create_config_file):
    set_up_overlay_at_start(run_brave, create_config_file)
    assert_mixers([{'id': 0, 'state': 'PLAYING'},
                   {'id': 1, 'state': 'PLAYING'}])
    assert_overlays([{'id': 0, 'state': 'PLAYING', 'props': {'mixer_id': 1}},
                     {'id': 1, 'state': 'PLAYING', 'props': {'mixer_id': 1}},
                     {'id': 2, 'state': 'PLAYING', 'props': {'mixer_id': 0}}])

    add_overlay({'type': 'text', 'props': {'text': 'Overlay #3', 'visible': True}})
    add_overlay({'type': 'text', 'props': {'text': 'Overlay #4', 'visible': True, 'mixer_id': 1}})
    time.sleep(1)
    assert_overlays([{'id': 0, 'state': 'PLAYING', 'props': {'mixer_id': 1}},
                     {'id': 1, 'state': 'PLAYING', 'props': {'mixer_id': 1}},
                     {'id': 2, 'state': 'PLAYING', 'props': {'mixer_id': 0}},
                     {'id': 3, 'state': 'PLAYING', 'props': {'mixer_id': 0}},
                     {'id': 4, 'state': 'PLAYING', 'props': {'mixer_id': 1}}])

    delete_overlay(1)
    delete_overlay(2)
    time.sleep(1)
    assert_overlays([{'id': 0, 'state': 'PLAYING', 'props': {'mixer_id': 1}},
                     {'id': 3, 'state': 'PLAYING', 'props': {'mixer_id': 0}},
                     {'id': 4, 'state': 'PLAYING', 'props': {'mixer_id': 1}}])

    # TODO confirm this returns a 400
    add_overlay({'type': 'text', 'props': {'text': 'Overlay #3', 'mixer_id': 999}}, status_code=400)


def test_overlay_on_unkown_mixer_returns_error(run_brave, create_config_file):
    config = {'default_overlays': [
        {'type': 'text', 'props': {'text': 'No such mixer', 'visible': False, 'mixer_id': 1}},
    ]}
    config_file = create_config_file(config)
    run_brave(config_file.name)
    check_return_value(1)


def set_up_overlay_at_start(run_brave, create_config_file):
    output_video_location = create_output_video_location()

    config = {
    'default_overlays': [
        {'type': 'text', 'props': {'text': 'Overlay #0', 'visible': False, 'mixer_id': 1}},
        {'type': 'text', 'props': {'text': 'Overlay #1', 'visible': True, 'mixer_id': 1}},
        {'type': 'text', 'props': {'text': 'Overlay #2', 'visible': True}}
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
