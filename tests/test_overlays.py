import time, pytest, inspect
from utils import *
from PIL import Image

def test_overlay_at_start(run_brave, create_config_file):
    set_up_overlay_at_start(run_brave, create_config_file)
    assert_overlays([{'id': 1, 'uid': 'overlay1'}])

    add_overlay({'type': 'text', 'source': 'mixer1', 'text': 'Overlay #1', 'visible': True})
    time.sleep(1)
    assert_overlays([{'id': 1, 'source': 'mixer1', 'visible': True},
                     {'id': 2, 'source': 'mixer1', 'visible': True}])

    # Try adding one that's not visible:
    add_overlay({'type': 'text', 'source': 'mixer1', 'text': 'Overlay #2', 'visible': False})
    time.sleep(1)
    assert_overlays([{'id': 1, 'visible': True},
                     {'id': 2, 'visible': True},
                     {'id': 3, 'visible': False}])

    # Try changing visible flag
    update_overlay(1, {'visible': False})
    update_overlay(3, {'visible': True})
    time.sleep(1)
    assert_overlays([{'id': 1, 'visible': False},
                     {'id': 2, 'visible': True},
                     {'id': 3, 'visible': True}])

    subtest_delete_overlay()
    subtest_add_overlay_without_source()
    subtest_make_overlay_without_source_visible()


def subtest_delete_overlay():
    delete_overlay(3)
    time.sleep(1)
    assert_overlays([{'id': 1, 'visible': False},
                     {'id': 2, 'visible': True}])


def subtest_add_overlay_without_source():
    add_overlay({'type': 'text', 'text': 'Overlay #3b', 'visible': False})
    time.sleep(1)
    assert_overlays([{'id': 1, 'visible': False, 'source': 'mixer1'},
                     {'id': 2, 'visible': True, 'source': 'mixer1'},
                     {'id': 3, 'visible': False, 'source': None}])


def subtest_make_overlay_without_source_visible():
    # Cant't make visible if no source - so will return with a 400
    update_overlay(3, {'visible': True}, status_code=400)
    time.sleep(1)
    assert_overlays([{'id': 1, 'visible': False, 'source': 'mixer1'},
                     {'id': 2, 'visible': True, 'source': 'mixer1'},
                     {'id': 3, 'visible': False, 'source': None}])


def set_up_overlay_at_start(run_brave, create_config_file):
    output_video_location = create_output_video_location()

    config = {
    'mixers': [
        {}
    ],
    'overlays': [
        {'type': 'text', 'source': 'mixer1', 'text': 'Overlay #1', 'visible': True}
    ],
    'outputs': [
        # {'type': 'local'} # good for debugging
        {'type': 'local'}
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(2)
    check_brave_is_running()
