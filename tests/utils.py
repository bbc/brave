import subprocess, sys, time, tempfile, yaml, os, requests, pytest, signal, json, inspect

brave_processes = {}

@pytest.fixture #(scope="module")
def run_brave(config_file=None, port=None):
    def _run_brave(config_file=None, port=None):
        cmd = './brave.py'
        if (config_file):
            cmd += ' -c ' + config_file
        if port:
            cmd = 'PORT=%d %s' % (port, cmd)
        global brave_processes
        brave_processes[config_file] = subprocess.Popen(cmd, shell=True)
        time.sleep(1)
    yield _run_brave
    print('Stopping Brave...')
    global brave_processes
    for config_file, process in brave_processes.items():
        process.send_signal(signal.SIGINT)
    brave_processes = {}


def api_get(path, port=5000):
    url = 'http://localhost:%d%s' % (port, path)
    return requests.get(url)


def api_post(path, data):
    url = 'http://localhost:5000' + path
    return requests.post(url, data=json.dumps(data))


def api_put(path, data):
    url = 'http://localhost:5000' + path
    return requests.put(url, data=json.dumps(data))


def api_delete(path):
    url = 'http://localhost:5000' + path
    return requests.delete(url)

brave_process = None


@pytest.fixture
def create_config_file():

    created_config_files = []

    def _create_config_file(config):
        fp = tempfile.NamedTemporaryFile(delete=False)
        fp.write(yaml.dump(config).encode())
        fp.close()
        created_config_files.append(fp)
        return fp

    yield _create_config_file
    for fp in created_config_files:
        os.unlink(fp.name)


def check_brave_is_running():
    global brave_processes
    for config_file, process in brave_processes.items():
        assert process.poll() == None


def check_return_value(return_value):
    global brave_processes
    for config_file, process in brave_processes.items():
        assert process.poll() == return_value


def assert_inputs_in_playing_state(json_response):
    if 'inputs' in json_response:
        for input in json_response['inputs']:
            assert input['state'] == 'PLAYING', 'Input in %s state, not PLAYING: %s' % (input['state'], str(input))


def assert_outputs_in_playing_state(json_response):
    if 'outputs' in json_response:
        for output in json_response['outputs']:
            assert output['state'] == 'PLAYING', 'Output in %s state, not PLAYING: %s' % (output['state'], str(output))


def assert_mixers_in_playing_state(json_response):
    if 'mixers' in json_response:
        for mixer in json_response['mixers']:
            assert mixer['state'] == 'PLAYING', 'Mixer in %s state, not PLAYING: %s' % (mixer['state'], str(mixer))


def assert_overlays_in_playing_state(json_response):
    if 'overlays' in json_response:
        for overlay in json_response['overlays']:
            assert overlay['state'] == 'PLAYING', 'Overlay in %s state, not PLAYING: %s' % (overlay['state'], str(overlay))


def assert_everything_in_playing_state(json_response):
    assert_inputs_in_playing_state(json_response)
    assert_outputs_in_playing_state(json_response)
    assert_mixers_in_playing_state(json_response)
    assert_overlays_in_playing_state(json_response)


def delete_if_exists(name):
    try:
        os.unlink(name)
    except FileNotFoundError:
        pass


def test_directory():
    return os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


OUTPUT_IMAGE_LOCATION = '/tmp/test.jpg'
def create_output_image_location():
    global OUTPUT_IMAGE_LOCATION
    delete_if_exists(OUTPUT_IMAGE_LOCATION)
    return OUTPUT_IMAGE_LOCATION


OUTPUT_VIDEO_LOCATION = '/tmp/test.mp4'
def get_output_video_location():
    return OUTPUT_VIDEO_LOCATION


def create_output_video_location():
    global OUTPUT_VIDEO_LOCATION
    delete_if_exists(OUTPUT_VIDEO_LOCATION)
    return OUTPUT_VIDEO_LOCATION


def add_output(details, status_code=200):
    response = api_put('/api/outputs', details)
    assert response.status_code == status_code
    time.sleep(0.5)


def add_overlay(details, status_code=200):
    response = api_put('/api/overlays', details)
    assert response.status_code == status_code, 'Status code to make overlay was %d' % response.status_code


def delete_overlay(overlay_id):
    response = api_delete('/api/overlays/%d' % overlay_id)
    assert response.status_code == 200, 'Status code to delete overlay was %d' % response.status_code


