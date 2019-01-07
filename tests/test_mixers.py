import time, pytest, inspect
from utils import *
from PIL import Image


def test_mixer_from_config(run_brave, create_config_file):
    subtest_start_brave_with_mixers(run_brave, create_config_file)
    subtest_assert_two_mixers(mixer_1_props={'width': 160, 'height': 90, 'pattern': 6})
    subtest_change_mixer_pattern()
    subtest_assert_two_mixers(mixer_1_props={'width': 160, 'height': 90, 'pattern': 7})
    subtest_change_width_and_height()
    subtest_assert_two_mixers(mixer_1_props={'width': 200, 'height': 300, 'pattern': 7})
    subtest_delete_mixers()
    subtest_delete_nonexistant_mixer()

def subtest_start_brave_with_mixers(run_brave, create_config_file):
    MIXER1 = {
        'width': 160,
        'height': 90,
        'pattern': 6
    }
    MIXER2 = {
        'width': 640,
        'height': 360
    }
    config = {'default_mixers': [MIXER1, MIXER2]}
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(1)
    check_brave_is_running()


def subtest_assert_two_mixers(mixer_1_props):
    assert_mixers([{
        'id': 1,
        **mixer_1_props,
    }, {
        'id': 2,
        'width': 640, 'height': 360, 'pattern': 0,
    }])

def subtest_change_mixer_pattern():
    update_mixer(1, {'pattern': 7})


def subtest_change_width_and_height():
    update_mixer(1, {'width': 200, 'height': 300})


def subtest_delete_mixers():
    delete_mixer(1)
    delete_mixer(2)
    assert_mixers([])


def subtest_delete_nonexistant_mixer():
    delete_mixer(10, 400)


def test_mixer_from_api(run_brave):
    run_brave()

    # There is one mixer by default
    assert_mixers([{'id': 1, 'width': 640, 'height': 360}])

    # Create input, ignore attempts to set an ID
    add_mixer({'width': 200, 'height': 200})
    time.sleep(1)
    assert_mixers([{'id': 1, 'width': 640, 'height': 360},
                   {'id': 2, 'width': 200, 'height': 200}])
    subtest_delete_mixers()
