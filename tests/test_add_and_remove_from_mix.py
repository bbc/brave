import time, pytest, inspect
from utils import *
from PIL import Image

def test_adding_and_removing_sources_to_a_mix(run_brave, create_config_file):
    set_up_two_sources(run_brave, create_config_file)
    assert_api_returns_right_mixer_sources([{'id': 1, 'block_type': 'input', 'in_mix': True}, {'id': 2, 'block_type': 'input', 'in_mix': True}])
    remove_source('input2', 1)
    assert_api_returns_right_mixer_sources([{'id': 1, 'block_type': 'input', 'in_mix': True}, {'id': 2, 'block_type': 'input', 'in_mix': False}])
    remove_source('input2', 1)  # Prove it's safe to do repeatedly
    assert_api_returns_right_mixer_sources([{'id': 1, 'block_type': 'input', 'in_mix': True}, {'id': 2, 'block_type': 'input', 'in_mix': False}])
    remove_source('input1', 1)
    assert_api_returns_right_mixer_sources([{'id': 1, 'block_type': 'input', 'in_mix': False}, {'id': 2, 'block_type': 'input', 'in_mix': False}])
    overlay_source('input2', 1)
    assert_api_returns_right_mixer_sources([{'id': 1, 'block_type': 'input', 'in_mix': False}, {'id': 2, 'block_type': 'input', 'in_mix': True}])
    overlay_source('input2', 1) # Prove it's safe to do repeatedly
    assert_api_returns_right_mixer_sources([{'id': 1, 'block_type': 'input', 'in_mix': False}, {'id': 2, 'block_type': 'input', 'in_mix': True}])
    overlay_source('input1', 1)
    assert_api_returns_right_mixer_sources([{'id': 1, 'block_type': 'input', 'in_mix': True}, {'id': 2, 'block_type': 'input', 'in_mix': True}])


def test_removing_input_whilst_in_a_mix(run_brave, create_config_file):
    set_up_two_sources(run_brave, create_config_file)
    assert_api_returns_right_mixer_sources([{'id': 1, 'block_type': 'input', 'in_mix': True}, {'id': 2, 'block_type': 'input', 'in_mix': True}])
    assert_number_of_sinks_on_mixer(3) # 3 because there's always a dummy one with test video src
    delete_input(2)
    assert_api_returns_right_mixer_sources([{'id': 1, 'block_type': 'input', 'in_mix': True}])
    assert_number_of_sinks_on_mixer(2)


def test_switching(run_brave, create_config_file):
    set_up_two_sources(run_brave, create_config_file)
    assert_api_returns_right_mixer_sources([{'id': 1, 'block_type': 'input', 'in_mix': True}, {'id': 2, 'block_type': 'input', 'in_mix': True}])
    cut_to_source('input2', 1)
    assert_api_returns_right_mixer_sources([{'id': 1, 'block_type': 'input', 'in_mix': False}, {'id': 2, 'block_type': 'input', 'in_mix': True}])
    cut_to_source('input1', 1)
    assert_api_returns_right_mixer_sources([{'id': 1, 'block_type': 'input', 'in_mix': True}, {'id': 2, 'block_type': 'input', 'in_mix': False}])
    cut_to_source('input1', 1)
    assert_api_returns_right_mixer_sources([{'id': 1, 'block_type': 'input', 'in_mix': True}, {'id': 2, 'block_type': 'input', 'in_mix': False}])

def set_up_two_sources(run_brave, create_config_file):
    output_video_location = create_output_video_location()

    config = {
    'default_inputs': [
        {'type': 'test_video', 'pattern': 4, 'zorder': 2}, # pattern 4 is red
        {'type': 'test_video', 'pattern': 5, 'zorder': 3}, # pattern 5 is green
    ],
    'default_mixers': [
        {
            'sources': {
                'input1': {},
                'input2': {},
            }
        }
    ],
    'default_outputs': [
        # {'block_type': 'local'} # good for debugging
    ]
    }
    config_file = create_config_file(config)
    run_brave(config_file.name)
    time.sleep(2)
    check_brave_is_running()


def assert_api_returns_right_mixer_sources(inputs):
    response = api_get('/api/all')
    assert response.status_code == 200
    for i in inputs:
        i['uid'] = '%s%d' % (i['block_type'], i['id'])

    if len(inputs) == 0:
        assert ('sources' not in response.json()['mixers'][0]) or \
               (len(response.json()['mixers'][0]['sources']) == 0)
    else:
        assert response.json()['mixers'][0]['sources'] == inputs


def assert_number_of_sinks_on_mixer(num):
    response = api_get('/api/elements')
    assert response.status_code == 200
    json_response = response.json()
    elements = json_response['mixers']['1']['elements']
    video_mixer = next((x for x in elements if x['name'] == 'video_mixer'), None)
    pad_names = video_mixer['pads'].keys()
    sink_pad_names = list(filter(lambda x: x.startswith('sink'), pad_names))
    assert len(sink_pad_names) == num, 'Expected %d sinks on mixer but got %s' % (num, video_mixer['pads'].keys())