def update_overlay(overlay_id, details, status_code=200):
    response = api_post('/api/overlays/' + str(overlay_id), details)
    assert response.status_code == status_code, 'Status code to update overlay was %d' % response.status_code


def set_mixer_state(mixer_id, state, status_code=200):
    response = api_post('/api/mixers/' + str(mixer_id), {'state': state})
    assert response.status_code == status_code, 'Status code to update mixer was %d' % response.status_code


def assert_outputs(outputs, check_playing_state=True):
    response = api_get('/api/all')
    assert response.status_code == 200
    if check_playing_state:
        assert_everything_in_playing_state(response.json())
    assert len(outputs) == len(response.json()['outputs'])

    # Chcek /api/outputs - should be the same
    response = api_get('/api/outputs')
    assert response.status_code == 200
    assert len(outputs) == len(response.json())

    for count, expected_output in enumerate(outputs):
        actual_output = response.json()[count]
        for (key, value) in expected_output.items():
            assert key in actual_output
            assert value == actual_output[key], 'For key "%s", expected "%s" but got "%s"' % (key, value, actual_output[key])


def assert_mixers(mixers):

    # Check /api/all
    response = api_get('/api/all')
    assert response.status_code == 200
    assert_everything_in_playing_state(response.json())
    assert len(mixers) == len(response.json()['mixers'])

    # Check /api/mixers - should be the same
    response = api_get('/api/mixers')
    assert response.status_code == 200
    assert len(mixers) == len(response.json())

    for count, expected_mixer in enumerate(mixers):
        actual_mixer = response.json()[count]
        for (key, value) in expected_mixer.items():
            assert key in actual_mixer
            assert value == actual_mixer[key], 'For key %s, expected %s but got %s' % (key, value, actual_mixer[key])


def assert_overlays(overlays):

    # Chcek /api/all
    response = api_get('/api/all')
    assert response.status_code == 200
    assert_inputs_in_playing_state(response.json())
    assert_mixers_in_playing_state(response.json())
    assert len(overlays) == len(response.json()['overlays'])

    # Chcek /api/overlays - should be the same
    response = api_get('/api/overlays')
    assert response.status_code == 200
    assert len(overlays) == len(response.json())

    for count, expected_overlay in enumerate(overlays):
        actual_overlay = response.json()[count]
        for (key, value) in expected_overlay.items():
            assert key in actual_overlay
            if key == 'props':
                for (key, value) in expected_overlay['props'].items():
                    assert key in actual_overlay['props']
                    assert value == actual_overlay['props'][key]
            else:
                assert value == actual_overlay[key], 'Key "%s" expected to be "%s", but was "%s"' % (key, value, actual_overlay[key])


def add_input(details):
    response = api_put('/api/inputs', details)
    assert response.status_code == 200
    time.sleep(0.2)


def delete_input(id, expected_status_code=200):
    response = api_delete('/api/inputs/' + str(id))
    assert response.status_code == expected_status_code
    time.sleep(0.2)


def update_input(id, updates, expected_status_code=200):
    response = api_post('/api/inputs/' + str(id), updates)
    assert response.status_code == expected_status_code
    time.sleep(0.2)


def update_mixer(id, updates, expected_status_code=200):
    response = api_post('/api/mixers/' + str(id), updates)
    assert response.status_code == expected_status_code
    time.sleep(0.2)


def assert_inputs(inputs, check_playing_state=True):
    response = api_get('/api/all')
    assert response.status_code == 200
    if check_playing_state:
        assert_everything_in_playing_state(response.json())
    assert len(inputs) == len(response.json()['inputs'])

    # Test /api/inputs as well as /api/all:
    response = api_get('/api/inputs')
    assert response.status_code == 200
    assert len(inputs) == len(response.json())

    for count, expected_input in enumerate(inputs):
        actual_input = response.json()[count]
        for (key, value) in expected_input.items():
            assert key in actual_input
            if key == 'props':
                for (key, value) in expected_input['props'].items():
                    assert key in actual_input['props']
                    assert value == actual_input['props'][key]
            else:
                assert value == actual_input[key], 'For key "%s", expected "%s" but got "%s"' % (key, value, actual_input[key])


def remove_input(id, expected_status_code=200):
    response = api_delete('/api/inputs/' + str(id))
    assert response.status_code == expected_status_code
    time.sleep(0.2)
