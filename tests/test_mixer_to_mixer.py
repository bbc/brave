import time, pytest, inspect
from utils import *
from PIL import Image


def test_mixer_to_mixer(run_brave, create_config_file):
    '''Ensure a mixer can accept another mixer as source'''
    subtest_start_brave_with_two_mixers(run_brave, create_config_file)
    subtest_add_mixer1_as_source_of_mixer2()

    # mixer1's background is red.
    # mixer2's background is green.
    # mixer1 has been added as a source of mixer1, so the output of mixer2 should be red.
    subtest_ensure_mixer2_is_red()


def subtest_add_mixer1_as_source_of_mixer2():
    cut_to_source('mixer1', 2)
    time.sleep(1)
    assert_everything_in_playing_state()


def subtest_ensure_mixer2_is_red():
    add_output({'type': 'image', 'source': 'mixer2'})
    time.sleep(3)
    assert_image_output_color(1, [255, 0, 0])


def subtest_start_brave_with_two_mixers(run_brave, create_config_file):
    # Pattern 4 is red and pattern 5 is green
    config = {'default_mixers': [{'props': {'pattern': 4}}, {'props': {'pattern': 5}}]}
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(0.5)
    check_brave_is_running()
