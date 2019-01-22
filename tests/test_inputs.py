import time, pytest, inspect
from utils import *


def test_inputs(run_brave):
    run_brave()
    check_brave_is_running()
    assert_inputs([])

    # Create input, and can set the id
    add_input({'type': 'test_video', 'id': 99})
    time.sleep(2)
    assert_inputs([{'type': 'test_video', 'id': 99, 'uid': 'input99'}])

    # Different types of inputs work:
    add_input({'type': 'test_audio'})
    time.sleep(1)
    assert_inputs([{'type': 'test_video', 'id': 99}, {'type': 'test_audio', 'id': 1}])

    # Change state to PAUSED
    update_input(1, {'state': 'NULL'})
    assert_inputs([{'type': 'test_video', 'id': 99}, {'type': 'test_audio', 'id': 1, 'state': 'NULL'}], check_playing_state=False)

    # Change state to READY
    update_input(1, {'state': 'READY'})
    assert_inputs([{'type': 'test_video', 'id': 99}, {'type': 'test_audio', 'id': 1, 'state': 'READY'}], check_playing_state=False)

    # Change state to NULL
    update_input(1, {'state': 'PAUSED'})
    assert_inputs([{'type': 'test_video', 'id': 99}, {'type': 'test_audio', 'id': 1, 'state': 'PAUSED'}], check_playing_state=False)

    # Change state to PLAYING
    update_input(1, {'state': 'PLAYING'})
    time.sleep(1)
    assert_inputs([{'type': 'test_video', 'id': 99}, {'type': 'test_audio', 'id': 1}])

    # Add a property to existing input
    update_input(99, {'pattern': 5})
    assert_inputs([{'type': 'test_video', 'id': 99, 'pattern': 5}, {'type': 'test_audio', 'id': 1}])

    # Add a bad property to existing input
    update_input(1, {'not_real': 100}, 400)
    assert_inputs([{'type': 'test_video', 'id': 99}, {'type': 'test_audio', 'id': 1}])

    # Add a property to missing input
    update_input(55, {'pattern': 6}, 400)

    # Change an ID of an input does not work
    update_input(99, {'id': 10}, 400)

    # Removing an existing input works:
    delete_input(99)
    assert_inputs([{'type': 'test_audio', 'id': 1}])

    # Removing a non-existant input causes a user error
    delete_input(55, expected_status_code=400) # Does not exist
    assert_inputs([{'type': 'test_audio', 'id': 1}])
