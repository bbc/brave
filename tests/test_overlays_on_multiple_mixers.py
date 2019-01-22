import time, pytest, inspect
from utils import *
from PIL import Image

def test_overlays_on_multiple_mixers(run_brave, create_config_file):
    init_three_overlays(run_brave, create_config_file)
    assert_mixers([{'id': 1, 'state': 'PLAYING'},
                   {'id': 2, 'state': 'PLAYING'}])
    assert_overlays([{'id': 1, 'source': 'mixer2'},
                     {'id': 2, 'source': 'mixer2'},
                     {'id': 3, 'source': 'mixer1'}])

    add_overlay({'type': 'text', 'source': 'mixer1', 'text': 'Overlay #3', 'visible': True})
    add_overlay({'type': 'text', 'source': 'mixer2', 'text': 'Overlay #4', 'visible': True})
    time.sleep(1)
    assert_overlays([{'id': 1, 'source': 'mixer2'},
                     {'id': 2, 'source': 'mixer2'},
                     {'id': 3, 'source': 'mixer1'},
                     {'id': 4, 'source': 'mixer1'},
                     {'id': 5, 'source': 'mixer2'}])

    delete_overlay(2)
    delete_overlay(3)
    time.sleep(1)
    assert_overlays([{'id': 1, 'source': 'mixer2'},
                     {'id': 4, 'source': 'mixer1'},
                     {'id': 5, 'source': 'mixer2'}])


def test_overlay_on_unknown_mixer_via_api_returns_error(run_brave, create_config_file):
    init_three_overlays(run_brave, create_config_file)
    add_overlay({'type': 'text', 'source': 'mixer999', 'text': 'Overlay #4'}, status_code=400)


def test_overlay_on_unknown_mixer_in_config_returns_error(run_brave, create_config_file):
    config = {'overlays': [
        {'type': 'text', 'source': 'mixer999', 'text': 'No such mixer', 'visible': False},
    ]}
    config_file = create_config_file(config)
    run_brave(config_file.name)
    check_return_value(1)


def test_can_move_overlay_between_mixers(run_brave, create_config_file):
    init_three_overlays(run_brave, create_config_file)
    update_overlay(1, {'source': 'mixer1'})  # Changing an invisible overlay
    update_overlay(3, {'source': 'mixer2'})  # Changing a visible overlay
    update_overlay(2, {'source': None})  # Removing a source
    assert_overlays([{'id': 1, 'source': 'mixer1', 'visible': False},
                     {'id': 2, 'source': None, 'visible': False},
                     {'id': 3, 'source': 'mixer2', 'visible': True}])


def test_handles_bad_source(run_brave, create_config_file):
    init_three_overlays(run_brave, create_config_file)
    update_overlay(1, {'source': 'mixer999'}, status_code=400)


def test_overlay_copes_when_source_mixer_is_deleted(run_brave, create_config_file):
    init_three_overlays(run_brave, create_config_file)
    delete_mixer(1)
    assert_overlays([{'id': 1, 'source': 'mixer2'},
                     {'id': 2, 'source': 'mixer2'},
                     {'id': 3, 'source': None}])


def test_overlay_can_start_without_a_source(run_brave, create_config_file):
    output_video_location = create_output_video_location()

    config = {
    'overlays': [{'type': 'text', 'source': None, 'text': 'foo', 'visible': False}],
    'mixers': [{}]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(1)
    check_brave_is_running()
    assert_overlays([{'id': 1, 'source': None, 'text': 'foo'}])

    # Now update a prop, to check not having a source doesn't cause a problem
    update_overlay(1, {'text': 'bar'})
    assert_overlays([{'id': 1, 'source': None, 'text': 'bar'}])

    # Now add a source
    update_overlay(1, {'source': 'mixer1'})
    assert_overlays([{'id': 1, 'source': 'mixer1', 'text': 'bar'}])

    assert_everything_in_playing_state()


def init_three_overlays(run_brave, create_config_file):
    output_video_location = create_output_video_location()

    config = {
    'overlays': [
        {'type': 'text', 'source': 'mixer2', 'text': 'Overlay #1', 'visible': False},
        {'type': 'text', 'source': 'mixer2', 'text': 'Overlay #2', 'visible': True},
        {'type': 'text', 'source': 'mixer1', 'text': 'Overlay #3', 'visible': True}
    ],
    'mixers': [
        {},
        {}
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(1)
    check_brave_is_running()
