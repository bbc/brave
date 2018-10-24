import time, pytest, inspect
from utils import *
from PIL import Image


def test_effect_overlay_visible_after_creation(run_brave):
    run_brave()
    time.sleep(0.5)
    check_brave_is_running()

    add_overlay({'type': 'effect', 'props': {'effect_name': 'edgetv'}})
    time.sleep(0.1)
    assert_overlays([{'id': 0, 'state': 'NULL', 'props': {'visible': False}}])

    # Making visible fails
    update_overlay(0, {'props': {'visible': True}}, status_code=400)
    time.sleep(0.1)
    assert_overlays([{'id': 0, 'state': 'NULL', 'props': {'visible': False}}])

    # But if the mixer is in READY, then making visible works
    set_mixer_state(0, 'READY')
    time.sleep(0.1)
    update_overlay(0, {'props': {'visible': True}})
    time.sleep(0.1)
    set_mixer_state(0, 'PLAYING')
    time.sleep(0.1)
    assert_overlays([{'id': 0, 'state': 'PLAYING', 'props': {'visible': True,'effect_name': 'edgetv'}}])

# @pytest.mark.skip(reason="known bug that effects made visible at start should not be permitted")
def test_effect_overlay_visible_at_creation(run_brave):
    '''Test that visible:true on creation also does not work if mixer is playing/paused'''
    run_brave()
    time.sleep(0.5)
    check_brave_is_running()

    # This time, visible from the start, will 400 fail as not allowed
    add_overlay({'type': 'effect', 'props': {'effect_name': 'warptv', 'visible': True}}, status_code=400)
    time.sleep(0.1)
    assert_overlays([])

    # But if the mixer is in READY, then creating one visible from the start works
    set_mixer_state(0, 'READY')
    time.sleep(0.1)
    add_overlay({'type': 'effect', 'props': {'effect_name': 'warptv', 'visible': True}})
    time.sleep(0.1)
    set_mixer_state(0, 'PLAYING')
    time.sleep(0.1)
    assert_overlays([{'state': 'PLAYING', 'props': {'visible': True, 'effect_name': 'warptv'}}])


def test_set_up_effect_overlay_in_config_file(run_brave, create_config_file):
    '''Test that an effect in a config file works fine'''
    output_video_location = create_output_video_location()

    config = {
    'default_overlays': [
        {'type': 'effect', 'props': {'effect_name': 'edgetv', 'visible': True}},
        {'type': 'effect', 'props': {'effect_name': 'warptv', 'visible': False}}
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(0.5)
    check_brave_is_running()
    assert_overlays([{'id': 0, 'state': 'PLAYING', 'props': {'effect_name': 'edgetv', 'visible': True}},
                     {'id': 1, 'state': 'PLAYING', 'props': {'effect_name': 'warptv', 'visible': False}}])
