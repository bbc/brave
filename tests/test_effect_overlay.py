import time, pytest, inspect
from utils import *
from PIL import Image


def test_effect_overlay_visible_after_creation(run_brave):
    run_brave()
    time.sleep(0.5)
    check_brave_is_running()

    add_overlay({'type': 'effect', 'source': 'mixer1', 'props': {'effect_name': 'edgetv'}})
    time.sleep(0.1)
    assert_overlays([{'id': 1, 'props': {'visible': False, 'effect_name': 'edgetv'}}])

    update_overlay(1, {'props': {'visible': True}}, status_code=200)
    time.sleep(0.1)
    assert_overlays([{'id': 1, 'props': {'visible': True,'effect_name': 'edgetv'}}])

    add_overlay({'type': 'effect', 'source': 'mixer1',  'props': {'effect_name': 'solarize'}})
    time.sleep(0.1)
    assert_overlays([{'id': 1, 'props': {'visible': True,'effect_name': 'edgetv'}},
                     {'id': 2, 'props': {'visible': False, 'effect_name': 'solarize'}}])

    update_overlay(2, {'props': {'visible': True}}, status_code=200)
    time.sleep(0.1)
    assert_overlays([{'id': 1, 'props': {'visible': True,'effect_name': 'edgetv'}},
                     {'id': 2, 'props': {'visible': True,'effect_name': 'solarize'}}])

    delete_overlay(1)
    time.sleep(0.1)
    assert_overlays([{'id': 2, 'props': {'visible': True,'effect_name': 'solarize'}}])

    delete_overlay(2)
    time.sleep(0.1)
    assert_overlays([])

# @pytest.mark.skip(reason="known bug that effects made visible at start should not be permitted")
def test_effect_overlay_visible_at_creation(run_brave):
    '''Test that visible:true on creation also does not work if mixer is playing/paused'''
    run_brave()
    time.sleep(0.5)
    check_brave_is_running()

    # This time, visible from the start with visible=True
    add_overlay({'type': 'effect', 'source': 'mixer1',  'props': {'effect_name': 'warptv', 'visible': True}}, status_code=200)
    time.sleep(0.1)
    assert_overlays([{'props': {'visible': True, 'effect_name': 'warptv'}}])


def test_set_up_effect_overlay_in_config_file(run_brave, create_config_file):
    '''Test that an effect in a config file works fine'''
    output_video_location = create_output_video_location()

    config = {
    'default_mixers': [{}],
    'default_overlays': [
        {'type': 'effect', 'source': 'mixer1', 'props': {'effect_name': 'burn', 'visible': True}},
        {'type': 'effect', 'source': 'mixer1', 'props': {'effect_name': 'vertigotv', 'visible': False}}
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(0.5)
    check_brave_is_running()
    assert_overlays([{'id': 1, 'props': {'effect_name': 'burn', 'visible': True}},
                     {'id': 2, 'props': {'effect_name': 'vertigotv', 'visible': False}}])
