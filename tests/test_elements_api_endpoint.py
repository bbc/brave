import time, pytest
from utils import *


def test_elements_api_endpoint(run_brave):
    '''
    Check that /api/elements returns a list of element details,
    including when "?show_inside_bin_elements=yes"
    '''
    run_brave()
    time.sleep(0.5)
    check_brave_is_running()
    add_input({'type': 'image', 'props': {'uri': 'file://' + test_directory() + '/assets/image_640_360.png'}})
    time.sleep(1)

    subtest_elements_endpoint()
    subtest_elements_endpoint_with_bin_elements()

def subtest_elements_endpoint():
    elements_response = api_get('/api/elements')
    assert elements_response.status_code == 200
    elements_object = elements_response.json()
    assert len(elements_object['inputs'].items()) == 1
    assert len(elements_object['mixers'].items()) == 1
    assert len(elements_object['outputs'].items()) == 0
    assert len(elements_object['inputs']['0']['elements']) == 5

def subtest_elements_endpoint_with_bin_elements():
    elements_response = api_get('/api/elements?show_inside_bin_elements=yes')
    assert elements_response.status_code == 200
    elements_object = elements_response.json()
    assert len(elements_object['inputs'].items()) == 1
    assert len(elements_object['mixers'].items()) == 1
    assert len(elements_object['outputs'].items()) == 0
    assert len(elements_object['inputs']['0']['elements']) == 10
