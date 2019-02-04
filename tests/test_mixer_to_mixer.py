import time, pytest, inspect
from utils import *
from PIL import Image

GREEN=[0, 255, 0]
BLUE=[0, 0, 255]


def test_mixer_to_mixer(run_brave, create_config_file):
    '''Ensure a mixer can accept another mixer as source'''
    subtest_start_brave_with_three_mixers(run_brave, create_config_file)
    subtest_add_mixer2_as_source_of_mixer1()

    # mixer1's background is red.
    # mixer2's background is green.
    # mixer2 has been added as a source of mixer1, so the output of mixer1 should be green.
    subtest_ensure_mixer1_color(GREEN)

    subtest_add_mixer3_as_source_of_mixer1()

    # mixer3 had a lower zorder than mixer2 so it will still be the color of mixer2 (green_)
    subtest_ensure_mixer1_color(GREEN)

    # But if we increase the zorder of mixer3, then it will appear on top of mixer2, making it blue
    subtest_update_mixer3_zorder()
    subtest_ensure_mixer1_color(BLUE)

def subtest_add_mixer2_as_source_of_mixer1():
    overlay_source('mixer2', 1, details={'zorder': 2})
    time.sleep(1)
    assert_everything_in_playing_state()


def subtest_add_mixer3_as_source_of_mixer1():
    overlay_source('mixer3', 1, details={'zorder': 1})
    time.sleep(1)
    assert_everything_in_playing_state()
    assert_mixers([
        {'pattern': 4, 'sources': [
            {'uid': 'mixer2', 'in_mix': True, 'zorder': 2},
            {'uid': 'mixer3', 'in_mix': True, 'zorder': 1}
        ]},
        {'pattern': 5, 'sources': []},
        {'pattern': 6, 'sources': []}
    ])

def subtest_ensure_mixer1_color(color):
    time.sleep(3)
    assert_image_output_color(1, color)


def subtest_update_mixer3_zorder():
    overlay_source('mixer3', 1, details={'zorder': 3})
    time.sleep(1)
    assert_everything_in_playing_state()
    assert_mixers([
        {'pattern': 4, 'sources': [
            {'uid': 'mixer2', 'in_mix': True, 'zorder': 2},
            {'uid': 'mixer3', 'in_mix': True, 'zorder': 3}
        ]},
        {'pattern': 5, 'sources': []},
        {'pattern': 6, 'sources': []}
    ])


def subtest_start_brave_with_three_mixers(run_brave, create_config_file):
    # Pattern 4 is red, pattern 5 is green, pattern 6 is blue
    config = {
        'mixers': [{'pattern': 4}, {'pattern': 5}, {'pattern': 6}],
        'outputs': [{'type': 'image', 'source': 'mixer1'}]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(0.5)
    check_brave_is_running()
