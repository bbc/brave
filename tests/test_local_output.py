import time, pytest, inspect
from utils import *


def test_can_only_have_one_local_output(run_brave):
    run_brave()
    check_brave_is_running()
    assert_outputs([])

    add_output({'type': 'local'})
    assert_outputs([{'type': 'local', 'id': 1}])

    # 400 user error response for making two local outputs:
    add_output({'type': 'local'}, status_code=400)
    assert_outputs([{'type': 'local', 'id': 1}])
