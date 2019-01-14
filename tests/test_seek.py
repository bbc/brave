import time, pytest, inspect
from utils import *
from PIL import Image


def test_seek(run_brave):
    '''Ensure that the user can seek to a position of an input.'''
    run_brave()
    create_input()

    # STEP 1: Check initial position is 0
    state, position, duration = get_input_details()
    assert state == 'PAUSED'
    assert position == 0
    assert_duation(duration)

    # STEP 2: Update to 4 seconds and validate
    update_input(1, {'position': 4000000000})
    state, position, duration = get_input_details()
    assert state == 'PAUSED'
    assert position == 4000000000
    assert_duation(duration)

    # STEP 3: Play video and check it completes within 2 seconds. (It's a 5 second video so it should.)
    update_input(1, {'state': 'PLAYING'})
    time.sleep(2)
    state, position, duration = get_input_details()
    assert state == 'READY'
    assert position in [-1, 0, None] # Ideally this would be more consistent


def create_input():
    uri = 'file://' + test_directory() + '/assets/5_second_video.mp4'
    run_brave()
    add_input({'type': 'uri', 'state': 'PAUSED', 'uri': uri})
    time.sleep(1)


def get_input_details():
    response = api_get('/api/inputs')
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) == 1
    state = response_json[0]['state']
    position = response_json[0]['position'] if 'position' in response_json[0] else None
    duration = response_json[0]['duration'] if 'duration' in response_json[0] else None
    return state, position, duration


def assert_duation(duration):
    GRACE_DURATION_DIFFERENCE = 100000000
    assert (5000000000 + GRACE_DURATION_DIFFERENCE) > duration > (5000000000 - GRACE_DURATION_DIFFERENCE)
