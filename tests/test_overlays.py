import time, pytest, inspect
from utils import *
from PIL import Image

def test_overlay_at_start(run_brave, create_config_file):
    set_up_overlay_at_start(run_brave, create_config_file)
    assert_overlays([{'id': 0, 'state': 'PLAYING'}])

    add_overlay({'type': 'text', 'source': 'mixer0', 'props': {'text': 'Overlay #1', 'visible': True}})
    time.sleep(1)
    assert_overlays([{'id': 0, 'state': 'PLAYING', 'source': 'mixer0', 'props': {'visible': True}},
                     {'id': 1, 'state': 'PLAYING', 'source': 'mixer0', 'props': {'visible': True}}])

    # Try adding one that's not visible:
    add_overlay({'type': 'text', 'source': 'mixer0', 'props': {'text': 'Overlay #2', 'visible': False}})
    time.sleep(1)
    assert_overlays([{'id': 0, 'state': 'PLAYING', 'props': {'visible': True}},
                     {'id': 1, 'state': 'PLAYING', 'props': {'visible': True}},
                     {'id': 2, 'state': 'NULL', 'props': {'visible': False}}])

    # Try changing visible flag
    update_overlay(0, {'props': {'visible': False}})
    update_overlay(2, {'props': {'visible': True}})
    time.sleep(1)
    assert_overlays([{'id': 0, 'state': 'NULL', 'props': {'visible': False}},
                     {'id': 1, 'state': 'PLAYING', 'props': {'visible': True}},
                     {'id': 2, 'state': 'PLAYING', 'props': {'visible': True}}])

    delete_overlay(2)
    time.sleep(1)
    assert_overlays([{'id': 0, 'state': 'NULL', 'props': {'visible': False}},
                     {'id': 1, 'state': 'PLAYING', 'props': {'visible': True}}])


def set_up_overlay_at_start(run_brave, create_config_file):
    output_video_location = create_output_video_location()

    config = {
    'default_mixers': [
        {}
    ],
    'default_overlays': [
        {'type': 'text', 'source': 'mixer0', 'props': {'text': 'Overlay #0', 'visible': True}}
    ],
    'default_outputs': [
        # {'type': 'local'} # good for debugging
        {'type': 'local'}
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(2)
    check_brave_is_running()
