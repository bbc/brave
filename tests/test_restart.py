import time, pytest, inspect
from utils import *

PORT_FROM_CONFIG_FILE = 12345
PORT_FROM_COMMAND_LINE = 12346

def test_restart_with_original_config(run_brave, create_config_file):
    '''
    WHEN user calls /api/restart with {'config':'original'}
    THEN Brave restarts and retains original config but not any additions
    '''
    config = {'inputs': [{'type': 'test_video'}]}
    config_file = create_config_file(config)
    run_brave(config_file.name)
    check_brave_is_running()
    add_input({'type': 'test_audio'})
    time.sleep(0.2)
    assert_inputs([{'type': 'test_video', 'id': 1}, {'type': 'test_audio', 'id': 2}])

    restart_brave({'config': 'original'})
    time.sleep(0.5)
    assert_inputs([{'type': 'test_video', 'id': 1}])


def test_restart_with_current_config(run_brave, create_config_file):
    '''
    WHEN user calls /api/restart with {'config':'current'}
    THEN Brave restarts and retains both original config and any additions
    '''
    config = {'inputs': [{'type': 'test_video'}]}
    config_file = create_config_file(config)
    run_brave(config_file.name)
    check_brave_is_running()
    add_input({'type': 'test_audio'})
    time.sleep(0.2)
    assert_inputs([{'type': 'test_video', 'id': 1}, {'type': 'test_audio', 'id': 2}])

    restart_brave({'config': 'current'})
    time.sleep(0.5)
    assert_inputs([{'type': 'test_video', 'id': 1}, {'type': 'test_audio', 'id': 2}])
